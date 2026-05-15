# RTE-PKT-09 Live Validation Plan

This artifact is plan-only. It does not authorize or execute live provider validation.

## Current Packet Boundary

Observed:
- Repo root is `/Users/hue/.codex/worktrees/227d/dopemux-mvp`.
- Branch is `codex/rte-pkt-09-live-validation-plan`.
- Current HEAD before artifact generation is `0179b17b03cf46518aa324bd8f50c805b627631d`.
- Required repo markers for RTE planning are present.
- Local `out/` proof outputs exist for RTE-PKT-01, 02, 03, 04, 05, 06, and 15.
- Local `out/` proof outputs for RTE-PKT-07 and RTE-PKT-08 are missing in this checkout.

Inferred:
- The active packet treats RTE-PKT-07 and RTE-PKT-08 as accepted. This plan preserves that as a packet claim, not as locally revalidated proof.

Unknown:
- Direct xAI live response shape.
- OpenRouter `x-ai/...` live equivalence.
- OpenAI-compatible edge response behavior across every configured provider lane.
- Gemini-compatible refusal, incomplete, and safety-field behavior.
- xAI/OpenAI-compatible downloaded batch output/error JSONL shape.
- ZDR, retention, billing, and account-level live truth.

## Static Runtime Trace Used

Observed from static source inspection:
- `run_extraction_v5.py` exposes provider routing ladders that include OpenAI, Gemini, xAI, and OpenRouter routes.
- `run_extraction_v5.py` live execution requires `--execute` and checks `DPMX_LIVE_OK` before live operation paths.
- `llm_runtime.py` sanitizes system and user content before provider-bound payload construction.
- `llm_runtime.py` records provider, requested model, endpoint, transport, status, response summary, retry trace, and structured-output metadata on sync attempts.
- `batch_clients.py` implements OpenAI-compatible batch behavior and derives `XAIBatchClient` from it.
- `batch_clients.py` explicitly blocks OpenRouter batch submit.
- `batch_retriever.py` supports OpenAI-compatible retrieval for `openai` and `xai`, plus Gemini retrieval helpers.
- `run_extraction_v5.py` CLI `--retrieve-provider` currently exposes `openai` and `gemini` choices only, so future xAI retrieval must not be assumed reachable through that CLI path without rechecking.

## Approval Gate

Future live validation must not start unless all are true:
- Operator explicitly authorizes bounded live validation in a separate instruction.
- The approval is equivalent to: `I authorize bounded live provider validation for RTE under the accepted RTE-PKT-09 plan.`
- RTE-PKT-09 is accepted.
- A dedicated clean worktree is verified.
- The future packet defines the exact providers, models, phases, spend cap, timeout cap, batch cap, artifact root, and cleanup authority.
- Provider credentials are supplied outside proof artifacts.
- Credentials are not printed, copied, committed, or summarized beyond boolean presence.
- Static safety proofs remain accepted or are rechecked.

Must not count as approval:
- Generic continuation language.
- Credentials existing in the environment.
- `DPMX_LIVE_OK` alone.
- A dry-run command.
- A draft PR approval.
- A request to review or generate planning artifacts.

## Default Future Caps

Recommended hard caps for any first live execution packet:
- Provider lanes: only explicitly named lanes.
- Sync prompts: synthetic, non-sensitive, one request per provider/model/route combination.
- Sync timeout: 60 seconds for preflight, 180 seconds per minimal response probe.
- Total wall-clock timeout: 30 minutes unless separately justified.
- Batch size: 1 to 3 requests total.
- Batch poll interval: at least 30 seconds.
- Batch wait timeout: no more than 30 minutes for first pilot.
- Spend cap: operator-set explicit cap, with a recommended first cap of USD 5.00 or lower.
- Batch cancellation: authorized only for validation-created job IDs.
- Remote file cleanup/deletion: separate explicit approval required.

Spend estimates are not billing truth. Billing truth requires provider-side evidence that is separately authorized and redacted.

## Future Phases

### LV-00 Static Readiness Recheck

Live calls: no.

Purpose:
- Reconfirm clean worktree, branch, HEAD, remotes, markers, packet acceptance, redaction gates, live gate, metadata handling, and batch static proof.

Required artifacts:
- `static_readiness_report`
- `accepted_packet_versions`
- `git_sha`
- `dirty_state_report`
- `provider_credentials_presence_boolean_only`
- `redaction_sanity_report`
- `no_live_call_preflight_attestation`

Stop if:
- Worktree is dirty before the run.
- Required packet proof is missing or not accepted.
- Explicit live authorization is absent.
- Spend, timeout, or batch caps are absent.
- Any credential value would be exposed.
- Static recheck finds drift in live gate or redaction behavior.

### LV-01 Provider Preflight Only

Live calls: yes, only after explicit approval.

