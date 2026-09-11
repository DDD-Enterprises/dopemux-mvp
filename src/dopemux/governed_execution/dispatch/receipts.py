"""Receipt input model and per-receipt extractors for the W02 dispatch join.

This module is a PURE data-shaping layer. It never opens a file, never
shells out, never computes a digest, never validates a receipt against a
schema (that is W04's boundary) and never reads the clock. It only reads
plain dicts (or None) that the caller already obtained and, where relevant,
already schema-validated.

Extractors never raise on malformed input. A missing, None, or
structurally-wrong-typed receipt payload -- or a malformed field within an
otherwise well-formed payload -- always yields a Finding rather than an
exception. This is what lets W02 fail closed instead of crashing.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Literal

ReceiptName = Literal[
    "ScopeAuthority",
    "WorkflowLegality",
    "PolicyEligibility",
    "CanonicalWriter",
    "ExecutionBinding",
    "OperatorGate",
    "DriftOverlap",
]

RECEIPT_NAMES: tuple[ReceiptName, ...] = (
    "ScopeAuthority",
    "WorkflowLegality",
    "PolicyEligibility",
    "CanonicalWriter",
    "ExecutionBinding",
    "OperatorGate",
    "DriftOverlap",
)

Effect = Literal["DENY", "UNKNOWN", "OK"]

# Sentinel field name used when the whole receipt payload is absent or is not
# a mapping (e.g. a string was supplied where a dict was expected). This is
# distinct from a malformed value *inside* an otherwise well-formed payload.
RECEIPT_FIELD = "__receipt__"


@dataclass(frozen=True)
class ReceiptInput:
    """One named receipt slot as supplied by the caller: name plus payload."""

    name: ReceiptName
    payload: Mapping[str, Any] | None


@dataclass(frozen=True)
class Provenance:
    """Caller-supplied provenance for the whole join call. Not validated here."""

    verified_by: str
    verified_at: str
    schema_set_digest: str


@dataclass(frozen=True)
class JoinInput:
    """The full input to qualify(): the seven receipt slots plus provenance."""

    receipts: Mapping[ReceiptName, Mapping[str, Any] | None]
    provenance: Provenance


@dataclass(frozen=True)
class Finding:
    """One extractor observation: what was read, from where, and its effect."""

    receipt: str
    field: str
    observed: str
    effect: Effect


def _guard_payload(receipt: ReceiptName, payload: Mapping[str, Any] | None) -> Finding | None:
    """Return a Finding if the whole receipt payload is unusable, else None."""
    if payload is None:
        return Finding(receipt=receipt, field=RECEIPT_FIELD, observed="absent", effect="DENY")
    if not isinstance(payload, Mapping):
        observed = f"malformed:{type(payload).__name__}"
        return Finding(receipt=receipt, field=RECEIPT_FIELD, observed=observed, effect="DENY")
    return None


def extract_scope_authority(payload: Mapping[str, Any] | None) -> tuple[Finding, ...]:
    guard = _guard_payload("ScopeAuthority", payload)
    if guard is not None:
        return (guard,)
    assert payload is not None
    status = payload.get("scope_status")
    if status == "BLOCKED":
        effect: Effect = "DENY"
    elif status == "PASS":
        effect = "OK"
    else:
        # "UNKNOWN" or any missing/malformed value: fail toward supervision.
        effect = "UNKNOWN"
    observed = status if isinstance(status, str) else repr(status)
    return (Finding(receipt="ScopeAuthority", field="scope_status", observed=observed, effect=effect),)


def extract_workflow_legality(payload: Mapping[str, Any] | None) -> tuple[Finding, ...]:
    guard = _guard_payload("WorkflowLegality", payload)
    if guard is not None:
        return (guard,)
    assert payload is not None
    transition_legal = payload.get("transition_legal")
    if transition_legal is False:
        effect: Effect = "DENY"
    elif transition_legal is True:
        effect = "OK"
    else:
        # None, missing, or a non-bool value: genuine uncertainty.
        effect = "UNKNOWN"
    observed = repr(transition_legal)
    return (
        Finding(receipt="WorkflowLegality", field="transition_legal", observed=observed, effect=effect),
    )


def extract_policy_eligibility(payload: Mapping[str, Any] | None) -> tuple[Finding, ...]:
    guard = _guard_payload("PolicyEligibility", payload)
    if guard is not None:
        return (guard,)
    assert payload is not None
    dcp_status = payload.get("dcp_status")
    if dcp_status == "BLOCKED":
        effect: Effect = "DENY"
    elif dcp_status == "PASS":
        effect = "OK"
    else:
        # UNKNOWN, NOT_RUN, missing, or malformed: cannot widen a denial or
        # invent a pass -- fail toward supervision.
        effect = "UNKNOWN"
    observed = dcp_status if isinstance(dcp_status, str) else repr(dcp_status)
    return (Finding(receipt="PolicyEligibility", field="dcp_status", observed=observed, effect=effect),)


def extract_canonical_writer(payload: Mapping[str, Any] | None) -> tuple[Finding, ...]:
    guard = _guard_payload("CanonicalWriter", payload)
    if guard is not None:
        return (guard,)
    assert payload is not None
    custody_state = payload.get("custody_state")
    if custody_state in ("RELEASED", "AMBIGUOUS"):
        effect: Effect = "DENY"
    elif custody_state == "HELD":
        effect = "OK"
    else:
        # Missing or malformed custody_state: custody cannot be confirmed
        # held, which is itself an ambiguous-custody condition. Fail closed
        # the same as an explicit AMBIGUOUS rather than escalate softly.
        effect = "DENY"
    observed = custody_state if isinstance(custody_state, str) else repr(custody_state)
    return (Finding(receipt="CanonicalWriter", field="custody_state", observed=observed, effect=effect),)


def extract_execution_binding(payload: Mapping[str, Any] | None) -> tuple[Finding, ...]:
    guard = _guard_payload("ExecutionBinding", payload)
    if guard is not None:
        return (guard,)
    assert payload is not None
    authority = payload.get("authority")
    if authority == "NONE":
        authority_effect: Effect = "OK"
    else:
        # Any value other than the literal string "NONE" -- missing, wrong
        # type, or a claimed grant -- is a malformed/authority-claiming
        # binding. ExecutionBinding is factual input, never authorization.
        authority_effect = "DENY"
    authority_observed = authority if isinstance(authority, str) else repr(authority)
    authority_finding = Finding(
        receipt="ExecutionBinding", field="authority", observed=authority_observed, effect=authority_effect
    )

    selection = payload.get("selection")
    runner_availability = selection.get("runner_availability") if isinstance(selection, Mapping) else None
    if runner_availability == "PROVEN":
        runner_effect: Effect = "OK"
    else:
        # PROPOSED, UNKNOWN, missing, or malformed selection: not proven.
        runner_effect = "UNKNOWN"
    runner_observed = runner_availability if isinstance(runner_availability, str) else repr(runner_availability)
    runner_finding = Finding(
        receipt="ExecutionBinding",
        field="runner_availability",
        observed=runner_observed,
        effect=runner_effect,
    )
    return (authority_finding, runner_finding)


def extract_operator_gate(payload: Mapping[str, Any] | None) -> tuple[Finding, ...]:
    guard = _guard_payload("OperatorGate", payload)
    if guard is not None:
        return (guard,)
    assert payload is not None
    required = payload.get("required")
    granted = payload.get("granted")
    if required is True:
        if granted is True:
            effect: Effect = "OK"
        else:
            # required and not affirmatively granted: cannot self-authorize,
            # even when a receipt_ref is present.
            effect = "DENY"
        observed = f"required=True granted={granted!r}"
    elif required is False:
        effect = "OK"
        observed = f"required=False granted={granted!r}"
    else:
        # required is missing or not a bool: genuinely unknown whether the
        # operator gate applies at all.
        effect = "UNKNOWN"
        observed = f"required={required!r} granted={granted!r}"
    return (Finding(receipt="OperatorGate", field="gate", observed=observed, effect=effect),)


def extract_drift_overlap(payload: Mapping[str, Any] | None) -> tuple[Finding, ...]:
    guard = _guard_payload("DriftOverlap", payload)
    if guard is not None:
        return (guard,)
    assert payload is not None
    drift_class = payload.get("drift_class")
    if drift_class == "CONFLICTING":
        effect: Effect = "DENY"
    elif drift_class in ("IDENTICAL", "SUBSET", "COMPATIBLE"):
        effect = "OK"
    else:
        # SUPERSET, UNKNOWN, missing, or malformed: not confirmed compatible.
        effect = "UNKNOWN"
    observed = drift_class if isinstance(drift_class, str) else repr(drift_class)
    return (Finding(receipt="DriftOverlap", field="drift_class", observed=observed, effect=effect),)


ExtractorFn = Callable[[Any], tuple[Finding, ...]]

EXTRACTORS: Mapping[ReceiptName, ExtractorFn] = {
    "ScopeAuthority": extract_scope_authority,
    "WorkflowLegality": extract_workflow_legality,
    "PolicyEligibility": extract_policy_eligibility,
    "CanonicalWriter": extract_canonical_writer,
    "ExecutionBinding": extract_execution_binding,
    "OperatorGate": extract_operator_gate,
    "DriftOverlap": extract_drift_overlap,
}
