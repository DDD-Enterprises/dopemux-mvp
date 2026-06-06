---
id: MODEL_ROUTING_POLICY
title: Model Routing Policy
type: reference
status: draft
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-06'
last_review: '2026-06-06'
next_review: '2026-09-06'
prelude: Repo-governed stage-routing policy for AI dev tools (Codex, Copilot, Claude Code, AGY, Gemini CLI, xAI, Moonshot, OpenRouter) — cheap reads, strong planning, scoped implementation, independent audit.
tags: [governance, model-routing, agents, proof]
---
# Model Routing Policy

Machine-readable source of truth: [`config/ai/model-routing.policy.yaml`](../../../config/ai/model-routing.policy.yaml).
This document explains it for humans. The policy is **advisory governance**, not a
runtime router — it tells each tool which *stage* and model tier to use; it
does not dispatch model calls.

> **STATUS labels** used below: **OBSERVED** = verified in repo runtime/config;
> **PROPOSED** = governance intent, operator-tunable, not yet wired; **UNKNOWN** =
> unresolved and preserved as such; **VERIFY_WITH_VENDOR_DOCS** = asserted from
> memory, not from repo evidence — do not rely on these without checking vendor docs.

---

## 1. Purpose

This policy assigns a **stage slot** (cheap_read → investigation → planner_strong →
implementer_standard → judge_strong → self_audit) and an appropriate model tier to
each AI development tool (Codex, Copilot, Claude Code, AGY, Gemini CLI, xAI,
Moonshot, OpenRouter) operating on this repo.

The goal is to ensure cheap models gather facts but never make architecture or
security decisions, and that implementation and judgment always operate under approved
task-packet constraints with proof captured.

---

## 2. Authority status

This policy is **PROPOSED governance** with `authority: advisory_until_runtime_wiring_verified`.
It is a third, separate concern from the two OBSERVED runtime systems:

| System | Concern | Authority |
|--------|---------|-----------|
| `templates/routing.yaml` + `src/dopemux/routing_config.py` + `dopemux routing` | LiteLLM provider-**proxy** plumbing (which endpoint a request hits) | OBSERVED runtime |
| `model_map_v2_tp008.yaml` + RTE cost profiles + `config/pricing.yaml` | Repo-Truth-Extractor extraction **lane → model** assignment | OBSERVED runtime |
| **This policy** (`config/ai/model-routing.policy.yaml`) | Development-workflow **agent stage** routing | PROPOSED governance |

If a runtime path disagrees with this policy, the runtime wins and the conflict is
preserved, not laundered (repo truth beats docs).

---

## 3. Stage routing table

| Stage | Purpose | May edit? | May decide authority? |
|-------|---------|-----------|----------------------|
| `cheap_read` | read-only investigation, grep, inventory, status, housekeeping | no | no |
| `investigation` | bounded subsystem understanding; starts cheap, escalates to planner_strong | no | no |
| `planner_strong` | architecture, task packet design, validation strategy, rollback strategy | no | no |
| `implementer_standard` | scoped edits from an **approved packet** with file allowlist | **yes** | no |
| `judge_strong` | synthesis, readiness decision, proof review, merge-risk assessment | no | no |
| `self_audit` | independent audit before final handoff; formal verdict required | no | no |

Verdict values for `self_audit`: `PASS` · `PASS_WITH_RISKS` · `FAIL` ·
`NEEDS_SUPERVISOR` · `SKIPPED`. These align with the canonical machine schema at
[`schemas/proof/embedded_audit.schema.json`](../../../schemas/proof/embedded_audit.schema.json).

---

## 4. Provider routing table

