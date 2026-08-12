"""Adversarial matrix for the Second Brain ADR machine-contract validator.

Every test executes the REAL validator as a subprocess against a mutated copy
of the repository slice. Nothing here reimplements the validator's logic — a
duplicate implementation would only prove the duplicate agrees with itself.

The shape of each negative test is: start from a sandbox that PASSES, apply
exactly one mutation, assert the validator now fails AND that the specific
guard responsible for that mutation is among the failures. Asserting only
"exit != 0" would let an unrelated check take the credit and leave the intended
guard silently dead.

Two adversary strengths are modelled:

* **plain** — the artifacts are edited. The frozen-denominator pin catches any
  change to a clause value, however consistently it is applied across files.
* **repinned** — the adversary also rewrites the pin inside the validator *and*
  the supersession receipt, so the freeze no longer objects. This is the
  producer-with-write-access case, and it is the one that shows whether the
  semantic guards do any work of their own. The first audit's BLOCKER 1 lived
  exactly here: every guard survived a consistent bilateral edit.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "scripts/governance/validate_second_brain_adr_contracts.py"

CONTRACT_DIR = "schemas/second_brain/contracts"
ADR_DIR = "docs/03-reference/architecture/second-brain/adr-candidates"
PROOF_DIR = "proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001"
CANDIDATE = f"{ADR_DIR}/second-brain-adr-candidates.md"
FO01_STATUS = f"{ADR_DIR}/fo-01-repair-status.json"
TRACEABILITY = f"{ADR_DIR}/traceability-matrix.json"
FO01_RECEIPT = (
    "proof/TP-DMX-SECOND-BRAIN-ADR-TRACEABILITY-REPAIR-001/FO01_RESOLUTION_RECEIPT.json"
)
INVENTORY = f"{PROOF_DIR}/ADR_CLAUSE_INVENTORY.json"
REFREEZE_RECEIPT = f"{PROOF_DIR}/DENOMINATOR_REFREEZE_RECEIPT.json"
COVERAGE = f"{CONTRACT_DIR}/ADR_CONTRACT_COVERAGE.json"
CUSTODY = f"{CONTRACT_DIR}/custody-port.contract.json"
SPOOL = f"{CONTRACT_DIR}/local-spool-port.contract.json"
CAPABILITY = f"{CONTRACT_DIR}/service-capability-receipt.schema.json"
ENVELOPE = f"{CONTRACT_DIR}/project-identity-envelope.schema.json"
OPEN_LOOP = f"{CONTRACT_DIR}/open-loop-candidate.schema.json"
PROMOTION = f"{CONTRACT_DIR}/task-promotion-request.schema.json"

COPY_FILES = [
    CANDIDATE, FO01_STATUS, TRACEABILITY, FO01_RECEIPT, INVENTORY, REFREEZE_RECEIPT,
]


# --------------------------------------------------------------------------
# Harness
# --------------------------------------------------------------------------

def run_validator(root: Path, validator: Path | None = None) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(validator or VALIDATOR), "--repo-root", str(root),
         "--json"],
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


def save(root: Path, rel: str, doc) -> None:
    (root / rel).write_text(
        json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def clause_of(doc, clause_id: str):
    for adr in doc["adrs"]:
        for c in adr["clauses"]:
            if c["clause_id"] == clause_id:
                return c
    raise AssertionError(f"clause {clause_id} not in inventory")


def mutate_clause(root: Path, clause_id: str, **fields) -> None:
    """Apply the same change to the inventory AND the ADR contract.

    Mutating only one side would trip the cross-file agreement guard, which
    would prove nothing about whether the semantic invariant works.
    """
    inv = load(root, INVENTORY)
    clause_of(inv, clause_id).update(fields)
    save(root, INVENTORY, inv)

    adr_id = clause_id.rsplit("-", 1)[0]
    rel = f"{CONTRACT_DIR}/{adr_id}.contract.json"
    contract = load(root, rel)
    for c in contract["decision_clauses"]:
        if c["clause_id"] == clause_id:
            c.update(fields)
    save(root, rel, contract)


def repin(root: Path) -> Path:
    """Re-pin the validator and the supersession receipt to the mutated state.

    Models the strongest realistic adversary: someone who can also edit the
    freeze. Returns the path of the re-pinned validator to run.
    """
    inv_bytes = (root / INVENTORY).read_bytes()
    new_sha = hashlib.sha256(inv_bytes).hexdigest()
    total = json.loads(inv_bytes.decode())["clause_total"]

    src = VALIDATOR.read_text(encoding="utf-8")
    src = re.sub(
        r'FROZEN_INVENTORY_SHA256 = \(\n    "[0-9a-f]{64}"\n\)',
        f'FROZEN_INVENTORY_SHA256 = (\n    "{new_sha}"\n)',
        src,
    )
    src = re.sub(r"FROZEN_CLAUSE_TOTAL = \d+", f"FROZEN_CLAUSE_TOTAL = {total}", src)
    assert new_sha in src, "repin helper failed to rewrite the pin"
    dest = root / "repinned_validator.py"
    dest.write_text(src, encoding="utf-8")

    receipt = load(root, REFREEZE_RECEIPT)
    receipt["new_inventory_sha256"] = new_sha
    receipt["new_clause_count"] = total
    save(root, REFREEZE_RECEIPT, receipt)
    return dest


def assert_guard(root: Path, guard: str, validator: Path | None = None) -> set[str]:
    code, payload = run_validator(root, validator)
    failures = failed_checks(payload)
    assert code != 0, f"mutation was accepted; expected {guard} to fire"
    assert guard in failures, (
        f"{guard} did not fire; failures were {sorted(failures)}. An unrelated "
        "check cannot take credit for catching this."
    )
    return failures


def projection_pointers() -> list[str]:
    spec = importlib.util.spec_from_file_location("sbval", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return sorted(module.RECEIPT_PROJECTION)


# --------------------------------------------------------------------------
# Baseline
# --------------------------------------------------------------------------

def test_repository_passes():
    code, payload = run_validator(REPO_ROOT)
    assert code == 0, payload.get("failures")
    assert payload["result"] == "PASS_SECOND_BRAIN_ADR_MACHINE_CONTRACT_COVERAGE"


def test_sandbox_passes(sandbox: Path):
    code, payload = run_validator(sandbox)
    assert code == 0, payload.get("failures")


def test_repinned_pristine_still_passes(sandbox: Path):
    """The repin helper must not itself break anything.

    Otherwise every 'repinned' mutation below could fail for the wrong reason.
    """
    validator = repin(sandbox)
    code, payload = run_validator(sandbox, validator)
    assert code == 0, payload.get("failures")


# --------------------------------------------------------------------------
# The operator's mandated mutation matrix
# --------------------------------------------------------------------------

def test_m01_bilateral_inventory_and_contract_change(sandbox: Path):
    """The exact false-green the first audit found: edit both sides at once."""
    mutate_clause(sandbox, "ADR-SB-002-C05", machine_value="AUTO_APPLY")
    assert_guard(sandbox, "A09-inventory-matches-frozen-pin")


def test_m02_authority_first_inverted(sandbox: Path):
    mutate_clause(sandbox, "ADR-SB-003-C01", machine_value=False)
    validator = repin(sandbox)
    assert_guard(sandbox, "S23-recall-authority-first", validator)


def test_m03_review_default_becomes_auto_apply(sandbox: Path):
    mutate_clause(sandbox, "ADR-SB-002-C09", machine_value=True)
    validator = repin(sandbox)
    assert_guard(sandbox, "S25-review-default-defer-no-mutation", validator)


def test_m04_drop_purge_from_closed_set(sandbox: Path):
    mutate_clause(sandbox, "ADR-SB-007-C01", machine_value=["ARCHIVE", "FORGET"])
    validator = repin(sandbox)
    failures = assert_guard(sandbox, "A26-closed-sets-bidirectional", validator)
    assert "S22-deletion-operations-exact" in failures


def test_m05_drop_review_from_ux_operations(sandbox: Path):
    mutate_clause(sandbox, "ADR-SB-010-C01", machine_value=["CAPTURE", "RECALL"])
    validator = repin(sandbox)
    failures = assert_guard(sandbox, "A26-closed-sets-bidirectional", validator)
    assert "S18-ux-operations-exact" in failures


def test_m06_add_invented_canonical_authority(sandbox: Path):
    mutate_clause(
        sandbox, "ADR-SB-008-C29",
        machine_value=["Leantime", "Task Orchestrator", "dopeTask"],
    )
    validator = repin(sandbox)
    failures = assert_guard(sandbox, "A27-no-invented-authority-value", validator)
    assert "A26-closed-sets-bidirectional" in failures


def test_m07_add_cloud_offload_to_custody_port(sandbox: Path):
    doc = load(sandbox, CUSTODY)
    doc["assertions"]["cloud_offload"] = True
    save(sandbox, CUSTODY, doc)
    assert_guard(sandbox, "A31-layer-b-surface-grounded")


def test_m08_invent_schema_property_and_enum(sandbox: Path):
    doc = load(sandbox, CAPABILITY)
    doc["properties"]["freshness_state"] = {"enum": ["CURRENT", "STALE"]}
    save(sandbox, CAPABILITY, doc)
    assert_guard(sandbox, "A31-layer-b-surface-grounded")
    _, payload = run_validator(sandbox)
    detail = " ".join(
        f["detail"] for f in payload["failures"] if f["check"].startswith("A31")
    )
    assert "freshness_state" in detail


def test_m09_remove_each_newly_added_denominator_clause(sandbox: Path):
    """Every clause the re-freeze added, removed one at a time.

    The operator's matrix says 'each', not a sample, so this loops over all of
    them with no cap. The denominator's completeness is held by the freeze, so
    the pin is the guard that must fire.
    """
    receipt = load(sandbox, REFREEZE_RECEIPT)
    added = receipt["added_clause_ids"]
    assert len(added) == 63, f"expected the 63 recorded additions, got {len(added)}"

    original = (sandbox / INVENTORY).read_text(encoding="utf-8")
    for clause_id in added:
        inv = json.loads(original)
        for adr in inv["adrs"]:
            before = len(adr["clauses"])
            adr["clauses"] = [c for c in adr["clauses"] if c["clause_id"] != clause_id]
            if len(adr["clauses"]) != before:
                adr["clause_count"] = len(adr["clauses"])
        inv["clause_total"] -= 1
        save(sandbox, INVENTORY, inv)
        assert_guard(sandbox, "A09-inventory-matches-frozen-pin")
    (sandbox / INVENTORY).write_text(original, encoding="utf-8")


def test_m09b_removed_clause_survives_a_repin(sandbox: Path):
    """With the pin also rewritten, the coverage matrix still objects.

    Not the primary guard — denominator completeness is held by the freeze and
    by independent audit — but it is not zero either.
    """
    inv = load(sandbox, INVENTORY)
    for adr in inv["adrs"]:
        if adr["adr_id"] == "ADR-SB-003":
            adr["clauses"] = [
                c for c in adr["clauses"] if c["clause_id"] != "ADR-SB-003-C12"
            ]
            adr["clause_count"] = len(adr["clauses"])
    inv["clause_total"] -= 1
    save(sandbox, INVENTORY, inv)
    validator = repin(sandbox)
    failures = assert_guard(sandbox, "A20-every-clause-covered-once", validator)
    assert "S24-historical-and-current-distinct" in failures


def test_m10_alter_each_fo01_receipt_derived_field(sandbox: Path):
    """Every projected FO-01 field, drifted one at a time.

    The finding this replaces was that a partial projection passed while a
    sibling field had drifted, so a single spot-check is not evidence.
    """
    pointers = projection_pointers()
    assert len(pointers) >= 39, f"projection map shrank to {len(pointers)} fields"

    original = (sandbox / FO01_STATUS).read_text(encoding="utf-8")
    for ptr in pointers:
        status = json.loads(original)
        parts = ptr.lstrip("/").split("/")
        node = status
        for part in parts[:-1]:
            node = node[part]
        current = node[parts[-1]]
        if isinstance(current, bool):
            node[parts[-1]] = not current
        elif isinstance(current, int):
            node[parts[-1]] = current + 1
        else:
            node[parts[-1]] = f"{current}-DRIFTED"
        save(sandbox, FO01_STATUS, status)
        assert_guard(sandbox, "B02-receipt-projection-exact")
    (sandbox / FO01_STATUS).write_text(original, encoding="utf-8")


# --------------------------------------------------------------------------
# Grounding and provenance
# --------------------------------------------------------------------------

def test_fragment_not_in_candidate_fails(sandbox: Path):
    mutate_clause(
        sandbox, "ADR-SB-001-C02",
        source_fragments=["The Second Brain owns a canonical database"],
    )
    validator = repin(sandbox)
    assert_guard(sandbox, "A23-fragments-are-candidate-substrings", validator)


def test_fragment_from_rejected_alternatives_fails(sandbox: Path):
    """A rejected design is verbatim candidate text — and must never ground."""
    frag = "Vector-first answer generation"
    mutate_clause(
        sandbox, "ADR-SB-003-C01",
        source_fragments=[frag],
        source_decision_text_hash=hashlib.sha256(frag.encode()).hexdigest(),
    )
    validator = repin(sandbox)
    assert_guard(sandbox, "A23-fragments-not-from-rejected-alternatives", validator)


def test_fragment_hash_tamper_fails(sandbox: Path):
    mutate_clause(sandbox, "ADR-SB-001-C02", source_decision_text_hash="0" * 64)
    validator = repin(sandbox)
    assert_guard(sandbox, "A24-fragment-hashes-recompute", validator)


def test_widening_a_closed_set_fails(sandbox: Path):
    mutate_clause(
        sandbox, "ADR-SB-004-C01",
        machine_value=["PROJECT", "HUE", "DOM", "SHARED", "PUBLIC"],
    )
    validator = repin(sandbox)
    assert_guard(sandbox, "A26-closed-sets-bidirectional", validator)


def test_label_only_rule_shape_fails(sandbox: Path):
    """The shape that made the superseded contracts unfalsifiable."""
    mutate_clause(
        sandbox, "ADR-SB-007-C02",
        rule_type="REQUIRE", operator="MUST_EXIST",
        machine_value="PURGE_DEPENDENCY_GRAPH",
    )
    validator = repin(sandbox)
    assert_guard(sandbox, "A25-rule-shapes-are-testable", validator)


def test_ungrounded_constant_fails(sandbox: Path):
    mutate_clause(sandbox, "ADR-SB-004-C05", machine_value="REAL_DATA_ALLOWED")
    validator = repin(sandbox)
    assert_guard(sandbox, "A26-machine-values-grounded", validator)


def test_numeric_not_in_text_fails(sandbox: Path):
    mutate_clause(sandbox, "ADR-SB-010-C03", machine_value=12)
    validator = repin(sandbox)
    assert_guard(sandbox, "A26-machine-values-grounded", validator)


def test_orphan_grounding_entry_fails(sandbox: Path):
    doc = load(sandbox, CUSTODY)
    doc["x-grounding"]["/assertions/nonexistent"] = {
        "clause_id": "ADR-SB-006-C16",
        "term": "Custody product remains replaceable",
    }
    save(sandbox, CUSTODY, doc)
    assert_guard(sandbox, "A32-no-orphan-grounding")


def test_grounding_term_not_in_clause_fails(sandbox: Path):
    doc = load(sandbox, CAPABILITY)
    doc["x-grounding"]["/properties/current"]["term"] = "always fresh"
    save(sandbox, CAPABILITY, doc)
    assert_guard(sandbox, "A31-layer-b-surface-grounded")


def test_layer_b_invariant_disagreeing_with_inventory_fails(sandbox: Path):
    doc = load(sandbox, CUSTODY)
    doc["x-machine-invariants"]["ADR-SB-006-C16"]["machine_value"] = False
    save(sandbox, CUSTODY, doc)
    assert_guard(sandbox, "A33-layer-b-invariants-agree-with-inventory")


# --------------------------------------------------------------------------
# Coverage integrity
# --------------------------------------------------------------------------

def test_dropping_a_coverage_entry_fails(sandbox: Path):
    cov = load(sandbox, COVERAGE)
    cov["entries"] = cov["entries"][:-1]
    save(sandbox, COVERAGE, cov)
    assert_guard(sandbox, "A20-every-clause-covered-once")


def test_marking_a_clause_not_applicable_fails(sandbox: Path):
    cov = load(sandbox, COVERAGE)
    cov["entries"][0]["coverage_status"] = "NOT_APPLICABLE_PROVEN"
    cov["coverage_status_counts"]["COVERED"] -= 1
    cov["coverage_status_counts"]["NOT_APPLICABLE_PROVEN"] = 1
    save(sandbox, COVERAGE, cov)
    assert_guard(sandbox, "A21-no-clause-excused")


def test_coverage_pointer_to_prose_fails(sandbox: Path):
    cov = load(sandbox, COVERAGE)
    cov["entries"][0]["contract_rule_pointer"] = "#/adr_title"
    save(sandbox, COVERAGE, cov)
    assert_guard(sandbox, "A22-rules-agree-with-inventory")


def test_unilateral_contract_edit_fails(sandbox: Path):
    rel = f"{CONTRACT_DIR}/ADR-SB-009.contract.json"
    doc = load(sandbox, rel)
    for c in doc["decision_clauses"]:
        if c["clause_id"] == "ADR-SB-009-C03":
            c["machine_value"] = 4
    save(sandbox, rel, doc)
    assert_guard(sandbox, "A22-rules-agree-with-inventory")


def test_coverage_unpinned_from_inventory_fails(sandbox: Path):
    cov = load(sandbox, COVERAGE)
    cov["clause_inventory_sha256"] = "0" * 64
    save(sandbox, COVERAGE, cov)
    assert_guard(sandbox, "A19-coverage-pins-inventory")


def test_refreeze_receipt_without_operator_ruling_fails(sandbox: Path):
    receipt = load(sandbox, REFREEZE_RECEIPT)
    receipt["authorization"]["ruling_verbatim"] = "authorized"
    save(sandbox, REFREEZE_RECEIPT, receipt)
    assert_guard(sandbox, "A11-refreeze-authorization-recorded")


def test_receipt_pointing_at_the_wrong_predecessor_fails(sandbox: Path):
    receipt = load(sandbox, REFREEZE_RECEIPT)
    receipt["supersedes_inventory_sha256"] = "1" * 64
    save(sandbox, REFREEZE_RECEIPT, receipt)
    assert_guard(sandbox, "A11-supersession-recorded")


# --------------------------------------------------------------------------
# Authority and status discipline
# --------------------------------------------------------------------------

def test_second_brain_as_authority_target_fails(sandbox: Path):
    mutate_clause(sandbox, "ADR-SB-002-C01", machine_value="Second Brain")
    validator = repin(sandbox)
    failures = assert_guard(sandbox, "A28-second-brain-never-authority", validator)
    assert "A26-machine-values-grounded" in failures


def test_denial_fixture_claim_fails(sandbox: Path):
    rel = f"{CONTRACT_DIR}/ADR-SB-006.contract.json"
    doc = load(sandbox, rel)
    doc["denial_fixtures"] = "IMPLEMENTED_AND_PASSING"
    save(sandbox, rel, doc)
    assert_guard(sandbox, "A38-denial-fixtures-deferred")


def test_runtime_authority_claim_fails(sandbox: Path):
    rel = f"{CONTRACT_DIR}/ADR-SB-001.contract.json"
    doc = load(sandbox, rel)
    doc["runtime_claims_permitted"] = True
    save(sandbox, rel, doc)
    assert_guard(sandbox, "A37-no-runtime-or-implementation-authority")


def test_accepted_status_token_fails(sandbox: Path):
    rel = f"{CONTRACT_DIR}/ADR-SB-001.contract.json"
    doc = load(sandbox, rel)
    doc["adr_status_at_contract_authoring"] = "ACCEPTED"
    save(sandbox, rel, doc)
    assert_guard(sandbox, "A36-no-accepted-token")


def test_candidate_document_tamper_fails(sandbox: Path):
    p = sandbox / CANDIDATE
    p.write_text(p.read_text(encoding="utf-8") + "\n<!-- drift -->\n",
                 encoding="utf-8")
    assert_guard(sandbox, "A04-candidate-sha256")


def test_sb_dec_reference_removal_fails(sandbox: Path):
    rel = f"{CONTRACT_DIR}/ADR-SB-009.contract.json"
    doc = load(sandbox, rel)
    doc["sb_dec_references"] = doc["sb_dec_references"][:-1]
    save(sandbox, rel, doc)
    assert_guard(sandbox, "A17-sb-dec-references-match-candidate")


# --------------------------------------------------------------------------
# Semantic pins
# --------------------------------------------------------------------------

def test_open_loop_pm_denial_removal_fails(sandbox: Path):
    doc = load(sandbox, OPEN_LOOP)
    doc["not"]["anyOf"] = [
        e for e in doc["not"]["anyOf"] if e["required"][0] != "assignee"
    ]
    doc["x-grounding"] = {
        k: v for k, v in doc["x-grounding"].items() if not k.startswith("/not/anyOf/")
    }
    save(sandbox, OPEN_LOOP, doc)
    assert_guard(sandbox, "S04-open-loop-denies-all-eight-pm-semantics")


def test_task_promotion_enabled_fails(sandbox: Path):
    doc = load(sandbox, PROMOTION)
    doc["properties"]["disabled"]["const"] = False
    save(sandbox, PROMOTION, doc)
    assert_guard(sandbox, "S06-task-promotion-disabled")


def test_dropping_a_promotion_precondition_fails(sandbox: Path):
    doc = load(sandbox, PROMOTION)
    doc["required"] = [r for r in doc["required"] if r != "explicit_approval"]
    doc["x-grounding"] = {
        k: v for k, v in doc["x-grounding"].items() if k != "/required/2"
    }
    save(sandbox, PROMOTION, doc)
    assert_guard(sandbox, "S07-promotion-requires-both-proofs-and-approval")


def test_identity_source_allowed_back_in_fails(sandbox: Path):
    doc = load(sandbox, ENVELOPE)
    doc["not"]["anyOf"] = [
        e for e in doc["not"]["anyOf"] if e["required"][0] != "ports"
    ]
    doc["x-grounding"] = {
        k: v for k, v in doc["x-grounding"].items() if not k.startswith("/not/anyOf/")
    }
    save(sandbox, ENVELOPE, doc)
    assert_guard(sandbox, "S13-identity-sources-rejected")


def test_multi_project_capture_enabled_fails(sandbox: Path):
    doc = load(sandbox, ENVELOPE)
    doc["properties"]["multi_project_background_capture"]["const"] = True
    save(sandbox, ENVELOPE, doc)
    assert_guard(sandbox, "S15-multi-project-capture-disabled")


def test_raising_the_visible_queue_maximum_fails(sandbox: Path):
    mutate_clause(sandbox, "ADR-SB-010-C03", machine_value=20)
    validator = repin(sandbox)
    assert_guard(sandbox, "S17-visible-queue-max-7", validator)


def test_residual_count_above_zero_fails(sandbox: Path):
    mutate_clause(sandbox, "ADR-SB-007-C07", machine_value=5)
    validator = repin(sandbox)
    assert_guard(sandbox, "S21-searchable-residual-zero", validator)


def test_dropping_purge_completion_receipt_fails(sandbox: Path):
    mutate_clause(sandbox, "ADR-SB-007-C13", machine_value=False)
    validator = repin(sandbox)
    assert_guard(sandbox, "S22-purge-completion-receipt-required", validator)


def test_conport_owning_task_state_fails(sandbox: Path):
    mutate_clause(sandbox, "ADR-SB-008-C34", machine_value=True)
    validator = repin(sandbox)
    assert_guard(sandbox, "S09-conport-never-owns-task-state", validator)


def test_dope_memory_granted_pm_authority_fails(sandbox: Path):
    mutate_clause(sandbox, "ADR-SB-008-C30", machine_value=True)
    validator = repin(sandbox)
    assert_guard(sandbox, "S10-dope-memory-no-pm-authority", validator)


def test_loop_event_kind_dropped_fails(sandbox: Path):
    mutate_clause(sandbox, "ADR-SB-008-C22", machine_value=["OPEN", "CLOSE"])
    validator = repin(sandbox)
    failures = assert_guard(sandbox, "S10-loop-event-kinds-exact", validator)
    assert "A26-closed-sets-bidirectional" in failures


def test_policy_dimension_dropped_fails(sandbox: Path):
    mutate_clause(
        sandbox, "ADR-SB-004-C09",
        machine_value=["IDENTITY", "GRANTS", "PROVIDER", "EMBEDDING", "CUSTODY",
                       "BACKUP"],
    )
    validator = repin(sandbox)
    failures = assert_guard(sandbox, "S12-policy-dimensions-complete", validator)
    assert "A26-closed-sets-bidirectional" in failures


def test_historical_current_distinction_dropped_fails(sandbox: Path):
    mutate_clause(sandbox, "ADR-SB-003-C12", machine_value=False)
    validator = repin(sandbox)
    assert_guard(sandbox, "S24-historical-and-current-distinct", validator)


def test_confidential_spooling_enabled_fails(sandbox: Path):
    doc = load(sandbox, SPOOL)
    doc["assertions"][
        "confidential_restricted_remain_disabled_until_verified_encryption_and_"
        "key_ownership"
    ] = False
    save(sandbox, SPOOL, doc)
    assert_guard(sandbox, "S02-confidential-restricted-spool-disabled")


def test_unknown_class_spooling_enabled_fails(sandbox: Path):
    doc = load(sandbox, SPOOL)
    doc["assertions"]["no_unknown_class_spooling"] = False
    save(sandbox, SPOOL, doc)
    assert_guard(sandbox, "S03-unknown-class-spooling-denied")


# --------------------------------------------------------------------------
# FO-01
# --------------------------------------------------------------------------

def test_fo01_unclassified_field_fails(sandbox: Path):
    """A new authoritative-looking field with no check behind it."""
    status = load(sandbox, FO01_STATUS)
    status["independent_verification"]["second_audit_verdict"] = "PASS"
    save(sandbox, FO01_STATUS, status)
    assert_guard(sandbox, "B11-every-status-field-classified")


def test_fo01_acceptance_authorization_flip_fails(sandbox: Path):
    status = load(sandbox, FO01_STATUS)
    status["adr_acceptance_authorized"] = True
    save(sandbox, FO01_STATUS, status)
    failures = assert_guard(sandbox, "B05-adr-acceptance-not-authorized")
    assert "B02-receipt-projection-exact" in failures


def test_fo01_gate_opened_fails(sandbox: Path):
    status = load(sandbox, FO01_STATUS)
    status["gates"]["adr_acceptance"] = "OPEN"
    save(sandbox, FO01_STATUS, status)
    assert_guard(sandbox, "B03-pinned-fields-unchanged")


def test_fo01_merge_authorization_flip_fails(sandbox: Path):
    status = load(sandbox, FO01_STATUS)
    status["gates"]["merge"] = "AUTHORIZED"
    save(sandbox, FO01_STATUS, status)
    assert_guard(sandbox, "B07-merge-not-authorized")


def test_fo01_not_run_downgrade_fails(sandbox: Path):
    status = load(sandbox, FO01_STATUS)
    status["preserved_not_run"]["purge_completeness"] = "PASS"
    save(sandbox, FO01_STATUS, status)
    assert_guard(sandbox, "B02-receipt-projection-exact")


def test_fo01_missing_traceability_matrix_fails(sandbox: Path):
    (sandbox / TRACEABILITY).unlink()
    assert_guard(sandbox, "B08-traceability-matrix-present")


def test_fo01_coverage_drift_from_matrix_fails(sandbox: Path):
    status = load(sandbox, FO01_STATUS)
    status["coverage"]["decisions_linked"] = 99
    save(sandbox, FO01_STATUS, status)
    assert_guard(sandbox, "B08-coverage-matches-traceability-matrix")


# --------------------------------------------------------------------------
# Fail-closed behaviour
# --------------------------------------------------------------------------

def test_missing_inventory_fails_closed(sandbox: Path):
    (sandbox / INVENTORY).unlink()
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "A08-inventory-present" in failed_checks(payload)


def test_unparseable_artifact_fails_closed(sandbox: Path):
    (sandbox / COVERAGE).write_text("{ not json", encoding="utf-8")
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "A02-all-artifacts-parse" in failed_checks(payload)


def test_semantic_group_not_silently_skipped(sandbox: Path):
    """If group A stops early, group S must fail rather than vanish."""
    (sandbox / INVENTORY).unlink()
    code, payload = run_validator(sandbox)
    assert code != 0
    assert "S00-not-reached" in failed_checks(payload)


def test_bad_repo_root_is_usage_error():
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR), "--repo-root", "/nonexistent-xyz"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 2
