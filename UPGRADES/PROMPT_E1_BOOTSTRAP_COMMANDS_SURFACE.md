# PROMPT_E1 — Bootstrap commands surface

ROLE: Execution plane extractor.
GOAL: enumerate bootstrap and "first 10 minutes" commands plus their ordering constraints.

OUTPUTS:
  • EXEC_BOOTSTRAP_COMMANDS.json
    - commands[]: {name, command, cwd, env_vars[], depends_on[], produces[]}
    - entrypoints[]: {human_name, canonical_command_ref}

RULES:
  • Only record literal commands present in scanned files.
  • Capture dependency hints (depends_on) only when explicitly stated.
