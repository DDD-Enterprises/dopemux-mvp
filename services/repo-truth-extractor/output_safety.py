from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

_SECRET_QUERY_RE = re.compile(r"([?&](?:key|api[_-]?key|token|access[_-]?token|secret)=)[^&\s]+", re.IGNORECASE)
_SECRET_ASSIGN_RE = re.compile(
    r"(?i)(\b(?:api[_-]?key|authorization|bearer|token|secret|password|private[_-]?key|webhook_secret)\b\s*[:=]\s*)([^,\s\]}]+)"
)
_BEARER_INLINE_RE = re.compile(r"(?i)(\bBearer\s+)([^\s,;]+)")
_AUTH_HEADER_RE = re.compile(r"(?i)(\b(?:Authorization|x-goog-api-key)\b\s*[:=]\s*)([^\n\r]+)")
_PRIVATE_KEY_BLOCK_RE = re.compile(
    r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----",
    re.DOTALL,
)
_PROVIDER_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9_-])(?:"
    r"sk-[A-Za-z0-9_-]{16,}|"
    r"sk-proj-[A-Za-z0-9_-]{16,}|"
    r"xai-[A-Za-z0-9_-]{16,}|"
    r"gsk_[A-Za-z0-9_-]{16,}|"
    r"ghp_[A-Za-z0-9_-]{16,}|"
    r"github_pat_[A-Za-z0-9_-]{16,}|"
    r"glpat-[A-Za-z0-9_-]{16,}"
    r")(?![A-Za-z0-9_-])"
)


_SAFE_SENSITIVE_KEYS = {
    "api_key_env",
    "api_key_env_name",
    "api_key_env_requested",
    "api_key_env_resolved",
    "api_key_present",
    "required_api_key_envs",
    "fallback_api_key_envs",
    "configured_not_required_api_key_envs",
    "missing_api_key_envs",
    "missing_fallback_api_key_envs",
    "all_route_api_key_envs",
    "api_key_env_categories",
    "input_tokens",
    "output_tokens",
    "prompt_tokens",
    "completion_tokens",
    "reasoning_tokens",
    "cached_tokens",
    "input_token_limit",
    "output_token_limit",
    "nextpagetoken",
    "page_token",
}


def _is_sensitive_key(key: Any) -> bool:
    token = str(key or "").strip().lower()
    if not token or token in _SAFE_SENSITIVE_KEYS:
        return False
    if token.endswith(("_env", "_envs", "_env_name", "_env_requested", "_env_resolved", "_present", "_set", "_sha256", "_signature", "_bytes", "_count", "_counts", "_seconds", "_ms", "_tokens", "_token_limit")):
        return False
    if token.startswith(("missing_", "required_", "configured_", "fallback_")) and "api_key" in token:
        return False
    if any(fragment in token for fragment in ("authorization", "bearer", "secret", "password", "private_key", "private-key", "webhook_secret")):
        return True
    if token == "key":
        return True
    if "api_key" in token and "env" not in token:
        return True
    if "token" in token and "tokens" not in token and "token_limit" not in token:
        return True
    return False


def sanitize_text_for_output(text: str) -> str:
    if not text:
        return ""
    value = str(text)
    value = _PRIVATE_KEY_BLOCK_RE.sub("[REDACTED PRIVATE KEY]", value)
    value = _SECRET_QUERY_RE.sub(r"\1REDACTED", value)
    value = _SECRET_ASSIGN_RE.sub(r"\1[REDACTED]", value)
    value = _AUTH_HEADER_RE.sub(r"\1[REDACTED]", value)
    value = _BEARER_INLINE_RE.sub(r"\1[REDACTED]", value)
    value = _PROVIDER_TOKEN_RE.sub("[REDACTED]", value)
    return value


def sanitize_failed_sidecar_text(text: str) -> str:
    return sanitize_text_for_output(text)


def sanitize_payload_for_output(payload: Any, *, field_name: str | None = None) -> Any:
    if isinstance(payload, Path):
        return sanitize_text_for_output(str(payload))
    if field_name is not None and _is_sensitive_key(field_name):
        if payload is None or isinstance(payload, bool):
            return payload
        if isinstance(payload, (int, float)):
            return payload
        return "[REDACTED]"
    if isinstance(payload, str):
        return sanitize_text_for_output(payload)
    if isinstance(payload, Mapping):
        return {
            str(key): sanitize_payload_for_output(value, field_name=str(key))
            for key, value in payload.items()
        }
    if isinstance(payload, Sequence) and not isinstance(payload, (str, bytes, bytearray)):
        return [sanitize_payload_for_output(item) for item in payload]
    return payload


def sanitized_json_text(
    payload: Any,
    *,
    indent: int | None = 2,
    sort_keys: bool = True,
    ensure_ascii: bool = True,
    separators: tuple[str, str] | None = None,
) -> str:
    sanitized = sanitize_payload_for_output(payload)
    return json.dumps(
        sanitized,
        indent=indent,
        sort_keys=sort_keys,
        ensure_ascii=ensure_ascii,
        separators=separators,
        default=str,
    )


def sanitized_json_bytes(
    payload: Any,
    *,
    sort_keys: bool = True,
    ensure_ascii: bool = True,
    separators: tuple[str, str] | None = None,
) -> bytes:
    return sanitized_json_text(
        payload,
        indent=None,
        sort_keys=sort_keys,
        ensure_ascii=ensure_ascii,
        separators=separators,
    ).encode("utf-8")
