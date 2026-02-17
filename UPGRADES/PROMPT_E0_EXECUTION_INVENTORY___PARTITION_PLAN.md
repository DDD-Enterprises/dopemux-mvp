GOAL: inventory execution-relevant files + produce a partition plan sized for API caps.

SCOPE TARGETS (repo):
	•	Root: Makefile, justfile, package.json, pyproject.toml, dopemux.toml, compose*.yml, docker-compose*.yml, Dockerfile*, .env*, README*, INSTALL*, QUICK_START*
	•	Dirs: scripts/, tools/, compose/, docker/, .github/, .githooks/, .taskx/, .claude/, config/
	•	Also include any bin/, cmd/, infra/ if present.

INPUT: file list + file contents for in-scope files only.

OUTPUTS (JSON):
	•	EXEC_INVENTORY.json
	•	EXEC_PARTITIONS.json

REQUIRED JSON SHAPE:

{
  "artifact_type": "EXEC_INVENTORY",
  "generated_at": "...",
  "root": "...",
  "items": [
    {"path":"...", "kind":"make|compose|script|ci|docker|config|doc|other", "size":123, "mtime":123, "notes":"..."}
  ]
}

{
  "artifact_type": "EXEC_PARTITIONS",
  "generated_at": "...",
  "partitions": [
    {
      "partition_id":"E_P0001",
      "label":"compose-core",
      "match_rules":["compose.yml","docker-compose*.yml","compose/*.yml"],
      "max_files_hint":30,
      "reason":"..."
    }
  ]
}

RULES:
	•	No invention. If file does not exist, do not mention it.
	•	Partition rules must be reproducible and non-overlapping where possible.
	•	Prefer partitions by function (compose, docker, make/scripts, CI, config/env).
	•	If repo is huge, cap partitions at ~20.
