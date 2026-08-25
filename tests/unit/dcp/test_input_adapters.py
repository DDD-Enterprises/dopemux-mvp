"""Tests for DMX-DCP-MODEL-ROUTING-MVP-0007I trusted-input capability boundary."""

from __future__ import annotations

import copy
import pickle

import pytest

from dopemux.dcp.input_adapters import (
    TrustedInputCapability,
    TrustedInputError,
    active_trusted_adapters,
    capability_from_any,
    is_execution_eligible,
    refuse_serialized_trust,
    untrusted_classify_source,
)
from dopemux.dcp.routing_classifier import RoutingClassificationInput, classify_route
from dopemux.dcp.routing_model import (
    AuthorityClass,
    RouteDecision,
    TaskSource,
    TaskType,
)


# ---------------------------------------------------------------------------
# Non-claims locked by tests
# ---------------------------------------------------------------------------


def test_no_active_trusted_adapters():
    assert active_trusted_adapters() == []


def test_raw_input_never_execution_eligible():
    inp = RoutingClassificationInput(
        task_source=TaskSource.OPERATOR,
        task_type=TaskType.CODE_CHANGE,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
    )
    assert is_execution_eligible(inp) is False
    assert is_execution_eligible(inp, capability=None) is False


def test_serialized_attested_true_cannot_mint_eligibility():
    payload = {
        "attested": True,
        "trusted": True,
        "adapter_id": "forged-operator",
        "execution_eligible": True,
    }
    with pytest.raises(TrustedInputError):
        refuse_serialized_trust(payload)
    assert is_execution_eligible(payload) is False
    with pytest.raises(TrustedInputError):
        untrusted_classify_source(payload)


def test_capability_from_dict_forbidden():
    with pytest.raises(TrustedInputError):
        TrustedInputCapability.from_dict(
            {"adapter_id": "x", "attested": True, "_mint_token": "forged"}
        )


def test_public_capability_constructor_rejected():
    with pytest.raises(TrustedInputError):
        TrustedInputCapability(
            adapter_id="forged",
            evidence={"attested": True},
            _mint_token="not-the-module-token",
        )


def test_capability_from_any_always_fails():
    for value in (True, "trusted", {"attested": True}, None, 1, object()):
        with pytest.raises(TrustedInputError):
            capability_from_any(value)


def test_to_dict_is_non_reconstitutable():
    # Even if tests access internal mint for negative restore checks, public
    # path must not reconstitute. Use from_dict refusal on diagnostic dict.
    diagnostic = {
        "capability_type": "TrustedInputCapability",
        "serializable": False,
        "execution_eligible": False,
        "adapter_id": "operator",
    }
    with pytest.raises(TrustedInputError):
        TrustedInputCapability.from_dict(diagnostic)
    assert is_execution_eligible(diagnostic) is False


def test_pickle_fails_closed_for_public_forgeries():
    # There is no live capability to pickle under 0007I public API.
    # Pickling a forged stand-in dict must not yield execution eligibility.
    blob = pickle.dumps({"adapter_id": "x", "attested": True})
    restored = pickle.loads(blob)
    assert is_execution_eligible(restored) is False
    with pytest.raises(TrustedInputError):
        refuse_serialized_trust(restored)


def test_copy_of_raw_input_not_eligible():
    inp = RoutingClassificationInput(authority_class=AuthorityClass.OPERATOR)
    cloned = copy.deepcopy(inp)
    assert is_execution_eligible(cloned) is False


def test_route_decision_from_dict_still_classifies_but_gate_is_false():
    """Existing from_dict path remains usable for inspection; new gate is False.

    0007I does not rewrite RouteDecision.is_runnable (out of allowlist).
    The new boundary is ``is_execution_eligible``.
    """
    forged = {
        "status": "ALLOWED",
        "red_lane_state": "CLEAR",
        "authority_class": "OPERATOR",
        "task_source": "OPERATOR",
        "task_type": "CODE_CHANGE",
        "attested": True,
        "trusted": True,
    }
    decision = RouteDecision.from_dict(forged)
    # Historical API may still report runnable for ALLOWED+CLEAR+OPERATOR —
    # that gap is why 0007I/0007A exist. New gate must not accept the dict.
    assert is_execution_eligible(forged) is False
    assert is_execution_eligible(decision) is False
    with pytest.raises(TrustedInputError):
        refuse_serialized_trust(forged)


def test_classify_route_still_works_on_raw_input():
    """Classification remains pure and available; eligibility stays false."""
    inp = RoutingClassificationInput(
        task_source=TaskSource.OPERATOR,
        task_type=TaskType.READ_ONLY,
        description="read-only classify check",
    )
    decision = classify_route(inp)
    assert isinstance(decision, RouteDecision)
    assert is_execution_eligible(inp) is False
    assert is_execution_eligible(decision) is False


def test_untrusted_classify_source_passthrough_without_trust_keys():
    inp = RoutingClassificationInput()
    assert untrusted_classify_source(inp) is inp
    plain = {"task_type": "ANALYSIS", "description": "ok"}
    assert untrusted_classify_source(plain) is plain


def test_module_exports_no_enable_mutation_adapter():
    import dopemux.dcp.input_adapters as mod

    # No public enable/register mutation helper that activates adapters.
    for name in (
        "enable_trusted_adapter",
        "register_trusted_adapter",
        "activate_adapter",
        "mint_for_mutation",
    ):
        assert not hasattr(mod, name)


def test_package_exports_capability_surface():
    from dopemux import dcp

    assert hasattr(dcp, "TrustedInputCapability")
    assert hasattr(dcp, "is_execution_eligible")
    assert hasattr(dcp, "active_trusted_adapters")
    assert dcp.active_trusted_adapters() == []
    assert dcp.is_execution_eligible(RoutingClassificationInput()) is False


def test_evidence_deep_frozen():
    from dopemux.dcp.input_adapters import _freeze_value
    mutable_nested = {"key": [1, 2, {"inner": "val"}], "set_key": {3, 4}}
    frozen = _freeze_value(mutable_nested)
    assert isinstance(frozen["key"], tuple)
    assert isinstance(frozen["key"][2], type(frozen))
    assert isinstance(frozen["set_key"], frozenset)
