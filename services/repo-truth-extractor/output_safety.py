from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

_SECRET_QUERY_RE = re.compile(
    r"([?&](?:key|api[_-]?key|token|access[_-]?token|secret)=)[^&\s]+", re.IGNORECASE
)
_SECRET_ASSIGN_RE = re.compile(
    r"(?i)((?:[\"']?([A-Za-z_][A-Za-z0-9_-]*)[\"']?\s*[:=]\s*)[\"']?)([^\"',\s\]\}]+)([\"']?)"
)
_BEARER_INLINE_RE = re.compile(r"(?i)(\bBearer\s+)([^\s,;]+)")
_AUTH_HEADER_RE = re.compile(
    r"(?i)((?:[\"']?\b(?:Authorization|x-goog-api-key)\b[\"']?\s*[:=]\s*)[\"']?)([^\n\r\"']+)([\"']?)"
)
_PRIVATE_KEY_BLOCK_RE = re.compile(
    r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----",
    re.DOTALL,
)
_PROVIDER_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9_-])(?:"
    r"sk-(?:proj-)?[A-Za-z0-9_-]{16,}|"
    r"xai-[A-Za-z0-9_-]{16,}|"
    r"gsk_[A-Za-z0-9_-]{16,}|"
    r"xox[baprs]-[A-Za-z0-9-]{16,}|"
    r"gh[pousr]_[A-Za-z0-9_]{20,}|"
    r"github_pat_[A-Za-z0-9_-]{16,}|"
    r"glpat-[A-Za-z0-9_-]{20,}|"
    r"AIza[0-9A-Za-z_-]{20,}|"
    r"ya29\.[0-9A-Za-z_-]{20,}|"
    r"(?:AKIA|ASIA)[0-9A-Z]{16}|"
    r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"
    r")(?![A-Za-z0-9_-])"
)
_LONG_TOKEN_CANDIDATE_RE = re.compile(
    r"(?<![A-Za-z0-9_])([A-Za-z0-9][A-Za-z0-9_-]{39,})(?![A-Za-z0-9_])"
)


# Single redaction token shared by scrubs and (after R3-010) prompt instructions.
# Prompts previously taught `<REDACTED>` while enforcement emitted `[REDACTED]`;
# both now use this constant's value so models and write-time scrub agree.
REDACTION_TOKEN = "[REDACTED]"
REDACTION_TOKEN_PRIVATE_KEY = "[REDACTED PRIVATE KEY]"

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

# Fragments that mark a JSON/assign key as secret-bearing (R3-010 expanded).
# Security judgment (explicit, not "structurally impossible"):
#   * Include `credential` so DEFAULT_CREDENTIALS / credentials / credential
#     values are masked by field-name path.
#   * Include `passwd` (common alias that lacks the full "password" substring).
#   * Include `access_key` for AWS-style access key material (access_key_id etc.).
#   * Do NOT include bare `cred` / `auth` — too many false positives
#     (credit, accreditation, author, authority).
#   * Env-name / presence / count keys remain excluded via suffix + allowlist.
_SENSITIVE_KEY_FRAGMENTS = (
    "authorization",
    "bearer",
    "secret",
    "password",
    "passwd",
    "credential",
    "private_key",
    "private-key",
    "webhook_secret",
    "access_key",
)

# SHORT-SECRET RESIDUAL (R3-010 — decide and document, do not overclaim):
# `_LONG_TOKEN_CANDIDATE_RE` requires >=40 char alnum/_- blobs with mixed case
# and a digit. Short non-prefixed secrets (e.g. `shortsecret`, 16-char
# passwords without a sensitive key name) intentionally survive BOTH the
# generic and provider/security scrubs when they appear only as free text.
# Lowering the threshold would massively false-positive on commit SHAs,
# UUIDs fragments, and normal identifiers. Mitigation for short secrets is
# the sensitive-key field path (expanded above) plus provider-prefix regexes,
# not a shorter bare-token catch-all. Residual: ACCEPT as known limit; do not
# claim "structurally impossible" for short free-text secrets without a
# sensitive key name or provider prefix.


def _is_sensitive_key(key: Any) -> bool:
    token = str(key or "").strip().lower().replace("-", "_")
    if not token or token in _SAFE_SENSITIVE_KEYS:
        return False
    if token.endswith(
        (
            "_env",
            "_envs",
            "_env_name",
            "_env_requested",
            "_env_resolved",
            "_present",
            "_set",
            "_sha256",
            "_signature",
            "_bytes",
            "_count",
            "_counts",
            "_seconds",
            "_ms",
            "_tokens",
            "_token_limit",
        )
    ):
        return False
    if (
        token.startswith(("missing_", "required_", "configured_", "fallback_"))
        and "api_key" in token
    ):
        return False
    if any(fragment in token for fragment in _SENSITIVE_KEY_FRAGMENTS):
        return True
    if token == "key":
        return True
    if (token == "apikey" or "api_key" in token) and "env" not in token:
        return True
    if "token" in token and "tokens" not in token and "token_limit" not in token:
        return True
    return False


