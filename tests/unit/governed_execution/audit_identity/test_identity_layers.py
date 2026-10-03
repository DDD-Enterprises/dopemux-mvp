"""Tests for AuditIdentity, IdentityLayer and layers()."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from dopemux.governed_execution.audit_identity.identity import (
    AuditIdentity,
    IdentityLayer,
    QualificationReceiptRef,
    layers,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
SRC_DIR = REPO_ROOT / "src" / "dopemux" / "governed_execution" / "audit_identity"
ENUMS_SCHEMA_PATH = REPO_ROOT / "schemas" / "governed_execution" / "enums.v1.schema.json"

_MODEL_LAYER_FIELDS = (
    "requested_model",
    "configured_model",
    "response_claimed_model",
    "provider_attested_model",
)


def _make(**overrides: str) -> AuditIdentity:
    base = dict(
        runner="claude-code-cli",
        runner_version="2.1",
        requested_model="claude-sonnet-5",
        configured_model="sonnet",
        response_claimed_model="claude-sonnet-5-response",
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


def test_identity_layer_enum_matches_schema() -> None:
    """Drift guard: IdentityLayer must mirror enums.v1 identity_layer exactly."""
    data = json.loads(ENUMS_SCHEMA_PATH.read_text(encoding="utf-8"))
    schema_values = tuple(data["definitions"]["identity_layer"]["enum"])
    assert schema_values == tuple(member.value for member in IdentityLayer)


def test_five_layers_distinct_after_construction() -> None:
    identity = _make()
    values = (
        identity.runner,
        identity.requested_model,
        identity.configured_model,
        identity.response_claimed_model,
        identity.provider_attested_model,
    )
    assert len(set(values)) == 5


def test_five_layers_distinct_after_validate() -> None:
    identity = _make()
    assert identity.validate() is True
    values = (
        identity.runner,
        identity.requested_model,
        identity.configured_model,
        identity.response_claimed_model,
        identity.provider_attested_model,
    )
    assert len(set(values)) == 5


def test_five_layers_distinct_after_layers_call() -> None:
    identity = _make()
    result = layers(identity)
    values = (identity.runner, *result.values())
    assert len(set(values)) == 5


def test_layers_returns_four_model_fields_no_proxy_reported() -> None:
    identity = _make()
    result = layers(identity)
    assert set(result) == {
        IdentityLayer.REQUESTED,
        IdentityLayer.CONFIGURED,
        IdentityLayer.RESPONSE_CLAIMED,
        IdentityLayer.PROVIDER_ATTESTED,
    }
    assert IdentityLayer.PROXY_REPORTED not in result
    assert result[IdentityLayer.REQUESTED] == identity.requested_model
    assert result[IdentityLayer.CONFIGURED] == identity.configured_model
    assert result[IdentityLayer.RESPONSE_CLAIMED] == identity.response_claimed_model
    assert result[IdentityLayer.PROVIDER_ATTESTED] == identity.provider_attested_model


def test_layers_mapping_is_read_only() -> None:
    identity = _make()
    result = layers(identity)
    with pytest.raises(TypeError):
        result[IdentityLayer.REQUESTED] = "mutated"  # type: ignore[index]


@pytest.mark.parametrize("field", _MODEL_LAYER_FIELDS + ("runner", "provider", "auth_profile_ref"))
@pytest.mark.parametrize("sentinel", ["UNKNOWN", "NOT_EXPOSED"])
def test_unknown_and_not_exposed_are_legal_on_any_string_field(field: str, sentinel: str) -> None:
    identity = _make(**{field: sentinel})
    assert identity.validate() is True
    assert getattr(identity, field) == sentinel


def test_validate_rejects_unknown_independence_class() -> None:
    identity = _make(independence_class="NOT_A_REAL_CLASS")
    assert identity.validate() is False


def test_validate_accepts_qualification_receipt_ref() -> None:
    identity = _make(
        qualification_receipt=QualificationReceiptRef(
            path="proof/W07/QUALIFICATION.md",
            sha256="a" * 64,
        )
    )
    assert identity.validate() is True


def test_validate_rejects_malformed_qualification_receipt_ref() -> None:
    identity = _make(
        qualification_receipt=QualificationReceiptRef(path="proof/x", sha256="not-hex")
    )
    assert identity.validate() is False


@pytest.mark.parametrize("value", ["NOT_RUN", "UNKNOWN", "NOT_EXPOSED"])
def test_validate_accepts_qualification_receipt_sentinels(value: str) -> None:
    identity = _make(qualification_receipt=value)
    assert identity.validate() is True


def test_validate_rejects_arbitrary_qualification_receipt_string() -> None:
    identity = _make(qualification_receipt="some-other-string")
    assert identity.validate() is False


def test_audit_identity_is_frozen() -> None:
    identity = _make()
    with pytest.raises(AttributeError):
        identity.requested_model = "mutated"  # type: ignore[misc]


def test_no_function_in_package_derives_one_layer_field_from_another() -> None:
    """Grep-style guard: no line in the audit_identity package assigns one
    model-identity layer field from another. This is a structural guard,
    not a semantic proof, but it catches the mistake I16 forbids.
    """
    assign_pattern = re.compile(r"^(\w+)\s*=\s*(.+)$")
    violations: list[str] = []
    for path in sorted(SRC_DIR.glob("*.py")):
        for lineno, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            line = raw_line.strip()
            match = assign_pattern.match(line)
            if not match:
                continue
            lhs, rhs = match.group(1), match.group(2)
            for field in _MODEL_LAYER_FIELDS:
                if field != lhs:
                    continue
                for other in _MODEL_LAYER_FIELDS:
                    if other != field and re.search(rf"\b{other}\b", rhs):
                        violations.append(f"{path.name}:{lineno}: {raw_line.strip()}")
    assert violations == []
