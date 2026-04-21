"""Dopemux reader and presenter for dopeCode execution receipt history."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


DOPECODE_EXECUTION_RECEIPT_VERSION = "dopecode.execution_receipt.v1"
DOPECODE_EXECUTION_RECEIPT_RELATIVE_PATH = Path(".dopemux/dopecode/execution_receipts.jsonl")
DOPECODE_EVENT_TYPES = frozenset(
    {
        "dopecode.mutation.previewed",
        "dopecode.mutation.applied",
        "dopecode.mutation.noop",
        "dopecode.mutation.partial_failure",
        "dopecode.mutation.failed",
    }
)

REQUIRED_EVENT_FIELDS = (
    "schema_version",
    "event_id",
    "idempotency_key",
    "mutation_id",
    "event_type",
    "lifecycle_stage",
    "ts_utc",
    "workspace_id",
    "workspace_root",
    "source",
    "operation",
    "operation_class",
    "execution_mode",
    "execution_status",
    "payload",
)


class DopeCodeReceiptReadError(RuntimeError):
    """Raised when dopemux cannot safely consume dopeCode execution receipts."""


def dopecode_receipt_ledger_path(workspace_root: Path) -> Path:
    return Path(workspace_root).resolve() / DOPECODE_EXECUTION_RECEIPT_RELATIVE_PATH


def _validate_event(
    event: Dict[str, Any], workspace_root: Path, expected_workspace_id: str | None = None
) -> Dict[str, Any]:
    missing = [field for field in REQUIRED_EVENT_FIELDS if field not in event]
    if missing:
        raise DopeCodeReceiptReadError(f"Execution receipt missing required fields: {missing}")
    if event["schema_version"] != DOPECODE_EXECUTION_RECEIPT_VERSION:
        raise DopeCodeReceiptReadError(f"Unsupported execution receipt schema: {event['schema_version']!r}")
    if event["event_type"] not in DOPECODE_EVENT_TYPES:
        raise DopeCodeReceiptReadError(f"Unsupported execution receipt event type: {event['event_type']!r}")
    workspace_id = str(event["workspace_id"]).strip()
    if not workspace_id:
        raise DopeCodeReceiptReadError("Execution receipt workspace_id must be non-empty")
    if expected_workspace_id is not None and workspace_id != expected_workspace_id:
        raise DopeCodeReceiptReadError(
            f"Execution receipt workspace_id mismatch: {event['workspace_id']!r}"
        )
    if Path(event["workspace_root"]).resolve() != workspace_root.resolve():
        raise DopeCodeReceiptReadError(
            f"Execution receipt workspace_root mismatch: {event['workspace_root']!r}"
        )
    if not isinstance(event["payload"], dict):
        raise DopeCodeReceiptReadError("Execution receipt payload must be an object")
    return event


def load_dopecode_execution_receipts(
    workspace_root: Path, expected_workspace_id: str | None = None
) -> List[Dict[str, Any]]:
    ledger_path = dopecode_receipt_ledger_path(workspace_root)
    if not ledger_path.exists():
        return []

    events: List[Dict[str, Any]] = []
    for line_no, raw_line in enumerate(ledger_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            payload = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise DopeCodeReceiptReadError(
                f"Execution receipt ledger is not valid JSONL at line {line_no}"
            ) from exc
        if not isinstance(payload, dict):
            raise DopeCodeReceiptReadError(
                f"Execution receipt ledger line {line_no} must decode to an object"
            )
        events.append(
            _validate_event(
                payload,
                Path(workspace_root),
                expected_workspace_id=expected_workspace_id,
            )
        )
    return events


def replay_dopecode_execution_receipts(events: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    deduped: Dict[str, Dict[str, Any]] = {}
    for raw_event in events:
        event = dict(raw_event)
        event_id = str(event.get("event_id", "")).strip()
        if not event_id:
            raise DopeCodeReceiptReadError("Execution receipt replay requires event_id")
        if event_id in deduped:
            if json.dumps(deduped[event_id], sort_keys=True) != json.dumps(event, sort_keys=True):
                raise DopeCodeReceiptReadError(
                    f"Execution receipt replay mismatch for event_id {event_id}"
                )
            continue
        deduped[event_id] = event
    return sorted(
        deduped.values(),
        key=lambda item: (str(item.get("ts_utc", "")), str(item.get("event_id", ""))),
    )


def build_dopecode_execution_history_view(events: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    replayed = replay_dopecode_execution_receipts(events)
    timeline = []
    for event in replayed:
        payload = dict(event.get("payload", {}))
        files = [str(item) for item in payload.get("files", []) if item]
        summary = str(payload.get("summary", "")).strip() or f"{event['operation']} {event['event_type']}"
        timeline.append(
            {
                "event_id": event["event_id"],
                "mutation_id": event["mutation_id"],
                "ts_utc": event["ts_utc"],
                "event_type": event["event_type"],
                "operation": event["operation"],
                "execution_status": event["execution_status"],
                "files": files,
                "summary": summary,
                "display": _format_history_line(event, summary, files),
            }
        )
    return {
        "schema_version": "dopemux.dopecode_history.v1",
        "event_count": len(timeline),
        "timeline": timeline,
    }


def _format_history_line(event: Dict[str, Any], summary: str, files: List[str]) -> str:
    file_summary = ", ".join(files) if files else "(no files)"
    return (
        f"{event['ts_utc']} | {event['operation']} | {event['event_type']} | "
        f"{event['execution_status']} | {file_summary} | {summary}"
    )
