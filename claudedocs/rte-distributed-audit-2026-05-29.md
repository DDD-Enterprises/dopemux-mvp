# RTE & Associated Systems — Distributed Audit (Final Synthesis)

**Audit ID:** `rte-distributed-audit-v2-2026-05-29`
**HEAD:** `755bf3846` (branch `main`) · **Date:** 2026-05-29 · **Auditor:** Claude (distributed workflow + scoped agents)
**Scope:** Repo Truth Extractor (`services/repo-truth-extractor/`), the dopemux CLI, install/bootstrap, documented usage, and the MCP layer.
**Posture:** **READ-ONLY.** No files modified, no `run_extraction_v*`/prescan/probe executed, no live LLM/network calls, no install scripts run. All execution-only checks are recorded as **NOT_RUN** with human-verify commands.

---

## 1. Executive Summary

The RTE is an architecturally mature, largely fail-closed pipeline whose **runtime engine (`run_extraction_v5.py`) and operator CLI are sound**, but whose **go-live readiness is bounded by the synthesis phase (S/SP), the prescan intelligence layer, and the operational substrate (install + MCP)**.

The single most important finding cluster is the **Phase S/SP "registry paradox" (S4-CRIT-1, S4-CRIT-2)**: the `--phase S` invocation silently resolves a *different step set* (S0–S12 vs SP0–SP12) depending on an environment variable, and the registry (SP) pipeline runs with **zero phase-contract enforcement** because `repo_truth_map.json`/`promptset.yaml` define phase `S` but never `SP`. Compounding this, **the pre-live gate's drift detector is a dead stub (S7)** — `collect_truth_split` always returns PASS, so the gate cannot detect the very runner/promptset/model-map drift it claims to guard.

Separately, the **MCP layer** (an "associated system") carries the audit's most concrete security exposures: an **unauthenticated debug endpoint that returns the Postgres password (MCP2-06)**, **provider keys likely left in git history (MCP2-04)**, and **every child MCP process inheriting the full host environment incl. all API keys (MCP1-04)**. The MCP authority/RBAC model could not be fully verified because the enforcement point (`broker.py`) fell outside the scoped pass (MCP1-01).

Good news worth recording: the **`rte list` prescan regression is fixed** (introspection commands short-circuit before prescan — CLI lane), the **dry-run/execute split is correct** (live spend requires explicit `--allow-online-llm`), `output_safety.py` redaction is thorough, and `phases.py`/`rte_phase_wrappers.py` are clean and deterministic for what they encode.

---

## 2. Readiness Verdicts (mode-split)

Gated only on findings that survived adversarial review (CONFIRMED), with RECALIBRATE severities applied and REFUTED dropped.

| Execution Mode | Verdict | Gating rationale |
|:---|:---|:---|
| **Prescan-Only** | **GO (with caveats)** | Prescan is non-destructive (no truth mutation, no live LLM in dry-run). Safe to run. BUT its cost/savings numbers are unreliable (S3-02 heuristic-only; S3-06 always reports 0% reduction) and its ordering/tiering is non-reproducible across environments (S3-05). Treat prescan output as advisory, not measured. |
| **Bounded Live (Ph A–C)** | **CONDITIONAL GO** | Early extraction phases avoid the Phase-S/SP CRITs. Conditional on: (a) pass `--allow-online-preflight` so the gate actually verifies provider reachability (S5 — otherwise it returns GO without checking); (b) accept or pin prescan reorder non-determinism (S3-01/05); (c) the MCP layer not networked, or MCP2-06/04 remediated first. |
| **Full Live (Ph A–Z)** | **NO-GO** | Blocked by **S4-CRIT-1** (env-dependent S/SP step-set swap writing both to `S_synthesis/`) and **S4-CRIT-2** (SP synthesis runs with no contract enforcement — 9 JSON-emitting steps get `contract=None`). The gate cannot catch this because **S7** (`collect_truth_split` stub) disables all STALE_* drift detection. Unblock by adding phase `SP` to the contract sources OR fencing off SP dispatch and pinning `DOPEMUX_S_PROMPTS=legacy`. |
| **MCP layer (networked deploy)** | **NO-GO** | **MCP2-06** (unauth `/api/debug/instance-info` returns DB password, binds `0.0.0.0`), **MCP2-04** (probable provider keys in git history), **MCP1-04** (full-env leak to children). RBAC enforcement **UNVERIFIED** (MCP1-01, broker.py out of scope). Localhost-only, single-tenant use is CONDITIONAL. |

