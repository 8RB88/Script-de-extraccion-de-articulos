"""Cliente tipado para buscar artículos en PubMed mediante E-utilities."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterator
from urllib.parse import quote
from xml.etree import ElementTree

import requests


ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
EFETCH_BATCH_SIZE = 200


class PubMedAPIError(RuntimeError):
    """Error legible devuelto por PubMed o por la configuración local."""


@dataclass(frozen=True)
class PubMedQuery:
    topic: str = ""
    max_results: int = 25
    year_from: int | None = None
    year_to: int | None = None
    language: str | None = None
    publication_type: str | None = None
    sort: str = "relevance"
    advanced_query: str | None = None

    def to_search_string(self) -> str:
        if self.max_results < 1:
            raise ValueError("El número de artículos debe ser mayor que cero.")
        if self.advanced_query is not None:
            query = self.advanced_query.strip()
            if not query:
                raise ValueError("La consulta avanzada no puede estar vacía.")
            return query
        topic = self.topic.strip()
        if not topic:
            raise ValueError("El tema de búsqueda no puede estar vacío.")
        if self.year_from is not None and self.year_to is not None and self.year_from > self.year_to:
            raise ValueError("El año inicial no puede ser posterior al año final.")
        clauses = [topic]
        if self.year_from is not None:
            clauses.append(f'"{self.year_from}"[Date - Publication] : "'
                           f'{self.year_to or self.year_from}"[Date - Publication]')
        if self.language:
            clauses.append(f"{self.language}[Language]")
        if self.publication_type:
            clauses.append(f'"{self.publication_type}"[Publication Type]')
        return " AND ".join(clauses)


@dataclass(frozen=True)
class PubMedArticle:
    title: str
    doi: str
    pmid: str
    authors: str
    publication_name: str
    cover_date: str
    abstract: str
    cited_by_count: int
    open_access: bool
    url: str
    pmc_id: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class PubMedClient:
    """Consulta PubMed y obtiene los metadatos completos de los resultados."""

    def __init__(
        self,
        *,
        email: str | None = None,
        api_key: str | None = None,
        timeout: float = 30.0,
        session: requests.Session | None = None,
    ) -> None:
        self.email = email.strip() if email else ""
        self.api_key = api_key.strip() if api_key else ""
        self.timeout = timeout
        self.session = session or requests.Session()

    def search(self, query: PubMedQuery) -> list[PubMedArticle]:
        return list(self.iter_search(query))

    def iter_search(self, query: PubMedQuery) -> Iterator[PubMedArticle]:
        search_params: dict[str, Any] = {
            "db": "pubmed",
            "term": query.to_search_string(),
            "retmax": query.max_results,
            "retmode": "json",
            "sort": query.sort,
        }
        self._add_common_params(search_params)
        response = self.session.get(ESEARCH_URL, params=search_params, timeout=self.timeout)
        if response.status_code == 429:
            raise PubMedAPIError("PubMed ha limitado temporalmente las solicitudes. Intenta más tarde.")
        if not response.ok:
            raise PubMedAPIError(f"PubMed respondió con HTTP {response.status_code}.")
        try:
            ids = response.json().get("esearchresult", {}).get("idlist", [])
        except ValueError as exc:
            raise PubMedAPIError("PubMed devolvió una respuesta JSON no válida.") from exc
        if not ids:
            return

        for start in range(0, len(ids), EFETCH_BATCH_SIZE):
            fetch_params: dict[str, Any] = {
                "db": "pubmed",
                "id": ",".join(ids[start:start + EFETCH_BATCH_SIZE]),
                "retmode": "xml",
            }
            self._add_common_params(fetch_params)
            response = self.session.get(EFETCH_URL, params=fetch_params, timeout=self.timeout)
            if not response.ok:
                raise PubMedAPIError(f"PubMed respondió con HTTP {response.status_code} al obtener metadatos.")
            try:
                root = ElementTree.fromstring(response.text)
            except ElementTree.ParseError as exc:
                raise PubMedAPIError("PubMed devolvió XML no válido.") from exc
            for record in root.findall(".//PubmedArticle"):
                yield self._to_article(record)

    def _add_common_params(self, params: dict[str, Any]) -> None:
        if self.email:
            params["email"] = self.email
        if self.api_key:
            params["api_key"] = self.api_key

    @staticmethod
    def _to_article(record: ElementTree.Element) -> PubMedArticle:
        def text(path: str) -> str:
            return (record.findtext(path) or "").strip()

        authors = []
        for author in record.findall(".//Author"):
            collective = author.findtext("CollectiveName")
            name = collective or " ".join(
                part for part in (author.findtext("ForeName"), author.findtext("LastName")) if part
            )
            if name:
                authors.append(name)
        doi = ""
        for article_id in record.findall(".//ArticleId"):
            if article_id.attrib.get("IdType") == "doi":
                doi = (article_id.text or "").strip()
                break
        pmid = text("./MedlineCitation/PMID")
        pmc_id = ""
        for article_id in record.findall(".//ArticleId"):
            if article_id.attrib.get("IdType") == "pmc":
                pmc_id = (article_id.text or "").strip()
                break
        abstract = " ".join(
            " ".join(part.itertext()).strip()
            for part in record.findall(".//Abstract/AbstractText")
            if " ".join(part.itertext()).strip()
        )
        date = text(".//ArticleDate/Year")
        if not date:
            date = text(".//PubDate/Year")
        return PubMedArticle(
            title=text(".//ArticleTitle"),
            doi=doi,
            pmid=pmid,
            authors=", ".join(authors),
            publication_name=text(".//Journal/Title"),
            cover_date=date,
            abstract=abstract,
            cited_by_count=0,
            open_access=bool(pmc_id),
            url=f"https://pubmed.ncbi.nlm.nih.gov/{quote(pmid)}/" if pmid else "",
            pmc_id=pmc_id,
        )
