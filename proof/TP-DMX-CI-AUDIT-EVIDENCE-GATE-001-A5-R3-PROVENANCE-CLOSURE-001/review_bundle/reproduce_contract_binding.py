"""Read-only counterexamples to canonical NOT_REQUIRED contract binding.

Run at the recorded head with PYTHONPATH=.:src using the repo test environment.
No network, model calls, or repository writes. Exit zero means gap reproduced.
"""
import copy
import json
import subprocess

from scripts.audit.run_embedded_audit import (
    build_evidence_gate_proof,
    independent_audit_errors,
)

REPO = "DDD-Enterprises/dopemux-mvp"
HEAD = "13562c8df1bc6621229eb4a38473da42be199825"
BASE = "6a728f74c0311967f83213513308f97613e3f28d"

actual_head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
assert actual_head == HEAD, "Replay subject mismatch"
proof = build_evidence_gate_proof(
    packet_id="TP-PROVENANCE-READONLY-PROBE",
    repo=REPO,
    pr_number=1330,
    head_sha=HEAD,
    base_sha=BASE,
    change_contract={"status": "PASS", "model_audit_required": False, "max_lane": "L0"},
    local_attestation=None,
    generated_at="2026-09-07T12:00:00Z",
)
cases = {"baseline": copy.deepcopy(proof)}
for field in ("head_sha", "base_sha"):
    for mutation in ("foreign", "missing", "malformed"):
        value = copy.deepcopy(proof)
        contract = value["provenance"]["change_contract"]
        if mutation == "missing":
            contract.pop(field)
        elif mutation == "foreign":
            contract[field] = "f" * 40
        else:
            contract[field] = {"bad": "shape"}
        cases[f"{mutation}_contract_{field}"] = value
cases["missing_provenance"] = copy.deepcopy(proof)
cases["missing_provenance"].pop("provenance")
for field, value in (("repo", "foreign/repo"), ("pr_number", 1331), ("head_sha", "f" * 40)):
    cases[f"foreign_top_level_{field}"] = copy.deepcopy(proof)
    cases[f"foreign_top_level_{field}"][field] = value
results = {
    name: independent_audit_errors(
        value, expected_repo=REPO, expected_pr=1330, expected_head_sha=HEAD
    )
    for name, value in cases.items()
}
assert not results["baseline"]
assert all(not errors for name, errors in results.items() if "_contract_" in name)
assert results["missing_provenance"]
assert all(errors for name, errors in results.items() if "top_level" in name)
print(json.dumps({
    "subject_head": HEAD,
    "status": "GAP_REPRODUCED",
    "interpretation": "Exit zero confirms counterexamples, not security PASS.",
    "results": results,
}, indent=2, sort_keys=True))
