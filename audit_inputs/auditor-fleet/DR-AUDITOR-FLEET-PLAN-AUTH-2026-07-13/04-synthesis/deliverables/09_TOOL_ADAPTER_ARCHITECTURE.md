# Tool Adapter Architecture

**Campaign:** `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`  
**Artifact:** `09_TOOL_ADAPTER_ARCHITECTURE.md`  
**Synthesis gate:** `ACCEPT_WITH_CARRIED_UNKNOWNS`  
**Architecture verdict:** `READY_WITH_BLOCKING_QUESTIONS`  
**Scope:** Specification only. No implementation, credential change, runner registration, live model probe, API call, route certification, or repository mutation is authorized.


## Adapter principle

`PROPOSED` An adapter converts one approved request into one tool invocation and one normalized receipt. It does not authorize credentials, certify quality, choose fallback, or decide merge readiness.

## Uniform adapter interface

Each adapter specification must declare:

- `adapter_id` and version;
- tool executable or API surface;
- supported execution modes;
- required auth class;
- approved deployment classes;
- exact config-root behavior;
- disabled tool, MCP, hook, plugin, skill, memory, subagent, shell, write, and web surfaces;
- network policy;
- input package format;
- output parser and schema;
- exit and timeout mapping;
- identity and usage evidence;
- known unsupported modes;
- conformance receipt hash;
- certification ID and expiry;
- revocation triggers.

## Adapter lifecycle

```text
DISCOVERED
  -> SPECIFIED_DISABLED
  -> STATIC_CONFORMANCE_PASSED
  -> AUTHORIZATION_PASSED
  -> LIVE_CONFORMANCE_PASSED
  -> SHADOW_EVALUATED
  -> CERTIFIED_OPERATOR_TRIGGERED
  -> CERTIFIED_AUTOMATED
  -> SUSPENDED | REVOKED
```

No accepted tool is beyond `SPECIFIED_DISABLED` today, except mechanical validation, which has an observed static execution inventory.

## Adapter matrix

| Adapter | Current disposition | Intended role | Promotion prerequisites |
|---|---|---|---|
| `mechanical` | `CURRENTLY_IMPLEMENTABLE` | Deterministic preflight and narrow closure | Read-only command allowlist, no-network worker, validator authority registry, proof integration |
| `codex_cli` | `BLOCKED_PENDING_EVIDENCE` | First model-adapter conformance candidate | Approved auth route, dedicated worker, sandbox/config negative checks, strict output schema, identity receipt, failure mapping, shadow certificate |
| `claude_code` | `BLOCKED_PENDING_EVIDENCE` | First model-adapter conformance candidate | First-party auth, setup-token lifecycle, clean settings proof, no-tools profile, network proof, identity receipt, output schema, certificate |
| `gemini_cli` | `BLOCKED_PENDING_EVIDENCE` | Secondary native-envelope candidate | Supported account/API route, sandbox and tool-denial proof, native envelope normalizer, identity/usage receipt, certificate |
| `grok_build` | `OPERATOR_TRIGGERED_OR_BLOCKED` | Supervised local or future adapter | Version-matched `0.2.99` documentation, plan-session permission or separate API route, complete containment, exit contract, certificate |
| `agy` | `MANUAL_OR_RESEARCH_ONLY` | Manual receipt | Official unattended receipt and lifecycle contract, complete containment, versioned output/exit behavior, certificate |
| `opencode` | `RESEARCH_ONLY` | Provider adapter research | Upstream vendor authorization, deterministic provider/fallback behavior, actual upstream identity, clean config root, strict receipt contract, certificate. It remains blocked from independence-critical routes until those facts are proven. |
| `openrouter_api` | `DESIGNABLE_DISABLED` | Public low-risk API fallback | Exact provider/model profile, fallback disabled, privacy and cost approval, returned provenance validation, certificate |
| `direct_provider_api` | `DESIGNABLE_DISABLED` | Exceptional private/governed fallback | Approved project and contract, key isolation, ZDR/retention review, cost cap, identity/usage receipt, certificate |
| `manual_receipt` | `DESIGNABLE` | Human-operated compatibility path | Manual receipt schema, exact-head display, artifact hash, operator attestation, evidence-confidence labeling |

## Containment profile

`PROPOSED` A model adapter should receive only:

- canonical request metadata;
- exact diff text or bounded file excerpts;
- explicit audit contract text;
- mechanical evidence summary;
- no live repository checkout;
- no hidden global instructions;
- no untrusted tool configuration;
- no GitHub token;
- no shared filesystem with another provider profile.

The wrapper rejects any tool mode that enables broad shell, filesystem writes, browser control, MCP, plugins, hooks, skills, memory, subagents, or provider fallback unless that surface is explicitly required and separately certified. For the initial audit role, the target profile is data-only and no-tool.

## Output normalization

| Tool | Normalization posture |
|---|---|
| Codex | Prefer caller-supplied final schema; preserve JSONL events as supporting trace |
| Claude Code | Use documented JSON/schema surface only after installed-version conformance |
| Gemini CLI | Normalize documented native JSON envelope; do not claim custom strict schema until proven |
| Grok Build | Treat local schema flags as host evidence, but require version-matched official contract |
| AGY | No unattended normalizer until stable machine export exists |
| OpenCode | Prefer server/OpenAPI integration, but block proof authority until provider provenance is solved |
| OpenRouter/direct APIs | Require structured output plus raw route metadata and request IDs |
| Manual | Normalize transcript/screenshot hashes, never invent missing machine metadata |

## Adapter failure contract

`PROPOSED` Map tool-specific behavior into shared classes:

- `AUTH_FAILURE`
- `TERMS_BLOCK`
- `CONFIG_DRIFT`
- `CONTAINMENT_FAILURE`
- `NETWORK_POLICY_FAILURE`
- `TIMEOUT`
- `SCHEMA_INVALID`
- `IDENTITY_MISSING`
- `PROVIDER_MISMATCH`
- `QUOTA_OR_RATE_LIMIT`
- `COST_ADMISSION_FAILURE`
- `TOOL_INTERNAL_FAILURE`

None of these automatically selects another adapter.

## Adapter research order

`INFERRED` Prioritize Codex CLI and Claude Code for conformance because their accepted first-party automation and structured-output surfaces are strongest. This is research ordering, not route binding or certification. Gemini follows. Grok, AGY, and OpenCode remain behind more fundamental provenance or lifecycle gaps.
