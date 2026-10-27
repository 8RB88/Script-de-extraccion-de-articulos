import json

import pytest

from scopus_extractor.client import ScopusClient, ScopusQuery
from scopus_extractor.exporters import articles_to_csv, articles_to_json


def test_query_builds_filters():
    query = ScopusQuery("climate change", max_results=10, year_from=2020, year_to=2022, language="English")
    assert query.to_search_string() == (
        "TITLE-ABS-KEY(climate change) AND OPENACCESS(1) AND "
        "PUBYEAR AFT 2019 AND PUBYEAR BEF 2023 AND LANGUAGE(English)"
    )


def test_query_rejects_invalid_years():
    with pytest.raises(ValueError):
        ScopusQuery("topic", year_from=2023, year_to=2020).to_search_string()


def test_advanced_query_is_sent_unchanged():
    advanced = 'TITLE-ABS-KEY("quantum computing") AND PUBYEAR > 2020 AND OPENACCESS(1)'
    query = ScopusQuery(
        advanced_query=advanced,
        open_access_only=False,
        year_from=2010,
        year_to=2020,
        language="English",
    )
    assert query.to_search_string() == advanced


class Response:
    status_code = 200
    ok = True

    def json(self):
        return {
            "search-results": {
                "entry": [
                    {
                        "dc:title": "An article",
                        "dc:creator": "Author",
                        "prism:doi": "10.1234/example",
                        "eid": "2-s2.0-1",
                        "openaccess": "1",
                        "citedby-count": "3",
                    }
                ]
            }
        }


class Session:
    def get(self, *args, **kwargs):
        return Response()


def test_search_normalizes_and_exports_article():
    articles = ScopusClient("key", session=Session()).search(ScopusQuery("topic", max_results=1))
    assert articles[0].title == "An article"
    assert articles[0].open_access is True
    assert json.loads(articles_to_json(articles))[0]["title"] == "An article"
    assert b"An article" in articles_to_csv(articles)
