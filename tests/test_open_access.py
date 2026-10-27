from scopus_extractor.open_access import OpenAccessClient, build_pdf_archive


class Response:
    status_code = 200
    ok = True
    headers = {"Content-Type": "application/pdf"}

    def __init__(self, payload=None):
        self.payload = payload

    def json(self):
        return self.payload

    def iter_content(self, chunk_size):
        yield b"%PDF-1.7 test"


class Session:
    def get(self, url, **kwargs):
        if "unpaywall" in url:
            return Response({"oa_locations": [{"url_for_pdf": "https://repository.example/article.pdf"}]})
        return Response()


class Article:
    doi = "10.1234/test"
    title = "A test/article"


def test_build_pdf_archive_downloads_and_sanitizes_names():
    archive, downloaded, unavailable, errors = build_pdf_archive(
        OpenAccessClient("test@example.com", session=Session()),
        [Article()],
    )
    assert downloaded == ["A test_article.pdf"]
    assert unavailable == []
    assert errors == []
    assert archive.startswith(b"PK")
