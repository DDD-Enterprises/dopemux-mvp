import pathlib
roots = [
  ".claude/claude.md",
  ".claude/context.md",
  ".claude/WORKTREE_MCP_SETUP.md",
  "docs/03-reference/services/task-orchestrator.md",
  "docs/90-adr/ADR-203-task-orchestrator-un-deprecation.md"
]
for p in roots:
  pp = pathlib.Path(p)
  if not pp.exists():
    print(f"MISSING: {p}")
    continue
  try:
    txt = pp.read_text(errors="ignore").splitlines()
    print(f"\n=== {p} ===")
    for i,line in enumerate(txt[:220], start=1):
      print(f"{i:04d}:{line}")
  except Exception as e:
    print(f"ERROR reading {p}: {e}")
