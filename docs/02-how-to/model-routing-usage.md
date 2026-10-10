---
id: MODEL_ROUTING_USAGE
title: How to Use the Model Routing Policy
type: how-to
status: draft
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-06'
prelude: "Operator usage guide \u2014 how to apply the stage-based model routing policy\
  \ in Claude Code, Codex, Copilot custom agents, and AGY/Gemini audit flows, with\
  \ example Task Packet and proof blocks."
tags:
- governance
- model-routing
- how-to
- operators
last_review: '2026-06-06'
next_review: '2026-09-04'
---
# How to Use the Model Routing Policy

Reference: [`config/ai/model-routing.policy.yaml`](../03-reference/governance/model-routing.md)

This guide explains how operators and agents apply the stage-based routing policy
in each supported tool. The policy is **advisory governance** — it tells you which
model tier to select, not which exact model string to use (those require
`VERIFY_WITH_VENDOR_DOCS` unless already established in repo config).

> All claims in this guide are **PROPOSED** unless marked OBSERVED. Model ids and
> tier names that are not in repo config are marked `VERIFY_WITH_VENDOR_DOCS`.

---

## Cost-first defaults and bounded delegation

Always choose cheapest adequate qualified model and lowest sufficient supported effort; deterministic shell/schema/hash/inventory tasks use no model. Explicit user/packet model, runner, same-route, approval, and no-fallback restrictions prevail. Strong supervisor delegates suitable bounded work with file/responsibility ownership, validation, and stop conditions; supervisor retains decisions, synthesis, escalation, and finality.

Repo Codex supervisor declares `gpt-6.1-sol` high. `[agents]` defaults declare `gpt-6-luna` medium. Custom role `model` / `model_reasoning_effort` override defaults and explicit spawn selection. These are configuration declarations; instructions still guide dispatch and actual identity/availability remain `UNKNOWN` without evidence. Fresh or bounded-history collaboration children accept explicit model/effort; full-history forks inherit supervisor and reject overrides. Report missing cheaper delegation controls instead of silently inheriting expensive model.

| Bounded task / role | Declared route | Effort / boundary |
|---|---|---|
| Evidence / research: dmx-explorer, researcher | gpt-6-luna | medium; read-only |
| Housekeeping / coordination: dmx-housekeeper, project-manager | gpt-6-luna | low; read-only |
| Allowlisted implementation: dmx-worker, developer | gpt-6.1-sol | medium; packet-scoped |
| Design: architect / advisory review: dmx-reviewer | gpt-6.1-sol | high; read-only; Codex never formal auditor |
| Claude architect / developer | claude-sonnet-5-5 | lowest sufficient supported effort; existing tool scopes |
| Claude project-manager / researcher | claude-haiku-4-5 | supported controls only; read-only |

GPT-6 Luna, GPT-6.1 Sol, Claude Sonnet 5.5 (`claude-sonnet-5-5`), and Gemini 3.8 Flash (`gemini-3.8-flash`) are candidates, not global numeric price ranking. Gemini Flash requires actual client/account qualification. Claude Opus 5.5 (`claude-opus-5-5`) is escalation only. Current prices, capability, availability, and actual identity remain `UNKNOWN` when unproven; selector syntax does not prove account access.

Cheap-model failure, insufficient confidence, contract ambiguity, or security/replay risk returns to supervisor. Record reason, narrow stronger slice, and bound retry under packet/evidence-economy limits. No hidden upgrade, fallback, retry, or provider substitution; stop when binding restrictions prohibit escalation. L0=0 model calls; L1≤1 implementer; L2/L3=1 implementer + one final independent frozen-head audit. Record budget exceptions; no intermediate audits or re-audits of unchanged proof-only content.

Other runners consume AGENTS.md §5 via loaded instructions and pin documented per-agent/per-invocation model and supported effort controls. OpenCode PAL is optional or packet-required within budget. Copilot accepted selectors remain unchanged. Report unavailable delegation/controls; never invent runtime keys. YAML remains advisory, not automatic enforcement. Formal audit candidate Sonnet 5.5 uses schema-compatible `sonnet` alias separately from actual ID evidence; Codex review cannot satisfy formal embedded audit.

Examples: hashes/schema checks → deterministic tools; bounded status/lookup → qualified Luna/Haiku role; approved implementation → qualified Sol medium/Sonnet; failed cheap lookup → supervisor narrows stronger investigation with reason and bounded retry. Config parsing verifies declarations, not account execution.

