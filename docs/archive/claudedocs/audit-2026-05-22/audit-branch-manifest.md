---
id: rte-audit-2026-05-22-branch-manifest
title: RTE Pre-Debut Audit — Branch Manifest (F0a)
type: audit-artifact
phase: F0a
owner: claude
date: 2026-05-22
status: draft
---

# Audit Branch Manifest — F0a

**Audit branch:** `audit/rte-pre-debut-2026-05-22`
**Worktree path:** `/Users/hue/code/dopemux-mvp-audit-rte-debut`
**HEAD SHA at branch creation:** `ab22df5a23432f0573ce01b2ec7ef0d1bea2420f`
**Base:** `main` at `ab22df5a2` (commit: `docs(governance): add Codex operator runbook and prompt pack (#666)`)
**Prior P5 baseline:** main HEAD `8ea182dd38ecd7754dff1c49224221cc49e390f4` (2026-05-09; was post-#603 readonly fix)
**Commits between P5 baseline and audit-branch HEAD:** 34 commits on main (2026-05-10 → 2026-05-22)

---

## Strategy

The audit-plan called for "rebase remediation branches → audit branch". Survey of open PRs (`gh pr list --search 'rte OR extractor OR repo-truth' --state open`) returned 4 open PRs, **none of which directly close a P5 CRIT**. All six P5 CRIT-closing PRs landed in `main` between 2026-05-10 and 2026-05-14 and are present in the audit branch's history.

**Therefore, the audit branch is `main` as-of `ab22df5a2`, no rebase necessary.** The 4 open RTE-touching PRs are deferred as out-of-scope for the audit (rationale below).

---

## PR → CRIT closure mapping

All seven PRs verified present in `audit/rte-pre-debut-2026-05-22` via `git merge-base --is-ancestor <sha> HEAD`.

| PR # | Title | Merge SHA | Merged | Closes (P5 finding) | Audit-Branch Status |
|------|-------|-----------|--------|---------------------|---------------------|
| [#603](https://github.com/DDD-Enterprises/dopemux-mvp/pull/603) | fix(rte): make introspection commands readonly | `8ea182dd3` | 2026-05-10 | F4-CRIT-1, F4-CRIT-3 | PRESENT (was P5 baseline) |
| [#605](https://github.com/DDD-Enterprises/dopemux-mvp/pull/605) | fix(rte): gate legacy v3 execution and reject unknown pipeline versions | `882a2f4b0` | 2026-05-10 | F1-CRIT-1, F1-CRIT-2 | PRESENT |
| [#606](https://github.com/DDD-Enterprises/dopemux-mvp/pull/606) | fix(rte): exclude generated artifacts from prescan | `c5ea7be47` | 2026-05-10 | F2-CRIT-2 | PRESENT |
| [#614](https://github.com/DDD-Enterprises/dopemux-mvp/pull/614) | fix(rte): repair batch result and strict handling | `9c30e9e86` | 2026-05-14 | F2-CRIT-1, F2-CRIT-3 | PRESENT |
| [#615](https://github.com/DDD-Enterprises/dopemux-mvp/pull/615) | fix(rte): wire strict batch response format | `a4227982f` | 2026-05-14 | F2-CRIT-3 (reinforcement) | PRESENT |
| [#616](https://github.com/DDD-Enterprises/dopemux-mvp/pull/616) | fix(rte): ground strict attestations in runtime evidence | `843a69242` | 2026-05-14 | F3-HIGH-2 | PRESENT |
| [#617](https://github.com/DDD-Enterprises/dopemux-mvp/pull/617) | docs(rte): canonicalize rte operator path | `a4214ca5b` | 2026-05-14 | F4-CRIT-2 | PRESENT |

**Closure coverage (static, by merge):** All 6 P5 CRIT BLOCKING findings have at least one merged remediation PR in the audit branch. Drift verification in F1 will determine whether each is `RESOLVED-WITH-TEST`, `RESOLVED-STATIC`, `NARROWED`, `UNCHANGED`, or `NEW-VARIANT`.

---

## Notable additional RTE work merged since P5 baseline

(Not directly tied to P5 CRITs but in the audit-branch HEAD.)

| PR # | Title | Theme |
|------|-------|-------|
| #620 | fix(rte): redact provider-bound payload content | secret hygiene |
| #621, #626 | fix(rte): reject stale imported prescan | freshness guard |
| #622, #654 | RTE failed sidecar redaction | log redaction |
| #623 | fix rte live gate terminality | gate hardening |
| #624 | label prescan influence surfaces | observability |
| #625 | preserve protected truth labels | data integrity |
| #628 | capture provider response metadata | observability |
| #630 | static batch proof metadata | proof bundle |
| #631 | RTE-PKT-09 live validation plan | runbook |
| #632 | classify proof contract conformance | proof contract |
| #633 | RTE risk dashboard | observability |
| #634 | separate OpenRouter x-ai route metadata | routing |
| #635 | static route fingerprint proof (blake2b→sha256 migration) | route attestation |
| #637 | expose static economic pricing surfaces | cost surfacing |
| #638 | enriched artifact consumer compatibility tests | regression cover |
| #640 | RTE UX valuation pack + authority order reconciliation | UX + governance |
| #642 | opus uiux audit bundle | UX |
| #643, #644 | RTE UX Claude safety guidance + proof replay metadata fix | safety |
| #645 | RTE UX CLI tone emoji cleanup | UX |
| #660 | public AI docs surface + RTE external baseline | docs |

All present in audit-branch HEAD. These represent the "extensive improvements since prior audit" the user referenced.

---

## Open PRs touching RTE (deferred from audit branch)

`gh pr list --search 'rte OR extractor OR repo-truth' --state open` returned 4 PRs:

| PR # | Title | Decision | Rationale |
|------|-------|----------|-----------|
| [#656](https://github.com/DDD-Enterprises/dopemux-mvp/pull/656) | RTE-UX-PKT: harden prelive validator error shape | **DEFER** | UX-only error-shape hardening; does not close any P5 finding. Audit will catch any new issues this PR might address through F2a/F10. |
| [#657](https://github.com/DDD-Enterprises/dopemux-mvp/pull/657) | docs(rte): orchestrate remaining remediation waves | **DEFER** | Meta-orchestration docs; not RTE runtime. |
| [#659](https://github.com/DDD-Enterprises/dopemux-mvp/pull/659) | docs(governance): add governance-principles module | **DEFER** | Cross-cutting governance; not RTE-specific. |
| [#663](https://github.com/DDD-Enterprises/dopemux-mvp/pull/663) | docs: strengthen frontdoor positioning | **DEFER** | Marketing/positioning docs; unrelated. |

**Net:** zero cherry-picks. Audit branch = main as-of `ab22df5a2`.

---

## Existing audit-related work (not in audit branch)

- **`tp-dmx-rte-55pro-audit-assembly-001`** (`/Users/hue/code/dopemux-mvp/.worktrees/tp-dmx-rte-55pro-audit-assembly-001`, branch HEAD `11ddf3b3f`):
  - Contains an assembled "55pro audit pack" under `audit_inputs/` and `audit_prep/` (~25 prompt bundles + reports from 2026-05-14).
  - Bundles include: extraction prompts (~290KB), adjudication prompts (~70KB), output-shaping prompts (~70KB), prescan/repair/retry prompts.
  - Reports A (inventory audit), B (portfolio brain), C (openrouter extension).
  - **Decision:** **DO NOT** adopt as audit branch (carries 100+ unrelated docs/governance changes). **DO** mine for F3 promptset audit context.

---

## Audit branch state

```
$ git status
On branch audit/rte-pre-debut-2026-05-22
Your branch is based on 'main'.
nothing to commit, working tree clean   (before F0a manifest commit)
```

After this manifest commits: 1 file change in `docs/archive/claudedocs/audit-2026-05-22/`.

---

## Exit criteria (F0a)

- [x] Audit branch created from current main HEAD
- [x] All 6 P5 CRIT-closing PRs verified present (via merge-base --is-ancestor)
- [x] PR→CRIT mapping table published
- [x] Open PRs surveyed and dispositioned (defer all 4)
- [x] Prior 55pro audit-assembly worktree triaged (reference-only, not adopted)
- [x] HEAD SHA captured: `ab22df5a23432f0573ce01b2ec7ef0d1bea2420f`
- [ ] Manifest committed to audit branch

---

## Next phase

F0b (Repo Hygiene Sweep) — runs in parallel; both gate F1 (Drift Re-verification).
