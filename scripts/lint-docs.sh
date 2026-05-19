#!/bin/bash
set -euo pipefail

# lint-docs.sh - Quick docs hygiene check
# Runs the key checks from  rules.
# Exit 0 = clean, Exit 1 = violations found.

DOCS_DIR="${1:-docs}"
VIOLATIONS=0
CHECKS=0

log_check() { echo "🔍 $1"; }
log_pass()  { echo "  ✅ $1"; }
log_fail()  { echo "  ❌ $1"; VIOLATIONS=$((VIOLATIONS + 1)); }
log_warn()  { echo "  ⚠️  $1"; }

# ── 1. No files in docs/ root (except allowed index files) ──────────
log_check "No loose files in docs/ root"
CHECKS=$((CHECKS + 1))
allowed_root="00-MASTER-INDEX.md INDEX.md docs_index.yaml  .DS_Store"
loose_files=()
while IFS= read -r f; do
  base=$(basename "$f")
  if ! echo "$allowed_root" | grep -qw "$base"; then
    loose_files+=("$f")
  fi
done < <(find "$DOCS_DIR" -maxdepth 1 -type f 2>/dev/null)

if [ ${#loose_files[@]} -eq 0 ]; then
  log_pass "No loose files in root"
else
  log_fail "${#loose_files[@]} loose files in docs/ root:"
  for f in "${loose_files[@]}"; do echo "    $f"; done
fi

# ── 2. Filename hygiene (delegated to canonical policy) ─────────────
# scripts/check_docs_filename_hygiene.py is the authoritative checker.
# It consumes config/docs_hygiene/docs_placement_policy.yaml exemptions
# (research/mcp-customization/**, Dopemux Cockpit TUI Design System/*,
# docs/archive/*, history/sourceFiles/*, etc.). lint-docs.sh historically
# used a naive `find` with only an archive/ exclusion and produced
# thousands of false-positives for content explicitly exempted by policy.
log_check "Filename hygiene (policy-aware)"
CHECKS=$((CHECKS + 1))
if python3 scripts/check_docs_filename_hygiene.py --check --all-files >/dev/null 2>&1; then
  log_pass "Filename hygiene policy passes"
else
  log_fail "Filename hygiene violations (run: python3 scripts/check_docs_filename_hygiene.py --check --all-files)"
fi

# ── 4. No .bak files ────────────────────────────────────────────────
log_check "No .bak files"
CHECKS=$((CHECKS + 1))
bak_count=$(find "$DOCS_DIR" -type f -name "*.bak" | wc -l | tr -d ' ')
if [ "$bak_count" -eq 0 ]; then
  log_pass "No .bak files"
else
  log_fail "$bak_count .bak files found"
fi

# ── 5. No directories exceeding 200 files (excluding quarantine) ────
log_check "No directories over 200 files"
CHECKS=$((CHECKS + 1))
over_limit=0
while IFS= read -r d; do
  count=$(find "$d" -maxdepth 1 -type f | wc -l | tr -d ' ')
  if [ "$count" -gt 200 ]; then
    log_fail "$d has $count files (max 200)"
    over_limit=$((over_limit + 1))
  fi
done < <(find "$DOCS_DIR" -type d -not -path "*/archive/*" -not -path "*/history/sourceFiles*" 2>/dev/null)

if [ "$over_limit" -eq 0 ]; then
  log_pass "All directories within 200-file limit"
fi

# ── 6. Frontmatter presence check (sample) ──────────────────────────
log_check "Frontmatter presence (active docs)"
CHECKS=$((CHECKS + 1))
no_fm=0
total_checked=0
while IFS= read -r f; do
  total_checked=$((total_checked + 1))
  first_line=$(head -1 "$f" 2>/dev/null)
  if [ "$first_line" != "---" ]; then
    if [ $no_fm -lt 5 ]; then echo "    Missing frontmatter: $f"; fi
    no_fm=$((no_fm + 1))
  fi
done < <(find "$DOCS_DIR" -type f -name "*.md" -not -path "*/archive/*" -not -path "*/history/sourceFiles/*" -not -name "00-MASTER-INDEX.md" -not -name "INDEX.md" -not -name "" 2>/dev/null)

if [ "$no_fm" -eq 0 ]; then
  log_pass "All $total_checked active docs have frontmatter"
else
  log_warn "$no_fm of $total_checked active docs missing frontmatter"
fi

# ── Summary ─────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$VIOLATIONS" -eq 0 ]; then
  echo "✅ All $CHECKS checks passed"
  exit 0
else
  echo "❌ $VIOLATIONS of $CHECKS checks failed"
  exit 1
fi
