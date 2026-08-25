"""GOV-AUD-F1 / GOV-AUD-001 / GOV-AUD-002 adversarial suite for proof-only equivalence.

The independent architecture audit's original finding is that a path-membership
predicate cannot see a semantic change made *inside* an allowed proof-only path.
The follow-up audit found two survivors of the first repair: an assertion could
still be laundered *between documents* of different authority, and every
structural conjunct could be satisfied by a caller simply asserting it.

Each negative fixture below performs exactly one of those laundering attempts
and must fail closed; each positive fixture is a genuinely inert change and must
pass.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

from dopemux.governed_delivery.equivalence import (
    UNKNOWN_DOCUMENT_ROLE,
    FieldClassification,
    ProofOnlyBundle,
    classify_field,
    derive_document_role,
    evaluate_proof_only_equivalence,
    evaluate_observed_proof_only_equivalence,
    flatten,
)
from dopemux.governed_delivery.models import FactBasis, STRUCTURAL_CONJUNCTS, StructuralFacts
from dopemux.governed_delivery.snapshot import observe_proof_only_facts, run_git_read

SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas" / "governed_delivery"

PROOF_PATH = "proof/TP-X/PROOF.json"
SUMMARY_PATH = "proof/TP-X/SUMMARY.md"
AUDIT_PATH = "proof/TP-X/AUDITOR_REPORT.md"

AUDITED_DOC = {
    "audit_verdict": "PASS_WITH_RISKS",
    "auditor_identity": "claude-fable-5",
    "auditor_provider_attested_identity": "UNKNOWN",
    "independence": "LIMITED",
    "known_risks": ["GOV-AUD-F1", "GOV-AUD-F2", "GOV-AUD-F3"],
    "unknowns": ["provider attestation UNKNOWN"],
    "blocking_findings": [],
    "conflicts": [],
    "authority_statements": ["merge not authorized"],
    "scope_statements": ["G0 read-only"],
    "acceptance_criteria": ["all gates PASS"],
    "operator_decision_refs": [],
    "content_head": "a" * 40,
    "audited_head": "a" * 40,
    "tree_digest": "sha256:tree",
    "validation_claims": {"pytest": "PASS", "ruff": "PASS"},
    "test_claims": {"focused": "PASS"},
    "security_claims": {"secret_scan": "NO_REAL_SECRETS"},
    "merge_readiness_claims": {"pr_steward": "NOT_RUN"},
    "activation_claims": {"activated": False},
    "evidence_refs": ["ev-1", "ev-2"],
    # Genuinely inert packaging metadata.
    "checksum": "deadbeef",
    "generated_at": "2026-08-24T00:00:00Z",
    "generator_version": "1.0.0",
}


def observed(**overrides) -> StructuralFacts:
    """Structural facts as the git observer would report them: all OBSERVED_GIT.

    Test scaffolding only. The observer itself is exercised against a real
    repository in :class:`TestGitObserver`; these fixtures isolate the evaluator.
    """
    values = dict(
        ancestry_established=True,
        actual_changed_paths=[SUMMARY_PATH],
        raw_diff_digest="sha256:rawdiff",
        content_tree_equivalent_under_exclusion=True,
        audited_packet_digest="sha256:packet",
        successor_packet_digest="sha256:packet",
        audited_policy_digest="sha256:policy",
        successor_policy_digest="sha256:policy",
        audited_audit_result_digest="sha256:audit",
        successor_audit_result_digest="sha256:audit",
        merge_base="a" * 40,
        observer_version="governed-delivery.git-observer.1",
        observation_digest="sha256:observation",
    )
    values.update(overrides)
    return StructuralFacts._from_git_observer(
        **values, basis={name: FactBasis.OBSERVED_GIT for name in STRUCTURAL_CONJUNCTS}
    )


BASE_ARGS = dict(
    equivalence_id="eq-test",
    audited_head="a" * 40,
    successor_head="b" * 40,
    allowed_paths=["proof/**"],
)


def evaluate(successor_doc, audited_doc=None, *, facts=None, **overrides):
    """Compare one audited PROOF.json against one successor PROOF.json."""
    args = dict(BASE_ARGS)
    args.update(overrides)
    args["audited_bundle"] = ProofOnlyBundle({PROOF_PATH: audited_doc or dict(AUDITED_DOC)})
    args["successor_bundle"] = ProofOnlyBundle({PROOF_PATH: successor_doc})
    args["facts"] = facts if facts is not None else observed()
    return evaluate_proof_only_equivalence(**args)


def mutated(**changes):
    doc = dict(AUDITED_DOC)
    doc.update(changes)
    return doc


def codes(result) -> set[str]:
    return {failure["code"] for failure in result.failures}


class TestF1NegativeFixtures:
    """Every one of these is a governance change hidden inside an allowed path."""

    def test_known_risk_removed(self):
        result = evaluate(mutated(known_risks=["GOV-AUD-F1", "GOV-AUD-F2"]))
        assert not result.passed
        assert "known_risks" in result.mismatched_fields

    def test_blocking_finding_removed(self):
        audited = mutated(blocking_findings=["BLOCKER-1"])
        result = evaluate(dict(AUDITED_DOC), audited_doc=audited)
        assert not result.passed
        assert "blocking_findings" in result.mismatched_fields

    def test_audit_verdict_changed(self):
        result = evaluate(mutated(audit_verdict="PASS"))
        assert not result.passed
        assert "audit_verdict" in result.mismatched_fields

    def test_auditor_identity_changed(self):
        result = evaluate(mutated(auditor_identity="some-other-model"))
        assert not result.passed
        assert "auditor_identity" in result.mismatched_fields

    def test_authority_statement_changed(self):
        result = evaluate(mutated(authority_statements=["merge authorized"]))
        assert not result.passed
        assert "authority_statements" in result.mismatched_fields

    def test_content_head_changed(self):
        result = evaluate(mutated(content_head="c" * 40))
        assert not result.passed
        assert "content_head" in result.mismatched_fields

    def test_validation_claim_changed(self):
        result = evaluate(mutated(validation_claims={"pytest": "NOT_RUN", "ruff": "PASS"}))
        assert not result.passed
        assert any("validation_claims" in name for name in result.mismatched_fields)

    def test_unknown_changed_to_proven(self):
        result = evaluate(mutated(unknowns=[]))
        assert not result.passed
        assert "unknowns" in result.mismatched_fields

    def test_empty_semantic_field_set(self):
        args = dict(BASE_ARGS)
        args["audited_bundle"] = ProofOnlyBundle({})
        args["successor_bundle"] = ProofOnlyBundle({})
        args["facts"] = observed()
        result = evaluate_proof_only_equivalence(**args)
        assert not result.passed
        assert "empty_semantic_field_set" in codes(result)

    def test_missing_original_bundle(self):
        args = dict(BASE_ARGS)
        args["audited_bundle"] = None
        args["successor_bundle"] = ProofOnlyBundle({PROOF_PATH: dict(AUDITED_DOC)})
        args["facts"] = observed()
        result = evaluate_proof_only_equivalence(**args)
        assert not result.passed
        assert "missing_original_bundle" in codes(result)

    def test_independence_downgraded(self):
        result = evaluate(mutated(independence="FULL"))
        assert not result.passed

    def test_evidence_ref_list_weakened(self):
        result = evaluate(mutated(evidence_refs=["ev-1"]))
        assert not result.passed
        assert "evidence_refs" in result.mismatched_fields

    def test_security_claim_changed(self):
        result = evaluate(mutated(security_claims={"secret_scan": "NOT_RUN"}))
        assert not result.passed

    def test_acceptance_criteria_changed(self):
        result = evaluate(mutated(acceptance_criteria=["most gates PASS"]))
        assert not result.passed
        assert "acceptance_criteria" in result.mismatched_fields


class TestAggregateForgery:
    """A synthesised comparison key must not share a namespace with real names."""

    AUDITED = {PROOF_PATH: {"known_risks": ["R1"]}, SUMMARY_PATH: {"known_risks": ["R2"]}}

    def _evaluate(self, successor, audited=None):
        args = dict(BASE_ARGS)
        args["audited_bundle"] = ProofOnlyBundle(audited or self.AUDITED)
        args["successor_bundle"] = ProofOnlyBundle(successor)
        args["facts"] = observed()
        return evaluate_proof_only_equivalence(**args)

    def test_crafted_separator_key_cannot_restore_the_aggregate(self):
        forged = {
            PROOF_PATH: {"known_risks": ["R1"], "known_risks#SUMMARY": ["R2"]},
            SUMMARY_PATH: {"known_risks": ["R1"]},
        }
        result = self._evaluate(forged)
        assert not result.passed
        assert "known_risks" in result.mismatched_fields

    def test_crafted_separator_with_arbitrary_suffix_also_rejected(self):
        forged = {
            PROOF_PATH: {"known_risks": ["R1"], "known_risks#ANYTHING": ["R2"]},
            SUMMARY_PATH: {"known_risks": ["R1"]},
        }
        assert not self._evaluate(forged).passed

    def test_value_dropped_from_one_of_several_documents_is_rejected(self):
        assert not self._evaluate(
            {PROOF_PATH: {"known_risks": ["R1"]}, SUMMARY_PATH: {}}
        ).passed

    def test_aggregate_is_keyed_by_path_role_and_field(self):
        """The key is a tuple, so no field name can ever collide with it."""
        aggregate = ProofOnlyBundle({PROOF_PATH: {"known_risks": ["R1"]}}).aggregate_fields()
        assert list(aggregate) == [(PROOF_PATH, "PROOF_BUNDLE", "known_risks")]
        assert all(isinstance(key, tuple) and len(key) == 3 for key in aggregate)

    def test_aggregate_counts_repeated_values_within_one_role(self):
        """Two documents of one role asserting the same value is not the same as one.

        Same role means same basename in different directories, which is exactly
        what a legitimate relocation produces.
        """
        one = ProofOnlyBundle({AUDIT_PATH: {"known_risks": ["R1"]}}).aggregate_fields()
        two = ProofOnlyBundle(
            {
                AUDIT_PATH: {"known_risks": ["R1"]},
                "proof/TP-Y/AUDITOR_REPORT.md": {"known_risks": ["R1"]},
            }
        ).aggregate_fields()
        assert one != two
        assert all(role == "AUDITOR_REPORT" for _, role, _ in two)

    def test_swapping_between_two_documents_of_the_same_role_is_visible_as_a_drop(self):
        """The one remaining same-role case: identical basenames in two directories.

        Their multisets merge, so a swap is invisible — but a DROP is not, which
        is the property that matters. Recorded explicitly rather than left implicit.
        """
        audited = ProofOnlyBundle(
            {
                "proof/A/AUDITOR_REPORT.md": {"known_risks": ["R1"]},
                "proof/B/AUDITOR_REPORT.md": {"known_risks": ["R2"]},
            }
        )
        dropped = ProofOnlyBundle(
            {
                "proof/A/AUDITOR_REPORT.md": {"known_risks": ["R1"]},
                "proof/B/AUDITOR_REPORT.md": {"known_risks": ["R1"]},
            }
        )
        assert audited.aggregate_fields() != dropped.aggregate_fields()


class TestCrossRoleLaundering:
    """GOV-AUD-001: an assertion must stay in the document class that carries it.

    The previous implementation compared a bundle-wide aggregate, so a risk could
    be removed from the document the operator and PR Steward actually read and
    re-encoded in one with no authority. The totals matched and it passed. Each
    fixture here is that move, and each must now fail.
    """

    AUDITED = {
        AUDIT_PATH: {"known_risks": ["R1", "R2"], "audit_verdict": "PASS_WITH_RISKS"},
        SUMMARY_PATH: {"known_risks": [], "audit_verdict": "PASS_WITH_RISKS"},
    }

    def _evaluate(self, successor):
        args = dict(BASE_ARGS)
        args["audited_bundle"] = ProofOnlyBundle(self.AUDITED)
        args["successor_bundle"] = ProofOnlyBundle(successor)
        args["facts"] = observed()
        return evaluate_proof_only_equivalence(**args)

    def test_risk_moved_from_audit_result_to_summary_is_rejected(self):
        laundered = {
            AUDIT_PATH: {"known_risks": ["R1"], "audit_verdict": "PASS_WITH_RISKS"},
            SUMMARY_PATH: {"known_risks": ["R2"], "audit_verdict": "PASS_WITH_RISKS"},
        }
        result = self._evaluate(laundered)
        assert not result.passed
        assert "known_risks" in result.mismatched_fields

    def test_swapping_values_between_roles_is_rejected(self):
        """The bundle-wide multiset is identical; the per-role multisets are not."""
        swapped = {
            AUDIT_PATH: {"known_risks": [], "audit_verdict": "PASS_WITH_RISKS"},
            SUMMARY_PATH: {"known_risks": ["R1", "R2"], "audit_verdict": "PASS_WITH_RISKS"},
        }
        result = self._evaluate(swapped)
        assert not result.passed
        assert "known_risks" in result.mismatched_fields

    def test_verdict_moved_out_of_the_audit_result_is_rejected(self):
        laundered = {
            AUDIT_PATH: {"known_risks": ["R1", "R2"]},
            SUMMARY_PATH: {
                "known_risks": [],
                "audit_verdict": "PASS_WITH_RISKS",
                "audit_verdict_copy": "PASS_WITH_RISKS",
            },
        }
        assert not self._evaluate(laundered).passed

    def test_relocation_within_the_same_role_fails_closed(self):
        """Path identity is part of diagnostic comparison; relocation is substantive."""
        relocated = {
            "proof/TP-X-renamed/AUDITOR_REPORT.md": {
                "known_risks": ["R1", "R2"],
                "audit_verdict": "PASS_WITH_RISKS",
            },
            "proof/TP-X-renamed/SUMMARY.md": {
                "known_risks": [],
                "audit_verdict": "PASS_WITH_RISKS",
            },
        }
        result = self._evaluate(relocated)
        assert not result.passed

    def test_document_with_no_known_role_fails_closed(self):
        args = dict(BASE_ARGS)
        args["audited_bundle"] = ProofOnlyBundle({"proof/TP-X/mystery.txt": {"known_risks": []}})
        args["successor_bundle"] = ProofOnlyBundle({"proof/TP-X/mystery.txt": {"known_risks": []}})
        args["facts"] = observed()
        result = evaluate_proof_only_equivalence(**args)
        assert not result.passed
        assert "unclassified_document_role" in codes(result)

    def test_declared_role_cannot_override_the_path_derived_one(self):
        """A role the caller could simply declare would be a relabelling channel."""
        args = dict(BASE_ARGS)
        args["audited_bundle"] = ProofOnlyBundle(self.AUDITED)
        args["successor_bundle"] = ProofOnlyBundle(
            self.AUDITED, {SUMMARY_PATH: "AUDIT_RESULT"}
        )
        args["facts"] = observed()
        result = evaluate_proof_only_equivalence(**args)
        assert not result.passed
        assert "document_role_declaration_conflict" in codes(result)


class TestDocumentRoleDerivation:
    @pytest.mark.parametrize(
        "path,role",
        [
            ("proof/TP-X/PROOF.json", "PROOF_BUNDLE"),
            ("proof/deeply/nested/PROOF.json", "PROOF_BUNDLE"),
            ("proof/TP-X/SUMMARY.md", "SUMMARY"),
            ("proof/TP-X/AUDITOR_REPORT.md", "AUDITOR_REPORT"),
            ("proof/TP-X/AUDIT.md", "AUDIT_RESULT"),
            ("proof/TP-X/VALIDATION.json", "VALIDATION_RECEIPT"),
            ("proof/TP-X/COMMAND_LOG.md", "COMMAND_LOG"),
            ("proof/TP-X/CHANGED_FILES.txt", "CHANGED_FILES"),
        ],
    )
    def test_role_is_derived_from_the_basename(self, path, role):
        assert derive_document_role(path) == role

    def test_the_role_table_is_injective(self):
        """One role per document kind.

        Grouping several basenames under one role would let an assertion move
        between them unseen — GOV-AUD-001's shape at finer grain.
        """
        from dopemux.governed_delivery.equivalence import (
            DOCUMENT_ROLES,
            _ROLE_BY_BASENAME,
        )

        assert len(DOCUMENT_ROLES) == len(_ROLE_BY_BASENAME)
        assert len(set(_ROLE_BY_BASENAME.values())) == len(_ROLE_BY_BASENAME)

    def test_differently_named_audit_documents_do_not_share_a_role(self):
        names = ["AUDITOR_REPORT.md", "AUDIT.md", "AGY_AUDIT.md", "AUDITOR_REPAIR_REPORT.md"]
        roles = [derive_document_role(f"proof/TP-X/{name}") for name in names]
        assert len(set(roles)) == len(names)
        assert UNKNOWN_DOCUMENT_ROLE not in roles

    def test_relocation_preserves_the_role(self):
        assert derive_document_role("proof/a/PROOF.json") == derive_document_role(
            "proof/b/c/PROOF.json"
        )

    def test_unlisted_basename_is_unknown(self):
        assert derive_document_role("proof/TP-X/notes.txt") == "UNKNOWN"

    def test_case_and_separator_are_normalized(self):
        assert derive_document_role("proof\\TP-X\\proof.JSON") == "PROOF_BUNDLE"


class TestDottedKeyNamespace:
    """A literal dotted key and real nesting flatten to the same path.

    That shared namespace is the same shape as the `#` forgery, so it is probed
    directly. It turns out not to be exploitable: `flatten` builds a dict, so a
    literal `a.b` key and a nested `{"a": {"b": ...}}` collapse to ONE entry
    within a document, which means a crafted key cannot inflate a value's count
    to disguise a drop elsewhere.
    """

    def _evaluate(self, audited, successor):
        args = dict(BASE_ARGS)
        args["audited_bundle"] = ProofOnlyBundle(audited)
        args["successor_bundle"] = ProofOnlyBundle(successor)
        args["facts"] = observed()
        return evaluate_proof_only_equivalence(**args)

    def test_literal_dotted_key_and_nesting_collide_to_one_entry(self):
        assert flatten({"audit": {"verdict": "PASS"}}) == flatten({"audit.verdict": "PASS"})

    def test_dotted_key_cannot_change_a_governance_value(self):
        result = self._evaluate(
            {PROOF_PATH: {"audit": {"verdict": "PASS_WITH_RISKS"}}},
            {PROOF_PATH: {"audit.verdict": "PASS"}},
        )
        assert not result.passed
        assert "audit.verdict" in result.mismatched_fields

    def test_dotted_key_cannot_inflate_a_count_to_disguise_a_drop(self):
        """One document drops its assertion; a crafted literal key cannot restore it."""
        audited = {
            AUDIT_PATH: {"audit": {"verdict": "PASS_WITH_RISKS"}},
            "proof/TP-X/AUDIT.md": {"audit": {"verdict": "PASS_WITH_RISKS"}},
        }
        forged = {
            AUDIT_PATH: {
                "audit.verdict": "PASS_WITH_RISKS",
                "audit": {"verdict": "PASS_WITH_RISKS"},
            },
            "proof/TP-X/AUDIT.md": {},
        }
        assert not self._evaluate(audited, forged).passed

    def test_pure_reencoding_preserving_every_assertion_passes(self):
        """Semantically neutral: the same assertions, differently encoded."""
        result = self._evaluate(
            {PROOF_PATH: {"audit": {"verdict": "PASS_WITH_RISKS", "risks": ["R1"]}}},
            {PROOF_PATH: {"audit.verdict": "PASS_WITH_RISKS", "audit": {"risks": ["R1"]}}},
        )
        assert result.passed, result.failures


class TestClaimedFactsCannotPass:
    """GOV-AUD-002: a caller's word is not evidence of equivalence."""

    def _claimed(self, **overrides):
        values = dict(
            ancestry_established=True,
            actual_changed_paths=[SUMMARY_PATH],
            raw_diff_digest="sha256:rawdiff",
            content_tree_equivalent_under_exclusion=True,
            audited_packet_digest="sha256:packet",
            successor_packet_digest="sha256:packet",
            audited_policy_digest="sha256:policy",
            successor_policy_digest="sha256:policy",
            audited_audit_result_digest="sha256:audit",
            successor_audit_result_digest="sha256:audit",
        )
        values.update(overrides)
        return StructuralFacts.claimed(**values)

    def test_every_structural_claim_true_still_fails(self):
        """The identical bundle and every conjunct asserted true: still not a PASS."""
        result = evaluate(dict(AUDITED_DOC), facts=self._claimed())
        assert not result.passed
        assert any(code.startswith("conjunct_not_observed:") for code in codes(result))

    def test_each_conjunct_is_individually_reported_as_unobserved(self):
        result = evaluate(dict(AUDITED_DOC), facts=self._claimed())
        unobserved = {
            code.split(":", 1)[1]
            for code in codes(result)
            if code.startswith("conjunct_not_observed:")
        }
        assert unobserved == set(STRUCTURAL_CONJUNCTS)

    def test_unknown_basis_also_fails(self):
        bare = StructuralFacts(
            ancestry_established=True,
            actual_changed_paths=[SUMMARY_PATH],
            raw_diff_digest="sha256:rawdiff",
            content_tree_equivalent_under_exclusion=True,
            audited_packet_digest="sha256:p",
            successor_packet_digest="sha256:p",
            audited_policy_digest="sha256:q",
            successor_policy_digest="sha256:q",
            audited_audit_result_digest="sha256:a",
            successor_audit_result_digest="sha256:a",
        )
        result = evaluate(dict(AUDITED_DOC), facts=bare)
        assert not result.passed
        assert not result.structural_basis_all_observed

    def test_receipt_records_the_basis_of_every_conjunct(self):
        result = evaluate(dict(AUDITED_DOC), facts=self._claimed())
        recorded = {item["conjunct"]: item["basis"] for item in result.as_dict()["structural_facts"]}
        assert set(recorded) == set(STRUCTURAL_CONJUNCTS)
        assert set(recorded.values()) == {"CLAIMED_INPUT"}

    def test_claimed_receipt_is_schema_valid_and_reports_fail(self):
        payload = evaluate(dict(AUDITED_DOC), facts=self._claimed()).as_dict()
        schema = json.loads(
            (SCHEMA_DIR / "proof-only-successor-equivalence.schema.json").read_text()
        )
        Draft7Validator(schema).validate(payload)
        assert payload["result"] == "FAIL"
        assert payload["structural_basis_all_observed"] is False

    def test_unknown_basis_key_is_denied(self):
        with pytest.raises(Exception):
            StructuralFacts(basis={"not_a_conjunct": FactBasis.OBSERVED_GIT})


