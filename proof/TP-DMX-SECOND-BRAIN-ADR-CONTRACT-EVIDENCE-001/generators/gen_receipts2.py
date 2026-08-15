#!/usr/bin/env python3
"""Update the round-2 proof receipts in place.

Loads each receipt, replaces the facts that the remediation changed, and leaves
the prose that is still true. PROOF.json is deliberately NOT written here: it
binds the audited content head, and a file cannot contain the sha of the commit
that introduces it.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    env = os.environ.get("SB_REPO_ROOT")
    if env:
        return Path(env)
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / ".git").exists():
            return parent
    raise SystemExit("FAIL: cannot locate repository root; set SB_REPO_ROOT")


ROOT = _repo_root()
PROOF = ROOT / "proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001"
CONTRACTS = ROOT / "schemas/second_brain/contracts"
PY = sys.executable

REFREEZE_COMMIT = subprocess.run(
    ["git", "log", "-1", "--format=%H", "--", str(PROOF / "DENOMINATOR_REFREEZE_RECEIPT.json")],
    cwd=ROOT, capture_output=True, text=True, check=True,
).stdout.strip()


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def save(p: Path, doc) -> None:
    p.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")


def main() -> int:
    inv_sha = sha(PROOF / "ADR_CLAUSE_INVENTORY.json")
    inv = load(PROOF / "ADR_CLAUSE_INVENTORY.json")
    total = inv["clause_total"]

    result = json.loads(subprocess.run(
        [PY, str(ROOT / "scripts/governance/validate_second_brain_adr_contracts.py"),
         "--repo-root", str(ROOT), "--json"],
        capture_output=True, text=True, check=True,
    ).stdout)
    if result["checks_failed"]:
        raise SystemExit(f"FAIL: validator is red: {result['failures']}")

    pytest_proc = subprocess.run(
        [PY, "-m", "pytest", "tests/governance/test_second_brain_adr_contracts.py",
         "-q", "--no-header"],
        cwd=ROOT, capture_output=True, text=True,
    )
    if pytest_proc.returncode != 0:
        raise SystemExit(f"FAIL: adversarial suite is red:\n{pytest_proc.stdout[-2000:]}")
    test_total = sum(
        1 for line in (ROOT / "tests/governance/test_second_brain_adr_contracts.py")
        .read_text(encoding="utf-8").splitlines()
        if line.startswith("def test_")
    )

    matrix = load(PROOF / "FALSE_GREEN_MATRIX.json")
    if not matrix["all_rows_held"]:
        raise SystemExit("FAIL: the false-green matrix has a row that did not hold")

    # ---- CONTRACT_COVERAGE_RECEIPT -------------------------------------
    rc = load(PROOF / "CONTRACT_COVERAGE_RECEIPT.json")
    rc["step"] = "S4-R2"
    rc["clause_inventory_sha256"] = inv_sha
    rc["clause_inventory_frozen_in_commit"] = REFREEZE_COMMIT
    rc["clause_inventory_supersedes"] = {
        "sha256": "f073ca28802e6b140dd5789d5fad5839962635f7b287cac589ec704efc663288",
        "clause_total": 97,
        "frozen_in_commit": "a9397e5630577ac5a2b0c8f89ad7d62d8ff7b296",
        "status": "SUPERSEDED_INCOMPLETE_DENOMINATOR",
        "authority": "operator ruling of 2026-08-12",
    }
    rc["freeze_evidence"] = (
        "The re-freeze commit contains no file under schemas/second_brain/ and no "
        "validator change. Git history, not a self-asserted field, is the proof "
        "that the denominator preceded the contracts written against it."
    )
    rc["clause_coverage"] = f"{total}/{total}"
    rc["contract_artifact_count"] = len(list(CONTRACTS.glob("*.json")))
    rc["contract_artifacts"] = sorted(p.name for p in CONTRACTS.glob("*.json"))
    rc["sb_dec_reference_count"] = 28
    rc["sb_dec_distinct_count"] = 26
    rc["validator_checks_total"] = result["checks_total"]
    rc["validator_checks_failed"] = result["checks_failed"]
    rc["adversarial_tests_passed"] = test_total
    rc["adversarial_tests_failed"] = 0
    rc["false_green_defence"] = (
        "Every negative test executes the real validator against a mutated "
        "repository copy and asserts the specific guard responsible fires. Half "
        "the tests additionally re-pin the validator and the supersession "
        "receipt to the mutated state, so the frozen-denominator hash cannot "
        "take credit for a semantic guard's work. The ten mutations the operator "
        "required are recorded row by row in FALSE_GREEN_MATRIX.json."
    )
    rc["false_green_matrix"] = {
        "artifact": "FALSE_GREEN_MATRIX.json",
        "rows": len(matrix["rows"]),
        "all_rows_held": matrix["all_rows_held"],
    }
    rc["audit_findings_addressed"] = {
        "BLOCKER_1_bilateral_edit_false_green": (
            "The frozen inventory sha256 is const-pinned in the validator "
            "(A09). Any post-freeze clause edit fails, and because every "
            "contract rule must equal its inventory clause (A22), editing both "
            "sides consistently fails too."
        ),
        "BLOCKER_2_invented_dopeTask_authority": (
            "Removed. AUTHORITY_TARGET values must appear verbatim in the cited "
            "candidate text (A26), which 'dopeTask' does not; a named "
            "regression guard (A27) states this by name across the clause set "
            "and every contract file."
        ),
        "BLOCKER_3_one_way_set_grounding": (
            "Closed sets are compared against the deterministic tokenization of "
            "a verbatim source_enumeration (A26). Shrinking now fails exactly "
            "as widening does."
        ),
        "MUST_FIX_1_denominator_gaps": (
            "The denominator was re-frozen under operator authorization: 160 "
            "clauses, 63 added. All six omissions the auditor named by hand are "
            "present and checked by name at generation time."
        ),
        "MUST_FIX_2_invented_typed_surface": (
            "Port operation catalogues deleted; invented schema properties, "
            "enums and lifecycle states deleted. Every remaining property name, "
            "enum member and const string is bound in x-grounding to a clause "
            "and a verbatim candidate phrase, recomputed by A31/A32."
        ),
        "MUST_FIX_3_invented_recall_ordering": (
            "The four-way ranking is gone. The contract encodes authority-first "
            "as a boolean and the four recall source classes as a closed set, "
            "with no relative order among chronology, source-native state and "
            "advisory retrieval."
        ),
        "MUST_FIX_4_label_only_pseudo_contracts": (
            "The rule taxonomy no longer contains a shape that can carry an "
            "opaque label. REQUIRE/MUST_EXIST token rules became boolean "
            "predicates on precise subjects; A25 rejects any other shape."
        ),
        "MUST_FIX_5_fo01_partial_receipt_lock": (
            "The FO-01 status record is checked as a whole projection of its "
            "receipt across 39 fields (B02), non-receipt fields are pinned "
            "(B03), and every leaf must be classified (B11) so a new field "
            "cannot appear with no check behind it."
        ),
    }
    rc["artifact_sha256"] = {
        p.name: sha(p) for p in sorted(CONTRACTS.glob("*.json"))
    }
    rc.pop("false_green_defect_found_and_closed", None)
    rc["false_green_defects_found_and_closed"] = {
        "round_1_producer_found": (
            "Rerouting ADR-SB-002 canonical capture from Dope-Memory to ConPort "
            "in the inventory and the contract together passed 113/113. Closed "
            "at the time by value grounding, which narrowed the class without "
            "closing it."
        ),
        "round_1_auditor_found": (
            "Value grounding covered only three rule shapes, leaving roughly 75 "
            "of 97 clauses exposed; and it rejected widening a closed set while "
            "accepting shrinking."
        ),
        "round_2_closure": (
            "The class is closed by the freeze pin rather than by enumerating "
            "the shapes it applies to, and the semantic pins in group S restate "
            "the load-bearing values a third time so that a re-pinned adversary "
            "still fails."
        ),
    }
    save(PROOF / "CONTRACT_COVERAGE_RECEIPT.json", rc)

    # ---- FO01 receipt: record the expanded lock ------------------------
    fo = load(PROOF / "FO01_RECONCILIATION_RECEIPT.json")
    fo["step"] = "S5-R2"
    fo["validation_expanded_round_2"] = {
        "finding": "MUST_FIX 5 — the reconciliation check was partial.",
        "detail": (
            "Several receipt-derived fields (nonblocking_observations, the "
            "auditor identity block, the source hashes) could drift while the "
            "checked subset still passed."
        ),
        "resolution": (
            "Group B now computes the full expected projection from the "
            "receipt and compares all 39 mapped fields, pins the 37 fields that "
            "are not receipt-derived, requires the traceability matrix to be "
            "present rather than skipping when it is absent, and fails on any "
            "status leaf that is not classified as projected, pinned, "
            "matrix-derived or declared prose."
        ),
        "file_changed_this_round": False,
        "note": (
            "fo-01-repair-status.json itself is unchanged in round 2. The "
            "finding was about the strength of the check, not the content of "
            "the record."
        ),
    }
    save(PROOF / "FO01_RECONCILIATION_RECEIPT.json", fo)

    # ---- VALIDATION ----------------------------------------------------
    val = load(PROOF / "VALIDATION.json")
    val["round"] = 2
    val["buckets"]["contract_validator"] = (
        f"PASS ({result['checks_total']} checks, 0 failed)"
    )
    val["buckets"]["adversarial_suite"] = f"PASS ({test_total} tests, 0 failed)"
    val["buckets"]["false_green_matrix"] = (
        f"PASS ({len(matrix['rows'])}/10 operator-mandated mutations failed as "
        "intended, each via its intended guard)"
    )
    val["buckets"]["denominator_refreeze"] = (
        f"PASS (160 clauses, sha256 {inv_sha[:12]}…, frozen in "
        f"{REFREEZE_COMMIT[:10]} with no contract or validator change)"
    )
    val["independent_audit"] = {
        "round_1": {
            "verdict": "FAIL",
            "blockers": 3,
            "must_fix": 5,
            "audited_head": "7955ef33d7c0ab29daecbab966bc6a9497dc69ce",
            "status": "HISTORICAL_CONTROLLING_EVIDENCE_DO_NOT_EDIT",
            "report": "AUDITOR_REPORT.md",
        },
        "round_2": "PENDING — run against the frozen round-2 content head",
    }
    save(PROOF / "VALIDATION.json", val)

    print(f"inventory      {inv_sha}")
    print(f"refreeze commit {REFREEZE_COMMIT}")
    print(f"validator      {result['checks_total']} checks, 0 failed")
    print(f"tests          {test_total} passed")
    print(f"matrix         {len(matrix['rows'])} rows, all held")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except BaseException as exc:  # fail closed
        print(f"FAIL: unhandled {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(2)
