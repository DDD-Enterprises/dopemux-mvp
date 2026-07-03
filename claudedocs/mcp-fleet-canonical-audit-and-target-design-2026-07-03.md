# Dopemux MCP Fleet — Canonical Feature Set, Implementation Audit, and Target-State Design

**Date**: 2026-07-03
**Scope**: Every MCP server the project runs or consumes, the design-doc corpus defining them, the wiring/lifecycle layer, and the DCP/integration mediation layer.
**Method**: 8 parallel read-only research agents (wiring map; ConPort; Serena+dope-context; dope-memory/Memory Trinity; task-orchestrator/PAL/gptr/exa/desktop-commander/litellm; DCP+integration services; 3× docs-corpus sweeps). All claims labeled VERIFIED (code/config read directly) or INFERRED. **Docker daemon was down throughout — all live-runtime claims are NOT_RUN; everything here is static code/config/ledger truth.**
**Worktree**: `.claude/worktrees/trusting-engelbart-d2fbfe` @ `dd3f59353` (branch `claude/trusting-engelbart-d2fbfe`). Nothing was edited outside this document.

---

## 1. Executive summary

The intended architecture is **good and unusually well-governed** — a split-authority model (ADR-backed Memory Trinity + authority map + DCP read-only mediation) with genuine fail-closed engineering in its newest layer. The implementation is **systemically undermined by one repeated failure mode: every major server exists in 2–3 competing personalities, and the connective tissue (wrappers, registries, hooks, health) points at the wrong one or at nothing.**

Five headline findings:

