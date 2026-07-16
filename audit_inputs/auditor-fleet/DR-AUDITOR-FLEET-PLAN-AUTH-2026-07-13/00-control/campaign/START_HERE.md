# Start Here

## Campaign

`DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`

## Purpose

Research the external facts needed to design a cost-effective Dopemux audit broker and
optional custom GitHub runner that can route audits across:

- mechanical validation only;
- Grok Build;
- AGY / Google Antigravity;
- Gemini CLI;
- Codex;
- Claude Code;
- OpenCode;
- OpenRouter fallback.

The local capability investigation is complete but static-only. Live model probes were
not run, plan-backed authentication was not independently demonstrated for every tool,
and provider/model identity remains limited. This campaign researches only the remaining
external questions. It must not overwrite local runtime evidence with vendor marketing.

## Required local inputs

Before running any track, upload or otherwise provide these accepted investigation outputs:

```text
AUDITOR_CAPABILITY_MATRIX.json
AUTHENTICATION_AND_TERMS_MATRIX.md
MECHANICAL_VALIDATION_INVENTORY.json
ROUTING_CONSTRAINTS.md
TOOL_SELECTION_CANDIDATES.json
BLOCKERS_AND_UNKNOWNS.json
MODEL_IDENTITY_OBSERVATIONS.json
NETWORK_AND_CONTAINMENT_OBSERVATIONS.md
PROBE_SUMMARY.md
HANDOFF_TO_GPT56PRO.json
PROOF_MANIFEST.json
```

Provide the static and live receipt indexes when available. Do not upload credential files,
session databases, OAuth tokens, cookies, keychains, or raw secret-bearing environment dumps.

## Run order

1. Run `tracks/DR-01-VENDOR-PLAN-AUTH-AND-TERMS.md`.
2. Run `tracks/DR-02-LOCAL-BROKER-AND-SELF-HOSTED-RUNNER-SECURITY.md`.
3. Run `tracks/DR-03-TOOL-AUTOMATION-AND-CONTAINMENT.md`.
4. Run `tracks/DR-04-AUDIT-ROUTING-EVALUATION-AND-INDEPENDENCE.md`.
5. Run `tracks/DR-05-API-FALLBACK-PRIVACY-AND-COST.md`.
6. Run `acceptance/DR-INDEPENDENT-ACCEPTANCE-PROMPT.md` against all five reports.
7. If accepted, use `synthesis/GPT56PRO-SYNTHESIS-HANDOFF-PROMPT.md`.

Each track should be a separate Deep Research run. This keeps source retrieval focused and
makes contradictions visible instead of letting one giant report average them into beige fog.

## Model posture

Use ChatGPT Deep Research. Record the displayed UI model label as `GPT-5.6 Pro`, but classify
that as a UI/configuration claim rather than provider-attested model identity.

## Final gate

Do not begin architecture synthesis until the acceptance run emits one of:

```text
ACCEPT_FOR_SYNTHESIS
ACCEPT_WITH_CARRIED_UNKNOWNS
REJECT_TRACKS_REQUIRE_RESEARCH_REPAIR
BLOCKED_INSUFFICIENT_INPUTS
```
