"""Exportadores de resultados de Scopus."""

from __future__ import annotations

import csv
import io
import json
from typing import Iterable

from .client import ScopusArticle


def articles_to_json(articles: Iterable[ScopusArticle]) -> bytes:
    data = [article.as_dict() for article in articles]
    return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")


def articles_to_csv(articles: Iterable[ScopusArticle]) -> bytes:
    data = [article.as_dict() for article in articles]
    if not data:
        return b""
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(data[0]))
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue().encode("utf-8-sig")