class TestStructuralConjuncts:
    def test_path_outside_allowlist_rejected(self):
        result = evaluate(
            dict(AUDITED_DOC),
            facts=observed(actual_changed_paths=["src/dopemux/thing.py"]),
        )
        assert not result.passed
        assert (
            "conjunct_failed:actual_changed_paths_subset_of_allowed_proof_only_paths"
            in codes(result)
        )
        assert result.as_dict()["non_allowed_diff_count"] == 1

    def test_ancestry_not_established_rejected(self):
        result = evaluate(dict(AUDITED_DOC), facts=observed(ancestry_established=False))
        assert not result.passed
        assert (
            "conjunct_failed:current_head_descends_from_or_is_patch_equivalent_to_audited_head"
            in codes(result)
        )

    def test_tree_not_equivalent_under_exclusion_rejected(self):
        result = evaluate(
            dict(AUDITED_DOC), facts=observed(content_tree_equivalent_under_exclusion=False)
        )
        assert not result.passed
        assert "conjunct_failed:audited_content_tree_equal_under_exclusion" in codes(result)

    def test_raw_diff_safety_is_derived_from_the_other_two_conjuncts(self):
        """It is no longer attestable, so breaking either input must break it."""
        result = evaluate(
            dict(AUDITED_DOC), facts=observed(content_tree_equivalent_under_exclusion=False)
        )
        assert "conjunct_failed:raw_diff_contains_no_substantive_source_change" in codes(result)

    def test_packet_digest_change_rejected(self):
        result = evaluate(
            dict(AUDITED_DOC), facts=observed(successor_packet_digest="sha256:different")
        )
        assert not result.passed
        assert "conjunct_failed:packet_and_policy_digests_unchanged" in codes(result)

    def test_policy_digest_change_rejected(self):
        result = evaluate(
            dict(AUDITED_DOC), facts=observed(successor_policy_digest="sha256:different")
        )
        assert not result.passed

    def test_audit_result_digest_change_rejected(self):
        result = evaluate(
            dict(AUDITED_DOC), facts=observed(successor_audit_result_digest="sha256:different")
        )
        assert not result.passed
        assert "conjunct_failed:audit_result_bytes_unchanged" in codes(result)

    def test_absent_digest_on_both_sides_is_not_unchanged(self):
        """An unmade comparison must never read as a satisfied one."""
        result = evaluate(
            dict(AUDITED_DOC),
            facts=observed(audited_packet_digest=None, successor_packet_digest=None),
        )
        assert not result.passed
        assert "conjunct_failed:packet_and_policy_digests_unchanged" in codes(result)

    def test_named_path_absent_at_a_head_is_reported(self):
        result = evaluate(
            dict(AUDITED_DOC), facts=observed(absent_named_paths=["task-packets/TP-X.json@audited"])
        )
        assert not result.passed
        assert "named_digest_path_absent" in codes(result)

    def test_missing_raw_diff_digest_rejected(self):
        result = evaluate(dict(AUDITED_DOC), facts=observed(raw_diff_digest=""))
        assert not result.passed
        assert "missing_raw_diff_digest" in codes(result)

    def test_all_eight_architecture_conjuncts_are_accounted_for(self):
        """Six observed conjuncts, plus the semantic comparison and the conjunction."""
        result = evaluate(dict(AUDITED_DOC))
        assert [item.conjunct for item in result.conjuncts] == [
            "current_head_descends_from_or_is_patch_equivalent_to_audited_head",
            "actual_changed_paths_subset_of_allowed_proof_only_paths",
            "raw_diff_contains_no_substantive_source_change",
            "audited_content_tree_equal_under_exclusion",
            "packet_and_policy_digests_unchanged",
            "audit_result_bytes_unchanged",
        ]
        assert result.compared_fields  # the seventh conjunct
        assert result.passed is (not result.failures)  # the eighth


