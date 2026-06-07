---
id: open-questions
title: Open Questions
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-06'
last_review: '2026-06-06'
next_review: '2026-09-04'
prelude: Open Questions (reference) for dopemux documentation and developer workflows.
---
# Open Questions — Verification Gates

12 verification gates from the architecture synthesis. **Status reflects `TP-DMX-EVIDENCE-GATE-VERIFY-001` (read-only, HEAD `8042f9f9f`).** All findings are static-analysis + live `docker ps` only; none involved running the systems under test. "VERIFIED" means the question is answered to that confidence; it does not certify runtime correctness.

| Gate | Question | Status | Finding @ HEAD `8042f9f9f` | Next |
|------|----------|--------|----------------------------|------|
| VG-001 | `dopetask-canonical-spec.json` authoritative & not outdated? | **VERIFIED** (existence); freshness open | Exists at `docs/03-reference/spec/dopetask/`, valid JSON, referenced as canonical by `AGENTS.md`. Census "MISSING" was stale. | `TP-DMX-DOPETASK-SPEC-RESTORE-001` → verify canonical/freshness, not restore |
| VG-002 | Python TO FastAPI (port 8000) a live process? | **VERIFIED** | Source + compose-defined (port 8000); **not running** (`curl :8000` refused, no container). | `TP-DMX-ORCH-NAMING-BOUNDARY-001` |
| VG-003 | Which `services/` dirs are invoked by active code? | **STILL_UNKNOWN / PARTIAL** | 41 dirs / 23 compose services; 35 not in compose — but not-in-compose ≠ orphaned. Invocation graph still needed. | `TP-DMX-SERVICES-INVENTORY-001` |
| VG-004 | Is `monitoring-dashboard` running, and where? | **SECURITY_RISK** (latent) | Binds `0.0.0.0:8098` (NOT 1561 — line-number confusion), no auth on own endpoints, **not running**. | Security remediation when started |
| VG-005 | S7 truth-split gate call graph / always-PASS? | **CONFLICTING** (census stale) | `collect_truth_split` builds rows, classifies, emits blockers into `all_blockers`. Stub claim stale. Body read, gate NOT run. | `TP-RTE-S7-DRIFT-FIX-001` → verify-and-close |
| VG-006 | Full definition of `LIVE_WRITE_READY`? | **VERIFIED** (undefined) | No schema defines it; tests actively forbid defining it. `UNDEFINED_AND_BLOCKING`. **Unchanged true L4+ blocker.** | `TP-DMX-LIVE-WRITE-READY-SCHEMA-001` |
| VG-007 | DCP-RED-MERGE-SEAM enforced in code or docs-only? | **CONFLICTING** (code exists, unwired) | `RedLaneScanner` + rules + tests exist in `src/dopemux/dcp/`; **not** referenced by CI/steward/auditor/scripts. | `TP-DMX-DCP-SEAM-ENFORCEMENT-001` → wire existing scanner |
| VG-008 | How are `services/agents/` invoked in production? | **VERIFIED** | 2 co-located tests (not "zero"); **no active code imports `services.agents`**. Authority unwired. | `TP-DMX-AGENT-AUTHORITY-001` |
| VG-009 | TO Kotlin MCP transport — stdio or HTTP cutover? | **VERIFIED** (stdio) | `.mcp.json` `type:stdio`; wrapper `MCP_TRANSPORT=stdio`, `--rm` per-client; running container port 3001/tcp internal. HTTP cutover **not applied**. | `TP-DMX-ORCH-NAMING-BOUNDARY-001` |
| VG-010 | Is `working-memory-assistant/main.py` orphaned / safe to delete? | **CONFLICTING** (not orphan) | `main.py` (`WMAService`) imported by `trigger_manager.py`, `cache_manager.py`. **NOT safe to delete.** Census claim wrong. | `TP-DMX-SERVICES-INVENTORY-001` |
| VG-011 | `src/conport/memory_server.py` vs `services/conport_kg/`? | **VERIFIED** (partial) | Canonical ConPort = compose `conport` (`docker/mcp-servers/conport/Dockerfile`, 3004/3005). `services/conport_kg/` not referenced by compose/.mcp.json/src — orphaned/experimental. | `TP-DMX-SERVICES-INVENTORY-001` |
| VG-012 | Which `.claude/hooks/` are active vs dormant; wrong endpoints? | **VERIFIED** (non-functional) | `check_energy.sh`/`save_context.sh` target `localhost:8080` (= Leantime, not adhd-engine:3025); engine not running; `native_hooks.py` has no ADHD wiring. Hooks no-op. | ADHD remediation series |

**Summary:** 7 VERIFIED · 3 CONFLICTING (census stale: VG-005, VG-007, VG-010) · 1 SECURITY_RISK (VG-004) · 1 STILL_UNKNOWN (VG-003). VG-006 remains the true L4+ blocker.
