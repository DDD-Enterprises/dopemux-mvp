# Prompt 6 Bundle — Risk / UNKNOWN Ledger (main `817d9d227`)

| ID | Severity | Status | Detail |
|----|----------|--------|--------|
| R1 | HIGH (deferred) | TRACKED | **0007 trusted input-provenance not implemented.** Caller-asserted provenance/authority is still trusted by the `classify` projection and by `RouteDecision.from_dict`. No runtime executor consumes runnable output today → not a live exploit, but it is the named blocker before ANY execution surface. Docs packets #908/#909 merged; implementation pending. |
| R2 | LOW | TRACKED | `recommend-backend` CLI deserializes a forged `RouteDecision` into the **inert** `select_backend_policy` (advisory only, no execution). Scoped to 0007 (commit `0c521642c`). |
| R3 | LOW (OBS) | DEFERRED → 0007 | CLI `has_unknown_authority` clearing uses coercible `bool()` (e.g. `0`/`""` → False), unlike the strict trust-raising parse for `exact_source_fetched`/`has_backend_wrapper_proof`. It is an authority signal, not a provenance flag, and the surface is projection-only. Operator decision (2026-06-17): leave for 0007, do not fold into #923. |
| R4 | TRIVIAL | OPEN (pre-existing) | `ruff check` on the broader DCP path reports 3 unused-import nits in **unrelated** files: `src/dopemux/dcp/red_lane_scanner.py:4` (typing imports), `tests/unit/dcp/test_routing_model.py:23` (`pytest`). Not introduced by #923 (changed files are ruff-clean). Auto-fixable. |
| R5 | INFO | RESOLVED | #906 F1/F2 forged-decision gaps — CLOSED by #923 (`817d9d227`): passive lanes use a read-only allowlist; executability gate fails closed on `decision.unknowns`. |

## Confidence
- **Lane engine MVP correctness on current main:** HIGH (165 DCP tests pass; F1/F2 reproduced RED→GREEN; classifier invariant `unknowns ⟹ not ALLOWED` independently verified).
- **Execution safety today:** HIGH conditional — safe because nothing executes `LaneDecision` yet.
- **Execution safety for future surfaces:** GATED on 0007 (R1).
