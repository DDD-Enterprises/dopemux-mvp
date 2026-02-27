"""Helpers for parsing service logs into investigation packet artifacts."""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

LEVEL_PATTERNS: List[Tuple[str, re.Pattern[str]]] = [
    ("critical", re.compile(r"\b(critical|fatal)\b", re.IGNORECASE)),
    (
        "error",
        re.compile(
            r"\b(error|exception|traceback|failed?|failure|panic)\b|[A-Za-z]+Error\b",
            re.IGNORECASE,
        ),
    ),
    ("warning", re.compile(r"\b(warn|warning)\b", re.IGNORECASE)),
    ("info", re.compile(r"\binfo\b", re.IGNORECASE)),
    ("debug", re.compile(r"\bdebug\b", re.IGNORECASE)),
]

TIMESTAMP_PREFIX = re.compile(
    r"^\s*(?P<ts>\d{4}-\d{2}-\d{2}[T ][0-9:.]+(?:Z|[+-]\d{2}:?\d{2})?)",
    re.IGNORECASE,
)
TIMESTAMP_ANY = re.compile(
    r"\b\d{4}-\d{2}-\d{2}[T ][0-9:.]+(?:Z|[+-]\d{2}:?\d{2})?\b",
    re.IGNORECASE,
)
UUID_PATTERN = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
HEX_PATTERN = re.compile(r"\b0x[0-9a-f]+\b", re.IGNORECASE)
NUM_PATTERN = re.compile(r"\b\d+\b")
MULTISPACE_PATTERN = re.compile(r"\s+")


def detect_level(line: str) -> str:
    """Infer canonical log level from a raw log line."""
    for level, pattern in LEVEL_PATTERNS:
        if pattern.search(line):
            return level
    return "unknown"


def extract_timestamp(line: str) -> Optional[str]:
    """Extract an ISO-like timestamp from the front of a line."""
    match = TIMESTAMP_PREFIX.match(line)
    if not match:
        return None
    return match.group("ts")


def normalize_error_signature(line: str) -> str:
    """
    Build a stable signature for grouping similar failures.

    We intentionally remove volatile IDs/timestamps/numbers so repeated failures
    cluster into one signature for fast triage.
    """
    signature = line.strip().lower()
    signature = TIMESTAMP_PREFIX.sub("", signature)
    signature = TIMESTAMP_ANY.sub("<ts>", signature)
    signature = UUID_PATTERN.sub("<uuid>", signature)
    signature = HEX_PATTERN.sub("<hex>", signature)
    signature = NUM_PATTERN.sub("<num>", signature)
    signature = MULTISPACE_PATTERN.sub(" ", signature).strip()
    return signature[:180]


def summarize_service_lines(service: str, lines: Iterable[str]) -> Dict[str, Any]:
    """Summarize line counts and top issue signatures for one service."""
    counts: Counter[str] = Counter()
    signatures: Counter[str] = Counter()
    first_ts: Optional[str] = None
    last_ts: Optional[str] = None
    total = 0

    for raw_line in lines:
        line = raw_line.rstrip("\n")
        if not line:
            continue

        total += 1
        level = detect_level(line)
        counts[level] += 1

        timestamp = extract_timestamp(line)
        if timestamp:
            if first_ts is None:
                first_ts = timestamp
            last_ts = timestamp

        if level in {"error", "critical"}:
            signatures[normalize_error_signature(line)] += 1

    top_signatures = [
        {"signature": sig, "count": count}
        for sig, count in signatures.most_common(15)
        if sig
    ]

    return {
        "service": service,
        "total_lines": total,
        "counts": dict(counts),
        "first_timestamp": first_ts,
        "last_timestamp": last_ts,
        "top_signatures": top_signatures,
        "error_lines": counts.get("error", 0) + counts.get("critical", 0),
        "warning_lines": counts.get("warning", 0),
    }


def log_line_to_json_record(
    *,
    service: str,
    line: str,
    packet_id: str,
    line_number: int,
) -> Dict[str, Any]:
    """Normalize one raw log line into a JSONL-friendly record."""
    return {
        "packet_id": packet_id,
        "service": service,
        "line_number": line_number,
        "timestamp": extract_timestamp(line),
        "level": detect_level(line),
        "message": line.rstrip("\n"),
        "signature": normalize_error_signature(line),
    }


def build_prometheus_export(
    *,
    packet_id: str,
    summary_by_service: Dict[str, Dict[str, Any]],
    health_status: Dict[str, Dict[str, Any]],
    metrics_status: Dict[str, Dict[str, Any]],
) -> str:
    """Render packet summary into Prometheus exposition format."""
    lines = [
        "# HELP dopemux_task_packet_info Metadata about generated investigation packets.",
        "# TYPE dopemux_task_packet_info gauge",
        f'dopemux_task_packet_info{{packet_id="{packet_id}"}} 1',
        "# HELP dopemux_task_packet_log_lines_total Lines collected per service and level.",
        "# TYPE dopemux_task_packet_log_lines_total gauge",
    ]

    for service, summary in sorted(summary_by_service.items()):
        for level, count in sorted(summary.get("counts", {}).items()):
            lines.append(
                'dopemux_task_packet_log_lines_total{packet_id="%s",service="%s",level="%s"} %s'
                % (packet_id, service, level, count)
            )

    lines.extend(
        [
            "# HELP dopemux_task_packet_health_status Service health snapshot (1=healthy).",
            "# TYPE dopemux_task_packet_health_status gauge",
        ]
    )
    for service, result in sorted(health_status.items()):
        status = str(result.get("status", "unknown")).lower()
        value = 1 if status in {"ok", "healthy", "up"} else 0
        lines.append(
            'dopemux_task_packet_health_status{packet_id="%s",service="%s",status="%s"} %d'
            % (packet_id, service, status, value)
        )

    lines.extend(
        [
            "# HELP dopemux_task_packet_metrics_endpoint_up Whether metrics endpoint responded.",
            "# TYPE dopemux_task_packet_metrics_endpoint_up gauge",
        ]
    )
    for service, result in sorted(metrics_status.items()):
        value = 1 if result.get("ok") else 0
        lines.append(
            'dopemux_task_packet_metrics_endpoint_up{packet_id="%s",service="%s"} %d'
            % (packet_id, service, value)
        )

    return "\n".join(lines) + "\n"


def build_datadog_series(
    *,
    packet_id: str,
    summary_by_service: Dict[str, Dict[str, Any]],
    timestamp: Optional[int] = None,
) -> Dict[str, Any]:
    """Build Datadog `series` payload from packet summary."""
    ts = timestamp or int(datetime.now(timezone.utc).timestamp())
    series: List[Dict[str, Any]] = []

    for service, summary in sorted(summary_by_service.items()):
        counts = summary.get("counts", {})
        for level, count in counts.items():
            series.append(
                {
                    "metric": "dopemux.task_packet.log_lines",
                    "type": 3,  # count
                    "points": [[ts, float(count)]],
                    "tags": [
                        f"packet_id:{packet_id}",
                        f"service:{service}",
                        f"level:{level}",
                    ],
                }
            )
        series.append(
            {
                "metric": "dopemux.task_packet.error_lines",
                "type": 3,
                "points": [[ts, float(summary.get("error_lines", 0))]],
                "tags": [f"packet_id:{packet_id}", f"service:{service}"],
            }
        )

    return {"series": series}
