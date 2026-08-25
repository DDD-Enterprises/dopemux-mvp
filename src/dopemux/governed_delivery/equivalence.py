"""Semantic proof-only successor equivalence — closes GOV-AUD-F1 and F1's residue.

The independent architecture audit constructed this attack against a
path-membership predicate: a proof bundle's known-risks list, unknowns, or
evidence-ref list lives *inside* an allowed proof-only path and is consumed
downstream by PR Steward and the operator merge card. Hand-editing it passes
every path and digest conjunct while laundering a governance-relevant change
past re-audit. A path allowlist is therefore necessary but not sufficient.

Four design choices answer that attack and the follow-up audit's findings:

1. Classification is total and fails closed. Every compared field resolves to
   GOVERNANCE_RELEVANT, INERT, or UNKNOWN, and UNKNOWN is rejected rather than
   waved through — so a field nobody anticipated cannot become a channel.

2. Governance fields are compared per exact document path and role. Relocation
   therefore fails closed, and moving an assertion between same-basename files
   cannot hide a risk or blocker swap.

3. Values are compared as a sorted multiset keyed by a *tuple*
   ``(path, role, field)``. No key is synthesised by string concatenation, so no
   crafted field name shares a namespace with a real one.

4. Structural conjuncts carry the basis on which they were established, and only
   ``OBSERVED_GIT`` supports a PASS. GOV-AUD-002 showed that accepting a caller's
   boolean for ancestry, tree equality or raw-diff safety lets a caller
   manufacture a PASS the evaluator never established. Facts come from
   ``snapshot.observe_proof_only_facts``; a claim stays visible as a claim.

The receipt enumerates every compared field and every conjunct's basis, so a
vacuous evaluation is visibly different from a genuine one. This module performs
no I/O: observation happens in ``snapshot``, judgement happens here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .models import (
    SCHEMA_PROOF_ONLY_EQUIVALENCE,
    STRUCTURAL_CONJUNCTS,
    Denial,
    FactBasis,
    NormalizedFailureClass,
    StructuralFacts,
    _require_git_oid,
    _require_keys,
    _require_mapping,
    _require_schema_version,
    _require_sequence,
    canonical_json,
    digest_of,
)

VALIDATOR_VERSION = "governed-delivery.equivalence.2"

CONTENT_DIGEST_EXCLUSION_DEFINITION = (
    "sha256 over the canonical JSON of sorted (path, 'mode type oid') pairs for "
    "every tracked entry NOT matching allowed_paths, at each head. Mode and type "
    "are included because a permission or symlink type change preserves the blob "
    "object id while altering what the file is"
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


# Basename-to-role table, derived from the file names the repository's proof
# tooling actually emits. Two properties matter and both are deliberate.
#
# Derivation from the path, not declaration: a role the caller could simply
# assert would be a relabelling channel, and an unlisted basename fails closed
# rather than defaulting to a permissive role.
#
# Injective, not grouped: each distinct document kind gets its own role. An
# earlier draft grouped AUDITOR_REPORT.md, AUDIT.md and AGY_AUDIT.md under one
# AUDIT_RESULT role on the theory that same-role documents are interchangeable
# carriers of one authority. They are not reliably interchangeable — a consumer
# that reads only AUDITOR_REPORT.md would not see an assertion moved into
# AUDIT.md — and that is GOV-AUD-001's own shape at finer grain. Architecture
# section 08 rules that genuinely ambiguous semantic status is classified as
# substantive, so grouping is refused. Splitting can only ever reject more; it
# cannot admit a change that grouping would have caught.
#
# Role is derived from basename, but comparison also binds exact path. Neither
# relocation nor rename is diagnostic-equivalent in G0.
_ROLE_BY_BASENAME: Mapping[str, str] = {
    "proof.json": "PROOF_BUNDLE",
    "proof-bundle.md": "PROOF_BUNDLE_NARRATIVE",
    "summary.md": "SUMMARY",
    "completion_report.md": "COMPLETION_REPORT",
    "auditor_report.md": "AUDITOR_REPORT",
    "auditor_repair_report.md": "AUDITOR_REPAIR_REPORT",
    "audit.md": "AUDIT_RESULT",
    "audit.json": "AUDIT_RESULT_JSON",
    "agy_audit.md": "AGY_AUDIT",
    "validation.json": "VALIDATION_RECEIPT",
    "validation.md": "VALIDATION_REPORT",
    "validation_output.md": "VALIDATION_OUTPUT",
    "implementer_report.md": "IMPLEMENTER_REPORT",
    "implementation-notes.md": "IMPLEMENTATION_NOTES",
    "handoff.md": "HANDOFF",
    "command_log.md": "COMMAND_LOG",
    "git_state.md": "GIT_STATE",
    "git_status_before.txt": "GIT_STATUS_BEFORE",
    "changed_files.txt": "CHANGED_FILES",
    "diff_stat.txt": "DIFF_STAT",
    "manifest.json": "MANIFEST",
    "run_manifest.json": "RUN_MANIFEST",
    "merge_readiness.json": "MERGE_READINESS",
}

# The closed set of authority classes a proof-only document can hold.
DOCUMENT_ROLES: tuple[str, ...] = tuple(sorted(set(_ROLE_BY_BASENAME.values())))

UNKNOWN_DOCUMENT_ROLE = "UNKNOWN"


def derive_document_role(path: str) -> str:
    """Derive a document's authority class from its path. Fails closed.

    Basename selects role; exact path remains a separate comparison key.
    """
    basename = str(path).replace("\\", "/").rsplit("/", 1)[-1].strip().lower()
    return _ROLE_BY_BASENAME.get(basename, UNKNOWN_DOCUMENT_ROLE)


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
    as a whole, so reordering a governance list is a change.
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

    ``documents`` maps exact path to parsed content. Path and derived role both
    enter comparison key, so all carrier movement fails closed.

    ``declared_roles`` is optional. When present it must agree with the derived
    role — a declaration can corroborate, never override.
    """

    documents: Mapping[str, Any] = field(default_factory=dict)
    declared_roles: Mapping[str, str] = field(default_factory=dict)

    def resolved_roles(self) -> dict[str, str]:
        return {path: derive_document_role(path) for path in sorted(self.documents)}

    def role_conflicts(self) -> list[str]:
        """Paths whose declared role contradicts the derived one."""
        derived = self.resolved_roles()
        return sorted(
            path
            for path, declared in self.declared_roles.items()
            if path in derived and declared != derived[path]
        )

    def unclassified_documents(self) -> list[str]:
        return sorted(
            path
            for path, role in self.resolved_roles().items()
            if role == UNKNOWN_DOCUMENT_ROLE
        )

    def aggregate_fields(self) -> dict[tuple[str, str, str], list[str]]:
        """Exact-path aggregate: ``(path, role, field)`` to sorted values.

        The key is a tuple, never a concatenated string. An earlier design
        disambiguated repeated names by synthesising a ``field#document`` key,
        but that separator lived in the same namespace as real field names and
        was therefore forgeable. A tuple has no textual namespace to collide
        with, so no crafted field name can construct one.

        Exact path remains part of key. Counting values across bundle or role
        let governance assertions move between carriers while totals stayed
        identical — GOV-AUD-001 and REPAIR-P3.
        """
        aggregate: dict[tuple[str, str, str], list[str]] = {}
        roles = self.resolved_roles()
        for path in sorted(self.documents):
            role = roles[path]
            for field_name, value in flatten(self.documents[path]).items():
                aggregate.setdefault((path, role, field_name), []).append(value)
        return {key: sorted(values) for key, values in aggregate.items()}


