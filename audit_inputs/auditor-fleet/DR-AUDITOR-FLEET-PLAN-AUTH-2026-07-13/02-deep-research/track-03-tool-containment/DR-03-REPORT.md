# DR-03: Tool Automation and Containment

**Campaign:** `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`  
**Track:** `DR-03-TOOL-AUTOMATION-AND-CONTAINMENT`  
**Research date:** 2026-07-13  
**Status:** `COMPLETE_WITH_UNKNOWNS`

## Executive assessment

`OBSERVED` The accepted local capability probe was static-only. Grok Build, AGY, Gemini CLI, Codex CLI, Claude Code, and OpenCode were installed, but no live model invocation occurred. Authentication route, plan billing provenance, actual model identity, and complete live containment therefore remain `UNKNOWN` for every model-capable local tool.

`CLAIMED` Current official documentation exposes meaningful headless or programmatic surfaces for Claude Code, Codex CLI, Gemini CLI, OpenCode, Grok Build, and OpenRouter. The strength of machine-readable output and containment controls varies substantially.

`INFERRED` Codex CLI and Claude Code have the strongest combined first-party automation and containment surfaces among the reviewed local agents. Gemini CLI is automation-capable but lacks a confirmed user-supplied final-output schema contract. OpenCode is best integrated through its documented server/OpenAPI surface, but upstream provider identity and fallback behavior require additional proof. Grok Build has an official headless surface, yet the reviewed documentation does not establish a complete deny-by-default shell, file, network, extension, and inherited-config containment matrix. AGY / Google Antigravity remains unsuitable for deterministic unattended proof generation on the evidence reviewed.

`PROPOSED` Mechanical validation remains the only currently executable lane under the accepted local evidence. All model-capable adapters must remain blocked from unattended execution until authentication provenance, configuration isolation, model identity evidence, and prohibited-surface disablement are proven for the intended deployment.

## Capability table

| Tool | Headless / programmatic surface | Machine-readable output | Strict schema support | Model / reasoning controls | Isolation and containment | Recommended posture |
|---|---|---|---|---|---|---|
| Claude Code | `claude -p` and Agent SDK | JSON and streaming-oriented output modes are documented | Strongest schema guarantees are documented through the Agent SDK; local probe observed `--json-schema` | Model selection documented; dedicated CLI reasoning-effort control not confirmed in this track | `CLAUDE_CONFIG_DIR`, permission rules, sandboxed Bash, MCP/hooks/plugin controls; clean config is not fully sterile on every OS | `BLOCKED` for unattended use pending auth and live containment proof; otherwise automated candidate |
| Codex CLI | `codex exec` | Final stdout, `--json` JSONL events, output-to-file | `--output-schema <path>` validates final response | `--model`; documented reasoning-effort config | `CODEX_HOME`, profiles, ephemeral sessions, sandbox and approval policies, feature disablement | `BLOCKED` for unattended use pending auth provenance; strongest adapter candidate |
| Gemini CLI | `-p/--prompt`, non-TTY headless mode | `text`, `json`, `stream-json` | Built-in JSON envelope; user-supplied final schema not confirmed | `--model`; no confirmed dedicated CLI reasoning-effort flag | Sandbox, approval modes, allow/exclude tool and MCP controls, admin extension/skill switches, telemetry settings | `BLOCKED` pending auth and complete containment proof; automated candidate with normalizer |
| OpenCode | `opencode serve`; local probe also observed `run` | OpenAPI HTTP API and events | No confirmed Codex-style final-response schema contract | `provider/model` selection | Agent permissions can deny tools; clean config root, provider fallback disablement, and actual upstream identity remain unproven | `BLOCKED`; research/adapter candidate only |
| Grok Build | Official headless invocation documented; local probe observed `--single` | JSON/streaming output; local probe observed JSON schema/output flags | Local probe observed `--json-schema`; current official contract still needs version-matched verification | `--model`; local probe observed no-subagent and web-search controls | Partial controls observed, but complete shell/file/network/config isolation not proven | `BLOCKED`; operator-triggered candidate after external sandboxing and auth proof |
| AGY / Antigravity | Local probe observed `--print`; official material reviewed was primarily TUI/codelab-oriented | Stable machine-readable export not established | Not established | Local probe observed `--model` and timeout | Complete extension, MCP, tool, shell, file-write, network, and config isolation not established | `RESEARCH_ONLY` or manual receipt path |
| OpenRouter | HTTPS API / SDK | Normalized JSON and streaming | `response_format` JSON schema for compatible routes | Explicit model, provider, reasoning and routing parameters | Routing/data controls, but no host sandbox | `API_FALLBACK` only; never a local containment or identity authority |
| Mechanical tools | Direct CLI / scripts | Explicit stdout, stderr, exit codes | Wrapper-defined | Not applicable | Caller-controlled OS/process isolation | `AUTOMATED`; only currently observed usable lane |

