---
title: "Routing Policy and Cost"
plane: "pm"
component: "dopemux"
status: "proposed"
---

# Routing Policy, Plans, and Cost Optimization

## Purpose
How Supervisor chooses the optimal runner + model combination for a given task stage, balancing cost, quality, and speed. This document defines the algorithmic decision-making process for resource allocation.

## Scope
- Model selection logic (Preference Ladder).
- Cost estimation and budget enforcement.
- Quality feedback loop (Optimization Loop).
- Failure modes and fallback strategies.

## Non-negotiable invariants
1. **Budget Cap**: A single task packet MUST NOT exceed its estimated cost by more than 50% without explicit operator confirmation.
2. **Quality Floor**: Critical stages (Architecture/Review) MUST run on high-reasoning models (Opus/GPT-4o/Reasoning) regardless of cost tier.
3. **No Silent Upgrades**: Escalating from a free/cheap tier to a paid API tier requires policy check (or prior approval).
4. **Deterministic Fallback**: If a preferred model is unavailable, valid alternatives are tried in a fixed, predictable order.

## FACT ANCHORS (Repo-derived)
- **Model Config**: `config/models.yaml` (to be created/verified).
- **Routing Logic**: `src/dopemux/supervisor/router.py` (to be created/verified).

## Open questions
- **Real-time Pricing**: Do we fetch live pricing API or stick to config?
  - *Resolution*: Config-based pricing updated via `dmux update-models`.
- **Quality Metrics**: How do we measure "quality" automatically?
  - *Resolution*: Start with binary "Success/Fail" and "Rewrite Count". Later add "Linter Score".

## Preference Ladder (Policy)
The Supervisor evaluates available runners in this order:

1. **Tier 1: Included Plans** (Sunk Cost)
   - **GitHub Copilot Chat** (if active subscription detected).
   - **ChatGPT Plus / Team** (via local bridge/browser integration if available).
   - **Anthropic Pro** (via local bridge).
   *Rationale*: Already paid for; marginal cost is near zero.

2. **Tier 2: Prepaid Credits / Low Cost API**
   - **OpenRouter (Route-to-Cheapest)**: For bulk/low-risk tasks.
   - **DeepSeek V3 / Grok Beta**: High performant, lower cost points.

3. **Tier 3: Premium API (Pay-as-you-go)**
   - **Claude 3.5 Sonnet / 3 Opus**: For complex reasoning/coding.
   - **GPT-4o**: For general high-quality output.

4. **Tier 4: Local Models (Free)**
   - **Ollama / Local LLM**: If hardware permits (e.g., M-series Mac).
   - *Constraint*: Only used if explicit "Offline Mode" or if API is down.

## Stage-to-Model Mapping Table

| Stage                     | Primary Model                    | Fallback | Rationale                                               |
| :------------------------ | :------------------------------- | :------- | :------------------------------------------------------ |
| **Preflight / Planning**  | **Claude 3 Haiku / GPT-4o-mini** | Local 7B | Fast, cheap context gathering.                          |
| **Architecture / Design** | **Claude 3.5 Sonnet / Opus**     | GPT-4o   | Requires reasoning & big context.                       |
| **Implementation (Core)** | **Claude 3.5 Sonnet (Coding)**   | GPT-4o   | Balance of strict instruction following & code quality. |
| **Implementation (Bulk)** | **DeepSeek V3 / GPT-4o-mini**    | Haiku    | Boilerplate generation, tests.                          |
| **Review / Audit**        | **Claude 3 Opus / GPT-4o**       | Sonnet   | "Fresh eyes" high-intelligence check.                   |
| **Ops / Git / Meta**      | **GPT-4o-mini / Haiku**          | Local 7B | Simple command generation.                              |

## Where numbers come from

### Pricing Sources
`config/pricing.yaml` maps `provider/model` to `input_cost_per_m` and `output_cost_per_m`.

### Limits Sources
`config/limits.yaml` defines:
- **Global**: Monthly Hard Cap ($50.00).
- **Project**: Per-packet Soft Cap ($2.00).
- **Daily**: Rolling 24h Cap ($10.00).

### Quality Sources
- **Pass Rate**: % of Task Packets that succeed without user intervention.
- **Rework Count**: Number of times a step had to be retried due to error.
- **User Rating**: Explicit thumbs up/down (if implemented in UI).

## Long-term Optimization Loop

**Input**:
- Log of every run: `{model, stage, tokens_in, tokens_out, cost, success, rework_count}`.

**Process**:
1. **Analyze**: Identify stages with high failure rate on "Cheap" models.
2. **Adjust**: Update `Stage-to-Model Mapping` to promote those stages to "Smart" models.
3. **Analyze**: Identify stages with 100% success on "Smart" models.
4. **Adjust**: Test "downgrading" to "Cheapest/Fast" models to save cost.

**Policy V1**:
- "If pass_rate < 80% on Tier 2, force upgrade to Tier 3 for that Stage."
- "If pass_rate > 95% on Tier 3 for >10 runs, try Tier 2."

## Failure Modes & Refusal Conditions

### 1. Cost Overrun
- **Mode**: A loop or massive context dump causes cost to spike.
- **Detection**: Real-time token counter checks against `Project Soft Cap`.
- **Refusal**: If projected cost > limit, **PAUSE** execution and request user Override. "Projected cost $2.50 exceeds limit $2.00."

### 2. Quality Collapse
- **Mode**: A cheap model generates syntactically correct but logically flawed code (hallucination).
- **Detection**: Linter/Test failure rate > 50% for the session.
- **Refusal**: If 3 consecutive failures occur on Tier 2/4 model, **STOP** and recommend upgrade to Tier 3.

### 3. Wrong Runner Config
- **Mode**: User asks for "Opus" but API key is missing.
- **Refusal**: **STOP** immediately. Do NOT silently fall back to a "dumber" model for critical tasks. explicitly fail with "Configuration Error: Opus key missing."

## Acceptance Criteria
1. **Budget Enforcement**: Run a synthetic task with a $0.01 limit. Ensure it pauses/stops before exceeding it.
2. **Routing Verification**: Request a "Design" task. Logs MUST show Tier 3 model selection. Request a "Bulk" task. Logs MUST show Tier 2/4.
3. **Fallback Logic**: Simulate "API Down" for Primary. Ensure Supervisor picks correct Fallback from the table.
