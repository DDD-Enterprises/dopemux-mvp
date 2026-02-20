Goal: REPO_HOOKS_SURFACE.json, REPO_IMPLICIT_BEHAVIOR_HINTS.json

Prompt:
- Inventory .githooks/**, scripts/**, any post-checkout, pre-commit, prepare-commit-msg, etc.
- Extract:
  - what they execute, which services they touch, any auto-run behavior, any writes to state DBs or out dirs.
- Build a "trigger map": trigger -> commands -> touched paths.