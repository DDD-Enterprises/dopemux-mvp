"""The W02 derived DispatchQualification join.

qualify() is a PURE function over the seven already-validated receipt dicts
plus caller-supplied provenance: no file reads, no subprocess, no digest
computation, no schema validation, no clock reads. Same input, same output,
always.

The result carries authority == "NONE" and is_execution_authority == False
unconditionally: this join never mints upstream authority. It can only
observe what the seven receipts already say and fold that into one of
DISPATCHABLE, BLOCKED, or NEEDS_SUPERVISOR.

Fixed rule precedence (a receipt or field may only ever push the result
toward BLOCKED; nothing here can widen a denial or invent a pass):
  1. any mandatory receipt absent or structurally malformed -> BLOCKED
  2. ExecutionBinding.authority != "NONE" -> BLOCKED
  3. PolicyEligibility.dcp_status == BLOCKED -> BLOCKED
  4. WorkflowLegality.transition_legal is False -> BLOCKED
  5. OperatorGate.required is True and granted is not True -> BLOCKED
  6. CanonicalWriter.custody_state in (AMBIGUOUS, RELEASED) -> BLOCKED
  7. DriftOverlap.drift_class == CONFLICTING -> BLOCKED
  8. ScopeAuthority.scope_status == BLOCKED -> BLOCKED
  9. any UNKNOWN/NOT_RUN/SUPERSET among the above fields, or
     ExecutionBinding.selection.runner_availability != PROVEN -> NEEDS_SUPERVISOR
  10. otherwise -> DISPATCHABLE

The result is computed as a fold over an ordering
BLOCKED > NEEDS_SUPERVISOR > DISPATCHABLE: every reason contributes its rank,
and the result is the maximum rank observed. Because the fold only ever
takes a maximum, no later reason can lift (downgrade the severity of) a
result a prior reason already set -- the join cannot mint authority or
soften a denial.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .receipts import (
    EXTRACTORS,
    RECEIPT_FIELD,
    RECEIPT_NAMES,
    Finding,
    JoinInput,
    Provenance,
)

DispatchResult = Literal["DISPATCHABLE", "BLOCKED", "NEEDS_SUPERVISOR"]
ReasonEffect = Literal["BLOCKED", "NEEDS_SUPERVISOR"]

# The three legal output values, in the same order as
# schemas/governed_execution/enums.v1.schema.json definitions/dispatch_qualification.
DISPATCH_QUALIFICATION_VALUES: tuple[str, ...] = (
    "DISPATCHABLE",
    "BLOCKED",
    "NEEDS_SUPERVISOR",
)

_RANK: dict[str, int] = {"DISPATCHABLE": 0, "NEEDS_SUPERVISOR": 1, "BLOCKED": 2}

# Fixed precedence rule numbers for each DENY-triggering (receipt, field)
# pair (rules 2-8). Rule 1 (receipt absent or malformed) is keyed on the
# RECEIPT_FIELD sentinel instead, since it is a whole-receipt condition.
# Every UNKNOWN-effect finding is rule 9 regardless of which field it is.
_DENY_RULE: dict[tuple[str, str], int] = {
    ("ExecutionBinding", "authority"): 2,
    ("PolicyEligibility", "dcp_status"): 3,
    ("WorkflowLegality", "transition_legal"): 4,
    ("OperatorGate", "gate"): 5,
    ("CanonicalWriter", "custody_state"): 6,
    ("DriftOverlap", "drift_class"): 7,
    ("ScopeAuthority", "scope_status"): 8,
}

_ABSENT_OR_MALFORMED_RULE = 1
_UNKNOWN_RULE = 9


@dataclass(frozen=True)
class Reason:
    """One reason contributing to a non-DISPATCHABLE result, with its rule."""

    rule: int
    receipt: str
    field: str
    observed: str
    effect: ReasonEffect


@dataclass(frozen=True)
class DispatchQualification:
    """The derived, non-authoritative outcome of the W02 join.

    authority is always the literal "NONE" and is_execution_authority is
    always False: this object records what the seven receipts jointly
    imply, it does not grant anything.
    """

    result: DispatchResult
    reasons: tuple[Reason, ...]
    provenance: Provenance
    authority: Literal["NONE"] = "NONE"
    is_execution_authority: Literal[False] = False


def _rule_for(finding: Finding) -> int:
    if finding.field == RECEIPT_FIELD:
        return _ABSENT_OR_MALFORMED_RULE
    if finding.effect == "DENY":
        return _DENY_RULE[(finding.receipt, finding.field)]
    return _UNKNOWN_RULE


def _reason_for(finding: Finding) -> Reason:
    effect: ReasonEffect = "BLOCKED" if finding.effect == "DENY" else "NEEDS_SUPERVISOR"
    return Reason(
        rule=_rule_for(finding),
        receipt=finding.receipt,
        field=finding.field,
        observed=finding.observed,
        effect=effect,
    )


def qualify(inp: JoinInput) -> DispatchQualification:
    """Derive a DispatchQualification from seven receipt dicts and provenance.

    Pure: no I/O, no digesting, no schema validation, no clock. Calling this
    twice with equal input always yields equal output.
    """
    findings: list[Finding] = []
    for name in RECEIPT_NAMES:
        payload = inp.receipts.get(name)
        extractor = EXTRACTORS[name]
        findings.extend(extractor(payload))

    reasons = sorted(
        (_reason_for(finding) for finding in findings if finding.effect != "OK"),
        key=lambda reason: (reason.rule, reason.receipt),
    )
    reasons_t = tuple(reasons)

    # Fold from DISPATCHABLE upward through the ranks; the maximum rank
    # observed wins. This is the "no rule may upgrade" guarantee by
    # construction: a maximum can never decrease as more terms are folded
    # in, so once BLOCKED is reached no later reason can lift it back down.
    result: DispatchResult = "DISPATCHABLE"
    for reason in reasons_t:
        if _RANK[reason.effect] > _RANK[result]:
            result = reason.effect

    return DispatchQualification(result=result, reasons=reasons_t, provenance=inp.provenance)
