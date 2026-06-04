# Audit — PR #713 "Auditor Router PAL-clink classification" (TP-DMX-AUDITOR-ROUTER-PAL-CLINK-002)

- **Auditor**: Claude Code (read-only audit), 2026-05-30
- **Trigger**: User handed a stale Codex status report ("act as auditor") describing pushed fixes to `codex/tp-dmx-auditor-router-pal-clink-002` at `f4e7f997a`.
- **Audit target**: `origin/main` (merged state), **not** the temp worktree the report references.
- **Method**: live `gh`, git history/relationship analysis, proof-bundle reading, merged-code inspection, and independent runtime verification (repro + targeted test run).

---

## Ground truth (corrects the handed report)

The handed report is a **point-in-time snapshot (~May 26)** that is now stale. Live state:

| Claim in report | Actual (verified) |
|---|---|
| "PR #713 is open and no longer draft" | **MERGED** to `main` at `be5a31d98` on **2026-05-28T20:38:59Z** by `hu3mann` (auto-merge, MERGE method, enabled 2026-05-28T07:16:27Z) |
| Head `f4e7f997a…` | `f4e7f997a` is **not** in `origin/main`; branch was rebased before merge, content landed under new SHAs (`ba8f579be`, `6a61a4208`, `52362f483`, …) |
| "embedded audit remains NEEDS_SUPERVISOR (no CLI in PATH)" | True **at report time**; **resolved before merge** — a real external clink audit ran later (see F1) |
| PR Steward blocks (REVIEW_ITEM_MUST_FIX / EMBEDDED_AUDIT_NEEDS_SUPERVISOR / PROOF_STALE) | Report-time PR-Steward state; **superseded** by merge. Not re-litigated here. |

The work was authored on a `codex/*` branch in a Codex worktree (`PROOF.json repo.path = /Users/hue/.codex/worktrees/693f/…`); commits are stamped under `hu3mann`'s account. Per repo norms, Codex vs human commits are not separable — attribution stated as "merged via auto-merge under hu3mann's account," nothing stronger.

---

## Headline verdict

