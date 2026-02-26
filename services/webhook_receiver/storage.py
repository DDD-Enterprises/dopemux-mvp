from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from ledger.interface import EventStore, parse_db_url
from ledger.postgres_store import PostgresEventStore
from ledger.sqlite_store import SQLiteEventStore


def resolve_webhook_db_url() -> str:
    db_url = os.getenv("WEBHOOK_DB_URL", "").strip()
    if db_url:
        return db_url
    legacy = os.getenv("WEBHOOK_DB_PATH", "").strip()
    if legacy:
        path = Path(legacy).resolve()
        return f"sqlite:///{path.as_posix()}"
    default_container = Path("/data/webhook_receiver.db")
    parent = default_container.parent
    if parent.exists() and os.access(parent, os.W_OK):
        return "sqlite:////data/webhook_receiver.db"
    local_default = (Path.cwd() / ".dopemux" / "webhook_receiver" / "webhook_receiver.db").resolve()
    return f"sqlite:///{local_default.as_posix()}"


def build_event_store(db_url: Optional[str] = None) -> EventStore:
    resolved = db_url.strip() if db_url is not None else resolve_webhook_db_url()
    parsed = parse_db_url(resolved)
    if parsed["backend"] == "sqlite":
        return SQLiteEventStore(parsed["path"])
    if parsed["backend"] == "postgres":
        return PostgresEventStore(parsed["url"])
    raise RuntimeError(f"Unsupported backend: {parsed['backend']}")
