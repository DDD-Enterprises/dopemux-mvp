from __future__ import annotations

import os
from typing import Any, Dict

from .base import ProviderEvent


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


class OpenAIWebhookAdapter:
    provider = "openai"

    def __init__(self, secret: str):
        self.secret = secret.strip()
        if not self.secret:
            raise ValueError("missing_openai_webhook_secret")

    def verify_and_normalize(self, raw_body: bytes, headers: Dict[str, str]) -> ProviderEvent:
        try:
            from openai import OpenAI
        except Exception as exc:  # pragma: no cover - runtime dependency guard
            raise RuntimeError(f"openai_sdk_unavailable:{type(exc).__name__}") from exc

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "sk-not-used"))
        event = client.webhooks.unwrap(raw_body.decode("utf-8", errors="replace"), headers, secret=self.secret)
        payload = event_to_dict(event)
        if not payload:
            raise RuntimeError("empty_event_payload")

        delivery_id = (
            headers.get("webhook-id")
            or headers.get("Webhook-Id")
            or headers.get("X-Webhook-Id")
            or ""
        ).strip()
        if not delivery_id:
            raise RuntimeError("missing_webhook_id")
        event_id = str(payload.get("id") or "")
        event_type = str(payload.get("type") or "")
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
        attempt = metadata.get("attempt")
        attempt_int = int(attempt) if isinstance(attempt, int) else None
        return ProviderEvent(
            provider=self.provider,
            delivery_id=delivery_id,
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            headers=headers,
            external_id=str(data.get("id") or ""),
            run_id=str(metadata.get("run_id") or ""),
            phase=str(metadata.get("phase") or ""),
            step_id=str(metadata.get("step_id") or ""),
            partition_id=str(metadata.get("partition_id") or ""),
            attempt=attempt_int,
        )