def sanitize_text_for_output(text: str) -> str:
    if not text:
        return ""
    value = str(text)
    value = _PRIVATE_KEY_BLOCK_RE.sub(REDACTION_TOKEN_PRIVATE_KEY, value)
    value = _SECRET_QUERY_RE.sub(r"\1REDACTED", value)
    value = _AUTH_HEADER_RE.sub(rf"\1{REDACTION_TOKEN}\3", value)
    value = _SECRET_ASSIGN_RE.sub(_redact_secret_assignment, value)
    value = _BEARER_INLINE_RE.sub(rf"\1{REDACTION_TOKEN}", value)
    value = _PROVIDER_TOKEN_RE.sub(REDACTION_TOKEN, value)
    return value


def _redact_secret_assignment(match: re.Match[str]) -> str:
    if not _is_sensitive_key(match.group(2)):
        return match.group(0)
    if match.group(3).startswith("[REDACTED"):
        return match.group(0)
    return f"{match.group(1)}{REDACTION_TOKEN}{match.group(4)}"


def sanitize_failed_sidecar_text(text: str) -> str:
    return sanitize_text_for_provider_payload(text)


def _looks_like_hex_digest(value: str) -> bool:
    if len(value) not in {32, 40, 64, 96, 128}:
        return False
    return bool(re.fullmatch(r"[0-9a-fA-F]+", value))


def _redact_long_token_candidate(match: re.Match[str]) -> str:
    token = match.group(1)
    if _looks_like_hex_digest(token):
        return token
    has_upper = any(ch.isupper() for ch in token)
    has_lower = any(ch.islower() for ch in token)
    has_digit = any(ch.isdigit() for ch in token)
    if has_upper and has_lower and has_digit:
        return REDACTION_TOKEN
    return token


def sanitize_text_for_provider_payload(text: str) -> str:
    """Redact secret-shaped values before text is sent to an LLM provider."""
    if not text:
        return ""
    value = str(text)
    value = _PRIVATE_KEY_BLOCK_RE.sub(REDACTION_TOKEN_PRIVATE_KEY, value)
    value = sanitize_text_for_output(value)
    value = _PROVIDER_TOKEN_RE.sub(REDACTION_TOKEN, value)
    value = _LONG_TOKEN_CANDIDATE_RE.sub(_redact_long_token_candidate, value)
    return value


def sanitize_payload_for_output(payload: Any, *, field_name: str | None = None) -> Any:
    if isinstance(payload, Path):
        return sanitize_text_for_output(str(payload))
    if field_name is not None and _is_sensitive_key(field_name):
        if payload is None or isinstance(payload, bool):
            return payload
        if isinstance(payload, (int, float)):
            return payload
        return REDACTION_TOKEN
    if isinstance(payload, str):
        return sanitize_text_for_output(payload)
    if isinstance(payload, Mapping):
        return {
            str(key): sanitize_payload_for_output(value, field_name=str(key))
            for key, value in payload.items()
        }
    if isinstance(payload, Sequence) and not isinstance(
        payload, (str, bytes, bytearray)
    ):
        return [sanitize_payload_for_output(item) for item in payload]
    return payload


def sanitize_payload_for_provider(
    payload: Any, *, field_name: str | None = None
) -> Any:
    if isinstance(payload, Path):
        return sanitize_text_for_provider_payload(str(payload))
    if field_name is not None and _is_sensitive_key(field_name):
        if payload is None or isinstance(payload, bool):
            return payload
        if isinstance(payload, (int, float)):
            return payload
        return REDACTION_TOKEN
    if isinstance(payload, str):
        return sanitize_text_for_provider_payload(payload)
    if isinstance(payload, Mapping):
        return {
            str(key): sanitize_payload_for_provider(value, field_name=str(key))
            for key, value in payload.items()
        }
    if isinstance(payload, Sequence) and not isinstance(
        payload, (str, bytes, bytearray)
    ):
        return [sanitize_payload_for_provider(item) for item in payload]
    return payload


def sanitize_payload_for_failed_sidecar(
    payload: Any, *, field_name: str | None = None
) -> Any:
    if isinstance(payload, Path):
        return sanitize_failed_sidecar_text(str(payload))
    if field_name is not None and _is_sensitive_key(field_name):
        if payload is None or isinstance(payload, bool):
            return payload
        if isinstance(payload, (int, float)):
            return payload
        return REDACTION_TOKEN
    if isinstance(payload, str):
        return sanitize_failed_sidecar_text(payload)
    if isinstance(payload, Mapping):
        return {
            str(key): sanitize_payload_for_failed_sidecar(value, field_name=str(key))
            for key, value in payload.items()
        }
    if isinstance(payload, Sequence) and not isinstance(
        payload, (str, bytes, bytearray)
    ):
        return [sanitize_payload_for_failed_sidecar(item) for item in payload]
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


