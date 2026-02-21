---
id: PIPELINE_PROOF
title: Pipeline Proof
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-21'
last_review: '2026-02-21'
next_review: '2026-05-22'
prelude: Pipeline Proof (explanation) for dopemux documentation and developer workflows.
---
# Pipeline Proof Pack Runbook

## 1. Required command sequence

```bash
run_id="$(cat extraction/latest_run_id.txt)"
python UPGRADES/run_extraction_v3.py --preflight-providers
python UPGRADES/run_extraction_v3.py --doctor-auth --gemini-transport openai_compat_http --gemini-auth-mode auto
python UPGRADES/run_extraction_v3.py --phase A --resume
python UPGRADES/run_extraction_v3.py --phase H --resume
python UPGRADES/run_extraction_v3.py --phase D --resume
python UPGRADES/run_extraction_v3.py --phase C --resume
python UPGRADES/run_extraction_v3.py --phase R --dry-run
python UPGRADES/run_extraction_v3.py --coverage-report --phase R
```

Collect:

- `extraction/doctor/AUTH_DOCTOR.json`
- `extraction/doctor/PROVIDER_PREFLIGHT.json`
- `extraction/runs/$run_id/RUN_MANIFEST.json`
- `extraction/runs/$run_id/PROOF_PACK.json`

## 2. Phase R required artifact globs (exact)

These are enforced by `R_REQUIRED_ARTIFACT_GROUPS` in `UPGRADES/run_extraction_v3.py`.

### Phase A (`extraction/runs/$run_id/A_repo_control_plane/norm/`)

- `REPO_INSTRUCTION_SURFACE.json`
- `REPO_INSTRUCTION_REFERENCES.json`
- `REPO_MCP_SERVER_DEFS.json`
- `REPO_MCP_PROXY_SURFACE.json`
- `REPO_ROUTER_SURFACE.json`
- `REPO_HOOKS_SURFACE.json`
- `REPO_IMPLICIT_BEHAVIOR_HINTS.json`
- `REPO_COMPOSE_SERVICE_GRAPH.json`
- `REPO_LITELLM_SURFACE.json`
- `REPO_TASKX_SURFACE.json`

### Phase H (`extraction/runs/$run_id/H_home_control_plane/norm/`)

- `HOME_MCP_SURFACE.json`
- `HOME_ROUTER_SURFACE.json`
- `HOME_PROVIDER_LADDER_HINTS.json`
- `HOME_LITELLM_SURFACE.json`
- `HOME_PROFILES_SURFACE.json`
- `HOME_TMUX_WORKFLOW_SURFACE.json`
- `HOME_SQLITE_SCHEMA.json`

### Phase D (`extraction/runs/$run_id/D_docs_pipeline/norm/`)

- `DOC_TOPIC_CLUSTERS.json`
- `DOC_SUPERSESSION.json`
- `DOC_CONTRACT_CLAIMS.json`
- `DUPLICATE_DRIFT_REPORT.json` or `DOC_RECENCY_DUPLICATE_REPORT.json`
- `DOC_INDEX.json`

### Phase C (`extraction/runs/$run_id/C_code_surfaces/norm/`)

- `SERVICE_ENTRYPOINTS.json`
- `EVENTBUS_SURFACE.json`
- `EVENT_PRODUCERS.json`
- `EVENT_CONSUMERS.json`
- `DOPE_MEMORY_CODE_SURFACE.json`
- `DOPE_MEMORY_SCHEMAS.json`
- `DOPE_MEMORY_DB_WRITES.json`
- `TRINITY_ENFORCEMENT_SURFACE.json`
- `REFUSAL_AND_GUARDRAILS_SURFACE.json`
- `TASKX_INTEGRATION_SURFACE.json`
- `WORKFLOW_RUNNER_SURFACE.json`
- `DETERMINISM_RISK_LOCATIONS.json`
- `IDEMPOTENCY_RISK_LOCATIONS.json`
- `CONCURRENCY_RISK_LOCATIONS.json`

## 3. Request provenance proof

From one run, capture two raw request-meta sidecars (one success and one failure) and verify each contains:

- `runner_script_sha256`
- `runner_script_path`
- `transport`
- `endpoint_effective`
- `endpoint_transport_signature`
- `provider_signature`
- `routing_signature`
- `gemini_auth_mode_effective` (Gemini calls)

This proves artifacts were produced by one runner identity and one endpoint/auth signature family.

## 4. Fail-fast auth proofs

- `auth_expired` is non-retryable and now fail-fast even when `--no-fail-fast-auth` is set.
- `--phase ALL` now blocks before execution when provider preflight fails.
- `AUTH_DOCTOR.json` now includes per-mode checks with succeeded/failed mode sets and a deterministic summary line.

## 5. Review checklist

- [ ] `AUTH_DOCTOR.json` exists and has `checks[]`, `succeeded_modes`, `failed_modes`, `summary`
- [ ] `PROVIDER_PREFLIGHT.json` status is `PASS` before `--phase ALL`
- [ ] No `R2_synthesis/` folder exists in the run tree
- [ ] A/H/D/C norm directories satisfy all required glob groups
- [ ] `RUN_MANIFEST.json` and `PROOF_PACK.json` updated for the same `run_id`
