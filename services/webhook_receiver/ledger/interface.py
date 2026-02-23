from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


@dataclass(frozen=True)
class WebhookEventInsert:
    provider: str
    idempotency_key: str
    event_type: str
    event_id: Optional[str]
    received_at_utc: str
    payload_json: str
    headers_json: str
    signature_valid: bool


@dataclass(frozen=True)
class RunEventInsert:
    run_id: Optional[str]
    phase: Optional[str]
    step_id: Optional[str]
    partition_id: Optional[str]
    provider: str
    event_type: str
    event_id: Optional[str]
    provider_ref: Optional[str]
    webhook_event_id: Optional[int]
    dedupe_key: str
    orphaned: bool


@dataclass(frozen=True)
class AsyncJobInsert:
    provider: str
    job_kind: str
    external_job_id: str
    run_id: str
    phase: str
    step_id: str
    partition_id: str
    attempt: int
    status: str
    last_error: Optional[str] = None


class EventStore(ABC):
    @abstractmethod
    def insert_webhook_event_if_absent(self, event: WebhookEventInsert) -> bool:
        raise NotImplementedError

    @abstractmethod
    def append_run_event(self, event: RunEventInsert) -> None:
        raise NotImplementedError

    @abstractmethod
    def register_async_job(self, job: AsyncJobInsert) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_pending_jobs(self, provider: str, run_id: Optional[str], phase: Optional[str]) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def update_async_job_status(
        self,
        *,
        provider: str,
        external_job_id: str,
        attempt: int,
        status: str,
        last_error: Optional[str],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def latest_attempt_for_tuple(self, *, run_id: str, phase: str, step_id: str, partition_id: str) -> Optional[int]:
        raise NotImplementedError

    @abstractmethod
    def find_async_job(
        self,
        *,
        provider: str,
        external_job_id: str,
        attempt: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def list_completed_provider_refs(self, *, provider: str, run_id: str, phase: str) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def fetch_webhook_payload(self, *, provider: str, run_id: str, provider_ref: str) -> Optional[str]:
        raise NotImplementedError

def parse_db_url(raw_url: str) -> Dict[str, str]:
    value = (raw_url or "").strip()
    if not value:
        raise ValueError("WEBHOOK_DB_URL is required")
    if value.startswith("sqlite:///"):
        path = value.removeprefix("sqlite:///")
        if not path:
            raise ValueError("Invalid sqlite WEBHOOK_DB_URL")
        return {"backend": "sqlite", "path": "/" + path if not path.startswith("/") else path}
    parsed = urlparse(value)
    if parsed.scheme.startswith("postgresql"):
        return {"backend": "postgres", "url": value}
    raise ValueError(f"Unsupported WEBHOOK_DB_URL scheme: {parsed.scheme or value}")