This sharpens — and is consistent with — the prior `DMX-RTE-DEEP-AUDIT-GEMINI-007` (2026-04-23) verdicts (Prescan GO / Bounded CONDITIONAL / Full NO-GO), adding specific, file:line-anchored blockers.

---

## 3. Confirmed Findings by Surface

### 3.1 RTE Core — Integration / Phase S-SP (S4) — **the central blocker**

- **[S4-CRIT-1] CRIT** — `--phase S` in `registry`/`auto` mode silently swaps the step set S0–S12 → SP0–SP12 while still writing under the `S` phase id and `S_synthesis/` dir. Driven solely by `DOPEMUX_S_PROMPTS` env. Coverage/proof tooling enumerates `REQUIRED_PROMPT_STEP_IDS["S"]`=S0–S12 → step-id mismatch against the SP* artifacts actually produced. `run_extraction_v5.py:6612-6618`, `rte_promptset.py:311-352`, `phases.py:152-158`.
- **[S4-CRIT-2] CRIT** — SP pipeline runs with **zero phase-contract enforcement**: `step_contract_for("SP", …)` always returns `None` because `repo_truth_map.json` (S=13, SP=0) and `promptset.yaml` (S, no SP) never define phase SP. 9 SP steps (SP4/5/7–12) emit JSON with `schema_path` set but get no `required_fields`/schema gate. The "modern" registry path is *less* governed than the legacy path it supersedes. `rte_promptset.py:346-349,380`, `lib/phase_contract_map.py:376,392-399`.
- **[S4-HIGH-1] HIGH** — `--s-steps S4` validates against S0–S12 but, in registry/auto mode, the prompt map only has SP0–SP12 → hard `RuntimeError` ("Selected steps are not resolvable for phase S"). Documented selective-rerun is mode-dependent. `rte_promptset.py:121-143`, `run_extraction_v5.py:17572-17577`.
- **[S4-HIGH-2] HIGH** — Naming inversion: dir `prompts/phase_s/` + functions `*_phase_s_registry` all say "S", but the payload and every error message assert `phase=="SP"`; the co-located `PHASE_S_SYSTEM_TRUTHS_GPT52.md` documents Phase S. The `promptset_sha256` fingerprint pins an SP payload retrieved from an S-named path. `rte_promptset.py:65-89,212-226`.
- **[S4-HIGH-3] HIGH** — Dependency DAG is triple-encoded (`phases.py` phase-level, wrapper globbing, `registry.json` per-step `input_phase_ids`) and the three disagree; `MANUAL` is a `phases.py` "dep" that is a run-root sidecar, not a phase. `phases.py` cannot be trusted as the sole DAG authority for synthesis. `phases.py:152-166`, `rte_phase_wrappers.py:296-346`.
- **[S4-MED-1] MED** — Orphan phase id `"M"` in `REQUIRED_PROMPT_STEP_IDS` + routing sets but absent from `PhaseId`/definitions/dir-map/verify-choices → biases completeness math for a phase that can never run. `phases.py:199`, `run_extraction_v5.py:1151,1222`.
- **[S4-MED-2] MED** — `validate_phase_s_registry` pins SP *step identity* to `phases.py` (fail-closed) but never validates `input_phase_ids`/`prior_step_ids`/`schema_path` → a cyclic or dangling SP dependency graph passes validation. `rte_promptset.py:212-272`.
- **[S4-OBS-1/2] OBS** — `plan_s_phase` optionally ingests Z norms (order-sensitive S manifest, fail-open); only one `LEGACY_PHASE_DIR_ALIASES` entry exists (no S/SP alias). 

### 3.2 RTE Core — Prescan Intelligence (S3)

