# PROMPT_Q11 - ARTIFACT COLLISION REPORT

TASK: Detect declared artifact collisions across the pipeline promptpack.

GOAL:
- Produce a deterministic collision report from declared outputs per step.
- Use promptpack declarations only when determining writers.

OUTPUTS:
- QA_ARTIFACT_COLLISION_REPORT.json

HARD RULES:
1) Do not rescan repository files.
2) Compute collisions from promptpack declarations, not filesystem-only observations.
3) No invention. If a writer is not provable from promptpack, omit it and add UNKNOWN in notes.
4) Deterministic ordering is required.

REQUIRED INPUTS:
- Q_PROMPTPACK_DECLARED_OUTPUTS.json

OPTIONAL INPUTS:
- QA_PROMPT_COLLISIONS.json
- QA_RUN_MANIFEST.json

OUTPUT SCHEMA:
{
  "collisions": [
    {
      "artifact_name": "DOC_TOPIC_CLUSTERS.json",
      "writers": [
        {"phase": "D", "step_id": "D4", "prompt_file": "PROMPT_D4_...md"},
        {"phase": "D", "step_id": "D5", "prompt_file": "PROMPT_D5_...md"}
      ],
      "risk": "overwrites_in_norm",
      "recommendation": "LATEST_WINS|APPEND_LEDGER|MERGE_BY_ID",
      "notes": ["..."]
    }
  ]
}

DETERMINISM:
- Sort collisions by artifact_name.
- Sort writers by (phase, step_id, prompt_file).
- Sort notes lexicographically where possible.
- Do not emit timestamps or runtime identity fields.
