# RTE Final Go-Live Audit — before live spend

**Date:** 2026-06-03
**Target:** `main` @ `31d1f168e` (audited in detached worktree `/Users/hue/code/dmx-rte-audit`)
**Auditor env:** Python 3.12.13 / macOS (CI reference env is Python 3.11 / Linux — see Lane 4)
**Scope (user-set):** both local-CLI and networked-MCP surfaces (separate verdicts); a bounded
~$0.05 real-money canary was authorized and executed.
**Prior baseline:** ~575 commits ago (`8ea182dd3`) the audit ended at **6 CRIT BLOCKING →
RUNNABLE-BOUNDED-LANE-ONLY**. This is a fresh verdict.

---

## TL;DR — Verdict

| Surface | Verdict | One-line basis |
|---|---|---|
| **Local-CLI, default (legacy) lane** | **CONDITIONAL-GO / RUNNABLE-BOUNDED-LANE** | Spend gates are real and fail-closed; the engine *self-blocks* until a real config issue (default model 404) is fixed. |
| **Local-CLI, `--s-prompts registry`/SP lane** | **NO-GO until S4 fixed** | SP steps run with **zero contract enforcement** (0 SP entries in contract map) and the only gate that catches it is **P1-waivable**. |
| **Networked-MCP deploy** | **NO-GO without hardening** | Headline MCP2-06 is fixed, but ~15 platform services still bind `0.0.0.0` by default and a default DB password ships in source. |

**Bottom line:** The money-safety machinery (dry-run default, fail-closed live consent, an
always-on execution-time validator with a non-waivable P0 provider-readiness gate, cost cap +
append-only ledger) is **genuinely built and verified**. The residual go-live risk is not
"will it bankrupt me" — it's **"the SP-registry lane can pay for contract-unenforced output"**
and **operational config** (default route model 404s). Do not authorize unattended/full-repo
spend yet. A bounded default-lane run, after fixing routing, is defensible.

---

## Validation Performed (PASS / FAIL / NOT_RUN)

**PASS**
- Full RTE suite ran on main in the worktree — **~1158 tests, green in CI's reference env**
  (4 "failures" on my env are strict-xfail XPASS, see Lane 4).
- **202 targeted spend/gate/structured-output tests pass on my env** (`test_spend_ledger*`,
  `test_cost_profiles`, `test_run_extraction_v5_cost_cap`, `test_pre_live_gate_v25`,
  validator/provenance, structured-output strictness, batch clients).
- **Live-consent guard fail-closed**: `--execute` without `DPMX_LIVE_OK=1` is *refused before
  provider/network dispatch* (reproduced).
- **Source-truth not poisoned**: a completing dry-run with `--output-root /tmp/...` left the
  repo git tree clean (0 dirty before/after); all 188 artifacts isolated under the sandbox.
- **SP-contract probe**: built the live phase-contract map → 112 step keys, **0 `SP:` entries**
  (and only 1 `S:` entry) — confirms `step_contract_for("SP", …)` returns `None`.
- **Live canary**: real call attempted with keys; gate **blocked NO_GO** (P0
  `ONLINE_PREFLIGHT_FAILURE` + P1 `TRUTH_SPLIT_NOT_IMPLEMENTED`) — end-to-end gate proven.

**FAIL (findings, not test infra failures)**
- S4 SP-registry paradox persists (contract-unenforced SP lane).
- Default phase-A route `openai/gpt-5.3-codex` returns **404** on the available key.

**NOT_RUN**
- A *completing* live extraction (canary blocked at preflight by design — never reached phase
  execution, so no `SPEND_LEDGER.json` from a real phase). Residual: the ledger's
  accumulate/cap path is covered by unit tests but not exercised end-to-end with a completing
  paid run, because routing 404s first.
- MCP2-04 (probable secrets-in-git-history) — not re-investigated this pass.

---

## Lane 1 — Spend-safety path (the money question): SOLID

Execution path `run_extraction_v5.py` → `llm_runtime.call_llm` → provider. Gates, all verified:

1. **Default dry-run.** A bare invocation estimates cost, makes no calls.
2. **Live consent, fail-closed.** Live needs `--execute` **and** `DPMX_LIVE_OK=1`. Missing
   consent → `parser.error("Live-capable operation refused before provider/network dispatch")`.
   *Reproduced.*
3. **Always-on execution-time validator** — `enforce_pre_live_validator_for_execution`
   (`run_extraction_v5.py:3457`). Runs whenever `DPMX_LIVE_OK=1`, **independent of `--preset`
   and NOT skippable by `--skip-pre-live-validator`** (that flag only skips the *preset-flow*
   validator at line 22923). This is a stronger posture than prior audits assumed. It includes
   a **P0, non-waivable** online provider-readiness preflight.