- **[S3-01] HIGH** — Prescan reordering is **default-on** (not gated by the scope-reduction flag), uses **two uncoordinated priority functions** (inventory vs partition), and silently mutates which files share an LLM context → extraction output differs run-to-run when a prescan artifact is present. `run_extraction_v5.py:8528-8538,8662`, `lib/intelligence_router.py:719-730,828-834`.
- **[S3-02] HIGH** — Net token/cost "savings" are hardcoded heuristics (80% version-chain, 0.15 output ratio) **never reconciled against actuals** — repo-wide search for any predicted-vs-realized check returned nothing. `lib/prescan/cost_estimator.py:41-49`, `run_extraction_v5.py:7798-7802`.
- **[S3-03] HIGH** — Model-tier routing returns the **raw LLM free-text** `recommended_model`; if the LLM emits an actual model name (which the prompt invites) instead of `premium/standard/economy`, the tier override is silently dropped **while still labeled `applied=True`** — a proof-truthfulness violation. `lib/intelligence_router.py:740-771`, `run_extraction_v5.py:8700-8725`.
- **[S3-04] MED** — LLM `optimize.skip_list` merged into the live skip set with only list-ness validation (no path-exists/duplicate-evidence check). Mitigated by default-OFF scope reduction. `lib/intelligence_router.py:283-293`, `run_extraction_v5.py:1746`.
- **[S3-05] MED** — Hotspot/priority scores are corpus-relative + git-depth-dependent (`use_churn = git_depth=="full"`) → same file is "premium" in a full clone, "standard" in CI/shallow → non-reproducible cost/ordering. `lib/prescan/code_intelligence_report.py:83,173-196,267-294`.
- **[S3-06] MED** — `estimate_token_savings` reads `corpus_summary.total_included_size_bytes` but the engine writes `total_size_bytes` → always reports 0% reduction (dead self-report; schema/runtime drift). `lib/intelligence_router.py:810-819`, `lib/prescan/engine.py:719-727`.
- **[S3-07] MED** — Schema permits bare-string `compress_candidates`, but `IntelligenceRouter.__init__` indexes them as objects → **`TypeError` crashes router construction** on a schema-valid *imported* prescan. `lib/intelligence_router.py:261`, `lib/prescan/schemas.py`.
- **[S3-08] LOW / S3-09 OBS** — dead `--no-*` positive flags (negative flags work); influence-labeling framework is otherwise honest (`does_not_claim_executed_route`, import freshness gating) — positive control, except the S3-03 mislabel.

### 3.3 RTE Core — Tests / Gate (S7) — **gate blindness**

- **[S7-STUB] HIGH** (embedded, not in a numbered block — agent hit turn limit) — `collect_truth_split` (`validate_pre_live_gate_v25.py:476-478`) is a **hardcoded stub returning PASS / 0 mismatches**; `classify_truth_split_row` is defined + tested but **never called by the live gate path**. All STALE_* drift detection (runner/promptset/model-map drift) is **non-functional**, and the test monkeypatches the same PASS stub so it never exercises real drift.
- **[S7-COVERAGE] MED** (embedded) — Gate runs **5 critical tests as blocking out of 178**; strong truth-quality tests (`test_truth_label_preservation.py`, source-truth poisoning) are **not** in the blocking set. The 3 golden smoke tests run dry-run on hand-built fixtures → validate *plumbing*, not LLM truth quality. `test_code_prescan_truthfulness.py` carries 3 `xfail(strict=True)` known-broken prescan-truthfulness bugs (deferred to TP-RTE-WALKER-006).

### 3.4 RTE Core — Authority / Prompts / Routing (S1, S2, S5 — embedded findings)

