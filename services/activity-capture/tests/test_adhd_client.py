from unittest.mock import AsyncMock

import pytest

from adhd_client import ADHDEngineClient, build_activity_payload


class FakeResponse:
    def __init__(self, status=200, payload=None):
        self.status = status
        self.payload = payload or {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def json(self):
        return self.payload


class FakeSession:
    def __init__(self):
        self.put_calls = []

    def put(self, url, json):
        self.put_calls.append((url, json))
        return FakeResponse(status=200)


@pytest.mark.asyncio
async def test_send_activity_data_uses_put_and_engine_payload_shape():
    client = ADHDEngineClient(
        base_url="http://adhd-engine:8095",
        user_id="default",
        api_key="secret-key",
    )
    session = FakeSession()
    client.session = session

    await client.send_activity_data({
        "completion_rate": 0.75,
        "context_switches": 2,
        "break_compliance": 0.5,
        "minutes_since_break": 18,
    })

    assert session.put_calls == [(
        "http://adhd-engine:8095/api/v1/activity/default",
        {
            "user_id": "default",
            "completion_rate": 0.75,
            "context_switches": 2,
            "break_compliance": 0.5,
            "minutes_since_break": 18,
        },
    )]


@pytest.mark.asyncio
async def test_initialize_attaches_api_key_headers():
    client = ADHDEngineClient(
        base_url="http://adhd-engine:8095",
        user_id="default",
        api_key="secret-key",
    )

    await client.initialize()

    assert client.session is not None
    assert client.headers["X-API-Key"] == "secret-key"


def test_build_activity_payload_ignores_content_bearing_fields():
    payload = build_activity_payload("default", {
        "completion_rate": 0.25,
        "context_switches": 3,
        "break_compliance": 0.5,
        "minutes_since_break": 12,
        "filename": "src/private_prompt.py",
        "prompt": "private prompt text",
        "code": "def leaked(): pass",
        "messages": [{"content": "secret message"}],
    })

    assert payload == {
        "user_id": "default",
        "completion_rate": 0.25,
        "context_switches": 3,
        "break_compliance": 0.5,
        "minutes_since_break": 12,
    }
    serialized = repr(payload)
    for forbidden in ["src/private_prompt.py", "private prompt text", "def leaked", "secret message"]:
        assert forbidden not in serialized
