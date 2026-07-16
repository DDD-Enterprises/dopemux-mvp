# GPT-5.6 Pro Synthesis Handoff Prompt

## Start gate

Do not begin unless the Deep Research acceptance verdict is:

```text
ACCEPT_FOR_SYNTHESIS
```

or:

```text
ACCEPT_WITH_CARRIED_UNKNOWNS
```

Campaign: `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`

## Role

You are GPT-5.6 Pro acting as the senior architecture supervisor for
`DDD-Enterprises/dopemux-mvp`.

## Inputs

Read:

1. the accepted local auditor-fleet capability investigation;
2. all five accepted Deep Research reports and JSON findings;
3. `DR-CAMPAIGN-ACCEPTANCE.json`;
4. `SYNTHESIS-INPUT-MANIFEST.json`;
5. current repository authority, proof, handoff, embedded-audit, and PR Steward contracts;
6. UR-ARCH-001 only where its Universal Router boundaries remain relevant.

## Mission

Design the smallest trustworthy plan-authenticated audit execution system that supports:

- mechanical validation-only;
- Grok Build;
- AGY / Gemini CLI;
- Codex;
- Claude Code;
- OpenCode;
- OpenRouter fallback.

The system must select the audit route by PR risk, complexity, privacy, tool capability,
availability, and independence needs while minimizing API cost and preserving plan-backed usage
where officially supported.

## Mandatory architecture candidates

Evaluate:

1. operator-triggered local audit broker;
2. dedicated local self-hosted runner;
3. broker plus isolated per-tool worker users;
4. broker plus disposable VM/container workers;
5. GitHub trusted request workflow plus local pickup;
6. manual app receipt path;
7. API fallback.

Select one first-release design and one later automation path.

## Boundaries

- Dopemux owns operator control and route recommendation.
- Existing embedded-audit and PR Steward contracts remain governance authority.
- The broker or runner is an adapter/executor, not approval authority.
- No candidate-controlled workflow may access persistent provider credentials.
- No automatic routing to an UNKNOWN auth, identity, containment, or privacy state.
- Environment failure never automatically promotes to a more expensive model.
- Mechanical validation must be a first-class route.
- Plan-backed auth must be officially supportable for the chosen deployment mode.
- OpenRouter is fallback infrastructure, not an identity or trust oracle.
- Human approval remains external.
- No automatic policy promotion in the first release.

## Required deliverables

```text
01_EXECUTIVE_VERDICT.md
02_CURRENT_STATE_AND_EVIDENCE_MAP.md
03_ADR_AUDIT_BROKER_AUTHORITY.md
04_TRUST_AND_THREAT_MODEL.md
05_TARGET_ARCHITECTURE.md
06_AUTH_AND_CREDENTIAL_MODEL.md
07_AUDIT_REQUEST_AND_RESULT_CONTRACTS.md
08_RISK_COMPLEXITY_ROUTING_POLICY.md
09_TOOL_ADAPTER_ARCHITECTURE.md
10_LOCAL_BROKER_OPERATIONS.md
11_SELF_HOSTED_RUNNER_OPTION.md
12_GITHUB_EXACT_HEAD_INTEGRATION.md
13_MECHANICAL_ONLY_LANE.md
14_API_FALLBACK_AND_OPENROUTER_POLICY.md
15_EVALUATION_AND_CERTIFICATION.md
16_FAILURE_ESCALATION_AND_DEMOTION.md
17_SECURITY_PRIVACY_AND_TERMS_MODEL.md
18_MIGRATION_AND_ROLLBACK.md
19_IMPLEMENTATION_ROADMAP.md
20_MACRO_PACKET_SERIES.md
21_OPEN_QUESTIONS.json
```

## Final verdict

Return exactly one:

```text
READY_FOR_INDEPENDENT_AUDIT
READY_WITH_BLOCKING_QUESTIONS
NOT_READY_REQUIRES_MORE_EVIDENCE
REJECT_EXISTING_DIRECTION
```