4. **Cost cap.** Pre-call `_check_projected_cost_limit` + post-call `_accumulate_runtime_spend`
   re-check against an **append-only** `SpendLedger` (`lib/spend_ledger.py`); breach → hard
   abort. Profile defaults apply a cap even if `--max-cost-usd` omitted; with a cap set,
   partition workers are forced to 1. 202 tests cover this.
5. **Output safety.** `output_safety.py` redacts secrets in provider payloads and outputs
   unconditionally.

**LOW finding (L1):** the **online preflight makes real provider probe calls that are NOT
counted against `--max-cost-usd` and NOT recorded in the spend ledger** — unmetered (tiny)
spend occurs before the cost gate. Observed in the canary (a 404 then a 200 OK probe).

---

## Lane 2 — Prior-CRIT reconciliation (verified against main)

| Finding | Prior | **This audit** | Evidence |
|---|---|---|---|
| F2-CRIT-1 batch dead code | open | **RESOLVED** | batch path live in `lib/batch_clients.py` + v5 batch branch |
| F2-CRIT-2 source-truth poisoning | UNKNOWN | **SAFE (dry-run)** | dry-run sandboxed, git tree untouched; *caveat C2 below* |
| F2-CRIT-3 `--strict` no-op | open | **N/A** | v5 removed the flag |
| **S4 SP-registry paradox** | open | **PARTIAL — still exploitable** | warning added + lookup wired, but **0 SP contract entries** (probed) |
| **S7 truth-split gate** | open | **PARTIAL — fail-closed but dead+waivable** | `collect_truth_split` (v25:477) emits P1-waivable blocker; `classify_truth_split_row` defined (v25:172) but **never called** |
| F4-CRIT-2 doc/CLI naming inversion | open | **likely STILL-OPEN** | not deeply re-verified; low priority |

**S4 detail (the load-bearing item).** In `rte_promptset.py:305-362`, non-legacy
`DOPEMUX_S_PROMPTS` / `--s-prompts registry` swaps phase-S steps from S0–S12 to the SP0–SP12
registry, written under `S_synthesis/`. Mitigations on main: a **loud warning** (can't activate
silently) and a wired `step_contract_for("SP", step_id)` lookup. **But** the contract map has
**0 SP entries** (runtime probe: 112 keys, 0 `SP:`), so every SP step runs with `contract=None`
→ no schema/strictness/canonical-writer enforcement. The gate that would catch this
(truth-split) is dead code and **P1-waivable**. Net: a live SP-registry run can spend real
money producing **contract-unenforced output that validates clean**. The default legacy lane is
unaffected.

**S7 detail.** Improvement over the prior fake-PASS: `collect_truth_split` now **fails closed**,
emitting a waivable `TRUTH_SPLIT_NOT_IMPLEMENTED` P1 blocker. The real classifier exists but is
never invoked. Waivers are logged (Lane 3), so a bypass is auditable — but it *is* a bypass.

**Caveat C2 (new, LOW):** the pre-live validator writes its report tree to
`reports/repo-truth-extractor/pre_live_gate_v25/<ts>/` **in the repo working tree, ignoring
`--output-root`** (untracked files; observed dirtying the worktree). Hygiene/containment issue,
not source corruption.

---

## Lane 3 — Bypass / waiver audit trail: GOOD

- `--waiver-code` waivers → persisted in `VALIDATION_VERDICT.json` (`"waivers": …`).
- `--skip-pre-live-validator` → recorded in the run config snapshot (v5:19270).
- `DPMX_LIVE_OK` presence → recorded in `BREAKER_STATE.json` (`live_ok_present`, v5:21518).
- **Severity gating works:** only **P1** blockers are waivable (`split_findings_by_waiver`,
  v25:1058). **P0** (e.g. `ONLINE_PREFLIGHT_FAILURE`) **cannot be waived** — confirmed in the
  canary verdict. So provider-readiness is a hard gate; truth-split is a soft (logged) one.

---

## Lane 4 — Tests / CI / structured outputs / proof: GOOD, with a masked-prescan caveat

- **CI really gates the RTE suite.** `.github/workflows/ci-complete.yml` runs `extractor-smoke`,
  `extractor-full` (whole `tests/` dir), and `audit-validator` as **required** PR checks;
  verified the `Extractor Full` job actually ran 6m19s and passed on the last main push.
