---
id: MCP_TOKEN_MANAGEMENT_BEST_PRACTICES
title: MCP Token Management Best Practices
type: reference
owner: '@hu3mann'
author: Codex
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-02-20'
status: active
prelude: Practical token budgeting and response-shaping standards for Dopemux MCP servers to prevent truncation failures and maintain predictable UX.
---
# MCP Token Management Best Practices

## Objectives

1. Avoid hard truncation in MCP responses.
2. Keep response quality predictable across large payloads.
3. Make token behavior observable in logs and metrics.

## Budgeting Standards

1. Define per-tool response token budgets explicitly.
2. Reserve safety margin for wrappers/metadata (minimum `10%`).
3. Prefer deterministic truncation strategies over implicit model truncation.
4. For list-style responses, cap item counts before serialization.
5. For large text sources, summarize first, then expose drill-down links/IDs.

## Response Shaping Pattern

1. Validate request size and complexity early.
2. Estimate candidate output size before full assembly.
3. Apply tiered output:
   - Tier 1: concise summary
   - Tier 2: key details
   - Tier 3: optional expanded payload behind pagination/filters
4. Emit truncation metadata when reduction is applied (`truncated=true`, reason, original-size hint).

## Operational Controls

1. Track truncation frequency per tool.
2. Track budget-usage ratio (`used_budget / configured_budget`).
3. Alert on sustained high budget utilization or repeated truncation spikes.
4. Include representative large-payload regression tests in CI.

## Production Validation Checklist

1. Run large-file response test (for example lockfiles or long manifests).
2. Run bulk-query response test (for example high-cardinality decision lists).
3. Run multi-step analysis flow to ensure cumulative budget safety.
4. Confirm logs include token-budget telemetry fields.

## Implementation References

1. `services/shared/mcp_response_budget.py`
2. `docs/05-audit-reports/MCP_RESPONSE_BUDGET_VERIFICATION_2026-02-06.md`
3. `docs/05-audit-reports/MCP_BUDGET_MONITORING_VERIFICATION_2026-02-06.md`
