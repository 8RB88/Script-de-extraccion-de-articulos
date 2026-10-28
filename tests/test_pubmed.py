import json

from scopus_extractor.exporters import articles_to_json
from scopus_extractor.pubmed import PubMedClient, PubMedQuery


def test_query_builds_pubmed_filters():
    query = PubMedQuery("climate change", year_from=2020, year_to=2022, language="English", publication_type="Review")
    assert query.to_search_string() == (
        'climate change AND "2020"[Date - Publication] : "2022"[Date - Publication] '
        'AND English[Language] AND "Review"[Publication Type]'
    )


class Response:
    status_code = 200
    ok = True

    def __init__(self, payload=None, text=""):
        self.payload = payload
        self.text = text

    def json(self):
        return self.payload


class Session:
    def get(self, url, **kwargs):
        if "esearch" in url:
            return Response({"esearchresult": {"idlist": ["123"]}})
        return Response(
            text="""
            <PubmedArticleSet><PubmedArticle>
              <MedlineCitation><PMID>123</PMID><Article>
                <ArticleTitle>A PubMed article</ArticleTitle>
                <Abstract><AbstractText>Summary text.</AbstractText></Abstract>
                <Journal><Title>Journal of Tests</Title></Journal>
                <AuthorList><Author><ForeName>Jane</ForeName><LastName>Doe</LastName></Author></AuthorList>
                <ArticleDate><Year>2024</Year></ArticleDate>
              </Article></MedlineCitation>
              <PubmedData><ArticleIdList><ArticleId IdType="doi">10.1234/example</ArticleId></ArticleIdList></PubmedData>
            </PubmedArticle></PubmedArticleSet>
            """,
        )


def test_search_parses_and_exports_pubmed_article():
    articles = PubMedClient(session=Session()).search(PubMedQuery("topic", max_results=1))
    assert articles[0].title == "A PubMed article"
    assert articles[0].authors == "Jane Doe"
    assert articles[0].doi == "10.1234/example"
    assert json.loads(articles_to_json(articles))[0]["pmid"] == "123"


class BatchedSession:
    def __init__(self):
        self.fetch_ids = []

    def get(self, url, **kwargs):
        if "esearch" in url:
            return Response({"esearchresult": {"idlist": [str(index) for index in range(1000)]}})
        self.fetch_ids.append(kwargs["params"]["id"].split(","))
        return Response(text="<PubmedArticleSet />")


def test_search_batches_large_pubmed_fetch_requests():
    session = BatchedSession()

    articles = PubMedClient(session=session).search(PubMedQuery("topic", max_results=1000))

    assert articles == []
    assert [len(batch) for batch in session.fetch_ids] == [200, 200, 200, 200, 200]
