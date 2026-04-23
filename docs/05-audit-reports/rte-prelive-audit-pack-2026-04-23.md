---
id: rte-prelive-audit-pack-2026-04-23
title: RTE Pre-Live Audit Pack
type: reference
owner: codex
date: 2026-04-23
status: complete
author: '@codex'
last_review: '2026-04-23'
next_review: '2026-07-22'
prelude: Deterministic pre-live Repo Truth Extractor audit pack for GPT-5.4 Pro review.
---
# RTE Pre-Live Audit Pack

**Task packet**: `TP-DMX-RTEAUDIT-001`  
**Audit date**: `2026-04-23`  
**Execution branch**: `codex/rte-audit-pack-assembly`  
**Target reviewer**: `GPT-5.4 Pro`  
**Scope**: assemble evidence only; no live RTE execution

---

## 1. Repo Identity And Scope Guard

Observed directly in this checkout:

- Repo root resolves to `/Users/hue/code/dopemux-mvp`
- `.dopetaskroot` exists at repo root
- `origin` remote is `https://github.com/DDD-Enterprises/dopemux-mvp.git`
- Current execution branch for this packet is `codex/rte-audit-pack-assembly`

Working constraints honored:

- No runtime code, service code, prompt content, or production config was edited for this packet
- No live repo-truth-extractor run was executed
- This pack uses runtime code, registries, tests, emitted artifacts, and existing proofs as evidence
- Documentation-only claims are called out separately from code-path evidence

Current worktree drift observed in the local checkout at packet start:

- Modified `AGENTS.md`
- Modified `task-packets/INDEX.md`
- Untracked `.claude/worktrees/`
- Uncommitted/untracked in the local worktree at packet start: `docs/05-audit-reports/repo-branch-worktree-cleanup-phase3.md`
- Uncommitted/untracked in the local worktree at packet start: `task-packets/TP-DMX-REPOHYG-003.json`

This packet does not normalize or overwrite that unrelated state.

---

## 2. Authority Used

### 2.1 Runtime Code Authority

- Canonical RTE runtime entrypoint: `services/repo-truth-extractor/run_extraction_v5.py`
- Compatibility runtime: `services/repo-truth-extractor/run_extraction_v4.py`
- Launch gate validator: `services/repo-truth-extractor/validate_pre_live_gate_v25.py`
- Prescan runtime prompt source: `services/repo-truth-extractor/lib/prescan/grok_passes.py`

### 2.2 Prompt And Registry Authority

- Canonical v4 promptset manifest: `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
- Canonical phase-SP registry: `services/repo-truth-extractor/prompts/phase_s/registry.json`
- Canonical prescan governance registry: `services/repo-truth-extractor/prompts/prescan/registry.json`

### 2.3 Test Authority

- `tests/unit/test_repo_truth_extractor_prompt_governance.py`
- `tests/unit/test_prescan_online_gate.py`

### 2.4 Existing Audit And Proof Context

- `docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md`
- `services/repo-truth-extractor/README.md`
- `docs/05-audit-reports/repo-branch-worktree-audit-2026-04-23.md`
- `docs/05-audit-reports/repo-branch-worktree-cleanup-phase2.md`
- `proof/repo-branch-worktree-cleanup-phase2.proof.json`
- `proof/rte-provider-preflight-scope-truth-hardening.proof.json`
- `proof/rte-doctor-diagnostic-clarity-and-final-launch-gate-review.proof.json`
- `reports/repo-truth-extractor/pre_live_gate_v25/pre_live_gate_v25_20260418T031822Z/VALIDATION_VERDICT.json`
- `services/repo-truth-extractor/extraction/repo-truth-extractor/v5/runs/run_20260418T040217Z/{RUN_MANIFEST.json,PHASE_GATE_DECISION.json,RUN_ROUTING_FINGERPRINT.json}`

### 2.5 Named-But-Absent Or Drifted Authority

The repo-level `AGENTS.md` still names these truth-doc paths as available:

- `tmp/dmx-chatgpt-project-truth-extraction-002/TRUTH_SYSTEMS.md`
- `tmp/dmx-chatgpt-project-truth-extraction-002/TRUTH_CANONICALS.md`
- `tmp/dmx-chatgpt-project-truth-extraction-002/TRUTH_GAPS.md`

Those exact paths were not present in this checkout during this packet. They were therefore not used as authority.

---

## 3. Canonical Runtime And Launch Surfaces

### 3.1 Canonical Runtime

Observed directly:

- `services/repo-truth-extractor/run_extraction_v5.py` is the strongest execution authority for current RTE runs
- `docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md` aligns with that code-path and classifies v4 as compatibility and v3 as legacy/fallback
- `run_extraction_v5.py` imports promptset, routing, output layout, reporting, phase wrappers, and LLM runtime surfaces directly, which makes it the canonical launch-relevant orchestration surface

### 3.2 Compatibility And Drift Surfaces

- `services/repo-truth-extractor/run_extraction_v4.py`: compatibility writer preserving v4 prompt/artifact contracts while delegating supported execution to v5
- `services/repo-truth-extractor/README.md`: documentation surface that broadly matches v5 authority, but remains documentation-only and can drift from runtime
- `dopemux extractor` references described in docs are not treated here as canonical runtime because runtime truth is centered in the v5 runner and validator code

### 3.3 Launch-Relevant Open PRs

Observed directly from `gh pr list --state open --limit 20` on `2026-04-23`:

- PR `#502`: `docs(audit): execute phase2 safe archive cleanup` on `codex/repo-hygiene-phase2-safe-archive-cleanup`
- PR `#501`: `docs(repo-hygiene): audit branches and worktrees, add cleanup plan` on `codex/repo-hygiene-audit-phase1`

