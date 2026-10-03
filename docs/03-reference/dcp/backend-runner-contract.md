---
id: REF-DCP-BACKEND-RUNNER-CONTRACT
title: Backend Runner Contract (0008)
type: reference
owner: Control Tower | Current
last_review: 2026-10-03
next_review: 2026-11-03
author: '@hu3mann'
date: '2026-10-03'
prelude: Backend Runner Contract (0008) (reference) for dopemux documentation and
  developer workflows.
---
# Backend Runner Contract (0008)

Inert pure data contract for future runner invocation.

## Non-claims

- `invocation_authorized` is always **false**
- No subprocess / network / model execution is implemented
- `execute_runner_plan` returns `NOT_RUN` only
- No bridge, memory, context, or task-orchestrator runtime mutations

## Types

- `RunnerInvocationPlan`
- `RunnerResult`
- `RunnerProofEnvelope`
- `RunnerContractDocument`
- `RunnerAdapter` (protocol)
- `InertRunnerAdapter` (reference inert implementation)

Schema: `schemas/dcp/runner_contract.schema.json`
