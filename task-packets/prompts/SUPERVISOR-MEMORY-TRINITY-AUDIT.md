---
id: SUPERVISOR-MEMORY-TRINITY-AUDIT
title: Supervisor Memory Trinity Audit
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-19'
last_review: '2026-06-19'
next_review: '2026-09-17'
prelude: Supervisor Memory Trinity Audit (explanation) for dopemux documentation and
  developer workflows.
---
# Supervisor Audit Prompt — Memory Trinity & Skills/Memory Remediation

**Series**: `DMX-MEMORY-TRINITY`
**Packet**: `TP-DMX-MEMORY-TRINITY-001` (parent) / slice audits as children
**Date**: 2026-06-19
**Role**: Supervisor (read-only audit; no implementation)

---

## Mission

Audit whether the Dopemux repository has **fully codified Memory Trinity as law** and whether **operator surfaces** (slash commands, skills, modules, MCP wiring) route operators to the correct canonical plane without dead-backend drift.

Produce a deterministic audit report with PASS / FAIL / NOT_RUN buckets. Do not collapse NOT_RUN into PASS.

---

## Authority order (mandatory)

1. Accepted ADRs (especially `adr-memory-trinity-authority-and-interaction-model.md` and child plane ADRs)
2. Runtime: `.mcp.json`, `~/.claude.json` mcpServers, `mcp_catalog.yaml`, `compose.yml`
3. `config/runtime_authority_manifest.json`
4. `.claude/commands/**`, `.claude/modules/**`, `templates/skills/**`
5. Docs (advisory only when runtime conflicts)

Mark unresolved items `UNKNOWN`. Never invent runtime behavior.

---

## Audit checklist

### A. Memory Trinity law

- [ ] All four ADRs show `status: accepted` in frontmatter AND `**Status:** Accepted` in body:
  - `adr-memory-trinity-authority-and-interaction-model.md`
  - `adr-conport-as-decision-progress-and-context-authority.md`
  - `adr-dope-memory-as-chronicle-memory-authority.md`
  - `adr-dope-context-as-search-and-retrieval-plane.md`
- [ ] `AGENTS.md` §6 cites Memory Trinity explicitly
- [ ] `.claude/modules/shared/memory-trinity-routing.md` exists and matches ADR object classes
- [ ] `authority-matrix.md` lists ConPort, dope-memory, dope-context (not Leantime as task authority)

### B. MCP wiring (observed runtime)

- [ ] `mcp-dope-context` container healthy on `127.0.0.1:3010`
- [ ] MCP `initialize` succeeds with `Accept: application/json, text/event-stream`
- [ ] `dope-context` present in `~/.claude.json` mcpServers (singleton)
- [ ] Per-worktree `.mcp.json` has `conport`, `dope-memory`, `task-orchestrator`
- [ ] `dopemux mcp doctor` — report per-server PASS/FAIL with env gaps noted

### C. Operator command drift

Run: `python3 scripts/validate_memory_command_refs.py`

- [ ] Exit 0 — no `openmemory`, `memory_bank`, `Mem0`, `Claude-Context` in active command bodies
- [ ] `/decision`, `/caveat`, `/followup`, `/scratch` → ConPort MCP tools
- [ ] `/ctx:search-here`, `/ctx:index-search` → dope-context MCP tools with frontmatter
- [ ] `/get-decisions`, `/search-decisions` unchanged (ConPort)

### D. Skills inventory

- [ ] `templates/skills/` — all `SKILL.md` have `name` + `description` frontmatter (flag exceptions)
- [ ] `.github/skills/` or `.claude/skills/` populated OR documented sync path (`scripts/skills/sync_repo_skills.py`)
- [ ] `docs/docs_index.yaml` skills section complete vs template count
- [ ] Count `tm:*` commands — target 0 post-remediation
- [ ] `templates/plugin/l0_membership.json` fleet deps still accurate

### E. Cross-plane enforcement surfaces

- [ ] `services/dope-context/src/mcp/server.py` — `TRINITY_BOUNDARY_MARKER` present in search_all responses
- [ ] `src/dopemux/orchestrator/memory_writers.py` — ConPort canonical + dope-memory mirror receipts
- [ ] DCP facade `dope_context.py` — document BLOCKED vs bridged status (NOT_RUN if transport gap remains)

### F. Residual risks

List top 5 risks with evidence paths. Examples:
- DCP facade cannot proxy dope-context JSON-RPC
- `search_all` decision projection misread as canonical
- Skill sync Codex-only
- Env not sourced (`.envrc.dopemux-mcp`)

---

## Required output artifacts

Write to `proof/TP-DMX-MEMORY-TRINITY-001/AUDIT_REPORT.md`:

```markdown
# Memory Trinity Supervisor Audit

## Verdict: PASS | FAIL | PARTIAL

## Summary (≤5 bullets)

## Checklist results (A–F)
| Section | Result | Evidence |
...

## Commands run (exit codes)

## UNKNOWNs

## Recommended next slices (ordered, max 5)
```

Also emit `AUDIT_REPORT.json`:
```json
{
  "verdict": "PASS|FAIL|PARTIAL",
  "checks": [{"id": "A1", "result": "PASS|FAIL|NOT_RUN", "evidence": "path:line"}],
  "unknowns": [],
  "next_slices": []
}
```

---

## Stop conditions

- Do not modify source files (audit only).
- Do not claim dope-context works without MCP initialize evidence.
- Do not approve if `validate_memory_command_refs.py` fails.
- Escalate if runtime ADR claims contradict observed MCP catalog.
