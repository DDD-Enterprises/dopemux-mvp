---
id: rte-truth-a6-fresh-eyes
title: "RTE-TRUTH Audit Pass A6 — Fresh Eyes (never-audited subsystems)"
type: audit-report
owner: claude-audit
date: 2026-07-10
worktree: /Users/hue/code/dopemux-mvp/.claude/worktrees/focused-mahavira-5bd29b
head: 542c17bb4
status: COMPLETE
---

# A6 — Fresh Eyes: Never-Audited RTE Subsystems

**Program**: RTE-TRUTH · **Pass**: A6 · **Mode**: READ-ONLY survey, scope-explosion firewall
**Scope**: `services/repo-truth-extractor/{benchmarking,llm_runtime.py,reporting.py,rte_reports.py,audit_tp008.py,s_int,fl_int,sp}` + post-cost-profile-merge commit delta.

Depth is proportional to risk per the escalation rule: money (pricing/spend), security (secrets/injection), and silent data corruption get deep dives; cosmetic issues get one line.

---

## 0. Scope note — git range correction

The mission's git delta spec (`git log 8c7da98ca..HEAD -- services/repo-truth-extractor`) returns **zero commits**. Verified: `8c7da98ca` (merge "feat/rte-cost-profile-alignment") is itself the most recent commit touching this path — nothing has landed in `services/repo-truth-extractor` since 2026-06-27. All nine commits named in the mission (`685b417bb`, `1301547b8`, `3522197cf`, `d2fe66cac`, `46da5f9c9`, `ae76136a3`, `13f0db81a`, `3a095341d`, `6ef9b9db1`) are **ancestors of** `8c7da98ca`, not descendants — they're part of the 23-commit "cost-profile alignment" bundle spanning 2026-06-04 (`d2fe66cac`) through 2026-06-27 (`8c7da98ca`). Area 6 below reviews that actual bundle, not a post-merge delta (which is empty).

---

## 6. Post-cost-profile-merge commit bundle (`d2fe66cac^..8c7da98ca`, 23 commits, 2026-06-04→2026-06-27)

**Verdict: FINDINGS (informational) — no new defects; confirms prior remediation is live at HEAD.**

This bundle is the "RTE cost-profile Plan B / CostProfile E/F series" already tracked in project memory (`F-VERIFY-002 VERIFIED`) and overlaps the P4-rerun 6-CRITICAL-BLOCKING finding (`8ea182dd3`, tracked in `rte_audit_findings_p4*.md`). Reviewed the named commits' actual diffs (not just the range) to check for anything the P4 pass or the CostProfile series review wouldn't have caught:

