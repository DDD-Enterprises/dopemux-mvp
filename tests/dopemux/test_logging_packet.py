"""Tests for packet-oriented logging helpers."""

import pytest

from src.dopemux.logging import bind_log_context, current_log_context, reset_log_context
from src.dopemux.logging.packet import (
    build_datadog_series,
    build_prometheus_export,
    detect_level,
    normalize_error_signature,
    summarize_service_lines,
)


def test_bind_and_reset_log_context():
    """Context binding should be reversible via token reset."""
    before = current_log_context()
    token = bind_log_context(service="svc", request_id="req-1")

    try:
        current = current_log_context()
        assert current["service"] == "svc"
        assert current["request_id"] == "req-1"
    finally:
        reset_log_context(token)

    assert current_log_context() == before


def test_error_signature_normalization_removes_volatile_tokens():
    line = (
        "2026-02-06T12:00:00Z ERROR request_id=4ca6372f-b3aa-4c7f-8884-4f2f8f22d60e "
        "failed after 3000 ms with trace 0x9ef2"
    )
    signature = normalize_error_signature(line)
    assert "4ca6372f-b3aa-4c7f-8884-4f2f8f22d60e" not in signature
    assert "<uuid>" in signature
    assert "<num>" in signature
    assert "<hex>" in signature


def test_service_summary_counts_error_and_warning_lines():
    lines = [
        "2026-02-06T12:00:00Z INFO startup complete",
        "2026-02-06T12:00:01Z WARNING retrying operation",
        "2026-02-06T12:00:02Z ERROR database timeout after 1200 ms",
        "2026-02-06T12:00:03Z CRITICAL redis unavailable",
    ]
    summary = summarize_service_lines("example", lines)
    assert summary["total_lines"] == 4
    assert summary["counts"]["info"] == 1
    assert summary["counts"]["warning"] == 1
    assert summary["counts"]["error"] == 1
    assert summary["counts"]["critical"] == 1
    assert summary["error_lines"] == 2
    assert summary["warning_lines"] == 1
    assert summary["top_signatures"]


def test_metrics_exports_include_packet_and_service_dimensions():
    summary = {
        "svc-a": {"counts": {"info": 10, "error": 2}, "error_lines": 2},
        "svc-b": {"counts": {"warning": 3}, "error_lines": 0},
    }
    health = {"svc-a": {"status": "ok"}, "svc-b": {"status": "fail"}}
    metrics = {"svc-a": {"ok": True}, "svc-b": {"ok": False}}

    prom = build_prometheus_export(
        packet_id="pkt-1",
        summary_by_service=summary,
        health_status=health,
        metrics_status=metrics,
    )
    assert 'packet_id="pkt-1"' in prom
    assert 'service="svc-a"' in prom
    assert "dopemux_task_packet_health_status" in prom

    datadog = build_datadog_series(packet_id="pkt-1", summary_by_service=summary)
    assert "series" in datadog
    assert datadog["series"]
    assert any("packet_id:pkt-1" in point["tags"] for point in datadog["series"])


@pytest.mark.parametrize(
    "line,expected",
    [
        ("CRITICAL: everything is on fire", "critical"),
        ("fatal system error", "critical"),
        ("An error occurred here", "error"),
        ("Exception in thread main", "error"),
        ("Traceback (most recent call last):", "error"),
        ("failed to connect to database", "error"),
        ("failure in component A", "error"),
        ("kernel panic!", "error"),
        ("RuntimeError: something went wrong", "error"),
        ("ValueERROR: bad value", "error"),
        ("WARNING: disk space low", "warning"),
        ("warn: possible issue", "warning"),
        ("info: service started", "info"),
        ("debug: internal state is 42", "debug"),
        ("just some random text", "unknown"),
        ("this is an informed decision", "unknown"),
        ("debugging is fun", "unknown"),
        ("information is power", "unknown"),
        ("it failed", "error"),
        ("ConnectionError", "error"),
        # New test cases below
        ("Critical Error: Database down", "critical"),  # Priority: Critical > Error
        ("Error: Critical failure", "critical"),  # Priority: Critical > Error (regex order)
        ("Warning: This is an error", "error"),  # Priority: Error > Warning
        ("Info: but there was a warning", "warning"),  # Priority: Warning > Info
        ("Debug info", "info"),  # Priority: Info > Debug
        ("erroring", "unknown"),  # Word boundary check
        ("failures", "unknown"),  # Word boundary check
        ("warned", "unknown"),  # Word boundary check
        ("fail", "error"),  # "fail" should match
        ("failed", "error"),  # "failed" should match
        ("failure", "error"),  # "failure" should match
    ],
)
def test_detect_level(line: str, expected: str):
    """It should correctly detect log levels from various string inputs."""
    assert detect_level(line) == expected
