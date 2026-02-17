# PROMPT_E0 — EXECUTION inventory + partition plan

ROLE: Execution plane recon.
GOAL: find every "thing that starts things" and chunk sources into tractable partitions.

SCOPE TARGETS:
  • Makefile, justfile, package.json, pyproject.toml, scripts/, tools/, compose/, .github/, docker*, *.sh, *.ps1, *.zsh, tmux-layout.sh

OUTPUTS:
  • EXEC_INVENTORY.json (items[]: {path, kind, toolchain, invokes[], writes_outputs[]})
  • EXEC_PARTITIONS.json (partitions[]: {id, label, include_globs[], exclude_globs[], max_files_hint})

RULES:
  • No invention. Only enumerate files that exist inside scope.
  • Keep partition rules deterministic and minimize overlap.
