# MCP Feature Triage — 2026-07 (DMX-MCPINT P1)

**Packet**: MCPINT-P1-TRIAGE-002 · **Program**: DMX-MCPINT (root `af10eefd`)
**Register**: `docs/03-reference/mcp/feature-register.yaml` (162 entries, all validated)
**Runtime basis**: `claudedocs/mcp-fleet-runtime-verification-2026-07-16.md` (P0) — runtime truth overrides docs everywhere they disagree.

**How to use this memo**: Section 1 needs no decisions (already packetized). Section 2 is
the only part that needs YOU — five gates, 2-3 options each, recommendation marked **REC**.
Answer the five gates and Phase 2 (ADRs) unblocks. Sections 3-5 are reference.

---

## 1. PLAN-NOW (already packetized — no decision needed)

### MCPINT packets (this program)

| Item | Register id | Packet |
|---|---|---|
| Deploy DCP read-only facade (12 tools, registry v2, dark today) | DCP-FACADE, DCP-REGISTRY-V2 | MCPINT-IMP-FACADE-001 |
| SessionStart recap injection (TP-MCF-004; blocked by MEMSPINE-IDENTITY-005) | TP-MCF-004 | MCPINT-IMP-RECAP-003 |
| SessionStart fleet-capability line | HOOK-FLEET-CAPABILITY-LINE | MCPINT-IMP-HEALTH-004 |
| Catalog completion + transport truth (pal `:3003/mcp` is fiction; add leantime-bridge, facade, mcp-registry, scheduled-tasks, context7; exa/desktop-commander runtime posture) | PAL-MANAGED-LIFECYCLE, PAL-VARIANT-DEDUPE, GPTR-TRANSPORT-TRUTH, SVC-LEANTIME-BRIDGE, PERIPH-* , DC-RUNTIME | MCPINT-FND-CATALOG-001 |
| Tool-surface snapshot command (seeded from P0 captures) | — (enables all `tools:` freshness) | MCPINT-FND-SNAPSHOT-002 |
| Tool-granular drift gate (dep: DMX-HYG-CONPORTREFS-003) | CMD-NAME-DRIFT-REPAIR | MCPINT-FND-DRIFTGATE-003 |
| Repair all drifted instruction surfaces (~11 ConPort names, mcp-system.md, /zen) | CMD-NAME-DRIFT-REPAIR | MCPINT-FND-INSTRREPAIR-004 |
| OpenCode/Copilot renderers + `--apply` real writes + parity gates | — | MCPINT-FND-CODEGEN-005 |
| Register contract test (`tests/arch/test_feature_register_contract.py`) | — | MCPINT-FND-REGISTER-GATE-006 |
| Heartbeat rate-limit; register-or-shelve mcp-capture + copilot ingester | SPINE-HEARTBEAT-LIMIT, MCP-CAPTURE, COPILOT-INGESTER | MCPINT-FND-HYG-007 |
| Docs: per-server contract pages, integration guide, workflows.yaml | CONPORT-ADMIN-DISCOVERY, DCTX-METRICS-EXTRAS, SVC-WEBHOOK-RECEIVER | MCPINT-DOC-001..003 |

### SVCFIN-owned (root `3ad40a72` — referenced, never re-decided here)

