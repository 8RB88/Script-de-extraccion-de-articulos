"""Localización y descarga de copias PDF legalmente disponibles en acceso abierto."""

from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import requests


UNPAYWALL_URL = "https://api.unpaywall.org/v2"
MAX_PDF_BYTES = 50 * 1024 * 1024


class OpenAccessError(RuntimeError):
    """Error al consultar o descargar una copia de acceso abierto."""


@dataclass(frozen=True)
class OpenAccessPDF:
    title: str
    doi: str
    url: str


class OpenAccessClient:
    """Busca copias OA por DOI y descarga solo respuestas PDF."""

    def __init__(
        self,
        email: str,
        *,
        timeout: float = 30.0,
        session: requests.Session | None = None,
    ) -> None:
        if "@" not in email.strip():
            raise ValueError("Unpaywall necesita un correo electrónico válido.")
        self.email = email.strip()
        self.timeout = timeout
        self.session = session or requests.Session()

    def find_pdf(self, doi: str, title: str) -> OpenAccessPDF | None:
        if not doi.strip():
            return None
        response = self.session.get(
            f"{UNPAYWALL_URL}/{quote(doi.strip(), safe='')}",
            params={"email": self.email},
            timeout=self.timeout,
        )
        if response.status_code == 404:
            return None
        if not response.ok:
            raise OpenAccessError(f"Unpaywall respondió con HTTP {response.status_code}.")
        try:
            locations = response.json().get("oa_locations", [])
        except ValueError as exc:
            raise OpenAccessError("Unpaywall devolvió una respuesta JSON no válida.") from exc
        for location in locations:
            url = location.get("url_for_pdf") or location.get("url")
            if isinstance(url, str) and url.startswith(("https://", "http://")):
                return OpenAccessPDF(title=title, doi=doi, url=url)
        return None

    def download(self, pdf: OpenAccessPDF) -> bytes:
        response = self.session.get(pdf.url, timeout=self.timeout, stream=True)
        if not response.ok:
            raise OpenAccessError(f"No se pudo descargar el PDF (HTTP {response.status_code}).")
        content_type = response.headers.get("Content-Type", "").lower()
        content_length = int(response.headers.get("Content-Length", "0") or 0)
        if content_length > MAX_PDF_BYTES:
            raise OpenAccessError("El PDF supera el límite de 50 MB.")
        chunks: list[bytes] = []
        total = 0
        for chunk in response.iter_content(chunk_size=64 * 1024):
            total += len(chunk)
            if total > MAX_PDF_BYTES:
                raise OpenAccessError("El PDF supera el límite de 50 MB.")
            chunks.append(chunk)
        content = b"".join(chunks)
        if not content.startswith(b"%PDF-") and "application/pdf" not in content_type:
            raise OpenAccessError("La fuente no devolvió un archivo PDF.")
        return content


def build_pdf_archive(
    client: OpenAccessClient,
    articles: list[Any],
) -> tuple[bytes, list[str], list[str], list[str]]:
    """Devuelve ZIP, nombres descargados, títulos sin PDF y errores."""

    archive = io.BytesIO()
    downloaded: list[str] = []
    unavailable: list[str] = []
    errors: list[str] = []
    used_names: set[str] = set()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for article in articles:
            try:
                pdf = client.find_pdf(article.doi, article.title)
                if pdf is None:
                    unavailable.append(article.title)
                    continue
                content = client.download(pdf)
            except (OpenAccessError, requests.RequestException) as exc:
                errors.append(f"{article.title}: {exc}")
                continue
            filename = _safe_filename(article.title or article.doi) + ".pdf"
            base_name = filename[:-4]
            suffix = 2
            while filename in used_names:
                filename = f"{base_name}_{suffix}.pdf"
                suffix += 1
            used_names.add(filename)
            zip_file.writestr(filename, content)
            downloaded.append(filename)
    return archive.getvalue(), downloaded, unavailable, errors


def _safe_filename(value: str) -> str:
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip(" .")
    return filename[:120] or "article"
