# Decision Record

Decisions made in the design conversation that produced this packet series.

| Decision | Rationale | Packet |
|----------|-----------|--------|
| DDF is a governed factory, not a mega-agent | Mega-agents drift authority, have no audit trail, and cannot be supervised. Factory model enforces scope, proof, and human checkpoints. | `TP-DMX-DDF-DOCS-001` |
| Current safe autonomy is L1/L2 only | LIVE_WRITE_READY undefined, S7 gate stub, agent authority unresolved, DCP-RED-MERGE-SEAM active. L3+ cannot safely run. | `TP-DMX-DDF-DOCS-001` |
| First implementation-ish packet after docs is evidence verification | Cannot write schemas or policies based on INFERRED/advisory evidence. Must verify key component statuses from runtime first. | `TP-DMX-EVIDENCE-GATE-VERIFY-001` |
| LIVE_WRITE_READY is not the first packet | It is packet 13 in the series. Prerequisites include RTE gate fixes, agent authority, and services inventory. | `TP-DMX-LIVE-WRITE-READY-SCHEMA-001` |
| Stage-based model routing is mandatory | Cheap models making architecture decisions is a root cause of hallucinated authority. Stage split is non-negotiable. | `TP-DMX-MODEL-ROUTING-POLICY-001` |
| Task-Orchestrator has two distinct surfaces | Kotlin MCP (14 tools, external Docker, stdio) vs Python FastAPI (port 8000, coordination REST). Same name, different systems. Boundary UNKNOWN. | `TP-DMX-ORCH-NAMING-BOUNDARY-001` |
| Obligation Ledger is mandatory | Work doesn't die silently. Every DEFERRED, BLOCKED, or PROOF_GAP must be tracked and cannot close without evidence. | `TP-DMX-OBLIGATION-LEDGER-001` |
| Execution Capsules replace loose packets | Loose packets lack authority constraints, scope enforcement, and model routing. Capsules are the atomic unit going forward. | `TP-DMX-EXECUTION-CAPSULE-SCHEMA-001` |
| PR Steward remains advisory | Track B mutation authority has not been formally activated. Steward emits readiness signals; merge requires supervisor sign-off. | All capsules |
| Agents are blocked from authority until decided and tested | Three competing families, zero test coverage for `services/agents/`. Cannot grant authority to untested, undeclared code. | `TP-DMX-AGENT-AUTHORITY-001` |

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
