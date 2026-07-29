# Independent Embedded Audit — PR #1150 (head 5075ee8ad8c791523607da980f08a26df1ce7ac6)

Third audit round: merge-fidelity review. The MUST_FIX repair round was fully audited and steward-approved at head 76abff766b. Branch protection then required updating with origin/main before merge (a real repository requirement, discovered when attempting `gh pr merge`), producing merge commit `5075ee8ad8` (first parent 76abff766b, second parent origin/main tip 414c7ac7f9). This audit verifies the merge introduced nothing new into the PR's own changes — the incoming main commits (#1126 dope-context, #1160 pr-steward, #1158/duplicate ddd-release-gate) are independently-already-merged work, not PR content.

Route: #2 Claude Code CLI with Sonnet, evidence-review mode (pre-gathered diffs/logs/test-output as files; auditor independently spot-checked hunks and re-derived claims rather than trusting summaries). Route #1 (AGY) was quota-limited throughout this round.
Invocation: `claude -p --model sonnet --add-dir <worktree> --allowedTools Read Grep Glob` against pre-computed evidence files (git diffs, test output, conflict-marker scan) in the scratchpad directory. Auditor session independent of the implementing session.

## Merge-Fidelity Audit — PR #1150 (head 5075ee8ad8)

### 1. Diff-identity claim (merge introduced nothing new to PR's own changes)

**VERIFIED.**

- `pr-diff-vs-old-main-v2.patch` and `pr-diff-vs-new-main-v2.patch` are **byte-identical** (`cmp` reports no difference), and both list exactly the same **62** `diff --git` file headers.
- Independently spot-checked 3 separate hunks across both files (not relying on the empty delta alone):
  - `src/dopemux/cli.py` — the added P-22 structural-bypass docstring note, word-for-word identical in both patches.
  - `.claude/hooks/mcp_health_probe.py` — the `_format_health(health, project_root)` signature change and repo-aware remediation string, identical in both.
  - `tests/mcp/test_provision.py` — the `start-all-mcp-servers.sh` → `README.md` touch-target rename across 4 test functions, identical in both.
- `pr-diff-delta-v2.txt` is confirmed 0 bytes, consistent with the above.

### 2. Overlap-check claim (no incoming main commit touches PR-owned paths)

**VERIFIED.**

- `overlap-check.txt` is confirmed empty (0 lines).
- By-eye re-derivation against `merge-incoming-files.txt` (35 files spanning `.claude/claude_config.json`, `.github/workflows/ddd-release-gate.yml`, `docs/03-reference/...`, `docs/runbooks/...`, `proof/...`, `services/dope-context/...`, `task-packets/dope-context/...`, `tests/pr_steward/...`, `tools/pr_steward/...`) confirms none match any of the 9 PR-owned path patterns (`src/dopemux/mcp/`, `src/dopemux/cli.py`, `tests/mcp/`, `.claude/hooks/mcp_health_probe.py`, `scripts/setup.sh`, `.github/copilot-instructions.md`, `docs/02-how-to/operations/pm-plane-runtime-recovery.md`, `claudedocs/mcp-fleet*`, `docs/90-adr/adr-dmx-mcp-project-scoped*`).

### 3. Conflict-marker false-positive claim

**PARTIALLY VERIFIED — the "not from this merge" part holds, but the "illustrative documentation" framing is inaccurate.**

- Confirmed: none of the 4 incoming commits (per `merge-incoming-commits-detail.txt` / `merge-incoming-files.txt`) touch `docs/pr_merge/usage-patterns.md`, `docs/planes/pm/pm-implementation-ledger.md`, `docs/planes/pm/write-boundaries.md`, or `docs/02-how-to/pr-merge-flight-dashboard.md`. So this merge did not introduce these markers.
- However, reading the actual file content (`docs/pr_merge/usage-patterns.md:57-64`, `docs/planes/pm/pm-implementation-ledger.md:129`, `docs/planes/pm/write-boundaries.md:140-141`) shows these are **not** illustrative/example syntax about the pr-merge tool — they are literal, unresolved `=======`/`>>>>>>>` conflict-marker fragments embedded directly in prose paragraphs, referencing real feature/worktree branch names (`codex/pr-merge-queue-unblockers`, `codex/pr-merge-queued-handoff`, `wt-collect-dopemux-pr321-20260330023335`, `codex/pm-jules-000-baseline-ledger`, `fix/pr-279-frontmatter`). This reads as genuine leftover debris from a prior, unrelated botched merge/rebase, not a documentation example.
- I could not independently confirm the "last modified 2026-03-30" date claim — the `git log` verification command required interactive approval that wasn't granted in this session — but this doesn't affect the merge-fidelity verdict since the files' absence from `merge-incoming-files.txt` is confirmed regardless of date.
- **This is a real, pre-existing documentation-integrity bug, unrelated to and not caused by this merge.** Worth a follow-up cleanup ticket; not a merge-fidelity blocker for PR #1150.

