"""Strict connector policy schema/loader (TP-DCP-MCP-RO-0013).

Loads non-secret connector policy records from operator-owned documents.
Populated production policy lives outside the repository; repository examples
are templates only. This module never stores raw credential values and never
opens network sockets or listeners.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

import yaml
from jsonschema import Draft202012Validator

from .redaction import redact_value

SCHEMA_VERSION = "1.0.0"
ENV_POLICY_PATH = "DCP_FACADE_CONNECTOR_POLICY"
DEFAULT_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schema" / "connector_policy.schema.json"

_FAIL_CLOSED_KEYS = (
    "unknown_target",
    "disabled_target",
    "unauthorized_target",
    "denied_tool",
    "expired_credential",
    "ambiguous_owner",
    "stale_runtime",
    "auth_failure",
    "missing_rate_policy",
    "provider_drift",
)

# Reject credential references that look like embedded secret material rather
# than non-secret locators (env:/keychain:/manager: style).
_SECRET_LIKE = re.compile(
    r"(?i)(sk-[A-Za-z0-9_\-]{8,}|gh[pousr]_[A-Za-z0-9]{16,}|AKIA[0-9A-Z]{16}|"
    r"bearer\s+[A-Za-z0-9._\-]{8,}|password\s*[=:]\s*\S+)"
)


@dataclass(frozen=True)
class CredentialRef:
    kind: str
    reference: str
    verification_fingerprint: str
    rotation_group: str


@dataclass(frozen=True)
class RateLimitPolicy:
    requests_per_minute: int
    burst: int
    max_concurrent: int
    deny_on_backend_unavailable: bool = True


@dataclass(frozen=True)
class ConnectorPolicy:
    """One independently revocable connector identity and authorization map."""

    schema_version: str
    connector_id: str
    provider: str
    transport_class: str
    credential_ref: CredentialRef
    default_target_id: Optional[str]
    allowed_target_ids: tuple[str, ...]
    multi_target_authorized: bool
    allowed_tools: tuple[str, ...]
    denied_tools: tuple[str, ...]
    enabled: bool
    rate_limit: RateLimitPolicy
    audit_label: str
    created_by: str
    created_at: str
    expires_at: Optional[str]
    last_verified_at: Optional[str]
    source_documentation_date: str
    provider_account_class: str
    fail_closed: Mapping[str, str]
    provider_metadata: Mapping[str, Any] = field(default_factory=dict)

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        if self.expires_at is None:
            return False
        current = now or datetime.now(timezone.utc)
        expiry = _parse_datetime(self.expires_at)
        if expiry is None:
            return True
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return current >= expiry


@dataclass
class ConnectorPolicyStore:
    """In-memory index of validated connector policies."""

    policies: dict[str, ConnectorPolicy] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    source_label: str = "inline"

    def get(self, connector_id: str) -> Optional[ConnectorPolicy]:
        return self.policies.get(connector_id)

    def by_fingerprint(self, fingerprint: str) -> list[ConnectorPolicy]:
        return [
            policy
            for policy in self.policies.values()
            if policy.credential_ref.verification_fingerprint == fingerprint
        ]

    def enabled_policies(self) -> list[ConnectorPolicy]:
        return [policy for policy in self.policies.values() if policy.enabled]


def load_schema(path: Optional[Path] = None) -> dict[str, Any]:
    schema_path = path or DEFAULT_SCHEMA_PATH
    return json.loads(schema_path.read_text(encoding="utf-8"))


def schema_validator(schema: Optional[dict[str, Any]] = None) -> Draft202012Validator:
    document = schema if schema is not None else load_schema()
    Draft202012Validator.check_schema(document)
    return Draft202012Validator(document)


def parse_connector_policy_document(
    raw: Any,
    *,
    schema: Optional[dict[str, Any]] = None,
    source_label: str = "inline",
) -> ConnectorPolicyStore:
    """Parse a connector policy document or single record fail-closed."""
    store = ConnectorPolicyStore(source_label=source_label)
    validator = schema_validator(schema)
    records = _extract_records(raw, store)
    for index, record in enumerate(records):
        policy, error = _parse_record(record, validator)
        if error is not None:
            store.warnings.append(f"record[{index}]: {error}")
            continue
        assert policy is not None
        if policy.connector_id in store.policies:
            store.warnings.append(
                f"record[{index}]: duplicate connector_id dropped ({policy.connector_id})"
            )
            # Ambiguous identity: drop both.
            store.policies.pop(policy.connector_id, None)
            continue
        store.policies[policy.connector_id] = policy
    return store


def load_connector_policy_path(
    path: Path,
    *,
    schema: Optional[dict[str, Any]] = None,
) -> ConnectorPolicyStore:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        store = ConnectorPolicyStore(source_label=str(path))
        store.warnings.append(f"policy file unreadable: {exc.__class__.__name__}")
        return store
    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError:
        store = ConnectorPolicyStore(source_label=str(path))
        store.warnings.append("policy file YAML parse error")
        return store
    return parse_connector_policy_document(raw, schema=schema, source_label=str(path.name))


def resolve_policy_path(explicit: Optional[str] = None) -> Path:
    import os

    raw = explicit or os.getenv(ENV_POLICY_PATH)
    if not raw:
        raise ValueError("connector policy path not configured")
    return Path(raw).expanduser()


def public_policy_receipt(policy: ConnectorPolicy) -> dict[str, Any]:
    """Serialize non-secret policy fields for tests/audit (no raw credentials)."""
    return {
        "connector_id": policy.connector_id,
        "provider": policy.provider,
        "transport_class": policy.transport_class,
        "enabled": policy.enabled,
        "default_target_id": policy.default_target_id,
        "allowed_target_ids": list(policy.allowed_target_ids),
        "allowed_tools": list(policy.allowed_tools),
        "denied_tools": list(policy.denied_tools),
        "credential_fingerprint": policy.credential_ref.verification_fingerprint,
        "rotation_group": policy.credential_ref.rotation_group,
        "credential_kind": policy.credential_ref.kind,
        "credential_reference": policy.credential_ref.reference,
        "audit_label": policy.audit_label,
        "expires_at": policy.expires_at,
        "rate_limit": {
            "requests_per_minute": policy.rate_limit.requests_per_minute,
            "burst": policy.rate_limit.burst,
            "max_concurrent": policy.rate_limit.max_concurrent,
            "deny_on_backend_unavailable": policy.rate_limit.deny_on_backend_unavailable,
        },
    }


def _extract_records(raw: Any, store: ConnectorPolicyStore) -> list[dict[str, Any]]:
    if isinstance(raw, dict) and isinstance(raw.get("records"), list):
        if raw.get("examples_only") is True:
            store.warnings.append("document marked examples_only; records are templates")
        out: list[dict[str, Any]] = []
        for item in raw["records"]:
            if isinstance(item, dict):
                out.append(item)
            else:
                store.warnings.append("non-object record dropped")
        return out
    if isinstance(raw, dict):
        return [raw]
    if isinstance(raw, list):
        out = []
        for item in raw:
            if isinstance(item, dict):
                out.append(item)
            else:
                store.warnings.append("non-object record dropped")
        return out
    store.warnings.append("policy document must be object or list")
    return []


def _parse_record(
    record: dict[str, Any], validator: Draft202012Validator
) -> tuple[Optional[ConnectorPolicy], Optional[str]]:
    errors = sorted(validator.iter_errors(record), key=lambda err: list(err.path))
    if errors:
        return None, f"schema: {errors[0].message}"

    cred_raw = record["credential_ref"]
    reference = cred_raw["reference"]
    kind = cred_raw["kind"]
    if kind == "environment" and not reference.startswith("env:"):
        return None, "environment credential_ref.reference must use env:VAR form"
    if not _is_locator_reference(kind, reference):
        return None, "credential_ref.reference must be a non-secret locator"
    if _looks_like_secret(reference):
        return None, "credential_ref.reference appears to contain secret material"

    # Defense in depth: run redaction categories over reference/fingerprint.
    _, categories = redact_value(reference, [])
    if categories:
        return None, "credential_ref.reference failed redaction hygiene"

    default_target = record.get("default_target_id")
    allowed_targets = tuple(record["allowed_target_ids"])
    if default_target is not None and default_target not in allowed_targets:
        return None, "default_target_id must appear in allowed_target_ids"

    multi = bool(record.get("multi_target_authorized", False))
    if not multi and len(allowed_targets) > 1:
        return None, "multi_target_authorized is false but multiple targets listed"

    rate_raw = record["rate_limit"]
    if rate_raw.get("deny_on_backend_unavailable") is not True:
        return None, "rate_limit.deny_on_backend_unavailable must be true"
    for key in ("requests_per_minute", "burst", "max_concurrent"):
        if key not in rate_raw:
            return None, "missing_rate_policy"

    fail_closed = record["fail_closed"]
    for key in _FAIL_CLOSED_KEYS:
        if fail_closed.get(key) != "BLOCK":
            return None, f"fail_closed.{key} must be BLOCK"

    if record.get("schema_version") != SCHEMA_VERSION:
        return None, "unsupported schema_version"

    if record.get("expires_at") is not None and _parse_datetime(record["expires_at"]) is None:
        return None, "expires_at is not a valid date-time"

    policy = ConnectorPolicy(
        schema_version=record["schema_version"],
        connector_id=record["connector_id"],
        provider=record["provider"],
        transport_class=record["transport_class"],
        credential_ref=CredentialRef(
            kind=cred_raw["kind"],
            reference=reference,
            verification_fingerprint=cred_raw["verification_fingerprint"],
            rotation_group=cred_raw["rotation_group"],
        ),
        default_target_id=default_target,
        allowed_target_ids=allowed_targets,
        multi_target_authorized=multi,
        allowed_tools=tuple(record["allowed_tools"]),
        denied_tools=tuple(record.get("denied_tools") or ()),
        enabled=bool(record["enabled"]),
        rate_limit=RateLimitPolicy(
            requests_per_minute=int(rate_raw["requests_per_minute"]),
            burst=int(rate_raw["burst"]),
            max_concurrent=int(rate_raw["max_concurrent"]),
            deny_on_backend_unavailable=True,
        ),
        audit_label=record["audit_label"],
        created_by=record["created_by"],
        created_at=record["created_at"],
        expires_at=record.get("expires_at"),
        last_verified_at=record.get("last_verified_at"),
        source_documentation_date=record["source_documentation_date"],
        provider_account_class=record["provider_account_class"],
        fail_closed=dict(fail_closed),
        provider_metadata=dict(record.get("provider_metadata") or {}),
    )
    return policy, None


def _is_locator_reference(kind: str, value: str) -> bool:
    """Require non-secret locator forms; reject bare password-like strings."""
    if value.startswith("<") and value.endswith(">"):
        return True  # repository template placeholder only
    if kind == "environment":
        return bool(re.fullmatch(r"env:[A-Za-z_][A-Za-z0-9_]*", value))
    if kind == "os_keychain":
        return value.startswith(("keychain:", "os_keychain:", "<"))
    if kind == "secret_manager":
        return value.startswith(("secret:", "sm:", "secret_manager:", "<"))
    if kind == "oauth_client":
        return value.startswith(("oauth:", "oauth_client:", "<"))
    if kind == "mtls_identity":
        return value.startswith(("mtls:", "mtls_identity:", "<"))
    return False


def _looks_like_secret(value: str) -> bool:
    if _SECRET_LIKE.search(value):
        return True
    # High-entropy blobs without a locator prefix are treated as secret-like.
    if re.fullmatch(r"[A-Za-z0-9+/=_\-]{16,}", value):
        if value.startswith(("env:", "keychain:", "secret:", "sm:", "oauth:", "mtls:")):
            return False
        if value.startswith("<") and value.endswith(">"):
            return False
        return True
    return False


def _parse_datetime(value: str) -> Optional[datetime]:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def iter_enabled_tool_names(policy: ConnectorPolicy) -> Iterable[str]:
    denied = set(policy.denied_tools)
    for tool in policy.allowed_tools:
        if tool not in denied:
            yield tool
