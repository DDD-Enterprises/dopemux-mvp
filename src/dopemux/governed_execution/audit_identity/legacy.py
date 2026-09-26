"""Project legacy ``embedded_audit`` proof records into AuditIdentity.

The legacy record (``schemas/proof/embedded_audit.schema.json``) is never
modified by this module -- it is read-only input. Every field the legacy
record lacks becomes the sentinel ``UNKNOWN``, never inferred from another
field. ``provider`` is derived ONLY from the closed table below, never from
model-name branding.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Optional

from dopemux.governed_execution.audit_identity.identity import AuditIdentity

UNKNOWN = "UNKNOWN"

# Closed table: auditor_tool (schemas/proof/embedded_audit.schema.json
# enum) -> provider. Never widened by inference from auditor_model text.
PROVIDER_TABLE: Mapping[str, str] = MappingProxyType(
    {
        "agy": "google",
        "antigravity": "google",
        "gemini-cli": "google",
        "claude-code-cli": "anthropic",
        "copilot-cli": "github",
        "grok-cli": "xai",
        "opencode-cli": UNKNOWN,
        "pal-mcp-clink": UNKNOWN,
        "none": "NONE",
    }
)


@dataclass(frozen=True)
class LegacyProjection:
    """Wraps the projected AuditIdentity plus the verbatim legacy invocation
    string, which has no home on AuditIdentity itself.
    """

    identity: AuditIdentity
    legacy_invocation: Optional[str]
    authority: str = "NONE"


def _legacy_model_token(record: Mapping[str, Any]) -> str:
    value = record.get("auditor_model")
    if not isinstance(value, str) or not value or value == "unknown":
        return UNKNOWN
    return value


def project_legacy_embedded_audit(record: Mapping[str, Any]) -> LegacyProjection:
    """Project one legacy embedded_audit record into an AuditIdentity.

    - ``auditor_tool`` -> ``runner``
    - ``auditor_model`` -> ``requested_model`` AND ``configured_model``
      (the legacy schema has a single model field)
    - ``provider`` from the closed table only; a legacy ``auditor_tool``
      that is absent, empty or outside the table yields ``UNKNOWN``
    - every field the legacy record has no equivalent for becomes
      ``UNKNOWN``
    - ``invocation`` is preserved verbatim as ``legacy_invocation`` on the
      wrapper, not placed on AuditIdentity
    """
    tool_value = record.get("auditor_tool")
    runner = tool_value if isinstance(tool_value, str) and tool_value else UNKNOWN
    model_token = _legacy_model_token(record)
    provider = PROVIDER_TABLE.get(runner, UNKNOWN) if isinstance(runner, str) else UNKNOWN

    invocation = record.get("invocation")
    legacy_invocation = invocation if isinstance(invocation, str) else None

    identity = AuditIdentity(
        runner=runner,
        runner_version=UNKNOWN,
        requested_model=model_token,
        configured_model=model_token,
        response_claimed_model=UNKNOWN,
        provider_attested_model=UNKNOWN,
        provider=provider,
        effort_requested=UNKNOWN,
        effort_observed=UNKNOWN,
        auth_profile_ref=UNKNOWN,
        containment=UNKNOWN,
        network_posture=UNKNOWN,
        independence_class=UNKNOWN,
        qualification_receipt=UNKNOWN,
    )
    return LegacyProjection(identity=identity, legacy_invocation=legacy_invocation)