- **`d2fe66cac` "harden go-live preflight safety"** — this is the fix that *implements* the truth-split drift audit (`collect_truth_split`) which previously returned a **hardcoded PASS with `status: NOT_IMPLEMENTED`** — i.e. the pre-live gate was silently asserting "no drift" without checking anything (this is almost certainly the S7 finding referenced in memory `reference_chronicle_mirror...`/P4 notes). At current HEAD this now does real per-step comparison against `promptset.yaml`/`model_map.yaml` declared step keys and fails closed (`status: FAIL` unless all rows `MATCH`), including a new `SP_CONTRACT_MISSING` P0 blocker when an SP-registry step lacks a phase contract. **This directly touches the `sp/` phase subsystem (area 5) via `s_prompts_mode` legacy/registry/auto** — cross-reference: confirm area-5 agent's `sp/` contract findings against this gate's `SP_CONTRACT_MISSING` check for consistency (WS3/WS5).
- **`46da5f9c9` + `ae76136a3` "contain/address pre-live validator"** — hardens `enforce_pre_live_validator_for_execution` in `run_extraction_v5.py`: (1) validator output now written to an isolated `tempfile.mkdtemp()` dir outside the repo tree (previously could pollute repo), (2) a validator that exits 0 but emits no parseable `verdict` field now explicitly fails closed to `NO_GO` (`missing_verdict` branch) instead of previously defaulting a return-code-0-with-no-verdict to `GO` — this was a real fail-open gap, now closed. Good fix, verified present at HEAD.
- **`685b417bb` "align cost profile controls and proof visibility"** — plumbs `--cost-profile`, `--model-alias`, `--disable-provider`, `--max-cost-usd` from `dopemux rte run` (`src/dopemux/cli.py`) through to `run_extraction_v5.py` and into `RUN_MANIFEST` (`reporting.py`) for audit-trail visibility. Money-adjacent (spend cap forwarding) but this commit only *records* `max_cost_usd`/`cost_profile` in the manifest — it does not itself enforce the cap. **Deferred**: whether `--max-cost-usd` is actually enforced as a hard stop at runtime (vs. advisory-only) was not verified in this pass — belongs to the benchmarking/pricing spend-path deep dive (area 1) or a dedicated runtime-behavior audit pass, not this doc-diff review.
- **`1301547b8`** — patches missing governance metadata (`workload_class`, `governance_posture`, `provider_surface`, `allowed_payload_sensitivity`) on 2 of 11 cost profiles + adds a test asserting all profiles carry these fields. Legitimate spec-gap close, test-backed.
- **`3522197cf`** — `print-config` cosmetic/compat fix: separates CLI-override `model_aliases` from profile-resolved `effective_cell_aliases` so operator-safety tests don't conflate the two. Low risk, correctly scoped (5-line diff).
- **`3a095341d` + `6ef9b9db1`** (OpenClaw benchmark result contract + secret redaction) — overlaps directly with area 1's mandate; see area 1 for the full pricing/secret deep dive. Independently verified `6ef9b9db1`'s diff: it *extends* `_SECRET_PATTERNS` in `benchmarking/openclaw_dcp_benchmark_result.py` to add `OPENAI_API_KEY`/`ANTHROPIC_API_KEY`/`GEMINI_API_KEY`/`GOOGLE_API_KEY` env-var patterns and a broader `sk-(proj-)?...` catch-all (previously only covered `sk-or-...` OpenRouter keys and Bearer tokens). **Gap observed directly**: the pattern list still has no entry for xAI/Grok keys (`xai-...`), Cohere, Mistral, Azure OpenAI keys, or a provider-agnostic fallback pattern (e.g. any `[A-Za-z0-9_-]{32,}` token following a `key`/`token`/`secret` label) — MEDIUM severity, WS-owner: benchmarking secret-redaction hardening. This same file is also the primary read target for area 1's agent; treat as one finding, not two.
- **`13f0db81a`** — adds a regression test guarding v3/v5 cell-model drift (documents that `run_extraction_v3.py` hardcodes value-default cell models and shares `model_map.yaml` directly, no cost-profile mechanism — i.e. v3 is intentionally NOT on the new cost-profile system). Test-only change, no production code touched. Note for future: v3 legacy runner is a second, unaudited model-routing path parallel to v5's cost-profile system — **deferred, not admitted to this program** (v3 is legacy/being phased toward v5 per commit message; full v3 audit is a separate scope decision).

**Findings summary for area 6:**
| Finding | Severity | WS owner |
|---|---|---|
| Mission's stated git range (`8c7da98ca..HEAD`) is empty; scope was actually the ancestor bundle | INFO (process) | n/a — corrected in this report |
| Truth-split drift gate previously fake-PASS, now real fail-closed check (`d2fe66cac`) — confirms prior P4/S7 remediation is live at HEAD | INFO (confirms fix) | WS-audit-tracking (link to P4 file) |
| `SP_CONTRACT_MISSING` gate check should be cross-verified against `sp/` subsystem's actual contract files | MEDIUM | WS3 (sp/ subsystem) / WS5 (pre-live gate) |
| `--max-cost-usd` enforcement (hard stop vs. advisory) not verified at runtime | MEDIUM (money, unverified) | WS1 (benchmarking/pricing) — needs runtime check, out of scope for this doc pass |
| Secret-redaction pattern list (`6ef9b9db1`) missing xAI/Cohere/Mistral/Azure key patterns + no generic fallback | MEDIUM (security) | WS1 (benchmarking) |
| `run_extraction_v3.py` is a second, cost-profile-unaware legacy routing path, still live and diverging from v5 by design | LOW–MEDIUM (architecture debt) | deferred — not admitted to this program |

---

## 1. benchmarking/ (~111 py files) — incl. pricing money-path deep dive + secret-redaction verify

**Verdict: FINDINGS — one HIGH money finding (in the spend_ledger consumer), one MEDIUM security gap in redaction; module itself is well-built.**