**The merge is NOT a laundered PASS.** A genuine external PAL-clink audit executed and earned `PASS_WITH_RISKS`; the bundle even preserved its own negative evidence (sandbox-blocked first attempt, scope conflict, the auditor's own finding against the proof). Honesty is largely intact.

**However**, for *governance/auditor* tooling the bundle falls short of clean: the external auditor's one required MEDIUM fix **shipped unactioned** (independently reproduced), the proof bundle is **internally inconsistent and overstates test results**, and **3 security-hardening regression tests are dead on import** in merged main. Net: **ACCEPTABLE-WITH-DOCUMENTED-DEBT**, but the auditor router's own proof bundle is not self-consistent or schema-clean — a notable irony for the surface it governs.

---

## Findings

### F1 — Embedded external audit genuinely ran (POSITIVE / resolved)
`proof/…/PAL_CLINK_AUDIT_OUTPUT.json` carries hard-to-fake provenance: `model_used=claude-haiku-4-5` + `claude-sonnet-4-6`, `cli_name=claude`, `role=codereviewer`, `duration_seconds=260.087`, `total_cost_usd=0.62779825`, real token/cache counts, `session_id=eef8a57f…`, `num_turns=12`, `return_code=0`. The audit read 12 bundle files, analyzed 14 criteria (all PASS) with line-level citations, returned `verdict=PASS_WITH_RISKS` / `final_recommendation=ACCEPT_WITH_RISKS`, `blocking_findings=[]`. The `NEEDS_SUPERVISOR` in the handed report was a true earlier state, superseded by a bundle-local re-run (`c4e953d78`).

### F2 — External auditor's required MEDIUM fix shipped UNACTIONED (MEDIUM, latent; **VERIFIED by execution**)
The clink audit's sole `required_fix`: guard `_embedded_audit_model` / `normalize_pal_clink_audit_output` against emitting `auditor_model="unknown"` with `status="NEEDS_SUPERVISOR"` (violates `embedded_audit.schema.json allOf[1]`), and add a schema-validation test.

In merged `tools/auditor_router/pal_clink.py`:
- `normalize_pal_clink_audit_output` sets `status="NEEDS_SUPERVISOR"` for an unproven route (lines ~296–298) → `build_pal_clink_embedded_audit_object` sets `auditor_model=_embedded_audit_model(route)` (line ~348) → `_embedded_audit_model` returns `"unknown"` when `underlying_cli ∉ {claude,gemini}` (lines ~491–496). **No guard added.**
- The only `assert_schema_valid` on an embedded audit (test line ~581) uses a *proven* route (`auditor_model="sonnet"`, `status="FAIL"`) — it never exercises the `unknown`+`NEEDS_SUPERVISOR` path.

Independent repro (merged code, current worktree):
```
route = {'audit_safe_config_proven': False, 'underlying_cli': None}
→ status=NEEDS_SUPERVISOR, auditor_model=unknown
→ embedded_audit.schema.json: "'unknown' should not be valid under {'const': 'unknown'}"  (1 error)
```
**Reachability**: `normalize_pal_clink_audit_output` currently has **no production caller** (only test callers). So this is a *latent* defect (defense-in-depth gap) that becomes live when the auditor-router runtime is wired to call `normalize`. `be5a31d98` ("Task R1 hardening") addressed Codex-review-thread items (shlex, mutation tokens, path traversal) — **not** this clink-audit MEDIUM.

### F3 — `PROOF.json` internally inconsistent vs its own audit report (MEDIUM, proof integrity)
In the **same merged bundle**:
- `PROOF.json route_behavior`: `external_cli_called_for_pal_clink=false`, `pal_clink_attempt_result="SANDBOX_BLOCKED"`, `pal_clink_attempted_clients=["claude"]`.
- `AUDITOR_REPORT.md` + `PAL_CLINK_AUDIT_OUTPUT.json`: clink "completed host-side… read all 12 attached files," `return_code=0`, `PASS_WITH_RISKS`.

The successful bundle-local re-run is **not reflected** in `route_behavior`; a machine consumer parsing `PROOF.json` would conclude the audit was sandbox-blocked. (Partly defensible: `pal_mcp_called=true`/`external_cli_called=false` describe the *router's* static-only contract per the auditor's Criterion 2 — but `pal_clink_attempt_result=SANDBOX_BLOCKED` as the sole recorded result is stale.) Also minor: `repo.base_sha=898310bd0` (#711) is stale relative to the actual merge base.

### F4 — `PROOF.json embedded_audit` understates the audit (MEDIUM, proof completeness)
Final `embedded_audit.findings=[]`, `fixes_applied=[]`, and `remaining_risks` lists only process blockers — it **drops the auditor's 1 MED + 2 LOW findings and its `required_fix`**. The substantive code finding survives only in raw `PAL_CLINK_AUDIT_OUTPUT.json`. The structured proof a consumer would read says the audit found nothing actionable; the audit actually issued a required fix (F2).

### F5 — "External" audit assurance is bounded (RISK / limitation)
(a) **Same-vendor**: Claude (haiku/sonnet) auditing Claude/Codex-authored code; `gemini-audit` configured but not the client that ran; copilot deferred. Not cross-vendor independence.
(b) **Bundle-local, not live diff**: audit ran against a curated 12-file evidence package in `~/.zen-mcp-server/audit-bundles/…`, `repo_context_sent=false`. The auditor self-disclosed `models.py`, fixtures, and `scripts/auditor-preflight` were **absent from the bundle** → Criterion 11 "verified by inference only." The `PASS_WITH_RISKS` is bounded by what was handed to the auditor, not the full change in repo context.

### F6 — Scope creep on a contract-sensitive surface (MEDIUM, hygiene)
`d97772503` ("classification tightening", +1796 lines) bundled unrelated artifacts into a governance-tooling commit: `claudedocs/CROSS_REPO_INVENTORY.md`, `claudedocs/pr-718-remediation-plan-for-agy.md` (+1033), a pr700 remediation plan, and two task-orchestrator session JSONs. Inflates blast radius and muddies provenance of the auditor-router change.

### F7 — Merge below AGENTS.md §8 "VERIFIED" bar; advisory check red (OBSERVATION — distinct axes)
- **Governance bar**: AGENTS.md §8 ("Proof and Finality") requires final confidence `VERIFIED`. The bundle self-classifies `PASS_WITH_RISKS` with 2 open blockers (`MISSING_BASELINE_AUDITOR_ROUTER_ON_MAIN`, `BLOCKED_BY_GITHUB_WORKFLOW_DISPATCH_500`). Merging at PASS_WITH_RISKS is a **documented human risk-acceptance** (auto-merge by hu3mann), not a concealed bypass. AGENTS.md defines no explicit "steward red blocks merge" rule, so no hard-gate violation is asserted.
- **Branch protection**: the failing `💅 Code Quality & Linting` check at merge is **advisory** — not in main's required contexts (`Security Review`, `Documentation Check`, `identity-check`, `Unit Tests`, `Analyze ×3`, `ci-summary`), all of which were green. GitHub permitted the merge. Keep this separate from the governance bar above.

### F8 — Failing tests + CI coverage gap + non-reproducible proof count (MEDIUM, **VERIFIED by execution**)
Under the repo's canonical invocation (`python -m pytest …`, `pythonpath=src`, `tools` as a root-relative namespace pkg; `tests/conftest.py` injects only `src`, not `tools`):
```
3 failed, 43 passed        (test_pal_clink.py)
3 failed, 47 passed        (tests/auditor_router/)
```
The 3 failures are the security-hardening tests added by `be5a31d98` — `test_as_args_shlex_parsing`, `test_detect_mutation_flags_new_tokens`, `test_canonical_role_prompt_path_strict` — each erroring `ModuleNotFoundError: No module named 'auditor_router'`. They use function-local `from auditor_router.pal_clink import …` (lines 766/773/779) while the rest of the file uses `from tools.auditor_router.pal_clink import …` (lines 10/11/20). No `conftest.py` (root or `tests/`) puts `tools/` on `sys.path`, so the bare import resolves in **no** standard configuration.

Three compounding facts (all verified, not inferred):
1. **CI never ran these tests.** The required `🧪 Unit Tests` job (`.github/workflows/ci-complete.yml`, job `tests`) runs an enumerated path list — `tests/unit`, `tests/test_voice_core.py`, `tests/test_brand_voice.py` — and **does not collect `tests/auditor_router/`**. The other pytest jobs (`extractor-smoke`, `audit-validator`, integration) are RTE/other-scoped; `🔗 Integration Tests` was SKIPPED for #713. So the green Unit Tests check is **not evidence** the auditor_router code or tests pass — that surface was outside every CI test gate on #713.
2. **Canonical local run fails.** As above, 3 of 46/50 error on import.
3. **Proof count not reproducible.** `PROOF.json` (updated in `be5a31d98`) records "46 passed / 50 passed." That count is reproducible in neither CI (doesn't run them) nor canonical local pytest (3 fail). It was evidently produced in a non-standard cwd/`pythonpath` where the bare `auditor_router` import resolves.

Impact: the new **security-hardening coverage is dead** (shlex injection, `execute/run/apply` mutation tokens, absolute/traversal/whitespace path rejection unexercised), and the recorded pass count overstates what any standard environment reproduces. (Scope note: a brand-new bootstrap surface not yet wired into CI is partly expected; the import bug + the recorded-but-unreproducible count are the defects.)

### F9 — Stale next-step directives in handed report (OBSERVATION)
The report's trailing `::git-commit{cwd=…wt}` / `::git-push{branch=…pal-clink-002}` point at the now-stale detached worktree (`f4e7f997a`). Acting on them is a no-op-or-harmful (PR merged, branch rebased). **Not acted on.** A pal-clink PR family exists (#711 configs, #713 this, `…-WRAPPER-003`/`…-RUNNER-003` follow-ups); this audit is scoped to #713.

---

## Validation performed

**PASS (ran, succeeded)**
- F2 repro: unproven route → `auditor_model="unknown"` + `NEEDS_SUPERVISOR` → 1 schema error (matches auditor's prediction).
- 43/46 `test_pal_clink.py` and 47/50 dir tests pass (the passing majority confirms core behavior).
- Provenance corroboration of F1 (model/cost/token/session metadata internally consistent).
- Git relationship analysis (commit ancestry, merge metadata, required-check list) via `gh`/git.
- CI scope (F8): read `ci-complete.yml` + all `conftest.py` — confirmed no `tools/` `sys.path` injection and that the required `🧪 Unit Tests` job does not collect `tests/auditor_router/`.

**FAIL (ran, failed)**
- 3 security-hardening tests error on import (F8), reproducibly, in merged main.

**NOT_RUN (skipped, with reason)**
- Re-running the embedded PAL-clink audit — out of scope for a read-only audit and likely to hit the same CLI/sandbox constraint; it is the prior agent's requested next step, not the auditor's.
- Full lint reproduction of the advisory `Code Quality & Linting` failure (F7) — advisory, non-required.

---

## Recommendations (priority order)

1. **F8 (do first, cheap, real)**: fix the 3 import paths to `from tools.auditor_router.pal_clink import …` so the security-hardening tests actually run; re-baseline the `PROOF.json` test counts to the canonical environment. Confirm CI collects `tests/auditor_router/`.
2. **F2**: add the guard the external auditor required (reject `auditor_model="unknown"` for non-`SKIPPED` status, or restrict `normalize` to AVAILABLE routes) **before** any runtime is wired to call `normalize`; add the missing `assert_schema_valid` test on the `NEEDS_SUPERVISOR`+unproven path.
3. **F3/F4**: make `PROOF.json` self-consistent — record the successful bundle-local re-run in `route_behavior`, and carry the auditor's MED/LOW findings + required_fix into `embedded_audit.findings`/`remaining_risks` rather than `[]`.
4. **F6**: avoid bundling unrelated remediation docs/session JSONs into governance-tooling commits.
5. **F5**: when feasible, run a cross-vendor (`gemini-audit`) clink pass and/or audit the live diff (not only a curated bundle) for higher assurance on this surface.

---

## Appendix — commit map (merged main)

```
be5a31d98  fix(governance): apply Task R1 hardening to pal_clink.py     <- merge HEAD; adds 3 broken-import tests (F8)
d97772503  feat(governance): PAL-clink classification tightening (+1796) <- scope creep (F6)
c4e953d78  chore(proof): capture pal clink audit verdict                 <- bundle-local rerun → PASS_WITH_RISKS (F1)
bf92149e4  chore(proof): record pal clink sandbox-blocked audit          <- honest negative evidence
ba8f579be  fix(governance): harden pal clink config shape validation     (= report's f4e7f997a)
6a61a4208  fix(governance): validate pal clink command and overrides     (= report's 92ca508aa)
52362f483  docs(proof): record failed pal clink audit attempt            (= report's e3246aee0)
973bfaed5  feat(governance): bootstrap auditor router pal clink classification
```
Merged 2026-05-28T20:38:59Z by hu3mann (auto-merge MERGE). Required checks green; advisory `Code Quality & Linting` red.
