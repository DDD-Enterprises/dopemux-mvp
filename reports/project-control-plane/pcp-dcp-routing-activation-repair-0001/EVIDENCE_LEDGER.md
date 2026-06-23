# Evidence Ledger

| CLAIM_ID | LABEL | CLAIM | EVIDENCE | CONFIDENCE |
|---|---|---|---|---|
| C1 | OBSERVED | Unsigned READY cannot reach writer when registry active | `test_live_write_ready_auth.py`, `assertion_auth.py` | VERIFIED |
| C2 | OBSERVED | Writer requires SOURCE authority-map binding | `test_bridge_authority_binding.py`, `authority_binding.py` | VERIFIED |
| C3 | OBSERVED | DCP proof family mapping exists and validates | `proof_family.dcp.json`, `test_dcp_proof_family.py` | VERIFIED |
| C4 | OBSERVED | SELECTED route cannot use unknown provider/model/runner (schema) | `route_decision.schema.json`, routing fixtures | VERIFIED |
| C5 | OBSERVED | PR Steward READY blocked on incomplete intake | `pr_steward.py`, `test_pr_steward.py::TestIntakeCompleteness` | VERIFIED |
| C6 | OBSERVED | Installed wheel imports `dopemux.pcp` | `test_packaging_pcp.py` | VERIFIED |
| C7 | OBSERVED | Top-level `dopemux` CLI has no live-write commands | `test_pcp_inert_wiring.py` | VERIFIED |
| C8 | OBSERVED | All targeted tests pass | `TEST_RESULTS.md` (exit 0) | VERIFIED |
| C9 | INFERRED | Runtime routers may bypass DCP route schema unless integrated | embedded audit remaining_risks | MEDIUM |