| Provider | cheap_read | planner_strong | implementer_standard | judge_strong / self_audit |
|----------|-----------|---------------|---------------------|--------------------------|
| Codex | VERIFY_WITH_VENDOR_DOCS (cheap_fast tier) | VERIFY_WITH_VENDOR_DOCS (strong_reasoning) | VERIFY_WITH_VENDOR_DOCS (coding_balanced) | VERIFY_WITH_VENDOR_DOCS (strong_reasoning / audit_strong) |
| Copilot | `dopemux-reader.agent.md` | `dopemux-planner.agent.md` | `dopemux-implementer.agent.md` | `dopemux-auditor.agent.md` |
| Claude Code | VERIFY_WITH_VENDOR_DOCS (Haiku / Sonnet-low) | VERIFY_WITH_VENDOR_DOCS (opusplan: Opus plans, Sonnet implements) | VERIFY_WITH_VENDOR_DOCS (Sonnet) | VERIFY_WITH_VENDOR_DOCS (Opus) |
| AGY | VERIFY_WITH_VENDOR_DOCS (Flash tier) | VERIFY_WITH_VENDOR_DOCS (Pro-high tier) | VERIFY_WITH_VENDOR_DOCS (Claude Sonnet in-AGY) | VERIFY_WITH_VENDOR_DOCS (Pro-high) |
| Gemini CLI | VERIFY_WITH_VENDOR_DOCS (Flash tier) | VERIFY_WITH_VENDOR_DOCS (Pro-high tier) | VERIFY_WITH_VENDOR_DOCS (coding_balanced) | VERIFY_WITH_VENDOR_DOCS (Pro-high / audit_strong) |
| xAI | VERIFY_WITH_VENDOR_DOCS (low-reasoning Grok) | VERIFY_WITH_VENDOR_DOCS (high-reasoning Grok) | VERIFY_WITH_VENDOR_DOCS (medium-reasoning Grok) | VERIFY_WITH_VENDOR_DOCS (high-reasoning Grok) |
| Moonshot | VERIFY_WITH_VENDOR_DOCS (Kimi thinking=off) | VERIFY_WITH_VENDOR_DOCS (Kimi thinking=on) | VERIFY_WITH_VENDOR_DOCS (coding_balanced) | VERIFY_WITH_VENDOR_DOCS (Kimi thinking=on) |
| OpenRouter | VERIFY_WITH_VENDOR_DOCS (broker, pinned cheap) | VERIFY_WITH_VENDOR_DOCS (broker, pinned strong) | VERIFY_WITH_VENDOR_DOCS (broker, pinned coding) | VERIFY_WITH_VENDOR_DOCS (broker, pinned strong + deterministic provider) |

> **Note on OBSERVED model ids**: `gpt-5.4-mini`, `gpt-5.3-codex`, `gpt-5.2`,
> `grok-code-fast-1`, `grok-4-1-fast` are OBSERVED in `model_map_v2_tp008.yaml` /
> `tests/test_routing_config.py` as **RTE extraction lane selectors**. `gpt-5.5` is
> OBSERVED in `config/pricing.yaml`. These are NOT confirmed as accepted model
> selector strings for the tools above; use them as hints only.

---

## 5. Escalation triggers

Any cheap_read or investigation lane must escalate to a strong lane (or stop and
report) when any of these conditions is observed:

- **Authority boundary unclear** — ownership of a surface, contract, or decision is not resolved in repo docs
- **Security / auth / secrets / CI touched** — any change to or near secrets, credentials, CI config, or auth surfaces
- **Runtime contradicts docs** — observed code/config differs from what docs claim
- **PM / workflow / chronicle / retrieval boundary touched** — crossing into ConPort, dope-memory, task-orchestrator, dopecon-bridge, or ADHD Engine authority
- **Task scope changes** — evidence suggests the actual work differs from the packet's scope
- **Diff exceeds allowlist** — changes detected outside the packet's explicitly listed files
- **Proof stale or incomplete** — proof artifact is missing, outdated, or has unresolved NOT_RUN entries
- **Reviewer / auditor identity unknown** — cannot determine if the reviewing agent is independent
- **Confidence below required gate** — internal confidence is below MEDIUM for a non-trivial claim

---

## 6. Anti-patterns

> These are the ways model routing goes wrong. Avoid all of them.

**1. Cheap model makes architecture decision.**
A `cheap_read` or `investigation` lane answers "which approach should we take?" or
"is this safe to merge?" directly. These are `planner_strong` or `judge_strong`
questions. The cheap lane must stop and escalate.

**2. Implementer audits itself without independent audit.**
The `implementer_standard` agent declares its own work ready without a separate
`self_audit` pass by a different tool or model. Self-certification is not evidence.
The proof bundle requires an independent audit verdict.

**3. Agent / coder chooses its own model silently.**
A tool decides at runtime which model to use without recording the actual choice in
proof. The policy requires `actual_tool`, `actual_model`, and `provider` to be
captured — not just the intended route.

