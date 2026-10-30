"""Tests for the read-only ``dopemux adhd status`` command."""

import json
from typing import Any, Callable, Dict, Tuple, Union

import pytest
import requests
from click.testing import CliRunner

from dopemux.commands import adhd_commands
from dopemux.commands.adhd_commands import (
    DEFAULT_ADHD_ENGINE_PORT,
    EXIT_CODES,
    adhd,
    resolve_engine_url,
)

MAIN_STATE = {
    "energy": "medium",
    "attention": "focused",
    "session_minutes": 0,
    "user_id": "op",
}
# PR #1472 at ee00d3655 adds *_level / *_state aliases beside the originals.
PULSE_STATE = {
    **MAIN_STATE,
    "energy_level": "medium",
    "attention_state": "focused",
}
FALLBACK_HEALTH = {
    "overall_status": "🟡 Degraded",
    "service": "adhd-engine",
    "mode": "fallback",
    "startup_error": "x",
}
NORMAL_HEALTH = {"overall_status": "🟢 Healthy", "components": {}}

Reply = Union[Tuple[int, Any], Exception]


class FakeResponse:
    def __init__(self, status_code: int, body: Any) -> None:
        self.status_code = status_code
        self._body = body
        self.text = body if isinstance(body, str) else json.dumps(body)

    def json(self) -> Any:
        if isinstance(self._body, str):
            raise ValueError("not json")
        return self._body


def fake_get(routes: Dict[str, Reply]) -> Callable[..., FakeResponse]:
    """Build a ``requests.get`` stand-in keyed by URL suffix."""

    def _get(url: str, *args: Any, **kwargs: Any) -> FakeResponse:
        for suffix, reply in routes.items():
            if url.endswith(suffix):
                if isinstance(reply, Exception):
                    raise reply
                return FakeResponse(*reply)
        raise AssertionError(f"unexpected URL {url}")

    return _get


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "DOPEMUX_ADHD_ENGINE_BASE_URL",
        "DOPEMUX_ADHD_ENGINE_PORT",
        "ADHD_ENGINE_PORT",
    ):
        monkeypatch.delenv(name, raising=False)


def run_status(
    monkeypatch: pytest.MonkeyPatch, routes: Dict[str, Reply], *args: str
) -> Any:
    monkeypatch.setattr(adhd_commands.requests, "get", fake_get(routes))
    return CliRunner().invoke(adhd, ["status", *args])


def test_resolve_order(capsys: pytest.CaptureFixture) -> None:
    env = {
        "DOPEMUX_ADHD_ENGINE_BASE_URL": "http://base:1",
        "DOPEMUX_ADHD_ENGINE_PORT": "2",
        "ADHD_ENGINE_PORT": "3",
    }
    assert resolve_engine_url("http://cli:9", env) == ("http://cli:9", "--url")
    assert resolve_engine_url(None, env) == (
        "http://base:1",
        "DOPEMUX_ADHD_ENGINE_BASE_URL",
    )
    del env["DOPEMUX_ADHD_ENGINE_BASE_URL"]
    assert resolve_engine_url(None, env) == (
        "http://127.0.0.1:2",
        "DOPEMUX_ADHD_ENGINE_PORT",
    )
    del env["DOPEMUX_ADHD_ENGINE_PORT"]
    assert resolve_engine_url(None, env) == (
        "http://127.0.0.1:3",
        "ADHD_ENGINE_PORT",
    )
    assert resolve_engine_url(None, {}) == (
        f"http://127.0.0.1:{DEFAULT_ADHD_ENGINE_PORT}",
        "registry-default",
    )
    assert resolve_engine_url(None, {}) == (
        "http://127.0.0.1:3025",
        "registry-default",
    )
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize("bad", ["abc", "0", "65536", "-1", "", "30.5"])
def test_resolve_ignores_invalid_port_env_with_warning(
    bad: str, capsys: pytest.CaptureFixture
) -> None:
    env = {"DOPEMUX_ADHD_ENGINE_PORT": bad, "ADHD_ENGINE_PORT": "4000"}
    assert resolve_engine_url(None, env) == (
        "http://127.0.0.1:4000",
        "ADHD_ENGINE_PORT",
    )
    assert "DOPEMUX_ADHD_ENGINE_PORT" in capsys.readouterr().err


