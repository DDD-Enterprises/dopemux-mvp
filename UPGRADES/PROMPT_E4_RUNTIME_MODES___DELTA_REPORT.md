GOAL: enumerate runtime modes and what changes between them.

OUTPUT (JSON):
	•	EXEC_RUNTIME_MODES.json
	•	EXEC_MODE_DELTAS.json

MUST INCLUDE:
	•	Mode names (dev/prod/smoke/test) if present
	•	Per mode: which compose files, which make targets, which scripts
	•	Deltas: env vars, service set changes, feature flags, profiles

FORMAT (delta):

{
  "artifact_type":"EXEC_MODE_DELTAS",
  "generated_at":"...",
  "deltas":[
    {"from":"dev","to":"prod","changes":[{"kind":"service_added","value":"...","evidence":["..."]}]}
  ]
}

RULES:
	•	If there’s only one mode, still emit with modes:[...] and deltas:[].
