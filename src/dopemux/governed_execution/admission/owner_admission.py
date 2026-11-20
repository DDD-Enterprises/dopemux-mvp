"""Owner-local admission ahead of the unchanged canonical GEC validation boundary.

Resolver instances are trusted native application ports, never model dictionaries.
This release supplies an explicitly synthetic local resolver and no live owner bridge.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from typing import Protocol

from ..receipts.validate import DEFAULT_SCHEMA_DIR, Provenance, ValidatedReceipt, validate_receipt
from .identity import AdmissionError, ExpectedScope, resolve_bound_identity


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def strict_json(raw):
    if not isinstance(raw, bytes) or len(raw) > 262144:
        raise AdmissionError("E_SCHEMA", "Expected bounded JSON bytes")

    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    def invalid(value):
        raise ValueError("Nonfinite JSON number")

    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise AdmissionError("E_SCHEMA", str(exc)) from exc


def native_schema_digest():
    return hashlib.sha256(
        canonical(
            {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(DEFAULT_SCHEMA_DIR.glob("*.schema.json"))
            }
        )
    ).hexdigest()


def validate_projection(family, payload):
    """Validate a portable projection against the bundled local schema only.

    Projection validation is structural and never authenticates an issuer.
    """
    from jsonschema import Draft202012Validator, FormatChecker

    path = (
        Path(__file__).resolve().parents[4]
        / "schemas/supervisor/full-system-contracts.v1.schema.json"
    )
    try:
        bundle = strict_json(path.read_bytes())
        schema = {
            "$schema": bundle["$schema"],
            "$defs": bundle["$defs"],
            "$ref": "#/$defs/" + family,
        }
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(payload)
    except (OSError, KeyError, ValueError) as exc:
        raise AdmissionError("E_SCHEMA", "Local portable schema unavailable or invalid") from exc
    except Exception as exc:
        raise AdmissionError("E_SCHEMA", "Portable projection rejected") from exc


@dataclass(frozen=True)
class OwnerEvidence:
    owner_domain: str
    issuer_ref: str
    principal_ref: str
    source_generation: int
    expires_at: float
    trust_digest: str
    kind: str
    raw_bytes: bytes
    evidence: dict
    scope: ExpectedScope
    delegation_depth_limit: int
    registry_path: object
    registry_generation: int
    fixture_only: bool


class OwnerResolver(Protocol):
    def resolve(self, receipt_ref, principal_ref) -> OwnerEvidence: ...


@dataclass(frozen=True)
class AdmittedReceipt:
    projection: dict
    canonical_receipt: ValidatedReceipt
    scope: ExpectedScope
    receipt_ref: dict
    principal_ref: str
    generation: int
    fixture_only: bool


class OwnerAdmitter:
    def __init__(self, owner_domain, resolver=None):
        self.owner_domain, self.resolver = owner_domain, resolver

    def admit(self, receipt_ref, principal_ref, expected_scope, expected_generation):
        if not isinstance(expected_scope, ExpectedScope) or type(expected_generation) is not int:
            raise AdmissionError("E_SCHEMA", "Typed expected scope and generation required")
        if (
            not isinstance(receipt_ref, dict)
            or set(receipt_ref) != {"ref_id", "sha256", "classification", "locator"}
            or any(not isinstance(v, str) or not v for v in receipt_ref.values())
        ):
            raise AdmissionError("E_SCHEMA", "Exact immutable source reference required")
        if (
            not isinstance(principal_ref, str)
            or not principal_ref.strip()
            or expected_generation < 1
        ):
            raise AdmissionError(
                "E_SCHEMA", "Explicit principal and nonnegative generation required"
            )
        validate_projection("evidence_ref", receipt_ref)
        validate_projection("id", principal_ref)
        if self.resolver is None:
            raise AdmissionError(
                "E_ISSUER_UNAVAILABLE", "No authenticated native owner port installed"
            )
        owner = self.resolver.resolve(receipt_ref, principal_ref)
        if not isinstance(owner, OwnerEvidence):
            raise AdmissionError("E_AUTHENTICITY", "Resolver did not supply native owner evidence")
        if owner.owner_domain != self.owner_domain:
            raise AdmissionError("E_ROLE", "Foreign owner cannot supply this role")
        if owner.principal_ref != principal_ref:
            raise AdmissionError("E_AUTHENTICITY", "Principal binding mismatch")
        if owner.source_generation != expected_generation:
            raise AdmissionError("E_STALE", "Owner generation changed")
        now = time.time()
        if now >= min(owner.expires_at, expected_scope.expires_at):
            raise AdmissionError("E_STALE", "Owner scope expired")
        expected_scope.require_within(owner.scope, owner.delegation_depth_limit)
        if owner.trust_digest != expected_scope.trust_digest:
            raise AdmissionError("E_AUTHENTICITY", "Trust policy does not match owner")
        if expected_scope.schema_set_digest != native_schema_digest():
            raise AdmissionError("E_DRIFT", "Canonical schema set changed")
        resolve_bound_identity(expected_scope, owner.registry_path, owner.registry_generation)
        payload = strict_json(owner.raw_bytes)
        if (
            not isinstance(payload, dict)
            or payload.get("schema_version")
            != "dopemux.governed_execution.dispatch_input_receipt.v1"
        ):
            raise AdmissionError(
                "E_UNSUPPORTED_VERSION", "This first-wave port supports dispatch-input v1 only"
            )
        if owner.kind != "dispatch_input_receipt.v1":
            raise AdmissionError("E_UNSUPPORTED_VERSION", "Unsupported native canonical kind")
        if (
            payload.get("macro_id") != expected_scope.macro_id
            or payload.get("packet_id") != expected_scope.packet_id
        ):
            raise AdmissionError("E_SCOPE", "Canonical packet subject does not match")
        if payload.get("receipt_type") != "ScopeAuthority" or payload.get("scope_status") != "PASS":
            raise AdmissionError("E_POLICY", "Native scope authority did not pass")
        observed = datetime.fromtimestamp(now, timezone.utc).isoformat().replace("+00:00", "Z")
        try:
            validated = validate_receipt(
                owner.kind,
                owner.raw_bytes,
                Provenance(
                    verified_by=("SYNTHETIC_FIXTURE:" if owner.fixture_only else "")
                    + owner.owner_domain
                    + ":"
                    + principal_ref,
                    verified_at=observed,
                    schema_set_digest=expected_scope.schema_set_digest,
                ),
            )
        except Exception as exc:
            raise AdmissionError(
                "E_SCHEMA", "Original canonical validator rejected source"
            ) from exc
        projection = {
            "schema_version": "dopemux.owner_admission.v1",
            "admission_id": "admission:"
            + hashlib.sha256(
                canonical(
                    {
                        "ref": receipt_ref,
                        "generation": expected_generation,
                        "subject": expected_scope.subject_digest,
                        "principal": principal_ref,
                    }
                )
            ).hexdigest(),
            "owner_domain": owner.owner_domain,
            "issuer_ref": owner.issuer_ref,
            "principal_ref": principal_ref,
            "project_id": expected_scope.project_id,
            "macro_id": expected_scope.macro_id,
            "packet_id": expected_scope.packet_id,
            "subject_digest": expected_scope.subject_digest,
            "source_generation": expected_generation,
            "decision": "ADMITTED",
            "source_receipt": {"schema_kind": owner.kind, "evidence": receipt_ref},
            "verification_method": "LOCAL_OWNER_RESOLVER",
            "trust_digest": expected_scope.trust_digest,
            "observed_at": observed,
            "expires_at": datetime.fromtimestamp(
                min(owner.expires_at, expected_scope.expires_at), timezone.utc
            )
            .isoformat()
            .replace("+00:00", "Z"),
            "authority": "NONE",
        }
        validate_projection("admission", projection)
        return AdmittedReceipt(
            projection,
            validated,
            expected_scope,
            dict(receipt_ref),
            principal_ref,
            expected_generation,
            owner.fixture_only,
        )

    def recheck(self, admitted):
        return self.admit(
            admitted.receipt_ref, admitted.principal_ref, admitted.scope, admitted.generation
        )
