"""Deterministic memory capture client with a per-project canonical ledger."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import logging
import os
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None


LOGGER = logging.getLogger(__name__)
_SCHEMA_INIT_LOCK = threading.Lock()
_SCHEMA_READY_LEDGER_PATHS: set[str] = set()

CAPTURE_MODE_PLUGIN = "plugin"
CAPTURE_MODE_CLI = "cli"
CAPTURE_MODE_MCP = "mcp"
CAPTURE_MODE_AUTO = "auto"
CAPTURE_MODES = {
    CAPTURE_MODE_PLUGIN,
    CAPTURE_MODE_CLI,
    CAPTURE_MODE_MCP,
    CAPTURE_MODE_AUTO,
}


class CaptureError(RuntimeError):
    """Raised when capture cannot proceed safely."""


@dataclass(frozen=True)
class CaptureResult:
    """Structured result for a capture write."""

    event_id: str
    inserted: bool
    ledger_path: Path
    repo_root: Path
    mode: str
    source: str
    event_type: str


def _repo_root_from_start(start_path: Path) -> Path:
    """Walk upward to find a deterministic project root marker."""
    current = start_path.resolve()
    if current.is_file():
        current = current.parent

    candidates = [current, *current.parents]
    for candidate in candidates:
        if (candidate / ".git").exists() or (candidate / ".dopemux").exists():
            return candidate

    raise CaptureError(
        "Unable to resolve repository root from current path. "
        "Capture fails closed outside a repo/workspace."
    )


def resolve_repo_root_strict(start_path: Optional[Path] = None) -> Path:
    """Resolve project root and fail closed when no markers exist."""
    return _repo_root_from_start(start_path or Path.cwd())


def _read_capture_mode_from_project_config(repo_root: Path) -> Optional[str]:
    """Read capture.mode from .dopemux/config.yaml if present."""
    config_path = repo_root / ".dopemux" / "config.yaml"
    if not config_path.exists() or yaml is None:
        return None

    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return None

    capture_cfg = raw.get("capture")
    if not isinstance(capture_cfg, dict):
        return None

    mode = capture_cfg.get("mode")
    if isinstance(mode, str):
        mode = mode.strip().lower()
        if mode in CAPTURE_MODES:
            return mode
    return None


def resolve_capture_mode(
    mode: str = CAPTURE_MODE_AUTO,
    *,
    repo_root: Optional[Path] = None,
) -> str:
    """Resolve capture mode from explicit argument, env, project config, then auto."""
    normalized = (mode or CAPTURE_MODE_AUTO).strip().lower()
    if normalized not in CAPTURE_MODES:
        raise CaptureError(
            f"Invalid capture mode '{mode}'. Expected one of: {sorted(CAPTURE_MODES)}"
        )
    if normalized != CAPTURE_MODE_AUTO:
        return normalized

    env_mode = os.getenv("DOPEMUX_CAPTURE_MODE", "").strip().lower()
    if env_mode in CAPTURE_MODES and env_mode != CAPTURE_MODE_AUTO:
        return env_mode

    root = repo_root or resolve_repo_root_strict()
    cfg_mode = _read_capture_mode_from_project_config(root)
    if cfg_mode and cfg_mode != CAPTURE_MODE_AUTO:
        return cfg_mode

    capture_context = os.getenv("DOPEMUX_CAPTURE_CONTEXT", "").strip().lower()
    if capture_context == CAPTURE_MODE_PLUGIN:
        return CAPTURE_MODE_PLUGIN
    if capture_context == CAPTURE_MODE_MCP:
        return CAPTURE_MODE_MCP

    # Claude Code style markers (best-effort)
    if os.getenv("CLAUDE_SESSION_ID") or os.getenv("CLAUDECODE"):
        return CAPTURE_MODE_PLUGIN

    return CAPTURE_MODE_CLI


def _default_source_for_mode(mode: str) -> str:
    if mode == CAPTURE_MODE_PLUGIN:
        return "claude_hook"
    if mode == CAPTURE_MODE_MCP:
        return "mcp"
    return "cli"


def _resolve_wma_schema_path(repo_root: Path) -> Path:
    schema_path = (
        repo_root
        / "services"
        / "working-memory-assistant"
        / "chronicle"
        / "schema.sql"
    )
    if not schema_path.exists():
        raise CaptureError(f"WMA schema not found: {schema_path}")
    return schema_path


def _load_wma_redactor(repo_root: Path) -> Any:
    redactor_path = (
        repo_root
        / "services"
        / "working-memory-assistant"
        / "promotion"
        / "redactor.py"
    )
    if not redactor_path.exists():
        raise CaptureError(f"WMA redactor not found: {redactor_path}")

    spec = importlib.util.spec_from_file_location(
        "dopemux_wma_redactor",
        str(redactor_path),
    )
    if spec is None or spec.loader is None:
        raise CaptureError(f"Failed to load redactor module from {redactor_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "Redactor"):
        raise CaptureError("Redactor class missing in WMA redactor module")

    return module.Redactor()


def _resolve_ledger_path(repo_root: Path) -> Path:
    override = os.getenv("DOPEMUX_CAPTURE_LEDGER_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return (repo_root / ".dopemux" / "chronicle.sqlite").resolve()


def _initialize_schema(conn: sqlite3.Connection, schema_path: Path) -> None:
    schema_sql = schema_path.read_text(encoding="utf-8")
    conn.executescript(schema_sql)
    conn.commit()


def _schema_table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        LIMIT 1
        """,
        (table_name,),
    ).fetchone()
    return bool(row)


