# PROMPT: A6 - Compose Service Graph

Phase: A
Step: A6

Outputs:
- REPO_COMPOSE_SERVICE_GRAPH.json

Mode: extraction
Strict: evidence_only
Format: JSON only (no markdown fences)

Hard rules:
1) Do NOT invent. If not present, write "UNKNOWN".
2) Every non-trivial field must include "evidence" with source_path and either key_path or excerpt.
3) Emit ONLY valid JSON. No commentary.

Input:
You will receive repo control-plane files. Extract only what is explicitly evidenced.

Required JSON shape:
{
  "artifact": "REPO_COMPOSE_SERVICE_GRAPH.json",
  "phase": "A",
  "step": "A6",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "service:<name>",
      "service_name": "...",
      "image": "...",
      "build": "...",
      "env": ["..."],
      "ports": ["..."],
      "volumes": ["..."],
      "depends_on": ["..."],
      "networks": ["..."],
      "evidence": [
        {
          "source_path": "...",
          "key_path": "...",
          "excerpt": "..."
        }
      ]
    }
  ],
  "unknowns": ["..."]
}

Extract:
- Compose services: image/build, env names, volumes, ports, depends_on
- Networks and volumes
- Do not infer service meaning unless explicitly named
