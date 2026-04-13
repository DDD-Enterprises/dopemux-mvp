from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import requests


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMRuntimeDeps:
    live_llm_calls_blocked_for_tests: Callable[[], bool]
    live_llm_tests_env: str
    llm_base_url: Callable[[str, Any], str]
    transport_for_provider: Callable[[str, Any], str]
    resolve_api_key: Callable[[str, str], Tuple[str, str]]
    build_chat_payload: Callable[..., Dict[str, Any]]
    serialize_payload_body: Callable[[Dict[str, Any]], str]
    measure_payload_bytes_from_body: Callable[[str], int]
    gemini_auth_mode_sequence: Callable[[str, str], List[str]]
    make_url: Callable[[str, str, Any, str, str], str]
    make_headers: Callable[[str, str, Any, str], Dict[str, str]]
    sdk_auth_present_flags: Callable[[str, bool], Dict[str, Any]]
    build_auth_present_flags: Callable[[Dict[str, str], bool], Dict[str, Any]]
    endpoint_effective: Callable[[str], str]
    endpoint_fingerprint: Callable[[str], Dict[str, Any]]
    provider_signature: Callable[[str, str, str, Optional[str]], str]
    get_http_session: Callable[[], requests.Session]
    get_gemini_client: Callable[[str], Any]
    extract_text_from_gemini_response: Callable[[Any], str]
    get_xai_client: Callable[[str], Any]
    get_openrouter_client: Callable[[str], Any]
    get_openai_client: Callable[[Any, str], Any]
    extract_text_from_chat_completion: Callable[[Any], str]
    summarize_llm_response: Callable[..., Dict[str, Any]]
    exception_status_code: Callable[[Exception], Optional[int]]
    exception_response_text: Callable[[Exception], str]
    classify_failure_type: Callable[[Optional[int], str, str], str]
    extract_provider_error_reason: Callable[[str], Optional[str]]
    sanitize_error_text: Callable[[str], str]
    capture_exception_metadata: Callable[[Exception], Dict[str, Any]]
    new_trace_id: Callable[[], str]
    new_span_id: Callable[[], str]
    cost_abort_failure_meta: Callable[..., Dict[str, Any]]
    should_retry: Callable[[Optional[int], str, Optional[Exception], str], bool]
    backoff_seconds: Callable[[int, float, float], float]
    is_spend_aborted: Callable[[], bool]
    sha256_text: Callable[[Path], str]
    runner_script: Path
    is_auth_classified_failure: Callable[[Optional[str]], bool]
    classify_escalation_class: Callable[..., str]
    is_break_glass_opus_route: Callable[[Tuple[str, str, str]], bool]
    provider_api_key_env: Dict[str, str]
    max_files_for_phase: Callable[[str, Any], int]
    estimate_text_tokens: Callable[[str, str], int]
    project_output_tokens: Callable[[int], int]
    check_projected_cost_limit: Callable[..., None]
    accumulate_runtime_spend: Callable[..., Optional[Dict[str, Any]]]
    cost_limit_exceeded_error: type[Exception]
    now_iso: Callable[[], str]
    strip_outer_json_fence: Callable[[str], Optional[str]]
    extract_first_fenced_json_block: Callable[[str], Optional[str]]
    extract_first_json_object: Callable[[str], Optional[str]]
    is_semantic_eof_eligible: Callable[[json.JSONDecodeError, str], bool]
    try_repair_json_truncation: Callable[[str, json.JSONDecodeError], Optional[str]]


def is_retryable_exception(exc: Exception) -> bool:
    text = str(exc).lower()
    return (
        isinstance(exc, requests.exceptions.Timeout)
        or "timeout" in text
        or "connection reset" in text
    )


def should_retry(
    status_code: Optional[int],
    failure_type: str,
    exc: Optional[Exception],
    retry_policy: str,
) -> bool:
    if retry_policy == "none":
        return False
    if failure_type.startswith("auth_") or failure_type in {
        "quota_or_billing",
        "api_key_missing_or_invalid",
        "permission_denied",
    }:
        return False
    if status_code in {408, 429, 500, 502, 503, 504}:
        return True
    if exc is not None and is_retryable_exception(exc):
        return True
    return False


def backoff_seconds(attempt: int, base_seconds: float, max_seconds: float) -> float:
    if attempt <= 1:
        return 0.0
    delay = base_seconds * (2 ** (attempt - 2))
    return min(delay, max_seconds)


def is_auth_classified_failure(failure_type: Optional[str]) -> bool:
    if not failure_type:
        return False
    return failure_type.startswith("auth_") or failure_type in {
        "api_key_missing_or_invalid",
        "permission_denied",
        "quota_or_billing",
        "auth_rejected",
    }


