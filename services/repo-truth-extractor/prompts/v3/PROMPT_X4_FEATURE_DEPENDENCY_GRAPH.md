# PROMPT_X4_FEATURE_DEPENDENCY_GRAPH

TASK: Build feature dependency graph across services, configs, and workflows.

OUTPUTS:
- FEATURE_DEP_GRAPH.json

REQUIREMENTS:
- Emit directed dependencies between features and critical infra/services.
- Include runtime-mode and environment dependencies where observable.
- Preserve cycle information; do not collapse conflicting edges.