## Containment-gap table

| Tool | Gap | Claim label | Decision impact |
|---|---|---|---|
| Claude Code | A relocated config directory does not necessarily eliminate managed settings or OS-keychain credentials | `CLAIMED` / `INFERRED` | Use a dedicated OS account or disposable worker for stronger isolation; do not equate config relocation with clean-room proof |
| Codex CLI | Dangerous bypass flags can remove approval and sandbox controls | `CLAIMED` | Wrapper must reject bypass/full-access compatibility paths and fail closed on sandbox unavailability |
| Gemini CLI | Sandbox may not be the default; custom final-output schema remains unconfirmed | `CLAIMED` | Require explicit sandbox and policy configuration; normalize the built-in JSON envelope rather than pretending it is a strict custom proof schema |
| OpenCode | Provider fallback behavior, actual upstream provider/model evidence, config-root isolation, and strict final schema remain incomplete | `UNKNOWN` | Do not claim provider independence or deterministic routing; block unattended adapter promotion |
| Grok Build | Local help shows useful controls, but a complete deny matrix and auth isolation are unproven | `CONFLICTING` | Treat official headless capability as separate from containment proof; require external sandbox and version-matched local verification |
| AGY | Local static help shows a print mode, while reviewed official material did not establish a stable unattended proof contract | `CONFLICTING` | Keep manual/research posture until exact command, output contract, exit behavior, and containment controls are officially documented and locally verified |
| OpenRouter | Router controls do not constrain local shell, filesystem, or execution host | `CLAIMED` | Pair only with a separately contained execution runtime; never call it a sandbox |
| Mechanical tools | Validators have narrow authority and some common commands can mutate or fetch dependencies | `OBSERVED` | Keep an allowlisted offline command set; record each validator’s authority limit |

## Identity and telemetry table

| Tool | Identity evidence | Usage / cost evidence | Local disposition |
|---|---|---|---|
| Claude Code | Requested/configured model can be selected; provider-attested actual model receipt not established here | No complete per-run cost contract established in this track | `UNKNOWN` actual identity after invocation |
| Codex CLI | JSONL and status surfaces can expose model/session/usage-related metadata | Token usage events and enterprise analytics surfaces documented | Still requires local live proof and auth-route attribution |
| Gemini CLI | Streaming initialization/result envelopes can expose session/model/stats | Built-in stats and telemetry controls documented | Treat displayed model as evidence, not provider attestation |
| OpenCode | Configured `provider/model` is observable | Upstream fallback and actual serving provider remain unproven | Cannot satisfy provider-independence proof yet |
| Grok Build | Local inspection and headless output surfaces appear capable of emitting useful receipts | Current xAI material claims token and cost data in headless output | Version-match against installed `grok 0.2.99` before reliance |
| AGY | No stable machine-readable actual-model receipt established | No stable quota/cost receipt established | Manual transcript/artifact evidence only |
| OpenRouter | Router metadata can expose model/provider attempts and request routing | Normalized usage and observability features | Useful fallback provenance, but not a provider-attested trust oracle |
| Mechanical tools | Binary/version/argv/cwd/stdout/stderr/exit status are directly recordable | Caller-defined | Strongest deterministic receipt surface |

## Deprecation and version risk

