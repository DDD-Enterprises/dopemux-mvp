#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from providers.gemini_poller import poll_status as poll_gemini_status
from providers.xai_poller import poll_status as poll_xai_status
from server import db_path_from_env, ingest_polled_job_event, init_db, list_pending_jobs


def _resolve_db_path(cli_db: str) -> Path:
    raw = str(cli_db or "").strip()
    if raw:
        return Path(raw)
    return db_path_from_env()


def run_poll_cycle(db_path: Path, providers: list[str]) -> dict:
    jobs = list_pending_jobs(db_path, providers)
    inserted = 0
    processed = 0
    for job in jobs:
        provider = str(job.get("provider") or "").lower()
        if provider == "xai":
            status = poll_xai_status(job)
        elif provider == "gemini":
            status = poll_gemini_status(job)
        else:
            continue
        if status not in {"completed", "failed"}:
            continue
        processed += 1
        if ingest_polled_job_event(db_path, job, status):
            inserted += 1
    payload = {
        "db_path": str(db_path.resolve()),
        "providers": providers,
        "jobs_seen": len(jobs),
        "jobs_processed": processed,
        "events_inserted": inserted,
    }
    return payload


def main() -> None:
    parser = argparse.ArgumentParser("webhook-receiver-poller")
    parser.add_argument("--db-path", type=str, default="")
    parser.add_argument("--providers", type=str, default="xai,gemini")
    parser.add_argument("--interval-seconds", type=int, default=10)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    db_path = _resolve_db_path(args.db_path)
    init_db(db_path)
    providers = [token.strip().lower() for token in str(args.providers).split(",") if token.strip()]
    if args.once:
        print(json.dumps(run_poll_cycle(db_path, providers), indent=2, sort_keys=True))
        return
    while True:
        print(json.dumps(run_poll_cycle(db_path, providers), indent=2, sort_keys=True), flush=True)
        time.sleep(max(1, int(args.interval_seconds)))


if __name__ == "__main__":
    main()