| Item | Register id(s) | SVCFIN packet |
|---|---|---|
| ConPort surface ADR (single-surface, product context, relationship APIs, JSON-RPC parity) | CONPORT-SINGLE-SURFACE, COPT-201/202/203/204/106 | DMX-ARCH-CONPORT-SURFACE-002 |
| Serena surface ADR (archive-or-promote candidate; **write-lane violation feeds this**) | SERENA-LOCAL-CANDIDATE, SERENA-WRITE-LANE | DMX-ARCH-SERENA-SURFACE-003 |
| Interruption shield (canonical home + root twin disposal) | ADHD-INTERRUPTION-SHIELD | DMX-ARCH-INTSHIELD-001 |
| Append-only invariants (enforce or delete from doctrine) | INV-MEM-APPENDONLY | DMX-ARCH-APPENDONLY-004 |
| Instance identity fail-closed (**N2 runtime smoking gun — priority raised**) | DMEM-IDENTITY-FAILCLOSED, CONPORT-IDENTITY-ISOLATION | DMX-MEMSPINE-IDENTITY-005 |
| task.*/workflow event producers | DMEM-TASK-EVENT-PRODUCERS | DMX-MEMSPINE-TASKCREATED-003 |
| Progress→chronicle spine completion | DMEM-CAPTURE-SPINE | DMX-MEMSPINE-PROGRESS-CHRONICLE-004 |
| Trinity Rule 2 indexing flag (verified OFF at P0) | DCTX-CHRONICLE-INDEX | DMX-MEMSPINE-DCINDEX-006 |
| gptr twin delete + extraction backend relocation (**cli.py:4328 no longer exists — re-locate entry point first**) | GPTR-TWIN-ARCHIVE | DMX-MEMSPINE-GPTR-TWIN-DELETE-002 / -EXTRACT-RELOCATE-001 |
| hooks → /external-activity ADHD ingress | ADHD-HOOK-INGRESS | DMX-ADHDLOOP-HOOKINGRESS-001 |
| adhd-engine ignition verify (**P0: NO CONTAINER — doc claim refuted**) | ADHD-ENGINE-CORE | DMX-ADHDLOOP-IGNITION-VERIFY-002 |
| ADHD-aware recap consumer (TUI) | ADHD-RECAP-CONSUMER, DMEM-ADHD-RECAP | DMX-ADHDLOOP-RECAP-003 |
| Desktop notification proof | ADHD-DESKTOP-NOTIFY | DMX-ADHDLOOP-DESKTOP-VERIFY-004 |
| adhd-dashboard keep+wire | DASH-ADHD-BACKEND | DMX-DASH-WIRE-001 |
| ConPort command-name repairs (prototypes the drift gate) | CMD-NAME-DRIFT-REPAIR | DMX-HYG-CONPORTREFS-003 |
| Dead-service deletions (WMA prototype, simple_server mock, dead triangle, voice-commands, dddpg, dashboards…) | DMEM-WMA-ARCHIVAL, DCTX-SIMPLE-SERVER-DELETE, ADHD-DEADCODE, SVC-DEAD-CLUSTER, SVC-DDDPG, DCP-DEAD-NEIGHBORS, DASH-*-DEAD | DMX-HYG-DEADSVC-001 |
| Loopback binding fixes (**exa world-bound 0.0.0.0:3011 while retired**) | EXA-RETIRE | DMX-HYG-LOOPBACK-002 |

---

## 2. THE FIVE GATES — your decisions (max 3 options each)

### G1 — Non-Claude agent MCP exposure

**Context.** Agent×MCP config divergence is total: Claude has the full fleet, **Codex has
zero**, OpenCode is pal-only, Gemini zero, Copilot an unproven proxy. The DCP read-only
facade (12 tools, route-manifest enforcement, 537/539 tests) was built exactly for this and
is verified **dark** — in no compose, catalog, or config (P0 claim 8). One catalog caveat
feeds this gate: **pal `:3003/mcp` does not exist** (P0 claim 11) — pal is stdio-exec only,
so "read-safe singleton" exposure of PAL to other agents must go through docker-exec
config, not an HTTP URL; FND-CATALOG-001 fixes the catalog lie either way.

