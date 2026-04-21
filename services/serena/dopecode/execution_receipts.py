from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


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


class ReceiptPersistenceError(RuntimeError):
    """Raised when the durable receipt ledger cannot be read or updated safely."""


class ReceiptReplayMismatchError(ReceiptPersistenceError):
    """Raised when an idempotency key is reused with different event content."""


def _datetime_to_utc_z(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


def normalize_ts_utc(value: datetime | str | None = None) -> str:
    if value is None:
        return _datetime_to_utc_z(datetime.now(timezone.utc))
    if isinstance(value, datetime):
        return _datetime_to_utc_z(value)
    if not isinstance(value, str):
        raise TypeError(f"ts_utc must be datetime, str, or None, got {type(value)!r}")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("ts_utc must not be empty")
    iso_candidate = cleaned[:-1] + "+00:00" if cleaned.endswith("Z") else cleaned
    parsed = datetime.fromisoformat(iso_candidate)
    return _datetime_to_utc_z(parsed)


def canonical_json(value: Any) -> str:
    def _normalize(item: Any) -> Any:
        if isinstance(item, datetime):
            return _datetime_to_utc_z(item)
        if isinstance(item, dict):
            return {str(key): _normalize(val) for key, val in item.items()}
        if isinstance(item, list):
            return [_normalize(entry) for entry in item]
        if isinstance(item, tuple):
            return [_normalize(entry) for entry in item]
        return item

    return json.dumps(
        _normalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sorted_unique(values: Iterable[str]) -> List[str]:
    return sorted({value for value in values if value})


def _bounded_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    bounded = dict(payload)
    files = bounded.get("files")
    if isinstance(files, list):
        bounded["files"] = _sorted_unique(str(item) for item in files)
        bounded["file_count"] = len(bounded["files"])
    return bounded


class DopeCodeExecutionReceiptStore:
    """Workspace-scoped durable ledger for dopeCode mutation lifecycle events."""

    def __init__(self, workspace_root: Path, workspace_id: str) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_id = workspace_id
        self.ledger_path = self.workspace_root / DOPECODE_EXECUTION_RECEIPT_RELATIVE_PATH

    def mutation_id_for(self, *, operation: str, operation_class: str, mutation_context: Dict[str, Any]) -> str:
        fingerprint = canonical_json(
            {
                "workspace_id": self.workspace_id,
                "operation": operation,
                "operation_class": operation_class,
                "mutation_context": mutation_context,
            }
        )
        return sha256_hex(fingerprint)

    def build_event(
        self,
        *,
        event_type: str,
        lifecycle_stage: str,
        operation: str,
        operation_class: str,
        execution_mode: str,
        execution_status: str,
        mutation_context: Dict[str, Any],
        payload: Dict[str, Any],
        ts_utc: datetime | str | None = None,
    ) -> Dict[str, Any]:
        if event_type not in DOPECODE_EVENT_TYPES:
            raise ValueError(f"Unsupported dopeCode event type: {event_type}")

        mutation_id = self.mutation_id_for(
            operation=operation,
            operation_class=operation_class,
            mutation_context=mutation_context,
        )
        normalized_payload = _bounded_payload(payload)
        core = {
            "schema_version": DOPECODE_EXECUTION_RECEIPT_VERSION,
            "mutation_id": mutation_id,
            "event_type": event_type,
            "lifecycle_stage": lifecycle_stage,
            "ts_utc": normalize_ts_utc(ts_utc),
            "workspace_id": self.workspace_id,
            "workspace_root": str(self.workspace_root),
            "source": "dopecode",
            "operation": operation,
            "operation_class": operation_class,
            "execution_mode": execution_mode,
            "execution_status": execution_status,
            "payload": normalized_payload,
        }
        event_id = sha256_hex(canonical_json(core))
        return {
            "event_id": event_id,
            "idempotency_key": event_id,
            **core,
        }

    def _validate_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        missing = [field for field in REQUIRED_EVENT_FIELDS if field not in event]
        if missing:
            raise ReceiptPersistenceError(f"Execution receipt missing required fields: {missing}")
        if event["schema_version"] != DOPECODE_EXECUTION_RECEIPT_VERSION:
            raise ReceiptPersistenceError(
                f"Unsupported execution receipt schema: {event['schema_version']!r}"
            )
        if event["event_type"] not in DOPECODE_EVENT_TYPES:
            raise ReceiptPersistenceError(f"Unsupported execution receipt event type: {event['event_type']!r}")
        if event["workspace_id"] != self.workspace_id:
            raise ReceiptPersistenceError(
                f"Execution receipt workspace_id mismatch: {event['workspace_id']!r}"
            )
        if Path(event["workspace_root"]).resolve() != self.workspace_root:
            raise ReceiptPersistenceError(
                f"Execution receipt workspace_root mismatch: {event['workspace_root']!r}"
            )
        return event

    def load_events(self) -> List[Dict[str, Any]]:
        if not self.ledger_path.exists():
            return []

        events: List[Dict[str, Any]] = []
        for line_no, raw_line in enumerate(self.ledger_path.read_text(encoding="utf-8").splitlines(), start=1):
            if not raw_line.strip():
                continue
            try:
                payload = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                raise ReceiptPersistenceError(
                    f"Execution receipt ledger is not valid JSONL at line {line_no}"
                ) from exc
            if not isinstance(payload, dict):
                raise ReceiptPersistenceError(
                    f"Execution receipt ledger line {line_no} must decode to an object"
                )
            events.append(self._validate_event(payload))
        return events

    def append_event(self, event: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        validated = self._validate_event(dict(event))
        existing_events = self.load_events()
        for existing in existing_events:
            if existing["idempotency_key"] != validated["idempotency_key"]:
                continue
            if canonical_json(existing) != canonical_json(validated):
                raise ReceiptReplayMismatchError(
                    f"Execution receipt idempotency mismatch for key {validated['idempotency_key']}"
                )
            return existing, "replayed"

        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with self.ledger_path.open("a", encoding="utf-8") as handle:
            handle.write(canonical_json(validated))
            handle.write("\n")
        return validated, "recorded"
