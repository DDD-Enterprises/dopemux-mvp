#!/usr/bin/env python3
"""Record the operator's mandated false-green matrix as a proof artifact.

Each row is executed, not asserted: the test that implements the mutation is
run on its own and its outcome recorded, together with the guard that test
requires to fire. The test helper fails unless that specific guard is among
the validator's failures, so a green row means the intended guard caught it —
not that something unrelated did.
"""

from __future__ import annotations

import ast
import json
import os
import re
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
TESTS = ROOT / "tests/governance/test_second_brain_adr_contracts.py"
PROOF = ROOT / "proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001"
PY = sys.executable

# operator matrix line -> implementing test
MATRIX = [
    ("inventory + contract bilateral change",
     "test_m01_bilateral_inventory_and_contract_change", "plain"),
    ("authority-first -> vector-first",
     "test_m02_authority_first_inverted", "repinned"),
    ("DEFER/NO MUTATION -> auto-apply",
     "test_m03_review_default_becomes_auto_apply", "repinned"),
    ("drop PURGE from a closed set",
     "test_m04_drop_purge_from_closed_set", "repinned"),
    ("drop Review from UX operations",
     "test_m05_drop_review_from_ux_operations", "repinned"),
    ("add dopeTask as canonical authority",
     "test_m06_add_invented_canonical_authority", "repinned"),
    ("add cloud_offload to CustodyPort",
     "test_m07_add_cloud_offload_to_custody_port", "plain"),
    ("invent unsupported schema enum/property",
     "test_m08_invent_schema_property_and_enum", "plain"),
    ("remove each newly-added MUST_FIX-1 denominator clause",
     "test_m09_remove_each_newly_added_denominator_clause", "plain"),
    ("alter FO-01 receipt-derived field",
     "test_m10_alter_each_fo01_receipt_derived_field", "plain"),
]

SUPPORTING = [
    "test_m09b_removed_clause_survives_a_repin",
    "test_repinned_pristine_still_passes",
]


def guards_of(tree: ast.Module, name: str) -> list[str]:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            src = ast.get_source_segment(TESTS.read_text(encoding="utf-8"), node) or ""
            return re.findall(r'assert_guard\([^,]+,\s*"([^"]+)"', src) + \
                re.findall(r'assert "([^"]+)" in failures', src)
    raise SystemExit(f"FAIL: test {name} not found")


def run_one(name: str) -> tuple[str, str]:
    proc = subprocess.run(
        [PY, "-m", "pytest", f"{TESTS}::{name}", "-q", "--no-header"],
        cwd=ROOT, capture_output=True, text=True,
    )
    return ("FAILED_AS_INTENDED" if proc.returncode == 0 else "MATRIX_ROW_DID_NOT_HOLD",
            proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else "")


def main() -> int:
    tree = ast.parse(TESTS.read_text(encoding="utf-8"))
    rows = []
    for label, test, mode in MATRIX:
        guards = guards_of(tree, test)
        outcome, tail = run_one(test)
        rows.append({
            "mutation": label,
            "adversary_mode": mode,
            "implementing_test": f"tests/governance/{TESTS.name}::{test}",
            "intended_guard": guards[0] if guards else None,
            "additional_guards_asserted": guards[1:],
            "result": outcome,
            "pytest_summary": tail,
        })
        print(f"  {outcome:26s} {label}")

    support = []
    for test in SUPPORTING:
        outcome, tail = run_one(test)
        support.append({
            "test": f"tests/governance/{TESTS.name}::{test}",
            "intended_guard": (guards_of(tree, test) or [None])[0],
            "result": outcome if test != "test_repinned_pristine_still_passes"
            else ("CONTROL_PASSES" if outcome == "FAILED_AS_INTENDED"
                  else "CONTROL_BROKEN"),
            "pytest_summary": tail,
        })
        print(f"  {support[-1]['result']:26s} {test}")

    doc = {
        "schema_version": "1.0.0",
        "task_id": "TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001",
        "record_kind": "FALSE_GREEN_MATRIX",
        "purpose": (
            "The ten mutations the operator required to be proven to fail, "
            "before a fresh independent audit. Each row names the guard its "
            "test requires to fire; the test helper fails unless that guard is "
            "among the validator's reported failures, so an unrelated parse "
            "error cannot take credit for catching a mutation."
        ),
        "adversary_modes": {
            "plain": (
                "Artifacts edited. The const-pinned frozen denominator catches "
                "any clause change, however consistently applied across files."
            ),
            "repinned": (
                "The pin inside the validator and the supersession receipt are "
                "rewritten too, so the freeze no longer objects. This is what "
                "tests whether the semantic guards do independent work — the "
                "first audit's BLOCKER 1 lived here."
            ),
        },
        "no_silent_caps": (
            "Row 9 loops over every one of the 63 clauses the re-freeze added, "
            "not a sample. Row 10 loops over every one of the 39 receipt-derived "
            "FO-01 fields. Neither is truncated."
        ),
        "rows": rows,
        "supporting_controls": support,
        "all_rows_held": all(r["result"] == "FAILED_AS_INTENDED" for r in rows),
    }
    (PROOF / "FALSE_GREEN_MATRIX.json").write_text(
        json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"\nall_rows_held: {doc['all_rows_held']}")
    return 0 if doc["all_rows_held"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except BaseException as exc:  # fail closed
        print(f"FAIL: unhandled {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(2)
