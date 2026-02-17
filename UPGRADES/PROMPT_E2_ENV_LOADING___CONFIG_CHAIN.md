# PROMPT_E2 — Environment loading + config chain

ROLE: Execution plane extractor.
GOAL: document env vars, where they originate, and the precedence chain they follow (dotenv, shell, config, CLI).

OUTPUTS:
  • EXEC_ENV_CHAIN.json
    - env_vars[]: {name, required, default, where_set[], where_used[]}
    - config_chain[]: {layer, files[], precedence_rule, notes}

RULES:
  • Mark precedence UNKNOWN unless explicitly stated.
  • Do not guess whether an env var is required unless annotated.
