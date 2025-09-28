    #!/usr/bin/env bash
    set -euo pipefail
    repo_root="$(git rev-parse --show-toplevel)"
    mkdir -p "$repo_root/.git/hooks"

    # prepare-commit-msg hook to run aicommits if message is empty or placeholder
    cat > "$repo_root/.git/hooks/prepare-commit-msg" << 'HOOK'
#!/usr/bin/env bash
set -euo pipefail
MSG_FILE="$1"
COMMIT_SOURCE="${2-}"
SHA="${3-}"

# Do not run for merges or reverts
if [[ "${COMMIT_SOURCE:-}" == "merge" ]] || grep -qiE '^revert' "$MSG_FILE"; then
  exit 0
fi

# If message already has content (not just comments), skip
if grep -q '^[^#[:space:]]' "$MSG_FILE"; then
  exit 0
fi

# Require aicommits
if ! command -v aicommits >/dev/null 2>&1; then
  echo "aicommits not found; install with: npm i -g aicommits" >&2
  exit 0
fi

# Generate commit message with conventional format
AICOMMITS_CONVENTIONAL=true aicommits --force --config .aicommitsrc --generate > "$MSG_FILE" || true
HOOK
    chmod +x "$repo_root/.git/hooks/prepare-commit-msg"
    echo "Git hook installed: .git/hooks/prepare-commit-msg"