def call_llm(
    deps: LLMRuntimeDeps,
    provider: str,
    model_id: str,
    api_key_env: str,
    system_prompt: str,
    user_content: str,
    cfg: Any,
    force_json_output: bool = False,
    response_format_override: Optional[Dict[str, Any]] = None,
    structured_output_override: Optional[Dict[str, Any]] = None,
    retry_callback: Optional[Callable] = None,
    timeout_seconds: Optional[int] = None,
    trace_context: Optional[Dict[str, Any]] = None,
    lifecycle_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> Dict[str, Any]:
    if deps.live_llm_calls_blocked_for_tests():
        message = "Live LLM call blocked in test context."
        logger.error(message)
        raise RuntimeError(message)
    base_url = deps.llm_base_url(provider, cfg)
    transport = deps.transport_for_provider(provider, cfg)
    api_key, resolved_api_key_env = deps.resolve_api_key(provider, api_key_env)
    payload = deps.build_chat_payload(
        provider,
        model_id,
        system_prompt,
        user_content,
        force_json_output=force_json_output,
        response_format_override=response_format_override,
    )
    body = deps.serialize_payload_body(payload)
    request_payload_bytes = deps.measure_payload_bytes_from_body(body)
    request_payload_bytes_mode = (
        "exact_http" if transport == "openai_compat_http" else "sdk_estimate"
    )
    gemini_mode_requested = cfg.gemini_auth_mode if provider == "gemini" else None
    gemini_family = (
        (
            "openai_compat"
            if provider == "gemini" and transport == "openai_compat_http"
            else "native"
        )
        if provider == "gemini"
        else None
    )
    using_structured_override = isinstance(response_format_override, dict)
    structured_output: Dict[str, Any] = {
        "enabled": bool(
            (provider == "gemini" and force_json_output) or using_structured_override
        ),
        "mime_type": (
            "application/json" if provider == "gemini" and force_json_output else None
        ),
        "schema": None,
        "schema_name": None,
        "schema_version": None,
        "strict": False,
        "contract_lane": None,
        "transport_mode": (
            "response_format_json_object"
            if provider == "gemini"
            and transport == "openai_compat_http"
            and force_json_output
            else (
                "response_mime_type"
                if provider == "gemini" and force_json_output
                else None
            )
        ),
    }
    if using_structured_override:
        rf_type = str(response_format_override.get("type") or "").strip()
        if rf_type == "json_schema":
            json_schema = (
                response_format_override.get("json_schema")
                if isinstance(response_format_override.get("json_schema"), dict)
                else {}
            )
            schema_name = str(json_schema.get("name") or "").strip() or None
            structured_output.update(
                {
                    "mime_type": "application/json",
                    "schema": schema_name,
                    "schema_name": schema_name,
                    "strict": bool(json_schema.get("strict")),
                    "transport_mode": "response_format_json_schema",
                }
            )
        elif rf_type == "json_object":
            structured_output.update(
                {
                    "mime_type": "application/json",
                    "transport_mode": "response_format_json_object",
                }
            )
        else:
            structured_output["transport_mode"] = (
                f"response_format_{rf_type}" if rf_type else "response_format_custom"
            )
    if isinstance(structured_output_override, dict):
        structured_output.update(structured_output_override)

    auth_mode_sequence = (
        deps.gemini_auth_mode_sequence(cfg.gemini_auth_mode, base_url)
        if provider == "gemini"
        else ["sdk_bearer"]
    )
    mode_index = 0
    effective_mode = auth_mode_sequence[mode_index]
    endpoint_url = (
        f"{base_url}/v1beta/models/{model_id}:generateContent"
        if provider == "gemini" and transport != "openai_compat_http"
        else f"{base_url}/chat/completions"
    )
    sent_header_keys: List[str] = []
    auth_flags = deps.sdk_auth_present_flags(provider, bool(api_key))
    base_trace_context = dict(trace_context or {})
    trace_id = str(base_trace_context.get("trace_id") or "").strip() or deps.new_trace_id()
    request_parent_span_id = (
        str(base_trace_context.get("parent_span_id") or "").strip() or None
    )
    if transport == "openai_compat_http":
        endpoint_url = deps.make_url(provider, base_url, cfg, api_key, effective_mode)
        headers = deps.make_headers(provider, api_key, cfg, effective_mode)
        sent_header_keys = sorted(list(headers.keys()))
        auth_flags = deps.build_auth_present_flags(
            headers, provider == "gemini" and effective_mode == "query_key"
        )

    if not api_key:
        logger.error("Missing API key env var")
        if provider == "gemini":
            logger.error(
                "Gemini credentials are missing in canonical repo-root env configuration."
            )
        return {
            "ok": False,
            "text": "",
            "meta": {
                "provider": provider,
                "model_id": model_id,
                "endpoint_base_url": base_url,
                "endpoint_effective": deps.endpoint_effective(endpoint_url),
                **deps.endpoint_fingerprint(endpoint_url),
                "status_code": None,
                "failure_type": "auth_missing",
                "sent_header_keys": sent_header_keys,
                "auth_present_flags": auth_flags,
                "gemini_auth_mode_requested": gemini_mode_requested,
                "gemini_auth_mode_effective": None,
                "provider_signature": deps.provider_signature(
                    provider, model_id, endpoint_url, None
                ),
                "provider_error_reason": "MISSING_API_KEY_ENV",
                "api_key_env_requested": "***redacted***",
                "api_key_env_resolved": "***redacted***",
                "gemini_endpoint_family": gemini_family,
                "gemini_auth_attempt_sequence": (
                    auth_mode_sequence if provider == "gemini" else None
                ),
                "request_payload_bytes": request_payload_bytes,
                "request_payload_bytes_mode": request_payload_bytes_mode,
                "transport": transport,
                "trace_id": trace_id,
                "parent_span_id": request_parent_span_id,
                "retry_trace": [],
                "structured_output": structured_output,
            },
        }

    if deps.is_spend_aborted():
        return {
            "ok": False,
            "text": "",
            "meta": deps.cost_abort_failure_meta(
                provider=provider,
                model_id=model_id,
                api_key_env=api_key_env,
                base_url=base_url,
                request_payload_bytes=request_payload_bytes,
                request_payload_bytes_mode=request_payload_bytes_mode,
                sent_header_keys=sent_header_keys,
                auth_flags=auth_flags,
                transport=transport,
                gemini_mode_requested=gemini_mode_requested,
                gemini_mode_effective=(
                    effective_mode if provider == "gemini" else None
                ),
                gemini_family=gemini_family,
                auth_mode_sequence=(
                    auth_mode_sequence if provider == "gemini" else None
                ),
                structured_output=structured_output,
            ),
        }

    last_failure_meta: Dict[str, Any] = {
        "provider": provider,
        "model_id": model_id,
        "endpoint_base_url": base_url,
        "endpoint_effective": deps.endpoint_effective(endpoint_url),
        **deps.endpoint_fingerprint(endpoint_url),
        "status_code": None,
        "failure_type": "unknown",
        "request_payload_bytes": request_payload_bytes,
        "request_payload_bytes_mode": request_payload_bytes_mode,
        "sent_header_keys": sent_header_keys,
        "auth_present_flags": auth_flags,
        "gemini_auth_mode_requested": gemini_mode_requested,
        "gemini_auth_mode_effective": effective_mode if provider == "gemini" else None,
        "provider_signature": deps.provider_signature(
            provider,
            model_id,
            endpoint_url,
            effective_mode if provider == "gemini" else None,
        ),
        "provider_error_reason": None,
        "api_key_env_requested": api_key_env,
        "api_key_env_resolved": resolved_api_key_env,
        "gemini_endpoint_family": gemini_family,
        "gemini_auth_attempt_sequence": (
            auth_mode_sequence if provider == "gemini" else None
        ),
        "transport": transport,
        "retry_trace": [],
        "structured_output": structured_output,
    }
    retry_trace: List[Dict[str, Any]] = []
    total_retry_delay = 0.0
    overall_timeout_seconds = max(
        1, int(timeout_seconds if timeout_seconds is not None else 180)
    )
    started_monotonic = time.monotonic()

    def _emit_lifecycle(status: str, **fields: Any) -> None:
        if lifecycle_callback is None:
            return
        payload = {
            "phase": base_trace_context.get("phase"),
            "step_id": base_trace_context.get("step_id"),
            "partition_id": base_trace_context.get("partition_id"),
            "trace_id": trace_id,
            "parent_span_id": request_parent_span_id,
            "provider": provider,
            "model_id": model_id,
            "route": base_trace_context.get("route"),
            "routing_policy": base_trace_context.get("routing_policy"),
            "hop": base_trace_context.get("hop"),
            "status": status,
        }
        payload.update(fields)
        lifecycle_callback({k: v for k, v in payload.items() if v is not None})

    def _remaining_timeout_seconds() -> int:
        elapsed = time.monotonic() - started_monotonic
        return max(1, int(overall_timeout_seconds - elapsed))

    attempt = 0
    while attempt < cfg.retry_max_attempts:
        attempt += 1
        status_code: Optional[int] = None
        response_body = ""
        failure_type = "unknown"
        provider_error_reason = None
        attempt_span_id = deps.new_span_id()
        _emit_lifecycle(
            "started",
            span_id=attempt_span_id,
            attempt=attempt,
            request_payload_bytes=request_payload_bytes,
        )
        try:
            response_json: Optional[Dict[str, Any]] = None
            if transport == "openai_compat_http":
                headers = deps.make_headers(provider, api_key, cfg, effective_mode)
                endpoint_url = deps.make_url(
                    provider, base_url, cfg, api_key, effective_mode
                )
                auth_flags = deps.build_auth_present_flags(
                    headers, provider == "gemini" and effective_mode == "query_key"
                )
                sent_header_keys = sorted(list(headers.keys()))
                response = deps.get_http_session().post(
                    endpoint_url,
                    headers=headers,
                    data=body,
                    timeout=_remaining_timeout_seconds(),
                )
                response.raise_for_status()
                status_code = response.status_code
                response_json = response.json()
                response_text = response_json["choices"][0]["message"]["content"]
            elif provider == "gemini":
                client = deps.get_gemini_client(api_key)
                response = client.models.generate_content(
                    model=model_id,
                    contents=user_content,
                    config={
                        "temperature": 0.1,
                        "system_instruction": system_prompt,
                        **(
                            {"response_mime_type": "application/json"}
                            if force_json_output
                            else {}
                        ),
                    },
                )
                status_code = 200
                response_text = deps.extract_text_from_gemini_response(response)
            else:
                if provider == "xai":
                    client = deps.get_xai_client(api_key)
                elif provider == "openrouter":
                    client = deps.get_openrouter_client(api_key)
                else:
                    client = deps.get_openai_client(None, api_key)
                chat_kwargs: Dict[str, Any] = {
                    "model": model_id,
                    "messages": payload["messages"],
                    "timeout": _remaining_timeout_seconds(),
                }
                if "temperature" in payload:
                    chat_kwargs["temperature"] = payload["temperature"]
                if "response_format" in payload:
                    chat_kwargs["response_format"] = payload["response_format"]
                response = client.chat.completions.create(**chat_kwargs)
                status_code = 200
                response_text = deps.extract_text_from_chat_completion(response)

            response_summary = deps.summarize_llm_response(
                provider=provider,
                transport=transport,
                response_obj=response,
                response_json=response_json,
                response_text=response_text,
            )
            retry_trace.append(
                {
                    "attempt": attempt,
                    "status_code": status_code,
                    "failure_type": None,
                    "delay_seconds": 0.0,
                    "gemini_auth_mode_effective": (
                        effective_mode if provider == "gemini" else None
                    ),
                    "provider_error_reason": None,
                    "response_received": True,
                    "response_summary": response_summary,
                }
            )
            _emit_lifecycle(
                "completed",
                span_id=attempt_span_id,
                attempt=attempt,
                latency_ms=int((time.monotonic() - started_monotonic) * 1000),
                status_code=status_code,
                finish_reason=response_summary.get("finish_reason"),
                prompt_tokens=response_summary.get("prompt_tokens"),
                completion_tokens=response_summary.get("completion_tokens"),
                upstream_request_id=response_summary.get("response_id"),
                request_payload_bytes=request_payload_bytes,
            )
            return {
                "ok": True,
                "text": response_text,
                "meta": {
                    "provider": provider,
                    "model_id": model_id,
                    "endpoint_base_url": base_url,
                    "endpoint_effective": deps.endpoint_effective(endpoint_url),
                    **deps.endpoint_fingerprint(endpoint_url),
                    "status_code": status_code,
                    "failure_type": None,
                    "request_payload_bytes": request_payload_bytes,
                    "request_payload_bytes_mode": request_payload_bytes_mode,
                    "sent_header_keys": sent_header_keys,
                    "auth_present_flags": auth_flags,
                    "gemini_auth_mode_requested": gemini_mode_requested,
                    "gemini_auth_mode_effective": (
                        effective_mode if provider == "gemini" else None
                    ),
                    "provider_signature": deps.provider_signature(
                        provider,
                        model_id,
                        endpoint_url,
                        effective_mode if provider == "gemini" else None,
                    ),
                    "provider_error_reason": None,
                    "api_key_env_requested": api_key_env,
                    "api_key_env_resolved": resolved_api_key_env,
                    "gemini_endpoint_family": gemini_family,
                    "gemini_auth_attempt_sequence": (
                        auth_mode_sequence if provider == "gemini" else None
                    ),
                    "transport": transport,
                    "trace_id": trace_id,
                    "span_id": attempt_span_id,
                    "parent_span_id": request_parent_span_id,
                    "retry_trace": retry_trace,
                    "response_received": True,
                    "response_summary": response_summary,
                    "structured_output": structured_output,
                },
            }
        except Exception as exc:
            status_code = deps.exception_status_code(exc)
            response_body = deps.exception_response_text(exc)[:1200]
            failure_type = deps.classify_failure_type(
                status_code, response_body, str(exc)
            )
            provider_error_reason = deps.extract_provider_error_reason(response_body)
            safe_exc = deps.sanitize_error_text(str(exc))
            safe_body = deps.sanitize_error_text(response_body)
            exception_info = deps.capture_exception_metadata(exc)
            retry_trace.append(
                {
                    "attempt": attempt,
                    "status_code": status_code,
                    "failure_type": failure_type,
                    "delay_seconds": 0.0,
                    "gemini_auth_mode_effective": (
                        effective_mode if provider == "gemini" else None
                    ),
                    "provider_error_reason": provider_error_reason,
                    "response_received": False,
                    **exception_info,
                }
            )
            last_failure_meta = {
                "provider": provider,
                "model_id": model_id,
                "endpoint_base_url": base_url,
                "endpoint_effective": deps.endpoint_effective(endpoint_url),
                **deps.endpoint_fingerprint(endpoint_url),
                "status_code": status_code,
                "failure_type": failure_type,
                "request_payload_bytes": request_payload_bytes,
                "request_payload_bytes_mode": request_payload_bytes_mode,
                "sent_header_keys": sent_header_keys,
                "auth_present_flags": auth_flags,
                "gemini_auth_mode_requested": gemini_mode_requested,
                "gemini_auth_mode_effective": (
                    effective_mode if provider == "gemini" else None
                ),
                "provider_signature": deps.provider_signature(
                    provider,
                    model_id,
                    endpoint_url,
                    effective_mode if provider == "gemini" else None,
                ),
                "provider_error_reason": provider_error_reason,
                **exception_info,
                "api_key_env_requested": api_key_env,
                "api_key_env_resolved": resolved_api_key_env,
                "gemini_endpoint_family": gemini_family,
                "gemini_auth_attempt_sequence": (
                    auth_mode_sequence if provider == "gemini" else None
                ),
                "transport": transport,
                "trace_id": trace_id,
                "span_id": attempt_span_id,
                "parent_span_id": request_parent_span_id,
                "retry_trace": retry_trace,
                "response_received": False,
                "structured_output": structured_output,
            }
            _emit_lifecycle(
                "failed",
                span_id=attempt_span_id,
                attempt=attempt,
                latency_ms=int((time.monotonic() - started_monotonic) * 1000),
                status_code=status_code,
                failure_type=failure_type,
                upstream_request_id=exception_info.get("request_id"),
                request_payload_bytes=request_payload_bytes,
                extra={
                    "provider_error_reason": provider_error_reason,
                    "exception_type": exception_info.get("exception_type"),
                },
            )
            if response_body:
                logger.warning(
                    "LLM call failed attempt %s/%s provider=%s model=%s status=%s failure_type=%s: %s | body=%s",
                    attempt,
                    cfg.retry_max_attempts,
                    provider,
                    model_id,
                    status_code,
                    failure_type,
                    safe_exc,
                    safe_body,
                )
            else:
                logger.warning(
                    "LLM call failed attempt %s/%s provider=%s model=%s status=%s failure_type=%s: %s",
                    attempt,
                    cfg.retry_max_attempts,
                    provider,
                    model_id,
                    status_code,
                    failure_type,
                    safe_exc,
                )

            if (
                transport == "openai_compat_http"
                and provider == "gemini"
                and cfg.gemini_auth_mode == "auto"
                and deps.is_auth_classified_failure(failure_type)
                and mode_index + 1 < len(auth_mode_sequence)
            ):
                mode_index += 1
                effective_mode = auth_mode_sequence[mode_index]
                logger.warning(
                    "Gemini openai_compat auth pivot after auth failure: next_mode=%s endpoint=%s",
                    effective_mode,
                    endpoint_url,
                )
                continue

            if not deps.should_retry(status_code, failure_type, exc, cfg.retry_policy):
                break

            delay_seconds = deps.backoff_seconds(
                attempt + 1, cfg.retry_base_seconds, cfg.retry_max_seconds
            )
            retry_trace[-1]["delay_seconds"] = delay_seconds
            total_retry_delay += delay_seconds
            if retry_callback is not None:
                try:
                    retry_callback(attempt + 1, status_code, failure_type, delay_seconds)
                except Exception:
                    pass
            if delay_seconds > 0:
                time.sleep(delay_seconds)
    logger.error(
        "LLM call failed after %s attempts (%.1fs retry delay) provider=%s model=%s.",
        attempt,
        total_retry_delay,
        provider,
        model_id,
    )
    last_failure_meta["total_retry_delay_seconds"] = total_retry_delay
    return {
        "ok": False,
        "text": "",
        "meta": last_failure_meta,
    }


def call_llm_with_ladder(
    deps: LLMRuntimeDeps,
    *,
    phase: str,
    step_id: str,
    partition_id: str,
    routing_policy: str,
    routing_tier: str,
    ladder: Sequence[Tuple[str, str, str]],
    cfg: Any,
    execute_attempt: Callable[[Tuple[str, str, str], int], Dict[str, Any]],
    ui: Optional[Any] = None,
) -> Dict[str, Any]:
    denylist = {str(provider).strip().lower() for provider in cfg.provider_denylist}
    if denylist:
        ladder = [
            tuple(route)
            for route in ladder
            if str(route[0]).strip().lower() not in denylist
        ]
    if not ladder:
        return {
            "response_text": "",
            "request_meta": {
                "failure_type": "routing_empty_ladder",
                "provider_error_reason": (
                    f"provider_denylist:{','.join(sorted(denylist))}"
                    if denylist
                    else "No routes configured for tier."
                ),
            },
            "artifacts": [],
            "route": ("", "", ""),
            "escalation_trigger": (
                "routing_all_routes_denylisted" if denylist else "routing_empty_ladder"
            ),
            "route_attempts": [],
        }

    max_hops = 1 if cfg.disable_escalation else max(1, int(cfg.escalation_max_hops) + 1)
    max_hops = min(max_hops, len(ladder))
    attempts: List[Dict[str, Any]] = []
    final_payload: Optional[Dict[str, Any]] = None
    opus_eligible: Optional[bool] = None
    opus_block_reason: Optional[str] = None
    for hop_index in range(max_hops):
        route = tuple(ladder[hop_index])
        provider, model_id, api_key_env = route
        payload = execute_attempt(route, hop_index)
        request_meta = (
            payload.get("request_meta")
            if isinstance(payload.get("request_meta"), dict)
            else {}
        )
        escalation_trigger = str(payload.get("escalation_trigger") or "").strip() or None
        escalation_class = deps.classify_escalation_class(
            phase=phase,
            escalation_trigger=escalation_trigger,
            request_meta=request_meta,
        )
        request_meta["escalation_class"] = escalation_class
        request_meta.setdefault("opus_eligible", None)
        request_meta.setdefault("opus_block_reason", None)
        payload["request_meta"] = request_meta
        attempts.append(
            {
                "hop_index": hop_index + 1,
                "provider": provider,
                "model_id": model_id,
                "api_key_env": api_key_env,
                "failure_type": request_meta.get("failure_type"),
                "status_code": request_meta.get("status_code"),
                "escalation_trigger": escalation_trigger,
                "escalation_class": escalation_class,
                "ok": bool(payload.get("artifacts_ok", False)),
            }
        )
        final_payload = dict(payload)
        if not escalation_trigger or hop_index + 1 >= max_hops:
            break
        next_route = tuple(ladder[hop_index + 1])
        if (
            deps.is_break_glass_opus_route(next_route)
            and escalation_class != "hard_reconciliation"
        ):
            opus_eligible = False
            opus_block_reason = f"blocked_for_escalation_class:{escalation_class or 'none'}"
            request_meta["opus_eligible"] = False
            request_meta["opus_block_reason"] = opus_block_reason
            final_payload["request_meta"] = request_meta
            break
        if deps.is_break_glass_opus_route(next_route):
            opus_eligible = True
            opus_block_reason = None
            request_meta["opus_eligible"] = True
            request_meta["opus_block_reason"] = None
        if ui is not None:
            next_provider, next_model, _ = next_route
            ui.escalation_event(
                phase=phase,
                step_id=step_id,
                partition_id=partition_id,
                reason=escalation_trigger,
                from_route=f"{provider}/{model_id}",
                to_route=f"{next_provider}/{next_model}",
                hop=hop_index + 1,
            )

    if final_payload is None:
        final_payload = {
            "response_text": "",
            "request_meta": {"failure_type": "routing_unresolved"},
            "artifacts": [],
            "route": tuple(ladder[0]),
            "escalation_trigger": "routing_unresolved",
        }
    final_request_meta = (
        dict(final_payload.get("request_meta"))
        if isinstance(final_payload.get("request_meta"), dict)
        else {}
    )
    final_request_meta["routing_tier"] = routing_tier
    final_request_meta["routing_policy"] = routing_policy
    final_request_meta["route_hop_total"] = len(attempts)
    final_request_meta["route_attempts"] = attempts
    final_request_meta["route_hop_index"] = int(attempts[-1]["hop_index"]) if attempts else 1
    final_request_meta["escalation_trigger"] = final_payload.get("escalation_trigger")
    final_request_meta.setdefault("escalation_class", "none")
    if opus_eligible is not None:
        final_request_meta["opus_eligible"] = opus_eligible
    else:
        final_request_meta.setdefault("opus_eligible", None)
    if opus_block_reason is not None:
        final_request_meta["opus_block_reason"] = opus_block_reason
    else:
        final_request_meta.setdefault("opus_block_reason", None)
    final_route = tuple(final_payload.get("route") or ("", "", ""))
    final_request_meta["provider"] = (
        final_route[0] if len(final_route) > 0 else final_request_meta.get("provider")
    )
    final_request_meta["model_id"] = (
        final_route[1] if len(final_route) > 1 else final_request_meta.get("model_id")
    )
    return {**final_payload, "request_meta": final_request_meta}


def parse_json_from_response_with_provenance(
    deps: LLMRuntimeDeps,
    text: str,
) -> Tuple[Optional[Any], Dict[str, Any]]:
    provenance = {
        "repair_applied": False,
        "repair_type": None,
        "original_response_length": len(text) if text else 0,
        "repaired_response_length": len(text) if text else 0,
        "chars_lost": 0,
        "chars_delta": 0,
    }
    if not text:
        return None, provenance
    stripped = text.strip()
    if not stripped:
        return None, provenance
    try:
        return json.loads(stripped), provenance
    except json.JSONDecodeError:
        pass
    except Exception:
        pass

    defenced = deps.strip_outer_json_fence(stripped)
    if defenced and defenced != stripped:
        try:
            parsed = json.loads(defenced)
            provenance.update(
                {
                    "repair_applied": True,
                    "repair_type": "strip_outer_json_fence",
                    "repaired_response_length": len(defenced),
                    "chars_delta": len(defenced) - len(stripped),
                }
            )
            return parsed, provenance
        except Exception:
            pass

    fenced_block = deps.extract_first_fenced_json_block(stripped)
    if fenced_block and fenced_block != stripped:
        try:
            parsed = json.loads(fenced_block)
            provenance.update(
                {
                    "repair_applied": True,
                    "repair_type": "extract_first_fenced_json_block",
                    "repaired_response_length": len(fenced_block),
                    "chars_delta": len(fenced_block) - len(stripped),
                }
            )
            return parsed, provenance
        except Exception:
            pass

    salvaged_object = deps.extract_first_json_object(stripped)
    if salvaged_object and salvaged_object != stripped:
        try:
            parsed = json.loads(salvaged_object)
            provenance.update(
                {
                    "repair_applied": True,
                    "repair_type": "extract_first_json_object",
                    "repaired_response_length": len(salvaged_object),
                    "chars_delta": len(salvaged_object) - len(stripped),
                }
            )
            return parsed, provenance
        except Exception:
            pass

    try:
        json.loads(stripped)
    except json.JSONDecodeError as exc:
        if deps.is_semantic_eof_eligible(exc, stripped):
            repaired = deps.try_repair_json_truncation(stripped, exc)
            if repaired:
                try:
                    parsed = json.loads(repaired)
                    provenance.update(
                        {
                            "repair_applied": True,
                            "repair_type": "try_repair_json_truncation",
                            "repaired_response_length": len(repaired),
                            "chars_delta": len(repaired) - len(stripped),
                        }
                    )
                    return parsed, provenance
                except Exception:
                    pass

    return None, provenance


def parse_json_from_response(
    deps: LLMRuntimeDeps,
    text: str,
    metadata_out: Optional[Dict[str, Any]] = None,
) -> Optional[Any]:
    parsed, provenance = parse_json_from_response_with_provenance(deps, text)
    if isinstance(metadata_out, dict):
        metadata_out.clear()
        metadata_out.update(provenance)
        metadata_out["truncation_salvage"] = bool(provenance.get("repair_applied"))
        metadata_out["lossy"] = bool(provenance.get("repair_applied"))
    return parsed


def coerce_artifacts_from_response(
    parsed: Optional[Any],
    raw_text: str,
    expected_artifacts: Tuple[str, ...],
) -> List[Dict[str, Any]]:
    expected_set = set(expected_artifacts)

    if isinstance(parsed, list):
        list_artifacts: List[Dict[str, Any]] = []
        for entry in parsed:
            if not isinstance(entry, dict):
                continue
            artifact_name_value = entry.get("artifact_name")
            if not isinstance(artifact_name_value, str):
                continue
            artifact_name = artifact_name_value.strip()
            if artifact_name not in expected_set:
                continue
            if "payload" not in entry:
                continue
            list_artifacts.append(
                {"artifact_name": artifact_name, "payload": entry.get("payload")}
            )
        if list_artifacts:
            return list_artifacts

    if isinstance(parsed, dict) and isinstance(parsed.get("artifacts"), list):
        artifacts: List[Dict[str, Any]] = []
        for entry in parsed["artifacts"]:
            if not isinstance(entry, dict):
                continue
            artifact_name = str(entry.get("artifact_name", "")).strip()
            if artifact_name not in expected_set:
                continue
            artifacts.append({"artifact_name": artifact_name, "payload": entry.get("payload")})
        if artifacts:
            return artifacts

    if isinstance(parsed, dict):
        artifact_name = str(parsed.get("artifact_name", "")).strip()
        if artifact_name in expected_set and "payload" in parsed:
            return [{"artifact_name": artifact_name, "payload": parsed.get("payload")}]

    if isinstance(parsed, dict):
        keyed_artifacts: List[Dict[str, Any]] = []
        for artifact_name in expected_artifacts:
            if artifact_name in parsed:
                keyed_artifacts.append(
                    {"artifact_name": artifact_name, "payload": parsed[artifact_name]}
                )
        if keyed_artifacts:
            return keyed_artifacts

    if len(expected_artifacts) == 1:
        artifact_name = expected_artifacts[0]
        if parsed is not None:
            envelope_like = False
            if isinstance(parsed, dict):
                envelope_like = "artifacts" in parsed or "artifact_name" in parsed
            elif isinstance(parsed, list):
                envelope_like = any(
                    isinstance(entry, dict)
                    and ("artifact_name" in entry or "payload" in entry)
                    for entry in parsed
                )
            if envelope_like:
                return []
            return [{"artifact_name": artifact_name, "payload": parsed}]
        if artifact_name.endswith(".md"):
            return [{"artifact_name": artifact_name, "payload": raw_text}]

    return []


def normalize_response_artifacts(
    deps: LLMRuntimeDeps,
    *,
    response_text: str,
    expected_artifacts: Tuple[str, ...],
    phase: str,
    step_id: str,
    partition_id: str,
    provider: str,
    model_id: str,
    contract_lane: str,
    parse_json_from_response_fn: Callable[[str, Optional[Dict[str, Any]]], Optional[Any]],
    coerce_artifacts_from_response_fn: Callable[[Optional[Any], str, Tuple[str, ...]], List[Dict[str, Any]]],
    finalize_response_parse_provenance: Callable[..., Dict[str, Any]],
    log_response_parse_repair: Callable[[Dict[str, Any]], None],
) -> Tuple[Optional[Any], List[Dict[str, Any]], Dict[str, Any]]:
    provenance: Dict[str, Any] = {}
    parsed = parse_json_from_response_fn(response_text, metadata_out=provenance)
    finalized_provenance = finalize_response_parse_provenance(
        provenance,
        phase=phase,
        step_id=step_id,
        partition_id=partition_id,
        provider=provider,
        model_id=model_id,
        contract_lane=contract_lane,
        accepted=True,
    )
    log_response_parse_repair(finalized_provenance)
    artifacts = coerce_artifacts_from_response_fn(parsed, response_text, expected_artifacts)
    return parsed, artifacts, finalized_provenance


def compute_comparison_resume_decision(
    comparison_artifact_path: Path,
    step_id: str,
    partition_id: str,
    provider: str,
    model: str,
) -> Dict[str, str]:
    del step_id, partition_id, provider, model
    if not comparison_artifact_path.exists():
        return {"action": "RERUN", "reason": "missing_comparison_artifact"}
    try:
        text = comparison_artifact_path.read_text(encoding="utf-8")
        if not text.strip():
            return {"action": "RERUN", "reason": "empty_comparison_artifact"}
        json.loads(text)
    except json.JSONDecodeError:
        return {"action": "RERUN", "reason": "invalid_comparison_artifact"}
    except Exception:
        return {"action": "RERUN", "reason": "unreadable_comparison_artifact"}
    return {"action": "SKIP", "reason": "valid_comparison_artifact"}


def comparison_artifact_dir(phase_dir: Path, provider: str, model: str) -> Path:
    safe_provider = provider.replace("/", "_")
    safe_model = model.replace("/", "_")
    return phase_dir / "raw" / "comparison" / f"{safe_provider}__{safe_model}"


def run_comparison_lane(
    deps: LLMRuntimeDeps,
    phase: str,
    step_id: str,
    partitions: List[Dict[str, Any]],
    phase_dir: Path,
    cfg: Any,
    prompt_text: str,
    output_artifacts: Tuple[str, ...],
    build_partition_context_fn: Callable[..., Tuple[str, Dict[str, Any]]],
    call_llm_fn: Callable[..., Dict[str, Any]],
    parse_json_from_response_fn: Callable[[str, Optional[Dict[str, Any]]], Optional[Any]],
    coerce_artifacts_from_response_fn: Callable[[Optional[Any], str, Tuple[str, ...]], List[Dict[str, Any]]],
    finalize_response_parse_provenance: Callable[..., Dict[str, Any]],
    log_response_parse_repair: Callable[[Dict[str, Any]], None],
    contract_lane: str = "comparison",
) -> List[Dict[str, Any]]:
    compare_provider = str(getattr(cfg, "compare_provider", None) or "xai")
    compare_model = str(getattr(cfg, "compare_model", None) or "grok-4.20-beta")
    comp_dir = comparison_artifact_dir(phase_dir, compare_provider, compare_model)
    comp_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for partition in partitions:
        partition_id = str(partition.get("id", "unknown"))
        artifact_path = comp_dir / f"{step_id}__{partition_id}.json"
        resume_decision = compute_comparison_resume_decision(
            comparison_artifact_path=artifact_path,
            step_id=step_id,
            partition_id=partition_id,
            provider=compare_provider,
            model=compare_model,
        )
        if resume_decision["action"] == "SKIP":
            logger.info(
                "COMPARE_RESUME_SKIP phase=%s step=%s partition=%s provider=%s model=%s",
                phase, step_id, partition_id, compare_provider, compare_model,
            )
            results.append(
                {
                    "partition_id": partition_id,
                    "success": True,
                    "resume_skipped": True,
                    "request_meta": {
                        "lane": "comparison",
                        "authoritative": False,
                        "provider": compare_provider,
                        "model_id": compare_model,
                        "resume_skipped": True,
                    },
                    "artifacts": [],
                    "failure_reason": None,
                }
            )
            continue

        logger.info(
            "COMPARE_EXEC_START phase=%s step=%s partition=%s provider=%s model=%s",
            phase, step_id, partition_id, compare_provider, compare_model,
        )
        logger.info(
            "COMPARE_ROUTE_CHOSEN phase=%s step=%s provider=%s model=%s",
            phase, step_id, compare_provider, compare_model,
        )
        try:
            context_text, _ctx_meta = build_partition_context_fn(
                phase=phase,
                partition_paths=list(partition.get("paths") or []),
                file_truncate_chars=cfg.file_truncate_chars,
                home_scan_mode=cfg.home_scan_mode,
                max_files=deps.max_files_for_phase(phase, cfg),
                max_chars=cfg.max_chars,
                router=cfg.router,
            )
            route_token = f"{compare_provider}/{compare_model}"
            projected_input_tokens = deps.estimate_text_tokens(prompt_text, context_text)
            projected_output_tokens = deps.project_output_tokens(projected_input_tokens)
            deps.check_projected_cost_limit(
                cfg,
                phase=phase,
                step_id=step_id,
                partition_id=partition_id,
                provider=compare_provider,
                model_id=compare_model,
                input_tokens=projected_input_tokens,
                output_tokens=projected_output_tokens,
                execution_mode="comparison",
                route=route_token,
            )
            started = time.time()
            llm_result = call_llm_fn(
                provider=compare_provider,
                model_id=compare_model,
                api_key_env=deps.provider_api_key_env.get(compare_provider, ""),
                system_prompt=prompt_text,
                user_content=context_text,
                cfg=cfg,
                force_json_output=True,
            )
            elapsed_ms = int((time.time() - started) * 1000)
            raw_text = llm_result.get("text", "")
            llm_meta = llm_result.get("meta", {})
            failure_type = llm_meta.get("failure_type")
            if failure_type:
                raise RuntimeError(f"LLM failure_type={failure_type!r}")
            parsed, artifacts, parse_provenance = normalize_response_artifacts(
                deps,
                response_text=raw_text,
                expected_artifacts=output_artifacts,
                phase=phase,
                step_id=step_id,
                partition_id=partition_id,
                provider=compare_provider,
                model_id=compare_model,
                contract_lane=contract_lane,
                parse_json_from_response_fn=parse_json_from_response_fn,
                coerce_artifacts_from_response_fn=coerce_artifacts_from_response_fn,
                finalize_response_parse_provenance=finalize_response_parse_provenance,
                log_response_parse_repair=log_response_parse_repair,
            )
            del parsed
            request_meta = {
                "lane": "comparison",
                "authoritative": False,
                "provider": compare_provider,
                "model_id": compare_model,
                "comparison_of_step": step_id,
                "elapsed_ms": elapsed_ms,
                "final_contract_status": "pass",
                "repair_invocations": 0,
                "repair_successes": 0,
                "response_parse_provenance": parse_provenance,
            }
            if llm_meta.get("response_received") or llm_result.get("ok"):
                spend_record = deps.accumulate_runtime_spend(
                    cfg,
                    phase=phase,
                    step_id=step_id,
                    partition_id=partition_id,
                    provider=compare_provider,
                    model_id=compare_model,
                    execution_mode="comparison",
                    response_summary=(
                        llm_meta.get("response_summary")
                        if isinstance(llm_meta.get("response_summary"), dict)
                        else None
                    ),
                    response_text=raw_text,
                    fallback_input_tokens=projected_input_tokens,
                    fallback_output_tokens=projected_output_tokens,
                    route=route_token,
                    raise_on_limit=False,
                )
                if spend_record is not None:
                    request_meta["spend_usage"] = spend_record
            payload = {
                "phase": phase,
                "step_id": step_id,
                "partition_id": partition_id,
                "artifacts": artifacts,
                "request_meta": request_meta,
            }
            artifact_path.write_text(
                json.dumps(payload, indent=2, sort_keys=True, default=str),
                encoding="utf-8",
            )
            if isinstance(request_meta.get("spend_usage"), dict) and isinstance(
                request_meta["spend_usage"].get("cost_abort_state"), dict
            ):
                raise deps.cost_limit_exceeded_error(
                    (
                        "Runtime cost cap exceeded during comparison lane "
                        f"(phase={phase} step={step_id} partition={partition_id})"
                    ),
                    request_meta["spend_usage"]["cost_abort_state"],
                )
            logger.info(
                "COMPARE_EXEC_DONE phase=%s step=%s partition=%s provider=%s model=%s elapsed_ms=%s",
                phase, step_id, partition_id, compare_provider, compare_model, elapsed_ms,
            )
            logger.info(
                "COMPARE_VALIDATION_RESULT phase=%s step=%s partition=%s status=pass",
                phase, step_id, partition_id,
            )
            results.append(
                {
                    "partition_id": partition_id,
                    "success": True,
                    "resume_skipped": False,
                    "request_meta": request_meta,
                    "artifacts": artifacts,
                    "failure_reason": None,
                }
            )
        except deps.cost_limit_exceeded_error:
            raise
        except Exception as exc:
            failure_reason = str(exc)
            logger.warning(
                "COMPARE_EXEC_DONE phase=%s step=%s partition=%s provider=%s model=%s status=FAILED reason=%s",
                phase, step_id, partition_id, compare_provider, compare_model, failure_reason,
            )
            logger.info(
                "COMPARE_VALIDATION_RESULT phase=%s step=%s partition=%s status=fail reason=%s",
                phase, step_id, partition_id, failure_reason,
            )
            failed_path = comp_dir / f"{step_id}__{partition_id}.FAILED.txt"
            try:
                failed_path.write_text(failure_reason, encoding="utf-8")
            except OSError:
                pass
            results.append(
                {
                    "partition_id": partition_id,
                    "success": False,
                    "resume_skipped": False,
                    "request_meta": {
                        "lane": "comparison",
                        "authoritative": False,
                        "provider": compare_provider,
                        "model_id": compare_model,
                        "final_contract_status": "fail",
                        "failure_type": "comparison_exec_error",
                        "repair_invocations": 0,
                        "repair_successes": 0,
                    },
                    "artifacts": [],
                    "failure_reason": failure_reason,
                }
            )
    return results