Observed directly:

- No open PR in the sampled remote set is an RTE runtime or prompt change PR
- The open PRs are hygiene/documentation-adjacent and still matter to launch readiness because repo cleanup state can affect operator trust and audit clarity

---

## 4. Prompt Surface Classification

This section classifies only prompt surfaces that materially affect current RTE execution or launch gating.

| Surface | Classification | Why it belongs in the pack | Code-path evidence |
| --- | --- | --- | --- |
| `services/repo-truth-extractor/promptsets/v4/promptset.yaml` | canonical | Declares active v4 prompt/artifact contract consumed by runtime and validator | Referenced by `run_extraction_v4.py`, `validate_pre_live_gate_v25.py`, and snapshot tests |
| `services/repo-truth-extractor/promptsets/v4/prompts/` | canonical | Contains the main phase prompt files enumerated into current run manifests | `RUN_MANIFEST.json` for `run_20260418T040217Z` lists these prompt files |
| `services/repo-truth-extractor/prompts/phase_s/registry.json` | canonical | Governs SP post-review registry-driven prompts and outputs | Verified by `tests/unit/test_repo_truth_extractor_prompt_governance.py` |
| `services/repo-truth-extractor/prompts/phase_s/PROMPT_SP11_CONTRACT_LINTER.md` | canonical | High-value launch-relevant contract-lint prompt referenced by registry and snapshot tests | Registry and validator-suite snapshot test reference it directly |
| `services/repo-truth-extractor/prompts/prescan/registry.json` | canonical_governance | Canonical governance metadata for prescan steps, schemas, and intended providers | Verified by `tests/unit/test_repo_truth_extractor_prompt_governance.py` |
| `services/repo-truth-extractor/lib/prescan/grok_passes.py` | canonical_runtime | Actual prescan system prompt constants and online gating logic live here, not in markdown prompt files | Verified by `tests/unit/test_prescan_online_gate.py` and governance test |
| `services/repo-truth-extractor/prompts/phase_fl_int/registry.json` | compatibility | Present as a registry population checked by governance tests, but not demonstrated here as the canonical first-live runtime path | Governance test checks presence; no stronger launch-path proof assembled in this packet |
| `services/repo-truth-extractor/prompts/phase_s_int/registry.json` | compatibility | Same status as `phase_fl_int`; registry exists and is tested, but this packet does not prove it as the canonical pre-live path | Governance test checks presence; canonicality not elevated here |
| `audit_prep/*` bundles and `audit_inputs/*` seeds | drifted | Useful historical/operator prep material, but not shown as active runtime prompt authority | Located in repo, not referenced by current v5 runtime evidence in this packet |
| `docs/archive/**/prompt*` | drifted | Historical prompt materials; inclusion would add noise and authority confusion | Archive location signals non-canonical status |
| `services/repo-truth-extractor/README.md` prompt examples | documentation_only | Helpful operator guidance, but not canonical prompt authority | README is prose, not prompt registry/runtime |
| Any `tmp/dmx-chatgpt-project-truth-extraction-002/TRUTH_*.md` prompt-related inference | unknown | Named by AGENTS, absent in checkout | Files not present |

Key observed drift:

