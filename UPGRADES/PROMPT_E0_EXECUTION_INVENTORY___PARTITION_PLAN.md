MODE: Mechanical extractions unless explicitly marked ARBITRATION (GPT-5.2).
NO INTERPRETATION: No "purpose", "likely", "should", "means".
EVIDENCE REQUIRED: Every extracted item must include path + line_range.
OUTPUT: JSON only for scan phases. Markdown only for arbitration phases.
STABLE ORDER: Sort lists by path, then line_range[0], then id.
CHUNKING: If output would exceed context, emit PART files and a CAP_NOTICES file.
RECENCY: For docs/config duplicates, include mtime and source_scope metadata. Do not choose "winner" in scan phases.

# Phase E0: Execution Inventory + Partition Plan

Outputs:
- EXEC_INVENTORY.json
- EXEC_PARTITIONS.json
- EXEC_TODO_QUEUE.json

Prompt:
Enumerate all execution/control surfaces:
- scripts: scripts/**, tools/**, install.sh, start-*.sh, verify_*.sh, run_*.sh
- orchestration: compose*.yml, compose/**, tmux-*.yaml, .tmux.conf
- Make/NPM: Makefile, package.json, package-lock.json, node scripts
- CI: .github/workflows/**

For each file:
- path, ext, size, mtime, sha256 (if feasible), first_40_nonempty_lines

Partition into buckets:
- EXEC_SHELL_SCRIPTS, EXEC_MAKE, EXEC_TMUX, EXEC_COMPOSE, EXEC_CI, EXEC_NODE, EXEC_PY_RUNNERS

Produce EXEC_TODO_QUEUE.json with recommended order by dependency likelihood:
(compose first, then start scripts, then verify scripts, then tmux).
