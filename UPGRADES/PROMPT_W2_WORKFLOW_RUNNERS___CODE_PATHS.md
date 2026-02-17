# PROMPT_W2 — Multi-service workflows (compose/tmux/runner graphs)

ROLE: Workflow plane extractor (graph mode).
GOAL: Build a graph of multi-service workflows and how they start/coordinate services.

OUTPUTS:
  • WORKFLOW_SERVICE_GRAPH.json
    - nodes[]: {id, kind(service/script/command), ref}
    - edges[]: {from, to, type(start/depends/waits_for/healthcheck/uses_env/produces_artifact), evidence_refs[]}

RULES:
  • Graph edges must be evidence-backed (compose depends_on, scripts invoking commands, tmux panes).
  • If a relation is suspected but not explicit: omit it (do not infer).