- **[S1-V3REACH] HIGH** (embedded) — v3 (the consent-gated legacy engine) is **operator-reachable**, not just helper-imported: `src/dopemux/commands/extractor_commands.py:474` resolves to `run_extraction_v3.py`, `scripts/reprocess_failed_partitions.py:17` hardcodes it, and a hidden `--engine-version` flag (`cli.py:4910`, default None) overrides the v5 default → `--engine-version v3` reaches live v3. `cli.py:5522` hardcodes v4 for one command. v4's `PHASE_DIR_NAMES` diverges from `phases.py` (v4:59 `S_synthesis_trace` vs phases.py:153 `S_synthesis`).
- **[S2-PROMPTS] MED** (embedded) — "Legacy Context" is referenced in v4 S-prompts as a guardrail but **never injected by any runtime code** (dead/misleading prompt text). `required_prompt_sections` (9 declared in `promptset.yaml`) is **not enforced by the v5 terminal engine** (v5 loads `PROMPTSET_RULES.md`, not `promptset.yaml`).
- **[S5-GATE] MED** (embedded) — The pre-live gate **does not verify live provider reachability** unless `--allow-online-preflight` is passed: the online preflight is downgraded to a Condition (WARN), and `derive_operator_verdict` returns `GO_NOW` whenever blockers are empty (Conditions never block). The provider-fallback "route guard" keys on `api_key_env` equality, not provider equality (`llm_runtime.py:1185-1194`). Fail-closed parts hold: online-preflight blockers are P0 (genuinely unwaivable; waivers only apply to P1).

### 3.5 RTE Core — Operator Surfaces (S6) & Boundaries (S8)

- **[S6-MED-1] MED** — **Five disjoint terminal-status vocabularies** across operator artifacts (`OK/BLOCKED/COST_ABORTED`, `VERIFIED/BLOCKED/UNKNOWN`, `PASS/FAIL`, `CLEAR/BLOCKED`, `ready/blocked`, `pass/fail`, `PASS/FAIL/SKIPPED`), and the same `RUN_MANIFEST.run_status` field written by two writers with two vocabularies. Every path is internally fail-closed (no machine fail-open) — this **bounds** unattended operation by raising operator-misread risk, does not block. S6-OBS-1..4 are latent/decorative (verified no live mis-normalization). `reporting.py:167-173,439-445,587,824,830,978`, `run_extraction_v5.py:3606-3643`.
- **[S8-001] HIGH** — `extraction_hygiene._REPO_ROOT_DEFAULT` resolves to `services/`, not repo root (off-by-one in `parents[]`).
- **[S8-002] MED** — Hardcoded exclude/authority policy diverges from the canonical YAML it claims to mirror; `_POLICY_PATH`/`_TIERS_PATH` are dead constants.
- **[S8-003] MED** — `--apply-cleanup` quarantine does real `shutil.move()` across the whole repo tree, scoped only by hardcoded prefixes + a backstop allowlist.
- **[S8-004 LOW / S8-005 OBS / S8-006 OBS]** — `.DS_Store` sweep wider than sibling sweeps; `output_safety.py` is a pure in-memory sanitizer (no out-of-scope writes, but load-bearing for proof integrity); `archive/` (40 files) is unreferenced dead pollution, not reachable legacy scripts.

### 3.6 CLI

- **[CLI-FIXED] POSITIVE** — The **`rte list` prescan regression is fixed**: `--print-config` exits at `run_extraction_v5.py:22645`, `--preflight-providers` at 22673, `--status` at 22526, `--doctor` at 22687 — **all before** `run_integrated_prescan_stage` (22701). Read-sounding verbs are now read-only.
- **[CLI-EXECSPLIT] POSITIVE** — `rte run` dry-run/execute split is correct: `--dry-run/--execute` defaults to dry-run=True (`cli.py:5072`); live LLM spend requires explicit `--allow-online-llm` forwarded to v5 (`cli.py:5126,5252`).
- **[CLI-V3] HIGH** (overlaps S1-V3REACH) — the multi-version dispatcher exposes live v3 via `--engine-version`/`--pipeline-version v3`.

### 3.7 Usage / Docs

- **[USAGE-INV] HIGH** — **Canonical-naming inversion**: `README:37` documents `dopemux extractor validate --output-dir …` as a current command, but `cli.py:3170-3184` registers `dopemux extractor` as a `LegacyReplacementCommand` that **disables all subcommands** → the documented command hits a refusal. The real command object exists; the canonical path is `dopemux rte promptset validate`. The user-guide simultaneously calls `dopemux extractor` a "legacy/refusal surface" — a direct internal doc contradiction. (Matches prior `F4-CRIT-2`.)