| Tool | Risk | Required control |
|---|---|---|
| Claude Code | Rapidly evolving settings and sandbox controls | Pin version and record effective settings plus `claude --version` |
| Codex CLI | Compatibility flags and config syntax can change; dangerous bypasses remain available | Pin version, ban unsafe flags, validate generated config against current official reference |
| Gemini CLI | Plan mode and structured-output behavior have evolved rapidly | Pin version; reject undocumented schema assumptions |
| OpenCode | Permissions/configuration surfaces are moving quickly | Pin version; use current permission model; capture server OpenAPI schema |
| Grok Build | Product and docs are fast-moving; local help and current web docs may differ | Treat local `--help` as host truth; preserve contradictions; require adapter conformance tests |
| AGY | Documentation maturity and unattended contract remain weak | No unattended adapter until official contract and local conformance evidence exist |
| OpenRouter | Provider/model inventory and aliases can change independently | Pin model and provider; disable fallback where provenance matters; record router metadata |
| Mechanical tools | Script assumptions and dependency behavior can mutate over time | Pin binaries, prohibit dependency-installing commands in offline lane, capture hashes and exits |

## Tool-specific findings

### Claude Code

`CLAIMED` Official documentation supports programmatic/headless use, configuration relocation, sandboxed shell execution, permission rules, and extension surfaces.

`OBSERVED` The installed local version was `Claude Code 2.1.207`; static help exposed print, JSON/schema, model, safe-mode, settings-source, MCP, plugin/skill/subagent, and no-tools controls.

`UNKNOWN` Subscription/OAuth versus API billing, live network posture, actual model identity, and complete inherited-configuration isolation were not tested.

**Adapter posture:** `BLOCKED` for unattended use. Candidate for automation after DR-01 authorization findings and a version-pinned local containment conformance probe.

### Codex CLI

`CLAIMED` Official documentation exposes `codex exec`, JSONL events, final-output JSON Schema validation, model/reasoning controls, sandbox modes, approval policies, config-root relocation, ephemeral sessions, resume behavior, CI guidance, and enterprise analytics.

`OBSERVED` The installed local version was `codex-cli 0.144.1`; root help exposed `exec`, model, sandbox, config, and profile controls.

`UNKNOWN` The local auth route, plan versus API billing, actual model identity, and full MCP/hooks/plugins/skills disablement were not proven.

**Adapter posture:** `BLOCKED` for unattended use, but the strongest first-party automation candidate once authentication and local conformance are established.

### Gemini CLI

`CLAIMED` Official documentation supports headless prompting and JSON/streaming JSON output, model selection, sandboxing, approval modes, tool/MCP restrictions, session controls, extensions/skills administration, and telemetry configuration.

`OBSERVED` The installed local version was `0.46.0`; static help exposed prompt, JSON output, model, sandbox, plan-mode, MCP-name, and extension surfaces.

`UNKNOWN` The live auth/billing route, complete containment, and user-supplied strict final schema remain unproven.

**Adapter posture:** `BLOCKED` pending auth and containment proof. Use a proof normalizer against the documented native envelope if later authorized.

### OpenCode

`CLAIMED` Official documentation provides a headless HTTP server with OpenAPI and explicit agent permissions.

`OBSERVED` The installed local version was `1.17.13`; static help exposed `run`, `--model provider/model`, and `--pure`.

`UNKNOWN` The configured provider, plan/API authentication, provider fallback, actual serving provider/model, config isolation, and stable final-output proof schema.

**Adapter posture:** `BLOCKED` and `RESEARCH_ONLY` for the first release. Do not promote branding or configured model strings into provider identity evidence.

### Grok Build

`OBSERVED` The installed local version was `grok 0.2.99`; static help exposed headless single-run, JSON/schema output, model selection, no-subagents, plan permission mode, and web-search disablement.

`CLAIMED` Current xAI documentation describes headless and machine-readable execution with usage/cost telemetry.

`CONFLICTING` Current web documentation may describe a newer product surface than the installed version. The research must not overwrite local help with newer marketing or docs.

**Adapter posture:** `BLOCKED`. May become operator-triggered or automated only after version-matched official documentation, auth authorization, config isolation, and complete containment conformance are proven.

### AGY / Google Antigravity

`OBSERVED` The installed local version was `1.1.1`; static help exposed `--print`, `--model`, `--mode plan`, `--sandbox`, and `--print-timeout`.

`UNKNOWN` Stable structured output, deterministic exit contract, unattended credential renewal, extension/MCP/tool disablement, shell/file/network denial, and actual model evidence.

