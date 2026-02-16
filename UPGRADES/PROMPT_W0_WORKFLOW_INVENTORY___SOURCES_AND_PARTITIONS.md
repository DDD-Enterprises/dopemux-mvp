MODE: Mechanical extractions unless explicitly marked ARBITRATION (GPT-5.2).
NO INTERPRETATION: No "purpose", "likely", "should", "means".
EVIDENCE REQUIRED: Every extracted item must include path + line_range.
OUTPUT: JSON only for scan phases. Markdown only for arbitration phases.
STABLE ORDER: Sort lists by path, then line_range[0], then id.
CHUNKING: If output would exceed context, emit PART files and a CAP_NOTICES file.

# Phase W0: Workflow Inventory + Sources & Partitions

Outputs:
- WORKFLOW_SOURCE_INDEX.json
- WORKFLOW_PARTITIONS.json
- WORKFLOW_TODO_QUEUE.json

Prompt:
Inputs to scan (already produced in D/C/E/A/H):
- DOC_WORKFLOWS.json, DOC_INTERFACES.json, DOC_BOUNDARIES.json
- WORKFLOW_RUNNER_SURFACE.json, SERVICE_ENTRYPOINTS.json
- EXEC_COMMAND_INDEX.json, EXEC_SERVICE_START_GRAPH.json
- instruction surfaces: repo + home

Build WORKFLOW_SOURCE_INDEX.json that lists:
- candidate workflow definitions with evidence pointers (doc lines, code symbols, scripts)

Partition workflows by plane:
- W_PM, W_MEMORY, W_MCP, W_HOOKS, W_ROUTING, W_UI, W_TASKX, W_MISC

Output todo queue that prioritizes:
- cross-service workflows first
- workflows involving instruction files
- workflows involving storage/eventbus
