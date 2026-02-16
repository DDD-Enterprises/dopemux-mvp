MODE: Mechanical extractions unless explicitly marked ARBITRATION (GPT-5.2).
NO INTERPRETATION: No "purpose", "likely", "should", "means".
EVIDENCE REQUIRED: Every extracted item must include path + line_range.
OUTPUT: JSON only for scan phases. Markdown only for arbitration phases.
STABLE ORDER: Sort lists by path, then line_range[0], then id.
CHUNKING: If output would exceed context, emit PART files and a CAP_NOTICES file.

# Phase W1: Workflow Extract Combined + Structured (Part X)

Run per workflow partition.

Outputs:
- WORKFLOWS_EXTRACTED.partX.json
- WORKFLOW_INTERFACE_TOUCHES.partX.json
- CAP_NOTICES.W1.partX.json (optional)

Prompt:
For each workflow candidate:
- Extract structured object:
  - workflow_id (stable slug)
  - trigger (event/command/hook/ui action)
  - steps[] (actor, action, inputs, outputs, side effects)
  - interfaces[] (db/event/file/http/mcp/hook/env)
  - guards[] (validation/enforcement points if explicitly cited)
  - artifacts[] (reports/out files)
  - evidence[] (path + line_range + short quote)

Output interface touches separately:
- per workflow, list which DB tables, event names, file paths are touched (only if cited)