def _ensure_schema_initialized(
    conn: sqlite3.Connection,
    schema_path: Path,
    ledger_path: Path,
) -> None:
    ledger_key = str(ledger_path.resolve())
    if ledger_key in _SCHEMA_READY_LEDGER_PATHS:
        return

    with _SCHEMA_INIT_LOCK:
        if ledger_key in _SCHEMA_READY_LEDGER_PATHS:
            return
        if _schema_table_exists(conn, "raw_activity_events"):
            _SCHEMA_READY_LEDGER_PATHS.add(ledger_key)
            return
        _initialize_schema(conn, schema_path)
        _SCHEMA_READY_LEDGER_PATHS.add(ledger_key)


def _normalize_payload(raw_payload: Any) -> dict[str, Any]:
    if raw_payload is None:
        return {}
    if isinstance(raw_payload, dict):
        return raw_payload
    return {"value": raw_payload}


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _deterministic_event_id(
    *,
    event_type: str,
    session_id: Optional[str],
    ts_utc: str,
    payload: dict[str, Any],
) -> str:
    """Generate deterministic event_id from semantic content only.
    
    Per Packet D §3.3: event_id is content-addressed, excluding adapter-specific
    metadata (source, project_id) to enable cross-adapter convergence.
    
    Fingerprint formula: event_type | session_id_or_empty | ts_bucket | stable_json(payload)
    
    Note: session_id_or_empty MUST be empty string ("") when session_id is None,
    not a sentinel value, to keep event_id stable across adapters and environments.
    """
    # Bucket to second precision for retry-idempotency.
    ts_bucket = ts_utc[:19]
    # Normalize session_id to empty string if None (per Packet D clarification)
    session_id_normalized = session_id or ""
    fingerprint = "|".join(
        [
            event_type,
            session_id_normalized,
            ts_bucket,
            _stable_json(payload),
        ]
    )
    return hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()


