# Backlog — Task-Packet Master Manifest & Traceability

**Date**: 2026-07-07 · **Branch**: `claude/backlog-taskpackets` · **Status**: authored (this pass = author + validate + index + load-plan; **no implementation, no live orchestrator mutation**)

Converts every actionable finding from this thread + the three merged PRs (#1011 Memory Context Fabric, #1002 MCP fleet audit, #1009 service P0) into schema-valid Task Packets (`task-packets/generated/<SERIES>/`) and a task-orchestrator load-plan (`ORCHESTRATOR_LOADPLAN.md` + `loadplan.json`). Decisions frozen in [`decisions-ledger.md`](decisions-ledger.md).

**Tiers**: **B** = implementation (frozen/plan-ready, mechanical steps) · **C** = planning (deliverable = a spec/plan, as TP-MCF-001 produced 002/003) · **A** = ADR (author the decision record). Every packet is a valid TP and an orchestrator item.

**Disposition** (load-plan `disp`): BUILD · WIRE · HARDEN · DELETE · RETIRE · CONSOLIDATE · REBUILD · SPEC · ADR.

**Artifacts in this dir**: `decisions-ledger.md` (frozen decisions) · `README.md` (this manifest) · `_AUTHORING_CONTRACT.md` (packet-authoring rules) · `loadplan.json` (machine-readable orchestrator load-plan) · `ORCHESTRATOR_LOADPLAN.md` (human-readable + MCP call recipe). Packets: `task-packets/generated/DMX-*/`. Index: `task-packets/INDEX.md`.

---

## Reconciliation with current `main` (important — runtime outranks the audit)

The MCP fleet audit is dated **2026-07-03**; `main` moved since. During authoring, agents cross-checked every audit claim against **live `origin/main`** (per the repo Truth Order) and found parts of Phase 0/1 **already shipped** — a schema-validated unified fleet catalog (`src/dopemux/mcp/fleet_catalog.py` + `schemas/mcp/fleet-catalog.schema.json`) with a 20+-test CI drift suite, a working `dopemux mcp ensure --fast/--full`, exa retirement via **ADR-223**, and P0 fixes (`4974015c3`, `b63b4b4a7`). Affected packets were **kept in the matrix but reframed to the verified residual gap**, not authored as greenfield:
- `DMX-FLEET-P0-001` / `-003` → **regression-lock** packets (bug already fixed; lock it in + wire the existing test into the discoverable path).
- `DMX-FLEET-P0-004` → the real issue is a **semantic** duplicate (`dopemux-pal`/`dopemux-zen`), not literal YAML key collision.
- `DMX-FLEET-P1-001/002/003/004/006` → close the residual gap (fold last legacy registries, close dry-run-only codegen, wire the advisory hook to the built `mcp ensure`, delete 5 stale exa refs); `P1-005`/`P1-007` confirmed genuinely unbuilt.
- New drift surfaced: `PROMOTABLE_EVENT_TYPES` is now duplicated across **3** files (`capture_client.py`, `promotion.py`, `dopecon_bridge/promotable_mirror.py`), not the 2 the audit recorded → `DMX-FLEET-P2-001` requires reconciling all three.

**Implication**: this backlog reflects *verified residual work as of 2026-07-07*, not the audit's original framing. Each affected packet's first step re-verifies current state before acting, so an executor never re-fixes a solved bug. **`bd85e784c`** (MCF fork decisions) also remains unmerged on `claude/memory-context-fabric` — land it or fold into a follow-up.

---

## Series DMX-MCF — Memory Context Fabric (8)
Source: `claudedocs/memory-context-fabric-*.md`, `claudedocs/plans/2026-07-04-*.md`, `claudedocs/tp-mcf-001-authority-map-2026-07-04.md`.

| ID | Tier | disp | Target (one sentence) | depends_on |
|---|---|---|---|---|
| `DMX-MCF-002-transcript-ingest` | B | BUILD | Ingest Claude Code transcript JSONL → dope-memory raw ledger only, with deterministic ids, stable-timestamp-or-quarantine, and a **non-queryable quarantine table** (schema migration) for redaction failures. | — |
| `DMX-MCF-003-decision-candidate` | B | BUILD | Add `conversation.decision_candidate` to both allowlists (sync-guard) + a deterministic promotion handler; never auto-writes ConPort. | `DMX-MCF-002` |
| `DMX-MCF-004-sessionstart-recap` | B | BUILD | Bounded SessionStart recap injection via native hooks (read-only SQLite, token budget, authority labels, kill switch). | `DMX-MCF-003` |
| `DMX-MCF-005-semantic-projection-spec` | C | SPEC | Produce the semantic-memory projection spec (dope-context `memory_{hash}`, privacy-safe embedding) — deferred go/no-go after 004. | `DMX-MCF-004`, `DMX-ADR-001-semantic-memory-home` |
| `DMX-MCF-006-conport-graph-spike-spec` | C | SPEC | Run the AGE data-layer spike, then spec `graph.neighbors`+genealogy tools; fall back to relationship-query if spike fails. | `DMX-ADR-005-conport-graph-exposure` |
| `DMX-MCF-007-fabric-orchestrator-spec` | C | SPEC | Spec the Fabric orchestrator + `context.recall`/`context.recap` MCP surface with graceful modality degradation. | `DMX-MCF-002`, `DMX-MCF-003`, `DMX-MCF-004` |
| `DMX-MCF-008-summarizer-spec` | C | SPEC | Spec the LLM summarization worker (candidate-only, cheap-model default, budgeted). | `DMX-MCF-003`, `DMX-MCF-007` |
| `DMX-MCF-009-proactive-injection-spec` | C | SPEC | Spec proactive mid-session injection (rate limit + relevance threshold + kill switch). | `DMX-MCF-007` |

## Series DMX-FLEET-P0 — Stop the bleeding (7, all B)
Source: fleet audit §8 Phase 0 + §7.1 kill list; runtime bugs (Category 5).

| ID | Tier | disp | Target | depends_on |
|---|---|---|---|---|
| `DMX-FLEET-P0-001-real-healthchecks` | B | HARDEN | Replace fake `exit 0` healthchecks (pal, dope-context) with real capability probes (MCP initialize + tools/list). | — |
| `DMX-FLEET-P0-002-ensure-pal-managed` | B | WIRE | Bring load-bearing PAL under managed startup: `ensure-pal.sh` + real healthcheck + compose integration. | — |
| `DMX-FLEET-P0-003-conport-schema-verify-failclosed` | B | HARDEN | Fix `_ensure_schema` verify to fail-closed on migration failure (currently a no-op). | — |
| `DMX-FLEET-P0-004-registry-dedup` | B | HARDEN | Dedupe duplicate YAML keys in `src/dopemux/mcp/registry.yaml` (last-wins silently disables servers). | — |
| `DMX-FLEET-P0-005-wrapper-path-fixes` | B | HARDEN | Fix broken MCP wrappers (conport→in-repo, dope-context env/path, serena phantom path). | — |
| `DMX-FLEET-P0-006-quarantine-killlist` | B | DELETE | Remove kill-list dead code + rename the Python task-orchestrator shadow-twin → `workflow-api`. | — |
| `DMX-FLEET-P0-007-desktop-commander-upstream` | B | REBUILD | Replace the broken desktop-commander container facade with real upstream DesktopCommanderMCP on the host. | — |

## Series DMX-FLEET-P1 — Single source of truth (7, mostly C)
Source: fleet audit §8 Phase 1 + §6.1; lost-pattern restorations (forgotten-features §3b).

| ID | Tier | disp | Target | depends_on |
|---|---|---|---|---|
| `DMX-FLEET-P1-001-unified-catalog-spec` | C | SPEC | Spec one schema-validated catalog merging `mcp_catalog.yaml` + `registry.yaml` + `services/registry.yaml` (canonical: dopemux). | `DMX-FLEET-P0-004` |
| `DMX-FLEET-P1-002-codegen-pipeline-spec` | C | SPEC | Spec codegen from the unified catalog → `.mcp.json`, `~/.claude.json`, `~/.codex/config.toml`, compose port/env, health lists, doctrine. | `DMX-FLEET-P1-001` |
| `DMX-FLEET-P1-003-mcp-ensure-command` | C | BUILD | `dopemux mcp ensure` + `--fast`: idempotent <2s daemon→compose→pal-recreate→orchestrator-singleton→capability-verify. | `DMX-FLEET-P1-001`, `DMX-FLEET-P0-002` |
| `DMX-FLEET-P1-004-ci-drift-gates` | B | HARDEN | CI drift gates: catalog↔generated-configs, commands↔tool-surfaces, compose-ports↔registry. | `DMX-FLEET-P1-002` |
| `DMX-FLEET-P1-005-orchestrator-autostart` | C | WIRE | Auto-start the task-orchestrator + refresh its truth-pack to the deployed version. | — |
| `DMX-FLEET-P1-006-exa-retire-cleanup` | B | RETIRE | Finish exa retirement: doctrine update (WebSearch fallback) + remove dead config writers/surfaces. | — |
| `DMX-FLEET-P1-007-token-truncation-utility-spec` | C | SPEC | Restore the lost progressive-token-truncation + MCP-boundary-enforcement pattern as one shared utility at the `call_tool()` boundary. | — |

## Series DMX-FLEET-P2 — Memory spine (5, B/C)
Source: fleet audit §7.2; PR #1009; forgotten-features (mcp-capture, event-bus triggers).

| ID | Tier | disp | Target | depends_on |
|---|---|---|---|---|
| `DMX-FLEET-P2-001-event-source-wiring` | C | WIRE | Wire `decision.logged`/`task.*`/`workflow.phase_changed` at their real emission sources (ConPort decision-write + workflow-kernel transitions); **fold mcp-capture into `capture_client.py`**. | — |
| `DMX-FLEET-P2-002-heartbeat-ratelimit` | B | HARDEN | Rate-limit `session-active` heartbeat spam and normalize/backfill `instance_id`. | — |
| `DMX-FLEET-P2-003-instance-identity-propagation` | C | SPEC | Move workspace/instance identity into per-request parameters (tool args/headers) so worktree scoping is real over shared HTTP servers. | — |
| `DMX-FLEET-P2-004-skill-mirror-receipts` | B | WIRE | `/decision`, `/caveat`, `/followup` append dope-memory mirror-receipt confirmations (Trinity Rule 1). | — |
| `DMX-FLEET-P2-005-dopecontext-indexing-enable` | B | WIRE | Flip `ENABLE_DOPECONTEXT_INDEX=true` with provenance pointers once the chronicle holds real content. | `DMX-FLEET-P2-001` |

## Series DMX-FLEET-P3 — Canonical surfaces (6, C/A/B)
Source: fleet audit §7.1/§7.3 + §8 Phase 3; forgotten-features §2.5–2.6.

| ID | Tier | disp | Target | depends_on |
|---|---|---|---|---|
| `DMX-FLEET-P3-001-conport-jsonrpc-parity` | C | SPEC | Spec ConPort packets 106/107/201/202: JSON-RPC tool parity (13→17), kill GET-mutation side-effect, product context, relationship write API. | — |
| `DMX-FLEET-P3-002-serena-promotion` | C | CONSOLIDATE | Promote the local 45-tool Serena surface to canonical per ADR (6 write tools out of default profile); archive/retire the wrapper split. | `DMX-ADR-002-serena-promotion` |
| `DMX-FLEET-P3-003-complexity-unify-spec` | C | SPEC | Pick the canonical complexity scorer among the three unwired implementations and spec wiring it everywhere. | `DMX-ADR-004-complexity-scorer` |
| `DMX-FLEET-P3-004-qdrant-gc` | B | HARDEN | Garbage-collect orphaned Qdrant collections per deleted worktree. | — |
| `DMX-FLEET-P3-005-voyage-cost-guard` | B | HARDEN | Add an external-embedding (Voyage) spend cap / cost guard to dope-context. | — |
| `DMX-FLEET-P3-006-loopback-binds` | B | HARDEN | Close `0.0.0.0` exposure fleet-wide (conport/dope-memory/serena/gptr loopback-bind). | — |

## Series DMX-FLEET-P4 — DCP activation (5, B/C)
Source: fleet audit §4 (DCP verdict) + §8 Phase 4.

| ID | Tier | disp | Target | depends_on |
|---|---|---|---|---|
| `DMX-FLEET-P4-001-facade-g1-contract-test` | B | WIRE | Close DCP facade G1: wire the 3 unwired tools + a CI contract test asserting `exposed == TOOL_CONTRACT`. | — |
| `DMX-FLEET-P4-002-dopecontext-bridge-spec` | C | SPEC | Spec the dope-context MCP-JSON-RPC bridge that unblocks the facade's dope-context adapter. | — |
| `DMX-FLEET-P4-003-lane-engine-wire` | B | WIRE | Wire `decide_lane()` as a real dispatch point (`dopemux dcp lane` + task-packet intake). | `DMX-ADR-003-lane-engine-dispatch` |
| `DMX-FLEET-P4-004-inventory-freshness-gate` | B | HARDEN | Add a facade inventory-freshness CI verification. | `DMX-FLEET-P4-001` |
| `DMX-FLEET-P4-005-facade-catalog-register` | B | WIRE | Register `dcp-readonly-facade` in the unified catalog (currently operator-run, unregistered). | `DMX-FLEET-P1-001` |

## Series DMX-FLEET-P5 — Prove it (3, B/C)
Source: fleet audit §8 Phase 5.

| ID | Tier | disp | Target | depends_on |
|---|---|---|---|---|
| `DMX-FLEET-P5-001-e2e-acceptance` | C | SPEC | Spec + build the end-to-end acceptance: fresh worktree → `mcp ensure` → all planes green → decision logged → mirrored → recapped → retrieved. | `DMX-FLEET-P1-003`, `DMX-FLEET-P2-005` |
| `DMX-FLEET-P5-002-docs-reconciliation` | B | HARDEN | Regenerate fleet doctrine; mark aspirational ADHD automation as specification-only. | — |
| `DMX-FLEET-P5-003-proof-discipline` | B | HARDEN | Establish the per-packet proof-bundle template + checker under `proof/`. | — |

## Series DMX-ADHD-WIRE — Forgotten-features wire-existing (6, B/C)
Source: `claudedocs/mcp-fleet-forgotten-features-addendum-2026-07-04.md` §3a/§3c.

| ID | Tier | disp | Target | depends_on |
|---|---|---|---|---|
| `DMX-ADHD-WIRE-001-predictive-risk-hook` | B | WIRE | Wire the built-but-dormant `predictive_risk_assessment.py` into the task-orchestrator (8 risk categories incl. hyperfocus burnout). | — |
| `DMX-ADHD-WIRE-002-context-preservation-display` | B | WIRE | Surface `adhd_engine/context_preserver.py` output on a PM display (backend already live). | — |
| `DMX-ADHD-WIRE-003-overwhelm-snapshot` | B | WIRE | Expose `event_coordinator.py` overwhelm telemetry on a PM surface. | — |
| `DMX-ADHD-WIRE-004-relationship-vocab-widening` | B | WIRE | Expose ConPort's richer relationship vocabulary (affects/depends_on/implemented_by/…) beyond `link_conport_items`. | `DMX-FLEET-P3-001` |
| `DMX-ADHD-WIRE-005-adaptive-learning-resurrect-spec` | C | SPEC | Spec resurrecting the Adaptive Learning engine foundation (unblocked by Serena promotion). | `DMX-FLEET-P3-002` |
| `DMX-ADHD-WIRE-006-fatigue-contextswitch-resurrect-spec` | C | SPEC | Spec resurrecting the Fatigue + Context-Switch + Untracked-Work modules (Serena-surface dependent). | `DMX-FLEET-P3-002`, `DMX-ADHD-WIRE-005` |

## Series DMX-ADR — Decision records (5, all A)
Source: `decisions-ledger.md`.

| ID | Tier | disp | Target | depends_on |
|---|---|---|---|---|
| `DMX-ADR-001-semantic-memory-home` | A | ADR | Author the ADR: semantic memory lives in dope-context (`memory_{hash}`, provisionally, deferred); ConPort does not own semantic. | — |
| `DMX-ADR-002-serena-promotion` | A | ADR | Author the ADR: promote the local 45-tool Serena surface to canonical (6 write tools out of default profile). | — |
| `DMX-ADR-003-lane-engine-dispatch` | A | ADR | Author the ADR: wire `decide_lane()` as the real DCP routing dispatch point. | — |
| `DMX-ADR-004-complexity-scorer` | A | ADR | Author the ADR: unify complexity scoring onto one canonical scorer (which one = P3-003's investigation). | — |
| `DMX-ADR-005-conport-graph-exposure` | A | ADR | Author the ADR: expose `graph.neighbors`+genealogy on active ConPort, spike-gated. | — |

---

## Coverage cross-check (finding → packet)

- **MCF 002–009 + forks** → `DMX-MCF-*` + `DMX-ADR-001/005`. ✓
- **Fleet Phase 0–5 (~30 items)** → `DMX-FLEET-P0..P5-*`. ✓
- **Forgotten-features wire-existing/resurrect** → `DMX-ADHD-WIRE-*` + folded (mcp-capture→P2-001, ConPort graph→ADR-005/MCF-006, relationship-vocab→WIRE-004, token-truncation→P1-007). ✓
- **10 decisions** → `decisions-ledger.md` + `DMX-ADR-*`. ✓
- **~20 runtime bugs (Category 5)** → each folded into a packet: wrong-stream→P2-001 · schema-verify→P0-003 · painted-socket→MCF-005 · PROMOTABLE dup→MCF-003 · wrapper paths→P0-005 · instance-identity→P2-003 · fake-healthchecks→P0-001 · dup-YAML→P0-004 · no-ensure→P1-003 · orchestrator-autostart→P1-005 · shadow-twin rename→P0-006 · GET-mutations→P3-001 · Qdrant-orphans→P3-004 · Voyage-guard→P3-005 · desktop-commander→P0-007 · 3-registries→P1-001 · dead-config→P1-006. ✓
- **Settled "don't do"** → no packets (listed in `decisions-ledger.md`). ✓

**Total: 52 packets** (8 MCF + 7 P0 + 7 P1 + 5 P2 + 6 P3 + 5 P4 + 3 P5 + 6 ADHD-WIRE + 5 ADR). No inventory item dropped.
