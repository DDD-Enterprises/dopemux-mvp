# PROMPT_E3 — Service startup graph

ROLE: Execution plane extractor.
GOAL: derive the startup graph from compose files, scripts, tmux layouts, and CLI entrypoints that start services.

OUTPUTS:
  • EXEC_STARTUP_GRAPH.json
    - nodes[]: {id, kind(service/script/command), ref, starts[]}
    - edges[]: {from, to, type(start/depends/healthcheck/waits_for)}

RULES:
  • Only include relations that are explicitly documented.
  • Leave ports/volumes out unless they appear alongside the service definition.
