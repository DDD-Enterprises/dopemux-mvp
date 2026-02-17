# PROMPT_W0 — WORKFLOWS inventory + partition plan

ROLE: Workflow plane recon (evidence-first).
GOAL: Identify all workflow “things humans do” and automation flows, then partition sources deterministically.

SCOPE TARGETS:
  • docs/ (runbooks, SOPs, workflow docs)
  • scripts/, tools/, compose/, docker/, .github/
  • tmux helpers, bootstrap scripts, Makefile targets
  • any file mentioning: "workflow", "runbook", "bootstrap", "start", "tmux", "compose", "orchestrator"

OUTPUTS:
  • WORKFLOW_INVENTORY.json
    - items[]: {path, kind(doc/script/ci/compose/tmux/make/cli), workflow_names[], commands_literal[], services_mentioned[], inputs[], outputs[], notes}
  • WORKFLOW_PARTITIONS.json
    - partitions[]: {id, label, include_globs[], exclude_globs[], max_files_hint, rationale}

RULES:
  • No invention. Only list what exists within the scanned files.
  • commands_literal must be verbatim snippets whenever possible.
  • Partitioning must minimize overlap and keep deterministic ordering (sorted by path).
