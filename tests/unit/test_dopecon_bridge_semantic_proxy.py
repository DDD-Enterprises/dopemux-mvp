import importlib.util
import json
import sys
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "services"
    / "dopecon-bridge"
    / "dopecon_bridge"
    / "conport_semantic_proxy.py"
)
MODULE_DIR = MODULE_PATH.parent

if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

SPEC = importlib.util.spec_from_file_location("conport_semantic_proxy_for_tests", MODULE_PATH)
PROXY_MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(PROXY_MODULE)


class _FakeLogger:
    def __init__(self):
        self.messages = []

    def warning(self, message, *args):
        self.messages.append((message, args))


class _FakeResponse:
    def __init__(self, status: int, payload=None, text_body: str = ""):
        self.status = status
        self._payload = payload
        self._text_body = text_body

    async def text(self) -> str:
        if self._payload is not None:
            return json.dumps(self._payload)
        return self._text_body


class _FakeContextManager:
    def __init__(self, response: _FakeResponse):
        self.response = response

    async def __aenter__(self):
        return self.response

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeSession:
    def __init__(self, response_plan):
        self.response_plan = response_plan
        self.calls = []

    def post(self, url, json):
        self.calls.append((url, json))
        queue = self.response_plan[url]
        if not queue:
            raise AssertionError(f"No response queued for URL: {url}")
        return _FakeContextManager(queue.pop(0))


@pytest.mark.asyncio
async def test_proxy_falls_back_on_404():
    base_url = "http://conport:3020"
    primary = f"{base_url}/api/adhd/semantic-search"
    legacy = f"{base_url}/api/semantic-search"
    session = _FakeSession(
        {
            primary: [_FakeResponse(404, text_body="not found")],
            legacy: [_FakeResponse(200, payload={"results": [{"id": "d1"}]})],
        }
    )
    logger = _FakeLogger()

    result = await PROXY_MODULE.run_semantic_search_with_fallback(
        session=session,
        base_url=base_url,
        payload={"workspace_id": "/tmp/workspace", "query_text": "auth"},
        logger=logger,
    )

    assert result["results"] == [{"id": "d1"}]
    assert result["endpoint"] == "/api/semantic-search"
    assert len(session.calls) == 2
    assert logger.messages, "fallback warning should be emitted"


@pytest.mark.asyncio
async def test_proxy_does_not_fallback_on_primary_500():
    base_url = "http://conport:3020"
    primary = f"{base_url}/api/adhd/semantic-search"
    legacy = f"{base_url}/api/semantic-search"
    session = _FakeSession(
        {
            primary: [_FakeResponse(500, text_body="upstream failed")],
            legacy: [_FakeResponse(200, payload={"results": [{"id": "unused"}]})],
        }
    )

    with pytest.raises(RuntimeError) as exc:
        await PROXY_MODULE.run_semantic_search_with_fallback(
            session=session,
            base_url=base_url,
            payload={"workspace_id": "/tmp/workspace", "query_text": "auth"},
            logger=_FakeLogger(),
        )

    assert "/api/adhd/semantic-search returned 500" in str(exc.value)
    assert len(session.calls) == 1
    assert session.calls[0][0] == primary


@pytest.mark.asyncio
async def test_proxy_maps_legacy_result_key_to_results():
    base_url = "http://conport:3020"
    primary = f"{base_url}/api/adhd/semantic-search"
    session = _FakeSession(
        {
            primary: [_FakeResponse(200, payload={"result": [{"id": "d2"}]})],
            f"{base_url}/api/semantic-search": [],
        }
    )

    result = await PROXY_MODULE.run_semantic_search_with_fallback(
        session=session,
        base_url=base_url,
        payload={"workspace_id": "/tmp/workspace", "query_text": "auth"},
        logger=_FakeLogger(),
    )

    assert result["results"] == [{"id": "d2"}]
    assert result["endpoint"] == "/api/adhd/semantic-search"
