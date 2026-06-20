# Command Log — TP-DMX-MEMORY-TRINITY-001 Local Audit

**Date**: 2026-06-19  
**Branch**: `fix/mcp-server-build-failures`  
**HEAD**: `a1690402b86f9304efb4da5068c03118239c1b4e`  
**Auditor**: Codex (read-only)

---

## Git preflight

### `git rev-parse --show-toplevel` → exit 0
```
/Users/hue/code/dopemux-mvp
```

### `git remote -v` → exit 0
```
mvp	https://github.com/DDD-Enterprises/dopemux-mvp.git (fetch)
mvp	https://github.com/DDD-Enterprises/dopemux-mvp.git (push)
origin	https://github.com/DDD-Enterprises/dopemux-mvp.git (fetch)
origin	https://github.com/DDD-Enterprises/dopemux-mvp.git (push)
```

### `git branch --show-current` → exit 0
```
fix/mcp-server-build-failures
```

### `git rev-parse HEAD` → exit 0
```
a1690402b86f9304efb4da5068c03118239c1b4e
```

### `git status --porcelain=v1` → exit 0
```
?? audit_inputs/open_pr_merge_train_2026_06_19/
```
(At audit time; proof artifacts modified afterward.)

---

## Validators

### `python3 scripts/validate_memory_command_refs.py` → exit 0
```
OK: no forbidden memory refs in .claude/commands
```

### `python3 scripts/validate_skill_frontmatter.py` → exit 0
```
OK: 20 skills have name+description frontmatter
```

---

## Docker / MCP runtime

### `docker ps --filter name=dope-context` → exit 0
```
mcp-dope-context	Up 2 hours (healthy)	127.0.0.1:3010->3010/tcp
```

### MCP initialize curl → exit 0
```bash
curl -sS -X POST http://127.0.0.1:3010/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"audit","version":"1.0"}}}'
```
```
http_code:200
event: message
data: {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","capabilities":{...},"serverInfo":{"name":"dope-context","version":"3.4.2"}}}
```

### `~/.claude.json` dope-context singleton → exit 0
```json
{
  "type": "http",
  "url": "http://localhost:3010/mcp",
  "description": "AST-aware semantic code & docs search; per-call workspace_path"
}
```
(Redacted: full file has other servers; no secrets in dope-context entry.)

### Related containers (observed)
```
mcp-dope-context      Up 2 hours (healthy)
task-orchestrator-dopemux-mvp-2e346e2084bca021  Up 8 hours
mcp-conport           Up 46 hours (healthy)
dopemux-dope-memory-1 Up 46 hours (healthy)
```

### `docker port mcp-conport` → exit 0
```
3004/tcp -> 0.0.0.0:3004
3005/tcp -> 0.0.0.0:3005
4004/tcp -> 0.0.0.0:4004
```

### `docker port dopemux-dope-memory-1` → exit 0
```
3020/tcp -> 0.0.0.0:3020
```

### `docker port task-orchestrator-dopemux-mvp-2e346e2084bca021` → exit 0
```
7890/tcp -> 127.0.0.1:7890
```

---

## mcp doctor

### Unsourced env → exit 1
```bash
PYTHONPATH=src python -m dopemux.cli mcp doctor
```
```
4 issue(s) found:
[TELEMETRY]   • `conport`: nothing listening on :3039 (start the container?).
[TELEMETRY]   • `dope-memory`: nothing listening on :3054 (start the container?).
[TELEMETRY]   • `task-orchestrator`: required env `TASK_ORCHESTRATOR_PROJECT_ROOT` is unset.
[TELEMETRY]   • `task-orchestrator`: env `TASK_ORCHESTRATOR_HTTP_PORT` is unset (source the .envrc?).
```

### Sourced `.envrc.dopemux-mcp` + task-orchestrator env → exit 1
```bash
source .envrc.dopemux-mcp
export TASK_ORCHESTRATOR_PROJECT_ROOT=/Users/hue/code/dopemux-mvp
export TASK_ORCHESTRATOR_HTTP_PORT=7890
PYTHONPATH=src python -m dopemux.cli mcp doctor
```
```
2 issue(s) found:
[TELEMETRY]   • `conport`: nothing listening on :3039 (start the container?).
[TELEMETRY]   • `dope-memory`: nothing listening on :3054 (start the container?).
```

### Worktree env ports (from `.envrc.dopemux-mcp`)
```
CONPORT_MCP_PORT=3039
DOPE_MEMORY_PORT=3054
```
Containers bound to `3005` (conport MCP) and `3020` (dope-memory) — **port drift**.

### `curl http://127.0.0.1:3039/sse` → exit 7
```
curl: (7) Failed to connect to 127.0.0.1 port 3039
```

---

## Branch vs main

### `git show origin/main:.claude/modules/shared/memory-trinity-routing.md` → exit 128
```
fatal: path '.claude/modules/shared/memory-trinity-routing.md' exists on disk, but not in 'origin/main'
```

### `git show origin/main:scripts/validate_memory_command_refs.py` → exit 128
```
fatal: path 'scripts/validate_memory_command_refs.py' exists on disk, but not in 'origin/main'
```

---

## Inventory counts

### `tm:*` commands → 0
```bash
find .claude/commands -path '*/tm/*' -name '*.md' | wc -l
# 0
rg -c 'tm:' .claude/commands
# rg_tm_matches=0
git log --oneline -1 -- .claude/commands/tm
# 2bab19203 feat(memory): PAL-gated skills remediation slices 002-004
```

### D3 — docs_index.yaml vs templates → exit 0
```bash
python3 -c "import yaml; from pathlib import Path; d=yaml.safe_load(open('docs/docs_index.yaml')); skills=d['skills']; tpl=list(Path('templates/skills').rglob('SKILL.md')); print(len(skills), len(tpl), [v for v in skills.values() if not Path(v).is_file()])"
# 20 20 []
```

### D2 — skills directory probe → exit 0
```bash
test -d .claude/skills || echo claude_skills_dir=ABSENT
test -d .github/skills || echo github_skills_dir=ABSENT
# claude_skills_dir=ABSENT
# github_skills_dir=ABSENT
```

### D2 — sync dry-run (proves target paths) → exit 0
```bash
python3 scripts/skills/sync_repo_skills.py --target claude --dry-run | head -3
```
```
[dry-run] sync .../templates/skills/testgen -> .../.claude/skills/testgen
[dry-run] sync .../templates/skills/testgen-gemini -> .../.claude/skills/testgen-gemini
[dry-run] sync .../templates/skills/testgen-copilot -> .../.claude/skills/testgen-copilot
```
Source mapping: `scripts/skills/sync_repo_skills.py:61-76` (`claude` → `.claude/skills`, `github` → `.github/skills`).
Catalog sync pointer: `docs/docs_index.yaml:175` (`skills_sync: scripts/skills/sync_repo_skills.py`).