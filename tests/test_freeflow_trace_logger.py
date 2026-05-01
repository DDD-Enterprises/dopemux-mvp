from __future__ import annotations

import asyncio
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from dopemux.freeflow import FreeflowQuotaExceeded  # noqa: E402
from dopemux.litellm_trace_logger import (  # noqa: E402
    LOG_PATH_ENV,
    DopemuxLiteLLMTraceLogger,
)


def _freeflow_kwargs() -> dict:
    return {
        "model": "gemini/gemini-2.5-flash-lite",
        "messages": [{"role": "user", "content": "private test prompt"}],
        "metadata": {"request_id": "req-1"},
        "model_info": {
            "freeflow_provider": "gemini",
            "freeflow_model": "gemini-2.5-flash-lite",
            "freeflow_bucket_id": "gemini:gemini-2.5-flash-lite",
            "quota_bucket": "gemini:gemini-2.5-flash-lite",
            "freeflow_limits": {"rpm": 2, "tpm": 10000},
            "selected_fallback_tier": "generated",
        },
    }


def _paid_cap_kwargs() -> dict:
    return {
        "model": "gemini/gemini-2.5-flash-lite-preview-09-2025",
        "messages": [{"role": "user", "content": "paid cap test prompt"}],
        "metadata": {
            "request_id": "req-paid-1",
            "estimated_input_tokens": 1000,
            "estimated_output_tokens": 1000,
        },
        "model_info": {
            "freeflow_provider": "gemini_paid_cap",
            "freeflow_model": "gemini-flash-lite-preview-paid-cap",
            "freeflow_bucket_id": (
                "gemini_paid_cap:gemini-flash-lite-preview-paid-cap"
            ),
            "quota_bucket": "gemini_paid_cap:gemini-flash-lite-preview-paid-cap",
            "freeflow_paid": True,
            "freeflow_pricing": {
                "input_usd_per_million": 0.10,
                "output_usd_per_million": 0.40,
            },
            "freeflow_paid_cap": {
                "enabled": True,
                "daily_usd": 0.5,
                "monthly_usd": 5.0,
                "day_reset": "utc_midnight",
            },
            "selected_fallback_tier": "paid_cap",
        },
    }


