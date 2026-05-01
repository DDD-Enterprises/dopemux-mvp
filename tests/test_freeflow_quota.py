from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from dopemux.freeflow import FreeflowQuotaLedger


def test_quota_ledger_creates_required_tables(tmp_path: Path) -> None:
    ledger = FreeflowQuotaLedger(tmp_path / "quota.sqlite")

    with sqlite3.connect(ledger.path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    assert {
        "usage_events",
        "route_decisions",
        "cooldowns",
        "bucket_state",
    }.issubset(tables)


def test_record_usage_blocks_exhausted_request_window(tmp_path: Path) -> None:
    ledger = FreeflowQuotaLedger(tmp_path / "quota.sqlite")
    when = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)

    ledger.record_usage(
        provider="gemini",
        model_name="gemini-2.5-flash-lite",
        model_id="gemini/gemini-2.5-flash-lite",
        bucket_id="gemini:gemini-2.5-flash-lite",
        input_tokens=20,
        output_tokens=10,
        now=when,
    )

    result = ledger.check_quota(
        provider="gemini",
        model_name="gemini-2.5-flash-lite",
        bucket_id="gemini:gemini-2.5-flash-lite",
        limits={"rpm": 1, "tpm": 1000},
        input_tokens=1,
        output_tokens=1,
        now=when,
    )

    assert result.allowed is False
    assert result.reason == "rpm_exhausted"
    assert result.reset_at is not None


def test_header_ingestion_creates_auditable_cooldown(tmp_path: Path) -> None:
    ledger = FreeflowQuotaLedger(tmp_path / "quota.sqlite")
    when = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)

    cooldown = ledger.ingest_response_headers(
        provider="groq",
        model_name="groq-llama-3.1-8b-instant",
        bucket_id="groq:groq-llama-3.1-8b-instant",
        headers={"retry-after": "2"},
        status_code=429,
        now=when,
    )

    assert cooldown is not None
    assert cooldown["reason"] == "rate_limited"
    assert ledger.active_cooldown(
        "groq",
        "groq-llama-3.1-8b-instant",
        "groq:groq-llama-3.1-8b-instant",
        now=when,
    )


def test_402_header_ingestion_marks_insufficient_credits(tmp_path: Path) -> None:
    ledger = FreeflowQuotaLedger(tmp_path / "quota.sqlite")
    when = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)

    cooldown = ledger.ingest_response_headers(
        provider="openrouter_free",
        model_name="openrouter-free-router",
        bucket_id="openrouter_free:openrouter-free-router",
        headers={"retry-after": "1"},
        status_code=402,
        now=when,
    )

    assert cooldown is not None
    assert cooldown["reason"] == "insufficient_credits"


def test_pacific_midnight_daily_reset_math(tmp_path: Path) -> None:
    ledger = FreeflowQuotaLedger(tmp_path / "quota.sqlite")
    when = datetime(2026, 5, 1, 8, 30, tzinfo=timezone.utc)

    result = ledger.check_quota(
        provider="gemini",
        model_name="gemini-2.5-flash-lite",
        bucket_id="gemini:gemini-2.5-flash-lite",
        limits={"rpd": 0, "day_reset": "pacific_midnight"},
        input_tokens=1,
        output_tokens=1,
        now=when,
    )

    assert result.allowed is True
    ledger.record_usage(
        provider="gemini",
        model_name="gemini-2.5-flash-lite",
        model_id="gemini/gemini-2.5-flash-lite",
        bucket_id="gemini:gemini-2.5-flash-lite",
        input_tokens=1,
        output_tokens=1,
        now=when,
    )
    exhausted = ledger.check_quota(
        provider="gemini",
        model_name="gemini-2.5-flash-lite",
        bucket_id="gemini:gemini-2.5-flash-lite",
        limits={"rpd": 1, "day_reset": "pacific_midnight"},
        input_tokens=1,
        output_tokens=1,
        now=when,
    )

    assert exhausted.allowed is False
    assert exhausted.reason == "rpd_exhausted"
    assert exhausted.reset_at == "2026-05-02T07:00:00Z"


def test_route_decisions_are_append_only(tmp_path: Path) -> None:
    ledger = FreeflowQuotaLedger(tmp_path / "quota.sqlite")

    first = ledger.record_route_decision(
        {
            "decision": "selected",
            "reason": "test",
            "sensitivity_class": "non_sensitive",
            "provider": "gemini",
            "model_name": "gemini-2.5-flash-lite",
            "model_id": "gemini/gemini-2.5-flash-lite",
        }
    )
    second = ledger.record_route_decision(
        {
            "decision": "queued",
            "reason": "quota",
            "sensitivity_class": "non_sensitive",
        }
    )

    with sqlite3.connect(ledger.path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM route_decisions").fetchone()[0]

    assert first != second
    assert count == 2