Purpose:
- Validate minimal auth/model availability/rate-limit surface for explicitly named providers.

Providers:
- `direct_xai`
- `openrouter`
- `openai_compatible`
- `gemini_if_in_scope`

Required artifacts:
- `LIVE_PROVIDER_PREFLIGHT.json`
- redacted auth status
- redacted model availability
- rate-limit or quota status if available
- not-billing-truth marker
- retention/ZDR unknown-or-observed marker

Stop if:
- Auth fails.
- The route or upstream provider differs from the requested lane.
- Any response lacks minimum metadata.
- Output contains credential-shaped material.
- Cost or quota risk exceeds cap.

### LV-02 Minimal Sync Response Metadata Probe

Live calls: yes, only after LV-01 passes for the lane.

Purpose:
- Validate returned/effective model, finish reason, response ID, usage, refusal, incomplete, and route metadata for minimal non-sensitive payloads.

Providers:
- direct xAI
- OpenRouter `x-ai/...`
- OpenAI-compatible
- Gemini-compatible if in scope

Required artifacts:
- `LIVE_RESPONSE_METADATA_MATRIX.json`
- redacted request metadata
- redacted response summary
- requested vs returned model
- finish reason
- usage
- refusal or null marker
- incomplete or null marker
- route kind
- live validation marker

Stop if:
- Returned route/proxy class is unexpected.
- Required response metadata is missing.
- Response content includes unsafe or unredacted data.
- Cost or timeout exceeds cap.

### LV-03 Structured Output Probe

Live calls: yes, only after LV-02 passes for the lane.

Purpose:
- Validate JSON object/schema behavior using minimal schemas only.

Providers:
- direct xAI
- OpenRouter `x-ai/...`
- OpenAI-compatible
- Gemini-compatible only if future packet explicitly includes it.

Required artifacts:
- `LIVE_STRUCTURED_OUTPUT_RESULTS.json`
- structured output mode
- response format type
- schema name and hash
- schema acceptance result
- local schema validation result
- provider failure/success
- no silent downgrade marker

Stop if:
- Schema mode silently downgrades.
- Provider rejects an expected exact schema and the failure is not preserved.
- Local validation fails without preserving the failure.
- Any raw payload or credential-shaped material is emitted.

### LV-04 Minimal Batch Pilot

Live calls: yes, only after explicit batch approval.

Purpose:
- Validate submit, poll, retrieve, cancel, output/error JSONL inventory, and custom_id reconciliation with a tiny synthetic batch.

Providers:
- xAI if the future provider contract explicitly supports it.
- OpenAI-compatible if in scope.
- Gemini if in scope and artifact schema accounts for JSON rather than OpenAI-compatible JSONL.
- OpenRouter is not eligible for batch submit unless runtime support changes in a future packet.

Required artifacts:
- `LIVE_BATCH_PILOT_INDEX.json`
- submit metadata
- batch ID
- custom_id map
- redacted status watch log
- output file ID if success
- error file ID if failure
- downloaded output JSONL if available and authorized
- downloaded error JSONL if available and authorized
- row count reconciliation
- missing row count
- terminal status marker
- partial failure marker
- cleanup/cancel result if authorized

Stop if:
- Batch provider is not explicitly authorized.
- Provider route or remote file lifecycle is unexpected.
- Downloaded JSONL contains credential-shaped material.
- Row count mismatch is not preserved as failure.
- Polling exceeds timeout.
- Cost exceeds cap.

### LV-05 Remote File Lifecycle / Retention Evidence

Live calls: yes, only after separate cleanup/retention approval.

Purpose:
- Collect redacted evidence about validation-created remote files, retention support, cleanup/deletion support, and ZDR/retention claims where provider exposes them.

Required artifacts:
- `LIVE_RETENTION_ZDR_EVIDENCE.md`
- retention claim source
- ZDR header or account setting if available
- validation-created file inventory
- cleanup attempt and result if authorized
- retention unknown marker when not observed

Stop if:
- Cleanup/deletion check is not explicitly authorized.
- Cleanup could affect non-validation files.
- Provider does not expose evidence.
- Evidence would expose account identifiers or secrets.

### LV-06 Final Live Validation Synthesis

Live calls: no.

Purpose:
- Distinguish what is proven live, what is static-only, and what remains unknown.

Required artifacts:
- `LIVE_VALIDATION_SUMMARY.md`
- provider lane verdicts
- batch lane verdict
- retention/ZDR verdict
- spend estimate, explicitly not billing truth
- remaining unknowns
- rollback/cleanup status

## Exit State For This Packet

This packet can only move the series to planned-live-validation readiness. It must not move RTE beyond `READY_FOR_LIMITED_DRY_STATIC_USE`.

All provider and batch live behaviors remain `LIVE_VALIDATION_REQUIRED` until a future explicitly approved live execution packet collects evidence.