- **(a) REC — Facade + read-safe singletons.** Facade = the only write-shaped surface
  non-Claude agents ever see (it's read-only by construction); plus direct read-safe
  singletons (serena*, dope-context, pal-stdio). Preserves actor-attribution + proof-bundle
  governance. (*subject to G3/Serena write-lane finding — see §5 anomaly 6.*)
- **(b) Full parity for Codex.** Same config Claude gets. Ends blindness fastest, but
  writes from an agent with no hook-side attribution enforcement = governance hole.
- **(c) Facade + TO-wrapper writes.** Like (a) plus a narrow task-orchestrator write
  wrapper so Codex can advance its own packets. Middle ground; needs a new wrapper packet.

**Answering unblocks**: MCPINT-IMP-FACADE-001 scope, IMP-CODEX-002, the `agents:` exposure
matrix in FND-CODEGEN-005/adr-mcpint-002, and the facade→dope-context bridge decision
(register: DCP-FACADE-DCTX-BRIDGE).

### G2 — Event ingress contract

**Context.** The bridge `/events` publish path is dead — P0 re-confirmed unauth POST →
401 with an **empty user store** (claim 7); `capture_client` direct-Redis is the only
working ingress. **P0 finding N2 raises the stakes**: the primary dope-memory container
carries another repo's workspace id (`dNh_CRM`), so chronicle writes attribute to the
wrong workspace — whatever ingress you bless must carry per-request workspace/instance
identity (MEMSPINE-IDENTITY-005), not env defaults.

- **(a) REC — Fix bridge JWT + bless `/events`.** One authenticated front door;
  dopecon-bridge is already the only multi-consumer seam. Identity rides the request.
- **(b) ADR-bless direct Redis, delete the dead path.** Cheapest; but every producer
  needs Redis creds and identity discipline is per-producer, not enforced at a door.
- **(c) Split by locality.** In-compose → Redis; host/hooks → bridge. Two contracts to
  keep honest.

**Answering unblocks**: MCPINT-IMP-EVENTS-006, adr-mcpint-004, heartbeat-limit placement
(FND-HYG-007), and cleanly sequences with MEMSPINE-IDENTITY-005.

### G3 — Serena ADHD layer (subordinate to DMX-ARCH-SERENA-SURFACE-003)

**Context.** The entire ADHD intelligence layer (F001 untracked-work lifecycle 973-line
storage, focus modes, fatigue detection, adaptive learning, cognitive-load orchestrator,
analytics) is **built-unwired** inside the undeployed `services/serena` candidate — design
4/5, reachability 1/5. The deployed upstream wrapper (27 tools) works and even calls
itself "serena-v2" at its health endpoint. Register holds 8 entries gated here.

- **(a) REC — Archive the candidate; port the untracked-work lifecycle into adhd-engine.**
  F001 is the one high-value piece (H5 lite probe already lives in hooks); the rest waits.
  Keeps one Serena surface (upstream), consistent with the SVCFIN surface ADR.
- **(b) Deploy the candidate as a second surface.** Unlocks everything at once; doubles
  the Serena maintenance + drift problem the fleet audit called shadow-twin syndrome.
- **(c) Upstream + minimal 5-tool ADHD extension.** Middle path; requires forking the
  upstream wrapper anyway.

**Answering unblocks**: disposition of F001, SERENA-ADHD-INTEL, SERENA-ANALYTICS,
SERENA-ADHD-CAPS, SERENA-COMPLEXITY-BANDING (jointly with G5), and the archive scope in
DMX-ARCH-SERENA-SURFACE-003.

### G4 — TO predictive-risk pilot

**Context.** `predictive_risk_assessment.py` (verified 527 lines, 8 risk categories incl.
hyperfocus burnout) is the highest-ROI stranded item — "~3 lines to hook" into PostToolUse
as an advisory. MCPINT-IMP-RISK-005 is pre-scoped as a flag-gated pilot
(`DOPEMUX_ENABLE_PREDICTIVE_RISK`, 2-week keep/kill).

- **(a) REC — Flag-gated pilot.** Cheap, reversible, measurable.
- **(b) Shelve.** Goes into adr-mcpint-005 with the other ML shelvings.

**Answering unblocks**: MCPINT-IMP-RISK-005 (executes only on yes).

### G5 — Complexity authority

**Context.** Three-going-on-**four** competing complexity scorers: Serena's
CodeComplexityAnalyzer (candidate, unwired), dope-context's `get_chunk_complexity` (live
but docstring lies and hits don't carry scores), TO's intelligence scorer (dormant), and —
found during this register pass — `services/dopecon-bridge/complexity_scorer.py`. The
built unifier exists: `services/complexity_coordinator` (AST + LSP + usage + ADHD
multiplier → `unified_score`) — in no compose or registry, unmentioned by every audit.

- **(a) REC — complexity_coordinator as the single scorer.** Wire it; the others become
  inputs or die. /dx:prd-parse scoring (DX-PRD-PARSE) finally gets a real backend.
- **(b) TO scorer only.** Smallest wiring, workflow-plane-centric; wastes the coordinator.
- **(c) Shelve all.** Complexity claims come out of doctrine until someone needs them.

**Answering unblocks**: SVC-COMPLEXITY-COORDINATOR, TO-COMPLEXITY-SCORER,
SERENA-COMPLEXITY-BANDING, DCTX-COMPLEXITY, DX-PRD-PARSE scoring, and the complexity
doctrine text in the docs phase.

---

## 3. SHELVE-BY-ADR (goes into adr-mcpint-005)

One combined shelve ADR; each item gets one line of rationale there. Register status
already `shelved`:

- **CONPORT-SEMSEARCH-MILVUS** — Milvus never deployed; semantic retrieval is
  dope-context's plane (Trinity boundary violation). Includes `mem.upsert`.
- **CONPORT-ZEP** — config-only stub, never implemented, same boundary problem.
- **TO-SPRINT-AUTOPLAN** — ConPort has no sprint API; genuinely unbuilt end-to-end.
- **TO-MULTITEAM** — dormant-by-design for a single-operator MVP; formalize the shelf.
- **MCF-FABRIC** — the whole fabric orchestrator/recall/recap/proactive-injection surface
  is design-only NO-GO; its two viable children escaped (TP-MCF-004 → IMP-RECAP-003;
  TP-MCF-006 → held for the ConPort surface ADR).
- **TP-MCF-005** — memory_{hash} semantic projection; NO-GO on external-embedding privacy.
  Revival requires its own ADR.

(G4=b or G5=c would add TO-PREDRISK / the scorer family here.)

---

## 4. Register statistics (computed from the YAML)

**162 entries** (target was 80-120; overage comes from preserving every historical
COPT-/TP-MCF-/F-series id as its own entry per the approved schema).

| Status | Count | | Plane | Count |
|---|---|---|---|---|
| planned | 48 | | memory | 26 |
| live | 43 | | chronicle | 25 |
| built-unwired | 26 | | infra | 15 |
| partial | 18 | | adhd | 14 |
| retired | 10 | | workflow | 13 |
| vaporware | 8 | | retrieval | 13 |
| shelved | 6 | | dcp | 12 |
| quarantined | 3 | | code-intel | 10 |
| | | | hooks | 10 |
| | | | dashboard | 8 |
| | | | research | 6 |
| | | | commands | 6 |
| | | | reasoning | 4 |

**Decisions**: held 58 · shipped 36 · packet:DMX-* (SVCFIN et al.) 31 · packet:MCPINT-* 18
· gate:G1/G2/G4 1 each · gate:G3 4 · gate:G5 4 · adr:adr-mcpint-005 6 · adr:other 2.

**Tool-surface checks**: every `tools:` list on conport / dope-memory / task-orchestrator /
serena / dope-context / desktop-commander entries verified ⊆ its P0 snapshot, with **full
coverage** (all 17+10+14+27+18+4 = 90 snapshot tools attributed to exactly one register
entry). pal-stdio (18), gpt-researcher (5), mcp-registry (3), scheduled-tasks (4) are
session-observed — flagged UNVERIFIED-SNAPSHOT per entry, capture owed to
MCPINT-FND-SNAPSHOT-002. The headline confirmed: **built-unwired + quarantined +
partial = 47 entries (29%)** — the program is mostly wiring, not building.

---

## 5. Anomalies — where runtime refuted the docs (now encoded in the register)

1. **adhd-engine ignition** — doc-asserted "shipped this cycle"; P0: `:3025` refused,
   container ABSENT from `docker ps -a` despite compose.yml:462. → ADHD-ENGINE-CORE
   `built-unwired`, doc claim preserved in note (claim 16).
2. **exa** — retired by ADR-223; P0: Up (healthy) AND world-bound `0.0.0.0:3011`.
   → EXA-RETIRE `retired` + runtime-posture note; loopback fix = DMX-HYG-LOOPBACK-002
   (claim 15).
3. **desktop-commander** — catalog-quarantined; P0: SSE :3012 answers with 4 GUI tools.
   Quarantine only affects generated configs, not runtime. → DC-RUNTIME `quarantined`
   with live tools listed (claim 14).
4. **pal transport** — catalog says `:3003/mcp`; P0: 404 on /mcp, /sse, /messages —
   endpoint is fiction; healthy wrapper only. pal-stdio is the sole PAL surface.
   → PAL-MANAGED-LIFECYCLE note; FND-CATALOG-001 scope (claim 11).
5. **dope-memory JSON-RPC** — raw register doc-asserted PARTIAL ("only /tools/*"); P0
   captured full JSON-RPC initialize+tools/list on POST /mcp. → DMEM-JSONRPC-PARITY
   upgraded to `live` (claim 6).
6. **Serena write lane** — docs assert a sanctioned read-only default profile; the P0
   snapshot shows 11 write-capable tools **including `execute_shell_command`** live on
   :3006. The read-only contract is already violated at runtime. → SERENA-WRITE-LANE
   `boundary_fit: violates`, feeds DMX-ARCH-SERENA-SURFACE-003 (new — found in this pass).
7. **Workspace contamination (N2)** — primary dope-memory carries
   `DOPE_MEMORY_WORKSPACE_ID=dNh_CRM` (another repo). Chronicle writes attribute wrongly;
   per-project twin containers (N5) make cross-project bleed systemic. → identity entries
   hardened; MEMSPINE-IDENTITY-005 priority raised; blocks IMP-RECAP-003.
8. **"serena-v2" naming** — health endpoint self-identifies as serena-v2 while the actual
   v2 candidate is undeployed — name is live, code is not (claim 4 twist).
9. **Graveyard prune not executed** (claim 17) — every `retired` entry with an existing
   code_path is still on disk on this branch/host; two expected corpses
   (monitoring-dashboard, mcp-integration-bridge, standalone ML twins) were NOT found and
   are marked unverified for the deletion packet to re-scan.
10. **gptr hidden HTTP surface** — :3009 serves an SSE-style /messages endpoint the
    catalog doesn't describe (claim 12). → GPTR-TRANSPORT-TRUTH.
11. **New operational findings encoded**: N1 `mcp init` catch-22 (TO-SINGLETON-LIFECYCLE),
    N3 litellm crash-loop (SVC-LITELLM `partial`), N4 docker-wedge blind spot
    (HOOK-H3-HEALTH-PROBE note; watchdog held as candidate packet, not scope-crept).

---

*Generated by MCPINT-P1 on 2026-07-16. Register + this memo are the Phase-1 exit
artifacts; Phase 2 (ADR set) starts once G1-G5 are answered.*
