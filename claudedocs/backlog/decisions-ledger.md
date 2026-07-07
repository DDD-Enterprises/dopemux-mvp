# Backlog Decisions Ledger

**Date**: 2026-07-07 · **Owner**: operator (houston@krohman.org) · **Status**: RESOLVED (frozen inputs for packet authoring)
**Purpose**: the frozen decisions that convert thread + PR findings into Task Packets. Every gate below is resolved; each row names the resulting packet(s). This ledger is authoritative for the `DMX-*` backlog series; where a formal ADR is warranted, a `DMX-ADR-*` packet authors it.

**Provenance loose-end**: MCF-005/006 were also recorded in commit `bd85e784c` on branch `claude/memory-context-fabric`, which is **unmerged** (PR #1011 merged an earlier commit). Main's `claudedocs/plans/2026-07-04-memory-context-fabric-build-plan.md` still shows "DECISION REQUIRED" for 005/006. This ledger supersedes that; `bd85e784c` should also be landed or folded into a follow-up.

| # | Gate | Decision | Rationale | Resulting packet(s) |
|---|---|---|---|---|
| MCF-005 | Semantic memory home | **Defer, provisionally Option A** (dope-context `memory_{hash}` projection); decide after 002–004 with real chronicle data | Recall-quality gap only measurable once chronicle has content; Voyage is external → privacy gate | `DMX-ADR-001`, `DMX-MCF-005` (planning, deferred) |
| MCF-006 | ConPort graph exposure | **Option A** — `graph.neighbors` + genealogy on active Docker ConPort, **spike-gated** (AGE data-layer spike is mandatory Task 1) | Decision-genealogy provenance is worth it; AGE writer path unproven → de-risk first | `DMX-ADR-005`, `DMX-MCF-006` (spike+spec) |
| MCF-002 | Redaction-failure quarantine location | **Non-queryable dope-memory table** (not a file path) | Keeps quarantine inside the store; requires a schema migration + non-searchable guardrail | `DMX-MCF-002` (adds migration sub-step) |
| FLEET | Canonical PAL management | **Manage** via `ensure-pal.sh` + real capability healthcheck + compose integration | PAL is load-bearing (`required=true`); must not stay off-compose/unmanaged | `DMX-FLEET-P0-002` |
| FLEET | exa | **Retire** (already shipped in #1002) | Zero consumers, broken catalog target; WebSearch fallback in place | `DMX-FLEET-P1-006` (doctrine + dead-config cleanup) |
| FLEET | Complexity scoring (3 unwired scorers) | **Unify** onto one canonical scorer | Keeps ADHD complexity-aware UX alive; which scorer = the planning packet's investigation | `DMX-ADR-004`, `DMX-FLEET-P3-003` (planning) |
| FLEET | Serena surface | **Promote local 45-tool candidate** via ADR (6 write tools out of default profile) | Canonicalizes the richer surface; **unblocks dormant ADHD-module resurrections** | `DMX-ADR-002`, `DMX-FLEET-P3-002`, `DMX-ADHD-WIRE-005/006` |
| FLEET | ConPort vector search (`mem.*` in `memory_server.py`) | **Do not build in ConPort** — dope-context owns semantic (per MCF-005) | Trinity law assigns semantic retrieval to dope-context; avoid a second authority | closed; no packet (noted in `DMX-ADR-001`) |
| DCP | Lane engine `decide_lane()` | **Wire as real dispatch** (`dopemux dcp lane` + task-packet intake) | "Latent security is not security"; wiring makes the routing design real | `DMX-ADR-003`, `DMX-FLEET-P4-003` |
| FLEET | desktop-commander (broken container facade) | **Run real upstream DesktopCommanderMCP on the host** (replace facade) | osascript-in-Linux facade fails every call while healthcheck lies; operator uses desktop tooling | `DMX-FLEET-P0-007` |
| FEAT | mcp-capture (built, unregistered) | **Fold into `capture_client.py`** (no separate server) | Memory-spine already routes capture through capture_client; one capture path, less fleet surface | folded into `DMX-FLEET-P2-001` |

## Out of scope by prior settlement (no packets)
documentation_search (drop) · Mem0 hosted-cloud memory (forbidden) · PRD→tasks auto-gen (disabled by design; `/dx:prd-parse` is sanctioned) · Leantime bidirectional write-sync (PM-authority-gated) · mcp-integration-bridge revival (secret-leaking; clean-rewrite only) · Multi-Team Coordination (dormant-by-design for single-operator MVP) · Sprint auto-planning (ConPort half unbuilt; revisit on need).