### 4. Test-pass claim

**VERIFIED per evidence file.** `post-merge-test-output.txt` shows `79 passed in 3.38s`, 0 failures, for the specified scope (`tests/mcp/`, `tests/test_mcp_health_probe.py`, `tests/test_cli_mcp_startup.py`) on the new head. I did not re-execute pytest myself; this reflects review of the pre-gathered output as instructed.

### Informational: incoming CI/security changes

- `.github/workflows/ddd-release-gate.yml`: reasonably scoped — `workflow_dispatch`-only, gated to the default branch, requires org App secrets (fails closed if absent), binds APPROVE to an exact head SHA, refuses drafts/non-default-base PRs, explicitly never merges/auto-merges, and uses minimal token permissions (`contents:read`, `pull-requests:write` for the review post). `pr_number` input is validated as numeric before use in `gh` calls. No injection concerns spotted.
- `tools/pr_steward/classifier.py` (`#1160`): the bare-bot-login normalization (`_normalize_bot_login`) is applied only to the candidate author, never the trusted roster, avoiding a normalization-based trust bypass. Logic looks sound.
- No adverse interaction found with `pr-steward.yml` / `embedded-audit.yml` / `clobber-guard.yml`: `ddd-release-gate` is manually operator-triggered from `main` only, decoupled from PR-event-triggered gates. Non-blocking.

```json
{"status": "PASS_WITH_RISKS", "findings": ["Diff-identity verified: pr-diff-vs-old-main-v2.patch and pr-diff-vs-new-main-v2.patch are byte-identical (62/62 files match); 3 independent hunk spot-checks (cli.py, mcp_health_probe.py, test_provision.py) confirm identical content, not just identical file sizes.", "Overlap-check verified empty by independent re-derivation: none of the 35 incoming files from the 4 merge commits fall under any of the 9 PR-owned path patterns.", "Conflict-marker scan's root claim (not introduced by this merge) verified: none of the 4 incoming commits touch the 4 flagged doc files.", "Conflict-marker scan's characterization is inaccurate: the 17 hits are genuine leftover unresolved conflict-marker debris referencing real branch names (e.g. codex/pr-merge-queue-unblockers, wt-collect-dopemux-pr321-20260330023335), not illustrative tool documentation -- a real but pre-existing, merge-unrelated doc-integrity bug.", "Post-merge test claim verified from evidence file: 79 passed, 0 failed, on the new head for the declared test scope.", "ddd-release-gate.yml and pr_steward/classifier.py changes reviewed: properly scoped (workflow_dispatch/main-only, exact-head SHA binding, no merge/auto-merge, roster-only normalization), no adverse interaction with embedded-audit/pr-steward/clobber-guard gates."], "remaining_risks": ["Could not independently verify the 2026-03-30 last-modified date claim for the 4 conflict-marker doc files (git log command required interactive approval not granted in-session); does not change the merge-fidelity verdict since file absence from merge-incoming-files.txt was confirmed directly.", "Pre-existing unresolved conflict-marker corruption in docs/pr_merge/usage-patterns.md, docs/planes/pm/pm-implementation-ledger.md, docs/planes/pm/write-boundaries.md, and docs/02-how-to/pr-merge-flight-dashboard.md should be cleaned up in a follow-up -- unrelated to PR #1150 but a latent doc-quality/trust issue in the repo.", "ddd-release-gate.yml grants a scoped GitHub App token pull-requests:write triggerable by anyone able to run workflow_dispatch on main; informational only, by design, not introduced by this PR."]}
```
