# PROMPT_W1 — Workflow catalog (human runnable)

ROLE: Workflow plane extractor.
GOAL: Produce a catalog of human workflows with literal commands and explicit dependencies.

INPUTS:
  • WORKFLOW_INVENTORY.json partition subset
  • source files in partition

OUTPUTS:
  • WORKFLOW_CATALOG.json
    - workflows[]: {
        id, name, description,
        steps[]: {step_num, description, command_literal, cwd, env_vars[], depends_on_steps[]},
        services_involved[], artifacts_written[], artifacts_read[],
        evidence_refs[]
      }

RULES:
  • Only include steps supported by explicit evidence.
  • If ordering is implied but not explicit: mark ordering UNKNOWN and cite the evidence.
  • evidence_refs must cite file path plus a quoted phrase (≤12 words).
