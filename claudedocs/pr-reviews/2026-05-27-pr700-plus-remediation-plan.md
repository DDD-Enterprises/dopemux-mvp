# PR #700+ Remediation, Repair, and Merge Plan

**Generated**: 2026-05-27
**Scope**: All 10 open PRs numbered #700 and higher
**Audience**: Downstream automation agent (Gemini / Codex / Claude Code)
**Repo**: `DDD-Enterprises/dopemux-mvp`
**Branch base**: `main` (current HEAD: `cc966a25d` at session start, has moved since)

This file is self-contained. Read top to bottom, then execute in the order in the **Recommended merge order** section.

---

## 0. Executive summary

| # | Title | Size | Status | Verdict | Action |
|---|-------|------|--------|---------|--------|
| 700 | Palette UX a11y in App.tsx | +44/-3 (1 file) | BEHIND, 1 thread | REPAIR | Address icon mapping, rebase, merge after #715 ladder |
| 703 | Palette notification scannability + AI Rec a11y | +27/-3 (1 file) | BEHIND, 2 threads | **BLOCKED — invalid JSX** | Fix broken `</Tooltip>oltip>` literal, then merge into #715 OR close as duplicate |
| 706 | docs(rte): ledger grok none reasoning fix | +1/-0 (1 file) | BEHIND, 1 outdated thread | **CLOSE as duplicate** | Title and file match merged PR #707 — close without merge |
| 712 | test(rte): verify CostProfile F repair | +2315/-0 (11) | BLOCKED, 1 thread | REPAIR-LIGHT | Tighten Gate 3 parse, merge |
| 713 | feat(governance): auditor router pal-clink classification | +3797/-1 (71) | BLOCKED, 5 P1 threads | REPAIR | Address 5 P1 hardening items in `tools/auditor_router/pal_clink.py` |
| 714 | feat(orchestrator): remaining operator workflows | +11269/-8 (64) | BLOCKED, 6 threads | REPAIR-LARGE | Address 4 P1 + 2 P2 items, refresh PROOF-017 |
| 715 | Palette notification iconography | +42/-3 (1 file) | BLOCKED, 3 threads | REPAIR | Fix a11y on chip + Alert icon + use `NotificationType` |
| 716 | plan(orchestrator): seed FOLLOWUP series (9 packets) | +1600/-0 (18) | BLOCKED, 3 threads | REPAIR | Fix non-existent CLI verify, packet ID mismatch, PROOF blockers |
| 717 | fix(governance): resolved threads + proof freshness | +2433/-20 (41) | BLOCKED, 3 threads | REPAIR | Tighten `CURRENT` branch to re-verify head SHA; close schema gap |
| 718 | feat(audit+pr): DMX-EMBEDDED-AUDIT-PR-CLEANUP-RECONCILED series | +9909/-17 (84) | **CI FAIL**, 5 threads | REPAIR-LARGE | Move `artifacts/` out of repo root, fix doc stale API ref, finish supervisor list, fix compiler field reads |

Key cross-cutting issues to handle before any merges:

