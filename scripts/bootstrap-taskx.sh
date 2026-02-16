#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -f "$REPO_ROOT/.taskx-pin" ]]; then
  echo "Error: .taskx-pin missing in repo root." >&2
  exit 1
fi

PIN_REPO="$(sed -n 's/^repo=//p' "$REPO_ROOT/.taskx-pin" | head -n 1)"
PIN_REF="$(sed -n 's/^ref=//p' "$REPO_ROOT/.taskx-pin" | head -n 1)"
PIN_COMMIT="$(sed -n 's/^commit=//p' "$REPO_ROOT/.taskx-pin" | head -n 1)"

if [[ -z "$PIN_REPO" || -z "$PIN_REF" || -z "$PIN_COMMIT" ]]; then
  echo "Error: .taskx-pin must include repo, ref, and commit fields." >&2
  exit 1
fi

VENV="$REPO_ROOT/.taskx_venv"

if [[ -d "$VENV" ]]; then
  echo "TaskX venv already exists. Reinstalling..."
  rm -rf "$VENV"
fi

echo "Creating TaskX venv at $VENV..."
python3 -m venv "$VENV"

echo "Installing TaskX from $PIN_REPO@$PIN_COMMIT..."
"$VENV/bin/pip" install --upgrade pip
"$VENV/bin/pip" install "git+$PIN_REPO@$PIN_COMMIT"

echo "TaskX bootstrapped successfully."
