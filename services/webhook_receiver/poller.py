#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List

from ledger.interface import RunEventInsert, WebhookEventInsert
from providers.gemini_poller import poll_status as poll_gemini_status
from providers.xai_poller import poll_status as poll_xai_status
from server import ensure_migrations
from storage import build_event_store, resolve_webhook_db_url

TERMINAL_STATUSES = {"completed", "failed"}
SUPPORTED_PROVIDERS: Dict[str, Callable[[Dict[str, Any]], str]] = {
    "xai": poll_xai_status,
    "gemini": poll_gemini_status,
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _parse_provider_list(raw: str) -> List[str]:
    providers = [token.strip().lower() for token in str(raw or "").split(",") if token.strip()]
    if not providers:
        raise ValueError("At least one provider is required")
    unsupported = sorted({provider for provider in providers if provider not in SUPPORTED_PROVIDERS})
    if unsupported:
        raise ValueError(f"Unsupported providers: {','.join(unsupported)}")
    deduped: List[str] = []
    for provider in providers:
        if provider not in deduped:
            deduped.append(provider)
    return deduped


def _resolve_db_url(cli_db_url: str, cli_db_path: str) -> str:
    raw_url = str(cli_db_url or "").strip()
    if raw_url:
        return raw_url
    raw_path = str(cli_db_path or "").strip()
    if raw_path:
        path = Path(raw_path).resolve()
        return f"sqlite:///{path.as_posix()}"
    return resolve_webhook_db_url()


def _poll_delivery_id(provider: str, external_job_id: str, attempt: int, status: str) -> str:
    payload = f"poll|{provider}|{external_job_id}|{attempt}|{status}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _poll_event_id(provider: str, external_job_id: str, attempt: int, status: str) -> str:
    return f"poll:{provider}:{external_job_id}:{attempt}:{status}"


def _run_event_dedupe_key(
    provider: str,
    run_id: str,
    phase: str,
    step_id: str,
    partition_id: str,
    attempt: int,
    event_type: str,
    external_job_id: str,
    orphaned: bool,
) -> str:
    payload = "|".join(
        [
            "poll",
            provider,
            run_id,
            phase,
            step_id,
            partition_id,
            str(attempt),
            event_type,
            external_job_id,
            "orphaned" if orphaned else "linked",
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def run_poll_cycle(event_store: Any, providers: List[str]) -> Dict[str, Any]:
    jobs: List[Dict[str, Any]] = []
    for provider in providers:
        jobs.extend(event_store.list_pending_jobs(provider=provider, run_id=None, phase=None))
    jobs.sort(
        key=lambda row: (
            str(row.get("provider") or ""),
            str(row.get("run_id") or ""),
            str(row.get("phase") or ""),
            str(row.get("step_id") or ""),
            str(row.get("partition_id") or ""),
            _as_int(row.get("attempt"), 0),
            str(row.get("external_job_id") or ""),
        )
    )

    inserted = 0
    processed = 0
    updated_running = 0

    for job in jobs:
        provider = str(job.get("provider") or "").lower().strip()
        poll_fn = SUPPORTED_PROVIDERS.get(provider)
        if poll_fn is None:
            continue

        status = str(poll_fn(job) or "").strip().lower()
        if status not in TERMINAL_STATUSES:
            if status in {"running", "submitted"}:
                attempt = _as_int(job.get("attempt"), 1)
                event_store.update_async_job_status(
                    provider=provider,
                    external_job_id=str(job.get("external_job_id") or ""),
                    attempt=attempt,
                    status=status,
                    last_error=None,
                )
                updated_running += 1
            continue

        processed += 1
        run_id = str(job.get("run_id") or "")
        phase = str(job.get("phase") or "")
        step_id = str(job.get("step_id") or "")
        partition_id = str(job.get("partition_id") or "")
        attempt = _as_int(job.get("attempt"), 1)
        external_job_id = str(job.get("external_job_id") or "")

        latest_attempt = event_store.latest_attempt_for_tuple(
            run_id=run_id,
            phase=phase,
            step_id=step_id,
            partition_id=partition_id,
        )
        orphaned = latest_attempt is not None and attempt < int(latest_attempt)

        event_type = "job.completed" if status == "completed" else "job.failed"
        delivery_id = _poll_delivery_id(provider, external_job_id, attempt, status)
        event_id = _poll_event_id(provider, external_job_id, attempt, status)
        payload = {
            "source": "poller",
            "provider": provider,
            "status": status,
            "run_id": run_id,
            "phase": phase,
            "step_id": step_id,
            "partition_id": partition_id,
            "attempt": attempt,
            "external_job_id": external_job_id,
            "latest_attempt": int(latest_attempt) if latest_attempt is not None else None,
            "orphaned": bool(orphaned),
            "polled_at_utc": now_iso(),
        }

        inserted_event = event_store.insert_webhook_event_if_absent(
            WebhookEventInsert(
                provider=provider,
                idempotency_key=delivery_id,
                event_type=event_type,
                event_id=event_id,
                received_at_utc=now_iso(),
                payload_json=json.dumps(payload, ensure_ascii=True, sort_keys=True),
                headers_json="{}",
                signature_valid=True,
            )
        )

        if inserted_event:
            webhook_event_id = None
            if hasattr(event_store, "fetch_webhook_event_id"):
                webhook_event_id = event_store.fetch_webhook_event_id(provider, delivery_id)  # type: ignore[attr-defined]
            event_store.append_run_event(
                RunEventInsert(
                    run_id=run_id,
                    phase=phase,
                    step_id=step_id,
                    partition_id=partition_id,
                    provider=provider,
                    event_type=event_type,
                    event_id=event_id,
                    provider_ref=external_job_id,
                    webhook_event_id=webhook_event_id,
                    dedupe_key=_run_event_dedupe_key(
                        provider,
                        run_id,
                        phase,
                        step_id,
                        partition_id,
                        attempt,
                        event_type,
                        external_job_id,
                        orphaned,
                    ),
                    orphaned=orphaned,
                )
            )
            inserted += 1

        next_status = "orphaned" if orphaned else status
        last_error = "stale_attempt" if orphaned else ("provider_failed" if status == "failed" else None)
        event_store.update_async_job_status(
            provider=provider,
            external_job_id=external_job_id,
            attempt=attempt,
            status=next_status,
            last_error=last_error,
        )

    return {
        "providers": providers,
        "jobs_seen": len(jobs),
        "jobs_processed": processed,
        "jobs_marked_running": updated_running,
        "events_inserted": inserted,
    }


def main() -> None:
    parser = argparse.ArgumentParser("webhook-receiver-poller")
    parser.add_argument("--db-url", type=str, default="")
    parser.add_argument("--db-path", type=str, default="")
    parser.add_argument("--providers", type=str, default="xai,gemini")
    parser.add_argument("--interval-seconds", type=int, default=10)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    db_url = _resolve_db_url(args.db_url, args.db_path)
    ensure_migrations(db_url)
    event_store = build_event_store(db_url)
    providers = _parse_provider_list(args.providers)

    if args.once:
        print(json.dumps(run_poll_cycle(event_store, providers), indent=2, sort_keys=True))
        return

    while True:
        print(json.dumps(run_poll_cycle(event_store, providers), indent=2, sort_keys=True), flush=True)
        time.sleep(max(1, int(args.interval_seconds)))


if __name__ == "__main__":
    main()
