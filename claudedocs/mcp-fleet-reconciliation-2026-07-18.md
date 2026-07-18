# Dopemux MCP Fleet — Consolidated Reconciliation Report (2026-07-18)

**Status**: Anchor document for DMX-MCPINT phase P7 ("fleet hardening", component code `HRD`).
**Consolidates**: `claudedocs/mcp-fleet-canonical-audit-and-target-design-2026-07-03.md` (§8 Phase 0–5 roadmap), `claudedocs/mcp-fleet-forgotten-features-addendum-2026-07-04.md` (§3 shortlist, §5 fold-in), the 2026-07-07 chronicle runtime findings/proofs, and the 2026-07-10 ChatGPT MCP instance-resolution probe (`claudedocs/probes/chatgpt-mcp-instance-resolution-2026-07-10/`).
**Verification basis**: repo ground truth re-verified 2026-07-18 at `c91852665` (branch `fix/reserved-singleton-identity-probe`) and origin/main `415f28d95`; DMX-MCPINT program branch `claude/mcp-dopemux-integration-audit-877f32` @ `302729384` (PR #1073); live task-orchestrator queries against trees `af10eefd` (DMX-MCPINT) and `f64aa1a9` (DMX-SVCFEAT).

---

## 1. Executive summary

The 07-03 audit's Phase 0–5 roadmap is now **partially executed and partially packetized**. This report is the single reconciliation of (a) what is verifiably done, (b) what is already owned by an existing work item in DMX-MCPINT or DMX-SVCFEAT, and (c) the residual gaps. The residual gaps are packetized as **18 `DMX-MCPINT-HRD-*` task packets** loaded as phase **P7** under the DMX-MCPINT tree, gated by three new decision gates (**G6 ConPort vector boundary, G7 complexity federation ratification, G8 PM write-sync boundary**) that are resolved by PAL multi-model consensus packets before dependent work unblocks.

Nothing in this phase re-decides SVCFIN-, SVCFEAT-, or MCPINT-owned items; overlaps are handled with scope-extension notes and cross-tree BLOCKS edges (§6.2, §6.3).

## 2. Done-ledger (verified — excluded from packetization)

| Item (07-03/07-04 roadmap ref) | Evidence |
|---|---|
| Fake healthchecks fixed (pal, dope-context) | `compose.yml:294` (`curl -f …/health \|\| exit 1`), `compose.yml:380`; no `exit 0` no-ops remain |
| `src/dopemux/mcp/registry.yaml` duplicate keys | deduped; 9 unique keys |
| exa server disposition | fully retired — absent from `mcp_catalog.yaml`, `compose.yml`, both registries (the "catalog points at LiteLLM" defect is moot) |
| Dead code quarantine | `services/mcp-integration-bridge/` and `services/router/` deleted (`7f904d78e`) |
| `dopemux mcp ensure` (`--fast`/`--full`) | `src/dopemux/commands/mcp_commands.py:1078`; `--full` runs compose up, `ensure-pal.sh`, orchestrator singleton, capability probes |
| Catalog codegen (`dopemux mcp generate`) | `mcp_commands.py:857` → `fleet_catalog.generate_fleet_output_files()` (`src/dopemux/mcp/fleet_catalog.py:288`); spec `docs/03-reference/mcp/fleet-generated-outputs.md` |
| Catalog↔`.mcp.json` drift check | `fleet_catalog.py:601-606`; `tests/unit/test_mcp_commands_catalog.py` |
| Facade 12-tool contract exposure | all 12 registered in `services/dcp-readonly-facade/src/dcp_facade/tools.py` (2 return BLOCKED pending dope-context bridge — gap G-11) |
| decision.logged → chronicle mirror | `docker/mcp-servers-source/conport/integration_bridge_client.py:42,73,110` (`CHRONICLE_STREAM=activity.events.v1`), called at `enhanced_server.py:726`; runtime-proven (`899684b41`, `claudedocs/runtime-proof-chronicle-mirror-2026-07-07.md`) |
| pal-stdio self-healing | `scripts/ensure_pal_stdio.sh` (`539752a4b`) |
| gpt-researcher transport cutover | sse (`539752a4b`) |
| Heartbeat rate-limit + mcp-capture disposition | MCPINT-FND-HYG-007 (terminal/done in tree `af10eefd`) |
| Reserved-singleton identity probe | `909928a39` (`port_allocator.py`, `task_orchestrator_identity.py`) |

**Branch caveat**: some ledger rows ride in-flight branches (PR #1073; `fix/reserved-singleton-identity-probe`) and are not yet on origin/main `415f28d95`. The ledger records *repo truth*, not merge state; P7 packets must re-verify any row they build on at execution time.

## 3. Already-owned work (existing items — never duplicated by P7)

| Owner item | Tree | State | Covers |
|---|---|---|---|
| MCPINT-FND-DRIFTGATE-003 / INSTRREPAIR-004 / REGISTER-GATE-006 | af10eefd P3 | queue | drift gates, instruction surfaces, register contract test |
| MCPINT-FND-REGKILL-008 | af10eefd P3 | queue | legacy `src/dopemux/mcp/registry.yaml` retirement (scope-extended by P7 note to also kill stale `services/registry.yaml`, last_updated 2026-03-11) |
| MCPINT-IMP-FACADE-001 | af10eefd P4 | work/in-progress | facade deployment (P7 FACADEDCTX-014 depends on it) |
| MCPINT-IMP-EVENTS-006 | af10eefd P4 | queue (G2/ADR-004) | event ingress contract (P7 EVHYG-008 layers dedup/PII on top) |
| MCPINT-IMP-RISK-005 | af10eefd P4 | queue (G4) | predictive_risk_assessment hook — sole owner |
| MCPINT-IMP-COMPLEX-008 | af10eefd P4 | queue (G5) | complexity_coordinator single-scorer wiring (now gated by G7 ratification) |
| MCPINT-P5 DOC-001..003, MCPINT-P6-E2E-001 | af10eefd | queue | docs catalog; e2e verification (scope-extended by P7 note) |
| DOPECODE-001 | f64aa1a9 | queue | deploy in-repo Serena engine (46 tools) — successor of cancelled ADHDINTEL-007; P7 SERENAWRAP-006 is cross-tree gated on it |
| DOPEMEM-001..008 | f64aa1a9 | queue | dope-memory build-out incl. hybrid RRF Trinity retrieval (G6 seam note) |
| SVCFEAT-003 | f64aa1a9 | queue | task.*/workflow.phase_changed chronicle emission (coordinate with EVHYG-008) |
| SVCFEAT-001 / SVCFEAT-004 | f64aa1a9 | queue | dope-context Qdrant GC + cost guard; adhd-engine ML predictions |

## 4. Gap register (P7 scope)

| # | Gap (verified 2026-07-18) | Packet |
|---|---|---|
| G-01 | No durable consolidated reconciliation report in-repo | HRD-REPORT-001 (this document) |
| G-02a | `scripts/mcp-wrappers/conport-wrapper.sh` still execs upstream `uvx --from context-portal-mcp` → split-brain DB; conport `_ensure_schema` fail-open unverified | HRD-CONPORTWRAP-005 |
| G-02b | `scripts/mcp-wrappers/serena-wrapper.sh` targets phantom `services/serena/v2/mcp_server.py` | HRD-SERENAWRAP-006 (repoint; interim-disable inside 005) |
| G-04 | desktop-commander: Linux container cannot run macOS commands; catalog `lifecycle: decision-required` | HRD-DESKCMD-007 (host-run per user decision) |
| G-05 | Chronicle ingress lacks `event_id` dedup + pre-storage PII redaction (addendum §2.6/2.7) | HRD-EVHYG-008 |
| G-06 | Instance identity passed via env (`DOPE_MEMORY_INSTANCE_ID`, `DOPEMUX_WORKSPACE_ID` in `.mcp.json`) — cannot scope per-request on shared HTTP servers; 07-10 probe blockers (`instances.json` missing, static base_url staleness, dual TO stacks) | HRD-IDENTITY-009 |
| G-07 | dope-context decision auto-indexing not enabled | HRD-DCTXIDX-010 (post-G6) |
| G-08 | No fleet token-truncation standard (progressive 9K budget; MCP-boundary truncation at `call_tool()`) — patterns lost in migration (archived CONPORT/LEANTIME_TOKEN_LIMIT_FIX) | HRD-TOKTRUNC-011 |
| G-09 | Loopback binds inconsistent (localhost vs 127.0.0.1; per-container publish unaudited) | HRD-LOOPBACK-012 |
| G-10 | `services/conport_kg/` graph traversal (neighbors, relationship-type queries) quarantined, unreachable | HRD-KGREAD-013 (post-G6; excludes vector) |
| G-11 | Facade `search_code_docs`/`get_index_status` return BLOCKED (REST-only client; needs MCP JSON-RPC bridge); facade unregistered in catalog; no inventory-freshness CI gate | HRD-FACADEDCTX-014 |
| G-12 | `decide_lane()` (`src/dopemux/dcp/lane_engine.py:335`) has zero non-test consumers | HRD-LANE-018 |
| G-13 | Python `services/task-orchestrator/` name-collides with Kotlin singleton; rename → `workflow-api` + strip redundant MCP declarations (partial migration suspected: `app/` subtree) | HRD-RENAME-015 |
| G-14 | ADHD wiring: `context_preserver` (services/adhd_engine/domains/attention/) has no PM surface; overwhelm snapshot, energy-aware routing, event-bus→orchestrator triggers unwired | HRD-ADHDSURF-016, HRD-ADHDROUTE-017 |
| G-15 | Three unresolved architecture decisions | HRD-CONSENSUS-VEC-002 (G6), HRD-CONSENSUS-CPLX-003 (G7), HRD-CONSENSUS-PMSYNC-004 (G8) |
| G-16 | E2E Trinity verification insufficiently scoped | note on MCPINT-P6-E2E-001 (no new packet) |

## 5. Decision register

**Resolved (2026-07-16, MCPINT gates — do not re-decide):**
- **G1** non-Claude agent MCP exposure → facade + read-safe singletons (adr-mcpint-002).
- **G2** event ingress contract → fix bridge JWT, bless `/events` (adr-mcpint-004).
- **G3** Serena ADHD layer → archive candidate, subordinate to DopeCode deploy (superseded by SVCFEAT DOPECODE-001).
- **G4** TO predictive-risk → flag-gated pilot (RISK-005).
- **G5** complexity authority → `complexity_coordinator` single scorer (adr-mcpint-001).

**Open (P7 — resolved by PAL consensus, ≥3 models, logged to ConPort + ADR):**
- **G6** ConPort vector-search boundary. Recommendation: ConPort stays out of embeddings; `mem.search` becomes a read-only adapter delegating to dope-context (Trinity plane law). Gates: DCTXIDX-010, KGREAD-013; seam note on DOPEMEM-005.
- **G7** Complexity federation — **ratify/challenge G5**, define the consumer API. If consensus overturns G5: halt, escalate to operator; COMPLEX-008 stays gated.
- **G8** Leantime/PM write-sync boundary. Recommendation: write-sync stays disabled; PM tools get a read-only mirror; task-orchestrator remains sole legal mutator of workflow state. Gates: ADHDSURF-016.

## 6. Packetization map

### 6.1 P7 packets (18)

| Wave | Packet | Gates/deps |
|---|---|---|
| 0 | DMX-MCPINT-HRD-REPORT-001 | — (blocks all 17) |
| 1 | HRD-CONSENSUS-VEC-002 (G6), HRD-CONSENSUS-CPLX-003 (G7), HRD-CONSENSUS-PMSYNC-004 (G8), HRD-CONPORTWRAP-005, HRD-DESKCMD-007, HRD-LOOPBACK-012 | REPORT-001 |
| 2 | HRD-EVHYG-008 (also EVENTS-006), HRD-IDENTITY-009, HRD-DCTXIDX-010 (G6), HRD-TOKTRUNC-011, HRD-KGREAD-013 (G6), HRD-FACADEDCTX-014 (also FACADE-001), HRD-RENAME-015, HRD-LANE-018 | as noted |
| 3 | HRD-SERENAWRAP-006 (DOPECODE-001 cross-tree), HRD-ADHDSURF-016 (RENAME-015 + G8), HRD-ADHDROUTE-017 (RENAME-015 + EVENTS-006) | as noted |

Packet files: `task-packets/DMX-MCPINT-HRD-*.json`. Load plan: `docs/ops/load-plans/load_plan-DMX-MCPINT-P7.json`.

### 6.2 Scope-extension / crosslink notes on existing items

1. MCPINT-FND-REGKILL-008 — also retire/regenerate stale `services/registry.yaml`.
2. MCPINT-P6-E2E-001 — full-Trinity e2e + P7 outcome assertions.
3. MCPINT-IMP-COMPLEX-008 — gated by G7 ratification.
4. MCPINT-IMP-RISK-005 — sole owner of predictive-risk hook.
5. DOPECODE-001 — SERENAWRAP-006 gated on this deploy.
6. DOPEMEM-005 — G6 defines the ConPort↔dope-context retrieval seam.
7. SVCFEAT-003 — coordinate ingress payload contract with EVHYG-008.

### 6.3 Cross-tree dependency

`DOPECODE-001` (f64aa1a9) —BLOCKS→ `MCPINT-HRD-SERENAWRAP-006` (af10eefd/P7).

## 7. Dormant-capability register (paths verified on disk 2026-07-18)

| Capability | Path | Disposition |
|---|---|---|
| Predictive risk ML (562 lines, 8 categories) | `services/task-orchestrator/predictive_risk_assessment.py` | RISK-005 owns |
| Context preservation backend | `services/adhd_engine/domains/attention/context_preserver.py` (moved from addendum path) | ADHDSURF-016 |
| Multi-team coordination | `services/task-orchestrator/multi_team_coordination.py` | dormant-by-design, keep |
| KG graph traversal / progressive disclosure | `services/conport_kg/` (`queries/models.py`, `orchestrator.py`, `age_client.py`) | KGREAD-013 (graph only); vector = G6 |
| Serena local engine (45+ modules: adhd_features, focus_manager, fatigue detection, adaptive learning, untracked-work detector) | `services/serena/` | DOPECODE-001 (deploy); SERENAWRAP-006 (wrapper) |
| Capture/emit audit tool | `services/mcp-capture/server.py` | resolved by FND-HYG-007 |
| Progressive token truncation / boundary truncation | archived docs only (CONPORT_TOKEN_LIMIT_FIX, LEANTIME_TOKEN_LIMIT_FIX) | TOKTRUNC-011 |

## 8. Fleet wiring snapshot (2026-07-18)

| Server | Transport / port | State |
|---|---|---|
| conport | SSE :3005 (compose) | healthy core; **stdio wrapper split-brain (G-02a)** |
| dope-memory | HTTP :3020/mcp | healthy; identity via env (G-06) |
| dope-context | HTTP :3010/mcp | healthy; wrapper fixed; decision-indexing off (G-07) |
| task-orchestrator | Kotlin singleton HTTP 127.0.0.1:7890/mcp | healthy; python twin rename pending (G-13) |
| serena | SSE :3006 (upstream wrapper) | wrapper phantom path (G-02b); local engine dormant |
| pal / pal-stdio | stdio via docker exec | self-healing wired |
| gpt-researcher | SSE :3009 | healthy |
| exa | — | retired |
| desktop-commander | SSE :3012 container | facade — decision-required (G-04) |
| dcp-readonly-facade | stdio (operator-run) | 12 tools; 2 BLOCKED (G-11); uncataloged |

## 9. Risks and unknowns

1. **Branch divergence**: MCPINT program artifacts (ADRs, load plan) land via PR #1073; P7 PR notes the merge-order dependency.
2. **G7 overturn path**: consensus may contradict the standing G5 user decision — halt + operator escalation, never silent overturn.
3. **RENAME-015 vs SVCFIN**: pre-flight must confirm no SVCFIN item claims `services/task-orchestrator/`.
4. **LOOPBACK-012 overlap** with DMX-HYG-LOOPBACK-002 — diff its proof bundle before acting.
5. **IDENTITY-009** touches `.mcp.json` (H1 contract surface) and must preserve the MEMSPINE-IDENTITY-005 fail-closed invariant.
6. **conport `_ensure_schema`** fail-open status is UNKNOWN until CONPORTWRAP-005 step-1 verifies it.
7. Multi-instance/ChatGPT routing stays **unsafe** until IDENTITY-009 lands (07-10 probe verdict).