`CONFLICTING` The reviewed official public material was primarily interactive and codelab-oriented, which does not erase the locally observed print flag but also does not prove a supported unattended audit contract.

**Adapter posture:** `RESEARCH_ONLY` or operator-supervised manual receipt path.

### OpenRouter

`CLAIMED` OpenRouter exposes strict structured outputs for compatible routes, explicit model/provider routing, fallback controls, data-collection selection, usage, request metadata, and observability integrations.

`OBSERVED` No dedicated local CLI, key read, or API call occurred. Local policy classifies OpenRouter as static-only API fallback.

`UNKNOWN` Future provider retention, ZDR applicability, exact route cost, and serving identity remain route-specific.

**Adapter posture:** `API_FALLBACK` only after DR-05 route-profile approval. Never use as local containment, automatic trust authority, or proof of plan-backed identity.

### Deterministic mechanical tools

`OBSERVED` The accepted local inventory defines read-only repository identity, JSON/schema validation, proof-bundle validation, diff hygiene, and static contract inspection. Some common tooling, including pre-commit and prior `uv` validation, can mutate or install dependencies and is excluded from the offline lane.

**Adapter posture:** `AUTOMATED`. Keep it first-class, narrow, offline, version-pinned, and explicit about each validator’s authority limit.

## Contradictions

1. **Grok Build local help versus current public documentation**  
   `CONFLICTING` The installed version exposes schema and containment-related flags, while the current web material may represent a newer release. Carry both. Resolve with a version-matched official reference and a static adapter conformance check.

2. **AGY local `--print` versus public documentation posture**  
   `CONFLICTING` A local print flag exists, but the reviewed official sources did not establish a stable unattended machine-readable proof contract. Headless possibility is not equivalent to an automation guarantee.

3. **OpenCode configured model versus actual provider identity**  
   `CONFLICTING` A configured `provider/model` name can be visible while actual fallback or upstream behavior remains unverified. Do not claim independence from config alone.

4. **Vendor clean-room claims versus host proof requirements**  
   `CONFLICTING` Vendor documentation can describe sandbox/config controls while the local packet requires proof of every prohibited surface for the installed version. Documentation extends but does not replace local conformance evidence.

## Unknowns

- Exact local authentication and billing route for every model-capable CLI.
- Provider-attested actual model identity for every live route.
- Complete inherited-configuration isolation for Claude Code, Codex, Gemini CLI, OpenCode, Grok Build, and AGY.
- Stable, versioned exit-code contracts across model tools.
- User-supplied strict final-output schema support in Gemini CLI, OpenCode, and AGY.
- Deterministic OpenCode provider fallback disablement and actual upstream identity evidence.
- Version-matched Grok Build containment documentation for installed `0.2.99`.
- Official AGY unattended receipt/export contract.
- Route-specific OpenRouter retention and ZDR enforcement.

## Activities not run

- No provider login or account inspection.
- No credential, token, keychain, cookie, or session-file inspection.
- No model invocation.
- No API call, including OpenRouter.
- No benchmark or schema-conformance execution against live tools.
- No repository mutation or GitHub mutation.
- No final architecture synthesis.

## Recommendations

1. `PROPOSED` Keep mechanical validation enabled as the only current automatic lane.
2. `BLOCKED` Do not promote any model-capable CLI to unattended execution until DR-01 authorizes the intended authentication mode and a version-pinned local conformance probe proves all required disablements.
3. `PROPOSED` Prioritize Codex CLI and Claude Code for the first adapter conformance work because they expose the clearest structured-output and containment surfaces.
4. `PROPOSED` Treat Gemini CLI as a native-envelope adapter, not a custom-schema adapter, unless current official documentation and the installed version prove otherwise.
5. `DEFERRED` Keep OpenCode out of independence-critical routes until actual upstream provider/model and fallback behavior can be captured.
6. `DEFERRED` Keep Grok Build operator-triggered until installed-version containment and auth isolation are proven.
7. `REJECTED` Do not build an AGY unattended adapter from terminal or UI scraping.
8. `PROPOSED` Require OpenRouter route profiles to pin model/provider, disable unapproved fallback, enforce data policy and price caps, and record router metadata.
9. `PROPOSED` Every adapter receipt should capture tool version, requested model, observed/displayed model, provider evidence, effective config, prohibited-surface checks, network policy, stdout/stderr, exit code, usage metadata, and artifact hashes.

