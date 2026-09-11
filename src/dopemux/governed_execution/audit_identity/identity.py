"""Structured audit identity: five distinct, never-reconciled identity layers.

Pure module: no filesystem writes, no external process spawning, no clock,
no network. Schema enum values are read once, read-only, via
``pathlib.Path.read_text()``.

The dataclass fields intentionally track the identity layers already used by
``schemas/governed_execution/execution_binding.v2.schema.json`` (W01, same
MacroPacket, A1-audited PASS): ``requested_model``, ``configured_model``,
``response_claimed_model`` and ``provider_attested_model``. That schema has
no ``proxy_reported`` layer either, even though
``enums.v1.schema.json#/definitions/identity_layer`` also defines a
``PROXY_REPORTED`` member (used elsewhere, by the out-of-scope audit_broker
schema family, for LLM-routing-proxy identity). ``IdentityLayer`` below is
the complete five-member enum for type-safety and future extension, but
``AuditIdentity`` carries no field for ``PROXY_REPORTED`` and ``layers()``
therefore returns four entries, not five. This is a deliberate scope
decision, not an omission: see the W07 section of
``docs/03-reference/governance/governed-execution-contract-v2.md``.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Union

REPO_ROOT = Path(__file__).resolve().parents[4]
_ENUMS_SCHEMA_PATH = REPO_ROOT / "schemas" / "governed_execution" / "enums.v1.schema.json"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

_SENTINEL_QUALIFICATION_RECEIPTS = frozenset({"NOT_RUN", "UNKNOWN", "NOT_EXPOSED"})


def _read_enum_values(definition_name: str) -> tuple[str, ...]:
    """Read one enum's legal values from ``enums.v1.schema.json``, read-only."""
    data = json.loads(_ENUMS_SCHEMA_PATH.read_text(encoding="utf-8"))
    return tuple(data["definitions"][definition_name]["enum"])


_INDEPENDENCE_CLASS_VALUES = _read_enum_values("independence_class")


class IdentityLayer(Enum):
    """Mirrors ``enums.v1.schema.json#/definitions/identity_layer`` exactly.

    A drift-guard test re-reads the schema file and asserts member-for-member
    equality against this enum, so the two cannot silently diverge.
    """

    REQUESTED = "REQUESTED"
    CONFIGURED = "CONFIGURED"
    RESPONSE_CLAIMED = "RESPONSE_CLAIMED"
    PROXY_REPORTED = "PROXY_REPORTED"
    PROVIDER_ATTESTED = "PROVIDER_ATTESTED"


@dataclass(frozen=True)
class QualificationReceiptRef:
    """A pointer to a qualification receipt: a repo-relative path and its sha256."""

    path: str
    sha256: str

    def validate(self) -> bool:
        if not self.path:
            return False
        return bool(_SHA256_RE.fullmatch(self.sha256))


QualificationReceipt = Union[str, QualificationReceiptRef]


@dataclass(frozen=True)
class AuditIdentity:
    """Five distinct identity layers plus runner, effort, environment and
    independence metadata. Every string field accepts the sentinels
    ``UNKNOWN`` and ``NOT_EXPOSED`` as legal, uncoerced values (I16): no
    function anywhere in this package fills one field from another.
    """

    runner: str
    runner_version: str
    requested_model: str
    configured_model: str
    response_claimed_model: str
    provider_attested_model: str
    provider: str
    effort_requested: str
    effort_observed: str
    auth_profile_ref: str
    containment: str
    network_posture: str
    independence_class: str
    qualification_receipt: QualificationReceipt

    def validate(self) -> bool:
        """Pure, deterministic structural check. Never raises."""
        if self.independence_class not in _INDEPENDENCE_CLASS_VALUES:
            return False
        receipt = self.qualification_receipt
        if isinstance(receipt, QualificationReceiptRef):
            return receipt.validate()
        if isinstance(receipt, str):
            return receipt in _SENTINEL_QUALIFICATION_RECEIPTS
        return False


def layers(identity: AuditIdentity) -> Mapping[IdentityLayer, str]:
    """Return the four model-identity layers this AuditIdentity carries, keyed
    by ``IdentityLayer``. No merging: each value is read directly off
    ``identity`` and never derived from another field. ``IdentityLayer.
    PROXY_REPORTED`` is intentionally absent (see module docstring).
    """
    return MappingProxyType(
        {
            IdentityLayer.REQUESTED: identity.requested_model,
            IdentityLayer.CONFIGURED: identity.configured_model,
            IdentityLayer.RESPONSE_CLAIMED: identity.response_claimed_model,
            IdentityLayer.PROVIDER_ATTESTED: identity.provider_attested_model,
        }
    )
