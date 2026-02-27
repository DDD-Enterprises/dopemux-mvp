"""Tests for core logging packet utilities."""

import pytest
from src.dopemux.core_logging.packet import (
    detect_level,
    extract_timestamp,
    normalize_error_signature,
    summarize_service_lines,
    log_line_to_json_record,
    build_prometheus_export,
    build_datadog_series,
)

def test_detect_level():
    assert detect_level("CRITICAL error occurred") == "critical"
    assert detect_level("FATAL system failure") == "critical"
    assert detect_level("Error: connection refused") == "error"
    assert detect_level("Exception: null pointer") == "error"
    assert detect_level("traceback (most recent call last)") == "error"
    assert detect_level("failed to load") == "error"
    assert detect_level("kernel panic") == "error"
    assert detect_level("ValueError: invalid input") == "error"
    assert detect_level("WARNING: disk full") == "warning"
    assert detect_level("warn: slow query") == "warning"
    assert detect_level("INFO: started") == "info"
    assert detect_level("debug: variable x=1") == "debug"
    assert detect_level("random log line") == "unknown"

def test_extract_timestamp():
    assert extract_timestamp("2023-10-27T10:00:00Z Log message") == "2023-10-27T10:00:00Z"
    assert extract_timestamp("2023-10-27 10:00:00.123 Log message") == "2023-10-27 10:00:00.123"
    assert extract_timestamp("No timestamp here") is None

def test_normalize_error_signature():
    line = "Error: user 12345 failed to login with uuid 550e8400-e29b-41d4-a716-446655440000 and hex 0x1A2B"
    signature = normalize_error_signature(line)
    assert "12345" not in signature
    assert "550e8400-e29b-41d4-a716-446655440000" not in signature
    assert "0x1A2B" not in signature
    assert "<num>" in signature
    assert "<uuid>" in signature
    assert "<hex>" in signature

    # Test stripping timestamp at start
    line_with_ts = "2023-10-27T10:00:00Z Error: connection timeout"
    assert normalize_error_signature(line_with_ts) == "error: connection timeout"

def test_summarize_service_lines():
    lines = [
        "2023-10-27T10:00:00Z INFO: start",
        "2023-10-27T10:00:01Z WARNING: low memory",
        "2023-10-27T10:00:02Z ERROR: database error 123",
        "2023-10-27T10:00:03Z ERROR: database error 456",
        "", # empty line
    ]
    summary = summarize_service_lines("test-service", lines)

    assert summary["service"] == "test-service"
    assert summary["total_lines"] == 4
    assert summary["counts"]["info"] == 1
    assert summary["counts"]["warning"] == 1
    assert summary["counts"]["error"] == 2
    assert summary["first_timestamp"] == "2023-10-27T10:00:00Z"
    assert summary["last_timestamp"] == "2023-10-27T10:00:03Z"
    assert summary["error_lines"] == 2
    assert summary["warning_lines"] == 1

    # Check signature grouping
    assert len(summary["top_signatures"]) == 1
    assert summary["top_signatures"][0]["count"] == 2
    assert "database error <num>" in summary["top_signatures"][0]["signature"]

def test_log_line_to_json_record():
    line = "2023-10-27T10:00:00Z ERROR: test error"
    record = log_line_to_json_record(
        service="test-service",
        line=line,
        packet_id="packet-123",
        line_number=42
    )

    assert record["packet_id"] == "packet-123"
    assert record["service"] == "test-service"
    assert record["line_number"] == 42
    assert record["timestamp"] == "2023-10-27T10:00:00Z"
    assert record["level"] == "error"
    assert record["message"] == line
    assert record["signature"] == "error: test error"

def test_build_prometheus_export():
    summary_by_service = {
        "service-a": {
            "counts": {"info": 10, "error": 2},
            "error_lines": 2
        }
    }
    health_status = {
        "service-a": {"status": "healthy"}
    }
    metrics_status = {
        "service-a": {"ok": True}
    }

    output = build_prometheus_export(
        packet_id="packet-123",
        summary_by_service=summary_by_service,
        health_status=health_status,
        metrics_status=metrics_status
    )

    assert 'dopemux_task_packet_info{packet_id="packet-123"} 1' in output
    assert 'dopemux_task_packet_log_lines_total{packet_id="packet-123",service="service-a",level="info"} 10' in output
    assert 'dopemux_task_packet_log_lines_total{packet_id="packet-123",service="service-a",level="error"} 2' in output
    assert 'dopemux_task_packet_health_status{packet_id="packet-123",service="service-a",status="healthy"} 1' in output
    assert 'dopemux_task_packet_metrics_endpoint_up{packet_id="packet-123",service="service-a"} 1' in output

def test_build_datadog_series():
    summary_by_service = {
        "service-a": {
            "counts": {"info": 10, "error": 2},
            "error_lines": 2
        }
    }
    timestamp = 1698400000

    result = build_datadog_series(
        packet_id="packet-123",
        summary_by_service=summary_by_service,
        timestamp=timestamp
    )

    series = result["series"]
    assert len(series) == 3 # info, error counts, error_lines total

    # Check for specific metrics
    info_metric = next(s for s in series if "level:info" in s["tags"])
    assert info_metric["metric"] == "dopemux.task_packet.log_lines"
    assert info_metric["points"][0] == [timestamp, 10.0]
    assert "packet_id:packet-123" in info_metric["tags"]

    error_metric = next(s for s in series if "level:error" in s["tags"])
    assert error_metric["metric"] == "dopemux.task_packet.log_lines"
    assert error_metric["points"][0] == [timestamp, 2.0]

    total_error_metric = next(s for s in series if s["metric"] == "dopemux.task_packet.error_lines")
    assert total_error_metric["points"][0] == [timestamp, 2.0]
