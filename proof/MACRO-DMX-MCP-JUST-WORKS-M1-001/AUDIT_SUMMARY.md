# MACRO-DMX-MCP-JUST-WORKS-M1-001 — proof summary

**Status:** READY_FOR_AUDIT_ADJUDICATION — three independent audit routes ran at the frozen head; two returned PASS_WITH_RISKS, one FAIL; the governing pick is the operator's. Merge, push and PR are owner-gated and not performed.

## Change Summary
Branch `feat/mcp-just-works-m1`, audited head `30b0fdec996fcd782bf2f816900f9ff4dabd4c01` (21 branch-authored commits after the merged PR #1439/#1459 heads; base for judgement `5742575c4`). Per-worktree MCP that needs zero typing: `.mcp.json` entries launch each server through `${DOPEMUX_BIN:-dopemux} mcp launch <name>` (SDK stdio proxy, on-demand lifecycle start, orchestrator ownership gate under a reserved-port flock, ownership re-verified before the first session, before every reconnect and after every initialize); git-only identity with `--trust-env`; hooks dispatcher resolved from the hook cwd; flock locks with inode re-check, non-blocking variants for automatic paths; sibling-aware lease allocation that heals collisions; automatic ConPort tenant resolution and provisioning (secrets file 0600, SCRAM verifier, two-phase gate via `docker exec --env-file`, per-migration resume, unknown history fails closed); bounded, kill-switchable reap-only cleanup from hooks and launcher starts; `switch-project`, `reap`, `init --repo`; shared image tags per service and Dockerfile version; docs (how-to rewrite, AGENTS.md §12, CLAUDE.md, append-only design/plan amendments).

## Authority Used
Owner instructions: design approved (D5 Option A); "subagent-driven. audit with astra, argon 4, and grok 4.7"; "reinstall dopemux and proceed"; model routing directive (opus/sonnet/haiku); "do it" for the Docker image prune. MacroPacket `MACRO-DMX-MCP-JUST-WORKS-M1-001` (TP_ROUTE blocks in the plan workspace). The owner pin on codex outranks the CLAUDE.md "Codex never the §9.1 auditor" default for route 1; the repo schema's `auditor_tool` enum has no codex entry, so the codex return is filed as informal evidence and the schema-valid `embedded_audit` record carries the AGY route.

## Analysis Performed
SDD loop: fresh implementer per task, per-task review (sonnet/opus), fix rounds with scoped re-reviews, final whole-branch opus review ("with fixes"), one consolidated fix round plus a residual round, then three audit freezes: eb3f0624b (codex FAIL — real first-session guard gap, fixed in 3bf5d4f26), 3bf5d4f26 (codex FAIL — two medium reap items, fixed in 30b0fdec9; Grok NEEDS_SUPERVISOR solely from auditor-addressed packaging text, fixed in the packaging), 30b0fdec9 (this bundle). Live controller checks on this host: launcher cold path in a worktree, fresh-project `init --repo` + tenant provisioning + conport launch with the gate, reap dry-run. Deterministic gates: ruff/flake8 per-file diffs vs base (0 new), black/isort/mypy on the new modules (clean).

## Validation Performed
- `make test-fast` at 30b0fdec9: **PASS** — 4229 passed, 2 skipped (implementer-run, controller-verified from the log).
- hooks workflow file, docs validators, lint/format/type diffs: **PASS** (see PROOF.json `validations`).
- repo-wide `make lint` / `make type-check`: **NOT_RUN** (not functional on main; per-file diffs recorded instead).
- live: launcher cold path, fresh-project provisioning + gate, reap dry-run: **PASS** (earlier heads; logs in the plan workspace).
- live: `reap --apply`, `switch-project`, Codex/EnterWorktree probes, legacy-envrc adoption, acceptance T1–T11: **NOT_RUN** (owner-run; `reap --apply` denied to the controller by the permission classifier).

## Audit (three routes at 30b0fdec9; observed identity UNKNOWN for all)
| route | requested model | status | findings |
|---|---|---|---|
| agy | gemini-4-argon-high | PASS_WITH_RISKS | F1 low: AGENTS.md:309 stale "first launch in a new worktree builds its images" |
| grok (tool-less, `init.tools == []`) | grok-4.7 | PASS_WITH_RISKS | none; documented residuals listed |
| codex | gpt-6-astra | FAIL | F1 medium reap.py:736 registry persistence failure still deletes the runtime dir and reports reaped; F2 medium lifecycle.py:1336 CLI start/restart not serialized against the automatic reaper; instruction-like: plan.md:17 (the plan's agentic-worker header) |
Reports: `AUDITOR_REPORT.md` (= AGY, schema record), `AUDIT_CODEX_REPORT.md`, `AUDIT_GROK_REPORT.md`, raw streams under `review_bundle/raw-*`; superseded freezes under `review_bundle/superseded-eb3f0624b-*` and `review_bundle/superseded-3bf5d4f26-*`.

## Remaining Uncertainty
Codex F1/F2 are OPEN (medium, robustness: no secret exposure, no cross-project data path); the controller's breaker stopped further fix/audit cycles after three freezes. Flaky `tests/unit/test_mcp_port_allocator.py::test_sequential_single_service_allocations_never_share_a_port` (~1/30 isolated runs). Owner-run acceptance T1–T11 not yet performed. Observed model identities of every delegated agent and auditor are UNKNOWN (no runtime receipts beyond harness error messages).

## Files Touched
See PROOF.json `files_changed` (65+ files). Sealed paths untouched: `docker/mcp-servers-source/conport/**`, `scripts/migration/provision_conport_project_db.sh`.

## Git State
Worktree `/Users/hue/code/dopemux-mvp/.worktrees/mcp-just-works-m1`, branch `feat/mcp-just-works-m1`, audited head 30b0fdec9; this proof commit is a proof-only successor. Not pushed; no PR; nothing merged.

## Rollback Plan
Branch-only: delete the branch/worktree. Host: `~/.local/bin/dopemux` is a uv editable install of main (`ln -sfn ~/.dopemux/venv/bin/dopemux ~/.local/bin/dopemux` to revert); `~/.dopemux/mcp/projects/*` holds provisioned secrets (keep); `~/.dopemux/mcp/runtime/reap.disabled` disables automatic reaps; the how-to's Rollback section covers repair-config back to URL entries. Probe fixture (`~/code/.tenant-probe-m1`, tenant `conport_tenant_probe_m1_84fc294a`) left for acceptance T8.

## Requested Next Step (owner)
1. Pick the governing verdict: (a) adopt AGY + Grok (PASS_WITH_RISKS) and file codex F1/F2 as the first follow-up PR, or (b) authorize one more fix + three-route audit cycle (~1.5 h).
2. Say the word for the PR (push + `gh pr create` are owner-gated); then merge #1439/#1456/#1459 first or let the PR carry them.
3. Run acceptance T1–T11 (T8 on the probe fixture), then delete `~/.dopemux/mcp/runtime/reap.disabled` and the probe artifacts.

## Adjudication (owner, 2026-11-07)
Owner ruling: the AGY (gemini-4-argon-high) and Grok (grok-4.7) verdicts, both PASS_WITH_RISKS at 30b0fdec9, govern Milestone 1. Codex gpt-6-astra findings F1 and F2 (medium, reap persistence / CLI start serialization) are accepted as OPEN residual risk and are filed for the first follow-up PR, not fixed in this packet. The owner also authorized: push + PR creation; acceptance T1-T11 run by the controller where the standing constraints allow; host cleanup after acceptance. The M1 merge itself remains owner-gated.

Bundle layout note: reports were renamed to the governance allowlist names (`AUDIT_AGY_REPORT.md`, `AUDIT_CODEX_REPORT.md`, `AUDIT_GROK_REPORT.md`, `AUDIT_SUMMARY.md`); raw auditor streams and the two superseded freezes live flat under `review_bundle/` with `superseded-<sha>-` / `raw-` prefixes; the sealed audit subject (prompts as sent, commit list, file hashes, full diff) is in `review_bundle/` too.