### Structure (one line per subdir)
`campaigns/` candidate selection · `cli/` 15 standalone smoke runners (`benchmark_*_smoke.py`) · `direct_model/` direct-provider benchmark runner + adapters (openrouter/xai) + spend helpers · `executors/` extraction-v5 adapter · `governance/` governance packets · `models/` entities · `orchestration/` attempt executor · `policies/` run policies · `pricing/` pricing truth catalog (deep dive below) · `registry/` model/route registry + openrouter discovery · `reporting/` report views · `rollups/` aggregation · `scenarios/` scenario defs · `scoring/` scoring · `storage/` sqlite repo/schema · `synthesis/` profile synthesis · `validators/` benchmark validators.

### Reachability: INTERNAL-ONLY (not operator-CLI)
No import of `benchmarking` anywhere in `src/dopemux/` (checked `cli.py` + `commands/*.py`); the only `pyproject.toml` "benchmark" reference is the unrelated `tools.prompt_rewrite_v4.benchmark`. The `benchmarking/cli/*_smoke.py` entry points are invoked exclusively by the RTE test suite (e.g. `tests/test_change_summaries.py:11`, `test_attempt_execution_smoke.py:13`) or run manually as scripts. Spend exposure from an operator mis-click is therefore low; live-call surfaces are `benchmark_live_route_readiness_smoke.py` and `direct_model/` (operator must invoke deliberately).

### Money-path deep dive: `benchmarking/pricing/` → `lib/spend_ledger.get_model_cost_rate`
The `pricing/` package itself (331 lines total: `catalog.py`, `normalization.py`, `coverage.py`, `spend_truth.py`) is **clean and fail-closed**: missing `config/pricing.yaml` raises (`catalog.py:40-41`), `Decimal`-based rates, enum-validated `pricing_status`/`pricing_confidence` (`normalization.py:30-36`), and priced entries missing rate values raise (`normalization.py:109-111`). Units are consistently per-1M (`*_cost_per_m` → `*_cost_per_1m_usd`), currency pinned USD.

The risk is in the **consumer seam**, `lib/spend_ledger.py`:

1. **HIGH (money — silent under-pricing on catalog failure)**: `spend_ledger.py:15-16` defines flat baselines `$0.15/$0.60 per 1M` for ~22 models (`MODEL_COST_RATES`, lines 47-69) — nano-tier rates. Real catalog rates are up to 33–50x higher (e.g. `openai/gpt-5.5` = $5/$30, `config/pricing.yaml`). `_catalog_rates()` (lines 90-97) overrides baselines at import, but **any catalog load failure is caught, logged as a warning, and silently degrades every model to baseline** — with `match_type: "exact"`, `unknown_model: False`, `pricing_status` defaulting `PRICED_WITH_CAVEAT` (lines 357-362). A run whose catalog import breaks (path move, YAML error, `ImportError` at line 18-21) would report ~1/30th of true spend while looking confidently priced, and `--max-cost-usd` enforcement (`check_limit`, `spend_ledger.py:924-928`; wired at `run_extraction_v5.py:23602`, checked at 11424/11517/11592) would be computed against those understated totals — the cap could pass while real spend blows through it. Mitigant: `pricing_source_type: "legacy_baseline"` is visible per-entry if anyone looks. **Recommend: catalog-load failure on a live (non-dry) run should be a blocker, not a warning.** → WS1.
2. **LOW (good behavior, note only)**: unknown-model fallback (`_fallback_cost_rate`, lines 286-299) uses the MAX of known rates — conservative/over-pricing, correct direction for cap safety — and increments `fallback_usage_count` + logs (lines 909-918). But if finding 1 fires first, the "max" is the cheap baseline max, compounding the underestimate.
3. **INFO**: preventive pre-call cap check exists (`make_projected_cost_check`, lines 580-616, explicitly closing prior audit finding F2-MED-1).

### Secret-redaction verification (commit `6ef9b9db1`)
The commit extends `_SECRET_PATTERNS` in `benchmarking/openclaw_dcp_benchmark_result.py:49-60` with OpenAI/Anthropic/Gemini/Google env-assignment patterns and a generic `sk-(proj-)?…` token pattern (Anthropic `sk-ant-…` is covered by that pattern). **Verdict: improved but not complete**:
- **MEDIUM (security)**: no pattern for raw **xAI keys (`xai-…`)** or raw **Google keys (`AIza…`)** — these are only caught in `ENVVAR=value` assignment form, not as bare tokens in provider error text. `XAI_API_KEY=...` assignment form is also absent from the env-var alternation (only OPENAI/ANTHROPIC/GEMINI/GOOGLE/OPENROUTER are listed). → WS1.
- **Scope caveat**: this redaction only guards the OpenClaw result contract's `details` field (`:203`). A second independent `_SECRET_PATTERNS` copy lives in `benchmarking/openrouter_structured_benchmark.py:20` (duplicate logic — drift risk, LOW). The main runner path uses the far stronger generic sanitizer `output_safety.sanitize_text_for_output` (entropy-based long-token candidates, private-key blocks, auth headers) — benchmarking should reuse it instead of maintaining two weaker local pattern lists. → WS1 (consolidation suggestion).
- Provider adapters (`direct_model/adapters/xai.py:16,64`, `openrouter.py:16,64`) reference API keys only by env-var *name* in errors — clean.

