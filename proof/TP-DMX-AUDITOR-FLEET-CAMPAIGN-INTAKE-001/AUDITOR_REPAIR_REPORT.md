# Embedded Audit — Repair Pass

**Packet**: TP-DMX-AUDITOR-FLEET-CAMPAIGN-INTAKE-001
**PR**: #1048 (`codex/auditor-fleet-campaign-intake-001`)
**Purpose**: Independent embedded audit of the intake diff, required to close CI gaps on PR #1048 (missing `embedded_audit` proof field; the original assembly session never recorded one).

## Auditor

- **Tool**: `agy` (AGY CLI) — genuinely independent of the Claude Code CLI session that performed this repair
- **Model**: Claude Sonnet 4.6 (Thinking) — distinct model/session from the Opus repair session
- **Invocation**: `agy -p "<audit prompt>" --model "Claude Sonnet 4.6 (Thinking)" --mode plan --add-dir "$(pwd)" --print-timeout 14m`
- **Mode**: `plan` (read-only; no file mutation permitted)
- **Working directory**: `/Users/hue/code/dopemux-mvp-wt-pr1048-repair` (dedicated worktree checked out at PR #1048 head `bf446ccfbfa308e786a4b482255f80be84ae92c7`, plus the uncommitted markdownlint fix)
- **Exit code**: 0

## Method

The repair session pre-computed an evidence bundle (full `git diff --stat`/file-list, a programmatic allowlist check against all 104 committed files, and independent SHA-256 recomputation of all 51 `ACCEPTED` artifacts against `HASH_VALIDATION.json`) and handed it to the auditor as *unverified claims*, not fact. The auditor was instructed to independently spot-check rather than trust the bundle, then render its own verdict.

## Spot Checks Performed (by the auditor, independently)

| Check | Result |
|---|---|
| SC-1: Recompute SHA-256 for 3 arbitrary accepted-tree files | All 3 match `HASH_VALIDATION.json` exactly (`ACCEPTED` / `HASH_AND_SIZE_VERIFIED`) |
| SC-2: `git diff --stat origin/main..HEAD` (live) | `104 files changed, 35314 insertions(+)` — matches bundle claim exactly |
| SC-3: Task packet allowlist vs. committed file list | All 104 committed files fall within the packet's "Allowed Files for Modification" prefixes |
| SC-4: `99-intake/MISSING-OR-MISMATCHED.json` vs. `04-synthesis`/`05-independent-audit` gaps | The 4 missing independent-audit deliverables are formally documented as `MISSING`, matching `INTAKE-STATUS.json`'s `missing_count: 4` |

## Findings

1. **F-001 (HIGH, was OPEN at audit time — now RESOLVED by this repair)** — `GIT_DIFF.patch`, `GIT_DIFF_STAT.txt`, `PATH_ALLOWLIST_CHECK.json`, and `SECRET_SCAN.json` in the proof bundle were captured against a stale intermediate 2-file working-tree diff, not the final 104-file/35,314-insertion commit that was actually pushed. The underlying outcomes (allowlist compliance, no secrets) independently re-verify as correct, but those four proof files misrepresented their own scope. **Fix applied**: all four files regenerated against the true final diff as part of this repair (see `fixes_applied` in `PROOF.json`).
2. **F-002 (MEDIUM, OPEN — accepted, not fixed by this repair)** — The `05-independent-audit/` stage is structurally absent from the evidence tree. This is legitimate: the 4 independent-audit deliverables (`AUDITOR-FLEET-SYNTHESIS-AUDIT.md`, `AUDITOR-FLEET-SYNTHESIS-FINDINGS.json`, `REQUIRED_SYNTHESIS_REPAIRS.md`, `AUDIT_HANDOFF_TO_SUPERVISOR.json`) were never physically supplied to the intake session, and the packet's own instructions forbid creating meaningless empty placeholder directories. Carried forward as a remaining risk, not a defect in this repair's scope (evidence intake cannot synthesize artifacts that were never supplied).
3. **F-003 (LOW, RESOLVED)** — A bug in the repair session's own evidence-bundle lookup script produced a spurious empty-match warning; the underlying `HASH_VALIDATION.json` data was confirmed correct by direct field-level inspection. No defect in the committed artifact.
4. **F-004 (INFO, ACCEPTED_RISK)** — `HASH_VALIDATION.json` carries 72 entries (51 `ACCEPTED` + 21 `PRESENT_UNACCEPTED`); the 21 are correctly excluded from the committed accepted tree and not mislabeled. No leakage detected.

## Verdict

**STATUS: PASS_WITH_RISKS**

The core intake is structurally sound: zero allowlist escapes across 104 committed files, all independently-spot-checked hashes match, no symlinks, no excluded-artifact leakage into accepted locations, no secrets detected in the full diff (re-scanned independently with a broader pattern set than the original `SECRET_SCAN.json`). One real proof-integrity defect (F-001) was identified and is fixed by this repair pass. Two items are carried forward as residual, non-blocking risk (see below) — neither is a violation of the packet's stated invariants.

## Remaining Risks (carried forward)

- `05-independent-audit` deliverables remain formally absent; if a downstream campaign step requires them before further synthesis work, that gap must be closed by re-supplying the source files, not by this evidence-intake packet.
- The content fidelity of `04-synthesis/deliverables/*` against the underlying Deep Research track findings was not cross-checked by this audit (out of scope for an evidence-intake integrity review) and remains unverified.
