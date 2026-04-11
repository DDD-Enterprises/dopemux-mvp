from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any

from run_extraction_v5 import RunnerConfig, build_chat_payload, call_llm
from ..spend import estimate_tokens


@dataclass(frozen=True)
class XaiDirectAdapter:
    provider_name: str = "xai"
    surface_id: str = "surface_xai_api_v1"
    surface_class: str = "direct_provider_api"
    api_key_env: str = "XAI_API_KEY"

    def invoke(
        self,
        *,
        model_id: str,
        system_prompt: str,
        user_prompt: str,
        response_format: dict[str, Any],
        max_tokens: int,
        retry_max_attempts: int,
    ) -> dict[str, Any]:
        cfg = RunnerConfig(
            dry_run=False,
            max_files_docs=1,
            max_files_code=1,
            max_chars=1000,
            max_request_bytes=100_000,
            file_truncate_chars=500,
            home_scan_mode="safe",
            resume=False,
            fail_fast_auth=False,
            gemini_auth_mode="auto",
            gemini_transport="sdk",
            openai_transport="openai_sdk",
            xai_transport="openai_sdk",
            retry_policy="transport_only",
            retry_max_attempts=retry_max_attempts,
            retry_base_seconds=0.5,
            retry_max_seconds=2.0,
            phase_auth_fail_threshold=1,
            partition_workers=1,
            debug_phase_inputs=False,
            fail_fast_missing_inputs=False,
            routing_policy="balanced_grok_openrouter",
        )
        request_payload = build_chat_payload(
            self.provider_name,
            model_id,
            system_prompt,
            user_prompt,
            response_format_override=response_format,
        )
        request_payload["max_tokens"] = max_tokens
        started = perf_counter()
        response = call_llm(
            self.provider_name,
            model_id,
            self.api_key_env,
            system_prompt,
            user_prompt,
            cfg,
            response_format_override=response_format,
        )
        ended = perf_counter()
        request_payload_bytes = estimate_tokens(system_prompt, user_prompt) * 4
        return {
            "ok": bool(response.get("ok")),
            "request_payload": request_payload,
            "response_text": str(response.get("text") or ""),
            "meta": dict(response.get("meta") or {}),
            "latency_ms": round((ended - started) * 1000, 3),
            "request_payload_bytes_estimate": request_payload_bytes,
        }
