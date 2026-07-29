# Backend Runner Contract (0008)

Inert pure data contract for future runner invocation.

## Non-claims

- `invocation_authorized` is always **false**
- No subprocess / network / model execution is implemented
- `execute_runner_plan` returns `NOT_RUN` only

## Types

- `RunnerInvocationPlan`
- `RunnerResult`
- `RunnerProofEnvelope`
- `RunnerContractDocument`

Schema: `schemas/dcp/runner_contract.schema.json`
