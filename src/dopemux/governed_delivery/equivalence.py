"""Semantic proof-only successor equivalence — closes GOV-AUD-F1.

The independent architecture audit constructed this attack against a
path-membership predicate: a proof bundle's known-risks list, unknowns, or
evidence-ref list lives *inside* an allowed proof-only path and is consumed
downstream by PR Steward and the operator merge card. Hand-editing it passes
every path and digest conjunct while laundering a governance-relevant change
past re-audit. A path allowlist is therefore necessary but not sufficient.

Two design choices answer that attack:

1. Classification is total and fails closed. Every compared field resolves to
   GOVERNANCE_RELEVANT, INERT, or UNKNOWN, and UNKNOWN is rejected rather than
   waved through — so a field nobody anticipated cannot become a channel.

2. Governance fields are compared as a path-independent aggregate. Byte-identical
   relocation of a proof reference leaves the aggregate untouched and passes,
   while semantic drift fails no matter which file happens to carry it.

The receipt enumerates every compared field, so a vacuous evaluation is visibly
different from a genuine one. No I/O: ancestry, digests, and bundle contents are
supplied by the caller.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import Any, Iterable, Mapping, Sequence

from .models import (
    SCHEMA_PROOF_ONLY_EQUIVALENCE,
    Denial,
    NormalizedFailureClass,
    canonical_json,
    digest_of,
)

VALIDATOR_VERSION = "governed-delivery.equivalence.1"

CONTENT_DIGEST_EXCLUSION_DEFINITION = (
    "sha256 over sorted (path, sha256(bytes)) pairs for every file NOT matching allowed_paths"
)

# Substring keywords marking a field as governance-relevant. Deliberately a
# broad net: over-matching costs a false rejection, under-matching would let a
# governance change through, and only the second failure mode is unsafe.
GOVERNANCE_FIELD_KEYWORDS: tuple[str, ...] = (
    "verdict",
    "risk",
    "unknown",
    "blocker",
    "finding",
    "conflict",
    "authority",
    "scope",
    "acceptance",
    "criteri",
    "operator",
    "decision",
    "head",
    "tree",
    "digest",
    "sha",
    "signature",
    "validation",
    "valid",
    "test",
    "security",
    "secret",
    "merge",
    "activation",
    "identity",
    "independence",
    "auditor",
    "audit",
    "ready",
    "claim",
    "gate",
    "evidence",
    "packet",
    "policy",
    "base",
    "status",
)

# Exact field names known to carry no governance meaning. Checked only after the
# governance net, and matched exactly rather than by substring, so a name like
# "audit_result_checksum" stays governance-relevant.
INERT_FIELD_NAMES: frozenset[str] = frozenset(
    {
        "checksum",
        "checksums",
        "bundle_checksum",
        "packaging_checksum",
        "file_checksum",
        "archive_checksum",
        "generated_at",
        "generated_by",
        "generator",
        "generator_version",
        "formatting",
        "format_version",
        "encoding",
        "line_ending",
        "byte_order_mark",
        "indent",
        "toc",
        "table_of_contents",
        "rendered_at",
        "display_order",
    }
)


class FieldClassification(str):
    GOVERNANCE_RELEVANT = "GOVERNANCE_RELEVANT"
    INERT = "INERT"
    UNKNOWN = "UNKNOWN"


def classify_field(field_name: str) -> str:
    """Classify a semantic field. Total, ordered, and fail-closed.

    The governance net is applied first so that a compound name containing a
    governance token wins over an inert-looking leaf.
    """
    normalized = field_name.strip().lower()
    if not normalized:
        return FieldClassification.UNKNOWN

    leaf = normalized.rsplit(".", 1)[-1]

    for keyword in GOVERNANCE_FIELD_KEYWORDS:
        if keyword in normalized:
            return FieldClassification.GOVERNANCE_RELEVANT

    if leaf in INERT_FIELD_NAMES or normalized in INERT_FIELD_NAMES:
        return FieldClassification.INERT

    return FieldClassification.UNKNOWN


def flatten(document: Any, prefix: str = "") -> dict[str, str]:
    """Flatten a document to dotted field paths with canonical scalar values.

    List indices are dropped from the field name and the list is canonicalized
    as a whole, so reordering a governance list is a change while relocating the
    document that carries it is not.
    """
    flat: dict[str, str] = {}
    if isinstance(document, Mapping):
        for key, value in document.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(value, Mapping):
                flat.update(flatten(value, child))
            else:
                flat[child] = canonical_json(value)
    else:
        flat[prefix or "<root>"] = canonical_json(document)
    return flat


@dataclass(frozen=True)
class ProofOnlyBundle:
    """The governance-bearing content of one side of the comparison.

    ``documents`` maps a logical document name to its parsed content. Path is
    deliberately not part of the key, because relocation must not by itself
    register as a semantic change.
    """

    documents: Mapping[str, Any] = field(default_factory=dict)

    def aggregate_fields(self) -> dict[str, list[str]]:
        """Path-independent aggregate: field name to its sorted multiset of values.

        A multiset, not a single value per name. An earlier design disambiguated
        repeated names by synthesising a ``field#document`` key, but that
        separator lived in the same namespace as real field names and was
        therefore forgeable: an edited bundle could drop a risk from one document
        and re-encode it as a literal ``field#document`` key in another,
        reproducing the original aggregate exactly. Counting values instead
        removes the synthesised namespace, so no crafted field name can restore a
        multiset that a dropped value has changed.
        """
        aggregate: dict[str, list[str]] = {}
        for name in sorted(self.documents):
            for field_name, value in flatten(self.documents[name]).items():
                aggregate.setdefault(field_name, []).append(value)
        return {name: sorted(values) for name, values in aggregate.items()}


@dataclass(frozen=True)
class FieldComparison:
    field: str
    classification: str
    changed: bool
    outcome: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "classification": self.classification,
            "changed": self.changed,
            "outcome": self.outcome,
        }


@dataclass(frozen=True)
class EquivalenceResult:
    equivalence_id: str
    passed: bool
    audited_head: str
    successor_head: str
    ancestry_basis: str
    ancestry_established: bool
    allowed_paths: Sequence[str]
    actual_changed_paths: Sequence[str]
    non_allowed_diff_count: int
    raw_diff_digest: str
    raw_diff_contains_no_substantive_source_change: bool
    content_tree_equivalent_under_exclusion: bool
    packet_digest_unchanged: bool
    policy_digest_unchanged: bool
    audit_result_digest_unchanged: bool
    compared_fields: Sequence[FieldComparison]
    failures: Sequence[Mapping[str, str]]
    merge_base: str | None = None

    @property
    def mismatched_fields(self) -> list[str]:
        return [
            item.field
            for item in self.compared_fields
            if item.outcome == "GOVERNANCE_CHANGE_REJECTED"
        ]

    @property
    def unclassified_fields(self) -> list[str]:
        return [
            item.field for item in self.compared_fields if item.outcome == "UNCLASSIFIED_REJECTED"
        ]

    def as_dict(self) -> dict[str, Any]:
        body = {
            "schema_version": SCHEMA_PROOF_ONLY_EQUIVALENCE,
            "equivalence_id": self.equivalence_id,
            "result": "PASS" if self.passed else "FAIL",
            "audited_head": self.audited_head,
            "successor_head": self.successor_head,
            "merge_base": self.merge_base,
            "ancestry_basis": self.ancestry_basis,
            "ancestry_established": self.ancestry_established,
            "allowed_paths": list(self.allowed_paths),
            "actual_changed_paths": list(self.actual_changed_paths),
            "non_allowed_diff_count": self.non_allowed_diff_count,
            "raw_diff_digest": self.raw_diff_digest,
            "raw_diff_contains_no_substantive_source_change": self.raw_diff_contains_no_substantive_source_change,
            "content_digest_exclusion_definition": CONTENT_DIGEST_EXCLUSION_DEFINITION,
            "content_tree_equivalent_under_exclusion": self.content_tree_equivalent_under_exclusion,
            "packet_digest_unchanged": self.packet_digest_unchanged,
            "policy_digest_unchanged": self.policy_digest_unchanged,
            "audit_result_digest_unchanged": self.audit_result_digest_unchanged,
            "compared_fields": [item.as_dict() for item in self.compared_fields],
            "compared_field_count": len(self.compared_fields),
            "mismatched_fields": self.mismatched_fields,
            "unclassified_fields": self.unclassified_fields,
            "failures": [dict(item) for item in self.failures],
            "validator_version": VALIDATOR_VERSION,
        }
        body["receipt_digest"] = digest_of(body)
        return body


def _paths_within_allowlist(paths: Iterable[str], allowed: Sequence[str]) -> list[str]:
    outside: list[str] = []
    for path in paths:
        if not any(fnmatch(path, pattern) for pattern in allowed):
            outside.append(path)
    return outside


def evaluate_proof_only_equivalence(
    *,
    equivalence_id: str,
    audited_head: str,
    successor_head: str,
    audited_bundle: ProofOnlyBundle | None,
    successor_bundle: ProofOnlyBundle | None,
    allowed_paths: Sequence[str],
    actual_changed_paths: Sequence[str],
    raw_diff_digest: str,
    ancestry_established: bool,
    ancestry_basis: str = "UNKNOWN",
    raw_diff_contains_no_substantive_source_change: bool = False,
    content_tree_equivalent_under_exclusion: bool = False,
    audited_packet_digest: str | None = None,
    successor_packet_digest: str | None = None,
    audited_policy_digest: str | None = None,
    successor_policy_digest: str | None = None,
    audited_audit_result_digest: str | None = None,
    successor_audit_result_digest: str | None = None,
    merge_base: str | None = None,
) -> EquivalenceResult:
    """Prove, or refuse to prove, that a successor head is proof-only.

    Every applicable condition must hold. Structural conjuncts (ancestry, path
    membership, tree equality under exclusion, frozen digests) are necessary;
    the semantic aggregate comparison is what makes them sufficient.
    """
    failures: list[dict[str, str]] = []

    if not audited_head or not successor_head:
        raise Denial(
            NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
            "both audited_head and successor_head are required",
        )

    # Anti-vacuity: without the original bundle there is nothing to compare, and
    # an unopposed successor must never be accepted as equivalent.
    if audited_bundle is None:
        failures.append(
            {
                "code": "missing_original_bundle",
                "detail": "no audited proof bundle supplied; equivalence cannot be established",
            }
        )
    if successor_bundle is None:
        failures.append(
            {
                "code": "missing_successor_bundle",
                "detail": "no successor proof bundle supplied; equivalence cannot be established",
            }
        )

    if ancestry_basis not in {"OBSERVED_GIT", "CLAIMED_INPUT", "UNKNOWN"}:
        raise Denial(
            NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
            f"unknown ancestry_basis {ancestry_basis!r}",
        )
    if ancestry_basis == "UNKNOWN" or not ancestry_established:
        failures.append(
            {
                "code": "ancestry_not_established",
                "detail": f"ancestry_established={ancestry_established} basis={ancestry_basis}",
            }
        )

    outside = _paths_within_allowlist(actual_changed_paths, allowed_paths)
    if outside:
        failures.append(
            {
                "code": "path_outside_proof_only_allowlist",
                "detail": f"changed paths outside allowlist: {', '.join(sorted(outside))}",
            }
        )

    if not raw_diff_contains_no_substantive_source_change:
        failures.append(
            {
                "code": "raw_diff_contains_substantive_source_change",
                "detail": "the raw diff was not attested free of substantive source change",
            }
        )

    if not content_tree_equivalent_under_exclusion:
        failures.append(
            {
                "code": "content_tree_not_equivalent_under_exclusion",
                "detail": "audited substantive bytes differ once proof-only paths are excluded",
            }
        )

    packet_unchanged = audited_packet_digest == successor_packet_digest
    policy_unchanged = audited_policy_digest == successor_policy_digest
    audit_unchanged = audited_audit_result_digest == successor_audit_result_digest

    if not packet_unchanged:
        failures.append({"code": "packet_digest_changed", "detail": "packet digest is not identical"})
    if not policy_unchanged:
        failures.append({"code": "policy_digest_changed", "detail": "policy digest is not identical"})
    if not audit_unchanged:
        failures.append(
            {"code": "audit_result_digest_changed", "detail": "audit result digest is not identical"}
        )

    comparisons: list[FieldComparison] = []
    if audited_bundle is not None and successor_bundle is not None:
        before = audited_bundle.aggregate_fields()
        after = successor_bundle.aggregate_fields()

        for name in sorted(set(before) | set(after)):
            old = before.get(name, [])
            new = after.get(name, [])
            # Multiset comparison: a value dropped from one document and added to
            # another leaves the count unchanged, but dropping it outright does not.
            changed = old != new
            classification = classify_field(name)

            if classification == FieldClassification.UNKNOWN:
                outcome = "UNCLASSIFIED_REJECTED"
            elif not changed:
                outcome = "UNCHANGED"
            elif classification == FieldClassification.INERT:
                outcome = "INERT_CHANGE_ALLOWED"
            else:
                outcome = "GOVERNANCE_CHANGE_REJECTED"

            comparisons.append(FieldComparison(name, classification, changed, outcome))

        # Anti-vacuity: proof content exists, so a zero-field comparison means
        # the evaluator inspected nothing and must not report equivalence.
        if not comparisons and (audited_bundle.documents or successor_bundle.documents):
            failures.append(
                {
                    "code": "empty_semantic_field_set",
                    "detail": "proof documents present but no comparable field was extracted",
                }
            )
        elif not comparisons:
            failures.append(
                {
                    "code": "empty_semantic_field_set",
                    "detail": "no semantic field was compared; a vacuous pass is refused",
                }
            )

    rejected = [item for item in comparisons if item.outcome == "GOVERNANCE_CHANGE_REJECTED"]
    if rejected:
        failures.append(
            {
                "code": "governance_relevant_field_changed",
                "detail": "changed governance fields: "
                + ", ".join(sorted(item.field for item in rejected)),
            }
        )

    unclassified = [item for item in comparisons if item.outcome == "UNCLASSIFIED_REJECTED"]
    if unclassified:
        failures.append(
            {
                "code": "unclassified_semantic_field",
                "detail": "unclassifiable fields treated as governance-relevant: "
                + ", ".join(sorted(item.field for item in unclassified)),
            }
        )

    return EquivalenceResult(
        equivalence_id=equivalence_id,
        passed=not failures,
        audited_head=audited_head,
        successor_head=successor_head,
        ancestry_basis=ancestry_basis,
        ancestry_established=ancestry_established,
        allowed_paths=list(allowed_paths),
        actual_changed_paths=list(actual_changed_paths),
        non_allowed_diff_count=len(outside),
        raw_diff_digest=raw_diff_digest,
        raw_diff_contains_no_substantive_source_change=raw_diff_contains_no_substantive_source_change,
        content_tree_equivalent_under_exclusion=content_tree_equivalent_under_exclusion,
        packet_digest_unchanged=packet_unchanged,
        policy_digest_unchanged=policy_unchanged,
        audit_result_digest_unchanged=audit_unchanged,
        compared_fields=comparisons,
        failures=failures,
        merge_base=merge_base,
    )