class TestPositiveFixtures:
    def test_checksum_only_change(self):
        result = evaluate(mutated(checksum="cafebabe"))
        assert result.passed, result.failures

    def test_formatting_only_generated_metadata_change(self):
        result = evaluate(
            mutated(generated_at="2026-08-25T12:00:00Z", generator_version="1.0.1")
        )
        assert result.passed, result.failures

    def test_proof_reference_relocation_with_byte_identity_fails_closed(self):
        """Exact document path prevents same-basename carrier swaps."""
        args = dict(BASE_ARGS)
        args["audited_bundle"] = ProofOnlyBundle({PROOF_PATH: dict(AUDITED_DOC)})
        args["successor_bundle"] = ProofOnlyBundle(
            {"proof/relocated/PROOF.json": dict(AUDITED_DOC)}
        )
        args["facts"] = observed()
        result = evaluate_proof_only_equivalence(**args)
        assert not result.passed

    def test_identical_bundle_passes(self):
        result = evaluate(dict(AUDITED_DOC))
        assert result.passed, result.failures


class TestAntiVacuity:
    def test_positive_result_compared_a_nonzero_field_set(self):
        result = evaluate(dict(AUDITED_DOC))
        assert result.passed
        assert len(result.compared_fields) > 20

    def test_every_compared_field_is_enumerated_with_an_outcome(self):
        payload = evaluate(mutated(checksum="cafebabe")).as_dict()
        assert payload["compared_field_count"] == len(payload["compared_fields"])
        for item in payload["compared_fields"]:
            assert item["outcome"] in {
                "UNCHANGED",
                "INERT_CHANGE_ALLOWED",
                "GOVERNANCE_CHANGE_REJECTED",
                "UNCLASSIFIED_REJECTED",
            }
            assert item["document_role"] == "PROOF_BUNDLE"

    def test_unclassified_field_fails_closed(self):
        result = evaluate(mutated(mystery_attribute="whatever"))
        assert not result.passed
        assert "mystery_attribute" in result.unclassified_fields

    def test_receipt_records_raw_diff_digest(self):
        assert evaluate(dict(AUDITED_DOC)).as_dict()["raw_diff_digest"] == "sha256:rawdiff"

    def test_receipt_validates_against_schema(self):
        payload = evaluate(dict(AUDITED_DOC)).as_dict()
        schema = json.loads(
            (SCHEMA_DIR / "proof-only-successor-equivalence.schema.json").read_text()
        )
        Draft7Validator(schema).validate(payload)
        assert payload["result"] == "PASS"

    def test_failing_receipt_lists_failures(self):
        payload = evaluate(mutated(known_risks=[])).as_dict()
        schema = json.loads(
            (SCHEMA_DIR / "proof-only-successor-equivalence.schema.json").read_text()
        )
        Draft7Validator(schema).validate(payload)
        assert payload["result"] == "FAIL"
        assert payload["failures"]


