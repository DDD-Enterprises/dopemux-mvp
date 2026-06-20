# Dopetask Runtime Surfaces

Wrapper/source evidence captured. Executable Dopetask calls were NOT_RUN due packet conflict with no Dopetask execution/no dependency installs.

# dopetask source/wrapper evidence
-rw-r--r--@ 1 hue  staff    39 Jun 11 17:28 .dopetask-pin
-rw-r--r--@ 1 hue  staff     0 Jun 11 17:28 .dopetaskroot
-rwxr-xr-x@ 1 hue  staff  2416 Jun 11 17:28 scripts/dopetask
-rwxr-xr-x@ 1 hue  staff   164 Jun 11 17:28 scripts/taskx
#!/usr/bin/env bash
set -euo pipefail

# --- Configuration ---
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXPECTED_PROJECT_ID="dopemux-mvp"
VENV="$REPO_ROOT/.dopetask_venv"
VERSION_MARKER="$VENV/.dopetask_version"
PIN_FILE="$REPO_ROOT/.dopetask-pin"

# --- Authority Rails ---
if [[ ! -f "$REPO_ROOT/.dopetaskroot" ]]; then
  echo "ERROR: .dopetaskroot missing in repo root: $REPO_ROOT" >&2
  exit 2
fi

if [[ ! -f "$PIN_FILE" ]]; then
  echo "ERROR: .dopetask-pin missing in repo root" >&2
  exit 2
fi

# Parse pin
INSTALL_METHOD=""
DEP_NAME=""
TARGET_VERSION=""
while IFS='=' read -r key value; do
  case "$key" in
    install) INSTALL_METHOD="$value" ;;
    dep) DEP_NAME="$value" ;;
    version) TARGET_VERSION="$value" ;;
  esac
done < "$PIN_FILE"

if [[ "$INSTALL_METHOD" != "pip" && "$INSTALL_METHOD" != "uv" ]]; then
  echo "ERROR: Invalid install method in .dopetask-pin: $INSTALL_METHOD" >&2
  exit 2
fi

if [[ -z "$DEP_NAME" || -z "$TARGET_VERSION" ]]; then
  echo "ERROR: Malformed .dopetask-pin (missing dep or version)" >&2
  exit 2
fi

# --- Venv & Install Management ---
mkdir -p "$VENV"
if [[ ! -d "$VENV/bin" ]]; then
  python3 -m venv "$VENV"
fi

CURRENT_INSTALLED=""
if [[ -f "$VERSION_MARKER" ]]; then
  CURRENT_INSTALLED="$(cat "$VERSION_MARKER" | tr -d '[:space:]')"
fi

install_dopetask() {
  echo "INFO: Installing $DEP_NAME==$TARGET_VERSION via $INSTALL_METHOD..."
  source "$VENV/bin/activate"

  if [[ "$INSTALL_METHOD" == "uv" ]] && command -v uv &> /dev/null; then
    uv pip install "$DEP_NAME==$TARGET_VERSION"
  else
    if [[ "$INSTALL_METHOD" == "uv" ]]; then
      echo "WARN: uv requested but not found, falling back to pip" >&2
    fi
    pip install --quiet --upgrade pip
    pip install --quiet "$DEP_NAME==$TARGET_VERSION"
  fi

  echo "$TARGET_VERSION" > "$VERSION_MARKER"
}

# Re-install on drift
if [[ "$CURRENT_INSTALLED" != "$TARGET_VERSION" ]]; then
  install_dopetask
fi

# Ensure executable exists
if [[ ! -x "$VENV/bin/dopetask" ]]; then
  install_dopetask
fi

# --- Execution ---
source "$VENV/bin/activate"

# Special handling for 'doctor' (known branch enforcement in 0.5.x)
if [[ "${1:-}" == "doctor" ]]; then
  set +e
  "$VENV/bin/dopetask" "$@"
  EXIT_CODE=$?
  set -e
  if [[ $EXIT_CODE -ne 0 ]]; then
    echo "HINT: dopetask doctor may fail on non-main branches in 0.5.x." >&2
  fi
  exit $EXIT_CODE
fi

exec "$VENV/bin/dopetask" "$@"
#!/usr/bin/env bash
set -euo pipefail

# Compatibility shim during taskx -> dopetask transition.
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/dopetask" "$@"
install=pip
dep=dopetask
version=0.5.1

## executable commands skipped
SKIPPED: ./scripts/dopetask --help, doctor, dopemux --help, compile-tasks --help, run-task --help, collect-evidence --help, gate-allowlist --help, promote-run --help, commit-run --help, spec-feedback --help, loop --help, tp --help.
Reason: Pack scope says no Dopetask execution and no dependency install. scripts/dopetask bootstraps .dopetask_venv and installs pinned external dopetask when absent/drifted.
OBSERVED .dopetask_venv absent
