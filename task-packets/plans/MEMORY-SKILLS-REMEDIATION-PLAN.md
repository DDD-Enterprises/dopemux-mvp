# Memory Trinity & Skills Remediation Plan

**Series**: `DMX-MEMORY-TRINITY`
**Parent packet**: `TP-DMX-MEMORY-TRINITY-001`
**Date**: 2026-06-19
**PAL chain** (architecture-sensitive): `analyze → thinkdeep → challenge → planner → challenge → implement → codereview → precommit → challenge`

---

## Phase 0 — Ground truth (COMPLETE in slice 001)

| Item | Status | Evidence |
|------|--------|----------|
| Memory Trinity ADRs accepted | DONE | `docs/90-adr/adr-memory-trinity-*.md` |
| Routing card module | DONE | `.claude/modules/shared/memory-trinity-routing.md` |
| dope-context MCP alive | OBSERVED | `mcp-dope-context` healthy; initialize OK on :3010 |
| Memory command drift fix | DONE | ConPort/dope-context routing in `.claude/commands/` |
| Drift validator | DONE | `scripts/validate_memory_command_refs.py` |

---

## Phase 1 — PAL validation gate (run before further slices)

Execute PAL tools in order; save artifacts under `proof/TP-DMX-MEMORY-TRINITY-001/pal/`.

| Step | PAL tool | Input focus | Pass criteria |
|------|----------|-------------|---------------|
| 1 | `analyze` | Diff + ADR promotion + command rewrites | Evidence ledger cites file paths |
| 2 | `thinkdeep` | Cross-plane overwrite risks, search_all decision projection | Lists ≥3 failure modes |
| 3 | `challenge` | Attack "Memory Trinity is law" claim vs runtime | Finds drift or confirms clean |
| 4 | `planner` | Phases 2–5 below as commit-sized slices | Each slice has validation commands |
| 5 | `challenge` | Plan completeness, scope creep | ≤5 slices, no tm:* resurrection |
| 6 | `codereview` | After each implementation slice | Security + authority violations |
| 7 | `precommit` | Before PR | `git diff --check`, validator exit 0 |
| 8 | `challenge` | Final verdict | Residual risks explicit |

**Supervisor audit** (parallel, read-only): run `task-packets/prompts/SUPERVISOR-MEMORY-TRINITY-AUDIT.md` → `proof/.../AUDIT_REPORT.md`.

---

## Phase 2 — Slice: Skills install path (TP-DMX-MEMORY-TRINITY-002)

**Goal**: Repo skills discoverable by Claude/Copilot/Codex.

| Task | Validation |
|------|------------|
| Extend `sync_repo_skills.py` with `--target claude\|github\|codex\|all` | dry-run copies to `.claude/skills/` |
| Add frontmatter to `pr-merge-specialist`, `vibe-pr-merge` | `python3 scripts/validate_skill_frontmatter.py` (new) |
| Complete `docs/docs_index.yaml` skills index | diff matches 20 templates |
| Delete 57 `tm:*` commands | `find .claude/commands/tm -name '*.md' \| wc -l` → 0 |

---

## Phase 3 — Slice: dope-memory operator surface (TP-DMX-MEMORY-TRINITY-003)

**Goal**: Expose chronicle plane to operators.

| Task | Validation |
|------|------------|
| Add `/mem:recap` command wrapping dope-memory MCP | frontmatter + allowed-tools |
| Verify mirror receipts in `memory_writers.py` tests | `pytest tests/unit/orchestrator/test_memory_writers.py -q` |
| Document mirror PARTIAL semantics in routing card | grep `mirror_status` |

---

## Phase 4 — Slice: Enforcement automation (TP-DMX-MEMORY-TRINITY-004)

**Goal**: Prevent drift regression.

| Task | Validation |
|------|------------|
| Wire `validate_memory_command_refs.py` into pre-commit | hook runs on `.claude/commands/**` |
| Add `validate_skill_frontmatter.py` for `templates/skills/**/SKILL.md` | exit 0 on catalog |
| Optional: extend `validate_dx_surface.py` pattern for memory commands | pytest |

---

## Phase 5 — Slice: Docs dedup (TP-DMX-MEMORY-TRINITY-005)

**Goal**: Single canonical skill doc tree.

| Task | Validation |
|------|------------|
| Canonical: `docs/03-reference/skills/` only | archive duplicates |
| Redirect stubs in `docs/skills/` | `docs_audit` PASS |

---

## Verification matrix (run after each slice)

```bash
python3 scripts/validate_memory_command_refs.py
PYTHONPATH=src python -m dopemux.cli mcp doctor
docker ps --filter name=dope-context --format '{{.Status}}'
python3 -m pytest services/dope-context/tests/test_mcp_server.py -q --tb=no -x  # if env allows
git diff --check
```

---

## NOT_RUN / UNKNOWN (track explicitly)

- DCP facade MCP JSON-RPC bridge for dope-context (Phase 1 BLOCKED per facade)
- Live PAL tool execution in this session (artifacts path reserved)
- Branch protection on ci-summary (orthogonal)
- Full `search_all` with ConPort decision projection in live stack
