#!/usr/bin/env bash
# Run PAL toolchain gates for Memory Trinity remediation phases.
set -euo pipefail
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"
RUNNER="python3 scripts/pal/run_pal_chain.py"
SLICE001_FILES="AGENTS.md,.claude/modules/shared/memory-trinity-routing.md,scripts/validate_memory_command_refs.py,docs/90-adr/adr-memory-trinity-authority-and-interaction-model.md,.claude/commands/decision.md,.claude/commands/ctx/search-here.md"

phase1() {
  local P="TP-DMX-MEMORY-TRINITY-001"
  $RUNNER --packet "$P" --step 01_ANALYZE --tool analyze --files "$SLICE001_FILES" \
    --prompt "Audit Memory Trinity slice 001 for authority compliance and drift elimination." --timeout 300
  $RUNNER --packet "$P" --step 02_THINKDEEP --tool thinkdeep --files "$SLICE001_FILES" \
    --prompt "Cross-plane risks: search_all decision projection, DCP facade gap, tm:* residue." --timeout 300
  $RUNNER --packet "$P" --step 03_CHALLENGE_UNDERSTANDING --tool challenge \
    --prompt "Slice 001 eliminated all memory command drift and made Trinity law without gaps."
  $RUNNER --packet "$P" --step 04_PLANNER --tool planner \
    --prompt "Produce commit-sized plan for slices 002-005 with explicit validation commands each." --timeout 300
  $RUNNER --packet "$P" --step 05_CHALLENGE_PLAN --tool challenge \
    --prompt "Four-slice plan is minimal and will not resurrect TaskMaster tm:* commands in hidden paths."
  $RUNNER --packet "$P" --step 06_CODEREVIEW --tool codereview --files "$SLICE001_FILES" \
    --prompt "Review slice 001 diff for authority violations." --timeout 300
  $RUNNER --packet "$P" --step 07_PRECOMMIT --tool precommit --files "$SLICE001_FILES" \
    --prompt "Precommit: validate_memory_command_refs.py, packet schema, git diff --check." --timeout 300
  $RUNNER --packet "$P" --step 08_FINAL_CHALLENGE --tool challenge \
    --prompt "Slice 001 ready to merge; residual work isolated to slices 002-005."
}

phase_gate() {
  local packet="$1" step="$2" tool="$3" prompt="$4"
  shift 4
  $RUNNER --packet "$packet" --step "$step" --tool "$tool" --prompt "$prompt" "$@"
}

echo "=== Phase 1 PAL gate ==="
phase1

echo "=== Phase 2 pre-implementation PAL gate ==="
phase_gate TP-DMX-MEMORY-TRINITY-002 01_ANALYZE analyze \
  "Analyze skills install path: sync_repo_skills.py, templates/skills, 47 tm:* commands." \
  --files "scripts/skills/sync_repo_skills.py,templates/skills/pr-merge-specialist/SKILL.md,docs/docs_index.yaml" --timeout 300
phase_gate TP-DMX-MEMORY-TRINITY-002 02_PLANNER planner \
  "Plan slice 002: extend sync targets, frontmatter validator, delete tm:*, update docs_index." --timeout 300

echo "=== Phase 3 pre-implementation PAL gate ==="
phase_gate TP-DMX-MEMORY-TRINITY-003 01_ANALYZE analyze \
  "Plan dope-memory operator surface /mem:recap and mirror semantics." \
  --files "src/dopemux/orchestrator/memory_writers.py,.claude/modules/shared/memory-trinity-routing.md" --timeout 300

echo "=== Phase 4 pre-implementation PAL gate ==="
phase_gate TP-DMX-MEMORY-TRINITY-004 01_ANALYZE analyze \
  "Wire memory/skill drift validators into pre-commit." \
  --files "scripts/validate_memory_command_refs.py,.pre-commit-config.yaml" --timeout 300

echo "=== Phase 5 pre-implementation PAL gate ==="
phase_gate TP-DMX-MEMORY-TRINITY-005 01_ANALYZE analyze \
  "Dedup skill docs to docs/03-reference/skills canonical tree." \
  --files "docs/docs_index.yaml,config/docs_hygiene/docs_placement_policy.yaml" --timeout 300

echo "Done. Artifacts under proof/TP-DMX-MEMORY-TRINITY-*/pal/"