- **Env-dependent quarantine (caveat L4).** Locally the suite shows 4 "failures" — they are
  **strict-xfail XPASS**: prescan code-intelligence tests (`test_code_prescan_truthfulness.py`,
  `test_prescan_e2e_smoke.py`) whose bodies *pass* on my 3.12/macOS but *fail* on CI's
  3.11/Linux, so the markers are calibrated to CI. The underlying prescan defect is **deferred
  to TP-RTE-WALKER-006**, not fixed. **Prescan feeds the cost estimate**, so this is a
  masked-correctness risk, not cosmetic. 4 strict-xfail invariants + the prescan markers should
  be treated as known-open.
- **Structured outputs** enforce strict closed schemas (`additionalProperties:false`) and
  validator/repair/provenance behavior is asserted — green on my env.
- **Proof bundles** mix structured (`RTE_PRESCAN_FIRST_LIVE_HARDENING.proof.json`,
  cost-profile SHA256SUMS with `pytest_full_run.txt`) and narrative; the structured ones carry
  real outputs.

---

## Lane 5 — Networked-MCP surface

- **MCP2-06 REMEDIATED.** `services/mcp-integration-bridge/main.py:1702` debug endpoint now
  returns only `database_configured`/`redis_configured` booleans (no connection strings), and
  the app binds `127.0.0.1` by default (`:1725`), off-host requires explicit
  `MCP_INTEGRATION_HOST`.
- **Residual (networked only):** ~15 other platform services still default to `host=0.0.0.0`
  (webhook_receiver, gpt-researcher ×4, task-router, adhd-dashboard, monitoring-dashboard,
  activity-capture, adhd_engine ×5); and `main.py:64` hardcodes a default DB password
  `dopemux_password`. None gate RTE spend, but they make an exposed networked deploy unsafe
  until bound to localhost / secrets rotated.

---

## Ranked blockers (for go-live before live spend)

1. **[HIGH] Fix default routing** — phase-A default `openai/gpt-5.3-codex` 404s on the live
   key. The gate blocks all live runs until routing resolves to a reachable model. (Operational;
   the gate is *working*.)
