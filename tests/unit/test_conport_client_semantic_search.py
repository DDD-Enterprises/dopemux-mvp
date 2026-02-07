import pytest

from dopemux.tools.conport_client import ConPortClient


class _FakeResponse:
    def __init__(self, status, payload=None, text_body=""):
        self.status = status
        self._payload = payload if payload is not None else {}
        self._text_body = text_body

    async def json(self):
        return self._payload

    async def text(self):
        return self._text_body


class _FakeRequestContext:
    def __init__(self, response):
        self._response = response

    async def __aenter__(self):
        return self._response

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeSession:
    def __init__(self, scripted_calls):
        self._scripted_calls = list(scripted_calls)
        self.calls = []
        self.closed = False

    def post(self, url, json=None, headers=None):
        self.calls.append({"url": url, "json": json, "headers": headers})
        assert self._scripted_calls, "Unexpected extra HTTP call"
        expected_suffix, response = self._scripted_calls.pop(0)
        assert url.endswith(expected_suffix)
        return _FakeRequestContext(response)


@pytest.mark.asyncio
async def test_semantic_search_prefers_adhd_endpoint():
    client = ConPortClient(base_url="http://localhost:3004")
    client.session = _FakeSession(
        [
            (
                "/api/adhd/semantic-search",
                _FakeResponse(
                    200,
                    payload={"results": [{"id": "x1"}], "deprecated": False},
                ),
            )
        ]
    )

    result = await client.semantic_search(
        workspace_id="dopemux-mvp",
        query="bridge routing",
        top_k=3,
    )

    assert result["_endpoint_used"] == "/api/adhd/semantic-search"
    assert len(result["results"]) == 1
    assert len(client.session.calls) == 1


@pytest.mark.asyncio
async def test_semantic_search_falls_back_on_404():
    client = ConPortClient(base_url="http://localhost:3004")
    client.session = _FakeSession(
        [
            ("/api/adhd/semantic-search", _FakeResponse(404, text_body="not found")),
            ("/api/semantic-search", _FakeResponse(200, payload={"results": []})),
        ]
    )

    result = await client.semantic_search(
        workspace_id="dopemux-mvp",
        query="legacy path",
        top_k=2,
    )

    assert result["_endpoint_used"] == "/api/semantic-search"
    assert len(client.session.calls) == 2


@pytest.mark.asyncio
async def test_semantic_search_no_fallback_on_server_error():
    client = ConPortClient(base_url="http://localhost:3004")
    client.session = _FakeSession(
        [
            (
                "/api/adhd/semantic-search",
                _FakeResponse(500, text_body="internal error"),
            )
        ]
    )

    result = await client.semantic_search(
        workspace_id="dopemux-mvp",
        query="should fail fast",
        top_k=1,
    )

    assert "error" in result
    assert result.get("endpoint") == "/api/adhd/semantic-search"
    assert len(client.session.calls) == 1