## Synthesis implications

- Authentication authorization and automation capability are separate gates. A beautiful JSON flag does not bless the credential path.
- Vendor documentation must not override the static host record. Local installed versions and captured help remain authoritative for the inspected host.
- `UNKNOWN`, `CLAIMED`, and `CONFLICTING` containment states must remain non-executable.
- Mechanical validation is a first-class route, not decorative parsley around an LLM verdict.
- OpenRouter may provide fallback provenance, but it cannot prove local containment or convert routed model metadata into provider attestation.
- Environment failure must fail closed and must not silently promote to a stronger or more expensive model.

## Source ledger

Access date for all web sources: **2026-07-13**.

| Source ID | Title / publisher | Class | Questions supported |
|---|---|---|---|
| S-CLAUDE-HEADLESS | Claude Code programmatic/headless documentation, Anthropic | OFFICIAL_DOCUMENTATION | Headless invocation, output modes, programmatic surface |
| S-CLAUDE-CONFIG | Claude Code settings, environment, sandbox, authentication and security docs, Anthropic | OFFICIAL_DOCUMENTATION / OFFICIAL_SECURITY | Config relocation, permissions, sandbox, credential storage, extension controls |
| S-CODEX-NONINTERACTIVE | Codex non-interactive mode, OpenAI | OFFICIAL_DOCUMENTATION | `codex exec`, JSONL, output schema, CI usage |
| S-CODEX-CLI-CONFIG | Codex CLI/config/auth/security references, OpenAI | OFFICIAL_DOCUMENTATION / OFFICIAL_SECURITY | Model/reasoning, sandbox, approvals, config home, sessions, auth storage |
| S-GEMINI-HEADLESS | Gemini CLI headless and automation docs, Google | OFFICIAL_DOCUMENTATION / OFFICIAL_REPOSITORY | Prompt mode, JSON/stream JSON, session output |
| S-GEMINI-CONFIG | Gemini CLI configuration and command reference, Google | OFFICIAL_DOCUMENTATION | Sandbox, approvals, tools, MCP, extensions, telemetry |
| S-OPENCODE-SERVER | OpenCode server/OpenAPI documentation | OFFICIAL_DOCUMENTATION | Headless server, OpenAPI, events |
| S-OPENCODE-PERMS | OpenCode agents, permissions, providers and tools docs | OFFICIAL_DOCUMENTATION | Tool denial, model/provider config, credential location |
| S-XAI-BUILD | Grok Build overview, CLI reference, enterprise docs and changelog, xAI | OFFICIAL_DOCUMENTATION | Headless, output, sessions, inspection, telemetry, enterprise controls |
| S-AGY-CODELABS | Google Antigravity / AGY official codelabs | OFFICIAL_DOCUMENTATION | Interactive/TUI workflows, skills/plugins, current documentation posture |
| S-OPENROUTER-API | OpenRouter API, structured output, routing, metadata and privacy docs | OFFICIAL_DOCUMENTATION | Schema output, provider routing, fallbacks, telemetry, data controls |
| L-CAP-MATRIX | `AUDITOR_CAPABILITY_MATRIX.json` | LOCAL OBSERVED EVIDENCE | Installed versions and static controls |
| L-NETWORK | `NETWORK_AND_CONTAINMENT_OBSERVATIONS.md` | LOCAL OBSERVED EVIDENCE | No live calls; aggregate CLI network defect; containment limits |
| L-ROUTING | `ROUTING_CONSTRAINTS.md` | LOCAL OBSERVED POLICY | Non-executable unknowns and fallback boundary |
| L-MECHANICAL | `MECHANICAL_VALIDATION_INVENTORY.json` | LOCAL OBSERVED EVIDENCE | Mechanical validator surfaces and authority limits |

## Final disposition

`COMPLETE_WITH_UNKNOWNS`

This track answers the automation and containment research questions sufficiently to rank adapter research priority and preserve fail-closed boundaries. It does **not** authorize unattended execution for any model-capable tool. The accepted local evidence still records model invocations as `NOT_RUN`, actual model identity as `UNKNOWN`, and plan-backed authentication as unproven.
