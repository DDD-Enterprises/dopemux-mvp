#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_ID="${1:-}"
LATEST_FILE="$ROOT_DIR/extraction/repo-truth-extractor/v3/latest_run_id.txt"

if [[ -z "$RUN_ID" ]]; then
  if [[ -f "$LATEST_FILE" ]]; then
    RUN_ID="$(tr -d '[:space:]' < "$LATEST_FILE")"
  else
    echo "No run id provided and latest_run_id.txt not found." >&2
    exit 1
  fi
fi

RUN_ROOT="$ROOT_DIR/extraction/repo-truth-extractor/v3/runs/$RUN_ID"
if [[ ! -d "$RUN_ROOT" ]]; then
  echo "Run root not found: $RUN_ROOT" >&2
  exit 1
fi

echo "=== TP-SCAN-PROMPTGEN-0001 Proof ==="
echo "repo_root=$ROOT_DIR"
echo "run_id=$RUN_ID"
echo "branch=$(git -C "$ROOT_DIR" rev-parse --abbrev-ref HEAD)"
echo "git_sha=$(git -C "$ROOT_DIR" rev-parse HEAD)"
echo

python3 - "$RUN_ROOT" <<'PY'
import json
import sys
from pathlib import Path

run_root = Path(sys.argv[1])
promptpacks = run_root / "promptpacks"
inputs = run_root / "00_inputs"

def load_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def print_json_head(label: str, path: Path, keys):
    payload = load_json(path)
    if payload is None:
        print(f"{label}: MISSING ({path})")
        return
    out = {k: payload.get(k) for k in keys}
    print(f"{label}: {path}")
    print(json.dumps(out, indent=2, sort_keys=True))

print_json_head(
    "RUN_PROMPTPACK_FINGERPRINT",
    run_root / "RUN_PROMPTPACK_FINGERPRINT.json",
    ["run_id", "promptgen_mode", "promptpack_path", "promptpack_sha256", "profile_id"],
)
print()
print_json_head(
    "REPO_FINGERPRINT",
    inputs / "REPO_FINGERPRINT.json",
    ["version", "run_id", "totals", "language_counts", "path_clusters"],
)
print()
print_json_head(
    "ARCHETYPES",
    inputs / "ARCHETYPES.json",
    ["version", "run_id", "archetypes", "contracts_present"],
)
print()

v1_hash = load_json(promptpacks / "PROMPTPACK.v1.sha256.json")
v2_hash = load_json(promptpacks / "PROMPTPACK.v2.sha256.json")
if v1_hash is not None:
    print("PROMPTPACK_V1_SHA:", v1_hash.get("pack_sha256"))
else:
    print("PROMPTPACK_V1_SHA: MISSING")
if v2_hash is not None:
    print("PROMPTPACK_V2_SHA:", v2_hash.get("pack_sha256"))
else:
    print("PROMPTPACK_V2_SHA: MISSING")
print()

diff_path = promptpacks / "PROMPTPACK_DIFF.md"
if diff_path.exists():
    print(f"PROMPTPACK_DIFF: {diff_path}")
    text = diff_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    for line in text[:40]:
        print(line)
else:
    print(f"PROMPTPACK_DIFF: MISSING ({diff_path})")
PY