### Skim findings (rest of benchmarking/)
- Storage is SQLite (`storage/sqlite_repo.py`) — single-writer; fine for smoke-scale, one line only.
- No `eval`/`exec`/shell-injection surfaces found in skim; smoke CLIs are import-driven.
- NOT deep-dived (survey depth only): `orchestration/attempt_executor.py`, `registry/openrouter_discovery.py` (network discovery — recommend a look if benchmarking is ever operator-exposed), `rollups/`, `scoring/`, `synthesis/` internals. Marked UNKNOWN, not clean.

---

## 2. llm_runtime.py (1,774L) — the LLM seam

**Verdict: FINDINGS — one MEDIUM availability gap (Gemini SDK timeout); secret hygiene is good.**

- **Provider dispatch**: dependency-injected (`LLMRuntimeDeps`, lines 31-86) — all provider/auth/pricing/sanitization behavior supplied by `run_extraction_v5.py` (`_llm_runtime_deps()` at v5:4390 area). Routes normalized to `(provider, model_id, api_key_env)` tuples with fail-closed arity check (`_normalize_route_tuple`, lines 136-154).
- **Retry logic — CLEAN**: `should_retry` (lines 97-115) refuses retry on `auth_*`, `quota_or_billing`, `api_key_missing_or_invalid`, `permission_denied`; retries only 408/429/5xx and timeout/connection-reset exceptions. Exponential backoff capped (`backoff_seconds`, lines 118-122). No infinite-retry path (attempt-bounded by callers).
- **Timeouts — MEDIUM finding**: an overall deadline exists (default 180s, `_remaining_timeout_seconds`, lines 670-696) and is passed to HTTP requests (line 726) and to OpenAI/xAI/OpenRouter SDK calls (`chat_kwargs["timeout"]`, line ~770). **But the Gemini SDK path passes no timeout**: `deps.get_gemini_client(api_key)` (line 733) — the deps signature is `Callable[[str], Any]` (line 49) so `get_gemini_client`'s `timeout_seconds` parameter (v5:10645, which would set `HttpOptions(timeout=…)`) is never used, and `client.models.generate_content(...)` (lines ~754-758) has no per-call timeout. A hung Gemini call can stall a lane indefinitely; the deadline bookkeeping doesn't preempt it. → WS2 (one-line fix: thread `_remaining_timeout_seconds()` into `get_gemini_client`).
- **Secret handling in logs — CLEAN (verified)**: header *values* are never persisted — only `sent_header_keys` (names, line 539) and boolean `auth_present_flags` (lines 530-544). Gemini `query_key` mode puts the API key in the URL, but everything persisted goes through `endpoint_effective`/`endpoint_fingerprint` → `_sanitize_url` (v5:10348-10365) which replaces the `key` query param with `REDACTED` and fingerprints only host+path. Error text goes through `sanitize_error_text` → `output_safety.sanitize_text_for_output` (v5:11800), which covers bearer/auth-header/assignment/private-key/long-token patterns. No leak path found at survey depth.
- **Error handling**: failures classified (`classify_failure_type` dep), auth failures fail closed (no retry, surfaced as `auth_*`), spend-abort integrated (`is_spend_aborted`, `cost_abort_failure_meta`, `check_projected_cost_limit`, `accumulate_runtime_spend` deps — cost checks happen pre-call, accumulation post-call). Spend/pricing itself delegated to spend_ledger (area 1).
- NOT reviewed line-by-line: `call_llm_with_ladder` (1064+), comparison-lane functions (1472-1774) — structure looks conventional; UNKNOWN.

---

## 3. reporting.py (1,121L) + rte_reports.py (305L)

**Verdict: FINDINGS — one MEDIUM secret-adjacent leak (webhook URL in manifest); otherwise clean.**

