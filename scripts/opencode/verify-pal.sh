#!/usr/bin/env bash
#
# Script: verify-pal.sh
# Purpose: Validate that PAL is correctly wired into OpenCode
#
# Usage:
#   ./scripts/opencode/verify-pal.sh
#
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

echo "🔍 Verifying PAL wiring for OpenCode..."

# 1. Config file exists
if [[ ! -f opencode.jsonc ]]; then
  echo "❌ opencode.jsonc not found"
  exit 1
fi
echo "✅ opencode.jsonc exists"

# 2. PAL guide exists
if [[ ! -f config/instructions/pal-opencode-guide.md ]]; then
  echo "❌ pal-opencode-guide.md not found"
  exit 1
fi
echo "✅ PAL behavior guide exists"

# 3. Agents exist
if [[ ! -f .opencode/agents/pal-planner.md ]]; then
  echo "❌ pal-planner.md not found"
  exit 1
fi
if [[ ! -f .opencode/agents/pal-reviewer.md ]]; then
  echo "❌ pal-reviewer.md not found"
  exit 1
fi
echo "✅ PAL agents exist"

# 4. Verify script itself
if [[ ! -x "$0" ]]; then
  echo "⚠️  verify-pal.sh is not executable (run: chmod +x $0)"
fi

# 5. Check OpenCode can see the config (best effort)
if command -v opencode >/dev/null 2>&1; then
  echo "🔎 Running opencode debug config..."
  opencode debug config > /tmp/opencode-config.txt 2>/dev/null || true

  if grep -q '"pal"' /tmp/opencode-config.txt; then
    echo "✅ PAL server present in resolved OpenCode config"
  else
    echo "⚠️  Could not confirm 'pal' in opencode debug config (may still work)"
  fi
else
  echo "⚠️  opencode CLI not found in PATH — skipping runtime config check"
fi

echo ""
echo "🎯 Next manual smoke test:"
echo "   opencode run \"Use pal_listmodels and report available models. Do not edit files.\""
echo ""
echo "✅ Basic wiring verification complete."
