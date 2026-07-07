# Orchestrator Load-Plan — DMX-BACKLOG-2026-07-07

**Status**: LOAD-PLAN ONLY — **not executed against the live task-orchestrator** (per operator decision). Machine-readable source: [`loadplan.json`](loadplan.json). Packets: [`README.md`](README.md). Decisions: [`decisions-ledger.md`](decisions-ledger.md).

**Contents**: 1 root · 9 epics (series) · 52 leaves (packets) · 28 BLOCKS edges. Items load as `QUEUE`; the BLOCKS DAG makes `get_blocked_items` derive blocked state — no pre-set BLOCKED role needed.

## How to load (operator runs these against the task-orchestrator MCP)

```
1. create_work_tree  ← root + epics + leaves from loadplan.json (root→epics→leaves via parent refs)
2. manage_dependencies (action=create) ← one BLOCKS edge per pair in loadplan.json.blocks: [blocker, blocked]
3. verify: query_items (count==52) · query_dependencies (==28) · get_blocked_items (decision/dep-gated show blocked) · get_next_item (returns a ready Tier-B leaf)
```

## Epics (series) & leaves

### DMX-MCF (8)

| Packet | disp | Target |
|---|---|---|
| `DMX-MCF-002-transcript-ingest` | BUILD | Build a one-shot, idempotent transcript-file ingest adapter that parses Claude Code session transcript JSONL into turn e |
| `DMX-MCF-003-decision-candidate` | BUILD | Add the conversation.decision_candidate event type end-to-end through the existing capture-to-promotion pipeline (both a |
| `DMX-MCF-004-sessionstart-recap` | BUILD | Extend the existing native_hooks.py SessionStart injection path with a bounded, token-budgeted, authority-labeled Top-3  |
| `DMX-MCF-005-semantic-projection-spec` | SPEC | Produce the semantic-memory projection spec for a derived dope-context memory_{hash} collection (privacy-safe embedding  |
| `DMX-MCF-006-conport-graph-spike-spec` | SPEC | Run the mandatory AGE data-layer spike against the active Docker ConPort runtime, then produce the spec for graph.neighb |
| `DMX-MCF-007-fabric-orchestrator-spec` | SPEC | Spec the Fabric orchestrator and its context.recall / context.recap MCP surface, fusing whichever retrieval modalities ( |
| `DMX-MCF-008-summarizer-spec` | SPEC | Spec the LLM summarization worker that distills candidate-only conversation-derived content using a cheap default model  |
| `DMX-MCF-009-proactive-injection-spec` | SPEC | Spec proactive mid-session context injection (Injection Phase 2) built on top of the Fabric orchestrator, gated by a rat |

### DMX-FLEET-P0 (7)

| Packet | disp | Target |
|---|---|---|
| `DMX-FLEET-P0-001-real-healthchecks` | BUILD | Prove that every MCP server healthcheck in the fleet is a real capability probe (non-2xx/unreachable = unhealthy) and ad |
| `DMX-FLEET-P0-002-ensure-pal-managed` | BUILD | Bring the load-bearing off-compose pal-mcp-server container fully under managed startup: add a real MCP capability healt |
| `DMX-FLEET-P0-003-conport-schema-verify-failclosed` | WIRE | Verify that ConPort's _ensure_schema post-apply verification is fail-closed (raises, does not silently proceed, on an un |
| `DMX-FLEET-P0-004-registry-dedup` | DELETE | Remove the competing PAL registry entries in src/dopemux/mcp/registry.yaml (dopemux-pal via uvx pal-mcp-server vs dopemu |
| `DMX-FLEET-P0-005-wrapper-path-fixes` | BUILD | Fix the three broken MCP stdio wrapper scripts under scripts/mcp-wrappers/: conport-wrapper.sh and conport-codex-wrapper |
| `DMX-FLEET-P0-006-quarantine-killlist` | BUILD | Quarantine the remaining startable kill-list dead code (services/mcp-integration-bridge, services/router, services/mcp-c |
| `DMX-FLEET-P0-007-desktop-commander-upstream` | REBUILD | Replace the broken desktop-commander container facade (docker/mcp-servers-source/desktop-commander/server.py, which call |

### DMX-FLEET-P1 (7)

| Packet | disp | Target |
|---|---|---|
| `DMX-FLEET-P1-001-unified-catalog-spec` | SPEC | Produce a spec that closes the residual multi-registry drift: current origin/main already has a schema-validated fleet c |
| `DMX-FLEET-P1-002-codegen-pipeline-spec` | SPEC | Produce a spec that closes the residual codegen gap: src/dopemux/mcp/fleet_catalog.py already renders .mcp.json, a Codex |
| `DMX-FLEET-P1-003-mcp-ensure-command` | SPEC | Produce a spec that closes the residual gap in `dopemux mcp ensure`: the command already exists on origin/main (src/dope |
| `DMX-FLEET-P1-004-ci-drift-gates` | BUILD | Close the residual CI-drift-gate gap: tests/arch/test_mcp_fleet_catalog_contract.py already gates catalog-schema conform |
| `DMX-FLEET-P1-005-orchestrator-autostart` | SPEC | Spec auto-starting the task-orchestrator singleton at session start and refreshing its repo truth-pack to the deployed v |
| `DMX-FLEET-P1-006-exa-retire-cleanup` | RETIRE | Finish the exa retirement (ADR-223, already merged to origin/main via commit 65313194a and enforced by tests/arch/test_m |
| `DMX-FLEET-P1-007-token-truncation-utility-spec` | SPEC | Spec restoring the lost progressive-token-truncation pattern (docs/archive/mcp-servers/CONPORT_TOKEN_LIMIT_FIX.md: item- |

### DMX-FLEET-P2 (5)

| Packet | disp | Target |
|---|---|---|
| `DMX-FLEET-P2-001-event-source-wiring` | WIRE | Produce the spec for wiring decision.logged/task.*/workflow.phase_changed at their real emission sources (ConPort decisi |
| `DMX-FLEET-P2-002-heartbeat-ratelimit` | BUILD | Rate-limit session-active heartbeat events in the dope-memory eventbus consumer to stop chronicle spam, and normalize/ba |
| `DMX-FLEET-P2-003-instance-identity-propagation` | SPEC | Produce the spec for moving workspace/instance identity into per-request parameters (tool arguments or headers) so workt |
| `DMX-FLEET-P2-004-skill-mirror-receipts` | BUILD | Append a dope-memory mirror-receipt confirmation to the /decision, /caveat, and /followup skill commands so each ConPort |
| `DMX-FLEET-P2-005-dopecontext-indexing-enable` | BUILD | Flip ENABLE_DOPECONTEXT_INDEX=true with provenance pointers once the chronicle holds real curated content, completing th |

### DMX-FLEET-P3 (6)

| Packet | disp | Target |
|---|---|---|
| `DMX-FLEET-P3-001-conport-jsonrpc-parity` | SPEC | Produce a spec for ConPort packets 106/107/201/202 that closes JSON-RPC tool parity (13 of 17 SSE tools currently advert |
| `DMX-FLEET-P3-002-serena-promotion` | WIRE | Produce a spec that promotes the local 45-tool Serena candidate (services/serena/) to the canonical Serena surface per D |
| `DMX-FLEET-P3-003-complexity-unify-spec` | SPEC | Produce a spec that picks the canonical complexity scorer among the three unwired implementations (Serena's CodeComplexi |
| `DMX-FLEET-P3-004-qdrant-gc` | DELETE | Add garbage collection for orphaned dope-context Qdrant collections (code_{workspace_hash}/docs_{workspace_hash}) whose  |
| `DMX-FLEET-P3-005-voyage-cost-guard` | WIRE | Wire the existing but dead rate_limits.voyage_api config (multi_index_config.yaml) into VoyageEmbedder and VoyageReranke |
| `DMX-FLEET-P3-006-loopback-binds` | BUILD | Close 0.0.0.0 exposure fleet-wide for conport, dope-memory, serena, and gptr-mcp by adding loopback-bind port publishing |

### DMX-FLEET-P4 (5)

| Packet | disp | Target |
|---|---|---|
| `DMX-FLEET-P4-001-facade-g1-contract-test` | WIRE | Close DCP read-only facade gap G1 by adding a CI contract test that asserts the MCP-registered tool set equals TOOL_CONT |
| `DMX-FLEET-P4-002-dopecontext-bridge-spec` | SPEC | Spec a minimal MCP-JSON-RPC read bridge that lets the DCP read-only facade's dope-context adapter issue real search_code |
| `DMX-FLEET-P4-003-lane-engine-wire` | WIRE | Wire the currently dead-code decide_lane() function into a real dispatch point (a `dopemux dcp lane` CLI subcommand plus |
| `DMX-FLEET-P4-004-inventory-freshness-gate` | WIRE | Add a CI verification that fails when the DCP facade's backend-surface inventory (RUNTIME_SURFACE_INVENTORY.md / READ_ON |
| `DMX-FLEET-P4-005-facade-catalog-register` | WIRE | Register dcp-readonly-facade as an operator-run stdio entry in the unified MCP catalog, closing the gap where the facade |

### DMX-FLEET-P5 (3)

| Packet | disp | Target |
|---|---|---|
| `DMX-FLEET-P5-001-e2e-acceptance` | SPEC | Spec the end-to-end fleet acceptance test: from a fresh worktree, `dopemux mcp ensure` brings every plane green, a decis |
| `DMX-FLEET-P5-002-docs-reconciliation` | WIRE | Regenerate the fleet's per-server doctrine docs (~/.claude/MCP_*.md sources and their in-repo equivalents) to match live |
| `DMX-FLEET-P5-003-proof-discipline` | BUILD | Establish a per-packet proof-bundle template and a checker script under proof/ that verifies every proof bundle contains |

### DMX-ADHD-WIRE (6)

| Packet | disp | Target |
|---|---|---|
| `DMX-ADHD-WIRE-001-predictive-risk-hook` | WIRE | Wire the built-but-dormant predictive_risk_assessment.py into the task-orchestrator runtime path so its 8 risk categorie |
| `DMX-ADHD-WIRE-002-context-preservation-display` | WIRE | Surface the live adhd_engine/domains/attention/context_preserver.py output (pre-break mental-model snapshots) on a real  |
| `DMX-ADHD-WIRE-003-overwhelm-snapshot` | WIRE | Expose the existing overwhelm-detection telemetry already computed inside event_coordinator.py as a queryable snapshot o |
| `DMX-ADHD-WIRE-004-relationship-vocab-widening` | WIRE | Widen the active ConPort MCP server's exposed relationship vocabulary beyond the current link_conport_items generic edge |
| `DMX-ADHD-WIRE-005-adaptive-learning-resurrect-spec` | SPEC | Produce a spec for resurrecting the dormant Serena Adaptive Learning Engine foundation (per-user attention patterns, cro |
| `DMX-ADHD-WIRE-006-fatigue-contextswitch-resurrect-spec` | SPEC | Produce a spec for resurrecting the dormant Serena Fatigue Detection Engine, Context Switching Optimizer, Untracked Work |

### DMX-ADR (5)

| Packet | disp | Target |
|---|---|---|
| `DMX-ADR-001-semantic-memory-home` | ADR | Author docs/90-adr/adr-224-semantic-memory-home.md recording the accepted decision that semantic memory lives in dope-co |
| `DMX-ADR-002-serena-promotion` | ADR | Author docs/90-adr/adr-225-serena-promotion.md recording the accepted decision to promote the local 45-tool Serena surfa |
| `DMX-ADR-003-lane-engine-dispatch` | ADR | Author docs/90-adr/adr-226-lane-engine-dispatch.md recording the accepted decision to wire decide_lane() as the real DCP |
| `DMX-ADR-004-complexity-scorer` | ADR | Author docs/90-adr/adr-227-complexity-scorer.md recording the accepted decision to unify the three unwired complexity-sc |
| `DMX-ADR-005-conport-graph-exposure` | ADR | Author docs/90-adr/adr-228-conport-graph-exposure.md recording the accepted decision to expose graph.neighbors plus deci |

## Dependency edges (BLOCKS: blocker → blocked)

```
DMX-ADHD-WIRE-005-adaptive-learning-resurrect-spec  →  DMX-ADHD-WIRE-006-fatigue-contextswitch-resurrect-spec
DMX-ADR-001-semantic-memory-home  →  DMX-MCF-005-semantic-projection-spec
DMX-ADR-002-serena-promotion  →  DMX-FLEET-P3-002-serena-promotion
DMX-ADR-003-lane-engine-dispatch  →  DMX-FLEET-P4-003-lane-engine-wire
DMX-ADR-004-complexity-scorer  →  DMX-FLEET-P3-003-complexity-unify-spec
DMX-ADR-005-conport-graph-exposure  →  DMX-MCF-006-conport-graph-spike-spec
DMX-FLEET-P0-002-ensure-pal-managed  →  DMX-FLEET-P1-003-mcp-ensure-command
DMX-FLEET-P0-004-registry-dedup  →  DMX-FLEET-P1-001-unified-catalog-spec
DMX-FLEET-P1-001-unified-catalog-spec  →  DMX-FLEET-P1-002-codegen-pipeline-spec
DMX-FLEET-P1-001-unified-catalog-spec  →  DMX-FLEET-P1-003-mcp-ensure-command
DMX-FLEET-P1-001-unified-catalog-spec  →  DMX-FLEET-P4-005-facade-catalog-register
DMX-FLEET-P1-002-codegen-pipeline-spec  →  DMX-FLEET-P1-004-ci-drift-gates
DMX-FLEET-P1-003-mcp-ensure-command  →  DMX-FLEET-P5-001-e2e-acceptance
DMX-FLEET-P2-001-event-source-wiring  →  DMX-FLEET-P2-005-dopecontext-indexing-enable
DMX-FLEET-P2-005-dopecontext-indexing-enable  →  DMX-FLEET-P5-001-e2e-acceptance
DMX-FLEET-P3-001-conport-jsonrpc-parity  →  DMX-ADHD-WIRE-004-relationship-vocab-widening
DMX-FLEET-P3-002-serena-promotion  →  DMX-ADHD-WIRE-005-adaptive-learning-resurrect-spec
DMX-FLEET-P3-002-serena-promotion  →  DMX-ADHD-WIRE-006-fatigue-contextswitch-resurrect-spec
DMX-FLEET-P4-001-facade-g1-contract-test  →  DMX-FLEET-P4-004-inventory-freshness-gate
DMX-MCF-002-transcript-ingest  →  DMX-MCF-003-decision-candidate
DMX-MCF-002-transcript-ingest  →  DMX-MCF-007-fabric-orchestrator-spec
DMX-MCF-003-decision-candidate  →  DMX-MCF-004-sessionstart-recap
DMX-MCF-003-decision-candidate  →  DMX-MCF-007-fabric-orchestrator-spec
DMX-MCF-003-decision-candidate  →  DMX-MCF-008-summarizer-spec
DMX-MCF-004-sessionstart-recap  →  DMX-MCF-005-semantic-projection-spec
DMX-MCF-004-sessionstart-recap  →  DMX-MCF-007-fabric-orchestrator-spec
DMX-MCF-007-fabric-orchestrator-spec  →  DMX-MCF-008-summarizer-spec
DMX-MCF-007-fabric-orchestrator-spec  →  DMX-MCF-009-proactive-injection-spec
```