# ---------------------------------------------------------------------------
# TP-RTE-TRUTH-R3-007: write-time secret scrub for security-risk-location /
# safe-export artifacts (F-23 enforcement half).
#
# R3-004 (commit 6aac1ef79) made secret redaction BINDING at the prompt layer
# for C8 (SECRETS_RISK_LOCATIONS), H1 (HOME_KEYS_SURFACE/HOME_REFERENCES), H7
# (HOME_SQLITE_SCHEMA) and the M3/M4/M5 safe-exports. That is an instruction,
# not an enforcement: a non-compliant or jailbroken model can still emit a raw
# secret value, and nothing re-scanned the merged artifact before it reached
# disk (and, via C8, PROMPT_R11_SECURITY_RISK_SYNTHESIS). The generic
# ``sanitize_payload_for_output`` scrub already runs on every artifact write
# (see run_extraction_v5.write_json), but it intentionally omits the
# high-entropy long-token catch-all (``_LONG_TOKEN_CANDIDATE_RE``) that
# ``sanitize_payload_for_provider`` applies before a payload leaves the
# machine -- so a secret with no recognizable key name or provider-prefix
# shape (e.g. a raw AWS secret *value*, as opposed to its AKIA/ASIA-prefixed
# access-key *id*) slips through the write path unless the stricter scrub is
# used for this named set of security-sensitive artifacts.
# ---------------------------------------------------------------------------

SECURITY_SENSITIVE_ARTIFACT_NAMES: frozenset[str] = frozenset(
    {
        "SECRETS_RISK_LOCATIONS.json",  # C8
        "HOME_KEYS_SURFACE.json",  # H1
        "HOME_REFERENCES.json",  # H1
        "HOME_SQLITE_SCHEMA.json",  # H7
        "M3_CONPORT_EXPORT_SAFE.json",  # M3
        "M4_DOPE_CONTEXT_EXPORT_SAFE.json",  # M4
        "M5_MCP_HEALTH_EXPORT_SAFE.json",  # M5
    }
)

# Normalize `.partX.` / `.part0001.` shards back to the logical artifact name
# so the partX write branch is symmetric with the merged-norm path (R3-010).
_PART_SHARD_RE = re.compile(r"\.part(?:X|\d+)\.", re.IGNORECASE)


def canonical_security_artifact_basename(artifact_name: Any) -> str:
    """Return the basename with any ``.partX.`` / ``.partNNNN.`` shard removed."""
    base = Path(str(artifact_name or "")).name
    return _PART_SHARD_RE.sub(".", base)


def is_security_sensitive_artifact(artifact_name: Any) -> bool:
    """Return True for the C8/H1/H7/M artifact names whose contract requires
    that no secret value ever appear on disk (F-23).

    Part shards (``NAME.part0001.json`` / ``NAME.partX.json``) resolve to the
    same decision as the merged name so the partX write branch cannot skip
    the security scrub (R3-010).
    """
    return canonical_security_artifact_basename(artifact_name) in (
        SECURITY_SENSITIVE_ARTIFACT_NAMES
    )


def sanitize_payload_for_security_artifact(payload: Any) -> Any:
    """Write-time scrub for security-risk-location / safe-export artifacts.

    Reuses ``sanitize_payload_for_provider`` (no third regex copy -- see
    TP-RTE-TRUTH-D-004) because it is strictly stricter than
    ``sanitize_payload_for_output``: it additionally masks high-entropy
    long tokens that don't match a known key name or provider-token shape.
    Only the secret span is masked; the finding's path/line/risk_type/id
    fields are untouched because they are not secret-shaped strings and do
    not match any sensitive field name.
    """
    return sanitize_payload_for_provider(payload)


def scrub_security_sensitive_artifacts_in_partition_payload(payload: Any) -> Any:
    """Scrub security-sensitive artifact payloads inside a raw partition JSON.

    R3-007 only hardened the norm/ merge write. Raw partition JSON
    (``raw/{step}__{partition}.json``) still embeds model output under
    ``artifacts[].payload`` and previously received only the generic
    ``sanitize_payload_for_output`` via ``write_json``. Apply the stricter
    security scrub to each security-sensitive artifact payload so raw/ is
    not a weaker residual path (R3-010).
    """
    if not isinstance(payload, Mapping):
        return payload
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        return payload
    scrubbed_artifacts: list[Any] = []
    changed = False
    for art in artifacts:
        if not isinstance(art, Mapping):
            scrubbed_artifacts.append(art)
            continue
        name = art.get("artifact_name")
        if is_security_sensitive_artifact(name):
            new_art = dict(art)
            new_art["payload"] = sanitize_payload_for_security_artifact(
                art.get("payload")
            )
            scrubbed_artifacts.append(new_art)
            changed = True
        else:
            scrubbed_artifacts.append(art)
    if not changed:
        return payload
    out = dict(payload)
    out["artifacts"] = scrubbed_artifacts
    return out