1. **Palette PR collision** (#700, #703, #715 all edit `ui-dashboard/src/App.tsx` and **all three independently add their own `getNotificationIcon` function** — they conflict, they are NOT supersets of each other). Verified diffs:
   - #700: `getNotificationIcon = (type: string)` + 44 lines
   - #703: `getNotificationIcon = (type: string, color: string)` + 27 lines + broken JSX at L496 (`</Tooltip>oltip>`)
   - #715: `getNotificationIcon = (type: string)` + 42 lines
   These cannot be merged sequentially without conflict resolution. Pick one (recommended #715, see §1.715).
2. **PR #706 is a duplicate of merged PR #707** — close.
3. **PR #718's CI failure is a hygiene policy violation** (a single file under `artifacts/` at repo root). Fixable in seconds.
4. **The orchestrator/governance stack (#713 → #714 → #716 → #717 → #718) shares files in `tools/pr_steward/`, `tools/auditor_router/`, `tools/pr_action_bridge/`, `src/dopemux/orchestrator/`.** Merge order matters — see §3.
5. **"BLOCKED" cause is most likely unresolved review threads or the PR Steward gate, not branch-protection review.** Branch protection on `main` requires `required_approving_review_count: 0` and `require_code_owner_reviews: false`. The required status check `ci-summary` is the only formal block — and that check itself fails (#718) or passes (#714 et al.). When `ci-summary` passes but `mergeStateStatus = BLOCKED`, the gate is almost certainly "require all conversations resolved" (not exposed by the public branch-protection API) or the PR Steward classifier. Confirm in the GitHub UI's "Merge blocked by:" string before relying on this.

---

## 1. Per-PR repair guide

For each PR: blockers, exact fixes, validation, rollback. All file paths are relative to repo root.

**🔍 PRECONDITION FOR ALL PRs**: Line numbers in this plan come from reviewer-bot comments captured 2026-05-27, not from re-reading the files. Before applying any patch, `Read` the target file (or `git show <branch>:<path>`) to confirm the line still maps to the described code. Especially for #713, #714, #717, #718 where file shapes are live-evolving.

**📋 AGENTS.md §9 proof-bundle contract** (quoted from `AGENTS.md` line 110-130):

> Proof for repo-changing work must include:
> - TP path and ID
> - worktree path
> - branch
> - repo identity result
> - slices completed
> - files changed
> - validations with exit codes
> - codereview status
> - precommit status
> - commit SHA
> - PR URL or exact blocker
> - residual risks
> - `UNKNOWN`s
> - cleanup status
>
> No proof means incomplete.

Use this list whenever §9 is referenced below.

### PR #700 — Palette: UX and accessibility improvements in App.tsx
**Branch**: `palette-ux-improvements-7854933912242465786`
**Status**: BEHIND main, MERGEABLE, all checks pass, 1 unresolved thread

**Repair**:
- Thread (P3, `ui-dashboard/src/App.tsx:167`): `getNotificationIcon` introduces a second switch over notification types alongside `getNotificationColor` in `ui-dashboard/src/notificationColors.ts`. To prevent drift, change the function signature to accept `NotificationType` (imported from `notificationColors.ts`) and colocate the icon mapping there.

**Fix steps**:
1. In `ui-dashboard/src/notificationColors.ts`, export a `getNotificationIcon(type: NotificationType): IconComponent` (or an `iconByType` record). Place the mapping next to `getNotificationColor` so both live in one source of truth.
2. In `App.tsx`, remove the local `getNotificationIcon` switch and import the new helper.
3. `git fetch origin main && git rebase origin/main` to clear the BEHIND state.

**Validation**: `cd ui-dashboard && npm run lint && npm run typecheck && npm run build`. UI smoke (visual): notifications still render icons.

**Rollback**: `git revert <merge-sha>` on main; the PR scope is single-file, safe.

---

### PR #703 — Palette: notification feed scannability + AI Rec a11y
**Branch**: `palette/notification-icons-and-a11y-fix-16620623900763162914`
**Status**: BEHIND, MERGEABLE-UNKNOWN, 2 unresolved threads
**🚨 Hard blocker (verified)**: invalid JSX literal `</Tooltip>oltip>` at `ui-dashboard/src/App.tsx:496` (confirmed by `git show origin/palette/notification-icons-and-a11y-fix-...:ui-dashboard/src/App.tsx | grep -n "</Tooltip"` — line 496 has the stray characters).

**Diff overlap analysis (verified 2026-05-27)**:
- #703 introduces `getNotificationIcon = (type: string, color: string) => {...}` — **two-arg variant**, unique to #703.
- #715 introduces `getNotificationIcon = (type: string) => {...}` — different signature.
- The two PRs' icon functions are not compatible; merging both would require explicit reconciliation.

**Repair (only if not closing)**:
1. `ui-dashboard/src/App.tsx:496` — remove the stray `oltip>` so the tag is exactly `</Tooltip>`.
2. `ui-dashboard/src/App.tsx:133` — same `NotificationType` reuse refactor as #700.
3. Rebase onto current `main`.

**Validation**: `cd ui-dashboard && npx tsc --noEmit && npm run build`. The build *must* fail before fix and pass after.

**Recommendation**: Three palette PRs (#700, #703, #715) conflict on the same function. They can't all merge.
- **Option A (preferred)**: Close #703 in favor of #715 — but **only after a human reviewer confirms the visual scannability changes in #715 cover #703's intent**. The two-arg color-aware icon in #703 is not in #715, so consolidation will drop the color-aware behavior unless it's ported.
- **Option B**: Pick #703 instead, fix JSX, close #700 and #715. Not recommended — #715 has the more polished a11y story.
- **Option C**: Cherry-pick #703's color-aware logic into #715 before closing #703.

---

### PR #706 — docs(rte): ledger grok none reasoning fix
**Branch**: `codex/rte-grok-none-ledger-001`
**Status**: BEHIND, 1 outdated thread

**Verdict**: **DUPLICATE — CLOSE WITHOUT MERGE.** PR #707 with the identical title, same +1/-0 file path (`task-packets/INDEX.md`), and equivalent payload merged 2026-05-26 at `2026-05-26T06:02:32Z`. The diff shown by #706 still shows the new row, but `main` already has it because #707 landed.

**Action**:
```bash
gh pr close 706 --comment "Superseded by merged PR #707 (same title, same INDEX.md row). Closing without merge."
```

---

### PR #712 — test(rte): verify CostProfile F repair (TP-RTE-COSTPROFILE-F-VERIFY-002)
**Branch**: `codex/rte-costprofile-f-verify-002`
**Status**: BLOCKED, MERGEABLE, all checks pass, 1 unresolved P2 thread

**Repair**:
- Thread (P2, `task-packets/generated/TP-RTE-COSTPROFILE-F-VERIFY-002.json:167`): Gate 3 uses `grep -q 'cost_profile'` on raw `print-config` output, which matches *any* substring. Replace with a structured parse that asserts a **top-level** `cost_profile` key.

**Fix steps**:
1. In `TP-RTE-COSTPROFILE-F-VERIFY-002.json` Gate 3, replace the `grep -q 'cost_profile'` step with something like:
   ```bash
   python -m dopemux.cli rte print-config --json | python -c "import sys,json; d=json.load(sys.stdin); assert 'cost_profile' in d, 'no top-level cost_profile'"
   ```
2. Re-run the gate locally and update the proof bundle path under `proof/repo-truth-extractor/cost-profile-f-verify/` with the new exit codes.

**Validation**: rerun the packet's Gate 3 against `HEAD a9dd06592`, confirm proof bundle records `PASS` for the new structured assertion.

**Note**: This PR carries the F-VERIFY-002 verdict already recorded in user memory (`project_rte_costprofile_f_verify_002.md`) — the verdict was VERIFIED, so the underlying work is correct; this thread is just a hardening request.

---

### PR #713 — feat(governance): auditor router pal-clink classification
**Branch**: `codex/tp-dmx-auditor-router-pal-clink-002`
**Status**: BLOCKED, MERGEABLE, all checks pass, 5 unresolved P1 threads (all in `tools/auditor_router/pal_clink.py`)

**Repair** (all in `tools/auditor_router/pal_clink.py`):

1. **L60 — Inspect audit configs by declared client name, not filename**: Route classification reads `pal_clink_audit_clients`/configs by filename stem matching `claude-audit`/`gemini-audit`. Switch to reading the `client` field inside each config so a renamed file (e.g. `zzz.json`) still classifies correctly.

2. **L75 — Treat string arg fields as single arguments**: `effective_args_for_config` iterates `additional_args`/`config_args`/`args` directly. When a config provides a string, Python iterates character-by-character. Add an `_as_args(value)` coercion: list → list, str → `[str]`, else `raise ValueError`.

3. **L75 — Validate arg field types before marking config AVAILABLE**: `config.get(key) or []` treats `{}` / `0` / `""` as empty silently. Use `_as_args` from (2) and fail-closed (`status: INVALID`) on type mismatch.

4. **L330 — Reject falsey non-list `role_args`**: same pattern as above for `role.get("role_args") or []`. Reuse `_as_args`.

5. **L242 — Guard PAL audit payload type before reading fields**: `normalize_pal_clink_audit_output` calls `payload.get(...)` without checking `payload` is a dict. Add `if not isinstance(payload, Mapping): return NormalizedAudit.invalid(...)`.

**Tests to add** (`tests/auditor_router/test_pal_clink.py`):
- string arg field → coerced to `[str]` not chars.
- dict arg field → INVALID, not AVAILABLE.
- payload type non-dict → returns invalid record, never raises.
- filename stem mismatch + correct `client` field → still classified.
- falsey `role_args` (string `""` or dict `{}`) → INVALID.

**Validation**: `pytest tests/auditor_router/ -xvs`. Then re-run any consuming `pal_clink` integration smoke.

**Rollback**: pure-Python file changes; `git revert` is clean.

---

### PR #714 — feat(orchestrator): add remaining operator workflows (TP-DMX-ORCH-008 → 017)
**Branch**: `codex/tp-dmx-orch-007-plugin-hooks`
**Status**: BLOCKED, MERGEABLE, all checks pass, 6 unresolved threads (4 P1, 2 P2)

**Repair** (mixed paths):

1. **P1, `src/dopemux/orchestrator/operator_workflows.py:461`**: Transition proof validator accepts any non-empty `schema_version`. Pin to known versions (e.g. `{"1", "1.0"}`) and fail-closed otherwise. Add unit test for `"999"` → INVALID.

2. **P2, `src/dopemux/commands/orchestrator_commands.py` (outdated)**: `--pr` parsing uses bare `int(token)`. Wrap in try/except and emit clear error, e.g.:
   ```python
   try:
       number = int(token)
   except ValueError:
       raise click.BadParameter(f"--pr expected integer PR number, got '{token}'")
   ```

3. **`src/dopemux/orchestrator/validation/proof.py:210`** (Copilot): `supporting_artifacts` permits empty strings. Reuse the existing `_non_empty_string` validator (or call `bool(item.strip())`) when warnings/blockers are present.

4. **`proof/dmx-orch-integration/TP-DMX-ORCH-017/PROOF.json:138`** (Copilot): Missing required fields per AGENTS.md §9 (validations with exit codes, codereview/precommit status, commit SHA, PR URL). Re-emit the proof bundle using the canonical proof template:
   - `validations`: array of `{name, exit_code, status: PASS|FAIL|NOT_RUN, log_path}`.
   - `codereview_status`, `precommit_status` (PASS/FAIL/NOT_RUN).
   - `commit_sha`: SHA at the moment proof was generated.
   - `pr_url`: this PR's URL.
   - If genuinely missing, set explicit `blocker` text instead of nulls.

5. **P1, `services/task-orchestrator/task_orchestrator/mcp/__init__.py:120`**: Wrapper dispatch forwards `orchestrator.*` MCP calls to `handle_orchestrator_tool_call`, which classifies capabilities from a config file. If the policy file is missing, the call still proceeds. Add an early check:
   ```python
   if not policy_path.exists():
       return ToolError("orchestrator policy missing", code="POLICY_UNAVAILABLE")
   ```

6. **P2, `src/dopemux/orchestrator/policy.py:259`**: Automatic-allowed computation ignores capability mode. Add:
   ```python
   if capability.tier in {"T0","T1"} and capability.mode in {"write","destructive"}:
       automatic_allowed = False
   ```

**Tests**: extend `tests/orchestrator/test_operator_workflows.py`, `test_validation_proof.py`, `test_policy.py`, `test_orchestrator_commands.py` per above.

**Validation**: `pytest tests/orchestrator/ -xvs && pytest services/task-orchestrator -xvs`. Manually re-emit PROOF-017 and re-run gates.

**Rollback**: This PR is the biggest in the queue (+11269/-8). Mergedown carries scope risk — be sure the proof bundle is verifiable before merging. `git revert` is supported but expensive.

---

### PR #715 — Palette: Enhanced Notification Scannability & Iconography
**Branch**: `palette-notification-iconography-9918379728212595040`
**Status**: BLOCKED, MERGEABLE, all checks pass, 3 unresolved threads

**Repair** (all in `ui-dashboard/src/App.tsx`):

1. **L483** — `aria-label` for the copyable recommendation Chip no longer indicates the action. Change to include both the verb and the recommendation:
   ```tsx
   aria-label={isCopied ? `Copied: ${rec}` : `Copy recommendation: ${rec}`}
   ```

2. **L518** — Custom Alert icon (SVG) needs `aria-hidden="true"` (and ideally `focusable={false}`). Without it screen readers double-announce.

3. **L149** — Same `NotificationType` union reuse as #700/#703. Make `getNotificationIcon` take `NotificationType`, add explicit `info` case, colocate with `getNotificationColor`.

**Consolidation note**: This PR is the *latest* of the three palette PRs and the cleanest, but it is **not a strict superset** of #700 or #703 (verified by diff comparison 2026-05-27).
- #700 adds 44 lines (this PR adds 42); the two diffs have different content.
- #703 has a unique 2-arg `getNotificationIcon(type, color)` not present here.

**Action if consolidating to #715**: a human reviewer or designer must approve which UX changes from #700 and #703 are kept. Suggested cherry-pick: port #703's `color` parameter into #715's icon function if the live-signal-feed coloring is desired. Then close #700 and #703 with explicit comments naming which lines were ported.

**Validation**: `cd ui-dashboard && npm run lint && npx tsc --noEmit && npm run build`. Then `npm test` if it exists.

---

### PR #716 — plan(orchestrator): seed DMX-ORCH-INTEGRATION-FOLLOWUP — 9 follow-up packets
**Branch**: `claude/tp-dmx-orch-followup-packets`
**Status**: BLOCKED, MERGEABLE, all checks pass, 3 unresolved threads. **This is the branch this session opened in.**

**Repair**:

1. **P1, `task-packets/generated/TP-DMX-ORCH-PROOF-PERPACKET-001.json:47`**: Verify list runs `python -m dopemux.cli orchestrator …`, but the CLI has no `orchestrator` top-level command. Either:
   - Add the `orchestrator` subcommand to `src/dopemux/cli.py` first, **or**
   - Replace the verify entries with commands that already exist (e.g. `dopemux orch-integration …` or whichever runtime command is canonical — confirm by `python -m dopemux.cli --help`).

2. **P2, `task-packets/generated/TP-DMX-ORCH-014A-UPSTREAM.json:10`**: Invariant references `TP-DMX-ORCH-014B`, which doesn't exist in the repo. Either create the consumer packet alongside, or change the reference to whichever consumer packet *does* exist in this same series.

3. **Copilot, `proof/dmx-orch-integration/TP-DMX-ORCH-DOCS-001/PROOF.json:46`**: All PLAN_ONLY proof bundles have `commit_sha: null` and `pr_url: null` without a `blocker` field explaining the absence. Add an explicit blocker like:
   ```json
   {"commit_sha": null, "pr_url": null, "blocker": "PLAN_ONLY packet — no commit or PR until execution packet runs"}
   ```
   Apply to all PLAN_ONLY proof bundles in this PR (search `proof/dmx-orch-integration/` for null SHAs).

**Validation**: re-run `tools/pr_steward/classifier.py` against the PR; the proof-freshness classifier should now accept the bundles. Also lint each JSON: `python -m json.tool task-packets/generated/TP-DMX-ORCH-*.json > /dev/null`.

---

### PR #717 — fix(governance): handle resolved threads + proof freshness
**Branch**: `codex/pr-steward-resolved-thread-proof-semantics-001`
**Status**: BLOCKED, MERGEABLE, all checks pass, 3 unresolved threads

**Repair**:

1. **P1, `tools/pr_steward/classifier.py:660`** (and Copilot duplicate): `_proof_is_current` trusts `proof_freshness.matches_pr_head` in the `CURRENT` branch and never verifies `proof_head_sha` equals the live `pr_head_sha`. Fix:
   ```python
   if freshness.status == "CURRENT":
       if freshness.proof_head_sha != pr_head_sha:
           return False
       if not freshness.matches_pr_head:
           return False
       return True
   ```

2. **`schemas/pr_steward/merge_readiness.schema.json:253`** (Copilot): The READY schema permits a self-reference exception purely from `proof_freshness.status`. A payload with `matches_pr_head: false`, `status: CURRENT_WITH_SELF_REFERENCE_EXCEPTION`, and a null `self_reference_exception` still passes validation. Tighten with a JSON Schema `dependentRequired`:
   ```json
   {
     "if": {"properties": {"proof_freshness": {"properties": {"status": {"const": "CURRENT_WITH_SELF_REFERENCE_EXCEPTION"}}}}},
     "then": {"required": ["self_reference_exception"], "properties": {"self_reference_exception": {"type": "object", "required": ["supervisor_accepted_at", "supervisor"]}}}
   }
   ```
   Adjust the property names to whatever the runtime expects (`tools/pr_steward/classifier.py` will tell you).

3. Re-run schema validation against every existing `MERGE_READINESS.json` fixture in `tests/pr_steward/` to make sure tightening doesn't reject historic payloads.

**Validation**: `pytest tests/pr_steward/ -xvs`. Run the classifier against a real PR and check the JSON output.

**Coupling note**: #718 builds the bridge that *consumes* this classifier's output. **Land #717 before #718.**

---

### PR #718 — feat(audit+pr): DMX-EMBEDDED-AUDIT-PR-CLEANUP-RECONCILED (12 TPs)
**Branch**: `claude/upbeat-thompson-35f2e8`
**Status**: BLOCKED, MERGEABLE, **3 CI checks FAILING**, 5 unresolved threads

**Critical CI fix (do this first)**:
- `💅 Code Quality & Linting` fails with: `root-hygiene: FAILED — artifacts/task-orchestrator/DMX-EMBEDDED-AUDIT-PR-CLEANUP-RECONCILED/load_plan.json: top-level directory 'artifacts' is not allowlisted`
- **Fix (preferred)**: move the file:
  ```bash
  git mv artifacts/task-orchestrator/DMX-EMBEDDED-AUDIT-PR-CLEANUP-RECONCILED/load_plan.json \
         reports/task-orchestrator/DMX-EMBEDDED-AUDIT-PR-CLEANUP-RECONCILED/load_plan.json
  ```
  Then `rmdir` any empty `artifacts/...` chain. Update any references to the old path (search: `grep -rn "artifacts/task-orchestrator/DMX-EMBEDDED-AUDIT-PR-CLEANUP-RECONCILED" .`).
- **Alternative**: add `"artifacts"` to allowlist in `config/repo_hygiene/root_hygiene_policy.json`. Only do this if the policy owners explicitly accept a new top-level directory.

**Thread repairs**:

1. **P1 (outdated), `tools/pr_action_bridge/compiler.py`**: Reads top-level `pr_number`, but real `MERGE_READINESS.json` from `tools.pr_steward.classifier.build_artifacts` emits `pr.number` (nested). Update compiler to read `payload["pr"]["number"]` with fallback to top-level for backward compat, then drop the fallback after one merge cycle.

2. **P2 (outdated), `scripts/audit/build_evidence_bundle.py`**: Writes absolute `--allowed-root` paths into `manifest.json`. Normalize to repo-relative:
   ```python
   allowed_root = Path(allowed_root).resolve().relative_to(repo_root)
   ```
   Falls back to a `relpath` if cross-drive.

3. **`docs/ops/pr-action-bridge.md:97`** (Copilot): Doc still imports `compile` (now `compile_action_plan`) and calls `compile(...)`. Update doc to current API surface introduced by TP-DMX-PR-ACTION-BRIDGE-006.

4. **`templates/copilot/PR_REPAIR_PACKET.md:16`** (Copilot): Supervisor-prohibition list omits `proof-missing` and `unknown-pr-author` categories added by TP-DMX-PR-STEWARD-HARDEN-010. Add them explicitly.

5. **P2, `tools/pr_action_bridge/compiler.py:82`**: When reading `CI_TRIAGE.json` from classifier, match the actual field names (`name`, `required`, `status`) instead of legacy aliases. Confirm field names by `python -c "from tools.pr_steward.classifier import build_artifacts; help(build_artifacts)"`.

**Validation pipeline**:
```bash
# 1. Re-run lint locally to confirm hygiene passes
python scripts/check_root_hygiene.py $(git diff --name-only --diff-filter=ACMR origin/main...HEAD)
# 2. Re-run unit tests
pytest tests/pr_steward tests/pr_action_bridge tests/audit -xvs
# 3. Re-run classifier+bridge end-to-end on a sample PR
python -m tools.pr_steward.classifier --pr <NUM> > /tmp/MR.json
python -m tools.pr_action_bridge.compiler /tmp/MR.json
```

**Rollback**: this PR has 12 task packets and 84 files — bias toward small, well-tested commits, and rebase, don't squash. If anything goes wrong after merge, prefer reverting individual files over the entire merge.

---

## 2. Cross-cutting risks

- **Palette collisions (#700/#703/#715)**: same file, overlapping fixes. Pick one canonical PR (recommend #715), close the others, do not merge all three.
- **Governance-stack ordering (#713 → #717 → #714 → #716 → #718)**: PR Steward and the action bridge share data shapes. Land foundations first; later PRs can rebase on top.
- **PR Steward "BLOCKED"**: the workflow uses an in-repo classifier that reads unresolved threads. Resolving threads (or marking them outdated) is the gating signal for those PRs to clear. None of the BLOCKED PRs are git-conflict-blocked.
- **Proof bundles**: AGENTS.md §9 requires durable proof bundles for repo-changing work. Several PRs (notably #714 and #716) ship proof bundles missing required fields. Fixing those is cheap and unblocks classifier acceptance.
- **#706 close**: confirm with the author before closing (PR was filed by `hu3mann`; #707 also filed by same author so likely just a stale duplicate window).

---

## 3. Recommended merge order

Pick the smallest unit of work first; quick wins clear the queue and reduce the risk surface for the large PRs.

1. **`gh pr close 706`** — duplicate of merged #707. No fix needed.

2. **Palette resolution** (#700/#703/#715): **needs a human design call** because the three branches conflict (not supersets). Sequence:
   - Run `git diff origin/main...origin/palette-ux-improvements-7854933912242465786 -- ui-dashboard/src/App.tsx > /tmp/p700.diff` and similar for #703, #715, then have a human (or design owner) review which changes to keep.
   - Apply chosen branch's repair (likely #715 + a11y patches from §1.715), cherry-pick what's needed from the others, then close the rest.
   - Cannot be automated safely; flagged for human decision.

3. **PR #717** (PR Steward proof-freshness hardening). Land before any PR that depends on classifier output.

4. **PR #713** (auditor-router pal-clink) — independent of stewardship; 5 small Python tightenings.

5. **PR #712** (CostProfile F verify) — one-line gate tightening; merge after lane is quiet.

6. **PR #716** (FOLLOWUP packets, plan-only) — fix CLI references, packet ID, PROOF blockers.

7. **PR #714** (operator workflows) — the largest scope change. Land only after #717 and #716 so its proof bundles and consumer references are stable.

8. **PR #718** (audit+PR cleanup series) — depends on #717 (proof-freshness contract) and ideally #716 (FOLLOWUP packets that this PR's bridge consumes). Land last in the queue.

---

## 4. Quick-reference command appendix

### Per-PR repair branch checkout

```bash
# Find branch
gh pr view <N> --json headRefName --jq .headRefName
# Check it out as a worktree
git fetch origin <branch>:<branch>
git worktree add ../dopemux-pr-<N> <branch>
cd ../dopemux-pr-<N>
```

### Rebase a BEHIND PR

```bash
git fetch origin main
git rebase origin/main
# resolve conflicts if any
git push --force-with-lease
```

### Verify unresolved review threads after pushing fixes

```bash
gh api graphql -f query='query{repository(owner:"DDD-Enterprises",name:"dopemux-mvp"){pullRequest(number:<N>){reviewThreads(first:100){nodes{isResolved path comments(first:1){nodes{author{login} body}}}}}}}' --jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false)] | length'
```

### Re-run failed checks after pushing

CI auto-triggers on push. To force a rerun without a push:

```bash
gh run rerun <run-id>
# Or rerun only failed jobs:
gh run rerun <run-id> --failed
```

### Mark a thread resolved (after pushing a fix that addresses it)

GitHub UI only — reviewer or repo admin resolves. Codex/Copilot review threads can be resolved by the author after pushing the fix.

### Close a duplicate PR

```bash
gh pr close <N> --comment "Superseded by #M (<reason>). Closing without merge."
```

### Merge a ready PR (squash strategy is repo default; check first)

```bash
gh pr merge <N> --squash --delete-branch
# or
gh pr merge <N> --merge --delete-branch
```

---

## 5. What this plan deliberately does NOT do

- Doesn't merge anything for you — every merge step is explicit and gated on validation.
- Doesn't override AGENTS.md governance — proof bundle fixes follow the §9 contract.
- Doesn't paper over the PR Steward classifier — fixes for #717 deliberately tighten the contract rather than loosen it.
- Doesn't speculate on root causes of the lint failure beyond what's in the CI log; the policy says `artifacts/` is forbidden, so the fix is concrete.
- Doesn't touch PRs <#700 (those are outside the requested scope).

---

## 6. Confidence and remaining uncertainty

- **HIGH** confidence on: failing CI cause for #718 (read the log directly), duplicate status of #706 (verified diff vs #707 file paths), thread inventories (verified via GraphQL), #703 broken JSX (confirmed by `git show ... | grep -n "</Tooltip"`), palette PRs are NOT supersets of each other (confirmed by diff stats and grep for added functions).
- **MEDIUM** confidence on: exact field shapes in `tools/pr_steward/classifier.py` and `MERGE_READINESS.json` — the repair guidance for #717/#718 names fields from the review comments. **Gemini MUST re-read these files before editing** because line numbers and field names may have drifted.
- **MEDIUM** confidence on: the real meaning of the `BLOCKED` mergeStateStatus. Branch protection is unusually permissive (`required_approving_review_count: 0`, no code-owner reviews), so the gate is almost certainly "conversations unresolved" (not exposed by branch-protection API) or the PR Steward in-repo gate. Look at the PR UI's "Merge blocked by:" string per-PR for confirmation.
- **UNKNOWN**: whether the palette PRs (#700/#703/#715) reflect deliberate parallel exploration or stale-PR drift. Recommend pinging the author (`@hu3mann`) directly before closing #700 and #703.

**Final gate before any merge**: run `pytest -xvs` for the affected module subtree, run the PR Steward classifier locally, confirm the proof bundle is well-formed per the AGENTS.md §9 field list quoted in §1 of this plan, and `Read` the actual target file before applying any line-numbered patch.

---

End of plan.
