GOAL: map where runtime artifacts go (logs, DBs, caches, run dirs).

OUTPUT (JSON):
	•	EXEC_ARTIFACT_OUTPUTS.json

MUST INCLUDE:
	•	Output directories (extraction/runs/..., /tmp/..., ~/.dopemux/...) if referenced
	•	DB files (sqlite paths) if referenced
	•	Log locations and naming patterns
	•	“Proof pack” outputs if mentioned

FORMAT:

{
  "artifact_type":"EXEC_ARTIFACT_OUTPUTS",
  "generated_at":"...",
  "outputs":[
    {"path":"extraction/runs/<run_id>/A_repo_control_plane/raw","kind":"pipeline_output","producer":"run_extraction_v3.py","evidence":["..."]}
  ]
}
