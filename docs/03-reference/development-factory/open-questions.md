# Open Questions — Verification Gates

12 verification gates from the architecture synthesis. Each must be resolved before related packets can execute safely.

| Gate | Question | Blocks |
|------|----------|--------|
| VG-001 | `dopetask-canonical-spec.json` confirmed at `docs/03-reference/spec/dopetask/`? (recon found it; verify it is the authoritative source and not outdated) | `TP-DMX-DOPETASK-SPEC-RESTORE-001` |
| VG-002 | Is the Python `services/task-orchestrator/` FastAPI (port 8000) a live process? Is it invoked by any active code path? | `TP-DMX-ORCH-NAMING-BOUNDARY-001` |
| VG-003 | Which of the ~29 uninventoried `services/` directories are programmatically invoked by active code? | `TP-DMX-SERVICES-INVENTORY-001` |
| VG-004 | Is `services/monitoring-dashboard/` actually running (0.0.0.0:1561)? `docker ps` or netstat check required. | Security remediation |
| VG-005 | What is the call graph leading to `validate_pre_live_gate_v25.py:476-478`? Which tests exercise it? | `TP-RTE-S7-DRIFT-FIX-001` |
| VG-006 | What is the full definition of `LIVE_WRITE_READY`? Who can declare it true? Which system reads it? | `TP-DMX-LIVE-WRITE-READY-SCHEMA-001` |
| VG-007 | Is DCP-RED-MERGE-SEAM-0001 enforced in any executable code, or only in `schemas/dcp/README.md`? | `TP-DMX-DCP-SEAM-ENFORCEMENT-001` |
| VG-008 | How are `services/agents/` agent types invoked in production? Via dopemux CLI, task-orchestrator, or direct import? | `TP-DMX-AGENT-AUTHORITY-001` |
| VG-009 | Is task-orchestrator Kotlin MCP transport still stdio? Has the HTTP-singleton cutover been applied? | `TP-DMX-ORCH-NAMING-BOUNDARY-001` |
| VG-010 | Is `services/working-memory-assistant/main.py` (orphaned) safe to delete? Is it imported anywhere? | `TP-DMX-SERVICES-INVENTORY-001` |
| VG-011 | What is the relationship between `src/conport/memory_server.py` and `services/conport_kg/`? Same runtime or two builds? | `TP-DMX-SERVICES-INVENTORY-001` |
| VG-012 | Which `.claude/hooks/` scripts are confirmed active at session start vs dormant? Do any target non-existent endpoints? | `TP-DMX-EVIDENCE-GATE-VERIFY-001` |
