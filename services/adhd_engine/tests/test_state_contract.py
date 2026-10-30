"""
Contract tests for GET /api/v1/state.

Consumers (TUI dashboard, check_energy.sh, adhd-tmux-status.sh, dope-memory
recap) read ``energy_level`` and ``attention_state``; the endpoint historically
served only ``energy`` and ``attention``. The endpoint must serve both
spellings with identical values, on the normal path and on the exception
fallback path.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from adhd_engine.main import app  # noqa: E402
from adhd_engine.models import AttentionState, EnergyLevel  # noqa: E402

STATE_KEYS = {
    "energy",
    "attention",
    "energy_level",
    "attention_state",
    "session_minutes",
    "user_id",
}


class SyncASGITestClient:
    """Minimal sync wrapper around httpx.AsyncClient + ASGI transport."""

    def __init__(self, app):
        self._transport = httpx.ASGITransport(app=app)
        self._client = httpx.AsyncClient(
            transport=self._transport,
            base_url="http://testserver",
        )

    def get(self, url, **kwargs):
        return asyncio.run(self._client.request("GET", url, **kwargs))

    def close(self):
        asyncio.run(self._client.aclose())


@pytest.fixture
def client():
    """FastAPI test client."""
    client = SyncASGITestClient(app)
    try:
        yield client
    finally:
        client.close()


@pytest.fixture
def state_engine():
    """Mock engine with a known state for ``test_user`` only."""
    mock_engine = MagicMock()
    mock_engine.current_energy_levels = {"test_user": EnergyLevel.HIGH}
    mock_engine.current_attention_states = {
        "test_user": AttentionState.SCATTERED,
    }
    mock_engine._session_start_times = {}
    return mock_engine


def get_state(client, user_id):
    return client.get("/api/v1/state", params={"user_id": user_id})


class _RaisingDict(dict):
    """dict whose lookups fail, to force the handler's exception fallback."""

    def get(self, *args, **kwargs):
        raise RuntimeError("simulated engine failure")


class TestStateContract:
    """GET /api/v1/state key contract."""

    def test_returns_all_six_keys(self, client, state_engine):
        with patch("adhd_engine.main.engine", state_engine):
            response = get_state(client, "test_user")

        assert response.status_code == 200
        data = response.json()
        assert STATE_KEYS <= set(data)
        assert data["user_id"] == "test_user"

    def test_alias_values_equal_primary_values(self, client, state_engine):
        with patch("adhd_engine.main.engine", state_engine):
            data = get_state(client, "test_user").json()

        assert data["energy"] == EnergyLevel.HIGH.value
        assert data["attention"] == AttentionState.SCATTERED.value
        assert data["energy_level"] == data["energy"]
        assert data["attention_state"] == data["attention"]

    def test_exception_fallback_all_six_keys(self, client, state_engine):
        state_engine.current_energy_levels = _RaisingDict()

        with patch("adhd_engine.main.engine", state_engine):
            response = get_state(client, "test_user")

        assert response.status_code == 200
        data = response.json()
        assert STATE_KEYS <= set(data)
        assert data["energy"] == "medium"
        assert data["attention"] == "focused"
        assert data["energy_level"] == data["energy"]
        assert data["attention_state"] == data["attention"]
        assert data["session_minutes"] == 0
        assert data["user_id"] == "test_user"

    def test_unknown_user_id_works(self, client, state_engine):
        with patch("adhd_engine.main.engine", state_engine):
            response = get_state(client, "nobody")

        assert response.status_code == 200
        data = response.json()
        assert STATE_KEYS <= set(data)
        assert data["user_id"] == "nobody"
        assert data["energy_level"] == data["energy"]
        assert data["attention_state"] == data["attention"]
