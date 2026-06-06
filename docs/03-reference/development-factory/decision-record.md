# Decision Record

Decisions made in the design conversation that produced this packet series.

| Decision | Rationale | Packet |
|----------|-----------|--------|
| DDF is a governed factory, not a mega-agent | Mega-agents drift authority, have no audit trail, and cannot be supervised. Factory model enforces scope, proof, and human checkpoints. | `TP-DMX-DDF-DOCS-001` |
| Current safe autonomy is L1/L2 only | `LIVE_WRITE_READY` undefined and DCP-RED-MERGE-SEAM active. Agent authority unresolved. S7/SP/seam implementations are present at HEAD but **unverified** (verify-and-close pending). L3+ cannot safely run until verification completes. | `TP-DMX-DDF-DOCS-001` |
| First implementation-ish packet after docs is evidence verification | Cannot write schemas or policies based on INFERRED/advisory evidence. Must verify key component statuses from runtime first. **Outcome: `TP-DMX-EVIDENCE-GATE-VERIFY-001` found several census claims stale (S7, SP, seam, monitoring port) — confirming the value of verify-before-build.** | `TP-DMX-EVIDENCE-GATE-VERIFY-001` |
| LIVE_WRITE_READY is not the first packet | Prerequisites include RTE verify-and-close, agent authority, and the services inventory. It remains the true L4+ blocker (VG-006: no schema defines it; tests forbid it). | `TP-DMX-LIVE-WRITE-READY-SCHEMA-001` |
| Stage-based model routing is mandatory | Cheap models making architecture decisions is a root cause of hallucinated authority. Stage split is non-negotiable. | `TP-DMX-MODEL-ROUTING-POLICY-001` |
| Task-Orchestrator has two distinct surfaces | Kotlin MCP (14 tools, external Docker, stdio) vs Python FastAPI (port 8000, coordination REST). Same name, different systems. Boundary UNKNOWN. | `TP-DMX-ORCH-NAMING-BOUNDARY-001` |
| Obligation Ledger is mandatory | Work doesn't die silently. Every DEFERRED, BLOCKED, or PROOF_GAP must be tracked and cannot close without evidence. | `TP-DMX-OBLIGATION-LEDGER-001` |
| Execution Capsules replace loose packets | Loose packets lack authority constraints, scope enforcement, and model routing. Capsules are the atomic unit going forward. | `TP-DMX-EXECUTION-CAPSULE-SCHEMA-001` |
| PR Steward remains advisory | Track B mutation authority has not been formally activated. Steward emits readiness signals; merge requires supervisor sign-off. | All capsules |
| Agents are blocked from authority until decided and tested | Three competing families, near-zero test coverage for `services/agents/` (VG-008: 2 co-located tests, no active imports). Cannot grant authority to untested, undeclared code. | `TP-DMX-AGENT-AUTHORITY-001` |
| **Docs are not source truth; when verification contradicts docs, docs must be patched before they can guide agents** | `TP-DMX-EVIDENCE-GATE-VERIFY-001` found the initial DDF docs contained materially stale claims (monitoring-dashboard port 1561→8098; S7/SP/seam framed as "missing" when implementation is present at HEAD `8042f9f9f`). Building automation on stale docs is the exact failure mode the evidence gate exists to prevent. A docs-correction trust-repair packet must precede further factory automation. | `TP-DMX-DDF-DOCS-CORRECT-001` |
| RTE S7 / SP / DCP seam are verify-and-close, not build-from-scratch | Implementation is present at HEAD for all three (S7 `collect_truth_split`→`all_blockers`; `SP_CONTRACT_MISSING` blocker; `RedLaneScanner` code). Re-implementing would duplicate working code and risk regression. The correct work is to verify existing behavior and wire/close. | `TP-RTE-S7-DRIFT-FIX-001`, `TP-RTE-SP-PHASE-CONTRACT-001`, `TP-DMX-DCP-SEAM-ENFORCEMENT-001` |

## Local Instruction Surfaces Consulted

| Surface | Actual Path | Notes |
|---------|-------------|-------|
| Project doctrine | `.claude/claude.md` | No root `CLAUDE.md` — `.claude/claude.md` is loaded by harness |
| Agent authority | `AGENTS.md` | Root-level, authoritative |
| Governance rules | `docs/03-reference/governance/rules.md` + `rules-2.md` | Two variants — canonical TBD |
| System boundaries | `docs/03-reference/systems/system-boundaries.md` | No root `SYSTEM_BOUNDARIES.md` |
| Dopetask schema | `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` | Found — verify canonical status |
| PAL chain rules | `AGENTS.md §5` | No standalone `PAL_*.md` files |
| Governance principles | `.claude/modules/shared/governance-principles.md` | Local copy; `~/.claude/GOVERNANCE_PRINCIPLES.md` is global fallback |
| Proof contract | `docs/03-reference/governance/proof-contract.md` | — |
| Proof bundle schema | `docs/03-reference/governance/proof-bundle-schema.md` | — |
| Handoff contract | `docs/03-reference/governance/handoff-contract.md` | — |
| Codex AGENTS | `.github/agents/dopemux-*.agent.md` | No root `CODEX.md` |
| Per-packet test map | `config/orchestrator/perpacket_test_map.yaml` | References missing spec — VG-001 |
