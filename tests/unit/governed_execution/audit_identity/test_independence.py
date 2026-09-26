"""Tests for independence(): pure, fail-closed IndependenceAssessment."""
from __future__ import annotations

import pytest

from dopemux.governed_execution.audit_identity.identity import AuditIdentity
from dopemux.governed_execution.audit_identity.independence import (
    DIFFERENT_FAMILY,
    DIFFERENT_FAMILY_AND_RUNTIME,
    DIFFERENT_RUNTIME,
    SAME_FAMILY_DIFFERENT_SESSION,
    SELF_CERTIFICATION_RISK,
    UNKNOWN,
    IndependenceAssessment,
    independence,
)


def _identity(**overrides: str) -> AuditIdentity:
    base = dict(
        runner="claude-code-cli",
        runner_version="2.1",
        requested_model="sonnet",
        configured_model="sonnet",
        response_claimed_model="claude-sonnet-5",
        provider_attested_model="claude-sonnet-5-20260101",
        provider="anthropic",
        effort_requested="high",
        effort_observed="high",
        auth_profile_ref="profile-a",
        containment="sandboxed",
        network_posture="offline",
        independence_class="UNKNOWN",
        qualification_receipt="NOT_RUN",
    )
    base.update(overrides)
    return AuditIdentity(**base)


def test_returns_assessment_never_approval() -> None:
    result = independence(_identity(), _identity(provider="google", runner="agy"))
    assert isinstance(result, IndependenceAssessment)
    assert result.authority == "NONE"
    assert not hasattr(result, "approved")


def test_different_family_and_runtime_positive() -> None:
    implementer = _identity(runner="claude-code-cli", provider="anthropic")
    auditor = _identity(runner="agy", provider="google")
    result = independence(implementer, auditor)
    assert result.class_ == DIFFERENT_FAMILY_AND_RUNTIME


def test_macro_packet_concrete_pair_is_different_family_and_runtime() -> None:
    """The concrete pair from this MacroPacket: implementer Claude Code Agent
    / anthropic / sonnet; auditor agy / google / gemini-3.1-pro-high.
    """
    implementer = _identity(
        runner="claude-code-cli",
        provider="anthropic",
        requested_model="sonnet",
        configured_model="sonnet",
    )
    auditor = _identity(
        runner="agy",
        provider="google",
        requested_model="gemini-3.1-pro-high",
        configured_model="gemini-3.1-pro-high",
        auth_profile_ref="profile-agy",
    )
    result = independence(implementer, auditor)
    assert result.class_ == DIFFERENT_FAMILY_AND_RUNTIME


def test_different_family_and_runtime_negative_same_runner() -> None:
    implementer = _identity(runner="claude-code-cli", provider="anthropic")
    auditor = _identity(runner="claude-code-cli", provider="google")
    result = independence(implementer, auditor)
    assert result.class_ != DIFFERENT_FAMILY_AND_RUNTIME


def test_different_family_positive() -> None:
    implementer = _identity(runner="claude-code-cli", provider="anthropic")
    auditor = _identity(runner="claude-code-cli", provider="google")
    result = independence(implementer, auditor)
    assert result.class_ == DIFFERENT_FAMILY


def test_different_family_negative_same_provider() -> None:
    implementer = _identity(runner="claude-code-cli", provider="anthropic")
    auditor = _identity(runner="claude-code-cli", provider="anthropic", auth_profile_ref="profile-b")
    result = independence(implementer, auditor)
    assert result.class_ != DIFFERENT_FAMILY


def test_different_runtime_positive() -> None:
    implementer = _identity(runner="claude-code-cli", provider="anthropic")
    auditor = _identity(runner="pal-mcp-clink", provider="anthropic", auth_profile_ref="profile-b")
    result = independence(implementer, auditor)
    assert result.class_ == DIFFERENT_RUNTIME


def test_different_runtime_negative_same_runner() -> None:
    implementer = _identity(runner="claude-code-cli", provider="anthropic")
    auditor = _identity(runner="claude-code-cli", provider="anthropic", auth_profile_ref="profile-b")
    result = independence(implementer, auditor)
    assert result.class_ != DIFFERENT_RUNTIME


def test_same_family_different_session_via_auth_profile() -> None:
    implementer = _identity(auth_profile_ref="profile-a")
    auditor = _identity(auth_profile_ref="profile-b")
    result = independence(implementer, auditor)
    assert result.class_ == SAME_FAMILY_DIFFERENT_SESSION


def test_same_family_different_session_via_runner_version_when_auth_unknown() -> None:
    implementer = _identity(auth_profile_ref="UNKNOWN", runner_version="2.1")
    auditor = _identity(auth_profile_ref="UNKNOWN", runner_version="2.2")
    result = independence(implementer, auditor)
    assert result.class_ == SAME_FAMILY_DIFFERENT_SESSION


def test_same_family_different_session_negative_identical_session() -> None:
    implementer = _identity()
    auditor = _identity()
    result = independence(implementer, auditor)
    assert result.class_ != SAME_FAMILY_DIFFERENT_SESSION


def test_self_certification_same_runner_provider_auth_profile() -> None:
    implementer = _identity()
    auditor = _identity()
    result = independence(implementer, auditor)
    assert result.class_ == UNKNOWN
    assert any(SELF_CERTIFICATION_RISK in reason for reason in result.reasons)


def test_self_certification_wins_over_runner_version_difference() -> None:
    """Same runner, provider and auth_profile_ref but different runner_version:
    invariant 3's self-certification clause is unconditional and does not
    mention runner_version, so self-certification still wins.
    """
    implementer = _identity(runner_version="2.1")
    auditor = _identity(runner_version="9.9")
    result = independence(implementer, auditor)
    assert result.class_ == UNKNOWN
    assert any(SELF_CERTIFICATION_RISK in reason for reason in result.reasons)


@pytest.mark.parametrize(
    "field",
    ["provider", "runner"],
)
def test_unknown_field_on_either_side_yields_unknown(field: str) -> None:
    implementer = _identity(**{field: "UNKNOWN"})
    auditor = _identity(runner="agy", provider="google")
    result = independence(implementer, auditor)
    assert result.class_ == UNKNOWN


def test_not_exposed_is_also_non_comparable() -> None:
    implementer = _identity(provider="NOT_EXPOSED")
    auditor = _identity(runner="agy", provider="google")
    result = independence(implementer, auditor)
    assert result.class_ == UNKNOWN


def test_unknown_auth_profile_and_unknown_runner_version_same_family_yields_unknown() -> None:
    implementer = _identity(auth_profile_ref="UNKNOWN", runner_version="UNKNOWN")
    auditor = _identity(auth_profile_ref="UNKNOWN", runner_version="UNKNOWN")
    result = independence(implementer, auditor)
    assert result.class_ == UNKNOWN


def test_independence_never_returns_approval_field() -> None:
    result = independence(_identity(), _identity(provider="google", runner="agy"))
    field_names = {f for f in vars(result)}
    assert "approved" not in field_names
    assert "approval" not in field_names
