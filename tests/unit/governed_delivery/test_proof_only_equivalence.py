"""GOV-AUD-F1 adversarial suite for proof-only successor equivalence.

The independent architecture audit's finding is that a path-membership predicate
cannot see a semantic change made *inside* an allowed proof-only path. Each
negative fixture below performs exactly that laundering attempt and must fail
closed; each positive fixture is a genuinely inert change and must pass.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

from dopemux.governed_delivery.equivalence import (
    FieldClassification,
    ProofOnlyBundle,
    classify_field,
    evaluate_proof_only_equivalence,
    flatten,
)

SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas" / "governed_delivery"

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

BASE_ARGS = dict(
    equivalence_id="eq-test",
    audited_head="a" * 40,
    successor_head="b" * 40,
    allowed_paths=["proof/**"],
    actual_changed_paths=["proof/TP-X/PROOF.json"],
    raw_diff_digest="sha256:rawdiff",
    raw_diff_contains_no_substantive_source_change=True,
    ancestry_established=True,
    ancestry_basis="OBSERVED_GIT",
    content_tree_equivalent_under_exclusion=True,
    audited_packet_digest="sha256:packet",
    successor_packet_digest="sha256:packet",
    audited_policy_digest="sha256:policy",
    successor_policy_digest="sha256:policy",
    audited_audit_result_digest="sha256:audit",
    successor_audit_result_digest="sha256:audit",
)


def evaluate(successor_doc, audited_doc=None, **overrides):
    """Compare one audited PROOF.json against one successor PROOF.json."""
    args = dict(BASE_ARGS)
    args.update(overrides)
    args["audited_bundle"] = ProofOnlyBundle({"PROOF.json": audited_doc or dict(AUDITED_DOC)})
    args["successor_bundle"] = ProofOnlyBundle({"PROOF.json": successor_doc})
    return evaluate_proof_only_equivalence(**args)


def mutated(**changes):
    doc = dict(AUDITED_DOC)
    doc.update(changes)
    return doc


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
        assert any("validation_claims" in f for f in result.mismatched_fields)

    def test_unknown_changed_to_proven(self):
        result = evaluate(mutated(unknowns=[]))
        assert not result.passed
        assert "unknowns" in result.mismatched_fields

    def test_empty_semantic_field_set(self):
        result = evaluate_proof_only_equivalence(
            **BASE_ARGS,
            audited_bundle=ProofOnlyBundle({}),
            successor_bundle=ProofOnlyBundle({}),
        )
        assert not result.passed
        assert "empty_semantic_field_set" in {f["code"] for f in result.failures}

    def test_missing_original_bundle(self):
        result = evaluate_proof_only_equivalence(
            **BASE_ARGS,
            audited_bundle=None,
            successor_bundle=ProofOnlyBundle({"PROOF.json": dict(AUDITED_DOC)}),
        )
        assert not result.passed
        assert "missing_original_bundle" in {f["code"] for f in result.failures}

    def test_independence_downgraded(self):
        result = evaluate(mutated(independence="PROVEN"))
        assert not result.passed

    def test_evidence_ref_list_weakened(self):
        result = evaluate(mutated(evidence_refs=["ev-1"]))
        assert not result.passed
        assert "evidence_refs" in result.mismatched_fields

    def test_security_claim_changed(self):
        result = evaluate(mutated(security_claims={"secret_scan": "SKIPPED"}))
        assert not result.passed

    def test_acceptance_criteria_changed(self):
        result = evaluate(mutated(acceptance_criteria=["some gates PASS"]))
        assert not result.passed


class TestAggregateForgery:
    """The aggregate must not be reproducible by crafting field names.

    An earlier design synthesised a ``field#document`` key to disambiguate a
    field repeated across documents. That key shared a namespace with real field
    names, so an edited bundle could drop a risk from one document and re-encode
    it as a literal ``known_risks#B`` key in another, reproducing the original
    aggregate byte for byte and passing equivalence.
    """

    AUDITED = {"A": {"known_risks": ["R1"]}, "B": {"known_risks": ["R2"]}}

    def _evaluate(self, successor):
        args = dict(BASE_ARGS)
        args["audited_bundle"] = ProofOnlyBundle(self.AUDITED)
        args["successor_bundle"] = ProofOnlyBundle(successor)
        return evaluate_proof_only_equivalence(**args)

    def test_crafted_separator_key_cannot_restore_the_aggregate(self):
        forged = {
            "A": {"known_risks": ["R1"], "known_risks#B": ["R2"]},
            "B": {"known_risks": ["R1"]},
        }
        result = self._evaluate(forged)
        assert not result.passed
        assert "known_risks" in result.mismatched_fields

    def test_crafted_separator_with_arbitrary_suffix_also_rejected(self):
        forged = {
            "A": {"known_risks": ["R1"], "known_risks#ANYTHING": ["R2"]},
            "B": {"known_risks": ["R1"]},
        }
        assert not self._evaluate(forged).passed

    def test_value_dropped_from_one_of_several_documents_is_rejected(self):
        assert not self._evaluate({"A": {"known_risks": ["R1"]}, "B": {}}).passed

    def test_aggregate_counts_repeated_values(self):
        """Two documents asserting the same value is not the same as one."""
        one = ProofOnlyBundle({"A": {"known_risks": ["R1"]}}).aggregate_fields()
        two = ProofOnlyBundle(
            {"A": {"known_risks": ["R1"]}, "B": {"known_risks": ["R1"]}}
        ).aggregate_fields()
        assert one != two

    def test_content_exchanged_between_documents_preserves_the_aggregate(self):
        """Documented boundary: the bundle's set of assertions is unchanged.

        This contract asserts path-independence, which is what lets a
        byte-identical relocation pass; it deliberately does not bind an
        assertion to the particular document carrying it.
        """
        swapped = {"A": {"known_risks": ["R2"]}, "B": {"known_risks": ["R1"]}}
        assert self._evaluate(swapped).passed


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
        return evaluate_proof_only_equivalence(**args)

    def test_literal_dotted_key_and_nesting_collide_to_one_entry(self):
        assert flatten({"audit": {"verdict": "PASS"}}) == flatten({"audit.verdict": "PASS"})

    def test_dotted_key_cannot_change_a_governance_value(self):
        result = self._evaluate(
            {"P": {"audit": {"verdict": "PASS_WITH_RISKS"}}},
            {"P": {"audit.verdict": "PASS"}},
        )
        assert not result.passed
        assert "audit.verdict" in result.mismatched_fields

    def test_dotted_key_cannot_inflate_a_count_to_disguise_a_drop(self):
        """Doc B drops its assertion; a crafted literal key in A cannot restore it."""
        audited = {
            "A": {"audit": {"verdict": "PASS_WITH_RISKS"}},
            "B": {"audit": {"verdict": "PASS_WITH_RISKS"}},
        }
        forged = {
            "A": {"audit.verdict": "PASS_WITH_RISKS", "audit": {"verdict": "PASS_WITH_RISKS"}},
            "B": {},
        }
        assert not self._evaluate(audited, forged).passed

    def test_pure_reencoding_preserving_every_assertion_passes(self):
        """Semantically neutral: the same assertions, differently encoded."""
        result = self._evaluate(
            {"P": {"audit": {"verdict": "PASS_WITH_RISKS", "risks": ["R1"]}}},
            {"P": {"audit.verdict": "PASS_WITH_RISKS", "audit": {"risks": ["R1"]}}},
        )
        assert result.passed


class TestStructuralConjuncts:
    def test_path_outside_allowlist_rejected(self):
        result = evaluate(dict(AUDITED_DOC), actual_changed_paths=["src/dopemux/thing.py"])
        assert not result.passed
        assert "path_outside_proof_only_allowlist" in {f["code"] for f in result.failures}
        assert result.non_allowed_diff_count == 1

    def test_ancestry_not_established_rejected(self):
        result = evaluate(dict(AUDITED_DOC), ancestry_established=False)
        assert not result.passed
        assert "ancestry_not_established" in {f["code"] for f in result.failures}

    def test_unknown_ancestry_basis_fails_closed(self):
        result = evaluate(dict(AUDITED_DOC), ancestry_basis="UNKNOWN")
        assert not result.passed

    def test_substantive_source_change_in_raw_diff_rejected(self):
        result = evaluate(dict(AUDITED_DOC), raw_diff_contains_no_substantive_source_change=False)
        assert not result.passed
        assert "raw_diff_contains_substantive_source_change" in {f["code"] for f in result.failures}

    def test_tree_not_equivalent_under_exclusion_rejected(self):
        result = evaluate(dict(AUDITED_DOC), content_tree_equivalent_under_exclusion=False)
        assert not result.passed

    def test_packet_digest_change_rejected(self):
        result = evaluate(dict(AUDITED_DOC), successor_packet_digest="sha256:different")
        assert not result.passed
        assert "packet_digest_changed" in {f["code"] for f in result.failures}

    def test_policy_digest_change_rejected(self):
        result = evaluate(dict(AUDITED_DOC), successor_policy_digest="sha256:different")
        assert not result.passed

    def test_audit_result_digest_change_rejected(self):
        result = evaluate(dict(AUDITED_DOC), successor_audit_result_digest="sha256:different")
        assert not result.passed

    def test_invalid_ancestry_basis_denied(self):
        with pytest.raises(Exception):
            evaluate(dict(AUDITED_DOC), ancestry_basis="MADE_UP")


class TestPositiveFixtures:
    def test_checksum_only_change(self):
        result = evaluate(mutated(checksum="cafebabe"))
        assert result.passed, result.failures

    def test_formatting_only_generated_metadata_change(self):
        result = evaluate(
            mutated(generated_at="2026-08-25T12:00:00Z", generator_version="1.0.1")
        )
        assert result.passed, result.failures

    def test_proof_reference_relocation_with_byte_identity(self):
        """The document moves; its governance content is byte-identical."""
        relocated = ProofOnlyBundle({"proof/relocated/PROOF.json": dict(AUDITED_DOC)})
        args = dict(BASE_ARGS)
        args["audited_bundle"] = ProofOnlyBundle({"PROOF.json": dict(AUDITED_DOC)})
        args["successor_bundle"] = relocated
        result = evaluate_proof_only_equivalence(**args)
        assert result.passed, result.failures

    def test_identical_bundle_passes(self):
        result = evaluate(dict(AUDITED_DOC))
        assert result.passed, result.failures


class TestAntiVacuity:
    def test_positive_result_compared_a_nonzero_field_set(self):
        result = evaluate(mutated(checksum="cafebabe"))
        assert result.passed
        assert len(result.compared_fields) > 0

    def test_every_compared_field_is_enumerated_with_an_outcome(self):
        result = evaluate(mutated(checksum="cafebabe"))
        for item in result.compared_fields:
            assert item.outcome in {
                "UNCHANGED",
                "INERT_CHANGE_ALLOWED",
                "GOVERNANCE_CHANGE_REJECTED",
                "UNCLASSIFIED_REJECTED",
            }

    def test_unclassified_field_fails_closed(self):
        result = evaluate(mutated(some_entirely_novel_field="value"))
        assert not result.passed
        assert "some_entirely_novel_field" in result.unclassified_fields

    def test_receipt_records_raw_diff_digest(self):
        result = evaluate(mutated(checksum="cafebabe"))
        assert result.as_dict()["raw_diff_digest"] == "sha256:rawdiff"

    def test_receipt_validates_against_schema(self):
        schema = json.loads(
            (SCHEMA_DIR / "proof-only-successor-equivalence.schema.json").read_text(encoding="utf-8")
        )
        validator = Draft7Validator(schema)
        validator.validate(evaluate(mutated(checksum="cafebabe")).as_dict())
        validator.validate(evaluate(mutated(known_risks=[])).as_dict())

    def test_failing_receipt_lists_failures(self):
        result = evaluate(mutated(audit_verdict="PASS"))
        assert result.as_dict()["result"] == "FAIL"
        assert len(result.as_dict()["failures"]) > 0


class TestClassifier:
    @pytest.mark.parametrize(
        "field_name",
        [
            "known_risks",
            "unknowns",
            "blocking_findings",
            "audit_verdict",
            "auditor_identity",
            "independence",
            "authority_statements",
            "scope_statements",
            "acceptance_criteria",
            "content_head",
            "tree_digest",
            "validation_claims",
            "security_claims",
            "merge_readiness_claims",
            "activation_claims",
            "evidence_refs",
            "conflicts",
            "operator_decision_refs",
        ],
    )
    def test_governance_fields_classified(self, field_name):
        assert classify_field(field_name) == FieldClassification.GOVERNANCE_RELEVANT

    @pytest.mark.parametrize("field_name", ["checksum", "generated_at", "generator_version"])
    def test_inert_fields_classified(self, field_name):
        assert classify_field(field_name) == FieldClassification.INERT

    def test_compound_name_with_governance_token_beats_inert_leaf(self):
        assert classify_field("audit_result_checksum") == FieldClassification.GOVERNANCE_RELEVANT

    def test_unrecognized_field_is_unknown(self):
        assert classify_field("wholly_unanticipated") == FieldClassification.UNKNOWN

    def test_empty_field_is_unknown(self):
        assert classify_field("   ") == FieldClassification.UNKNOWN


class TestFlatten:
    def test_nested_mapping_flattens_to_dotted_paths(self):
        assert flatten({"a": {"b": 1}}) == {"a.b": "1"}

    def test_list_is_canonicalized_as_a_whole(self):
        assert flatten({"a": [1, 2]}) == {"a": "[1,2]"}

    def test_list_reordering_is_a_change(self):
        assert flatten({"a": [1, 2]}) != flatten({"a": [2, 1]})