**4. Vendor docs guessed from memory.**
Claims like "grok-4-1-fast handles planning" are asserted without checking current
xAI documentation. Model availability, capability, and pricing change. Mark
unverified claims `VERIFY_WITH_VENDOR_DOCS`; do not launder them into `PROPOSED`.

**5. Bridge / proxy treated as authority.**
`dopecon-bridge` routes or retrieval output are promoted to canonical state.
Bridge routes are plumbing; retrieval is derived evidence. Neither is a source of
truth for architecture decisions, task scope, or proof verdicts.

**6. Model routing used to bypass Task Packet gates.**
A cheap_read stage is used to perform scoped implementation work to avoid writing a
Task Packet. Every non-trivial repo-changing operation requires an approved packet,
file allowlist, and validation gates — regardless of which model is used.

**7. Multi-agent consensus theatre without evidence.**
Multiple agents are invoked and their outputs are averaged or synthesized into a
verdict without preserving individual responses, disagreements, or confidence levels.
Consensus must produce a findable audit trail; "three models agreed" with no log is
not evidence.

---

## 7. Task Packet integration

Task Packets declare their intended model routing in a `## Model Routing` section
(see [`task-packets/TEMPLATE_TASK_PACKET.md`](../../../task-packets/TEMPLATE_TASK_PACKET.md)):

```markdown
## Model Routing
- cheap_read:
- investigation:
- planner_strong:
- implementer_standard:
- judge_strong:
- self_audit:
Escalate to strong model if:
- authority boundary unclear
- security/auth/secrets/CI touched
- runtime contradicts docs
- diff exceeds allowlist
- proof stale or incomplete
- reviewer/auditor unknown
- confidence below required gate
```

The declared routes are **intent** only; what was actually used must be captured in
the proof bundle under `actual_tool`, `actual_model`, `provider`, `stage_slot`,
`fallback_used`, and `fallback_reason`.

---

## 8. Proof requirements

Every substantive run must record the **actual** route, not just the intended one.
Required fields per run:

- `actual_tool` — which tool was used (e.g., `claude_code`, `codex`, `copilot`)
- `actual_model` — the model that executed the stage
- `provider` — direct provider or `openrouter` broker
- `stage_slot` — which stage this run operated in
- `requested_model` — what was requested (may differ from actual if fallback occurred)
- `fallback_used` — `true` / `false`
- `fallback_reason` — explanation if fallback occurred
- `reasoning_effort_or_thinking_mode` — e.g., `high`, `thinking=enabled`, `n/a`
- `data_policy_applied` — ZDR / data-collection policy if OpenRouter was used
- `cost_policy_applied` — price cap or cost policy if relevant

The embedded audit object (in `proof/…/PROOF.json`) is governed by
[`schemas/proof/embedded_audit.schema.json`](../../../schemas/proof/embedded_audit.schema.json)
(canonical field `status`, plus `required` and `report_path`). The model-routing
policy references that schema rather than forking it. PROOF.json uses field name
`auditor_verdict` per TP spec; the canonical schema uses `status` — these name the
same verdict space.

---

## 9. Known limitations / unresolved facts

- **Copilot model tiers**: Whether VS Code Copilot accepts `model:` strings beyond
  the repo's current `'Claude Sonnet 4.5'` (implementer) and what cheap/strong
  alternatives are available is **UNKNOWN**. Cheap/strong intent is enforced via
  tool scope (read+search vs. edit) rather than per-agent model selection.

- **Agent model naming drift**: The `auditor_model` schema enum lists
  `claude-sonnet-4.6` (`schemas/proof/embedded_audit.schema.json:45-54`) while
  the agents declare `Claude Sonnet 4.5`. Reconciling this naming is out of scope
  here and preserved as **UNKNOWN**.

- **All provider model selectors**: Exact model selector strings for Codex CLI,
  Claude Code `--model`, AGY, Gemini CLI, xAI, and Moonshot are marked
  **VERIFY_WITH_VENDOR_DOCS** throughout this policy. Operators must replace tier
  intent labels with actual verified model strings before treating this policy as
  executable configuration.

- **Runtime wiring**: No runtime system currently reads this file. The policy is
  advisory until a runtime routing component explicitly consumes it, at which point
  the `authority` field should be updated and the change committed with evidence.
