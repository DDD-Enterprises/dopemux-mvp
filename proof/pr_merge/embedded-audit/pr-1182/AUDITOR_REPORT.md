# Formal Embedded Audit Report — PR #1182 (steward repair head)

**Supervisor decision:** `AUTHORIZE_CODEX_AS_FORMAL_AUDITOR_EXCEPTION` (packet-specific; still in force)

## Identity ledger (real auditor)

| Field | Value |
|---|---|
| runner | codex-cli 0.146.0 |
| configured_model | default/unset |
| response_claimed_model | gpt-5.5 |
| proxy_reported_identity | provider: openai |
| provider_attested_identity | OpenAI Codex session 019fc4ee-bb77-7680-91d5-8bff0a3a38ae (R4) |
| prior sessions | R1 019fc4cf-… · R2 019fc4d4-… · R3 019fc4e8-… |
| implementer | grok-4.5-xai |

**Invocation:** `codex review --base origin/main` on content head `a5fb1e07398b4ad2df741c19040c5295bcdc80fe`

## Schema note

`schemas/proof/embedded_audit.schema.json` on main cannot encode `codex-cli` / `gpt-5.5`. Under the supervisor exception, schema fields `auditor_tool`/`auditor_model` are filled with the minimum schema-valid non-SKIPPED pair required by allOf (not the real auditor). **Real identity is only this ledger + PROOF.supervisor_exception + invocation.**

## Deterministic validation

See review_bundle/DETERMINISTIC_VALIDATION.json — PASS (539; class sum 539; 0 BLOCKS inversions; 0 program roots actionable; 0 needs-rescope routing; 0 gemini dispatchable; 0 actionable without routing).

## Steward repair coverage

1. Wave/BLOCKS topology reconciled
2. Implemented audit-series → verify-close-candidate + evidence
3. Gemini CLI unproven → non-dispatchable cohort
4. Program roots containers
5. needs-rescope non-dispatchable
6. Load-plan LOADED → verification/guarded recovery

## Findings

### F-001 RESOLVED — Review-thread content defects
All MUST_FIX content items from current threads addressed in content head `a5fb1e07398b4ad2df741c19040c5295bcdc80fe`.

### F-002 ACCEPTED_RISK — Schema cannot name Codex
Supervisor exception accepted. Real identity outside enum fields.

### F-003 RESOLVED — Prior stale proof
Prior proof bound to 2cb743117d superseded by this proof bound to `a5fb1e07398b4ad2df741c19040c5295bcdc80fe`.

## Verdict

**PASS_WITH_RISKS** under `AUTHORIZE_CODEX_AS_FORMAL_AUDITOR_EXCEPTION`.
