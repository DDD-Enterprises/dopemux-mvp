"""FreezeReceipt authoring.

Binds a repo identity, base/head/tree sha and a set of substantive
path -> bytes blobs into a schema-valid ``freeze_receipt.v1`` payload. All
inputs (shas, blobs, timestamps) are caller-supplied; this module never runs
git and never reads a clock. Digests are computed exactly as MACRO W04
invariant 4 specifies:

- ``substantive_path_digest`` = sha256 of the newline-joined sorted paths.
- ``candidate_digest`` = sha256 over the concatenation of
  ``"<sha256(blob)>\\n"`` for each path, in sorted path order.

Both digests are therefore independent of the order paths or blobs were
supplied in.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Mapping, Sequence

from dopemux.governed_execution.receipts.store import EvidenceRef
from dopemux.governed_execution.receipts.validate import Provenance, validate_receipt

_KIND = "freeze_receipt.v1"
_SCHEMA_VERSION = "dopemux.governed_execution.freeze_receipt.v1"


@dataclass(frozen=True)
class RepoIdentity:
    """A caller-attested repository identity (never derived by running git)."""

    origin_url: str
    toplevel: str


@dataclass(frozen=True)
class FreezeSubject:
    """The candidate content a FreezeReceipt is authored over."""

    repo_identity: RepoIdentity
    base_sha: str
    head_sha: str
    tree_sha: str
    blobs: Mapping[str, bytes]


def substantive_path_digest(paths: Sequence[str]) -> str:
    """sha256 of the newline-joined, sorted, deduplicated ``paths``."""
    joined = "\n".join(sorted(set(paths)))
    return sha256(joined.encode("utf-8")).hexdigest()


def candidate_digest(blobs: Mapping[str, bytes]) -> str:
    """sha256 over ``"<sha256(blob)>\\n"`` per path, in sorted path order."""
    parts = "".join(f"{sha256(blobs[path]).hexdigest()}\n" for path in sorted(blobs))
    return sha256(parts.encode("ascii")).hexdigest()


def author_freeze_receipt(
    subject: FreezeSubject,
    *,
    validation_refs: Sequence[EvidenceRef],
    review_refs: Sequence[EvidenceRef],
    frozen_at: str,
    packet_id: str,
    macro_id: str,
    provenance: Provenance,
    supersedes_freeze_ref: EvidenceRef | None = None,
) -> Mapping[str, Any]:
    """Author and schema-validate a FreezeReceipt for ``subject``.

    ``validation_refs`` must be non-empty (the schema requires at least one).
    ``freeze_state`` is always authored as ``"FROZEN"``,
    ``no_audit_before_freeze`` is always ``True`` and ``authority`` is always
    ``"NONE"``. ``supersedes_freeze_ref``, when given, is the EvidenceRef of
    the prior FreezeReceipt this one replaces (a NEW_FREEZE event).

    Returns the validated payload dict; raises ReceiptInvalid if, despite
    this authoring logic, the assembled payload fails schema validation.
    """
    paths = sorted(subject.blobs)
    payload: dict[str, Any] = {
        "schema_version": _SCHEMA_VERSION,
        "packet_id": packet_id,
        "macro_id": macro_id,
        "repo_identity": {
            "origin_url": subject.repo_identity.origin_url,
            "toplevel": subject.repo_identity.toplevel,
        },
        "base_sha": subject.base_sha,
        "head_sha": subject.head_sha,
        "tree_sha": subject.tree_sha,
        "substantive_paths": paths,
        "substantive_path_digest": substantive_path_digest(paths),
        "candidate_digest": candidate_digest(subject.blobs),
        "validation_refs": [
            {"path": ref.path, "sha256": ref.sha256} for ref in validation_refs
        ],
        "review_refs": [
            {"path": ref.path, "sha256": ref.sha256} for ref in review_refs
        ],
        "frozen_at": frozen_at,
        "freeze_state": "FROZEN",
        "no_audit_before_freeze": True,
        "authority": "NONE",
    }
    if supersedes_freeze_ref is not None:
        payload["supersedes_freeze_ref"] = {
            "path": supersedes_freeze_ref.path,
            "sha256": supersedes_freeze_ref.sha256,
        }
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    validated = validate_receipt(_KIND, raw, provenance)
    return validated.payload
