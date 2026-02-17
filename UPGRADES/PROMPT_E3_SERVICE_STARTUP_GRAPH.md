GOAL: derive the actual service startup graph from compose/scripts/Make.

OUTPUT (JSON):
	•	EXEC_SERVICE_STARTUP_GRAPH.json

MUST EXTRACT:
	•	Services and their names (compose service keys)
	•	Dependency edges (depends_on, “start X before Y” comments, sequencing scripts)
	•	Ports, volumes, env_files only if explicitly shown
	•	Profiles/modes (dev/prod/smoke) if present

FORMAT:

{
  "artifact_type":"EXEC_SERVICE_STARTUP_GRAPH",
  "generated_at":"...",
  "services":[
    {"name":"conport","defined_in":"docker-compose.dev.yml","depends_on":["postgres"],"ports":["..."],"env_files":["..."],"evidence":["..."]}
  ],
  "edges":[
    {"from":"conport","to":"postgres","type":"depends_on","evidence":["..."]}
  ],
  "modes":[
    {"mode":"dev","compose_files":["..."],"evidence":["..."]}
  ]
}

RULES:
	•	Only include a field if seen.
	•	Don’t deduce hidden dependencies.