def test_trace_logger_pre_call_adds_freeflow_decision_metadata(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("DOPEMUX_FREEFLOW_LEDGER", str(tmp_path / "quota.sqlite"))
    logger = DopemuxLiteLLMTraceLogger()

    result = asyncio.run(
        logger.async_pre_call_deployment_hook(_freeflow_kwargs(), call_type=None)
    )

    assert result is not None
    metadata = result["metadata"]
    assert metadata["freeflow_provider"] == "gemini"
    assert metadata["freeflow_model"] == "gemini-2.5-flash-lite"
    assert metadata["quota_bucket"] == "gemini:gemini-2.5-flash-lite"
    assert metadata["route_decision_id"]

    with sqlite3.connect(tmp_path / "quota.sqlite") as conn:
        row = conn.execute("SELECT decision, reason FROM route_decisions").fetchone()

    assert row == ("selected", "strict_free_pre_call_admitted")


def test_trace_logger_blocks_sensitive_hosted_route(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("DOPEMUX_FREEFLOW_LEDGER", str(tmp_path / "quota.sqlite"))
    logger = DopemuxLiteLLMTraceLogger()
    kwargs = _freeflow_kwargs()
    kwargs["metadata"]["sensitivity_class"] = "memory"

    try:
        asyncio.run(logger.async_pre_call_deployment_hook(kwargs, call_type=None))
    except FreeflowQuotaExceeded as exc:
        assert exc.reason == "sensitive_hosted_route_blocked"
    else:
        raise AssertionError("expected strict-free privacy block")

    with sqlite3.connect(tmp_path / "quota.sqlite") as conn:
        row = conn.execute("SELECT decision, reason FROM route_decisions").fetchone()

    assert row == ("blocked", "sensitive_hosted_route_blocked")


def test_trace_logger_records_usage_without_prompt_content(
    tmp_path: Path, monkeypatch
) -> None:
    ledger_path = tmp_path / "quota.sqlite"
    log_path = tmp_path / "events.jsonl"
    monkeypatch.setenv("DOPEMUX_FREEFLOW_LEDGER", str(ledger_path))
    monkeypatch.setenv(LOG_PATH_ENV, str(log_path))
    logger = DopemuxLiteLLMTraceLogger()
    kwargs = asyncio.run(
        logger.async_pre_call_deployment_hook(_freeflow_kwargs(), call_type=None)
    )
    response = SimpleNamespace(
        id="upstream-1",
        model="gemini/gemini-2.5-flash-lite",
        usage=SimpleNamespace(
            prompt_tokens=12,
            completion_tokens=7,
            total_tokens=19,
            reasoning_tokens=None,
            cached_tokens=None,
        ),
        choices=[SimpleNamespace(finish_reason="stop")],
    )

    logger.log_success_event(
        kwargs,
        response,
        datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc),
        datetime(2026, 5, 1, 12, 0, 1, tzinfo=timezone.utc),
    )

    payload = json.loads(log_path.read_text(encoding="utf-8").splitlines()[-1])
    serialized = json.dumps(payload, sort_keys=True)
    assert payload["route_decision_id"] == kwargs["metadata"]["route_decision_id"]
    assert payload["quota_bucket"] == "gemini:gemini-2.5-flash-lite"
    assert "private test prompt" not in serialized

    with sqlite3.connect(ledger_path) as conn:
        row = conn.execute("""
            SELECT requests, input_tokens, output_tokens, status
            FROM usage_events
            """).fetchone()

    assert row == (1, 12, 7, "completed")


def test_trace_logger_reserves_paid_cap_spend(tmp_path: Path, monkeypatch) -> None:
    ledger_path = tmp_path / "quota.sqlite"
    monkeypatch.setenv("DOPEMUX_FREEFLOW_LEDGER", str(ledger_path))
    logger = DopemuxLiteLLMTraceLogger()

    kwargs = asyncio.run(
        logger.async_pre_call_deployment_hook(_paid_cap_kwargs(), call_type=None)
    )

    assert kwargs["metadata"]["route_decision_id"]
    assert kwargs["metadata"]["estimated_cost_usd"] == 0.0005
    with sqlite3.connect(ledger_path) as conn:
        row = conn.execute("""
            SELECT provider, model_name, cost_usd, status
            FROM spend_events
            """).fetchone()

    assert row == (
        "gemini_paid_cap",
        "gemini-flash-lite-preview-paid-cap",
        0.0005,
        "reserved",
    )


def test_trace_logger_blocks_paid_cap_over_limit(
    tmp_path: Path, monkeypatch
) -> None:
    ledger_path = tmp_path / "quota.sqlite"
    monkeypatch.setenv("DOPEMUX_FREEFLOW_LEDGER", str(ledger_path))
    logger = DopemuxLiteLLMTraceLogger()
    kwargs = _paid_cap_kwargs()
    kwargs["model_info"]["freeflow_paid_cap"]["daily_usd"] = 0.0004

    try:
        asyncio.run(logger.async_pre_call_deployment_hook(kwargs, call_type=None))
    except FreeflowQuotaExceeded as exc:
        assert exc.reason == "daily_paid_cap_exhausted"
    else:
        raise AssertionError("expected paid cap block")

    with sqlite3.connect(ledger_path) as conn:
        spend_count = conn.execute("SELECT COUNT(*) FROM spend_events").fetchone()[0]
        decision = conn.execute(
            "SELECT decision, reason FROM route_decisions"
        ).fetchone()

    assert spend_count == 0
    assert decision == ("blocked", "daily_paid_cap_exhausted")
