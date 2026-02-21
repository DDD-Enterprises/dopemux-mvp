#!/usr/bin/env python3
"""OpenAI webhook receiver sidecar.

Verifies signed webhook payloads, deduplicates by webhook-id, and writes
normalized event rows into a lightweight sqlite ledger.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("webhook_receiver")

DB_LOCK = threading.Lock()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def db_path_from_env() -> Path:
    raw = os.getenv("WEBHOOK_DB_PATH", "/data/webhook_receiver.db").strip()
    return Path(raw)


def init_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS webhook_events (
              webhook_id TEXT PRIMARY KEY,
              event_id TEXT,
              event_type TEXT,
              created_at INTEGER,
              received_at_utc TEXT NOT NULL,
              payload_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS run_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              run_id TEXT,
              phase TEXT,
              step_id TEXT,
              partition_id TEXT,
              provider TEXT NOT NULL,
              event_type TEXT,
              event_id TEXT,
              response_id TEXT,
              payload_ref_webhook_id TEXT NOT NULL,
              created_at_utc TEXT NOT NULL
            )
            """
        )
        conn.commit()


def event_to_dict(event_obj: Any) -> Dict[str, Any]:
    if isinstance(event_obj, dict):
        return dict(event_obj)
    if hasattr(event_obj, "model_dump"):
        dumped = event_obj.model_dump()
        if isinstance(dumped, dict):
            return dumped
    if hasattr(event_obj, "to_dict"):
        dumped = event_obj.to_dict()
        if isinstance(dumped, dict):
            return dumped
    if hasattr(event_obj, "__dict__"):
        dumped = dict(getattr(event_obj, "__dict__"))
        if isinstance(dumped, dict):
            return dumped
    return {}


def verify_openai_webhook(raw_body: bytes, headers: Dict[str, str], secret: str) -> Dict[str, Any]:
    try:
        from openai import OpenAI
    except Exception as exc:  # pragma: no cover - dependency/runtime guard
        raise RuntimeError(f"openai_sdk_unavailable:{type(exc).__name__}") from exc

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "sk-not-used"))
    event = client.webhooks.unwrap(raw_body.decode("utf-8", errors="replace"), headers, secret=secret)
    payload = event_to_dict(event)
    if not payload:
        raise RuntimeError("empty_event_payload")
    return payload


def insert_webhook_event(path: Path, webhook_id: str, payload: Dict[str, Any]) -> bool:
    event_id = str(payload.get("id") or "")
    event_type = str(payload.get("type") or "")
    created_at = payload.get("created_at")
    created_at_int = int(created_at) if isinstance(created_at, int) else None
    with DB_LOCK:
        with sqlite3.connect(path) as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO webhook_events (
                      webhook_id, event_id, event_type, created_at, received_at_utc, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        webhook_id,
                        event_id,
                        event_type,
                        created_at_int,
                        now_iso(),
                        json.dumps(payload, ensure_ascii=True, sort_keys=True),
                    ),
                )
            except sqlite3.IntegrityError:
                return False

            data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
            metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
            conn.execute(
                """
                INSERT INTO run_events (
                  run_id, phase, step_id, partition_id, provider, event_type,
                  event_id, response_id, payload_ref_webhook_id, created_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(metadata.get("run_id") or ""),
                    str(metadata.get("phase") or ""),
                    str(metadata.get("step_id") or ""),
                    str(metadata.get("partition_id") or ""),
                    "openai",
                    event_type,
                    event_id,
                    str(data.get("id") or ""),
                    webhook_id,
                    now_iso(),
                ),
            )
            conn.commit()
    return True


class WebhookHandler(BaseHTTPRequestHandler):
    server_version = "DopemuxWebhookReceiver/1.0"

    def _write_json(self, status: int, payload: Dict[str, Any]) -> None:
        raw = json.dumps(payload, ensure_ascii=True, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/healthz":
            self._write_json(HTTPStatus.OK, {"status": "ok", "schema": "DPMX_WEBHOOK_V1"})
            return
        self._write_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/webhook/openai":
            self._write_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return

        secret = os.getenv("OPENAI_WEBHOOK_SECRET", "").strip()
        if not secret:
            self._write_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "missing_openai_webhook_secret"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0") or "0")
        except Exception:
            content_length = 0
        raw_body = self.rfile.read(max(0, content_length))
        headers = {str(k): str(v) for k, v in self.headers.items()}

        webhook_id = (
            self.headers.get("webhook-id")
            or self.headers.get("Webhook-Id")
            or self.headers.get("X-Webhook-Id")
            or ""
        ).strip()
        if not webhook_id:
            self._write_json(HTTPStatus.BAD_REQUEST, {"error": "missing_webhook_id"})
            return

        try:
            payload = verify_openai_webhook(raw_body, headers, secret)
        except Exception as exc:
            logger.warning("Webhook verification failed webhook_id=%s reason=%s", webhook_id, exc)
            self._write_json(HTTPStatus.UNAUTHORIZED, {"error": "invalid_signature"})
            return

        inserted = insert_webhook_event(self.server.db_path, webhook_id, payload)
        if inserted:
            logger.info(
                "Webhook accepted webhook_id=%s event_type=%s",
                webhook_id,
                str(payload.get("type") or "unknown"),
            )
        else:
            logger.info("Webhook duplicate ignored webhook_id=%s", webhook_id)

        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        logger.info("%s - %s", self.address_string(), fmt % args)


class WebhookServer(ThreadingHTTPServer):
    def __init__(self, host: str, port: int, db_path: Path) -> None:
        super().__init__((host, port), WebhookHandler)
        self.db_path = db_path


def main() -> None:
    host = os.getenv("WEBHOOK_RECEIVER_HOST", "0.0.0.0").strip() or "0.0.0.0"
    port = int(os.getenv("WEBHOOK_RECEIVER_PORT", "8790") or "8790")
    db_path = db_path_from_env()
    init_db(db_path)
    server = WebhookServer(host, port, db_path)
    logger.info("Webhook receiver listening on %s:%s db=%s", host, port, db_path)
    server.serve_forever()


if __name__ == "__main__":
    main()