1. **Shadow-twin syndrome (systemic).** ConPort: stdio wrappers launch the *upstream PyPI* `context-portal-mcp` while SSE serves the in-repo server — two tool sets, two storages, and `.claude/commands/*` call 6 tool names the real SSE server doesn't have. Serena: 3 surfaces (45-tool local candidate, deployed upstream-oraios wrapper, phantom `v2/` path in the wrapper script) and 3 conflicting tool counts (23/33/45). PAL: 3 deployments; only the *unmanaged, off-compose* one is consumed. task-orchestrator: the Kotlin MCP jar (:7890) and an unrelated in-repo Python FastAPI service (:8000) share one name. GPT-Researcher: deployed upstream clone + dead in-repo parallel server.
2. **The memory spine is severed at the source.** The chronicle ledger holds 24,537 raw events — **100% `session-active` heartbeat spam — and 0 curated work-log entries**. Claude hooks emit content-free pings to the wrong Redis stream (`dopemux:events` vs `activity.events.v1`); the fully-functional capture spine (`capture_client.py`) is simply never called by them. `/mem:recap`, `memory_search`, reflections, and trajectory all rank an empty table. ConPort→dope-memory mirroring (Trinity Rule 1) exists only in a gated CLI path; dope-memory→dope-context indexing (Rule 2) is flagged off. **One import in `native_hooks.py` fixes the root cause.**
3. **Built-but-unwired is the norm, not the exception.** exa (healthy, 4 real tools, zero consumers, broken catalog entry), leantime-bridge (no client), mcp-capture (finished + tested, registered nowhere), DCP lane engine (`decide_lane()` — zero non-test consumers), 3 of 12 contracted facade tools never exposed on the MCP surface, facade itself absent from every registry.
4. **Health/lifecycle is advisory theater.** Four diagnostic layers (H3 hook, `mcp doctor`, `/mcp:doctor`, health report script) and none remediates. Fake healthchecks (`exit 0` for pal, `|| exit 0` for dope-context). Nothing ensures the load-bearing `pal-mcp-server` container exists (Codex declares it `required=true` → hard client outage on prune). Nothing auto-starts the task-orchestrator singleton. Three overlapping registries disagree, one has duplicate YAML keys silently disabling servers, and `sync-globals --apply` would *regress* working config.
5. **The one bright spot is real.** The DCP read-only facade and PCP live-write gate are structurally fail-closed (mutating HTTP verbs don't exist in the client class; execution-eligibility is computed, never serialized; untrusted-by-default envelopes; 537/539 tests pass). The task-orchestrator HTTP-singleton launcher is the best-engineered lifecycle path in the fleet. **The target state is mostly "make everything else as honest as these two."**

Prior-audit deltas worth recording: the 2026-06-16 "ConPort never applies migrations" finding is **stale** — `schema.sql` now applies at startup (root cause was a GRANT to a nonexistent role, fixed by #894) and enhanced migrations are *deliberately* operator-gated per ADR (PR #917/#936). A new fail-open bug in `_ensure_schema` verification was found instead.

---

## 2. Fleet inventory & wiring ground truth

| Server | Real source | Transport/port | Consumed by | Managed? | Healthcheck |
|---|---|---|---|---|---|
| conport | in-repo (`docker/mcp-servers-source/conport/`), 1 container / 3 procs | SSE :3005, REST :3004, info :4004 | Claude `.mcp.json` **and** duplicated in `~/.claude.json`; Codex **not wired** | compose | real |
| conport (shadow) | upstream `context-portal-mcp` via `conport-*.sh` wrappers | stdio in-container | any stdio client using wrappers | none | none |
| pal-mcp-server (**the real PAL**) | separate checkout `~/code/pal-mcp-server` (zen fork v9.0.2, 18 tools) | stdio via `docker exec` | Claude global + Codex (`required=true`) | **unmanaged, off-compose, no ensure script** | none |
| pal / pal-stdio (compose) | vendored fork `docker/mcp-servers-source/pal/` | HTTP :3003 / toolkit stdio | **nobody** | compose | `exit 0` no-op |
| task-orchestrator (MCP) | external image ghcr.io/jpicklyk v3.8.0, 13 tools | HTTP singleton 127.0.0.1:7890 | Claude `.mcp.json`, Codex, 18 `/dx:*` commands | singleton script (excellent) — **no auto-start** | script-level |
| task-orchestrator (compose) | in-repo Python FastAPI `services/task-orchestrator/` — *different system* | REST :8000 (+ unwired MCP stdio) | dopecon-bridge/ADHD stack; **no MCP client** | compose | real |
| dope-memory | `services/working-memory-assistant/dope_memory_main.py`, 10 MCP tools | streamable HTTP :3020/mcp | Claude `.mcp.json` | compose | real |
| dope-context | `services/dope-context/src/mcp/server.py`, 18 real tools | streamable HTTP 127.0.0.1:3010/mcp | Claude global, Codex | compose | **fail-open (`\|\| exit 0`)** |
| serena (deployed) | **upstream oraios/serena** via mcp-proxy wrapper | SSE :3006 | Claude global | compose | real |
| serena v2 (local) | `services/serena/mcp_server.py`, 45 tools incl. 6 write tools | — | **nobody** (wrapper broken: points at nonexistent `v2/mcp_server.py`) | none | — |
| gptr-mcp | upstream assafelovic/gptr-mcp pinned clone | SSE :3009 (Claude) + exec-stdio (Codex) | Claude global, Codex, `/research:*` | compose | contradictory (curl vs pgrep) |
| exa | in-repo FastMCP, 4 tools | HTTP :3011 | **nobody**; catalog entry broken (targets litellm container) | compose | real |
| desktop-commander | in-repo 4-tool server calling **macOS `osascript` inside a Linux container** | SSE 127.0.0.1:3012 | Claude global | compose | passes while all tools are no-ops |
| leantime-bridge | in-repo | SSE 127.0.0.1:3015 | **nobody** | compose | real |
| litellm | in-repo proxy config | HTTP :4000 (not MCP) | RTE/extraction lane only — **not** the MCP fleet's model plane (PAL/gptr/exa hit providers directly) | compose | real |
| dcp-readonly-facade | `services/dcp-readonly-facade/` | stdio, operator-run | ChatGPT via tunnel (design); **in no registry/compose/.mcp.json** | manual | n/a |
| mcp-capture | `services/mcp-capture/` (1 tool: `capture/emit`) | stdio | **nobody** (unregistered) | none | — |
| mcp-client / mcp-integration-bridge / router | in-repo | — | dead code (bridge has secret-leaking debug endpoint if ever revived) | none | — |

Config planes: per-worktree `.mcp.json` (3 servers, matches catalog) · `~/.claude.json` globals (7 servers, **drifted** from catalog) · `~/.codex/config.toml` (5 servers, no conport) · dead surfaces (`.claude/claude_config.json`, `wire_claude_mcp.py`, `manage-mcp-servers.sh`). **Three overlapping registries**: `mcp_catalog.yaml`, `src/dopemux/mcp/registry.yaml` (duplicate YAML keys ×4 → last-wins silently disables), `services/registry.yaml` (ports/health).

---

## 3. Canonical intended feature set (the docs' answer)

### 3.1 Architecture law (ADR-grade, consistent across the corpus)

- **Memory Trinity** (ADRs accepted 2026-03-11, reviewed 2026-06-19): plane 1 **ConPort** = canonical writer for decisions/progress/durable structured context; plane 2 **dope-memory** = chronicle/recap/replay/reflection/trajectory, *mirror only* (SQLite ledger canonical, Postgres mirror non-canonical, Redis transport-only); plane 3 **dope-context** = semantic retrieval, read-only, never truth-bearing. Cross-plane canonical overwrite forbidden; no silent authority escalation; provenance mandatory on multi-plane reads. Serena = technical-context plane deliberately *outside* the Trinity.
- **Authority map** (docs/03-reference/governance): task-orchestrator = workflow-transition legality only; Leantime = PM metadata; dopecon-bridge = transport/proxy only; ADHD engine = operator-support only; RTE = audit only; agents = UNKNOWN authority (recommendations only). Claim labels: canonical / mirror / proxy / derived / UNKNOWN.
- **MCP customization synthesis** (2026-05-01, PASS w/ guardrails): split-authority preserved; Serena read-mostly with write/shell hidden by default; dope-context = derived retrieval sidecar, `clear_index` + auto-provision rejected; Claude-Mem/Mem0 = evaluated upstream candidates only, deferred (Mem0 hosted-cloud forbidden). Roadmap: Series A evidence registry → B boundary adapters → audit → C exposure controls → D retrieval guardrails → E operator UX → F tests.
- **DCP charter**: v1 strictly read-only/contract-only; 11 systems mapped as adapters/projections with `live_write=false`; red lane DCP-RED-MERGE-SEAM-0001; `LIVE_WRITE_READY` undefined-and-blocking; execution-eligibility as an unforgeable computed capability; provenance flags only lower trust.

### 3.2 Per-server intended capability register

| Server | Intended capabilities (doc-sourced) |
|---|---|
| ConPort | decisions log/get/search; progress CRUD + lifecycle; active+product context; custom-data CRUD; relationship queries (write authority UNKNOWN); FTS + (aspirational) semantic search; REST canonical / FastMCP sanctioned wrapper / JSON-RPC compat-only; dark admin methods (fork/promote); operator-gated enhanced schema (13-table target); per-worktree instance isolation |
| task-orchestrator | persistent work-item graph; roles queue→work→review→terminal; trigger transitions + gates; dependency graph + blocked queries; note-schema gates; proof-bundle-in-note; repo-scoped state; 13 tools |
| dope-memory | event intake → redaction → raw store (7-day TTL) → high-signal promotion → curated chronicle; recap/replay/reflection/trajectory; supersession-style correction; workspace+instance partitioning; mirror receipts from ConPort |
| dope-context | AST-aware hybrid dense+sparse code+docs indexing (Voyage+Qdrant+BM25+rerank); search profiles; sync via SHA256; autonomous indexing (opt-in); per-worktree collections; complexity scoring; **lexical-only Phase-1 enforcement (required by repo rules, never proven)** |
| Serena | symbol nav, def/ref, project scoping, read-only default; ADHD caps (≤10 results, 3-level depth, complexity bands); edit lane only behind separate policy + flag |
| PAL | 18-tool multi-model reasoning suite backing AGENTS.md §5 chains |
| GPT-Researcher | deep_research / quick_search / write_report / sources / context; ConPort research_id persistence via `/research:*` |
| exa | quick neural search lane (doctrine: "Exa for quick lookups") |
| desktop-commander | doctrine says terminal/process control (matches neither implementation) |
| DCP facade | loopback evidence projection to external LLMs: 12 contracted tools, registry trust boundary, untrusted-by-default envelopes, denylist, redaction |

### 3.3 Documented contradictions (docs vs docs)

37-vs-13 orchestrator tool counts (era drift); port 8000 vs 7890 (resolved: two different systems); dope-memory 3020 vs 8096 (legacy adapter); Serena canonical writer UNKNOWN; ConPort "sole authority" claims = acknowledged drift vs split-authority law; multi-index api/chat configs unimplemented; service-discovery ADR adopted by 3/12 servers; `/dx:` 18-command surface lives on a series branch, not main; ADHD automation (timers, auto-save loops, forced breaks) is explicitly *specification-only*.

---

## 4. Implementation audit — per-server verdicts

### ConPort — WORKING CORE, SPLIT-BRAIN PERIPHERY
17 real SSE tools, all functional on the base schema (custom-data + search added recently). JSON-RPC advertises 13 of 17 (3 dark, 1 missing). **Wrappers launch upstream context-portal instead** → `.claude/commands` reference 6 nonexistent tools. Knowledge graph = plain table, read-only traversal, no write API, no AGE/Cypher at runtime. Migration-gate design is now sound; `_ensure_schema` verification is **fail-open** (new bug). Worktree isolation inert over SSE (server-env `DOPEMUX_INSTANCE_ID`, one global value). `GET /api/progress` mutates (auto-fork default ON). No auth on any endpoint. INV-MEM append-only invariants unenforced. Unexecuted packets: 101, 106, 107, 108, 109, 201, 202, 204, 206, 301–303.

### task-orchestrator — SOLID CORE, NO IGNITION, NAME COLLISION
Kotlin jar wiring + singleton lifecycle excellent; consumed by 18 `/dx:*` commands; **nothing auto-starts it**. Truth pack extracted at v2.2.0 vs deployed v3.8.0 (stale); schemas dir is a different surface entirely. In-repo Python `services/task-orchestrator` = unwired parallel MCP surface sharing the name. Known upstream bugs: health-check undercounts blocked items (0 vs 27); timestamp parse breaks overview.

### dope-memory — GOOD SERVER, EMPTY CHRONICLE
10-tool `/mcp` surface exceeds stale docs; fail-closed canonical SQLite ledger; schema right. **Capture pipeline severed**: hooks ping wrong stream with unpromotable payloads → `work_log_entries` = 0 rows against 24.5k heartbeat spam. Instance identity not passed through compose (`.mcp.json` env blocks can't reach HTTP servers — a design misunderstanding). WMA prototype (~3.6k lines) still co-resident; dead stdio shim on stale port 8096; `dope-query` is a husk despite being named in the ADR.

### dope-context — REAL ENGINE, BROKEN ON-RAMPS
18 real tools, real hybrid pipeline. Wrapper broken twice (wrong path, wrong env var); not in `.mcp.json`; container pins one workspace; healthcheck fail-open; no Qdrant collection GC (orphans for every deleted worktree); no Voyage cost guard; `simple_server.py` mock fabricates plausible results; complexity docstring lies (ast, not Tree-sitter); results don't carry per-hit complexity despite doctrine.

### Serena — THREE SURFACES, NONE RECONCILED
Deployed = upstream wrapper (fine, but not what docs describe). Local 45-tool candidate includes 6 write tools violating the sanctioned read-only contract; hardcoded localhost infra; silent degradation. ADHD caps genuinely implemented in the local candidate. Wrapper points at a nonexistent path.

### PAL — LOAD-BEARING AND UNMANAGED
Real 18-tool suite; consumed via an off-compose hand-made container with no ensure script, no healthcheck; Codex `required=true` makes it a fleet-wide hard dependency. Two managed compose variants nobody uses.

### GPT-Researcher / exa / desktop-commander
gptr: correctly wired both clients; contradictory healthchecks; dead in-repo twin. exa: orphan (built, healthy, unconsumed, catalog entry targets the wrong container). desktop-commander: **facade** — macOS automation tools inside a Linux container; every tool call should fail while health passes; matches neither upstream-of-same-name nor doctrine.

### DCP / PCP / integration layer — STRONGEST LAYER, LATENT IN PLACES
Facade structurally read-only (verbs don't exist), untrusted-by-default, fail-closed resolver/registry/redaction; 537/539 tests. Gaps: 3 of 12 contracted tools unwired on the MCP surface (G1); dope-context adapter permanently blocked pending an MCP-JSON-RPC bridge; lane engine + control snapshot have zero non-test consumers (protection latent); denylist is data+tests+advisory hooks, not runtime middleware; surface inventory is point-in-time with no freshness gate. PCP live-write bridge fully fail-closed (no default writer exists). Dead-but-startable neighbors (mcp-integration-bridge with secret-leaking debug endpoint; mcp-client) remain in tree.

---

## 5. Design validation — is the *intended* design right?

**Validated as sound** (evidence: it caught real hazards):
- Split-authority + canonical-writer labels. The facade's `search_progress` block exists precisely because the model forced someone to notice a GET that writes. Keep.
- Trinity plane separation with mirror receipts and fail-closed cross-plane routing. Keep.
- DCP structural fail-closed patterns (capability-not-field execution eligibility, trust-lowering-only provenance, untrusted-by-default envelopes). Keep and **generalize** — these are the house style the rest of the fleet should adopt.
- Repo-scoped orchestrator singleton + worktree-scoped memory: correct two-level scoping (workflow state is per-repo; context/chronicle per-worktree).

**Design defects to correct** (the design itself, not just execution):
1. **No single source of truth for the fleet.** Three registries + N client configs with manual sync is a design hole; ADR-002's own lesson ("HTTP/SSE + discovery eliminates drift") was adopted by 3/12 servers and then stalled.
2. **Env-var-shaped worktree isolation is unimplementable over shared HTTP servers.** `.mcp.json` env blocks cannot influence a remote container; the design must move workspace/instance identity into **per-request parameters** (tool args or headers), as dope-context already does correctly.
3. **Diagnosis without remediation.** Four doctors and zero nurses is a design stance, not an accident — it needs an explicit `ensure` layer.
4. **Doctrine files live outside the repo** (`~/.claude/MCP_*.md`) yet act as the de-facto interface contract; they drift with no CI. Contracts must be generated from the same catalog that generates client config.
5. **No decommissioning protocol.** Every superseded implementation stays in-tree, startable, and half-referenced — the direct cause of shadow-twin syndrome.

---

## 6. Optimal interaction model

### 6.1 Server ⇄ dopemux (engine/CLI)
- **One catalog, generated everything.** Merge `mcp_catalog.yaml` + `src/dopemux/mcp/registry.yaml` + MCP-relevant slice of `services/registry.yaml` into one schema-validated catalog (canonical writer: dopemux). Codegen: `.mcp.json`, `~/.claude.json` project entries, `~/.codex/config.toml` fragment, compose port/env blocks, health-probe lists, and the per-server doctrine docs. CI gate: generated artifacts match catalog (the existing `test_registry_compose_alignment.py` pattern, widened).
- **`dopemux mcp ensure`** (new, idempotent, <2s cached fast-path): daemon check → compose up required services → recreate `pal-mcp-server` (`ensure-pal.sh` with `--env-file`) → orchestrator singleton → verify capability (one real MCP `initialize`+`tools/list` per server, not TCP-only). `doctor` diagnoses; `ensure` remediates; H3 SessionStart hook calls `ensure --fast` instead of advising.
- **Authority labels at runtime**: every dopemux-owned server adopts the facade envelope fields (`source_system`, `authority_label`, `untrusted`, `freshness`, `limitations`) so consumers can't mistake mirrors/proxies/derived views for canon.

### 6.2 Server ⇄ developer (Claude/Codex sessions)
- **Contract honesty**: `.claude/commands/*` and `~/.claude/MCP_*.md` are regenerated from the catalog + live `tools/list` snapshots; a CI drift test fails when a command references a tool no server exposes (today: 6 broken ConPort references).
- **Session start**: H3 → `ensure --fast` → one-line fleet status (✅/⚠ per plane), ADHD-friendly, max 3 remediation options.
- **Memory capture is ambient, not manual**: lifecycle hooks emit structured promotable events through `capture_client` (see 7.2); `/decision`/`/caveat` skills append the dope-memory mirror receipt; recap actually recaps.
- **Per-worktree identity per-request**: workspace_id/instance_id resolved client-side (wrapper or hook) and passed as tool parameters; servers reject requests without identity rather than defaulting to a shared one (fail closed, per governance).

### 6.3 Server ⇄ host system
- Two-level scoping stays: repo-scoped orchestrator (git-common-dir hash — already correct), worktree-scoped conport/dope-memory/dope-context identity (per-request), host-singleton reasoning/research servers (PAL, gptr, exa) — stateless, shared safely.
- All listeners loopback-bound (several already are; conport/dope-memory/serena/gptr should match) — closes the standing 0.0.0.0 exposure family.
- Resource hygiene: Qdrant collection GC keyed to `git worktree list`; chronicle heartbeat rate-limiting; leak detector distinguishes legit per-repo singletons (match by data-dir mount, as the singleton script already does) from true leaks.

### 6.4 Server ⇄ environment (secrets/config)
- Secrets flow one way: `.env` → compose/ensure scripts → containers. No per-client key duplication (today Codex/Claude/catalog each carry key lists). litellm explicitly documented as *not* the MCP model plane.
- Delete dead config surfaces (`.claude/claude_config.json` writer, `wire_claude_mcp.py`, `manage-mcp-servers.sh`) so no tool can resurrect retired servers.

---

## 7. Target-state design

### 7.1 Target fleet (one personality each)

| Plane | Server | Decision |
|---|---|---|
| Knowledge/decisions | **conport (in-repo)** | Canonical. Retire upstream-wrapper path; rewrite wrappers/commands/doctrine against the real 17-tool surface; per-request instance identity; fail-closed schema verify; execute packets 106/107/201/202 (JSON-RPC parity, kill GET-mutation, product context, relationship write API) — the minimum set that makes "knowledge graph" true. |
| Workflow | **task-orchestrator Kotlin jar** | Canonical. Auto-start via ensure; regen truth pack at v3.8.0; rename Python service → `workflow-api` (compose + docs) and archive its MCP surface or register it as a distinct server with a distinct name. |
| Chronicle | **dope-memory** | Canonical. Wire capture (7.2); pass instance identity; archive WMA prototype; delete dead shim; rename dir `services/dope-memory/`; enable dope-context indexing after curated entries exist. |
| Retrieval | **dope-context** | Canonical. Fix healthcheck; add collection GC + cost guard; delete mock server; align complexity contract (shared scorer with Serena or drop the claim); wire into catalog with per-request workspace. |
| Code intel | **Serena = upstream wrapper** (short term) | Deployed reality becomes documented reality. The 45-tool local candidate is archived or promoted later via ADR + proof — not left ambient. Its 6 write tools stay out of any default profile per the sanctioned contract. |
| Reasoning | **PAL standalone** | Keep, but managed: `ensure-pal.sh`, real healthcheck, referenced in H3 remediation; delete both unconsumed compose variants; dedupe registry keys. |
| Research | **gptr-mcp upstream clone** | Keep; unify healthcheck; archive in-repo twin. |
| Quick search | **exa** | Decide once: wire natively (`http://localhost:3011/mcp` in catalog, fix the litellm-exec entry) or retire the service and update doctrine to WebSearch. Recommendation: wire — the server is real and the doctrine wants it. |
| Desktop | **desktop-commander** | Delete the container facade; if the capability matters, run the actual upstream DesktopCommanderMCP on the host. |
| External projection | **dcp-readonly-facade** | Close G1 (wire 3 tools + contract test `exposed == TOOL_CONTRACT`); Phase-2 minimal MCP-JSON-RPC read bridge for dope-context; register in catalog as operator-run stdio; add inventory-freshness CI gate. |
| Lane engine | **decide** | Wire `decide_lane()` into a real dispatch point (`dopemux dcp lane` + task-packet intake) or ADR it to the design shelf. Latent security is not security. |
| Kill list | mcp-integration-bridge, mcp-client, `services/router/`, gptr in-repo server, dope-memory stdio shim, `simple_server.py`, dead config writers/scripts, conport upstream wrapper path, 2 compose PAL variants, serena phantom wrapper | Archive under `SYSTEM_ARCHIVE/` or delete; remove Dockerfiles so nothing dead is startable (the bridge leaks secrets if revived). |

### 7.2 The memory spine fix (highest leverage)
> **Correction (2026-07-03, from implementation):** the WMA promotion allowlist (`services/working-memory-assistant/promotion/promotion.py`) is exactly `{decision.logged, task.completed, task.failed, task.blocked, error.encountered, workflow.phase_changed, manual.memory_store}`. There is **no** `session.started`/`session.ended`/`file.edited` promotion handler — those are heartbeat (non-promotable) by design. So this is **not** a one-import fix: hooks can only contribute `error.encountered` (now wired). Populating the chronicle end-to-end requires emitting the promotable types at their real sources (ConPort decision logging → `decision.logged`; workflow-kernel/task-orchestrator transitions → `task.*`/`workflow.phase_changed`). Step 1 below is revised accordingly.
1. **Done**: `native_hooks.py` PostToolUseFailure → `capture_client.emit_capture_event(event_type="error.encountered")`, fail-open, tested. **Follow-on**: wire `decision.logged` at the ConPort decision path and `task.*`/`workflow.phase_changed` at the workflow-transition source — these are what actually fill `work_log_entries`.
2. Rate-limit/drop `session-active` heartbeats; backfill/normalize `instance_id`.
3. `/decision`, `/caveat`, `/followup` append dope-memory mirror receipts (Trinity Rule 1 beyond the gated CLI).
4. After curated entries exist, flip `ENABLE_DOPECONTEXT_INDEX=true` with provenance pointers (Rule 2), completing the Trinity loop.

### 7.3 Invariants to enforce (currently fiction)
- ConPort append-only decisions: one migration (REVOKE + trigger). Either enforce INV-MEM-002/003/004 or delete them from doctrine.
- No GET mutates (packet 107; `DOPEMUX_AUTO_FORK_PROGRESS` default off).
- Every server: real healthcheck = capability probe, loopback bind, identity-required requests.
- CI: catalog↔generated-config drift gate; command↔tool-surface drift gate; backend-surface↔facade-inventory freshness gate.

---

## 8. Phased implementation plan (packet-ready)

**Phase 0 — Stop the bleeding (1–2 days, no architecture)**
0.1 Fix fake healthchecks (pal `exit 0`, dope-context `|| exit 0`). 0.2 `ensure-pal.sh` + H3 remediation pointer. 0.3 Fix `_ensure_schema` fail-open verify. 0.4 Dedupe `src/dopemux/mcp/registry.yaml` duplicate keys. 0.5 Quarantine kill-list dead code (DEPRECATED markers, remove Dockerfiles). 0.6 Fix or delete the three broken wrappers (conport→in-repo server, dope-context path/env, serena phantom path).

**Phase 1 — Single source of truth (≈1 week)**
1.1 Unified catalog schema + merge of three registries. 1.2 Codegen for `.mcp.json` / global / Codex / compose env / doctrine docs. 1.3 `dopemux mcp ensure` (+ `--fast`), H3 hook calls it. 1.4 CI drift gates (catalog↔configs, commands↔tool surfaces). 1.5 Orchestrator auto-start + truth-pack regen at v3.8.0. 1.6 exa decision executed; desktop-commander deleted/replaced.

**Phase 2 — Memory spine (≈1 week, parallel with 1)**
2.1 native_hooks→capture_client (the one-import fix) + heartbeat rate-limit. 2.2 Instance identity per-request (dope-memory + conport); compose passes `DOPE_MEMORY_INSTANCE_ID`. 2.3 Skill-layer mirror receipts. 2.4 Chronicle validation: recap returns real content (acceptance test). 2.5 Enable dope-context decision indexing.

**Phase 3 — Canonical surfaces (1–2 weeks)**
3.1 ConPort packets 106/107/201/202 + append-only enforcement decision. 3.2 Serena single-surface ADR + archive/promote. 3.3 Complexity-scoring unification or claim removal. 3.4 Qdrant GC + Voyage cost guard. 3.5 Loopback binds fleet-wide.

**Phase 4 — DCP activation (≈1 week)**
4.1 Close facade G1 + contract test. 4.2 dope-context MCP-JSON-RPC read bridge. 4.3 Lane-engine wire-or-shelve ADR. 4.4 Inventory-freshness CI gate. 4.5 Register facade in catalog.

**Phase 5 — Prove it**
5.1 End-to-end acceptance: fresh worktree → `dopemux mcp ensure` → all planes green → decision logged → mirrored → recapped → retrieved. 5.2 Docs reconciliation (regenerate doctrine; mark aspirational ADHD automation as such everywhere). 5.3 Proof bundles per packet per AGENTS.md §8/§9.

Sequencing rationale: Phase 0 items are independently safe; Phase 1 must precede any config rewrites (otherwise sync tools keep regressing reality); Phase 2 is independent and highest user-visible value; Phases 3–4 ride on the catalog + CI gates so fixed things stay fixed.

---

## 9. Governance footer

**Authority used**: runtime code/config (primary), ADRs + docs/03-reference (design intent), prior audit reports (docs/05-audit-reports), task-packet series, proof/ dirs, user/global doctrine files, live chronicle ledger (read-only SQL), `~/.claude.json` + `~/.codex/config.toml` (read-only).
**Validation**: PASS — static code/config verification across 8 agents (file:line-cited in agent reports); facade suite result (537/539) as reported by the DCP agent. FAIL — none run. NOT_RUN — all live-runtime behavior (Docker daemon down): container health, MCP handshakes, v3.8.0 tool surface, per-worktree compose stacks. These are labeled INFERRED wherever cited.
**Remaining uncertainty**: upstream-image internals (orchestrator v3.8.0, oraios serena) not inspected; `~/.claude.json` per-project sections beyond top-level keys; whether any external process currently depends on the shadow surfaces slated for the kill list (verify before deletion); exact effort estimates are directional.
**Rollback**: this document is additive; delete the file to roll back. No other files touched.