class TestFieldClassification:
    @pytest.mark.parametrize(
        "field_name",
        ["audit_verdict", "known_risks", "blocking_findings", "merge_readiness", "tree_digest"],
    )
    def test_governance_fields_classified(self, field_name):
        assert classify_field(field_name) == FieldClassification.GOVERNANCE_RELEVANT

    @pytest.mark.parametrize("field_name", ["checksum", "generated_at", "generator_version"])
    def test_inert_fields_classified(self, field_name):
        assert classify_field(field_name) == FieldClassification.INERT

    def test_compound_name_with_governance_token_beats_inert_leaf(self):
        assert classify_field("audit_result_checksum") == FieldClassification.GOVERNANCE_RELEVANT

    def test_unrecognized_field_is_unknown(self):
        assert classify_field("nonsense_attribute") == FieldClassification.UNKNOWN

    def test_empty_field_is_unknown(self):
        assert classify_field("   ") == FieldClassification.UNKNOWN


class TestFlatten:
    def test_nested_mapping_flattens_to_dotted_paths(self):
        assert flatten({"a": {"b": 1}}) == {"a.b": "1"}

    def test_list_is_canonicalized_as_a_whole(self):
        assert flatten({"a": [1, 2]}) == {"a": "[1,2]"}

    def test_list_reordering_is_a_change(self):
        assert flatten({"a": [1, 2]}) != flatten({"a": [2, 1]})


