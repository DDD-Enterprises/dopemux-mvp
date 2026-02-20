# SYSTEM PROMPT\nMODE: Mechanical extractions unless explicitly marked ARBITRATION (GPT-5.2).
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
\n\n# USER CONTEXT\n\n--- FILE: /Users/hue/code/dopemux-mvp/scripts/pipeline_manifest.py ---\nimport os
import json
import datetime
import subprocess

def get_git_sha():
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
    except:
        return "unknown"

def is_git_dirty():
    try:
        return len(subprocess.check_output(['git', 'status', '--porcelain']).decode('ascii').strip()) > 0
    except:
        return True

def main():
    latest_id_file = "extraction/latest_run_id.txt"
    if not os.path.exists(latest_id_file):
        print("No run initialized. Run 'make x-run-init' first.")
        return

    with open(latest_id_file, 'r') as f:
        run_id = f.read().strip()

    manifest_path = f"extraction/runs/{run_id}/MANIFEST.json"

    manifest = {
        "run_id": run_id,
        "repo_root": os.getcwd(),
        "git_sha": get_git_sha(),
        "is_dirty": is_git_dirty(),
        "created_at_local": datetime.datetime.now().isoformat(),
        "phases": {
            "A": {"status": "pending"},
            "H": {"status": "pending"},
            "D": {"status": "pending"},
            "C": {"status": "pending"},
            "R": {"status": "pending"},
            "R2": {"status": "pending"},
            "X": {"status": "pending"},
            "T": {"status": "pending"}
        }
    }

    # If manifest already exists, preserve status but update metadata
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            old_manifest = json.load(f)
            manifest["phases"] = old_manifest.get("phases", manifest["phases"])

    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    # Also update symlink if possible (already handled by Makefile usually)
    print(f"✓ Updated manifest at {manifest_path}")

if __name__ == "__main__":
    main()
\n\n--- FILE: /Users/hue/code/dopemux-mvp/scripts/setup.sh ---\n#!/bin/bash
#
# Dopemux Setup Script - One-Command ... [truncated for trace]