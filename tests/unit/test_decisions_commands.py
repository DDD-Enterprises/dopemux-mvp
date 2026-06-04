from __future__ import annotations

from typing import Any

import pytest
import requests
from click.testing import CliRunner

from dopemux.commands import decisions_commands


class FakeResponse:
    def __init__(self, payload: dict[str, Any], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            exc = requests.HTTPError(f"HTTP {self.status_code}")
            exc.response = self
            raise exc


def test_decisions_list_uses_conport_http_port_and_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    recorded: dict[str, Any] = {}

    def fake_get(url: str, *, params: dict[str, Any], timeout: int) -> FakeResponse:
        recorded.update({"url": url, "params": params, "timeout": timeout})
        return FakeResponse({
            "decisions": [
                {
                    "id": "decision-1",
                    "summary": "Choose tracked wrapper",
                    "rationale": "Fresh clones need tracked files",
                    "created_at": "2026-06-01T00:00:00Z",
                }
            ]
        })

    monkeypatch.delenv("CONPORT_URL", raising=False)
    monkeypatch.setenv("CONPORT_HTTP_PORT", "3999")
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ID", "workspace-a")
    monkeypatch.setattr(decisions_commands.requests, "get", fake_get)

    result = CliRunner().invoke(decisions_commands.decisions, ["list", "--limit", "50"])

    assert result.exit_code == 0, result.output
    assert recorded == {
        "url": "http://localhost:3999/api/decisions",
        "params": {"workspace_id": "workspace-a", "limit": 50},
        "timeout": 10,
    }


def test_decisions_show_accepts_string_decision_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        decisions_commands,
        "_get_decisions",
        lambda workspace_id, limit=20: [
            {
                "id": "f8f12c3e-8421-46b9-b7c7-4a9128f21355",
                "summary": "Keep append-only decisions",
                "rationale": "Auditability",
                "alternatives": [],
                "tags": [],
                "created_at": "2026-06-01T00:00:00Z",
            }
        ],
    )

    result = CliRunner().invoke(
        decisions_commands.decisions,
        ["show", "f8f12c3e-8421-46b9-b7c7-4a9128f21355"],
    )

    assert result.exit_code == 0, result.output
    assert "Keep append-only decisions" in result.output


def test_decisions_query_fetches_lookup_window_and_limits_output(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, int]] = []

    def fake_get_decisions(workspace_id: str, limit: int = 20) -> list[dict[str, Any]]:
        calls.append((workspace_id, limit))
        return [
            {"id": "decision-1", "summary": "alpha choice", "rationale": "", "created_at": "now"},
            {"id": "decision-2", "summary": "beta choice", "rationale": "alpha detail", "created_at": "now"},
        ]

    monkeypatch.setenv("DOPEMUX_WORKSPACE_ID", "workspace-a")
    monkeypatch.setattr(decisions_commands, "_get_decisions", fake_get_decisions)

    result = CliRunner().invoke(decisions_commands.decisions, ["query", "alpha", "--limit", "1"])

    assert result.exit_code == 0, result.output
    assert calls == [("workspace-a", decisions_commands.DEFAULT_DECISION_LOOKUP_LIMIT)]


def test_decisions_review_validates_target_and_reads_nested_response_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorded: dict[str, Any] = {}

    monkeypatch.setenv("DOPEMUX_WORKSPACE_ID", "workspace-a")
    monkeypatch.setattr(
        decisions_commands,
        "_get_decisions",
        lambda workspace_id, limit=20: [{"id": "decision-1", "summary": "Original"}],
    )

    def fake_post(url: str, *, json: dict[str, Any], timeout: int) -> FakeResponse:
        recorded.update({"url": url, "json": json, "timeout": timeout})
        return FakeResponse({"status": "logged", "decision": {"id": "decision-review"}})

    monkeypatch.setattr(decisions_commands.requests, "post", fake_post)

    result = CliRunner().invoke(
        decisions_commands.decisions,
        ["review", "decision-1", "--note", "Still valid"],
    )

    assert result.exit_code == 0, result.output
    assert recorded["json"]["summary"] == "[Review of decision-1] Still valid"
    assert "decision-review" in result.output


def test_decisions_review_rejects_missing_target_before_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(decisions_commands, "_get_decisions", lambda workspace_id, limit=20: [])
    monkeypatch.setattr(
        decisions_commands.requests,
        "post",
        lambda *args, **kwargs: pytest.fail("review must not write without target decision"),
    )

    result = CliRunner().invoke(
        decisions_commands.decisions,
        ["review", "missing-id", "--note", "Do not write"],
    )

    assert result.exit_code == 1


def test_decisions_update_outcome_references_target_and_reads_nested_response_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorded: dict[str, Any] = {}

    monkeypatch.setattr(
        decisions_commands,
        "_get_decisions",
        lambda workspace_id, limit=20: [{"id": "decision-1", "summary": "Original"}],
    )

    def fake_post(url: str, *, json: dict[str, Any], timeout: int) -> FakeResponse:
        recorded.update({"url": url, "json": json, "timeout": timeout})
        return FakeResponse({"status": "logged", "decision": {"id": "decision-outcome"}})

    monkeypatch.setattr(decisions_commands.requests, "post", fake_post)

    result = CliRunner().invoke(
        decisions_commands.decisions,
        ["update-outcome", "decision-1", "--outcome", "It worked"],
    )

    assert result.exit_code == 0, result.output
    assert recorded["json"]["summary"] == "[Outcome of decision-1] It worked"
    assert "references decision-1" in result.output
    assert "decision-outcome" in result.output


def test_get_decisions_distinguishes_conport_rejection(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, *, params: dict[str, Any], timeout: int) -> FakeResponse:
        return FakeResponse({"error": "bad workspace"}, status_code=403)

    monkeypatch.setattr(decisions_commands.requests, "get", fake_get)

    assert decisions_commands._get_decisions("blocked-workspace", limit=5) == []
