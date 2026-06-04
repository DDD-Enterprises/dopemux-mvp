# Open-PR Review Status & Merge Plan (for gpt5.4-mini)

**Generated**: 2026-06-03 · **Repo**: DDD-Enterprises/dopemux-mvp · **Target**: `main`
**Author of analysis**: Claude (read-only audit; no merges performed)

**Execution status**: completed on 2026-06-03. The merge wave below has been
executed against live GitHub state; the remaining sections are the original
pre-execution analysis preserved for auditability.

## 0. Execution result (live state)

- `#781` MERGED
- `#796` MERGED
- `#793` MERGED
- `#791` MERGED
- `#785` MERGED
- `#794` MERGED
- `#795` MERGED
- `#784` CLOSED as superseded by `#791`

Historical notes about unresolved threads, branch protection, and merge order
below were accurate at analysis time but are no longer current.

## 1. Claude-review status

**None of the 32 open PRs have a Claude-authored review.** Existing feedback is from
`chatgpt-codex-connector` (Codex), `copilot-pull-request-reviewer`, and `google-labs-jules`
only. So "PRs that have yet to have a Claude review" = **all of them**.

## 2. Merge gates on `main` (verified via branch-protection API)

- `required_approving_review_count: 0` — reviews are **not** a hard merge gate.
- `required_conversation_resolution: enabled` — **all review threads must be resolved** → this is why 795/794/793/791 are `BLOCKED`.
- `required_status_checks.strict: true` (up-to-date) — a PR must contain main's latest HEAD → why 784/785 are `BEHIND`, **and why every merge re-stales every other open PR** (forces serialized merges).
- Required checks: Security Review · Documentation Check · identity-check · Unit Tests · Analyze (py/js/ruby) · CI Pipeline Summary.

## 3. PR classification

### TIER 1 — MERGE NOW (to `main`, in this order)

Order is set by: keystone-first (largest blast radius, currently clean, rots fastest), then security, then readiness. Because `strict=true`, **each merge forces an `update-branch` + CI re-run on the next PR** — this is inherent, not avoidable by reordering.

