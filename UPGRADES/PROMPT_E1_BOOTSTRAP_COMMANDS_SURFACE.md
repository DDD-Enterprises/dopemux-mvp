GOAL: extract every literal runnable command that starts or orchestrates the system.

INPUT: contents from E_P* partitions.

OUTPUT (JSON):
	•	EXEC_BOOTSTRAP_COMMANDS.json

MUST EXTRACT:
	•	Make targets (target name → command lines)
	•	CLI entrypoints invoked (python -m, uv run, node, docker compose, etc.)
	•	Script entrypoints (scripts/*.sh, tools/*.py, bin/*)
	•	Compose up/down commands if explicitly written
	•	Any “quickstart” sequences in docs if they contain literal commands

FORMAT:

{
  "artifact_type":"EXEC_BOOTSTRAP_COMMANDS",
  "generated_at":"...",
  "commands":[
    {
      "id":"CMD_0001",
      "source_path":"Makefile",
      "source_locator":"target:x-run-init",
      "command":"make x-run-init",
      "expands_to":["mkdir -p ...", "..."],
      "notes":"literal; extracted"
    }
  ]
}

RULES:
	•	Only literal commands that appear in the files.
	•	No inferred flags or implied sequences.
