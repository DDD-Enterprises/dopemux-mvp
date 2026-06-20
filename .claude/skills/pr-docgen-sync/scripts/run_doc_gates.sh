#!/usr/bin/env bash
set -euo pipefail

repo_root="${1:-$(pwd)}"
fix_frontmatter="${FIX_FRONTMATTER:-0}"

cd "$repo_root"

echo "==> python scripts/docs_validator.py"
python scripts/docs_validator.py

echo "==> python scripts/docs_frontmatter_guard.py"
python scripts/docs_frontmatter_guard.py

if [[ "$fix_frontmatter" == "1" ]]; then
  echo "==> applying docs frontmatter fixes"
  python scripts/docs_frontmatter_guard.py --fix
  python scripts/docs_validator.py
fi

echo "==> python scripts/check_root_hygiene.py"
python scripts/check_root_hygiene.py

echo "All documentation gates passed."