class TestR2DiagnosticOnlyEquivalence:
    def _same_basename_swap(self, field):
        left = "proof/a/SUMMARY.md"
        right = "proof/b/SUMMARY.md"
        args = dict(BASE_ARGS)
        args["audited_bundle"] = ProofOnlyBundle(
            {left: {field: ["A"]}, right: {field: ["B"]}}
        )
        args["successor_bundle"] = ProofOnlyBundle(
            {left: {field: ["B"]}, right: {field: ["A"]}}
        )
        args["facts"] = observed(actual_changed_paths=[left, right])
        return evaluate_proof_only_equivalence(**args)

    def test_same_basename_cross_directory_risk_swap_fails(self):
        assert not self._same_basename_swap("known_risks").passed

    def test_same_basename_cross_directory_blocker_swap_fails(self):
        assert not self._same_basename_swap("blocking_findings").passed

    def test_diagnostic_pass_has_no_governance_authority(self):
        payload = evaluate(dict(AUDITED_DOC)).as_dict()
        assert payload["result"] == "PASS"
        assert payload["authority_effect"] == "NONE"
        assert payload["audit_reuse_authorized"] is False
        assert payload["diagnostic_only"] is True

    @pytest.mark.parametrize("field", ["audited_head", "successor_head"])
    @pytest.mark.parametrize("value", ["abc123", "HEAD", "f" * 39, "f" * 41])
    def test_non_full_git_object_id_is_denied(self, field, value):
        args = dict(BASE_ARGS)
        args[field] = value
        args["audited_bundle"] = ProofOnlyBundle({PROOF_PATH: dict(AUDITED_DOC)})
        args["successor_bundle"] = ProofOnlyBundle({PROOF_PATH: dict(AUDITED_DOC)})
        args["facts"] = observed()
        with pytest.raises(Exception):
            evaluate_proof_only_equivalence(**args)

    def test_claimed_structural_facts_cannot_label_themselves_observed(self):
        with pytest.raises(TypeError):
            StructuralFacts(
                ancestry_established=True,
                basis={name: FactBasis.OBSERVED_GIT for name in STRUCTURAL_CONJUNCTS},
            )


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=str(repo), check=True, capture_output=True)


