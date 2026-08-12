"""Adversarial matrix for the Second Brain ADR machine-contract validator.

Every test executes the REAL validator as a subprocess against a mutated copy
of the repository slice. Nothing here reimplements the validator's logic — a
duplicate implementation would only prove the duplicate agrees with itself.

The shape of each negative test is: start from a sandbox that PASSES, apply
exactly one mutation, assert the validator now fails AND that the specific
guard responsible for that mutation is the one reporting it. Asserting only
"exit != 0" would let an unrelated check take the credit and leave the
intended guard silently dead.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "scripts" / "governance" / "validate_second_brain_adr_contracts.py"

CONTRACT_DIR = "schemas/second_brain/contracts"
ADR_DIR = "docs/03-reference/architecture/second-brain/adr-candidates"
CANDIDATE = f"{ADR_DIR}/second-brain-adr-candidates.md"
FO01_STATUS = f"{ADR_DIR}/fo-01-repair-status.json"
TRACEABILITY = f"{ADR_DIR}/traceability-matrix.json"
FO01_RECEIPT = (
    "proof/TP-DMX-SECOND-BRAIN-ADR-TRACEABILITY-REPAIR-001/FO01_RESOLUTION_RECEIPT.json"
)
INVENTORY = (
    "proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/ADR_CLAUSE_INVENTORY.json"
)
COVERAGE = f"{CONTRACT_DIR}/ADR_CONTRACT_COVERAGE.json"

COPY_FILES = [CANDIDATE, FO01_STATUS, TRACEABILITY, FO01_RECEIPT, INVENTORY]


def run_validator(root: Path) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR), "--repo-root", str(root), "--json"],
        capture_output=True,
        text=True,
    )
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        payload = {"failures": [], "stdout": proc.stdout, "stderr": proc.stderr}
    return proc.returncode, payload


def failed_checks(payload: dict) -> set[str]:
    return {f["check"] for f in payload.get("failures", [])}


@pytest.fixture(scope="session")
def pristine(tmp_path_factory) -> Path:
    """A byte-copy of the repository slice the validator reads."""
    root = tmp_path_factory.mktemp("sb-pristine")
    shutil.copytree(REPO_ROOT / CONTRACT_DIR, root / CONTRACT_DIR)
    for rel in COPY_FILES:
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / rel, dest)
    return root


@pytest.fixture
def sandbox(pristine: Path, tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    shutil.copytree(pristine, root)
    return root


def load(root: Path, rel: str):
    return json.loads((root / rel).read_text(encoding="utf-8"))


def save(root: Path, rel: str, obj) -> None:
    (root / rel).write_text(
        json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def rehash_inventory(root: Path) -> None:
    """Keep the coverage matrix's frozen-denominator hash consistent.

    Used by mutations that legitimately rewrite the inventory. Without this the
    denominator-hash guard fires first and masks the invariant under test.
    """
    import hashlib

    digest = hashlib.sha256((root / INVENTORY).read_bytes()).hexdigest()
    cov = load(root, COVERAGE)
    cov["clause_inventory_sha256"] = digest
    save(root, COVERAGE, cov)


def mutate_clause(root: Path, clause_id: str, **fields) -> None:
    """Apply the same change to the inventory AND the ADR contract.

    Mutating only one side would trip the cross-file agreement guard, which
    would prove nothing about whether the semantic invariant works. Mutating
    both sides consistently is the real false-green attempt.
    """
    adr_id = clause_id.rsplit("-", 1)[0]
    inv = load(root, INVENTORY)
    for adr in inv["adrs"]:
        for c in adr["clauses"]:
            if c["clause_id"] == clause_id:
                c.update(fields)
    save(root, INVENTORY, inv)
    rehash_inventory(root)

    rel = f"{CONTRACT_DIR}/{adr_id}.contract.json"
    contract = load(root, rel)
    for c in contract["decision_clauses"]:
        if c["clause_id"] == clause_id:
            c.update(fields)
    save(root, rel, contract)


# ---------------------------------------------------------------------------
# Positive control
# ---------------------------------------------------------------------------


def test_valid_frozen_contract_set_passes(sandbox: Path) -> None:
    code, payload = run_validator(sandbox)
    assert code == 0, payload.get("failures") or payload
    assert payload["result"] == "PASS_SECOND_BRAIN_ADR_MACHINE_CONTRACT_COVERAGE"
    assert payload["coverage_group"] == "PASS"
    assert payload["fo01_group"] == "PASS"
    assert payload["checks_failed"] == 0
    # A matrix of negative tests is worthless if the validator only ever fails.
    assert payload["checks_total"] > 100


# ---------------------------------------------------------------------------
# Structural mutations
# ---------------------------------------------------------------------------


def test_delete_one_adr_contract_fails(sandbox: Path) -> None:
    (sandbox / CONTRACT_DIR / "ADR-SB-005.contract.json").unlink()
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "A01-ten-adr-contracts-exist" in failed_checks(payload)


def test_change_candidate_sha_binding_fails(sandbox: Path) -> None:
    rel = f"{CONTRACT_DIR}/ADR-SB-003.contract.json"
    contract = load(sandbox, rel)
    contract["candidate_sha256"] = "0" * 64
    save(sandbox, rel, contract)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert {"A04-contracts-bind-candidate", "A03-validates:ADR-SB-003"} & failed_checks(
        payload
    )


def test_mutated_candidate_document_fails(sandbox: Path) -> None:
    """The candidate is frozen authority; any byte change must be detected."""
    p = sandbox / CANDIDATE
    p.write_text(p.read_text(encoding="utf-8") + "\ntrailing drift\n", encoding="utf-8")
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "A04-candidate-sha256" in failed_checks(payload)


def test_remove_one_coverage_clause_fails(sandbox: Path) -> None:
    cov = load(sandbox, COVERAGE)
    cov["entries"] = [e for e in cov["entries"] if e["clause_id"] != "ADR-SB-007-C06"]
    cov["coverage_status_counts"]["COVERED"] -= 1
    save(sandbox, COVERAGE, cov)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "A08-every-clause-covered-once" in failed_checks(payload)


def test_mark_one_clause_missing_fails(sandbox: Path) -> None:
    cov = load(sandbox, COVERAGE)
    for e in cov["entries"]:
        if e["clause_id"] == "ADR-SB-002-C04":
            e["coverage_status"] = "MISSING"
    cov["coverage_status_counts"]["COVERED"] -= 1
    cov["coverage_status_counts"]["MISSING"] = 1
    save(sandbox, COVERAGE, cov)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "A10-missing-zero" in failed_checks(payload)


def test_mark_one_clause_ambiguous_fails(sandbox: Path) -> None:
    cov = load(sandbox, COVERAGE)
    for e in cov["entries"]:
        if e["clause_id"] == "ADR-SB-003-C05":
            e["coverage_status"] = "AMBIGUOUS"
    cov["coverage_status_counts"]["COVERED"] -= 1
    cov["coverage_status_counts"]["AMBIGUOUS"] = 1
    save(sandbox, COVERAGE, cov)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "A11-ambiguous-zero" in failed_checks(payload)


def test_point_coverage_at_nonexistent_rule_fails(sandbox: Path) -> None:
    cov = load(sandbox, COVERAGE)
    for e in cov["entries"]:
        if e["clause_id"] == "ADR-SB-001-C01":
            e["contract_rule_pointer"] = "#/decision_clauses/999"
    save(sandbox, COVERAGE, cov)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "A09-pointers-resolve" in failed_checks(payload)


def test_coverage_pointing_at_prose_fails(sandbox: Path) -> None:
    """A pointer must land on a structured rule, not an explanatory string."""
    rel = f"{CONTRACT_DIR}/ADR-SB-001.contract.json"
    contract = load(sandbox, rel)
    contract["decision_clauses"][0] = "covered, trust me"
    save(sandbox, rel, contract)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert {
        "A09-pointers-are-structured-rules",
        "A03-validates:ADR-SB-001",
    } & failed_checks(payload)


def test_rule_disagreeing_with_clause_fails(sandbox: Path) -> None:
    """Naming a clause is not covering it: the rule must actually match."""
    rel = f"{CONTRACT_DIR}/ADR-SB-006.contract.json"
    contract = load(sandbox, rel)
    for c in contract["decision_clauses"]:
        if c["clause_id"] == "ADR-SB-006-C13":
            c["machine_value"] = "ALLOWED"
    save(sandbox, rel, contract)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "A09-rules-agree-with-clause" in failed_checks(payload)


def test_corrupt_one_sb_dec_reference_fails(sandbox: Path) -> None:
    rel = f"{CONTRACT_DIR}/ADR-SB-009.contract.json"
    contract = load(sandbox, rel)
    contract["sb_dec_references"] = ["SB-DEC-009", "SB-DEC-013", "SB-DEC-999"]
    save(sandbox, rel, contract)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "A07-sb-dec:ADR-SB-009" in failed_checks(payload)


def test_linking_sb_dec_026_fails(sandbox: Path) -> None:
    """SB-DEC-026 is operator-ruled A_LEAVE_UNLINKED."""
    rel = f"{CONTRACT_DIR}/ADR-SB-010.contract.json"
    contract = load(sandbox, rel)
    contract["sb_dec_references"] = ["SB-DEC-020", "SB-DEC-021", "SB-DEC-026"]
    save(sandbox, rel, contract)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert {"A19-sb-dec-026-unlinked", "A07-sb-dec:ADR-SB-010"} & failed_checks(payload)


def test_change_adr_status_proposed_to_accepted_fails(sandbox: Path) -> None:
    p = sandbox / CANDIDATE
    text = p.read_text(encoding="utf-8")
    p.write_text(text.replace("**Status:** `PROPOSED`", "**Status:** `ACCEPTED`", 1),
                 encoding="utf-8")
    code, payload = run_validator(sandbox)
    assert code != 0
    failed = failed_checks(payload)
    assert "A16-ten-proposed" in failed
    assert "A18-no-accepted-token" in failed


def test_delete_local_spool_port_contract_fails(sandbox: Path) -> None:
    (sandbox / CONTRACT_DIR / "local-spool-port.contract.json").unlink()
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "A13-named-typed-artifacts-exist" in failed_checks(payload)


def test_delete_open_loop_candidate_contract_fails(sandbox: Path) -> None:
    (sandbox / CONTRACT_DIR / "open-loop-candidate.schema.json").unlink()
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "A13-named-typed-artifacts-exist" in failed_checks(payload)


def test_redefining_the_frozen_denominator_fails(sandbox: Path) -> None:
    """Dropping a clause from the inventory must not shrink the denominator."""
    inv = load(sandbox, INVENTORY)
    for adr in inv["adrs"]:
        adr["clauses"] = [c for c in adr["clauses"] if c["clause_id"] != "ADR-SB-005-C07"]
    inv["clause_total"] = sum(len(a["clauses"]) for a in inv["adrs"])
    save(sandbox, INVENTORY, inv)
    code, payload = run_validator(sandbox)
    assert code != 0
    failed = failed_checks(payload)
    assert "A08-inventory-hash-agrees-with-coverage" in failed
    assert "A08-inventory-total" in failed


def test_forged_source_fragment_fails(sandbox: Path) -> None:
    """A clause may not cite decision text the candidate does not contain."""
    inv = load(sandbox, INVENTORY)
    for adr in inv["adrs"]:
        for c in adr["clauses"]:
            if c["clause_id"] == "ADR-SB-004-C05":
                c["source_fragments"] = ["Dom real data is permitted"]
    save(sandbox, INVENTORY, inv)
    rehash_inventory(sandbox)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "A08-fragments-are-candidate-substrings" in failed_checks(payload)


# ---------------------------------------------------------------------------
# Semantic mutations — schema-valid, architecturally wrong
# ---------------------------------------------------------------------------


def test_allow_restricted_spool_without_encryption_fails(sandbox: Path) -> None:
    rel = f"{CONTRACT_DIR}/local-spool-port.contract.json"
    spool = load(sandbox, rel)
    spool["classification_matrix"]["restricted"] = "ALLOWED"
    save(sandbox, rel, spool)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "S01-restricted-spool-requires-encryption" in failed_checks(payload)


def test_allow_unknown_class_spooling_fails(sandbox: Path) -> None:
    rel = f"{CONTRACT_DIR}/local-spool-port.contract.json"
    spool = load(sandbox, rel)
    spool["classification_matrix"]["unknown"] = "ALLOWED"
    save(sandbox, rel, spool)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "S01-unknown-class-denied" in failed_checks(payload)


def test_give_open_loop_candidate_an_assignee_fails(sandbox: Path) -> None:
    rel = f"{CONTRACT_DIR}/open-loop-candidate.schema.json"
    olc = load(sandbox, rel)
    olc["properties"]["assignee"] = {"type": "string"}
    save(sandbox, rel, olc)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "S02-open-loop-no-pm-properties" in failed_checks(payload)


def test_open_loop_candidate_open_shape_fails(sandbox: Path) -> None:
    """additionalProperties:false is what makes the PM firewall enforceable."""
    rel = f"{CONTRACT_DIR}/open-loop-candidate.schema.json"
    olc = load(sandbox, rel)
    olc["additionalProperties"] = True
    save(sandbox, rel, olc)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "S02-open-loop-closed-shape" in failed_checks(payload)


def test_give_open_loop_candidate_workflow_status_fails(sandbox: Path) -> None:
    rel = f"{CONTRACT_DIR}/open-loop-candidate.schema.json"
    olc = load(sandbox, rel)
    olc["properties"]["workflow_status"] = {"type": "string"}
    save(sandbox, rel, olc)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "S02-open-loop-no-pm-properties" in failed_checks(payload)


def test_enable_task_promotion_by_default_fails(sandbox: Path) -> None:
    rel = f"{CONTRACT_DIR}/task-promotion-request.schema.json"
    tpr = load(sandbox, rel)
    tpr["properties"]["enabled"] = {"type": "boolean", "default": True}
    save(sandbox, rel, tpr)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "S03-task-promotion-disabled" in failed_checks(payload)


def test_drop_task_promotion_proof_requirements_fails(sandbox: Path) -> None:
    rel = f"{CONTRACT_DIR}/task-promotion-request.schema.json"
    tpr = load(sandbox, rel)
    tpr["required"] = [r for r in tpr["required"] if r != "task_orchestrator_proof_ref"]
    save(sandbox, rel, tpr)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "S03-promotion-requires-both-proofs-and-approval" in failed_checks(payload)


def test_allow_unknown_policy_eligibility_fails(sandbox: Path) -> None:
    mutate_clause(sandbox, "ADR-SB-004-C04", machine_value="ALLOW")
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "S04-unknown-eligibility-denies" in failed_checks(payload)


def test_enable_confidential_semantic_indexing_fails(sandbox: Path) -> None:
    mutate_clause(
        sandbox,
        "ADR-SB-004-C07",
        machine_value=["public", "internal", "confidential", "restricted"],
    )
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "S04-no-confidential-restricted-indexing" in failed_checks(payload)


def test_allow_wrong_project_write_fails(sandbox: Path) -> None:
    rel = f"{CONTRACT_DIR}/project-identity-envelope.schema.json"
    pie = load(sandbox, rel)
    pie["properties"]["wrong_project_write_disposition"] = {"const": "ALLOW"}
    save(sandbox, rel, pie)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "S05-envelope-denies-wrong-project" in failed_checks(payload)


def test_enable_multi_project_background_capture_fails(sandbox: Path) -> None:
    rel = f"{CONTRACT_DIR}/project-identity-envelope.schema.json"
    pie = load(sandbox, rel)
    pie["properties"]["multi_project_background_capture_enabled"] = {"const": True}
    save(sandbox, rel, pie)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "S05-multi-project-capture-disabled" in failed_checks(payload)


def test_allow_more_than_one_active_capture_project_fails(sandbox: Path) -> None:
    rel = f"{CONTRACT_DIR}/project-identity-envelope.schema.json"
    pie = load(sandbox, rel)
    pie["properties"]["active_automatic_capture_project_count"]["maximum"] = 5
    save(sandbox, rel, pie)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "S05-envelope-single-active-project" in failed_checks(payload)


def test_raise_ux_visible_queue_max_above_seven_fails(sandbox: Path) -> None:
    mutate_clause(sandbox, "ADR-SB-010-C03", machine_value=25)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "S06-visible-queue-max-7" in failed_checks(payload)


def test_permit_surprise_write_fails(sandbox: Path) -> None:
    mutate_clause(sandbox, "ADR-SB-010-C10", machine_value=True)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "S07-no-surprise-writes" in failed_checks(payload)


def test_nonzero_searchable_residual_fails(sandbox: Path) -> None:
    mutate_clause(sandbox, "ADR-SB-007-C07", machine_value=5)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "S08-searchable-residual-zero" in failed_checks(payload)


def test_claim_denial_fixtures_implemented_fails(sandbox: Path) -> None:
    rel = f"{CONTRACT_DIR}/ADR-SB-006.contract.json"
    contract = load(sandbox, rel)
    contract["denial_fixtures"] = "IMPLEMENTED"
    save(sandbox, rel, contract)
    code, payload = run_validator(sandbox)
    assert code != 0
    failed = failed_checks(payload)
    assert "A15-no-denial-fixture-claim" in failed
    assert "A14-no-runtime-or-implementation-authority" in failed


def test_claim_runtime_authority_fails(sandbox: Path) -> None:
    rel = f"{CONTRACT_DIR}/ADR-SB-002.contract.json"
    contract = load(sandbox, rel)
    contract["runtime_claims_permitted"] = True
    save(sandbox, rel, contract)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert {
        "A14-no-runtime-or-implementation-authority",
        "A03-validates:ADR-SB-002",
    } & failed_checks(payload)


def test_port_claiming_implementation_fails(sandbox: Path) -> None:
    rel = f"{CONTRACT_DIR}/custody-port.contract.json"
    port = load(sandbox, rel)
    port["implementation_status"] = "IMPLEMENTED"
    save(sandbox, rel, port)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert {
        "A14-port-not-implemented:custody-port.contract.json",
        "A14-no-runtime-or-implementation-authority",
    } & failed_checks(payload)


def test_second_brain_as_authority_target_fails(sandbox: Path) -> None:
    """No contract may promote the Second Brain to a canonical authority."""
    mutate_clause(sandbox, "ADR-SB-002-C01", machine_value="second_brain")
    code, payload = run_validator(sandbox)
    assert code != 0
    failed = failed_checks(payload)
    assert "A20-authority-targets-closed-set" in failed
    assert "A20-second-brain-never-authority" in failed


# ---------------------------------------------------------------------------
# FO-01 reconciliation
# ---------------------------------------------------------------------------


def test_stale_fo01_record_fails(sandbox: Path) -> None:
    """The original F-2 defect: authority record contradicting its receipt."""
    status = load(sandbox, FO01_STATUS)
    status["fo01_status"] = "REPAIR_COMPLETE_PENDING_INDEPENDENT_VERIFICATION"
    status["independent_verification"] = {"performed": False, "verdict": None}
    save(sandbox, FO01_STATUS, status)
    code, payload = run_validator(sandbox)
    assert code != 0
    failed = failed_checks(payload)
    assert "B02-status-matches-receipt" in failed
    assert "B03-independent-verification-performed" in failed


def test_fo01_claiming_acceptance_authorized_fails(sandbox: Path) -> None:
    status = load(sandbox, FO01_STATUS)
    status["adr_acceptance_authorized"] = True
    save(sandbox, FO01_STATUS, status)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "B04-adr-acceptance-not-authorized" in failed_checks(payload)


def test_fo01_claiming_implementation_execution_fails(sandbox: Path) -> None:
    status = load(sandbox, FO01_STATUS)
    status["gates"]["implementation_execution"] = "AUTHORIZED"
    save(sandbox, FO01_STATUS, status)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "B07-implementation-execution-not-authorized" in failed_checks(payload)


def test_fo01_verdict_not_derived_from_receipt_fails(sandbox: Path) -> None:
    """Reconciliation may only mirror the receipt, never invent a verdict."""
    status = load(sandbox, FO01_STATUS)
    status["independent_verification"]["audited_content_head"] = "deadbeef" * 5
    save(sandbox, FO01_STATUS, status)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "B03-receipt-derived:audited_content_head" in failed_checks(payload)


def test_fo01_dropping_not_run_discipline_fails(sandbox: Path) -> None:
    status = load(sandbox, FO01_STATUS)
    status["preserved_not_run"]["purge_completeness"] = "PASS"
    save(sandbox, FO01_STATUS, status)
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "B09-not-run-preserved" in failed_checks(payload)


# ---------------------------------------------------------------------------
# Fail-closed behaviour
# ---------------------------------------------------------------------------


def test_unparseable_contract_fails(sandbox: Path) -> None:
    (sandbox / CONTRACT_DIR / "ADR-SB-008.contract.json").write_text(
        "{ not json", encoding="utf-8"
    )
    code, _ = run_validator(sandbox)
    assert code != 0


def test_missing_candidate_document_fails(sandbox: Path) -> None:
    (sandbox / CANDIDATE).unlink()
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "A04-candidate-present" in failed_checks(payload)


def test_missing_clause_inventory_fails(sandbox: Path) -> None:
    (sandbox / INVENTORY).unlink()
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "A08-inventory-present" in failed_checks(payload)


def test_empty_repo_root_fails(tmp_path: Path) -> None:
    code, _ = run_validator(tmp_path)
    assert code != 0


def test_nonexistent_repo_root_is_usage_error() -> None:
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR), "--repo-root", "/nonexistent/xyzzy"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
