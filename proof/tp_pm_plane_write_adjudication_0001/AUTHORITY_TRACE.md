# Authority Trace

## Canonical write rules

- Leantime is canonical for `create_work_item`, `update_pm_metadata`, and `mirror_workflow_outcome_into_leantime`.
- Task Orchestrator is the canonical adjudicator and writer for workflow-significant mutations:
  - `transition_workflow_state`
  - `block_unblock_work_item`
- ConPort is canonical for:
  - `attach_decision`
  - `log_progress`
  - durable context attachments for technical and retrieval metadata
- dope-memory is canonical for `emit_chronicle_event`.
- dopecon-bridge is never canonical and only appears as proxy, router, or transport.

## Mandatory adjudication rule

Workflow-significant mutations must be adjudicated by Task Orchestrator before reflection into Leantime.

## Canonical resolution rules

- Decision and progress mutations resolve to ConPort.
- Chronicle mutations resolve to dope-memory.
- Adapter or proxy layers may not silently escalate authority.