- **Relationship**: `rte_reports.py` is a thin binding layer that injects concrete deps and delegates every function to `reporting.py` (`rte_reports.py:8-24`). One report inventory, not two.
- **Report inventory**: step metrics snapshot, failure index snapshot, run dashboard snapshot, certification result, RUN_MANIFEST, phase coverage manifest, coverage rollup, resume proof, proof pack, blocked-promptset proof pack + marker, runner identity (function list `reporting.py:75-1082`).
- **MEDIUM (security)**: `write_run_manifest` embeds the **raw webhook URL** in the manifest: `"dpmx_webhook_url": os.getenv(...)` (`reporting.py:588`). Webhook URLs are frequently bearer-equivalent secrets (Slack/Discord-style capability URLs). The adjacent secret is handled correctly (`dpmx_webhook_secret_set` boolean only, line 589) — the URL should get the same presence-flag or `_sanitize_url` treatment. RUN_MANIFEST files land in run output dirs and are exactly the kind of artifact that gets committed into `reports/` or attached to proof bundles. → WS3.
- **PII**: reports carry file counts, hashes, step IDs, failure histograms + `first_failure` metadata (already-sanitized failure meta from the call path) — no raw source snippets or env dumps found at survey depth. Failure index write is lock-guarded and re-aggregates defensively (`reporting.py:98-147`).
- **Correctness**: `_normalize_gate_status` maps unknown statuses conservatively; nothing observed that fabricates success. One-line note: `except Exception: continue` in histogram aggregation (line ~136) can silently drop malformed rows — cosmetic.

---

## 4. audit_tp008.py (1,327L)

**Verdict: CLEAN (live, referenced) — organization nit only.**

- **Purpose**: TP-008 audit utilities with three modes — legacy contract audit, drift audit against the canonical TP-008 mapping, and model-usage audit against expected lane ladders (docstring, lines 1-9). Pure read/report: argparse + yaml/json, **no subprocess/os.system/eval/exec** (grep verified), writes only under `reports/strict_closure/`.
- **Still referenced? YES — live**: (1) `src/dopemux/commands/extractor_validation.py:836` invokes it by resolved path from the operator validation surface; (2) `tests/test_audit_tp008_drift.py:11-12` imports it via `importlib.util.spec_from_file_location`; (3) historical references in `reports/extraction/gate/2026-03-11/*` and `reports/work-recovery/…/salvage-classification.md`. Not orphaned; do **not** archive.
- **One-liner (cosmetic)**: it's a 1.3KLoC module loaded by file path from two places because it sits at service root outside any package — moving it into a package would let both callers import it normally. LOW → deferred list.

---

## 5. s_int/, fl_int/, sp/ phase subsystems

**Verdict: FINDINGS — routing-truth fragmentation (shadow-twin pattern), plus one consistency observation for the pre-live gate.**