@pytest.fixture()
def observer_repo(tmp_path: Path) -> tuple[Path, str, str]:
    """A real two-commit repository: content head, then a proof-only successor."""
    repo = tmp_path / "repo"
    (repo / "proof" / "TP-X").mkdir(parents=True)
    (repo / "src").mkdir()
    (repo / "task-packets").mkdir()
    _git(repo.parent, "init", "-q", str(repo))
    _git(repo, "config", "user.email", "tester@example.com")
    _git(repo, "config", "user.name", "Tester")
    (repo / "src" / "a.py").write_text("print(1)\n")
    (repo / "task-packets" / "TP-X.json").write_text('{"id": "TP-X"}\n')
    (repo / "proof" / "TP-X" / "PROOF.json").write_text('{"audit_verdict": "PASS"}\n')
    (repo / "proof" / "TP-X" / "AUDITOR_REPORT.md").write_text("verdict PASS\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "content")
    audited = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(repo), capture_output=True, text=True
    ).stdout.strip()
    (repo / "proof" / "TP-X" / "SUMMARY.md").write_text("generated 2026-08-25\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "proof-only")
    successor = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(repo), capture_output=True, text=True
    ).stdout.strip()
    return repo, audited, successor


class TestGitObserver:
    """The observer is what makes OBSERVED_GIT mean anything."""

    def _observe(self, repo, audited, successor, **overrides):
        kwargs = dict(
            allowed_paths=["proof/**"],
            packet_path="task-packets/TP-X.json",
            policy_path="src/a.py",
            audit_result_path="proof/TP-X/AUDITOR_REPORT.md",
        )
        kwargs.update(overrides)
        return observe_proof_only_facts(
            repo, audited_head=audited, successor_head=successor, **kwargs
        )

    def test_observes_a_genuine_proof_only_successor(self, observer_repo):
        repo, audited, successor = observer_repo
        facts = self._observe(repo, audited, successor)
        assert facts.ancestry_established
        assert list(facts.actual_changed_paths) == ["proof/TP-X/SUMMARY.md"]
        assert facts.content_tree_equivalent_under_exclusion
        assert facts.raw_diff_digest.startswith("sha256:")
        assert facts.observation_digest and facts.observer_version

    def test_observed_facts_reach_pass(self, observer_repo):
        repo, audited, successor = observer_repo
        doc = {"audit_verdict": "PASS"}
        result = evaluate_observed_proof_only_equivalence(
            repo_root=repo,
            equivalence_id="eq",
            audited_head=audited,
            successor_head=successor,
            audited_bundle=ProofOnlyBundle({PROOF_PATH: doc}),
            successor_bundle=ProofOnlyBundle({PROOF_PATH: doc}),
            allowed_paths=["proof/**"],
            packet_path="task-packets/TP-X.json",
            policy_path="src/a.py",
            audit_result_path="proof/TP-X/AUDITOR_REPORT.md",
        )
        assert result.passed, result.failures
        assert result.structural_basis_all_observed

    def test_source_change_is_observed_not_asserted(self, observer_repo):
        repo, audited, successor = observer_repo
        (repo / "src" / "a.py").write_text("print(2)\n")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "source change")
        moved = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(repo), capture_output=True, text=True
        ).stdout.strip()
        facts = self._observe(repo, audited, moved)
        assert not facts.content_tree_equivalent_under_exclusion
        assert "src/a.py" in facts.actual_changed_paths

    def test_non_descendant_is_not_established(self, observer_repo):
        repo, audited, successor = observer_repo
        facts = self._observe(repo, successor, audited)
        assert not facts.ancestry_established
        assert (
            facts.basis_for("current_head_descends_from_or_is_patch_equivalent_to_audited_head")
            is FactBasis.OBSERVED_GIT
        )

    def test_mode_only_change_breaks_tree_equivalence(self, observer_repo):
        """A source file becoming executable preserves its blob oid exactly.

        Digesting the oid alone would call the trees equivalent. The conjunct is
        meant to be independent of the path check, so it must see this itself.
        """
        repo, audited, _ = observer_repo
        (repo / "src" / "a.py").chmod(0o755)
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "chmod +x")
        moved = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(repo), capture_output=True, text=True
        ).stdout.strip()
        facts = self._observe(repo, audited, moved)
        assert not facts.content_tree_equivalent_under_exclusion

    def test_type_change_to_symlink_breaks_tree_equivalence(self, observer_repo):
        """A regular file whose content is a path, retyped as a symlink to it.

        Git stores a symlink's target as the blob body, so the oid is unchanged.
        """
        repo, _, _ = observer_repo
        (repo / "src" / "link.txt").write_text("/etc/passwd")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "add regular file")
        before = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(repo), capture_output=True, text=True
        ).stdout.strip()
        (repo / "src" / "link.txt").unlink()
        (repo / "src" / "link.txt").symlink_to("/etc/passwd")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "retype as symlink")
        after = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(repo), capture_output=True, text=True
        ).stdout.strip()
        oids = [
            subprocess.run(
                ["git", "ls-tree", "-r", head, "--", "src/link.txt"],
                cwd=str(repo),
                capture_output=True,
                text=True,
            ).stdout.split()[2]
            for head in (before, after)
        ]
        assert oids[0] == oids[1], "precondition: the blob oid must be unchanged"
        facts = self._observe(repo, before, after)
        assert not facts.content_tree_equivalent_under_exclusion

    def test_absent_named_path_is_reported(self, observer_repo):
        repo, audited, successor = observer_repo
        facts = self._observe(repo, audited, successor, packet_path="task-packets/NOPE.json")
        assert facts.absent_named_paths

    def test_observation_digest_changes_with_the_subject(self, observer_repo):
        repo, audited, successor = observer_repo
        first = self._observe(repo, audited, successor)
        second = self._observe(repo, audited, successor, allowed_paths=["proof/TP-X/**"])
        assert first.observation_digest != second.observation_digest

    def test_unresolved_head_is_denied(self, observer_repo):
        repo, audited, successor = observer_repo
        with pytest.raises(Exception):
            self._observe(repo, "HEAD~1", successor)

    def test_abbreviated_head_is_denied(self, observer_repo):
        """A receipt binds an exact head pair, so a short sha is not a head."""
        repo, audited, successor = observer_repo
        with pytest.raises(Exception):
            self._observe(repo, audited[:12], successor)

    def test_pass_receipt_without_observation_provenance_is_schema_invalid(self):
        """A hand-written PASS must not be able to omit how it was observed."""
        payload = evaluate(dict(AUDITED_DOC)).as_dict()
        assert payload["result"] == "PASS"
        schema = json.loads(
            (SCHEMA_DIR / "proof-only-successor-equivalence.schema.json").read_text()
        )
        forged = {
            key: value
            for key, value in payload.items()
            if key not in {"observer_version", "observation_digest"}
        }
        with pytest.raises(Exception):
            Draft7Validator(schema).validate(forged)

    def test_write_verbs_are_refused_even_with_valid_shas(self, observer_repo):
        repo, audited, successor = observer_repo
        for forbidden in (
            ["reset", "--hard", audited],
            ["checkout", audited],
            ["push", "origin", audited],
        ):
            with pytest.raises(Exception):
                run_git_read(repo, forbidden)

    def test_path_traversal_in_a_blobspec_is_refused(self, observer_repo):
        repo, audited, _ = observer_repo
        with pytest.raises(Exception):
            run_git_read(repo, ["show", f"{audited}:../outside"])
