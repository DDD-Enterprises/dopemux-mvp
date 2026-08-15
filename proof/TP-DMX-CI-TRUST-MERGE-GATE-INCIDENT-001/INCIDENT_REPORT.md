# INCIDENT_REPORT — TP-DMX-CI-TRUST-MERGE-GATE-INCIDENT-001

**Risk**: L3
**Stage**: Phase A complete (read-only investigation). Phase B not started.
**Status**: append-only record

## 1. Identities

- Repo: `DDD-Enterprises/dopemux-mvp`
- `main` (current, post-#1227): `75b4cfc581786a53445e412bfc8e25a6e0fdb978`
- PR #1227: `tp/DMX-SB-ADR-CONTRACT-EVIDENCE-001` → `main`
  - head: `da2523aafb6725be33f7bb69bc5eb50764d7394c`
  - merge commit: `75b4cfc581786a53445e412bfc8e25a6e0fdb978`
  - merged_by: `hu3mann` (admin permission on repo)
  - merged_at: `2026-08-13T17:36:52Z`
- PR #1224 (parked, unaffected): head `83ef9e30440bf3d1481bfe61beedf80e48afe6f9`, non-draft, mergeable, Steward green, review threads resolved. **Remains `READY_FOR_OPERATOR_MERGE_DECISION`; not touched by this incident or its investigation.**

## 2. Chronology (PR #1227, exact head `da2523aafb`)

| Time (UTC) | Event | Evidence |
|---|---|---|
| 2026-08-13T17:29:57Z–17:32:xx | CI suite runs on head | `evidence/head_sha_check_runs.json` |
| 2026-08-13T17:30:20Z | `independent embedded audit` check-run → **FAILURE** | `evidence/head_sha_check_runs.json`, `evidence/pr1227_view.json` |
| 2026-08-13T17:30:28Z (run 31726038754) | `PR Steward / final readiness` **status context** → **FAILURE**, description: `final readiness not READY for PR 1227 (audit=failure/failure steward=skipped)` | `evidence/head_sha_status_api.json` |
| 2026-08-13T17:36:52Z | PR merged by `hu3mann` | `evidence/pr1227_full.json`, `evidence/pr1227_timeline.json` |

All other CI check-runs (Unit Tests, CodeQL, Security Review, identity-check, CI Pipeline Summary, etc.) were `SUCCESS`.

## 3. Two distinct signal types — this matters

GitHub carries two independent mechanisms that both surface as "checks" in the PR UI but are enforced separately:

- **Check-runs** (GitHub Checks API) — e.g. `independent embedded audit`. Reported **FAILURE**.
- **Commit statuses** (legacy Status API) — e.g. `PR Steward / final readiness`. Reported **FAILURE**, and does not even appear in `statusCheckRollup` via `gh pr view`'s default fields the same way check-runs do; it had to be queried directly via `GET /commits/{sha}/status`.

Both are real, both failed. Neither blocked the merge.

## 4. Why the merge was not blocked (root cause)

Two merge-gate enforcement surfaces exist on this repo, and **neither lists the audit or Steward gate as required**:

### 4a. Classic branch protection (`GET /branches/main/protection`)
`required_status_checks.contexts` = exactly:
```
🔒 Security Review, 📚 Documentation Check, identity-check,
🧪 Unit Tests, Analyze (python), Analyze (javascript-typescript),
Analyze (ruby), 📊 CI Pipeline Summary
```
`independent embedded audit` and `PR Steward / final readiness` are **absent** from this list. `enforce_admins.enabled = false`.

### 4b. Modern ruleset (`GET /rulesets/13063360`, "Default branch protection (restored after history rewrite)")
`rules` = `deletion`, `non_fast_forward`, `pull_request` (0 required approvals, required thread resolution, squash/rebase only), `copilot_code_review`. **There is no `required_status_checks` rule type in this ruleset at all** — it does not gate on any CI signal, green or red.
`bypass_actors` grants `OrganizationAdmin` and two `RepositoryRole` ids `always` bypass, and `current_user_can_bypass: "always"` — but this is moot here, since no status-check rule existed to bypass.

**Conclusion: both required-check lists were satisfied because the failing gates were never in either list.** GitHub did not misbehave, no admin bypass flag was exercised, and no stale-status caching occurred — the merge was permitted exactly per configuration. `hu3mann` merged a PR that, from GitHub's protection-rule perspective, had 100% of *required* checks green; the two workflows built to be the actual final gate were invisible to enforcement.

**Classification: B — repository configuration defect** (gate-wiring gap), not A (process/operator bypass), not C (workflow/status publication defect — the workflows correctly published FAILURE), not D (GitHub enforcement mismatch — GitHub enforced its configuration correctly).

## 5. This is a known, previously-deferred gap, not a new regression

`pr-steward.yml` and `embedded-audit.yml` were explicitly hardened to **fail closed** in commit `db9b844fc7` ("make independent audit and Steward fail closed", #1042) — i.e., the intent was unambiguous: these are supposed to be blocking gates.

However, `proof/TP-DMX-PR-STEWARD-HARDEN-010/AUDITOR_REPORT.md` line 113 records, as an explicit **PASS** criterion for that hardening packet: **"No branch protection mutation."** That packet deliberately scoped out wiring the new fail-closed status into GitHub's required-checks list. No later packet closed that gap. The two enforcement mechanisms (branch protection contexts, ruleset rules) have not been touched to add either check since at least `2026-04-21T12:30:04Z` (ruleset `updated_at`) — well before Steward/audit fail-closed hardening shipped.

So: the gate was built to fail closed in *workflow logic*, but was never connected to *merge enforcement*. It has silently been advisory-only for every PR merged since.

## 6. Scope check on #1224

#1224 is unaffected by this finding — its Steward status is independently green (not merged past a red gate), so its `READY_FOR_OPERATOR_MERGE_DECISION` disposition stands. It was not re-examined further under this incident and was not modified.

## 7. Evidence bundle

All raw API responses backing the above are in `proof/TP-DMX-CI-TRUST-MERGE-GATE-INCIDENT-001/evidence/`:
`pr1227_view.json`, `pr1227_full.json`, `pr1227_timeline.json`, `head_sha_status_api.json`, `head_sha_check_runs.json`, `branch_protection_main.json`, `rulesets_list.json`, `ruleset_13063360_detail.json`, `merger_permission.json`, `gate_workflow_history.txt`.

## 8. Recommended smallest governance control (Phase B candidate — NOT authorized to execute yet)

This is a configuration gap, not a code defect — there is no application code to patch. The smallest closing control is a **branch-protection/ruleset mutation**: add `independent embedded audit` and `PR Steward / final readiness` to `required_status_checks.contexts` (or an equivalent ruleset `required_status_checks` rule).

Per this packet's explicit authorization boundary, **changing branch protection/rulesets requires a fresh, separate operator gate** and is not performed in this Phase A pass. This report and its evidence bundle constitute the deliverable that gate should be granted against.

## 9. Rollback plan

No mutating action has been taken against `main`, branch protection, or rulesets. This incident branch (`incident/TP-DMX-CI-TRUST-MERGE-GATE-INCIDENT-001`) contains only this append-only report and its evidence bundle, branched from `origin/main` at `75b4cfc581786a53445e412bfc8e25a6e0fdb978`. Rollback = delete the branch / do not open a PR; no other state was touched. #1227's merge commit and its failed historical statuses are preserved unmodified.

## 10. Independent second read

**Performed 2026-08-15.** Runner: `agy` CLI (Antigravity) v1.1.13, `--model gemini-3.1-pro-high --effort high --sandbox`, proven-selected (no silent fallback — see `evidence/AGY_VERSION.txt` for exact invocation, `evidence/AGY_AUDIT_GEMINI31_PHASE_A_RAW.json` for raw transcript/usage). Run in an isolated `git worktree` pinned at this branch's exact head `4cb2b1f5916ed9dc05c4d17b11709455a193cfe3` (draft PR #1233), independent from the Claude Sonnet 5 session that authored §1–9.

**Verdict: PASS_WITH_RISKS.** Full text: `evidence/AGY_AUDIT_GEMINI31_PHASE_A.md`. The auditor re-derived every claim in §1–9 from live `gh api`/`git` calls rather than trusting this document, and:
- Independently confirmed the #1227 chronology, the current classic-protection and ruleset configuration, the absence of both gates from either enforcement surface, and that no admin/ruleset bypass was exercised (the merge was fully compliant under the as-configured rules).
- Confirmed `TP-DMX-PR-STEWARD-HARDEN-010`'s "No branch protection mutation" PASS line and that its diff never touched protection config.
- **Softened §5's "advisory-only for every PR since" claim**: only provable back to the ruleset's `updated_at` (`2026-04-21T12:30:04.081-07:00`); classic branch-protection has no exposed mutation history via this API, so the claim should be read as "at least since the ruleset's last update" rather than an unbounded historical guarantee.
- Confirmed no PR-Steward self-referential deadlock risk (`ddd-release-gate.yml` explicitly filters the Steward self-status out of its own readiness evaluation).
- Flagged two **non-blocking** residual risks, both already named in §9/§8 of this report: (a) `PR Steward / final readiness` is a legacy commit status with no GitHub-App identity binding, so any actor with repo write access could POST a spoofed green status for that exact context string — a real gap, but orthogonal to this incident (closing it means migrating Steward off the Status API, out of scope here); (b) `enforce_admins=false` plus the ruleset's always-bypass actors mean privileged bypass remains possible after this fix — explicitly already deferred to a separate authority-policy decision per this packet's scope.

**Correction to the auditor's output — do not use as-is:** the auditor's "Proposed Exact Mutation" JSON snippet sets `"strict": false`. This is wrong and contradicts both the verified live configuration (`evidence/branch_protection_main.json` shows `strict: true`) and the operator's explicit instruction to preserve `strict=true`. Phase B execution uses the verified real value (`strict: true`, 8 existing contexts unchanged, 2 new contexts appended) and disregards this line of the auditor's snippet. Flagging this discrepancy rather than silently correcting it, since it's evidence that even an independent auditor's structured output must be checked against primary sources, not trusted verbatim — consistent with why this audit was required in the first place.

## 11. Phase B execution

See `evidence/PHASE_B_MUTATION.md` for the exact PATCH payload, before/after read-back, and canary validation (PR #1224 not used as canary, per instruction).

## 12. Requested next step (superseded — see §11)

1. ~~Operator reviews this report.~~ Done — conditional authorization received.
2. ~~Independent second-family audit~~ — done, PASS_WITH_RISKS, §10.
3. Operator reviews Phase B execution record (§11) and the canary result.
4. #1224 stays parked at `READY_FOR_OPERATOR_MERGE_DECISION`, unaffected throughout.