2. **[HIGH] S4 SP-registry lane** — either populate SP contract entries or hard-block
   `--s-prompts registry`/SP execution (don't rely on a P1-waivable gate). Until then, **do not
   run the SP lane live**, and **never waive `TRUTH_SPLIT_NOT_IMPLEMENTED`**.
3. **[MED] Wire `classify_truth_split_row`** into `collect_truth_split` so the drift gate is
   real (S7), and consider making it non-waivable for SP-mode runs.
4. **[MED] Networked hardening** — bind all services localhost by default; rotate the default
   `dopemux_password`. Only blocks the *networked* verdict.
5. **[LOW] Meter preflight probe spend** (L1) and **contain validator report writes** to
   `--output-root` (C2).
6. **[LOW] Resolve the deferred prescan-correctness defect** (TP-RTE-WALKER-006); the cost
   estimate depends on prescan output.

---

## Lane 6 — Cost profiles & spend estimate (added pass)

### Profiles (`COST_PROFILES`, `run_extraction_v5.py:624`)

| Profile | routing_policy | tier | batch | escalation | **default cap** | key models |
|---|---|---|---|---|---|---|
| economy | cost | flex | yes | 1 | **$5.00** | gpt-5.1-codex-mini, haiku-4.5, sonnet-4.5, gpt-5.4-mini |
| **value-default** (DEFAULT) | balanced_openrouter | default | yes | 2 | **None (UNCAPPED)** | gpt-5.3-codex, gpt-5.4, sonnet-4.6, opus-4.6, gpt-5.4-mini |
| quality | quality | priority | no | 3 | **None (UNCAPPED)** | gpt-5.5, opus-4.6, gpt-5.5-pro |
| experimental | optimal | default | no | 2 | **$25.00** | gpt-5.5, opus-4.7 |

### Real full-repo spend estimate (`--print-cost-preview --phase ALL`, main, this repo)

| Profile | **Estimated total** | Top phases |
|---|---|---|
| value-default (default) | **~$63.39** | (all 15 phases flagged low-confidence) |
| economy | **~$47.19** | Q $17.84, C $14.67, H $11.30 |
| quality | **~$47.19** | Q $17.64, C $14.67, H $11.30 |

So a single full-repo extraction on the **default** profile lands around **$63**, and — because
value-default is **uncapped** — a real run proceeds toward that (or higher) with **no ceiling**
unless the operator sets `--max-cost-usd` or uses a preset.

### Cost findings (rank-ordered)

1. **[HIGH] Default & quality profiles are UNCAPPED.** `value-default` (the default) and `quality`
   carry `max_cost_usd_default: None`. When no `--max-cost-usd` is set, `run_extraction_v5.py:3945`
   **returns early and disables the cost-cap preflight entirely** — no ceiling, no warning. Only
   economy ($5), experimental ($25), and presets first-live ($5) / staged-safe ($25) cap spend.
   *Before live spend: always pass `--max-cost-usd` or use a preset; do not rely on profile defaults.*
2. **[HIGH/MED] The preview does not faithfully price profile model selection.** quality (~$47)
   came out **cheaper than value-default (~$63)** and essentially equal to economy (~$47),
   directly contradicting the quality profile's own note ("3-5x cost of value-default"). The
   estimate is dominated by routing-policy phase-default routes + a bulk heuristic, not the
   premium cell-alias models — so it **cannot be trusted to compare profiles and likely
   under-estimates quality/experimental**.
3. **[MED] Every phase is `low_confidence`** in the preview, and the preview self-labels as
   "planning guidance, not ledger authority." Treat ~$63 as an order-of-magnitude floor.
4. **[MED] Output-token heuristic under-counts reasoning models.** `cost_estimator.py:49` assumes
   output = **15% of input**. gpt-5.x / opus reasoning models emit far more (reasoning + answer)
   tokens, so real output cost — and the total — is likely **higher** than estimated.
5. **[MED] Two conflicting fallback rates.** The prescan estimator falls back to **$0.15/$0.60**
   per 1M (`cost_estimator.py:19`); the ledger falls back to **$30/$180** (`spend_ledger.py`) — a
   ~200x gap. An unpriced model previews cheap but bills expensive. Profile models are mostly
   priced (59 entries), but `value-default`'s bare `anthropic/claude-sonnet-4.6` / `-opus-4.6`
   aliases are **only** priced under an `openrouter/` prefix — anthropic-direct routes may hit the
   $30/$180 fallback.
6. **[LOW] Cost-profile tests validate plumbing, not money.** The 19 `test_cost_profiles.py` tests
   assert profile structure, alias resolution, tier/model selection, CLI flags — **none** assert
   dollar accuracy or that rates match real provider prices.

**Cost verdict:** profiles are structurally sound and the cap machinery works *when a cap is set*,
but (a) the recommended default is uncapped, and (b) the preview is a rough, likely-low planning
number that doesn't differentiate profiles reliably. **Budget ~$60–$150 for a full-repo default
run, set an explicit `--max-cost-usd`, and reconcile against `SPEND_LEDGER.json` after a first
small completing run before trusting any estimate.**

## Adversarial review (PAL challenge) — refinements to confidence

Stress-testing the CONDITIONAL-GO for the default lane surfaced three honest qualifications:

- **"Always-on validator" is scoped, not universal.** Enforcement is gated by
  `should_enforce_pre_live_validator` (v5:3124, called at 22193). It correctly skips read-only
  introspection modes, **and also `--finalize`, `--batch-retrieve`, `--batch-watch`** (v5:3160-3165).
  Those are post-submit batch-lifecycle steps where **no new spend originates** (batch spend
  commits at *submit*, which IS validated), so the skip is defensible — but the gate protects
  the *initial dispatch / batch submit*, not "every live operation." It remains **not** skippable
  by `--skip-pre-live-validator` (verified empirically in the canary).
- **[NOT_RUN → precondition] The cost-cap abort is unit-tested only.** The canary blocked at
  preflight, so the ledger accumulate + hard-abort path was never exercised by a *completing*
  paid run. "202 tests pass" proves the ledger logic with synthetic usage; it does **not** prove
  real provider token-usage fields parse into the ledger or that an abort halts an in-flight
  multi-step run. **Treat "exercise the cap with one small completing paid run" as a hard
  precondition before any unattended/larger spend.**
- **[LOW] Theoretical validator fail-open.** `enforce_pre_live_validator_for_execution` (v5:3494)
  treats `returncode==0 + empty stdout` as `GO`. The validator's own `main` always prints its
  verdict before returning 0, so this is not practically reachable — but the enforcement trusts
  the subprocess return code; harden by requiring a parsed GO verdict, not bare exit 0.
- **[LOW-MED] Preflight probe spend scales.** Preflight retries up to 4× per probe and probes
  each targeted phase route; with `--phase ALL` this is many small **unmetered** real calls
  (not counted against `--max-cost-usd`, not ledgered). Bounded but uncapped.

These tighten — they do not flip — the verdict.

## What is safe to do now

A **local-CLI, default-lane, bounded** run is defensible **after fixing routing (#1)**: keep the
cost cap small (`--max-cost-usd`), do not use `--s-prompts registry`, do not pass any
`--waiver-code`, and review `VALIDATION_VERDICT.json` before each run. The engine's own gates
enforce most of this. Unattended or full-repo spend, or the SP lane, is **not** cleared.
