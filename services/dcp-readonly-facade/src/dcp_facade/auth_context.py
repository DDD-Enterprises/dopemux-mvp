"""Provider-neutral connector authentication context (TP-DCP-MCP-RO-0013).

Authentication and target/tool authorization primitives only. No public
listener, tunnel, or backend call is performed here. Raw credential values are
never retained on the trusted context object.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Optional, Protocol

from .connector_policy import ConnectorPolicy, ConnectorPolicyStore
from .redaction import redact_value

# Generic public reason — never distinguish missing/disabled/unknown connector.
GENERIC_AUTH_FAILURE = "authentication failed"
GENERIC_TARGET_DENY = "target not authorized"
GENERIC_TOOL_DENY = "tool not authorized"
GENERIC_EXPIRED = "authentication failed"
GENERIC_DISABLED = "authentication failed"

# Inbound headers that claim connector identity must never be trusted as auth.
UNTRUSTED_CONNECTOR_HEADERS = (
    "x-dcp-connector-id",
    "x-dcp-connector-context",
    "x-dcp-auth-context",
    "x-dcp-connector-seal",
    "x-connector-id",
    "x-authenticated-connector",
)

_BEARER_RE = re.compile(r"(?i)^bearer\s+(\S+)$")
_ENV_REF_RE = re.compile(r"^env:([A-Za-z_][A-Za-z0-9_]*)$")


class SecretResolver(Protocol):
    """Resolve a non-secret credential reference to a raw secret for verification."""

    def resolve(self, kind: str, reference: str) -> Optional[str]:
        ...


class EnvironmentSecretResolver:
    """Resolve ``env:VAR`` references from process environment only."""

    def resolve(self, kind: str, reference: str) -> Optional[str]:
        if kind != "environment":
            return None
        match = _ENV_REF_RE.fullmatch(reference.strip())
        if not match:
            return None
        value = os.environ.get(match.group(1))
        if value is None or value == "":
            return None
        return value


class MappingSecretResolver:
    """Test helper: explicit kind/reference map to secret values."""

    def __init__(self, mapping: Mapping[tuple[str, str], str]):
        self._mapping = dict(mapping)

    def resolve(self, kind: str, reference: str) -> Optional[str]:
        return self._mapping.get((kind, reference))


@dataclass(frozen=True)
class AuthDecision:
    allowed: bool
    reason: str
    connector_id: Optional[str] = None
    code: str = "ok"

    def to_public_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "connector_id": self.connector_id if self.allowed else None,
            "code": self.code if self.allowed else "denied",
        }


@dataclass(frozen=True)
class ConnectorAuthContext:
    """Trusted connector context. Construct only via authenticate_* helpers."""

    connector_id: str
    provider: str
    transport_class: str
    audit_label: str
    credential_fingerprint: str
    rotation_group: str
    allowed_target_ids: tuple[str, ...]
    default_target_id: Optional[str]
    allowed_tools: tuple[str, ...]
    denied_tools: tuple[str, ...]
    rate_limit_rpm: int
    rate_limit_burst: int
    rate_limit_max_concurrent: int
    expires_at: Optional[str]
    seal: str

    def to_public_dict(self) -> dict:
        """Public-safe view: no seal material that could aid forgery replay beyond id."""
        return {
            "connector_id": self.connector_id,
            "provider": self.provider,
            "transport_class": self.transport_class,
            "audit_label": self.audit_label,
            "credential_fingerprint": self.credential_fingerprint,
            "rotation_group": self.rotation_group,
            "allowed_target_ids": list(self.allowed_target_ids),
            "default_target_id": self.default_target_id,
            "allowed_tools": list(self.allowed_tools),
            "denied_tools": list(self.denied_tools),
            "rate_limit": {
                "requests_per_minute": self.rate_limit_rpm,
                "burst": self.rate_limit_burst,
                "max_concurrent": self.rate_limit_max_concurrent,
            },
            "expires_at": self.expires_at,
        }


# Process-local sealing key. Not a credential store; prevents reconstructing a
# trusted context from untrusted headers without going through authenticate.
_SEAL_KEY = os.environ.get("DCP_FACADE_AUTH_SEAL_KEY", "").encode("utf-8") or secrets.token_bytes(32)


def _seal_material(fields: Mapping[str, object]) -> str:
    # Structured JSON avoids delimiter ambiguity across list/string fields.
    payload = json.dumps(fields, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hmac.new(_SEAL_KEY, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return digest


def _context_seal_fields(
    *,
    connector_id: str,
    provider: str,
    transport_class: str,
    audit_label: str,
    credential_fingerprint: str,
    rotation_group: str,
    allowed_target_ids: tuple[str, ...],
    default_target_id: Optional[str],
    allowed_tools: tuple[str, ...],
    denied_tools: tuple[str, ...],
    rate_limit_rpm: int,
    rate_limit_burst: int,
    rate_limit_max_concurrent: int,
    expires_at: Optional[str],
) -> dict[str, object]:
    return {
        "connector_id": connector_id,
        "provider": provider,
        "transport_class": transport_class,
        "audit_label": audit_label,
        "credential_fingerprint": credential_fingerprint,
        "rotation_group": rotation_group,
        "allowed_target_ids": list(allowed_target_ids),
        "default_target_id": default_target_id,
        "allowed_tools": list(allowed_tools),
        "denied_tools": list(denied_tools),
        "rpm": rate_limit_rpm,
        "burst": rate_limit_burst,
        "max_concurrent": rate_limit_max_concurrent,
        "expires_at": expires_at,
    }


def _build_context(policy: ConnectorPolicy) -> ConnectorAuthContext:
    fields = _context_seal_fields(
        connector_id=policy.connector_id,
        provider=policy.provider,
        transport_class=policy.transport_class,
        audit_label=policy.audit_label,
        credential_fingerprint=policy.credential_ref.verification_fingerprint,
        rotation_group=policy.credential_ref.rotation_group,
        allowed_target_ids=policy.allowed_target_ids,
        default_target_id=policy.default_target_id,
        allowed_tools=policy.allowed_tools,
        denied_tools=policy.denied_tools,
        rate_limit_rpm=policy.rate_limit.requests_per_minute,
        rate_limit_burst=policy.rate_limit.burst,
        rate_limit_max_concurrent=policy.rate_limit.max_concurrent,
        expires_at=policy.expires_at,
    )
    return ConnectorAuthContext(
        connector_id=policy.connector_id,
        provider=policy.provider,
        transport_class=policy.transport_class,
        audit_label=policy.audit_label,
        credential_fingerprint=policy.credential_ref.verification_fingerprint,
        rotation_group=policy.credential_ref.rotation_group,
        allowed_target_ids=policy.allowed_target_ids,
        default_target_id=policy.default_target_id,
        allowed_tools=policy.allowed_tools,
        denied_tools=policy.denied_tools,
        rate_limit_rpm=policy.rate_limit.requests_per_minute,
        rate_limit_burst=policy.rate_limit.burst,
        rate_limit_max_concurrent=policy.rate_limit.max_concurrent,
        expires_at=policy.expires_at,
        seal=_seal_material(fields),
    )


def verify_context_seal(context: ConnectorAuthContext) -> bool:
    """Return True only if the context seal matches sealed policy fields."""
    fields = _context_seal_fields(
        connector_id=context.connector_id,
        provider=context.provider,
        transport_class=context.transport_class,
        audit_label=context.audit_label,
        credential_fingerprint=context.credential_fingerprint,
        rotation_group=context.rotation_group,
        allowed_target_ids=context.allowed_target_ids,
        default_target_id=context.default_target_id,
        allowed_tools=context.allowed_tools,
        denied_tools=context.denied_tools,
        rate_limit_rpm=context.rate_limit_rpm,
        rate_limit_burst=context.rate_limit_burst,
        rate_limit_max_concurrent=context.rate_limit_max_concurrent,
        expires_at=context.expires_at,
    )
    expected = _seal_material(fields)
    return hmac.compare_digest(expected, context.seal)


def context_from_untrusted_headers(headers: Mapping[str, str]) -> AuthDecision:
    """Always deny. Connector context headers are never authoritative."""
    return AuthDecision(allowed=False, reason=GENERIC_AUTH_FAILURE, code="untrusted_headers")


def strip_untrusted_connector_headers(
    headers: Mapping[str, str],
) -> tuple[dict[str, str], list[str]]:
    """Remove forgeable connector-identity headers; return clean map + redactions."""
    cleaned: dict[str, str] = {}
    redactions: list[str] = []
    for key, value in headers.items():
        lowered = key.lower()
        if lowered in UNTRUSTED_CONNECTOR_HEADERS:
            redactions.append(f"stripped:{lowered}")
            continue
        clean_value, categories = redact_value(value, [])
        if categories:
            redactions.extend(categories)
            cleaned[key] = str(clean_value)
        else:
            cleaned[key] = value
    # Also redact Authorization values in returned copy when present.
    for key in list(cleaned):
        if key.lower() == "authorization":
            cleaned[key] = "Bearer <redacted>"
            if "secrets" not in redactions:
                redactions.append("secrets")
    return cleaned, sorted(set(redactions))


def extract_bearer_token(authorization_header: Optional[str]) -> Optional[str]:
    if not authorization_header or not isinstance(authorization_header, str):
        return None
    match = _BEARER_RE.match(authorization_header.strip())
    if not match:
        return None
    token = match.group(1).strip()
    return token or None


def authenticate_bearer(
    store: ConnectorPolicyStore,
    *,
    authorization_header: Optional[str] = None,
    presented_token: Optional[str] = None,
    connector_id_hint: Optional[str] = None,
    secret_resolver: Optional[SecretResolver] = None,
    now: Optional[datetime] = None,
) -> tuple[Optional[ConnectorAuthContext], AuthDecision]:
    """Authenticate a connector via bearer token against policy credential refs.

    On any failure returns a generic authentication failure without reflecting
    tokens, missing connector ids, or secret values.
    """
    resolver = secret_resolver or EnvironmentSecretResolver()
    token = presented_token if presented_token is not None else extract_bearer_token(authorization_header)
    if not token:
        return None, AuthDecision(allowed=False, reason=GENERIC_AUTH_FAILURE, code="missing_token")

    candidates: list[ConnectorPolicy]
    if connector_id_hint:
        # Hint is optional and never sufficient alone.
        policy = store.get(connector_id_hint)
        candidates = [policy] if policy is not None else []
    else:
        candidates = list(store.policies.values())

    matched: Optional[ConnectorPolicy] = None
    for policy in candidates:
        secret = resolver.resolve(policy.credential_ref.kind, policy.credential_ref.reference)
        if secret is None:
            continue
        if hmac.compare_digest(secret, token):
            if matched is not None:
                # Ambiguous credential binding — fail closed.
                return None, AuthDecision(allowed=False, reason=GENERIC_AUTH_FAILURE, code="ambiguous")
            matched = policy

    if matched is None:
        return None, AuthDecision(allowed=False, reason=GENERIC_AUTH_FAILURE, code="auth_failure")

    if not matched.enabled:
        return None, AuthDecision(allowed=False, reason=GENERIC_DISABLED, code="disabled")

    if matched.is_expired(now):
        return None, AuthDecision(allowed=False, reason=GENERIC_EXPIRED, code="expired")

    context = _build_context(matched)
    if not verify_context_seal(context):
        return None, AuthDecision(allowed=False, reason=GENERIC_AUTH_FAILURE, code="seal_failure")

    return context, AuthDecision(
        allowed=True,
        reason="authenticated",
        connector_id=matched.connector_id,
        code="ok",
    )


def authorize_target(context: ConnectorAuthContext, target_id: object) -> AuthDecision:
    if not verify_context_seal(context):
        return AuthDecision(allowed=False, reason=GENERIC_AUTH_FAILURE, code="forged_context")
    if not isinstance(target_id, str) or not target_id:
        return AuthDecision(
            allowed=False,
            reason=GENERIC_TARGET_DENY,
            connector_id=context.connector_id,
            code="invalid_target",
        )
    if target_id not in context.allowed_target_ids:
        return AuthDecision(
            allowed=False,
            reason=GENERIC_TARGET_DENY,
            connector_id=context.connector_id,
            code="unauthorized_target",
        )
    return AuthDecision(
        allowed=True,
        reason="target authorized",
        connector_id=context.connector_id,
        code="ok",
    )


def authorize_tool(context: ConnectorAuthContext, tool_name: object) -> AuthDecision:
    if not verify_context_seal(context):
        return AuthDecision(allowed=False, reason=GENERIC_AUTH_FAILURE, code="forged_context")
    if not isinstance(tool_name, str) or not tool_name:
        return AuthDecision(
            allowed=False,
            reason=GENERIC_TOOL_DENY,
            connector_id=context.connector_id,
            code="invalid_tool",
        )
    if tool_name in context.denied_tools:
        return AuthDecision(
            allowed=False,
            reason=GENERIC_TOOL_DENY,
            connector_id=context.connector_id,
            code="denied_tool",
        )
    if tool_name not in context.allowed_tools:
        return AuthDecision(
            allowed=False,
            reason=GENERIC_TOOL_DENY,
            connector_id=context.connector_id,
            code="unauthorized_tool",
        )
    return AuthDecision(
        allowed=True,
        reason="tool authorized",
        connector_id=context.connector_id,
        code="ok",
    )


def resolve_request_target(
    context: ConnectorAuthContext, requested_target_id: Optional[str]
) -> tuple[Optional[str], AuthDecision]:
    """Resolve caller target or connector default under multi-target rules."""
    if not verify_context_seal(context):
        return None, AuthDecision(allowed=False, reason=GENERIC_AUTH_FAILURE, code="forged_context")
    if requested_target_id:
        decision = authorize_target(context, requested_target_id)
        return (requested_target_id if decision.allowed else None), decision
    if context.default_target_id and context.default_target_id in context.allowed_target_ids:
        return context.default_target_id, AuthDecision(
            allowed=True,
            reason="default target applied",
            connector_id=context.connector_id,
            code="ok",
        )
    if len(context.allowed_target_ids) == 1:
        only = context.allowed_target_ids[0]
        return only, AuthDecision(
            allowed=True,
            reason="single allowed target applied",
            connector_id=context.connector_id,
            code="ok",
        )
    return None, AuthDecision(
        allowed=False,
        reason=GENERIC_TARGET_DENY,
        connector_id=context.connector_id,
        code="target_required",
    )


def forge_context_attempt(
    **kwargs: object,
) -> ConnectorAuthContext:
    """Test helper that builds an unsealed/forged context-like object.

    Production callers must not use this. Seal will not verify unless kwargs
    include a correctly computed seal for the process key.
    """
    base = {
        "connector_id": str(kwargs.get("connector_id", "forged-connector")),
        "provider": str(kwargs.get("provider", "chatgpt")),
        "transport_class": str(kwargs.get("transport_class", "local_stdio")),
        "audit_label": str(kwargs.get("audit_label", "forged.label")),
        "credential_fingerprint": str(kwargs.get("credential_fingerprint", "fp:forged")),
        "rotation_group": str(kwargs.get("rotation_group", "forged-group")),
        "allowed_target_ids": tuple(kwargs.get("allowed_target_ids", ("dopemux-main",))),  # type: ignore[arg-type]
        "default_target_id": kwargs.get("default_target_id", "dopemux-main"),
        "allowed_tools": tuple(kwargs.get("allowed_tools", ("list_targets",))),  # type: ignore[arg-type]
        "denied_tools": tuple(kwargs.get("denied_tools", ())),  # type: ignore[arg-type]
        "rate_limit_rpm": int(kwargs.get("rate_limit_rpm", 10)),  # type: ignore[arg-type]
        "rate_limit_burst": int(kwargs.get("rate_limit_burst", 1)),  # type: ignore[arg-type]
        "rate_limit_max_concurrent": int(kwargs.get("rate_limit_max_concurrent", 1)),  # type: ignore[arg-type]
        "expires_at": kwargs.get("expires_at"),
        "seal": str(kwargs.get("seal", "invalid-seal")),
    }
    return ConnectorAuthContext(**base)  # type: ignore[arg-type]


def redact_authorization_header(value: str) -> str:
    clean, _ = redact_value(value, [])
    if isinstance(clean, str) and clean.lower().startswith("bearer "):
        return "Bearer <redacted>"
    return str(clean)
