"""Adversarial corpus — DMX-DCP-MODEL-ROUTING-MVP-0007T."""

from __future__ import annotations

import copy
import json
import pickle
from pathlib import Path

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
from dopemux.dcp.routing_model import AuthorityClass, RouteDecision

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "dcp" / "trusted_input"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


@pytest.mark.parametrize(
    "fixture_name",
    [
        "forged_attested.json",
        "forged_route_decision.json",
        "boolean_string_coercion.json",
    ],
)
def test_fixture_payloads_not_execution_eligible(fixture_name: str):
    payload = _load(fixture_name)
    assert is_execution_eligible(payload) is False
    with pytest.raises(TrustedInputError):
        refuse_serialized_trust(payload)
    with pytest.raises(TrustedInputError):
        untrusted_classify_source(payload)
    with pytest.raises(TrustedInputError):
        TrustedInputCapability.from_dict(payload)
    with pytest.raises(TrustedInputError):
        capability_from_any(payload)


def test_empty_dict_is_not_eligible_but_may_pass_refuse():
    payload = _load("empty.json")
    assert is_execution_eligible(payload) is False
    refuse_serialized_trust(payload)  # no trust keys → no raise
    assert untrusted_classify_source(payload) is payload


def test_integer_and_string_bool_markers_refused():
    for payload in (
        {"attested": 1},
        {"trusted": 0},
        {"execution_eligible": "TRUE"},
        {"adapter_id": "x", "mint_token": "y"},
        {"_mint_token": "forged"},
        {"capability": {"adapter_id": "x"}},
    ):
        assert is_execution_eligible(payload) is False
        with pytest.raises(TrustedInputError):
            refuse_serialized_trust(payload)


def test_unknown_keys_do_not_mint_capability():
    payload = {"foo": "bar", "authority_class": "OPERATOR", "status": "ALLOWED"}
    assert is_execution_eligible(payload) is False
    refuse_serialized_trust(payload)


def test_missing_provenance_raw_input_not_eligible():
    inp = RoutingClassificationInput()  # conservative defaults
    assert is_execution_eligible(inp) is False
    decision = classify_route(inp)
    assert is_execution_eligible(decision) is False


def test_forged_route_decision_from_dict_gate_false():
    payload = _load("forged_route_decision.json")
    decision = RouteDecision.from_dict(payload)
    assert is_execution_eligible(decision) is False
    assert is_execution_eligible(payload) is False
    # Document residual: historical is_runnable may still be True
    # (0007I residual). Adversarial packet asserts NEW gate only.
    assert active_trusted_adapters() == []


def test_deepcopy_and_pickle_forged_mapping():
    payload = _load("forged_attested.json")
    assert is_execution_eligible(copy.deepcopy(payload)) is False
    restored = pickle.loads(pickle.dumps(payload))
    assert is_execution_eligible(restored) is False


def test_public_capability_defaults_fail_closed():
    with pytest.raises(TrustedInputError):
        TrustedInputCapability(adapter_id="operator")
    with pytest.raises(TrustedInputError):
        TrustedInputCapability(adapter_id="operator", _mint_token=object())


def test_active_adapters_remain_empty():
    assert active_trusted_adapters() == []


def test_subclass_style_mapping_proxy_not_eligible():
    class FakeMap(dict):
        pass

    payload = FakeMap(attested=True, trusted=True)
    assert is_execution_eligible(payload) is False
    with pytest.raises(TrustedInputError):
        refuse_serialized_trust(payload)