Official sources: [OpenAI subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [Claude Code subagents](https://code.claude.com/docs/en/sub-agents), [Anthropic models](https://platform.claude.com/docs/en/models/overview), [Google Gemini models](https://ai.google.dev/gemini-api/docs/models).

---

## 1. How to use the policy in Claude Code

Claude Code supports explicit model selection via `--model` and the `opusplan`
mode (`Opus plans, Sonnet implements`).

**Stage mapping (PROPOSED intent; exact model strings VERIFY_WITH_VENDOR_DOCS):**

| Stage | Recommended approach |
|-------|---------------------|
| `cheap_read` | Default model or Haiku-equivalent; avoid Opus-tier for pure reads |
| `investigation` | Default or cheap model; escalate to planner if escalation triggers hit |
| `planner_strong` | architect: qualified `claude-sonnet-5-5`; Opus escalation only |
| `implementer_standard` | Sonnet-tier; constrained by approved Task Packet allowlist |
| `judge_strong` | Supervisor synthesis with cheapest adequate qualified route |
| `self_audit` | One independent final Sonnet candidate audit for L2/L3; Opus escalation only |

**Usage pattern:**

```bash
# Planning candidate — qualify client/account; lowest sufficient supported effort
claude --model claude-sonnet-5-5

# Implementation stage — Sonnet (default or explicit)
# Constrained by the active Task Packet file allowlist.

# L2/L3 — one independent final audit after frozen content head
# Capture auditor_tool, auditor_model, exit_code, and verdict in PROOF.json
```

**Recording proof (required):**
After each substantive run, capture `actual_tool: claude_code`, `actual_model`,
`provider: anthropic`, `stage_slot`, `fallback_used`, and `fallback_reason` in the
Task Packet's `PROOF.json`. If `opusplan` dispatched to Sonnet for implementation,
record both the planning model (Opus) and the implementation model (Sonnet).

---

## 2. How to use the policy in Codex

Codex project defaults and role pins are declared in `.codex/config.toml` and `.codex/agents/*.toml`; current mapping appears above. These do not establish runtime identity or account availability.

| Stage | Project role / model | Boundary |
|-------|----------------------|----------|
| `cheap_read` | dmx-explorer: gpt-6-luna medium | Read-only |
| `investigation` | researcher: gpt-6-luna medium | Read-only |
| `planner_strong` | architect: gpt-6.1-sol high | Read-only design |
| `implementer_standard` | developer: gpt-6.1-sol medium | Approved packet allowlist |
| `judge_strong` | dmx-reviewer: gpt-6.1-sol high | Advisory review |
| `self_audit` | FORBIDDEN as formal embedded auditor | Use authorized independent route |

**Recording proof:**
Capture `actual_tool: codex`, `actual_model`, `provider: openai`, and `stage_slot`
in the Task Packet's `PROOF.json`.

---

## 3. How to use the policy in Copilot custom agents

This repo provides four `.github/agents/*.agent.md` custom agents that map to the
stage slots. These are `OBSERVED` in the repo.

**Agent-to-stage mapping:**

| Stage | Agent file | Tools | Model |
|-------|-----------|-------|-------|
| `cheap_read` / `investigation` | `dopemux-reader.agent.md` | read, search | Claude Sonnet 4.5 (OBSERVED) |
| `planner_strong` | `dopemux-planner.agent.md` | read, search | Claude Sonnet 4.5 (OBSERVED) |
| `implementer_standard` | `dopemux-implementer.agent.md` | read, edit, search | Claude Sonnet 4.5 (OBSERVED) |
| `judge_strong` / `self_audit` | `dopemux-auditor.agent.md` | read, search | Claude Sonnet 4.5 (OBSERVED) |

**How tool scope enforces stage boundaries:**
- Reader, planner, and auditor agents have `tools: ['read', 'search']` — they
  physically cannot edit files.
- The implementer has `tools: ['read', 'edit', 'search']` — it can edit, but is
  bound to the Task Packet file allowlist.

**Pinned baseline (OBSERVED):**
Reader, planner, implementer, and auditor all pin `model: 'Claude Sonnet 4.5'`.
Cheap/strong separation is therefore enforced primarily by tool scope
(`read/search` vs. `read/edit/search`), not by per-agent model tiering.

If you want model-tier separation later:
1. Verify currently supported Copilot `model:` values from vendor docs.
2. Update the targeted `.github/agents/*.agent.md` frontmatter values.
3. Verify each updated agent can still be invoked from VS Code.

**Handoffs:**
The reader agent includes handoffs to `dopemux-planner` (escalate for planning) and
`dopemux-auditor` (request audit). The implementer includes a handoff to
`dopemux-auditor` for the independent audit step before proof is filed.

---

## 4. How to use the policy in OpenCode

OpenCode in this repo is configured by `opencode.jsonc` and two PAL subagents in
`.opencode/agents/`.

**Stage mapping (repo baseline):**

| Stage | Route |
|-------|-------|
| `cheap_read` / `investigation` | Main OpenCode session model (operator-configured, `VERIFY_WITH_VENDOR_DOCS`) |
| `planner_strong` | `.opencode/agents/pal-planner.md` |
| `implementer_standard` | Main OpenCode session model with `AGENTS.md` + Task Packet allowlist discipline |
| `judge_strong` / `self_audit` | `.opencode/agents/pal-reviewer.md` |

**Usage pattern:**
1. Perform read-only inventory in the main OpenCode session.
2. Delegate non-trivial planning to `pal-planner`.
3. Implement in the main session under packet allowlist constraints.
4. Optional advisory `pal-reviewer` within budget; deterministic precommit required. L2/L3 require one independent final frozen-head audit, with qualified formal auditor route.

---

## 5. How to use the policy in AGY / Gemini audit flows

AGY (Antigravity) and Gemini CLI route through Google's Gemini model family.
All model selector strings require `VERIFY_WITH_VENDOR_DOCS`.

**Stage mapping (tier intent; model strings VERIFY_WITH_VENDOR_DOCS):**

| Stage | Tier intent |
|-------|-------------|
| `cheap_read` | Flash-equivalent (fast, cheap) |
| `investigation` | Flash-equivalent |
| `planner_strong` | Pro-high-equivalent (thinking/reasoning enabled) |
| `implementer_standard` | Coding-balanced (or Claude Sonnet in-AGY if available) |
| `judge_strong` | Pro-high-equivalent |
| `self_audit` | Pro-high-equivalent or a separate audit-capable model |

**Embedded audit in AGY flows:**
When AGY performs an embedded audit, record:

```json
{
  "auditor_tool": "agy",
  "auditor_model": "VERIFY_WITH_VENDOR_DOCS",
  "invocation": "AGY audit pass after implementation",
  "exit_code": 0,
  "auditor_verdict": "PASS | PASS_WITH_RISKS | FAIL | NEEDS_SUPERVISOR | SKIPPED",
  "auditor_findings": [],
  "fixes_applied_from_audit": [],
  "remaining_risks": [],
  "skip_reason": null
}
```

The `auditor_verdict` field in `PROOF.json` aligns with the verdict enum in
`schemas/proof/embedded_audit.schema.json` (`status` field).

---

## 6. Example Task Packet model_routing block

Include this section in every Task Packet before implementation begins.
Operators fill in the actual model/tier used per stage; entries that are not yet
determined use `VERIFY_WITH_VENDOR_DOCS` or a tier name.

```markdown
## Model Routing
- cheap_read: VERIFY_WITH_VENDOR_DOCS
- investigation: VERIFY_WITH_VENDOR_DOCS
- planner_strong: claude_code/architect | codex/architect | VERIFY_WITH_VENDOR_DOCS
- implementer_standard: claude_code/sonnet | codex/coding_balanced | copilot/dopemux-implementer.agent.md
- judge_strong: VERIFY_WITH_VENDOR_DOCS
- self_audit: qualified independent claude_code/sonnet for L2/L3 | packet-required route
Escalate to strong model if:
- authority boundary unclear
- security/auth/secrets/CI touched
- runtime contradicts docs
- diff exceeds allowlist
- proof stale or incomplete
- reviewer/auditor unknown
- confidence below required gate
```

---

## 7. Example proof block

This is the structure required in `proof/<TP-ID>/PROOF.json` for a substantive
run. Fields marked `actual_*` capture what was used, not just what was intended.

```json
{
  "tp_id": "TP-DMX-EXAMPLE-001",
  "status": "IMPLEMENTATION_COMPLETE",
  "repo": "dopemux-mvp",
  "branch": "claude/feature-branch",
  "git_status_before": " M some/file.py\n",
  "git_status_after": " M some/file.py\n?? proof/TP-DMX-EXAMPLE-001/\n",
  "files_changed": [
    "src/module/file.py",
    "tests/test_file.py",
    "proof/TP-DMX-EXAMPLE-001/PROOF.json"
  ],
  "commands": [
    {
      "command": "pytest tests/test_file.py -v",
      "exit_code": 0,
      "stdout_summary": "5 passed in 0.12s",
      "stderr_summary": ""
    }
  ],
  "validation": {
    "required_files_present": true,
    "yaml_valid": true,
    "proof_json_valid": true,
    "diff_reviewed": true
  },
  "embedded_audit": {
    "auditor_tool": "claude_code",
    "auditor_model": "sonnet",
    "invocation": "independent final Claude Code audit on frozen content head",
    "exit_code": 0,
    "auditor_verdict": "PASS_WITH_RISKS",
    "auditor_findings": [
      "F1: <description of finding>"
    ],
    "fixes_applied_from_audit": [
      "Fixed F1 before filing proof"
    ],
    "remaining_risks": [
      "R1: <description of residual risk>"
    ],
    "skip_reason": null
  },
  "remaining_risks": [
    "R1: <description of residual risk>"
  ],
  "commit": {
    "created": true,
    "sha": "abc1234",
    "message": "Add feature X per TP-DMX-EXAMPLE-001"
  }
}
```

**Key rules for proof blocks:**
- `actual_model` must reflect the model that actually ran, not just the one requested.
- `auditor_verdict` must be one of: `PASS`, `PASS_WITH_RISKS`, `FAIL`,
  `NEEDS_SUPERVISOR`, `SKIPPED`.
- If the auditor is skipped, `skip_reason` is required; do not silently omit it.
- `commit.sha` is filled after the commit is made; it is `null` before commit.
