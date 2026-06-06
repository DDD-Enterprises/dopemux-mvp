---
id: MODEL_ROUTING_USAGE
title: How to Use the Model Routing Policy
type: how-to
status: draft
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-06'
prelude: Operator usage guide — how to apply the stage-based model routing policy in Claude Code, Codex, Copilot custom agents, and AGY/Gemini audit flows, with example Task Packet and proof blocks.
tags: [governance, model-routing, how-to, operators]
---
# How to Use the Model Routing Policy

Reference: [`config/ai/model-routing.policy.yaml`](../../03-reference/governance/model-routing.md)

This guide explains how operators and agents apply the stage-based routing policy
in each supported tool. The policy is **advisory governance** — it tells you which
model tier to select, not which exact model string to use (those require
`VERIFY_WITH_VENDOR_DOCS` unless already established in repo config).

> All claims in this guide are **PROPOSED** unless marked OBSERVED. Model ids and
> tier names that are not in repo config are marked `VERIFY_WITH_VENDOR_DOCS`.

---

## 1. How to use the policy in Claude Code

Claude Code supports explicit model selection via `--model` and the `opusplan`
mode (`Opus plans, Sonnet implements`).

**Stage mapping (PROPOSED intent; exact model strings VERIFY_WITH_VENDOR_DOCS):**

| Stage | Recommended approach |
|-------|---------------------|
| `cheap_read` | Default model or Haiku-equivalent; avoid Opus-tier for pure reads |
| `investigation` | Default or cheap model; escalate to planner if escalation triggers hit |
| `planner_strong` | `opusplan` mode (`--model opusplan`) or equivalent Opus-tier invocation |
| `implementer_standard` | Sonnet-tier; constrained by approved Task Packet allowlist |
| `judge_strong` | Opus-tier for synthesis and readiness judgment |
| `self_audit` | Opus-tier; must be run after implementation, before final proof |

**Usage pattern:**

```bash
# Planning stage — use opusplan mode or specify a strong model
claude --model opusplan --effort high

# Implementation stage — Sonnet (default or explicit)
# Constrained by the active Task Packet file allowlist.

# Self-audit — run Opus explicitly after implementation
# Capture auditor_tool, auditor_model, exit_code, and verdict in PROOF.json
```

**Recording proof (required):**
After each substantive run, capture `actual_tool: claude_code`, `actual_model`,
`provider: anthropic`, `stage_slot`, `fallback_used`, and `fallback_reason` in the
Task Packet's `PROOF.json`. If `opusplan` dispatched to Sonnet for implementation,
record both the planning model (Opus) and the implementation model (Sonnet).

---

## 2. How to use the policy in Codex

Codex CLI selects models via flags (exact flag names and accepted model strings
require `VERIFY_WITH_VENDOR_DOCS`).

**Stage mapping (tier intent; model strings VERIFY_WITH_VENDOR_DOCS):**

| Stage | Tier intent | OBSERVED ids (RTE routing — not confirmed for Codex CLI) |
|-------|-------------|----------------------------------------------------------|
| `cheap_read` | cheap_fast | `gpt-5.4-mini` (OBSERVED in RTE) |
| `investigation` | cheap_fast | `gpt-5.4-mini` |
| `planner_strong` | strong_reasoning | `gpt-5.5` (OBSERVED in config/pricing.yaml) |
| `implementer_standard` | coding_balanced | `gpt-5.3-codex` (OBSERVED in RTE) |
| `judge_strong` | strong_reasoning | `gpt-5.5` |
| `self_audit` | audit_strong | `gpt-5.5` or equivalent |

> **Important**: The model ids in the table above are OBSERVED in `model_map_v2_tp008.yaml`,
> `tests/test_routing_config.py`, and `config/pricing.yaml` as RTE extraction lane
> selectors. Whether they are accepted as Codex CLI `--model` arguments requires
> `VERIFY_WITH_VENDOR_DOCS`. Do not assume portability.

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
| `cheap_read` / `investigation` | `dopemux-reader.agent.md` | read, search | VERIFY_WITH_VENDOR_DOCS |
| `planner_strong` | `dopemux-planner.agent.md` | read, search | VERIFY_WITH_VENDOR_DOCS |
| `implementer_standard` | `dopemux-implementer.agent.md` | read, edit, search | Claude Sonnet 4.5 (OBSERVED) |
| `judge_strong` / `self_audit` | `dopemux-auditor.agent.md` | read, search | VERIFY_WITH_VENDOR_DOCS |

**How tool scope enforces stage boundaries:**
- Reader, planner, and auditor agents have `tools: ['read', 'search']` — they
  physically cannot edit files.
- The implementer has `tools: ['read', 'edit', 'search']` — it can edit, but is
  bound to the Task Packet file allowlist.

**Replacing VERIFY_WITH_VENDOR_DOCS model values:**
To activate per-agent model tiering, an operator must:
1. Consult VS Code Copilot documentation for currently supported `model:` values.
2. Replace `VERIFY_WITH_VENDOR_DOCS` in the agent frontmatter with a supported
   cheap model (reader/planner) and a supported strong model (auditor).
3. Verify the replacement does not break existing Copilot agent invocation.

Until replaced, `VERIFY_WITH_VENDOR_DOCS` is a sentinel — Copilot will use its
default model, and cheap/strong differentiation relies on tool scope alone.

**Handoffs:**
The reader agent includes handoffs to `dopemux-planner` (escalate for planning) and
`dopemux-auditor` (request audit). The implementer includes a handoff to
`dopemux-auditor` for the independent audit step before proof is filed.

---

## 4. How to use the policy in AGY / Gemini audit flows

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

## 5. Example Task Packet model_routing block

Include this section in every Task Packet before implementation begins.
Operators fill in the actual model/tier used per stage; entries that are not yet
determined use `VERIFY_WITH_VENDOR_DOCS` or a tier name.

```markdown
## Model Routing
- cheap_read: VERIFY_WITH_VENDOR_DOCS
- investigation: VERIFY_WITH_VENDOR_DOCS
- planner_strong: opusplan (claude_code) | VERIFY_WITH_VENDOR_DOCS
- implementer_standard: claude_code/sonnet | codex/coding_balanced | copilot/dopemux-implementer.agent.md
- judge_strong: VERIFY_WITH_VENDOR_DOCS
- self_audit: claude_code/opus | VERIFY_WITH_VENDOR_DOCS
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

## 6. Example proof block

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
    "auditor_model": "claude-opus-4",
    "invocation": "self-audit inside Claude Code after edits",
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