def _emit_to_event_stream(event: dict[str, Any]) -> None:
    """Best-effort Redis stream fan-out for downstream consumers."""
    try:
        import redis  # type: ignore
    except Exception:
        LOGGER.debug("redis package unavailable; skipping event stream emit")
        return

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    stream_name = os.getenv("DOPE_MEMORY_INPUT_STREAM", "activity.events.v1")
    redis_password = os.getenv("REDIS_PASSWORD")

    try:
        client = redis.Redis.from_url(redis_url, password=redis_password, decode_responses=True)
        envelope = {
            "id": event["id"],
            "ts": event["ts_utc"],
            "workspace_id": event["workspace_id"],
            "instance_id": event["instance_id"],
            "session_id": event.get("session_id") or "",
            "type": event["event_type"],
            "source": event["source"],
            "data": _stable_json(event["payload"]),
        }
        client.xadd(stream_name, envelope)
    except Exception as exc:  # pragma: no cover - best effort
        LOGGER.debug("event stream emit failed: %s", exc)


def emit_capture_event(
    event: dict[str, Any],
    *,
    mode: str = CAPTURE_MODE_AUTO,
    repo_root: Optional[Path] = None,
    emit_event_bus: Optional[bool] = None,
) -> CaptureResult:
    """Redact + write raw activity event to canonical per-project ledger."""
    root = repo_root.resolve() if repo_root else resolve_repo_root_strict()
    selected_mode = resolve_capture_mode(mode, repo_root=root)
    source = str(event.get("source") or _default_source_for_mode(selected_mode))

    event_type = str(
        event.get("event_type")
        or event.get("type")
        or ""
    ).strip()
    if not event_type:
        raise CaptureError("event_type is required")

    payload = _normalize_payload(event.get("payload", event.get("data")))
    ts_utc = str(event.get("ts_utc") or event.get("ts") or datetime.now(timezone.utc).isoformat())
    session_id = event.get("session_id")
    instance_id = str(event.get("instance_id") or os.getenv("DOPEMUX_INSTANCE_ID", "A"))

    project_id = str(root)
    workspace_id = str(event.get("workspace_id") or project_id)

    redactor = _load_wma_redactor(root)
    redacted_payload = redactor.redact_payload(payload)

    # Generate event_id BEFORE injecting project_id (Packet D §3.3)
    # project_id is machine-specific and must not affect event identity
    event_id = str(
        event.get("event_id")
        or event.get("id")
        or _deterministic_event_id(
            event_type=event_type,
            session_id=session_id,
            ts_utc=ts_utc,
            payload=redacted_payload,
        )
    )

    # Inject project_id AFTER event_id generation for storage/routing only
    redacted_payload["project_id"] = project_id

    ledger_path = _resolve_ledger_path(root)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(ledger_path))
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        _ensure_schema_initialized(
            conn,
            _resolve_wma_schema_path(root),
            ledger_path,
        )
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO raw_activity_events (
                id, workspace_id, instance_id, session_id,
                ts_utc, event_type, source,
                payload_json, redaction_level, ttl_days, created_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                workspace_id,
                instance_id,
                session_id,
                ts_utc,
                event_type,
                source,
                json.dumps(redacted_payload, ensure_ascii=True),
                "strict",
                int(event.get("ttl_days", 7)),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
        inserted = cur.rowcount > 0
    finally:
        conn.close()

    should_emit_event_bus = emit_event_bus
    if should_emit_event_bus is None:
        should_emit_event_bus = (
            os.getenv("DOPEMUX_CAPTURE_EMIT_EVENTBUS", "false").strip().lower()
            in {"1", "true", "yes", "on"}
        )

    if should_emit_event_bus:
        _emit_to_event_stream(
            {
                "id": event_id,
                "workspace_id": workspace_id,
                "instance_id": instance_id,
                "session_id": session_id,
                "event_type": event_type,
                "source": source,
                "payload": redacted_payload,
                "ts_utc": ts_utc,
            }
        )

    return CaptureResult(
        event_id=event_id,
        inserted=inserted,
        ledger_path=ledger_path,
        repo_root=root,
        mode=selected_mode,
        source=source,
        event_type=event_type,
    )