def test_resolve_invalid_port_falls_back_to_default(
    capsys: pytest.CaptureFixture,
) -> None:
    assert resolve_engine_url(None, {"ADHD_ENGINE_PORT": "nope"}) == (
        "http://127.0.0.1:3025",
        "registry-default",
    )
    assert "ADHD_ENGINE_PORT" in capsys.readouterr().err


def test_status_ok_main_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    result = run_status(
        monkeypatch,
        {"/api/v1/state": (200, MAIN_STATE), "/health": (200, NORMAL_HEALTH)},
    )
    assert result.exit_code == EXIT_CODES["ok"] == 0
    assert result.output.strip() == (
        "ADHD engine ok (http://127.0.0.1:3025, registry-default): "
        "energy medium, attention focused"
    )


def test_status_ok_pulse_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    result = run_status(
        monkeypatch,
        {"/api/v1/state": (200, PULSE_STATE), "/health": (200, NORMAL_HEALTH)},
        "--json",
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status"] == "ok"
    assert data["energy"] == "medium"
    assert data["engine_mode"] == "normal"


def test_aliases_win_over_originals(monkeypatch: pytest.MonkeyPatch) -> None:
    state = {
        **MAIN_STATE,
        "energy_level": "high",
        "attention_state": "scattered",
    }
    result = run_status(
        monkeypatch,
        {"/api/v1/state": (200, state), "/health": (200, NORMAL_HEALTH)},
        "--json",
    )
    data = json.loads(result.output)
    assert (data["energy"], data["attention"]) == ("high", "scattered")


def test_status_degraded_on_fallback_health(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = run_status(
        monkeypatch,
        {
            "/api/v1/state": (200, MAIN_STATE),
            "/health": (200, FALLBACK_HEALTH),
        },
    )
    assert result.exit_code == EXIT_CODES["degraded"] == 3
    assert "ADHD engine degraded" in result.output
    assert "engine running on its fallback class" in result.output

    result = run_status(
        monkeypatch,
        {
            "/api/v1/state": (200, MAIN_STATE),
            "/health": (200, FALLBACK_HEALTH),
        },
        "--json",
    )
    data = json.loads(result.output)
    assert data["status"] == "degraded"
    assert data["engine_mode"] == "fallback"


def test_status_health_missing_is_unknown_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = run_status(
        monkeypatch,
        {
            "/api/v1/state": (200, MAIN_STATE),
            "/health": (404, {"detail": "nope"}),
        },
        "--json",
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status"] == "ok"
    assert data["engine_mode"] == "unknown"


def test_status_health_error_body_is_unknown_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error_health = {
        "overall_status": "🔴 Error",
        "error": "boom",
        "service": "adhd-engine",
    }
    result = run_status(
        monkeypatch,
        {"/api/v1/state": (200, MAIN_STATE), "/health": (200, error_health)},
        "--json",
    )
    assert json.loads(result.output)["engine_mode"] == "unknown"


def test_status_health_unreachable_is_unknown_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = run_status(
        monkeypatch,
        {
            "/api/v1/state": (200, MAIN_STATE),
            "/health": requests.Timeout("slow"),
        },
        "--json",
    )
    assert result.exit_code == 0
    assert json.loads(result.output)["engine_mode"] == "unknown"


def test_status_connection_refused_is_unreachable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = run_status(
        monkeypatch, {"/api/v1/state": requests.ConnectionError("refused")}
    )
    assert result.exit_code == EXIT_CODES["unreachable"] == 1
    assert "ADHD engine unreachable" in result.output


def test_status_timeout_is_unreachable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = run_status(monkeypatch, {"/api/v1/state": requests.Timeout("slow")})
    assert result.exit_code == 1
    assert "ADHD engine unreachable" in result.output


def test_status_non_2xx_is_unreachable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = run_status(monkeypatch, {"/api/v1/state": (500, {"detail": "err"})})
    assert result.exit_code == 1
    assert "ADHD engine unreachable" in result.output
    assert "500" in result.output


def test_status_non_json_body_is_malformed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = run_status(monkeypatch, {"/api/v1/state": (200, "<html>hi</html>")})
    assert result.exit_code == EXIT_CODES["malformed"] == 1
    assert "ADHD engine malformed" in result.output


def test_status_missing_energy_is_malformed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = run_status(monkeypatch, {"/api/v1/state": (200, {"attention": "focused"})})
    assert result.exit_code == 1
    assert "ADHD engine malformed" in result.output


def test_status_non_object_body_is_malformed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = run_status(monkeypatch, {"/api/v1/state": (200, ["energy"])})
    assert result.exit_code == 1
    assert "ADHD engine malformed" in result.output


def test_status_unknown_level_shown_verbatim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = {**MAIN_STATE, "energy": "recharging"}
    result = run_status(
        monkeypatch,
        {"/api/v1/state": (200, state), "/health": (200, NORMAL_HEALTH)},
    )
    assert result.exit_code == 0
    assert "recharging" in result.output
    assert "ADHD engine ok" in result.output


def test_session_minutes_hidden_when_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    routes: Dict[str, Reply] = {
        "/api/v1/state": (200, MAIN_STATE),
        "/health": (200, NORMAL_HEALTH),
    }
    assert "session" not in run_status(monkeypatch, routes).output

    routes["/api/v1/state"] = (200, {**MAIN_STATE, "session_minutes": 12})
    assert "session 12 min" in run_status(monkeypatch, routes).output


@pytest.mark.parametrize("minutes", [-3, 0])
def test_session_minutes_hidden_when_not_positive(
    monkeypatch: pytest.MonkeyPatch, minutes: int
) -> None:
    routes: Dict[str, Reply] = {
        "/api/v1/state": (200, {**MAIN_STATE, "session_minutes": minutes}),
        "/health": (200, NORMAL_HEALTH),
    }
    assert "session" not in run_status(monkeypatch, routes).output


def test_json_output_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    result = run_status(
        monkeypatch,
        {"/api/v1/state": (200, MAIN_STATE), "/health": (200, NORMAL_HEALTH)},
        "--json",
    )
    data = json.loads(result.output)
    assert list(data) == [
        "status",
        "url",
        "url_source",
        "engine_mode",
        "energy",
        "attention",
        "session_minutes",
        "detail",
    ]
    assert data["url_source"] == "registry-default"


def test_url_option_overrides_and_is_used(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = []
    base = fake_get(
        {"/api/v1/state": (200, MAIN_STATE), "/health": (200, NORMAL_HEALTH)}
    )

    def spy(url: str, *args: Any, **kwargs: Any) -> FakeResponse:
        seen.append(url)
        return base(url, *args, **kwargs)

    monkeypatch.setattr(adhd_commands.requests, "get", spy)
    result = CliRunner().invoke(adhd, ["status", "--url", "http://example.test:9/"])
    assert result.exit_code == 0
    assert seen == [
        "http://example.test:9/api/v1/state",
        "http://example.test:9/health",
    ]
    assert "--url" in result.output


def test_requests_use_two_second_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []
    base = fake_get(
        {"/api/v1/state": (200, MAIN_STATE), "/health": (200, NORMAL_HEALTH)}
    )

    def spy(url: str, *args: Any, **kwargs: Any) -> FakeResponse:
        calls.append((url, kwargs))
        return base(url, *args, **kwargs)

    monkeypatch.setattr(adhd_commands.requests, "get", spy)
    result = CliRunner().invoke(adhd, ["status"])
    assert result.exit_code == 0
    assert [url.rsplit("/", 1)[-1] for url, _ in calls] == ["state", "health"]
    assert [kwargs.get("timeout") for _, kwargs in calls] == [2.0, 2.0]


def _record_urls(monkeypatch: pytest.MonkeyPatch) -> list:
    seen: list = []
    base = fake_get(
        {"/api/v1/state": (200, MAIN_STATE), "/health": (200, NORMAL_HEALTH)}
    )

    def spy(url: str, *args: Any, **kwargs: Any) -> FakeResponse:
        seen.append(url)
        return base(url, *args, **kwargs)

    monkeypatch.setattr(adhd_commands.requests, "get", spy)
    return seen


def test_url_without_scheme_gets_http(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _record_urls(monkeypatch)
    result = CliRunner().invoke(adhd, ["status", "--url", "localhost:8095", "--json"])
    assert result.exit_code == 0
    assert seen == [
        "http://localhost:8095/api/v1/state",
        "http://localhost:8095/health",
    ]
    assert json.loads(result.output)["url"] == "http://localhost:8095"


def test_url_path_is_dropped(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _record_urls(monkeypatch)
    result = CliRunner().invoke(
        adhd, ["status", "--url", "https://example.test:9/some/path?x=1"]
    )
    assert result.exit_code == 0
    assert seen[0] == "https://example.test:9/api/v1/state"


@pytest.mark.parametrize(
    "bad",
    ["", "http://", "localhost:notaport", "localhost:99999", "ftp://host:1", "://x"],
)
def test_invalid_url_option_is_usage_error(
    monkeypatch: pytest.MonkeyPatch, bad: str
) -> None:
    seen = _record_urls(monkeypatch)
    result = CliRunner().invoke(adhd, ["status", "--url", bad])
    assert result.exit_code == 2
    assert "--url" in result.output
    assert seen == []


def test_invalid_base_url_env_is_skipped_with_warning(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    env = {
        "DOPEMUX_ADHD_ENGINE_BASE_URL": "localhost:notaport",
        "ADHD_ENGINE_PORT": "4000",
    }
    assert resolve_engine_url(None, env) == (
        "http://127.0.0.1:4000",
        "ADHD_ENGINE_PORT",
    )
    assert "DOPEMUX_ADHD_ENGINE_BASE_URL" in capsys.readouterr().err
    assert resolve_engine_url(None, {"DOPEMUX_ADHD_ENGINE_BASE_URL": "ftp://x"}) == (
        "http://127.0.0.1:3025",
        "registry-default",
    )
    assert "DOPEMUX_ADHD_ENGINE_BASE_URL" in capsys.readouterr().err


def test_base_url_env_without_scheme_is_normalized() -> None:
    env = {"DOPEMUX_ADHD_ENGINE_BASE_URL": "localhost:8095/health"}
    assert resolve_engine_url(None, env) == (
        "http://localhost:8095",
        "DOPEMUX_ADHD_ENGINE_BASE_URL",
    )


def test_human_line_stays_one_line_for_multiline_startup_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    health = {
        **FALLBACK_HEALTH,
        "startup_error": 'Traceback (most recent call last):\n  File "x"\n\n\tBoom',
    }
    routes: Dict[str, Reply] = {
        "/api/v1/state": (200, MAIN_STATE),
        "/health": (200, health),
    }
    result = run_status(monkeypatch, routes)
    assert result.exit_code == 3
    assert result.output.count("\n") == 1
    assert (
        'startup error: Traceback (most recent call last): File "x" Boom'
        in result.output
    )
    raw = json.loads(run_status(monkeypatch, routes, "--json").output)
    assert raw["detail"].endswith(health["startup_error"] + ")")
    assert "startup_error" not in raw


def test_human_line_truncates_long_engine_strings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    long = "x" * 500
    health = {**FALLBACK_HEALTH, "startup_error": long}
    state = {**MAIN_STATE, "energy": long}
    result = run_status(
        monkeypatch, {"/api/v1/state": (200, state), "/health": (200, health)}
    )
    assert result.output.count("\n") == 1
    assert long not in result.output
    assert result.output.count("\u2026") == 2
    assert "x" * 199 + "\u2026" in result.output
    assert "x" * 200 not in result.output
