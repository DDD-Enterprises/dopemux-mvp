# DR-03: Tool Automation and Containment

## Objective

Determine the current officially supported automation, structured-output, model-selection,
configuration-isolation, and containment surfaces for each audit tool.

## Targets

- Claude Code
- Codex CLI
- Gemini CLI
- OpenCode
- Grok Build
- AGY / Google Antigravity
- OpenRouter client/API
- deterministic mechanical tools

## Research dimensions

For each tool research:

- supported non-interactive/headless command;
- machine-readable output modes;
- strict JSON or schema-output support;
- model selection;
- reasoning/effort selection;
- timeout control;
- exit-code contract;
- session persistence;
- resume behavior;
- configuration directory override;
- clean-room or bare mode;
- repository-instruction loading;
- MCP disablement;
- hooks disablement;
- plugins/extensions disablement;
- skills/memory disablement;
- subagent disablement;
- shell disablement;
- file-write disablement;
- network restriction;
- telemetry controls;
- credential storage and isolation;
- model identity evidence;
- usage, quota, and cost telemetry;
- official CI guidance;
- support status and deprecations.

## Questions unique to OpenCode

- Which providers support plan authentication?
- Can the upstream provider and actual model be observed?
- Can OpenCode disable tools and provider fallback deterministically?
- Are structured event outputs stable enough for a proof normalizer?

## Questions unique to Grok Build and AGY

- Is an official unattended interface available?
- Can output be exported in a machine-readable way?
- Are they suitable only for operator-supervised manual audit receipts?
- What safe evidence can be collected without UI scripting?

## Required deliverables

- One capability table with exact current flags or official control surfaces.
- One containment-gap table.
- One identity/telemetry table.
- One deprecation/version-risk table.
- Recommended adapter posture for each tool:
  - automated;
  - operator-triggered;
  - manual app;
  - unsupported;
  - research-only.