- **s_int/** (7 files): Phase S_INT — synthesis-integration steps S16-S20 (MCP split validity, hook surface map, contract coverage, gradecard, v1 release plan — `s_int/models.py:43-49`). **Live**: invoked from `run_extraction_v5.py:23149-23151` and `run_extraction_v3.py:11549-11551` when `--phase S_INT`.
- **fl_int/** (7 files): Feature-Ledger integration (steps produce `MASTER_FEATURE_LEDGER.json`, `FEATURE_LEDGER_ROUTING.json` — `fl_int/run_fl_int.py:642-645`). **Live**: root `run_fl_int.py:16-18` wraps it; reuses `s_int.schema_validate` for validation (good reuse).
- **sp/** (3 files): SP synthesis-phase step definitions SP0-SP12 + prompt renderer (`sp/models.py`, `sp/render.py`). **Effectively orphaned from the runtime**: only importer is `tests/test_sp_render.py:7-8`. The runner's SP-registry mode does **not** use `sp/` — `rte_promptset.resolve_phase_s_prompts` (rte_promptset.py:291+) loads a JSON registry file instead.
- **MEDIUM (dual truth / drift risk)**: SP step definitions exist twice — `sp/models.py:SP_STEPS` (with `ladder_name`/`routing_tier`/`max_hops` that nothing at runtime consumes) and the Phase-S JSON registry consumed by the runner. The pre-live gate's `SP_CONTRACT_MISSING` P0 check (validate_pre_live_gate_v25.py:105,600) guards the registry path only; `sp/models.py` can drift silently. Either delete `sp/`'s routing metadata or make it the generator of the registry. → WS3/WS5.
- **HIGH-adjacent, same family as area 6's v3 note (routing bypass, money-relevant)**: `s_int/models.py:20-41` and `fl_int/models.py:105-131` **hardcode their own model ladders** (provider/model/API-key-env triples), fully bypassing `model_map.yaml` and the v5 cost-profile mechanism — and the two ladders differ (fl_int prefers Gemini first; s_int prefers OpenRouter GPT-5.3-codex first; both escalate to `openrouter/anthropic/claude-opus-4-6`). Mitigant verified: execution still flows through v5's `call_llm`/`call_llm_with_ladder` (prompt_executor closure near v5:23212-23238), so **spend accounting and cost caps do apply** — this is a routing-governance bypass, not a spend-accounting bypass. `--cost-profile`/`--disable-provider` do not constrain S_INT/FL_INT ladders. → WS1 (cost-profile coverage) / WS3.
- Conventions otherwise consistent: same fail-closed schema validation (`validate_payload_or_raise`), outputs sanitized via `output_safety.sanitized_json_text`, dry-run supported, executor injected (testable). Hygiene: 3 broad `except Exception` in input collectors (`s_int/collect_input.py:55,139`, `fl_int/run_fl_int.py:988`) that return empty defaults — acceptable for best-effort input scans, one line only.

---

## Consolidated findings routing

| # | Area | Finding | Severity | Owner |
|---|------|---------|----------|-------|
| F1 | 1 | Catalog-load failure silently degrades all pricing to $0.15/$0.60 baseline; cap math runs on understated spend (`lib/spend_ledger.py:15-16,90-97`) | HIGH (money) | WS1 |
| F2 | 1 | Redaction patterns missing raw `xai-…`/`AIza…` tokens + `XAI_API_KEY=` assignment (`benchmarking/openclaw_dcp_benchmark_result.py:49-60`) | MEDIUM (security) | WS1 |
| F3 | 1 | Two weaker local `_SECRET_PATTERNS` copies instead of reusing `output_safety.sanitize_text_for_output` | LOW | WS1 |
| F4 | 2 | Gemini SDK path has no request timeout — `get_gemini_client` called without `timeout_seconds` (llm_runtime.py:733 vs run_extraction_v5.py:10645) | MEDIUM (availability) | WS2 |
| F5 | 3 | Raw `dpmx_webhook_url` embedded in RUN_MANIFEST (`reporting.py:588`) — capability-URL leak risk | MEDIUM (security) | WS3 |
| F6 | 5 | s_int/fl_int hardcoded model ladders bypass cost-profile routing governance (spend caps still apply) | MEDIUM (money-governance) | WS1/WS3 |
| F7 | 5 | `sp/models.py` is a runtime-orphaned shadow twin of the Phase-S JSON registry — drift risk | MEDIUM | WS3/WS5 |
| F8 | 6 | `--max-cost-usd` hard-stop semantics not runtime-verified in this pass (static wiring looks correct: v5:23602 + check_limit call sites) | MEDIUM (money, unverified) | WS1 |
| F9 | 6 | Redaction gap follow-on from `6ef9b9db1` (same as F2) | — | merged into F2 |

## Deferred — not admitted to this program

1. **Full audit of legacy `run_extraction_v3.py` routing** — second cost-profile-unaware model-routing path, guarded only by one drift test (`13f0db81a`). Real, but v3 is legacy; separate scope decision.
2. **Runtime verification of `--max-cost-usd` hard stop** (live-run behavior test) — F8 static review done; dynamic proof needs a spend-capped live run.
3. **`benchmarking/registry/openrouter_discovery.py` network-discovery deep dive** — only relevant if benchmarking becomes operator-exposed.
4. **Relocating `audit_tp008.py` into a package** — cosmetic refactor.
5. **`benchmarking/orchestration`/`rollups`/`scoring`/`synthesis` internals** — surveyed structurally only; no red flags in skim; full pass not justified at current risk level.
6. **Consolidation of the three `_SECRET_PATTERNS`/sanitizer implementations into one shared module** — overlaps F3 but is a refactor program, not an audit finding.

## Validation

- **PASS**: all file/line citations verified against worktree at HEAD `542c17bb4`; git ancestry claims verified via `git merge-base --is-ancestor`.
- **NOT_RUN**: no tests executed, no live calls (mission constraint: read-only, no live calls). Runtime behaviors (F4 hang, F8 cap stop) are static-analysis conclusions only.
