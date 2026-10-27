"""Cliente pequeño y tipado para la API de búsqueda de Scopus."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterator

import requests


SEARCH_URL = "https://api.elsevier.com/content/search/scopus"


class ScopusAPIError(RuntimeError):
    """Error legible devuelto por la API o por la configuración local."""


@dataclass(frozen=True)
class ScopusQuery:
    """Criterios soportados por la búsqueda guiada o avanzada."""

    topic: str = ""
    max_results: int = 25
    open_access_only: bool = True
    year_from: int | None = None
    year_to: int | None = None
    language: str | None = None
    document_type: str | None = None
    subject_area: str | None = None
    sort: str = "-coverDate"
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

        clauses = [f"TITLE-ABS-KEY({topic})"]
        if self.open_access_only:
            clauses.append("OPENACCESS(1)")
        if self.year_from is not None:
            clauses.append(f"PUBYEAR AFT {self.year_from - 1}")
        if self.year_to is not None:
            clauses.append(f"PUBYEAR BEF {self.year_to + 1}")
        if self.language:
            clauses.append(f"LANGUAGE({self.language})")
        if self.document_type:
            clauses.append(f"DOCTYPE({self.document_type})")
        if self.subject_area:
            clauses.append(f"SUBJAREA({self.subject_area})")
        return " AND ".join(clauses)


@dataclass(frozen=True)
class ScopusArticle:
    """Metadatos normalizados para una entrada de Scopus."""

    title: str
    doi: str
    eid: str
    authors: str
    publication_name: str
    cover_date: str
    abstract: str
    cited_by_count: int
    open_access: bool
    url: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ScopusClient:
    """Consulta Scopus usando la API de Elsevier."""

    def __init__(self, api_key: str, *, timeout: float = 30.0, session: requests.Session | None = None) -> None:
        if not api_key.strip():
            raise ValueError("Se necesita una clave API de Scopus.")
        self.api_key = api_key.strip()
        self.timeout = timeout
        self.session = session or requests.Session()

    def search(self, query: ScopusQuery) -> list[ScopusArticle]:
        return list(self.iter_search(query))

    def iter_search(self, query: ScopusQuery) -> Iterator[ScopusArticle]:
        search_string = query.to_search_string()
        start = 0
        remaining = query.max_results
        while remaining:
            page_size = min(25, remaining)
            response = self.session.get(
                SEARCH_URL,
                headers={"X-ELS-APIKey": self.api_key, "Accept": "application/json"},
                params={
                    "query": search_string,
                    "start": start,
                    "count": page_size,
                    "sort": query.sort,
                },
                timeout=self.timeout,
            )
            if response.status_code == 401:
                raise ScopusAPIError("La clave API no es válida o no tiene acceso a Scopus.")
            if response.status_code == 429:
                raise ScopusAPIError("Scopus ha limitado temporalmente las solicitudes. Intenta más tarde.")
            if not response.ok:
                raise ScopusAPIError(f"Scopus respondió con HTTP {response.status_code}.")
            try:
                entries = response.json().get("search-results", {}).get("entry", [])
            except ValueError as exc:
                raise ScopusAPIError("Scopus devolvió una respuesta JSON no válida.") from exc
            if not entries:
                return
            for entry in entries:
                yield self._to_article(entry)
                remaining -= 1
                if not remaining:
                    return
            start += len(entries)
            if len(entries) < page_size:
                return

    @staticmethod
    def _to_article(entry: dict[str, Any]) -> ScopusArticle:
        authors = entry.get("dc:creator", "")
        author_list = entry.get("author", [])
        if author_list:
            authors = ", ".join(
                author.get("ce:indexed-name", author.get("ce:surname", ""))
                for author in author_list
                if author.get("ce:indexed-name", author.get("ce:surname", ""))
            )
        return ScopusArticle(
            title=entry.get("dc:title", ""),
            doi=entry.get("prism:doi", ""),
            eid=entry.get("eid", ""),
            authors=authors,
            publication_name=entry.get("prism:publicationName", ""),
            cover_date=entry.get("prism:coverDate", ""),
            abstract=entry.get("dc:description", ""),
            cited_by_count=int(entry.get("citedby-count", 0) or 0),
            open_access=str(entry.get("openaccess", "0")) in {"1", "true", "True"},
            url=entry.get("prism:url", ""),
        )
