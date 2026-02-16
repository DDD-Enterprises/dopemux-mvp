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

### INV-COST-001: Preference Ladder is Deterministic
**Statement**
- MUST select the same model for the same stage/budget context every time.

**Owner**
- Supervisor

**Scope**
- Applies to: per-packet
- Surfaces: `src/dopemux/supervisor/router.py`

**Evidence**
- FACT ANCHORS:
- `config/models.yaml` (Static configuration)

**Enforcement**
- Mechanism:
- Runtime: Hardcoded `Stage-to-Model` lookup table.

**Test**
- Local command(s):
- `dmux route --stage "Design" --budget "High"`
- Expected signals:
- Always returns "Claude 3.5 Sonnet" (or configured Tier 3).
- Failure signature:
- Returns "GPT-4o-mini" randomly.
- Exit behavior:
- Log decision and proceed (if valid).

**Failure modes**
- If violated:
- Impact: nondeterminism, cost variance.
- Severity: S2 medium.
- Containment: Lock random seed (if applicable).

### INV-COST-002: Routing Decisions are Logged
**Statement**
- MUST record *why* a specific runner was chosen (e.g., "Tier 1 fallback due to cost limit").

**Owner**
- Supervisor

**Scope**
- Applies to: per-run
- Surfaces: `logs/supervisor.log`, `RUN_REPORT.json`

**Evidence**
- FACT ANCHORS:
- `src/dopemux/supervisor/router.py` (logging calls)

**Enforcement**
- Mechanism:
- Runtime: Router component integrity check.

**Test**
- Local command(s):
- `grep "Routing decision:" logs/supervisor.log`
- Expected signals:
- "Selected Runner: X Reason: Y"
- Failure signature:
- Missing log lines.
- Exit behavior:
- N/A.

**Failure modes**
- If violated:
- Impact: audit loss.
- Severity: S3 low.
- Containment: Fix logging.

### INV-COST-003: Limits Model Never Guessed
**Statement**
- MUST NOT invent pricing or limits. If config is missing, assume $0.00 budget (Safe Mode).

**Owner**
- Supervisor

**Scope**
- Applies to: per-run
- Surfaces: `config/limits.yaml`

**Evidence**
- FACT ANCHORS:
- `config/pricing.yaml` (source of truth)

**Enforcement**
- Mechanism:
- Runtime: Default to `SAFE_MODE` if config missing.

**Test**
- Local command(s):
- `mv config/limits.yaml config/limits.bak && dmux run`
- Expected signals:
- "Limits config missing. Entering Safe Mode (Budget: $0.00)."
- Failure signature:
- Runs with infinite budget.
- Exit behavior:
- Fallback to Safe Mode.

**Failure modes**
- If violated:
- Impact: cost leak.
- Severity: S1 high.
- Containment: Hard API quotas on provider side.

### INV-COST-004: Cheap-Mode Triggers Reduce Scope
**Statement**
- When in "Cheap Mode", Supervisor MUST reduce scope (chunk size, context window), NOT correctness (e.g., using a dumb model for complex math).

**Owner**
- Supervisor

**Scope**
- Applies to: per-packet
- Surfaces: `src/dopemux/packets/generator.py`

**Evidence**
- FACT ANCHORS:
- `config/limits.yaml` (defines cheap mode threshold)

**Enforcement**
- Mechanism:
- Runtime: If `cheap_mode=True`, max_steps = 3 (vs 7).

**Test**
- Local command(s):
- `dmux run --profile economy --objective "Massive refactor"`
- Expected signals:
- "Objective too large for Economy Profile. Breaking down..."
- Failure signature:
- Attempts massive refactor on Haiku and fails.
- Exit behavior:
- Refusal / Decomposition.

**Failure modes**
- If violated:
- Impact: failed runs, wasted tokens.
- Severity: S2 medium.
- Containment: User intervention.

### INV-COST-005: External Pricing Stored as Config
**Statement**
- MUST store pricing rates in `config/pricing.yaml`, NOT hardcoded in python source.

**Owner**
- Store

**Scope**
- Applies to: repo
- Surfaces: `config/pricing.yaml`

**Evidence**
- FACT ANCHORS:
- `config/pricing.yaml`

**Enforcement**
- Mechanism:
- Gate: `doc_gate.py` (could check for hardcoded rates in src).

**Test**
- Local command(s):
- `grep "0.0001" src/dopemux/supervisor/cost.py`
- Expected signals:
- No results (should import from config).
- Failure signature:
- Hardcoded magic numbers.
- Exit behavior:
- Code Review Rejection.

**Failure modes**
- If violated:
- Impact: stale pricing, maintenance nightmare.
- Severity: S3 low.
- Containment: Update code.

## FACT ANCHORS (Repo-derived)

- **OBSERVED: Intelligent Routing**: `services/adhd_engine/core/engine.py` implements routing based on cognitive capacity and energy matching (`_assess_energy_match`).
- **OBSERVED: Context Switch Tracker**: `services/adhd_engine/domains/context-switch-tracker/` calculates distraction scores and context switch costs.
- **OBSERVED: Performance Optimization**: `services/task-orchestrator/performance_optimizer.py` handles resource-aware task execution.
- **OBSERVED: Metrics**: `services/task_orchestrator/app/main.py` exports `task_orchestrator_tasks_orchestrated_total` and `ai_agent_dispatches_total`.
- **DOC-CLAIM: Cost Preference Ladder**: Described in `.claude/claude.md` but implementation details for model pricing are not yet observed in `adhd_engine`.

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

1. **Tier 2: Prepaid Credits / Low Cost API**
- **OpenRouter (Route-to-Cheapest)**: For bulk/low-risk tasks.
- **DeepSeek V3 / Grok Beta**: High performant, lower cost points.

1. **Tier 3: Premium API (Pay-as-you-go)**
- **Claude 3.5 Sonnet / 3 Opus**: For complex reasoning/coding.
- **GPT-4o**: For general high-quality output.

1. **Tier 4: Local Models (Free)**
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
1. **Adjust**: Update `Stage-to-Model Mapping` to promote those stages to "Smart" models.
1. **Analyze**: Identify stages with 100% success on "Smart" models.
1. **Adjust**: Test "downgrading" to "Cheapest/Fast" models to save cost.

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
1. **Routing Verification**: Request a "Design" task. Logs MUST show Tier 3 model selection. Request a "Bulk" task. Logs MUST show Tier 2/4.
1. **Fallback Logic**: Simulate "API Down" for Primary. Ensure Supervisor picks correct Fallback from the table.
