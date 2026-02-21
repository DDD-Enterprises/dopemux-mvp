#!/usr/bin/env python3
"""OpenAI webhook receiver sidecar.

Verifies signed webhook payloads, deduplicates by webhook-id, and writes
normalized event rows into a dual-db ledger (sqlite/postgres).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional

from ledger.interface import RunEventInsert, WebhookEventInsert
from reconcile import extract_run_mapping
from storage import build_event_store, resolve_webhook_db_url

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("webhook_receiver")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"openai_sdk_unavailable:{type(exc).__name__}") from exc

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "sk-not-used"))
    event = client.webhooks.unwrap(raw_body.decode("utf-8", errors="replace"), headers, secret=secret)
    payload = event_to_dict(event)
    if not payload:
        raise RuntimeError("empty_event_payload")
    return payload


def _header_webhook_id(headers: Dict[str, str]) -> str:
    candidates = ["webhook-id", "Webhook-Id", "X-Webhook-Id"]
    for key in candidates:
        value = str(headers.get(key) or "").strip()
        if value:
            return value
    return ""


def _json_compact(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _run_event_dedupe_key(
    *,
    provider: str,
    run_id: Optional[str],
    phase: Optional[str],
    step_id: Optional[str],
    partition_id: Optional[str],
    event_type: str,
    event_id: Optional[str],
    provider_ref: Optional[str],
    idempotency_key: str,
    orphaned: bool,
) -> str:
    base = "|".join(
        [
            provider,
            run_id or "",
            phase or "",
            step_id or "",
            partition_id or "",
            event_type or "",
            event_id or "",
            provider_ref or "",
            idempotency_key,
            "orphaned" if orphaned else "linked",
        ]
    )
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def ensure_migrations(db_url: str) -> None:
    root = Path(__file__).resolve().parents[2]
    migrate_script = root / "scripts" / "webhook_migrate.py"
    if not migrate_script.exists():
        raise RuntimeError(f"missing migration script: {migrate_script}")
    subprocess.run(
        [os.getenv("PYTHON", "python3"), str(migrate_script), "--db", db_url],
        check=True,
        capture_output=True,
        text=True,
    )


class WebhookHandler(BaseHTTPRequestHandler):
    server_version = "DopemuxWebhookReceiver/2.0"

    def _write_json(self, status: int, payload: Dict[str, Any]) -> None:
        raw = _json_compact(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/healthz":
            self._write_json(HTTPStatus.OK, {"status": "ok", "schema": "DPMX_WEBHOOK_V2"})
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
        webhook_id = _header_webhook_id(headers)
        if not webhook_id:
            self._write_json(HTTPStatus.BAD_REQUEST, {"error": "missing_webhook_id"})
            return

        try:
            payload = verify_openai_webhook(raw_body, headers, secret)
        except Exception as exc:
            logger.warning("Webhook verification failed provider=openai delivery_id=%s reason=%s", webhook_id, exc)
            self._write_json(HTTPStatus.UNAUTHORIZED, {"error": "invalid_signature"})
            return

        payload_json = raw_body.decode("utf-8", errors="replace")
        headers_json = _json_compact(headers)
        event_type = str(payload.get("type") or "unknown")
        event_id = str(payload.get("id") or "") or None
        inserted = self.server.event_store.insert_webhook_event_if_absent(
            WebhookEventInsert(
                provider="openai",
                idempotency_key=webhook_id,
                event_type=event_type,
                event_id=event_id,
                received_at_utc=now_iso(),
                payload_json=payload_json,
                headers_json=headers_json,
                signature_valid=True,
            )
        )

        if inserted:
            mapping = extract_run_mapping(payload)
            run_id = mapping.get("run_id")
            phase = mapping.get("phase")
            step_id = mapping.get("step_id")
            partition_id = mapping.get("partition_id")
            provider_ref = mapping.get("provider_ref")
            orphaned = not bool(run_id and phase and step_id and partition_id)
            webhook_event_id = None
            if hasattr(self.server.event_store, "fetch_webhook_event_id"):
                webhook_event_id = self.server.event_store.fetch_webhook_event_id("openai", webhook_id)  # type: ignore[attr-defined]
            dedupe_key = _run_event_dedupe_key(
                provider="openai",
                run_id=run_id,
                phase=phase,
                step_id=step_id,
                partition_id=partition_id,
                event_type=event_type,
                event_id=event_id,
                provider_ref=provider_ref,
                idempotency_key=webhook_id,
                orphaned=orphaned,
            )
            self.server.event_store.append_run_event(
                RunEventInsert(
                    run_id=run_id,
                    phase=phase,
                    step_id=step_id,
                    partition_id=partition_id,
                    provider="openai",
                    event_type=event_type,
                    event_id=event_id,
                    provider_ref=provider_ref,
                    webhook_event_id=webhook_event_id,
                    dedupe_key=dedupe_key,
                    orphaned=orphaned,
                )
            )
            logger.info(
                "Webhook accepted provider=openai delivery_id=%s event_type=%s event_id=%s linked_run_mapping_status=%s",
                webhook_id,
                event_type,
                event_id or "",
                "orphaned" if orphaned else "mapped",
            )
        else:
            logger.info("Webhook duplicate ignored provider=openai delivery_id=%s", webhook_id)

        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        logger.info("%s - %s", self.address_string(), fmt % args)


class WebhookServer(ThreadingHTTPServer):
    def __init__(self, host: str, port: int, event_store: Any) -> None:
        super().__init__((host, port), WebhookHandler)
        self.event_store = event_store


def main() -> None:
    env = os.getenv("DPMX_ENV", "dev").strip().lower()
    secret = os.getenv("OPENAI_WEBHOOK_SECRET", "").strip()
    if env == "prod" and not secret:
        logger.error("DPMX_ENV is prod but OPENAI_WEBHOOK_SECRET is missing. Refusing to start.")
        raise RuntimeError("OPENAI_WEBHOOK_SECRET is required in prod")

    host = os.getenv("WEBHOOK_RECEIVER_HOST", "0.0.0.0").strip() or "0.0.0.0"
    port = int(os.getenv("WEBHOOK_RECEIVER_PORT", "8790") or "8790")
    db_url = resolve_webhook_db_url()
    ensure_migrations(db_url)
    event_store = build_event_store(db_url)
    server = WebhookServer(host, port, event_store)
    logger.info("Webhook receiver listening on %s:%s db_url=%s", host, port, db_url)
    server.serve_forever()


if __name__ == "__main__":
    main()
