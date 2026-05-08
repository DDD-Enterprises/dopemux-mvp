# OPEN_PR_AUDIT — TP-DMX-COCKPIT-MAIN-STATE-RECON-001

As of 2026-05-07. **5 open PRs.** No PRs were merged, retargeted, edited, or closed by this packet.

## Summary

| Bucket | PRs |
| --- | --- |
| OPEN_RELEVANT (Cockpit runtime surface) | #573 |
| OPEN_STACKED (Cockpit governance artifact) | #572 |
| OPEN_UNRELATED | #582, #583, #584 |
| NEEDS_HUMAN_DECISION | #572, #573 |

## #572 — docs(cockpit): prepare merge stack consolidation (OPEN_STACKED)

- **Base**: `pack/cockpit-pack-remediate-006-ia` · **Head**: `codex/cockpit-merge-stack-consolidate-001` (`23ec8b70f`).
- **CI**: all SUCCESS or SKIPPED. **GitHub mergeable**: yes. **Review**: not decided.
- **Touched paths (artifact-only)**:
  - `task-packets/generated/TP-DMX-COCKPIT-MERGE-STACK-CONSOLIDATE-001.json`
  - `task-packets/INDEX.md`
  - `tests/unit/dopemux/ui/cockpit/test_merge_stack_artifacts.py`
  - `out/cockpit-merge-stack/TP-DMX-COCKPIT-MERGE-STACK-CONSOLIDATE-001/**`
  - `proof/cockpit-merge-stack/TP-DMX-COCKPIT-MERGE-STACK-CONSOLIDATE-001/README.md`
- **Cockpit impact**: documents stack readiness for PRs 568–571. The PR is artifact-only and read-mostly; per its own body it performed no PR merges, no retargets, no rebase, no force push, no branch deletion.
- **Design impact**: PR explicitly preserves `safe_for_claude_design: NO` and `READY_FOR_CLAUDE_DESIGN: not approved`.
- **Proof / governance impact**: introduces a new merge-stack proof tree and flags Settings/Admin per-row tier mapping and inventory aggregate residual risks.
- **Verdict (PR-self-reported)**: `READY_WITH_RISKS_NEEDS_LEDGER_DECISION`. The PR explicitly states it is **not** merge authorization.
- **Recommended action**: route the verdict to the Ledger before any operator-initiated consolidation of pack into main. **Do not let this PR's stack-readiness verdict imply main readiness.** It does not audit PR #573.
- **Blocks Cockpit design pickup**: YES.

## #573 — fix(cockpit): repair runtime contract fidelity gaps (OPEN_RELEVANT)

- **Base**: `pack/cockpit-pack-remediate-006-ia` · **Head**: `codex/cockpit-runtime-contract-fidelity-001` (`1236757c1`).
- **CI**: all SUCCESS or SKIPPED. **GitHub mergeable**: yes. **Review**: not decided.
- **Touched paths** (status `M` for source/tests, `A` for new packet/proof artifacts):
  - `src/dopemux/ui/cockpit/runtime_contract.py` — **modifies** existing Cockpit runtime surface (file first introduced by PR 568 commit `ea640b47b`).
  - `tests/unit/dopemux/ui/cockpit/test_runtime_contract.py` — modifies existing tests.
  - `tests/unit/dopemux/ui/cockpit/test_inventory_regen_artifacts.py` — modifies existing tests.
  - `task-packets/generated/TP-DMX-COCKPIT-RUNTIME-CONTRACT-FIDELITY-001.json`
  - `task-packets/INDEX.md`
  - `out/cockpit-runtime-contract-fidelity/TP-DMX-COCKPIT-RUNTIME-CONTRACT-FIDELITY-001/PROOF.json`
  - `proof/cockpit-runtime-contract-fidelity/TP-DMX-COCKPIT-RUNTIME-CONTRACT-FIDELITY-001/README.md`
- **Cockpit impact**: changes Cockpit runtime contract for EXTERNAL_ONLY gating, canonical action-row hashing, receipt lifecycle fields, palette_request_id nullability, gate_request_id stability, UNKNOWN aggregate counting, redaction-before-hash queue IDs, deterministic package-dir resolution, and inventory metadata tests.
- **Design impact**: PR explicitly preserves `safe_for_claude_design: NO` and `READY_FOR_CLAUDE_DESIGN: not approved`. Runtime renderer surface remains non-executing.
- **Proof / governance impact**: adds packet-owned proof tree.
- **Stack relationship**: stacked on top of PRs 568–571 already merged into pack. **PR #572 does not reference PR #573**, and **PR #573 does not reference PR #572**. The merge-stack consolidation packet did **not** audit this runtime-contract surface.
- **Recommended action**: must be audited before any operator-initiated consolidation of pack into main; consolidation packet must be regenerated to include #573.
- **Blocks Cockpit design pickup**: YES.

## #582 — chore(deps): bump the pip group across 7 directories (OPEN_UNRELATED)

Dependabot. Touches MCP and service `requirements.txt` files only. No cockpit src or tests. Process via standard dependency review track. Does not block design pickup.

## #583 — chore(deps): bump the uv group across 8 directories (OPEN_UNRELATED)

Dependabot. Touches root `pyproject.toml`, `uv.lock`, MCP server lock/requirements files. No cockpit src or tests. Process via standard dependency review track. Does not block design pickup.

## #584 — chore(mcp): apply PR #576 review follow-ups (OPEN_UNRELATED)

- **Base**: `main` · **Head**: `chore/pr576-followups` (`af6d325f6`). **GitHub mergeable**: yes.
- **Touched paths**:
  - `.claude/modules/coordination/authority-matrix.md` — single-line update of a stale `pm-plane/...` reference; no Cockpit, Claude Design, T4, or Safe Action rows touched.
  - `src/dopemux/commands/mcp_commands.py` — comment-only documentation of port-hash collision math and `_port_is_free` semantics inversion.
  - `tests/unit/test_mcp_commands_catalog.py` — five new MCP CLI tests.
- **Cockpit impact**: none observed.
- **Recommended action**: process via MCP review track. Does not block design pickup.

## Cross-cutting non-actions

- no PR merges performed
- no PR retargeting performed
- no PR edits performed
- no PR closes performed
- no rebases performed
- no force pushes performed
- no branch deletions performed