| # | Order | PR | State | Blocker to clear | Note |
|---|-------|----|----|------------------|------|
| `#781` | 1 | autoreview platform integration (60 commits, 115 files) | CLEAN | none | **Keystone.** Supersedes 7 steward drafts (close after). No file overlap with #794. |
| `#794` | 2 | fix(security): remove ADHD weak secret defaults | BLOCKED | 3 unresolved threads | Security — prioritize. Zero file overlap with #781. |
| `#796` | 3 | test(adhd): dashboard state wiring | CLEAN | none (will go BEHIND after #781) | Trivial. |
| `#793` | 4 | fix(adhd): wire interactive prompts into launch/profile | BLOCKED | 1 unresolved thread | |
| `#795` | 5 | test(adhd): enforce activity payload privacy | BLOCKED | 2 unresolved threads | |
| `#791` | 6 | 🎨 Palette: Dynamic Feedback & Progress UI | BLOCKED | 3 unresolved threads | **Superset of #784** (same files + TeamDashboard.tsx). Close #784. |
| `#785` | 7 | chore(deps-dev): bump vitest 4.0.18→4.1.0 | BEHIND | update-branch | Lowest risk; can land anytime. |

### TIER 2 — CLOSE (superseded, do not merge)

- **Steward stack → folded into #781**: `#765 #766 #767 #770 #772 #775 #779` (all draft). Close with comment "superseded by #781" once #781 merges.
- **Palette duplicate**: `#784` (subset of #791). Close once #791 merges.

### TIER 3 — HOLD (WIP drafts, not in merge scope)

- **ADHD cognitive-remediation chain** (12-deep draft stack, base = each other / `feat/autoreview-platform-series`): `#771 #773 #774 #776 #777 #778 #780 #782 #783 #786 #787 #788 #789 #790`. This is the 39-TP remediation program — not ready.
- **#792** docs(adhd) → `feat/autoreview-platform-series`: UNSTABLE (lint failing), and its base lineage is orphaned (see risk below).

## 4. gpt5.4-mini runbook (deterministic, per-PR loop)

For each PR in Tier-1 order, run this loop. Do **not** parallelize merges (strict mode serializes).

```
For PR N in [781, 794, 796, 793, 795, 791, 785]:
  1. REVIEW:   gh pr diff N   → sanity-check scope matches title; no secrets, no unrelated files.
  2. THREADS:  gh api graphql ... reviewThreads → for each isResolved=false:
                 - read the comment; confirm the concern is addressed in the diff OR is a non-issue.
                 - resolve it: gh api graphql -f query='mutation{resolveReviewThread(input:{threadId:"<id>"}){thread{isResolved}}}'
                 - if a thread flags a REAL unaddressed bug → STOP, do not merge, report it.
  3. UPDATE:   if mergeStateStatus is BEHIND → gh pr update-branch N ; then wait for required checks to pass.
  4. WAIT:     gh pr checks N --watch  (all required checks must be 'pass').
  5. MERGE:    gh pr merge N --squash --delete-branch   (only when mergeStateStatus == CLEAN).
  6. POST-781: after #781 merges, close superseded drafts:
                 for d in 765 766 767 770 772 775 779: gh pr close $d -c "Superseded by #781 (consolidated integration)."
  7. POST-791: after #791 merges: gh pr close 784 -c "Superseded by #791 (superset of these UI changes)."
```

**Guardrails for mini (low-judgment safe):**
- Never resolve a thread you cannot map to a concrete line in the diff that addresses it. When unsure → STOP and escalate to Claude/human.
- Never `--admin`-override a failing required check.
- Squash-merge only. Delete branch on merge.
- One PR at a time, top to bottom. Re-fetch `mergeStateStatus` before every merge.

## 5. Risks / open decisions (need human/Claude, not mini)

- **`feat/autoreview-platform-series` is orphaned**: it's only the 2 seed commits; #781 (codex integration) is a *different lineage* and does NOT contain it. After #781 lands, the ADHD draft stack + #792 target a base that never reaches main. **Decision needed**: retarget the ADHD remediation program to `main`, or rebuild on post-#781 main. (Out of mini's scope.)
- **#781 is 115 files / 7162 additions** — green CI + 24/24 threads resolved, but a human/Claude should eyeball the integration-repair slice before the squash, given blast radius.
- **#794 is security** — confirm the 3 codex threads are genuinely addressed (fail-closed secret handling) before resolving, not rubber-stamped.

---

## 6. Claude review outcomes (2026-06-03, posted as PR comments)

`gh` is authed as the PR author (`hu3mann`), so reviews were posted as comments (GitHub blocks formal self-reviews). Thread verdicts rendered with evidence; non-blocking/false-positive threads resolved, real-bug threads kept open.

| PR | Verdict | State now | Threads acted |
|----|---------|-----------|---------------|
| #781 | ✅ APPROVE (caveat: 115-file blast radius, eyeball schema/policy slice) | CLEAN | 0 open |
| #796 | ✅ APPROVE (test-only) | CLEAN | — |
| #793 | ✅ APPROVE (nit) | CLEAN | resolved unused-imports (non-blocking) |
| #791 | ✅ APPROVE (3 nits) | CLEAN | resolved 3 TS nits (non-blocking) |
| #785 | ✅ APPROVE | BEHIND → update-branch | — |
| **#794** | ⚠️ **REQUEST CHANGES** | BLOCKED | resolved Fernet (false +ve); **kept open ×2 empty-ENV fail-open** |
| **#795** | ⚠️ **REQUEST CHANGES** | BLOCKED | **kept open ×2 numeric-field content smuggling** |

### Real bugs found (must fix before merge)
- **#794** — `runtime_environment()` empty-`ENVIRONMENT` bypass (config.py + security_config.py). When `ENVIRONMENT=""` and `DPMX_ENV=production`, resolves to `development` → fail-closed secrets BYPASSED. Empirically reproduced. Fix: `os.getenv("ENVIRONMENT") or os.getenv("DPMX_ENV") or "development"`.
- **#795** — `normalize_file_activity` forwards `seconds_since_last_save` uncoerced + unguarded `int(files_modified)` → content smuggling / log leak through numeric fields. Coerce both; add regression test.
- **#794 Fernet** — Copilot false positive; `Fernet(str)` works on `cryptography==48.0.0` (verified). Resolved.

### Revised merge wave (mini-executable, strict-serialized)
**Ready now:** `#781` → `#796` → `#793` → `#791` → (`#785` after update-branch).
**Hold for fix:** `#794`, `#795` (REQUEST CHANGES — re-review after the numeric-coercion / blank-env fixes land).
**Close after #781:** 765/766/767/770/772/775/779. **Close after #791:** 784.