- `services/repo-truth-extractor/prompts/prescan/registry.json` says prescan prompts are Python constants in `lib/prescan/grok_passes.py`; therefore the registry is governance metadata, not the canonical prompt text source
- `reports/repo-truth-extractor/pre_live_gate_v25/pre_live_gate_v25_20260418T031822Z/VALIDATION_VERDICT.json` records `repo_drift_tests` failure in `services/repo-truth-extractor/tests/test_promptset_v4_lint.py` because prescan constants were reported as not found even though `_DEDUP_SYSTEM_PROMPT`, `_DISCOVER_SYSTEM_PROMPT`, `_FEASIBILITY_SYSTEM_PROMPT`, and `_OPTIMIZE_SYSTEM_PROMPT` are present in `lib/prescan/grok_passes.py`

That mismatch is preserved as current launch-relevant drift, not normalized away.

---

## 5. Recommended Upload Set

This set is intentionally bounded for ChatGPT Project upload use. It favors canonical runtime, compact registries/manifests, targeted tests, current run evidence, and current gate evidence.

### 5.1 Upload Set A: Core Runtime And Prompt Contract

1. `services/repo-truth-extractor/run_extraction_v5.py`
2. `services/repo-truth-extractor/run_extraction_v4.py`
3. `services/repo-truth-extractor/validate_pre_live_gate_v25.py`
4. `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
5. `services/repo-truth-extractor/prompts/phase_s/registry.json`
6. `services/repo-truth-extractor/prompts/prescan/registry.json`
7. `services/repo-truth-extractor/lib/prescan/grok_passes.py`

### 5.2 Upload Set B: Targeted Tests

8. `tests/unit/test_repo_truth_extractor_prompt_governance.py`
9. `tests/unit/test_prescan_online_gate.py`

### 5.3 Upload Set C: Current Launch Evidence

10. `reports/repo-truth-extractor/pre_live_gate_v25/pre_live_gate_v25_20260418T031822Z/VALIDATION_VERDICT.json`
11. `services/repo-truth-extractor/extraction/repo-truth-extractor/v5/runs/run_20260418T040217Z/RUN_MANIFEST.json`
12. `services/repo-truth-extractor/extraction/repo-truth-extractor/v5/runs/run_20260418T040217Z/PHASE_GATE_DECISION.json`
13. `services/repo-truth-extractor/extraction/repo-truth-extractor/v5/runs/run_20260418T040217Z/RUN_ROUTING_FINGERPRINT.json`

### 5.4 Upload Set D: Compact Context

14. `docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md`
15. `proof/rte-provider-preflight-scope-truth-hardening.proof.json`
16. `proof/rte-doctor-diagnostic-clarity-and-final-launch-gate-review.proof.json`
17. `docs/05-audit-reports/repo-branch-worktree-cleanup-phase2.md`

Recommended use:

- Upload Set A+B+C as the minimum launch-review pack
- Add Set D only if the review needs compact narrative context or prior hardening provenance

Not recommended for the first upload:

- Full prompt directories beyond the active registries and manifests
- Archive prompt bundles
- Large historical run trees
- Proofs unrelated to current launch readiness

---

## 6. Deterministic File Inventory

Each included file below has a stated reason and an upload recommendation.

| Path | Authority class | Reason for inclusion | Upload to GPT-5.4 Pro |
| --- | --- | --- | --- |
| `services/repo-truth-extractor/run_extraction_v5.py` | canonical_runtime | Strongest execution authority for current RTE launch behavior | yes |
| `services/repo-truth-extractor/run_extraction_v4.py` | compatibility_runtime | Shows current compatibility layer and v4 contract preservation boundary | yes |
| `services/repo-truth-extractor/validate_pre_live_gate_v25.py` | canonical_gate | Defines the bounded pre-live validator used by first-live flows | yes |
| `services/repo-truth-extractor/promptsets/v4/promptset.yaml` | canonical_prompt_contract | Declares active promptset contract and phase/step outputs | yes |
| `services/repo-truth-extractor/prompts/phase_s/registry.json` | canonical_prompt_registry | Direct registry authority for SP prompt steps and outputs | yes |
| `services/repo-truth-extractor/prompts/prescan/registry.json` | canonical_governance_registry | Governs prescan step metadata and explains registry-vs-runtime split | yes |
| `services/repo-truth-extractor/lib/prescan/grok_passes.py` | canonical_runtime_prompt_source | Holds real prescan prompt constants and online gate enforcement | yes |
| `tests/unit/test_repo_truth_extractor_prompt_governance.py` | canonical_test | Verifies prompt registry population, prompt existence, and deterministic snapshot behavior | yes |
| `tests/unit/test_prescan_online_gate.py` | canonical_test | Verifies online gate behavior for prescan runtime | yes |
| `reports/repo-truth-extractor/pre_live_gate_v25/pre_live_gate_v25_20260418T031822Z/VALIDATION_VERDICT.json` | emitted_launch_evidence | Current no-go gate evidence for provider and drift blockers | yes |
| `services/repo-truth-extractor/extraction/repo-truth-extractor/v5/runs/run_20260418T040217Z/RUN_MANIFEST.json` | emitted_run_evidence | Shows prompt files, routing summary, output layout, and dry-run state for a recent first-live preset run | yes |
| `services/repo-truth-extractor/extraction/repo-truth-extractor/v5/runs/run_20260418T040217Z/PHASE_GATE_DECISION.json` | emitted_run_evidence | Compact gate outcome for the recent first-live preset run | yes |
| `services/repo-truth-extractor/extraction/repo-truth-extractor/v5/runs/run_20260418T040217Z/RUN_ROUTING_FINGERPRINT.json` | emitted_run_evidence | Detailed per-step routing and prompt-file mapping evidence | yes |
| `docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md` | documentation_context | Concise current reference doc that largely matches runtime authority | optional |
| `proof/rte-provider-preflight-scope-truth-hardening.proof.json` | prior_hardening_proof | Shows earlier proof about run-scoped provider preflight authority boundaries | optional |
| `proof/rte-doctor-diagnostic-clarity-and-final-launch-gate-review.proof.json` | prior_hardening_proof | Shows earlier proof separating diagnostic doctor artifacts from launch authority | optional |
| `docs/05-audit-reports/repo-branch-worktree-cleanup-phase2.md` | repo_hygiene_context | Compact evidence that open hygiene PRs are docs-only and bounded | optional |

---

## 7. Current Launch-Relevant Drift

Observed directly from current evidence:

1. `VALIDATION_VERDICT.json` records `operator_verdict = NO_GO_EXTERNAL` and `verdict = NO_GO` for `pre_live_gate_v25_20260418T031822Z`.
2. The same verdict records a P0 `ONLINE_PREFLIGHT_FAILURE` for `openrouter:openai/gpt-5.4` with HTTP `402` and quota/billing classification.
3. The same verdict records a repo drift failure in `services/repo-truth-extractor/tests/test_promptset_v4_lint.py` tied to prescan prompt constant discovery.
4. `PHASE_GATE_DECISION.json` for `run_20260418T040217Z` is `BLOCKED`, with `provider_preflight_status = FAIL` and phase sequence `A,H,D,C`.
5. `RUN_MANIFEST.json` for `run_20260418T040217Z` is a dry-run artifact with `preset = first-live`, `routing_policy = cost`, and `blocked_promptset = false`; it is useful launch evidence but not proof of a successful live run.
6. `AGENTS.md` still points to absent truth-doc paths under `tmp/dmx-chatgpt-project-truth-extraction-002/`, which is documentation drift in the repo’s operator-control layer.

None of these contradictions were normalized away in this packet.

---

## 8. Code-Path Evidence vs Documentation Claims

### 8.1 Code-Path Evidence

- `run_extraction_v5.py` is the canonical runtime authority
- `validate_pre_live_gate_v25.py` is the bounded launch gate authority for pre-live validation
- `grok_passes.py` contains the actual prescan system prompt constants and online gating logic
- Registry and prompt governance tests directly verify active registry surfaces
- Current `VALIDATION_VERDICT.json`, `RUN_MANIFEST.json`, `PHASE_GATE_DECISION.json`, and `RUN_ROUTING_FINGERPRINT.json` are emitted evidence artifacts from prior executions

### 8.2 Documentation-Only Claims

- `system-repotruthextractor.md` and `README.md` are useful summaries, but they do not outrank runtime code or emitted run artifacts
- Open hygiene PRs indicate cleanup work in flight, but they do not by themselves alter RTE runtime authority

---

## 9. Audit Judgment

This pack is ready for a bounded GPT-5.4 Pro pre-live review because:

- it is grounded in the current runtime entrypoint, validator, prompt contracts, registries, tests, and emitted launch artifacts
- each included file has an explicit reason for inclusion
- canonical, compatibility, drifted, and unknown prompt surfaces are separated
- the upload recommendation is small enough for a ChatGPT Project workflow

This pack is not evidence of live-launch readiness. Current emitted evidence still shows:

- provider/billing blockage for the sampled `openrouter:openai/gpt-5.4` live preflight path
- repo drift around prescan prompt linting
- absent named truth-doc paths in repo-level operator guidance

