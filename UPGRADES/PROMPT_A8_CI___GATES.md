# PHASE A8 — CI + GATES + POLICY ENFORCEMENT (REPO)
Model: Gemini Flash 3
Goal: Produce REPO_CI_GATES.json

Hard rules:
- Mechanical extraction only.
- Evidence required.

Inputs:
- .github/workflows/**, .pre-commit-config.yaml, Makefile, scripts/*check*, policy jsons.

Task:
REPO_CI_GATES.json:
- ci_workflows[]:
  - name, triggers, jobs, steps (literal)
- local_gates[]:
  - precommit hooks, make targets, scripts
- policy_files[]:
  - root hygiene policy, allowlists/denylists
- artifact_paths[]:
  - known output dirs that gates care about (out/, extraction/, reports/, etc.)
- evidence everywhere