@dataclass(frozen=True)
class FieldComparison:
    document_path: str
    document_role: str
    field: str
    classification: str
    changed: bool
    outcome: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "document_path": self.document_path,
            "document_role": self.document_role,
            "field": self.field,
            "classification": self.classification,
            "changed": self.changed,
            "outcome": self.outcome,
        }


@dataclass(frozen=True)
class ConjunctResult:
    """One structural conjunct, whether it holds, and how it was established."""

    conjunct: str
    holds: bool
    basis: FactBasis
    detail: str = ""

    @property
    def supports_pass(self) -> bool:
        """Only an observed fact can carry a PASS. A claim never does."""
        return self.holds and self.basis is FactBasis.OBSERVED_GIT

    def as_dict(self) -> dict[str, Any]:
        return {
            "conjunct": self.conjunct,
            "holds": self.holds,
            "basis": self.basis.value,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class EquivalenceResult:
    equivalence_id: str
    passed: bool
    audited_head: str
    successor_head: str
    allowed_paths: Sequence[str]
    facts: StructuralFacts
    conjuncts: Sequence[ConjunctResult]
    compared_fields: Sequence[FieldComparison]
    failures: Sequence[Mapping[str, str]]

    def _conjunct(self, name: str) -> ConjunctResult | None:
        for item in self.conjuncts:
            if item.conjunct == name:
                return item
        return None

    def holds(self, name: str) -> bool:
        found = self._conjunct(name)
        return bool(found and found.holds)

    @property
    def structural_basis_all_observed(self) -> bool:
        return all(item.basis is FactBasis.OBSERVED_GIT for item in self.conjuncts)

    @property
    def mismatched_fields(self) -> list[str]:
        return sorted(
            {
                item.field
                for item in self.compared_fields
                if item.outcome == "GOVERNANCE_CHANGE_REJECTED"
            }
        )

    @property
    def unclassified_fields(self) -> list[str]:
        return sorted(
            {
                item.field
                for item in self.compared_fields
                if item.outcome == "UNCLASSIFIED_REJECTED"
            }
        )

    def as_dict(self) -> dict[str, Any]:
        outside = _paths_outside_allowlist(self.facts.actual_changed_paths, self.allowed_paths)
        body = {
            "schema_version": SCHEMA_PROOF_ONLY_EQUIVALENCE,
            "equivalence_id": self.equivalence_id,
            "result": "PASS" if self.passed else "FAIL",
            "diagnostic_only": True,
            "authority_effect": "NONE",
            "audit_reuse_authorized": False,
            "audited_head": self.audited_head,
            "successor_head": self.successor_head,
            "merge_base": self.facts.merge_base,
            "ancestry_established": self.facts.ancestry_established,
            "allowed_paths": list(self.allowed_paths),
            "actual_changed_paths": list(self.facts.actual_changed_paths),
            "non_allowed_diff_count": len(outside),
            "raw_diff_digest": self.facts.raw_diff_digest,
            "raw_diff_contains_no_substantive_source_change": self.holds(
                "raw_diff_contains_no_substantive_source_change"
            ),
            "content_digest_exclusion_definition": CONTENT_DIGEST_EXCLUSION_DEFINITION,
            "content_tree_equivalent_under_exclusion": self.facts.content_tree_equivalent_under_exclusion,
            "packet_and_policy_digests_unchanged": self.holds(
                "packet_and_policy_digests_unchanged"
            ),
            "audit_result_digest_unchanged": self.holds("audit_result_bytes_unchanged"),
            "structural_facts": [item.as_dict() for item in self.conjuncts],
            "structural_basis_all_observed": self.structural_basis_all_observed,
            "observer_version": self.facts.observer_version,
            "observation_digest": self.facts.observation_digest,
            "compared_fields": [item.as_dict() for item in self.compared_fields],
            "compared_field_count": len(self.compared_fields),
            "mismatched_fields": self.mismatched_fields,
            "unclassified_fields": self.unclassified_fields,
            "failures": [dict(item) for item in self.failures],
            "validator_version": VALIDATOR_VERSION,
        }
        body["receipt_digest"] = digest_of(body)
        return body

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> Mapping[str, Any]:
        """Strictly validate a diagnostic receipt without granting authority."""
        raw = _require_mapping(raw, "ProofOnlySuccessorEquivalence")
        allowed = (
            "schema_version",
            "equivalence_id",
            "result",
            "diagnostic_only",
            "authority_effect",
            "audit_reuse_authorized",
            "audited_head",
            "successor_head",
            "merge_base",
            "ancestry_established",
            "allowed_paths",
            "actual_changed_paths",
            "non_allowed_diff_count",
            "raw_diff_digest",
            "raw_diff_contains_no_substantive_source_change",
            "content_digest_exclusion_definition",
            "content_tree_equivalent_under_exclusion",
            "packet_and_policy_digests_unchanged",
            "audit_result_digest_unchanged",
            "structural_facts",
            "structural_basis_all_observed",
            "observer_version",
            "observation_digest",
            "compared_fields",
            "compared_field_count",
            "mismatched_fields",
            "unclassified_fields",
            "failures",
            "validator_version",
            "receipt_digest",
        )
        _require_keys(
            raw,
            required=allowed,
            allowed=allowed,
            contract="ProofOnlySuccessorEquivalence",
        )
        _require_schema_version(raw["schema_version"], SCHEMA_PROOF_ONLY_EQUIVALENCE)
        _require_git_oid(raw["audited_head"], "audited_head")
        _require_git_oid(raw["successor_head"], "successor_head")
        if raw["merge_base"] is not None:
            _require_git_oid(raw["merge_base"], "merge_base")
        if raw["diagnostic_only"] is not True:
            raise Denial(
                NormalizedFailureClass.SECURITY_OR_TRUST_INCIDENT,
                "equivalence must remain diagnostic_only",
            )
        if raw["authority_effect"] != "NONE" or raw["audit_reuse_authorized"] is not False:
            raise Denial(
                NormalizedFailureClass.SECURITY_OR_TRUST_INCIDENT,
                "G0 equivalence has no authority and cannot authorize audit reuse",
            )
        failures = _require_sequence(raw["failures"], "failures")
        if raw["result"] == "PASS":
            if failures or not raw["observer_version"] or not raw["observation_digest"]:
                raise Denial(
                    NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
                    "diagnostic PASS requires observation provenance and no failures",
                )
        elif raw["result"] != "FAIL" or not failures:
            raise Denial(
                NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
                "result must be PASS without failures or FAIL with failures",
            )
        body = dict(raw)
        receipt_digest = body.pop("receipt_digest")
        if receipt_digest != digest_of(body):
            raise Denial(
                NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
                "receipt_digest does not match canonical diagnostic receipt",
            )
        return raw


def _paths_outside_allowlist(paths: Iterable[str], allowed: Sequence[str]) -> list[str]:
    outside: list[str] = []
    for path in paths:
        if not any(fnmatch(path, pattern) for pattern in allowed):
            outside.append(path)
    return outside


def _weakest(*bases: FactBasis) -> FactBasis:
    """Combine bases for a derived conjunct: observed only if every input was."""
    if any(basis is FactBasis.UNKNOWN for basis in bases):
        return FactBasis.UNKNOWN
    if any(basis is FactBasis.CLAIMED_INPUT for basis in bases):
        return FactBasis.CLAIMED_INPUT
    return FactBasis.OBSERVED_GIT


def _digest_pair_unchanged(audited: str | None, successor: str | None) -> tuple[bool, str]:
    """Both digests must be present and equal.

    Absent-on-both is not "unchanged": it is an unmade comparison, and treating
    it as satisfied is the vacuity this evaluator exists to refuse.
    """
    if audited is None or successor is None:
        return False, "digest absent on at least one side; equality was never established"
    if audited != successor:
        return False, f"digest changed: {audited} -> {successor}"
    return True, "digests present and identical"


def _evaluate_conjuncts(
    facts: StructuralFacts, allowed_paths: Sequence[str]
) -> list[ConjunctResult]:
    """Evaluate the six structural conjuncts of architecture section 08."""
    outside = _paths_outside_allowlist(facts.actual_changed_paths, allowed_paths)
    paths_ok = not outside

    ancestry_basis = facts.basis_for(
        "current_head_descends_from_or_is_patch_equivalent_to_audited_head"
    )
    paths_basis = facts.basis_for("actual_changed_paths_subset_of_allowed_proof_only_paths")
    tree_basis = facts.basis_for("audited_content_tree_equal_under_exclusion")
    digest_basis = facts.basis_for("packet_and_policy_digests_unchanged")
    audit_basis = facts.basis_for("audit_result_bytes_unchanged")

    packet_ok, packet_detail = _digest_pair_unchanged(
        facts.audited_packet_digest, facts.successor_packet_digest
    )
    policy_ok, policy_detail = _digest_pair_unchanged(
        facts.audited_policy_digest, facts.successor_policy_digest
    )
    audit_ok, audit_detail = _digest_pair_unchanged(
        facts.audited_audit_result_digest, facts.successor_audit_result_digest
    )

    return [
        ConjunctResult(
            "current_head_descends_from_or_is_patch_equivalent_to_audited_head",
            facts.ancestry_established,
            ancestry_basis,
            f"merge_base={facts.merge_base}",
        ),
        ConjunctResult(
            "actual_changed_paths_subset_of_allowed_proof_only_paths",
            paths_ok,
            paths_basis,
            "all changed paths within allowlist"
            if paths_ok
            else f"outside allowlist: {', '.join(sorted(outside))}",
        ),
        # Derived, never attested: a raw diff that touches only allowed paths and
        # leaves every excluded byte identical cannot carry a source change.
        # GOV-AUD-002 removed the caller boolean that used to stand here.
        ConjunctResult(
            "raw_diff_contains_no_substantive_source_change",
            paths_ok and facts.content_tree_equivalent_under_exclusion,
            _weakest(paths_basis, tree_basis),
            "derived from path membership and tree equality under exclusion",
        ),
        ConjunctResult(
            "audited_content_tree_equal_under_exclusion",
            facts.content_tree_equivalent_under_exclusion,
            tree_basis,
            CONTENT_DIGEST_EXCLUSION_DEFINITION,
        ),
        ConjunctResult(
            "packet_and_policy_digests_unchanged",
            packet_ok and policy_ok,
            digest_basis,
            f"packet: {packet_detail}; policy: {policy_detail}",
        ),
        ConjunctResult(
            "audit_result_bytes_unchanged",
            audit_ok,
            audit_basis,
            audit_detail,
        ),
    ]


def evaluate_proof_only_equivalence(
    *,
    equivalence_id: str,
    audited_head: str,
    successor_head: str,
    audited_bundle: ProofOnlyBundle | None,
    successor_bundle: ProofOnlyBundle | None,
    allowed_paths: Sequence[str],
    facts: StructuralFacts,
) -> EquivalenceResult:
    """Prove, or refuse to prove, that a successor head is proof-only.

    Every applicable condition must hold *and* rest on an observed basis.
    Structural conjuncts (ancestry, path membership, tree equality under
    exclusion, frozen digests) are necessary; the role-scoped semantic
    comparison is what makes them sufficient.
    """
    failures: list[dict[str, str]] = []

    _require_git_oid(audited_head, "audited_head")
    _require_git_oid(successor_head, "successor_head")

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

    conjuncts = _evaluate_conjuncts(facts, allowed_paths)
    for item in conjuncts:
        if not item.holds:
            failures.append(
                {"code": f"conjunct_failed:{item.conjunct}", "detail": item.detail}
            )
        elif item.basis is not FactBasis.OBSERVED_GIT:
            # GOV-AUD-002: the conjunct may well be true, but nothing here
            # established it. A caller's word is not a proof of equivalence.
            failures.append(
                {
                    "code": f"conjunct_not_observed:{item.conjunct}",
                    "detail": f"basis is {item.basis.value}; only OBSERVED_GIT supports a PASS",
                }
            )

    if facts.absent_named_paths:
        failures.append(
            {
                "code": "named_digest_path_absent",
                "detail": "named digest paths missing at one or both heads: "
                + ", ".join(sorted(facts.absent_named_paths)),
            }
        )

    if not facts.raw_diff_digest:
        failures.append(
            {
                "code": "missing_raw_diff_digest",
                "detail": "no raw diff digest was recorded; the diff cannot be re-checked later",
            }
        )

    for side, bundle in (("audited", audited_bundle), ("successor", successor_bundle)):
        if bundle is None:
            continue
        unclassified = bundle.unclassified_documents()
        if unclassified:
            failures.append(
                {
                    "code": "unclassified_document_role",
                    "detail": f"{side} bundle has documents with no known authority class: "
                    + ", ".join(unclassified),
                }
            )
        conflicts = bundle.role_conflicts()
        if conflicts:
            failures.append(
                {
                    "code": "document_role_declaration_conflict",
                    "detail": f"{side} bundle declares a role contradicting the path-derived one: "
                    + ", ".join(conflicts),
                }
            )

    comparisons: list[FieldComparison] = []
    if audited_bundle is not None and successor_bundle is not None:
        before = audited_bundle.aggregate_fields()
        after = successor_bundle.aggregate_fields()

        for path, role, name in sorted(set(before) | set(after)):
            old = before.get((path, role, name), [])
            new = after.get((path, role, name), [])
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

            comparisons.append(
                FieldComparison(path, role, name, classification, changed, outcome)
            )

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
                + ", ".join(
                    sorted(
                        f"{item.document_path}:{item.document_role}/{item.field}"
                        for item in rejected
                    )
                ),
            }
        )

    unclassified_fields = [item for item in comparisons if item.outcome == "UNCLASSIFIED_REJECTED"]
    if unclassified_fields:
        failures.append(
            {
                "code": "unclassified_semantic_field",
                "detail": "unclassifiable fields treated as governance-relevant: "
                + ", ".join(
                    sorted(
                        f"{item.document_path}:{item.document_role}/{item.field}"
                        for item in unclassified_fields
                    )
                ),
            }
        )

    if set(item.conjunct for item in conjuncts) != set(STRUCTURAL_CONJUNCTS):
        raise Denial(
            NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
            "structural conjunct set does not match the declared architecture predicate",
        )

    return EquivalenceResult(
        equivalence_id=equivalence_id,
        passed=not failures,
        audited_head=audited_head,
        successor_head=successor_head,
        allowed_paths=list(allowed_paths),
        facts=facts,
        conjuncts=conjuncts,
        compared_fields=comparisons,
        failures=failures,
    )


