#!/usr/bin/env python3
"""
Runtime smoke test for Dope-Memory in the canonical compose stack.

Checks:
1) Health endpoint is up
2) Redis XADD event is ingested and redacted before persistence
3) Top-3 search is deterministic across repeats
4) Cursor pagination has no overlap across pages
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request


SERVICE_DIR = Path(__file__).parent.resolve()
if str(SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_DIR))

SERVICE_URL = os.getenv("DOPE_MEMORY_URL", "http://localhost:8096")
REDIS_CONTAINER = os.getenv("DOPE_MEMORY_REDIS_CONTAINER", "redis-events")
LEDGER_PATH = Path(
    os.getenv("DOPEMUX_CAPTURE_LEDGER_PATH_HOST", ".dopemux/chronicle.sqlite")
).resolve()
WORKSPACE_ID = os.getenv("DOPE_MEMORY_WORKSPACE_ID", str(Path.cwd().resolve()))
INSTANCE_ID = os.getenv("DOPE_MEMORY_INSTANCE_ID", "A")


def _http_json(method: str, path: str, payload: dict | None = None) -> dict:
    url = f"{SERVICE_URL}{path}"
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = request.Request(url, method=method, data=data, headers=headers)
    try:
        with request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} {path}: {body}") from exc


def _assert(cond: bool, message: str) -> None:
    if not cond:
        print(f"FAIL: {message}")
        raise SystemExit(1)


def _inject_redaction_event(event_id: str, marker: str) -> None:
    data_payload = json.dumps(
        {
            "category": "debugging",
            "entry_type": "manual_note",
            "summary": "Runtime smoke redaction event",
            "details": {
                "token": marker,
                "note": f"Bearer {marker}",
            },
        }
    )
    cmd = [
        "docker",
        "exec",
        REDIS_CONTAINER,
        "redis-cli",
        "XADD",
        "activity.events.v1",
        "*",
        "type",
        "manual.memory_store",
        "source",
        "runtime.smoke",
        "workspace_id",
        WORKSPACE_ID,
        "instance_id",
        INSTANCE_ID,
        "session_id",
        "runtime-smoke-session",
        "id",
        event_id,
        "ts",
        datetime.now(timezone.utc).isoformat(),
        "data",
        data_payload,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    _assert(proc.returncode == 0, f"Redis XADD failed: {proc.stderr.strip()}")
    print(f"XADD id: {proc.stdout.strip()}")


def _wait_for_event(event_id: str, timeout_sec: int = 10) -> sqlite3.Connection:
    _assert(LEDGER_PATH.exists(), f"Ledger not found: {LEDGER_PATH}")
    conn = sqlite3.connect(str(LEDGER_PATH))
    started = time.time()
    while time.time() - started < timeout_sec:
        row = conn.execute(
            "SELECT payload_json FROM raw_activity_events WHERE id = ?",
            (event_id,),
        ).fetchone()
        if row:
            return conn
        time.sleep(0.5)
    conn.close()
    raise SystemExit(f"FAIL: Timed out waiting for event {event_id} in raw_activity_events")


def _run_determinism_checks() -> None:
    # Use an isolated ledger for deterministic paging checks.
    from mcp.server import DopeMemoryMCPServer

    with tempfile.TemporaryDirectory(prefix="dm-smoke-") as tmpdir:
        ledger = Path(tmpdir) / "chronicle.sqlite"
        os.environ["DOPEMUX_CAPTURE_LEDGER_PATH"] = str(ledger)
        server = DopeMemoryMCPServer(workspace_id="runtime-smoke-local", instance_id="A")

        for label, score in [("A", 9), ("B", 8), ("C", 7), ("D", 6), ("E", 5)]:
            resp = server.memory_store(
                workspace_id="runtime-smoke-local",
                instance_id="A",
                category="debugging",
                entry_type="manual_note",
                summary=f"RuntimeSmoke-{label}",
                importance_score=score,
                tags=["runtime-smoke"],
            )
            _assert(resp.get("success") is True, f"local memory_store failed for {label}: {resp}")

        search_args = dict(
            query="RuntimeSmoke-",
            workspace_id="runtime-smoke-local",
            instance_id="A",
            top_k=3,
        )
        page1a = server.memory_search(**search_args)
        page1b = server.memory_search(**search_args)
        _assert(page1a.get("success") is True and page1b.get("success") is True, "local memory_search failed")
        _assert(page1a.get("items") == page1b.get("items"), "Top-3 results changed across repeats")
        _assert(
            page1a.get("next_token") == page1b.get("next_token"),
            "next_token changed across identical repeats",
        )
        print("Determinism: Top-3 stable across repeats")

        token = page1a.get("next_token")
        if token:
            page2a = server.memory_search(**{**search_args, "cursor": token})
            page2b = server.memory_search(**{**search_args, "cursor": token})
            _assert(page2a == page2b, "Cursor page is not stable across repeats")
            ids1 = {item["id"] for item in page1a.get("items", [])}
            ids2 = {item["id"] for item in page2a.get("items", [])}
            _assert(not ids1.intersection(ids2), "Cursor pagination overlap detected")
            print("Pagination: no overlap across pages")


def main() -> int:
    print("Dope-Memory Runtime Smoke")
    print("=========================")
    print(f"Service URL: {SERVICE_URL}")
    print(f"Ledger: {LEDGER_PATH}")

    try:
        health = _http_json("GET", "/health")
    except error.URLError as exc:
        print(f"FAIL: health check request failed: {exc}")
        return 1

    _assert(health.get("status") == "healthy", f"health status is not healthy: {health}")
    print("Health: OK")

    marker = "FAKE_SECRET_RUNTIME_SMOKE_123"
    event_id = f"runtime-smoke-{uuid.uuid4().hex[:12]}"
    _inject_redaction_event(event_id, marker)

    conn = _wait_for_event(event_id)
    row = conn.execute(
        "SELECT payload_json FROM raw_activity_events WHERE id = ?",
        (event_id,),
    ).fetchone()
    _assert(row is not None, "event row missing after wait")
    payload_json = row[0]
    _assert(marker not in payload_json, "unredacted marker persisted in raw payload")
    _assert("[REDACTED:BEARER]" in payload_json, "expected redaction token not present")
    conn.close()
    print("Redaction: raw payload is redacted")

    _run_determinism_checks()

    print("PASS: runtime smoke checks succeeded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
