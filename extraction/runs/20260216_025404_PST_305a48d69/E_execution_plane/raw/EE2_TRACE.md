# SYSTEM PROMPT\nMODE: Mechanical extractions unless explicitly marked ARBITRATION (GPT-5.2).
NO INTERPRETATION: No "purpose", "likely", "should", "means".
EVIDENCE REQUIRED: Every extracted item must include path + line_range.
OUTPUT: JSON only for scan phases. Markdown only for arbitration phases.
STABLE ORDER: Sort lists by path, then line_range[0], then id.
CHUNKING: If output would exceed context, emit PART files and a CAP_NOTICES file.

# Phase E2: Exec Start Graph + Merge & Normalize

Outputs:
- EXEC_COMMAND_INDEX.json
- EXEC_SERVICE_START_GRAPH.json
- EXEC_QA.json

Prompt:
Merge all EXEC_COMMAND_INDEX.part*.json
Build EXEC_SERVICE_START_GRAPH.json:
- nodes: services/scripts/commands
- edges: "invokes", "depends_on", "writes_to", "reads_from"

QA:
- missing partitions
- commands without citations
- duplicate IDs
- unstable ordering
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