def evaluate_observed_proof_only_equivalence(
    *,
    repo_root: Path,
    equivalence_id: str,
    audited_head: str,
    successor_head: str,
    audited_bundle: ProofOnlyBundle | None,
    successor_bundle: ProofOnlyBundle | None,
    allowed_paths: Sequence[str],
    packet_path: str | None = None,
    policy_path: str | None = None,
    audit_result_path: str | None = None,
) -> EquivalenceResult:
    """Observe local Git facts, then return non-authoritative diagnostic result.

    Caller cannot supply PASS-bearing structural facts through this public path.
    Result always retains ``authority_effect=NONE`` and
    ``audit_reuse_authorized=false`` when serialized.
    """
    from .snapshot import observe_proof_only_facts

    facts = observe_proof_only_facts(
        repo_root,
        audited_head=audited_head,
        successor_head=successor_head,
        allowed_paths=allowed_paths,
        packet_path=packet_path,
        policy_path=policy_path,
        audit_result_path=audit_result_path,
    )
    return evaluate_proof_only_equivalence(
        equivalence_id=equivalence_id,
        audited_head=audited_head,
        successor_head=successor_head,
        audited_bundle=audited_bundle,
        successor_bundle=successor_bundle,
        allowed_paths=allowed_paths,
        facts=facts,
    )
