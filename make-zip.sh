#!/usr/bin/env zsh
set -e
setopt NULL_GLOB

PKG="docs/03-reference/Dopemux Cockpit TUI Design System"
WT="docs/03-reference/.claude/worktrees/jovial-hellman-c3848d/docs/03-reference/Dopemux Cockpit TUI Design System"
OUT_DIR="/tmp/dopemux-cockpit-review-pack"
ZIP="/tmp/dopemux-cockpit-doctrine-review-pack.zip"

rm -rf "$OUT_DIR" "$ZIP"
mkdir -p "$OUT_DIR/current-package"
mkdir -p "$OUT_DIR/claude-worktree-draft"
mkdir -p "$OUT_DIR/references"
mkdir -p "$OUT_DIR/repo-state"
mkdir -p "$OUT_DIR/diffs"

DOCTRINE_FILES=(
  "ARCHITECTURE_SAFETY_OVERLAY.md"
  "PM_IMPLEMENTER_COCKPIT_REDIRECTION.md"
  "UX_REFERENCE_RECONCILIATION.md"
  "README.md"
  "PREIMPLEMENTATION.md"
  "ACCEPTANCE.md"
  "SKILL.md"
)

for f in "${DOCTRINE_FILES[@]}"; do
  if [[ -f "$PKG/$f" ]]; then
    cp "$PKG/$f" "$OUT_DIR/current-package/$f"
  else
    print "MISSING current-package/$f" > "$OUT_DIR/current-package/$f.MISSING.txt"
  fi

  if [[ -f "$WT/$f" ]]; then
    cp "$WT/$f" "$OUT_DIR/claude-worktree-draft/$f"
  else
    print "MISSING claude-worktree-draft/$f" > "$OUT_DIR/claude-worktree-draft/$f.MISSING.txt"
  fi
done

KEY_FILES=(
  "preview/03-status-chips.html"
  "preview/08-row-anatomy.html"
  "preview/09-authority-bridge.html"
  "preview/10-mode-bar.html"
  "preview/11-rails.html"
  "preview/18-inspector.html"
  "preview/20-cockpit-composition.html"
  "fonts/README.md"
  "ui_kits/cockpit/Primitives.jsx"
  "ui_kits/cockpit/Cockpit.jsx"
  "ui_kits/cockpit/README.md"
)

for f in "${KEY_FILES[@]}"; do
  if [[ -f "$PKG/$f" ]]; then
    mkdir -p "$OUT_DIR/current-package/${f:h}"
    cp "$PKG/$f" "$OUT_DIR/current-package/$f"
  else
    print "MISSING $PKG/$f" > "$OUT_DIR/current-package/${f:t}.MISSING.txt"
  fi
done

if [[ -f "docs/03-reference/gpt55_pm_implementer_redesign.md" ]]; then
  cp "docs/03-reference/gpt55_pm_implementer_redesign.md" "$OUT_DIR/references/gpt55_pm_implementer_redesign.md"
fi

if [[ -d "docs/ux" ]]; then
  mkdir -p "$OUT_DIR/references/docs-ux"
  for f in docs/ux/*.md; do
    [[ -f "$f" ]] && cp "$f" "$OUT_DIR/references/docs-ux/"
  done
fi

{
  print "pwd: $(pwd)"
  print ""
  print "git root:"
  git rev-parse --show-toplevel || true
  print ""
  print "git status --short:"
  git status --short || true
  print ""
  print "current package files:"
  find "$PKG" -maxdepth 4 -type f | sort || true
  print ""
  print "claude draft doctrine files:"
  find "$WT" -maxdepth 1 -type f | sort || true
} > "$OUT_DIR/repo-state/state.txt"

{
  print "=== stale doctrine / authority grep ==="
  rg -n "Bridge actions authority|Services authority: dopemux|command authority: dopemux|SRC=dopemux|UNKNOWN.?->.?EDGE|UNKNOWN.?→.?EDGE|UNKNOWN=EDGE|Every row carries SRC|every row in every pane|every row carries one" "$PKG" || true
  print ""
  print "=== PM/Implementer semantic grep ==="
  rg -n "PM|Implementer|PKT-|PKB-|handoff|handback|acceptance|evidence|workflow triage|current task|System Map|retrieval console|global search|search everything" "$PKG" || true
} > "$OUT_DIR/repo-state/grep-results.txt"

for f in "${DOCTRINE_FILES[@]}"; do
  if [[ -f "$PKG/$f" && -f "$WT/$f" ]]; then
    diff -u "$PKG/$f" "$WT/$f" > "$OUT_DIR/diffs/$f.diff" || true
  fi
done

cat > "$OUT_DIR/README_REVIEW_PACK.md" <<'EOF'
# Dopemux Cockpit Doctrine Review Pack

Purpose:
Compare the current design-system package files against the Claude-worktree corrected doctrine drafts and decide whether to overwrite, selectively merge, or patch.

Folders:
- current-package/ — files currently in docs/03-reference/Dopemux Cockpit TUI Design System/
- claude-worktree-draft/ — corrected doctrine drafts from docs/03-reference/.claude/worktrees/...
- references/ — GPT-5.5 Pro PM/Implementer reference and docs/ux reference files
- repo-state/ — git status, file inventory, grep evidence
- diffs/ — unified diffs current package vs Claude draft doctrine

Review goal:
Preserve valid package-specific content while removing stale rules:
- UNKNOWN→EDGE / UNKNOWN=EDGE
- Bridge actions authority
- Services authority: dopemux
- command authority: dopemux
- SRC=dopemux in chrome
- Every row carries SRC
EOF

(
  cd /tmp
  zip -qr "$ZIP" "${OUT_DIR:t}"
)

print "Created: $ZIP"
ls -lh "$ZIP"
