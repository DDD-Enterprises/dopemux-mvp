"""Pure, fail-closed independence assessment between two AuditIdentity records.

``independence()`` never approves an audit; it returns an assessment only.
All outputs carry authority ``"NONE"``.
"""

from __future__ import annotations

from dataclasses import dataclass

from dopemux.governed_execution.audit_identity.identity import AuditIdentity

_NON_COMPARABLE = frozenset({"UNKNOWN", "NOT_EXPOSED"})

DIFFERENT_FAMILY_AND_RUNTIME = "DIFFERENT_FAMILY_AND_RUNTIME"
DIFFERENT_FAMILY = "DIFFERENT_FAMILY"
DIFFERENT_RUNTIME = "DIFFERENT_RUNTIME"
SAME_FAMILY_DIFFERENT_SESSION = "SAME_FAMILY_DIFFERENT_SESSION"
UNKNOWN = "UNKNOWN"

SELF_CERTIFICATION_RISK = "SELF_CERTIFICATION_RISK"


@dataclass(frozen=True)
class IndependenceAssessment:
    """The result of comparing an implementer identity against an auditor
    identity. Never an approval, never a merge/readiness signal.
    """

    class_: str
    reasons: tuple[str, ...]
    authority: str = "NONE"


def _comparable(a: str, b: str) -> bool:
    return a not in _NON_COMPARABLE and b not in _NON_COMPARABLE


def independence(implementer: AuditIdentity, auditor: AuditIdentity) -> IndependenceAssessment:
    """Fail-closed: any UNKNOWN/NOT_EXPOSED on a field a determination
    depends on yields class UNKNOWN, never a guessed class.
    """
    provider_comparable = _comparable(implementer.provider, auditor.provider)
    runner_comparable = _comparable(implementer.runner, auditor.runner)

    if not provider_comparable or not runner_comparable:
        reasons = []
        if not provider_comparable:
            reasons.append("provider not comparable: UNKNOWN or NOT_EXPOSED on at least one side")
        if not runner_comparable:
            reasons.append("runner not comparable: UNKNOWN or NOT_EXPOSED on at least one side")
        return IndependenceAssessment(class_=UNKNOWN, reasons=tuple(reasons))

    same_provider = implementer.provider == auditor.provider
    same_runner = implementer.runner == auditor.runner

    if same_provider and same_runner:
        auth_comparable = _comparable(implementer.auth_profile_ref, auditor.auth_profile_ref)
        if auth_comparable and implementer.auth_profile_ref == auditor.auth_profile_ref:
            return IndependenceAssessment(
                class_=UNKNOWN,
                reasons=(
                    f"{SELF_CERTIFICATION_RISK}: identical runner, provider and "
                    "auth_profile_ref (runner_version not considered; FR-001)",
                ),
            )
        if auth_comparable and implementer.auth_profile_ref != auditor.auth_profile_ref:
            return IndependenceAssessment(
                class_=SAME_FAMILY_DIFFERENT_SESSION,
                reasons=("same provider and runner; different auth_profile_ref",),
            )
        version_comparable = _comparable(implementer.runner_version, auditor.runner_version)
        if version_comparable and implementer.runner_version != auditor.runner_version:
            return IndependenceAssessment(
                class_=SAME_FAMILY_DIFFERENT_SESSION,
                reasons=("same provider and runner; different runner_version",),
            )
        return IndependenceAssessment(
            class_=UNKNOWN,
            reasons=(
                "same provider and runner; auth_profile_ref and runner_version "
                "not comparable (UNKNOWN or NOT_EXPOSED) or identical",
            ),
        )

    if not same_provider and not same_runner:
        return IndependenceAssessment(
            class_=DIFFERENT_FAMILY_AND_RUNTIME,
            reasons=("provider differs and runner differs; both provider fields known",),
        )
    if not same_provider:
        return IndependenceAssessment(class_=DIFFERENT_FAMILY, reasons=("provider differs",))
    return IndependenceAssessment(class_=DIFFERENT_RUNTIME, reasons=("runner differs",))