### 3.8 MCP Layer (orchestration lib + standalone servers)

Full detail in [`rte-audit-MCP-findings-2026-05-29.md`](rte-audit-MCP-findings-2026-05-29.md). Headlines:

- **[MCP2-06] MED→HIGH** — `GET /api/debug/instance-info` returns `POSTGRES_URL` (with embedded password) + Redis URL, **no auth, no plane check, `host=0.0.0.0`, CORS `*`**. If reachable off-host → CRIT. `services/mcp-integration-bridge/main.py:1680-1695,1701`.
- **[MCP2-04] HIGH** — Provider keys as `os.getenv()` fallbacks (redacted in tree now → **probable git-history leak**). `services/mcp-client/main.py:278-279`. Verify (don't echo values): `git log -p -- services/mcp-client/main.py | grep -iE 'AIza|xai-|sk-[A-Za-z0-9]'`; if found, rotate + scrub.
- **[MCP1-04] HIGH** — Every child MCP process spawned with `os.environ.copy()` → inherits all host secrets (ANTHROPIC/OPENAI/VOYAGE/GROQ keys, DB creds). `src/dopemux/mcp/server_manager.py:446-461`.
- **[MCP2-01/02] HIGH** — KG authority middleware **fails open** for unlisted `/kg/*` paths; PM-plane "authority" is a **self-asserted unauthenticated `X-Source-Plane` header**. `kg_authority.py:40-93`, `kg_endpoints.py`.
- **[MCP2-03] HIGH** — `capture/emit` forwards an **unvalidated event envelope** into Chronicle ingestion (declared schema not enforced; `lane` self-assignable). `services/mcp-capture/server.py:99-114`.
- **[MCP1-02] HIGH** — Discovery gate **fails open** for env-var/global-fallback servers; any `DOPMUX_*_URL` env var registers an endpoint the Phase-0 gate never blocks. `src/dopemux/mcp/gate.py:48,73-83`.
- **[MCP1-01] HIGH (UNVERIFIED authority)** — The audited library defines roles as *data* but the enforcement point is `broker.py` (out of scope). **RBAC fail-open-vs-closed is unverified** — must inspect `broker.py` before trusting least-privilege claims.
- Plus MED/LOW/OBS: `/tmp` session path + traversal (MCP1-05), instance port collisions (MCP1-06), advisory budget (MCP1-07), provisioner dir clobber (MCP1-08), error-string leakage (MCP2-05), wide CORS (MCP2-07), stdio framing (MCP2-08), SA-2.x bare-SQL breakage (MCP2-09), `gate.py` conport no-op (MCP1-10).

### 3.9 Install / Bootstrap (both adversarial reviews completed)

- **[INST-01] HIGH (CONFIRMED)** — `install.sh` (documented installer) never creates `dopemux-network`; every stack's compose-up precondition is unmet.
- **[INST-02] HIGH (CONFIRMED)** — Installer tests run only in `INSTALLER_TEST_MODE=1`, which dead-codes every Docker/network/compose step (8 skip-guards) → green tests, broken real install.
- **[INST-03] ~~HIGH~~ → MED (RECALIBRATED by review)** — `scripts/install.py` does `pip install -e scripts/` with no build metadata → structurally broken, but low blast radius (legacy path).
- **[INST-04] HIGH (CONFIRMED)** — `scripts/setup.sh` has `set -e` but no `pipefail`; `docker compose … | tail -5` makes the `exit 1` branch dead code → prints success on compose failure. Also creates wrong network name `dopemux-unified-network`.
- **[INST-05] HIGH (CONFIRMED, one sub-claim recalibrated)** — `install-docker-mcp-servers.sh`: unpinned `git clone` at HEAD, `.env` secrets written world-readable (no `chmod 600`), then auto-built and run → supply-chain + secret-exposure path.
- **[INST-06..11] MED/LOW/OBS (CONFIRMED)** — no preflight for Docker-VM-disk blocker; floated `>=` deps (`fastmcp`/`rank_bm25` unbounded); `dope-context` healthcheck `|| exit 0` can never be unhealthy; `Dockerfile.frontend` private-registry dep (orphaned); stale `mcp-proxy-setup.sh`; `install.sh` is otherwise well-engineered (uninstall `down -v` data-loss nit).

---

## 4. Refuted / Downgraded (adversarial review honesty)

So nothing looks silently dropped:

- **INST-03** HIGH → **MED** (security-review: correctly broken but blast radius too low for HIGH).
- **INST-05** one sub-claim (clone SHA/date staleness) **recalibrated**; security core confirmed.
- **S3-08** self-downgraded LOW (the `--no-*` negative flags *do* work via the `and not` guard; only the positive flags are inert).
- **S6** — auditor explicitly **resisted manufacturing a CRIT**: all status paths are fail-closed; the vocabulary fragmentation bounds (not blocks) go-live. S6-OBS-1..4 verified **latent** (no live mis-normalization at this HEAD).
- **S4-OBS-1** — the S-reads-Z ordering coupling **fails open by design** (`.exists()`-guarded), so it is OBS, not a crash.
- **MCP2-09** — the bare-SQL pattern looks like injection but is **NOT** (values are bound `?` params); flagged as a correctness/fail-shut issue instead.

---

## 5. Prioritized Remediation Matrix

| Priority | Surface | Action |
|:--|:--|:--|
| **P0** | RTE S4 | Add phase `SP` to `repo_truth_map.json` + `promptset.yaml` so SP contracts resolve (closes S4-CRIT-2), OR fence off SP dispatch and pin `DOPEMUX_S_PROMPTS=legacy` (closes S4-CRIT-1). |
| **P0** | RTE S7 | Wire `classify_truth_split_row` into `collect_truth_split` (remove the PASS stub) so the gate actually detects runner/promptset/model-map drift. |
| **P0** | MCP | Remove/auth-gate `/api/debug/instance-info` (MCP2-06); verify+rotate+scrub git-history keys (MCP2-04); scope child-process env to an allow-list (MCP1-04). |
| **P1** | MCP | Audit `broker.py` to verify RBAC fails closed (MCP1-01); make KG authority middleware deny-by-default (MCP2-01); bind a real identity to plane auth (MCP2-02); validate `capture/emit` input (MCP2-03); fail-closed discovery gate for env-var servers (MCP1-02). |
| **P1** | RTE S3 | Validate LLM tier hints against the `premium/standard/economy` enum and fix the `applied=True` mislabel (S3-03); fix the `total_size_bytes` key drift (S3-06); guard `compress_candidates` string members (S3-07); gate reorder behind an explicit flag (S3-01). |
| **P1** | Install | Create `dopemux-network` in `install.sh` (INST-01); add `pipefail` + fix dead failure branch + network name in `setup.sh` (INST-04); `chmod 600` the generated `.env` + pin the clone (INST-05); make installer tests exercise real steps (INST-02). |
| **P1** | Docs/CLI | Fix README `dopemux extractor validate` → `dopemux rte promptset validate` (USAGE-INV); decide v3's status and fence `--engine-version v3` if v3 is deprecated (S1/CLI-V3). |
| **P2** | RTE | Single canonical status-enum across reporting writers (S6-MED-1); resolve orphan phase `M` (S4-MED-1); remove dead "Legacy Context" prompt text + enforce `required_prompt_sections` or delete it (S2); fix `extraction_hygiene` repo-root off-by-one (S8-001). |

---

## 6. Proof Bundle

```
audit_id:            rte-distributed-audit-v2-2026-05-29
head:                755bf38460d1f2f6bba6e072ec9a627e9e218b15 (main)
scope_flags:         read_only=true, live_run=false, files_modified=false,
                     llm_calls=false, install_run=false
authority_used:      runtime code (run_extraction_v5/v4/v3, phases.py, rte_promptset.py,
                     validate_pre_live_gate_v25.py, llm_runtime.py, intelligence_router.py,
                     lib/prescan/*, lib/phase_contract_map.py, reporting.py, rte_ops_surfaces.py,
                     extraction_hygiene.py, src/dopemux/mcp/*, services/mcp-*, cli.py,
                     src/dopemux/commands/*), registries/promptsets, scripts/install*, README/QUICK_START.
severity_counts:     CRIT=2  HIGH≈18  MED≈17  LOW≈6  OBS≈12   (+ adversarial review: 1 RECALIBRATE, several REFUTED-as-not-applicable)
adversarial_review:  COMPLETED for INSTALL (correctness + security lenses); other lanes
                     reviewed inline by the synthesis pass (review fan-out did not complete in the workflow).
```

**NOT_RUN register (each needs a human to run under a proper harness):**
- `S4-CRIT-1`: `DOPEMUX_S_PROMPTS=registry python -c "import run_extraction_v5 as r; print([s.step_id for s in r.get_phase_prompts('S')])"` → expect `SP0..SP12`.
- `S4-CRIT-2`: `python -c "from lib.phase_contract_map import get_step_contract as g; print(g('SP','SP4'), g('SP','SP7'))"` → expect `None None`.
- `S3-07`: `cd services/repo-truth-extractor && python -c "from lib.intelligence_router import IntelligenceRouter; IntelligenceRouter({'extraction_hints':{'compress_candidates':['x.md']}})"` → expect `TypeError`.
- `MCP2-06`: `curl http://<bridge-host>:3016/api/debug/instance-info` → check `database_url`.
- `MCP2-04`: `git log -p -- services/mcp-client/main.py | grep -iE 'AIza|xai-|sk-[A-Za-z0-9]'` (do not echo values).
- Full per-finding falsifying checks are in the raw lane files.

**Provenance / supporting artifacts:**
- Raw lane harvest: [`rte-audit-RAW-harvest-2026-05-28.md`](rte-audit-RAW-harvest-2026-05-28.md)
- MCP lane (scoped re-run): [`rte-audit-MCP-findings-2026-05-29.md`](rte-audit-MCP-findings-2026-05-29.md)
- Early-run salvage: [`rte-distributed-audit-SALVAGE-2026-05-28.md`](rte-distributed-audit-SALVAGE-2026-05-28.md)

---

## 7. Appendix — How this audit was run (the distributed-workflow method)

The original question was *how to use a distributed workflow* for this. What actually worked:

1. **Discover-first barrier.** One sequential agent pinned canonical authority (v5 terminal engine, v4 contract wrapper, v3 shadow, bifurcated registry truth) and that map was injected into every downstream lane. Without this, parallel lanes contradict each other on "which file is canonical." This was the highest-leverage step.
2. **One lane per surface, fan-out.** RTE-core fanned into 8 stage sub-lanes (S1 authority … S8 boundaries — the Gemini-007 methodology); CLI/install/usage/MCP each got a specialist agent type (`root-cause-analyst`, `devops-architect`, `technical-writer`, `security-engineer`).
3. **Read-only contract on every agent** (no writes, no live runs, no LLM calls; execution-only checks → NOT_RUN + human-verify command). Essential when auditing a live extraction engine in parallel.
4. **Adversarial verification** (per-lane, two lenses: correctness/repro + security/severity) — completed for INSTALL and produced real recalibrations (INST-03 HIGH→MED).

**Two failure modes hit, both instructive for next time:**
- **Schema-strictness killed run #1**: forcing agents to call a `StructuredOutput` tool failed (agents reached for a "final advisor check" and never made the terminal call). **Fix: schemaless agents that return markdown.**
- **Scope-overload hung run #2's MCP lane**: one agent reading ~22 MCP files hung and stalled the whole pipeline. **Fix: split oversized lanes into bounded sub-agents** (the MCP lane re-run as 2 scoped agents finished cleanly and produced the richest findings).

Net: a distributed audit is most reliable as **discover (1) → fan-out schemaless lanes (N, each scope-bounded) → adversarial verify (per-lane) → synthesize**. Keep individual agent scope under ~10 files; return markdown, not schema; ban `advisor()` inside workflow agents.
