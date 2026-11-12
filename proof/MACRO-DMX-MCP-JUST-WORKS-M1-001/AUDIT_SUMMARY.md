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

## Cycle 2 (2026-11-08) — forced fix + re-audit at 3f1335e7fdcf8165d4669195bfd521cafca13304

### Change Summary
Forced fix + re-audit cycle after the 30b0fdec9 round: origin/main (#1500) merged as 0cde3a921; then ten commits that close the five PR review-bot threads (test path case; SessionEnd hook timeout 60; `_url_is_repairable` templated URLs fail closed; `--repo` commands load the target checkout's catalog; AGENTS.md image sentence), codex F1 (`state_error`: a failed registry/lease save keeps the runtime dir) and F2 (CLI start/restart/stop serialize the worktree-scoped services under one instance-lock acquisition with facts re-taken under the lock, images pre-built outside it, docker-unavailable snapshots failing closed; the orchestrator stays outside under its own `:7890` lock because the whole-selection design deadlocked against `switch-project`), the crashed-launcher idle rule (dead attach records count from their attach time without mutating during planning), the build-only orphan runtime dir (`instance.json` marker + dir-only `worktree_missing` candidates), the pre-existing restart-did-nothing bug and the orchestrator-only artifact-write race, plus append-only design amendments, how-to corrections and the T7 evidence note; after the push, the Codex connector's one new P2 (tenant provisioning replayed a committed non-re-runnable migration when its checkpoint write was lost) was fixed as Task C, and its follow-up P2 on the next push (`init --repo <subdir>` keeping the subdirectory) as Task A2, both before the freeze.

### Authority Used
Owner: "fold everything" (2026-11-07) after the forced-cycle ruling; push authorized within the cycle. Not used: merge, thread resolution, signing (owner-only).

### Analysis Performed
Subagent-driven: two implementers (sonnet batch, opus concurrency cluster; implementers never commit, the controller commits by explicit paths), task reviews with fix rounds, one final whole-cycle review with one fix dispatch and one scoped re-review, a controller-verified micro round. Findings caught before the freeze: ABBA deadlock (implementer), stale snapshot under the lock, inline build under the lock, restart pre-stop snapshot, docker-unavailable fail-open, orchestrator-only override overwrite (reviewers).

### Validation Performed
See `validations` in PROOF.json and `review_bundle/subject-validations.md`: make test-fast PASS at the frozen head; hooks workflow PASS; docs validators PASS on the two docs pages; ruff/flake8/mypy deltas 0; black/isort 0 on added lines; live cold launch + reap dry-run PASS at this head; acceptance T1–T11 NOT_RUN at this head (recorded at 30b0fdec9); root hygiene FAIL pre-existing.

### Audit outcome at 3f1335e7f
agy gemini-4-argon-high PASS_WITH_RISKS (governing record), grok grok-4.7 PASS_WITH_RISKS (no findings), codex gpt-6-astra FAIL with two new mediums: F1 mcp_json.py:140 (the host-placeholder guard splits the URL authority before masking placeholders, so a default containing `/`, `?` or `#` escapes the check) and F2 stdio_proxy.py:198 (resend-once recognises "Session terminated" as a substring and can replay a request the backend committed). Breaker tripped per the ruling: owner decides between a cycle 3 (both fixes small) and adjudicating AGY + Grok as governing with codex F1/F2 as a follow-up. Earlier codex F1/F2 (30b0fdec9) are closed: codex confirms C-REAP/C-LOCKS PASS and lists only the two new findings.

### Remaining Uncertainty
`residual_risks` and `unknowns` in PROOF.json (the final reviewer's list of what an L3 auditor may still raise is pre-stated there).

### Files Touched
`files_changed` in PROOF.json (diff of the frozen head against the synthetic base merge-tree(5742575c4, f16e0da2c), proof/ excluded).

### Git State
Branch feat/mcp-just-works-m1 pushed at the frozen head; proof-only successor commits follow; PR #1503 open, base main (up to date with f16e0da2c at freeze time).

### Rollback Plan
Revert the PR; on a host `ln -sfn ~/.dopemux/venv/bin/dopemux ~/.local/bin/dopemux`; provisioned secrets and the shared images are kept; the how-to's Rollback section restores URL entries.

### Requested Next Step (owner)
Resolve the five review threads against the fixing commits (table in the hand-off), run the cleanup script, then sign `scripts/audit/sign_local_audit_proof.sh 1503` at the frozen head's proof successor; merge stays owner-gated.

### Audit (three routes at 3f1335e7; observed identity UNKNOWN for all)

| route | requested model | status | findings |
|---|---|---|---|
| agy | gemini-4-argon-high | PASS_WITH_RISKS | none |
| grok | grok-4.7 | PASS_WITH_RISKS | none |
| codex | gpt-6-astra | FAIL | F1 medium src/dopemux/mcp/mcp_json.py:140; F2 medium src/dopemux/mcp/stdio_proxy.py:198 |

## Cycle 6 (2026-11-11) — Task H reverted (open follow-up recorded) + re-audit, Grok governing, at efb06f7c5a0677d5a6103cbcb86e02d199c133ba

### Correction to the cycle-2 record

The d4e021126 proof said the Codex connector did not review the cycle-2 head 3f1335e7f within the 30-minute cap. It did: issue-comment receipt 2026-11-08T20:50:31Z, "Didn't find any major issues", reviewed commit 3f1335e7fd. A clean Codex result is posted as an issue comment, not a PR review; the capture script read reviews only. The script now captures receipts (review_bundle/cycle3-codex-receipts.txt).

### Cycle 3 scope

Owner decision after the cycle-2 verdicts (AGY PASS_WITH_RISKS, Grok PASS_WITH_RISKS, Codex FAIL F1/F2): cycle 3 limited to the two codex findings. Task D (implementer sonnet, review opus: round 0 NEEDS_FIXES (FINDING 1 medium: first-`://` strip after masking) → round 1 APPROVED (45-URL adversarial probe, RED re-verified) → docstring micro round controller-verified): F1 mask-first host-placeholder detection in mcp_json.py; F2 exact SDK-literal match in stdio_proxy.py; tests RED→GREEN plus an SDK drift guard. Commits 43294e99b. Re-frozen at 43294e99b and re-audited by the same three routes.

### Audit outcome at 43294e99b (cycle 3)

Grok PASS_WITH_RISKS (0 findings; states codex F1/F2 from 3f1335e7f closed by items 11-12); AGY NOT_RUN (runner quota, HTTP 429 'Individual quota reached', resets ≈2026-11-14, no audit produced); Codex FAIL with ONE NEW medium F1 mcp_json.py:170 — a port-position placeholder is judged by its default, but PORT=`3005@remote.example` expands to host remote.example, so `http://localhost:${PORT:-3005}/sse` was repairable and the planner would replace an operator endpoint; both 3f1335e7f findings 'closed as specifically reported'. Breaker → owner decided 2026-11-09: Grok governs the embedded-audit record (precedent #1459/#1500) and cycle 4 fixes F1.

### Owner decisions after cycle 3 (2026-11-09)

Grok governs the embedded-audit record (AGY quota 429 until ≈2026-11-14; precedent #1459/#1500; enum value 'unknown' for grok-4.7, exact model in the invocation). Cycle 4 limited to Codex F1.

### Cycle 4 scope

Task E (implementer sonnet, review opus: Task E round 0 NEEDS_FIXES on one LOW doc sentence dictated by the controller's brief (the how-to's manual recipe equals the catalog templates and is still repaired) → doc/comment micro round controller-verified, code approved (63-URL adversarial probe, env-independence proven); Task F round 0 NEEDS_FIXES (MEDIUM: dropped doctor findings were the only guard for a same-project sibling-worktree container on a resolved port; LOW: stop control proved nothing) → round 2 `_collision_checks(worktree_hash)` + launcher ownership rule → re-review NEEDS_FIXES on two LOWs (other-project diagnosis; overclaiming bullet) → round 3 APPROVED (25-case probe table, no false positives)): `_url_is_repairable` replaces only what dopemux rendered (allowlist of its own port variables in port position; every other template preserved; environment never read); `_neutralize_placeholders` removed; planner reason text; design amendment; tests RED→GREEN. Commits 83b468e71 (Task E), fc591cba1 (Task F). Re-frozen at fc591cba1 and re-audited by the codex and grok routes (agy not launched: quota).

### Audit outcome at fc591cba1 (cycle 4)

Grok PASS_WITH_RISKS (0 findings; GOVERNING by owner decision; closure stated for items 6-7, 11-12, 13 and 14); AGY NOT_RUN (not launched: quota); Codex FAIL with TWO NEW mediums, both in item 14 (Task F): F1 lifecycle.py:1469 — the dropped doctor reserved-port / duplicate-port blockers are not recomputed when `_resolve_ports` retains existing leases without allocating (probe: two services' leases retained on :7890, zero collision findings; the doctor blocked this before); F2 lifecycle.py:702 — rule (2) needs a worktree hash, so a managed same-project container with a contradictory workspace label and no hash passes although ownership classifies WRONG_PROJECT and the launcher refuses it. Breaker → owner chose cycle 5 with the convergent fix.

### Owner decision after cycle 4 (2026-11-09)

Cycle 5 with the convergent fix (option 1 of three): the Task F six-code drop is replaced by one checkable invariant and the resolved port map is validated; both codex mediums were regressions of Task F versus main.

### Cycle 5 scope

Task G (implementer sonnet, review opus: Task G round 0 NEEDS_FIXES (one medium: a container with our exact expected name and contradictory workspace labels on an off-map port was dropped as off-port and adopted by name) → round 1 APPROVED (29-case probe table on main vs new: every case main blocked blocks again except the stale-port recovery; Codex F1/F2 probes block; helper edge cases fail closed). Task H: APPROVED first pass (pre-check mirrors the planner; maybe_reap otherwise identical; 5000-dir listing 46 ms; RED verified on 192a84dc3; host registry untouched)): see slices. Commits 192a84dc3 (Task G), 380c2c52c (Task H). Re-frozen at 380c2c52c and re-audited by the codex and grok routes (agy not launched: quota).

### Codex connector at the frozen head

First trigger 10:46:23Z unanswered within the cap → frozen with NOT_RUN in the sealed VALIDATIONS.md; re-trigger 11:19:39Z → clean receipt 11:23:21Z (reviewed commit 380c2c52c8), recorded in cycle5-gates.json and cycle5-bots-note.txt.

### Audit outcome at 380c2c52c (cycle 5)

Grok PASS_WITH_RISKS (GOVERNING; ONE LOW: how-to :287 said automatic reap sees a marker-only runtime dir only while the registry lists an instance — stale after item 16; closure stated for items 6-7, 11-12, 13, 14, 15, 16); AGY NOT_RUN (not launched: quota); Codex FAIL with TWO NEW mediums, both in item 16 (Task H): F1 reap.py:697 — the fix covered an empty registry FILE but not an absent one (fresh host: RuntimeRegistry.load() reports MISSING and plan_reap plans nothing unless OK, before marker discovery; the test used an empty present registry); F2 reap.py:545 — marker discovery enumerated, sorted and read every runtime dir without a deadline or count bound. Codex connector clean on the head (receipt 11:23Z). Breaker → owner chose to REVERT item 16 (2bbf08f65; tree identical to 192a84dc3) and record the connector's finding as an open follow-up (design amendment, fbbe95a59).

### Owner decision after cycle 5 (2026-11-09)

Revert Task H (option 1 of three): the change covered an empty registry file but not an absent one and brought two Codex mediums; Grok had passed the pre-Task-H code; Task G stays. The Codex connector's reap finding is an open, documented follow-up.

### Cycle 6 scope

Mechanical `git revert` of 380c2c52c (2bbf08f65; tree identical to 192a84dc3) plus one append-only design bullet recording the revert and the open follow-up (fbbe95a59). Re-frozen at efb06f7c5 and re-audited by the codex and grok routes (agy not launched: quota).

### Audit outcome at efb06f7c5

| Route | Model (requested) | Status | Findings | Notes |
|---|---|---|---|---|
| grok (governing, owner decision) | grok-4.7 | PASS_WITH_RISKS | 0 | Source diff only on this route: design.md line-316 wording and the item-1 test file NOT_RUN; tests/lint and live T1-T11 NOT_RUN |
| codex (advisory) | gpt-6-astra | NEEDS_SUPERVISOR | 0 | Status comes only from the agentic-worker template line at plan.md:17, classified benign and ignored by the auditor; adjudication is the owner's (pending). All earlier findings confirmed closed; Task H confirmed fully reverted; item-18 follow-ups do not reopen a closure |
| agy | gemini-4-argon-high | NOT_RUN | - | Quota 429; not launched |

Observed model and effort are UNKNOWN on every route (no runtime receipt). Acceptance NOT_GRANTED by both returns; the signature and the plan.md:17 adjudication are owner steps.

### Audit (three routes at efb06f7c; observed identity UNKNOWN for all)

| route | requested model | status | findings |
|---|---|---|---|
| agy | gemini-4-argon-high | NOT_RUN (not launched in cycles 4 to 6: the agy route failed on its individual quota at the cycle-3 freeze (HTTP 429 RESOURCE_EXHAUSTED 2026-11-09T04:43Z, resets ≈2026-11-14; review_bundle/cycle3-raw-agy-quota-error.json); the owner chose Grok as the governing route on 2026-11-09) | none |
| grok | grok-4.7 | PASS_WITH_RISKS | none |
| codex | gpt-6-astra | NEEDS_SUPERVISOR | none |
