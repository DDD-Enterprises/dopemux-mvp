# AGENTS.md

## 1. Purpose

This is an operator-control document for the current repo state. It is meant to help you act safely without inventing a unified architecture, smoothing over drift, or hiding `UNKNOWN`.

Repo truth beats docs.

## 2. Read This First

- The task packet names `RULES.md`, `PROJECT.md`, `ARCHITECTURE.md`, `SYSTEM_BOUNDARIES.md`, `PM_PLANE.md`, `DOC_TRUST_MAP.md`, and `DOCS_VS_REPO_DIFF.md` as allowed authority.
- In this checkout, the exact packet-named top-level files were not present during this rewrite, but derived tracked references now exist for system boundaries and the PM plane under `docs/03-reference/`.
- The repo-truth artifacts present in this pass are tracked in:
  - `docs/03-reference/truth/truth-systems.md`
  - `docs/03-reference/truth/truth-canonicals.md`
  - `docs/03-reference/truth/truth-gaps.md`
  - `docs/03-reference/truth/truth-interfaces.md`
  - `docs/03-reference/truth/truth-data-events.md`
  - `docs/03-reference/truth/truth-scope.md`
- Do not invent the contents of `RULES.md`, `DOC_TRUST_MAP.md`, or any missing packet-named top-level file. For system boundaries and the PM plane, use the tracked derived references under `docs/03-reference/`, but repo truth beats docs.

## 3. Canonical Operator Surfaces

- `dopemux` CLI is the main operator control plane.
- `services/repo-truth-extractor/run_extraction_v5.py` is the canonical repo-truth extraction path.
- `scripts/dopetask` is the runtime authority for dopetask. `scripts/taskx` is a compatibility shim, not a separate runtime.
- `services/task-orchestrator/app/main.py` is the intended task-orchestrator runtime surface from this pass, but runtime packaging and Docker alignment are unresolved.
- `services/dopecon-bridge/dopecon_bridge/routes.py` exposes important routing and compatibility surfaces, but bridge is not authority.

## 4. PM Plane

- PM truth is split across multiple surfaces. This pass does not support a single-file PM authority claim.
- `services/task-orchestrator` is the workflow coordination and PM write-normalization surface.
- `src/dopemux/pm/writes.py` shows PM writes crossing Leantime, task-orchestrator, ConPort, and dope-memory mirror receipts.
- Agents do not own PM truth.
- Bridge is not authority for PM truth. Treat `/route/pm` as routing, not as canonical state.
- `PM_PLANE.md` is named by the packet, and the tracked derived PM-plane reference is `docs/03-reference/planes/pm/pm-plane.md`. Use the tracked doc as a secondary authority check, not as a replacement for runtime truth.

## 5. Memory and Retrieval

- `dope-memory` is the durable evidence-preserving memory sink.
- `dope-memory` is not the canonical PM status authority.
- `conport` is the structured memory, graph, and semantic retrieval surface.
- `dope-context` is the deterministic code and docs retrieval surface.
- `working-memory-assistant` overlaps with memory-related responsibilities, but this pass did not prove it is the canonical durable runtime for the same authority slice.

## 6. Agent Systems

- Agent system authority is `UNKNOWN`.
- This repo contains at least three agent families:
  - `services/agents`
  - `src/dopemux/agent_orchestrator.py`
  - `services/task-orchestrator/task_orchestrator/agents`
- Do not assume one unified agent architecture.
- Do not route operator decisions through agent abstractions unless you verify the exact runtime path in code and config.
- Agents do not own PM truth.

## 7. Working Rules

- Start from runtime code, config, and tests. Do not start from hopeful docs.
- Prefer canonical writers over bridges, adapters, aliases, and shims.
- Mark `UNKNOWN` explicitly when canonicality is unresolved.
- Treat `RULES.md` as a named-but-absent authority doc in this checkout. For system boundaries, use `docs/03-reference/systems/system-boundaries.md` as the tracked derived reference.
- If a doc conflicts with runtime behavior, repo truth beats docs.

## 8. Docs Trust

- For this rewrite pass, the usable truth docs are the tracked `docs/03-reference/truth/*` references, with `truth-systems.md`, `truth-canonicals.md`, and `truth-gaps.md` carrying the strongest direct operator guidance.
- `DOC_TRUST_MAP.md` and `DOCS_VS_REPO_DIFF.md` were named in the packet but not present in this checkout.
- Older docs and README surfaces may drift from runtime reality. Escalate the drift instead of normalizing it away.
- Repo truth beats docs.

## 9. Known Dangers

- `dopecon-bridge` exposes broad surfaces that can look authoritative. It is not canonical task, workflow, decision, or progress authority.
- Task-orchestrator runtime authority is conflicted across `app/main.py`, `task_orchestrator/app.py`, and the Dockerfile.
- Memory-related surfaces overlap across `dope_memory_main.py`, `main.py`, and `mcp/server.py`.
- Agent responsibilities are duplicated across multiple families, and agent authority is `UNKNOWN`.
- `scripts/dopetask` is the observed runtime, but operator naming still drifts through TaskX language.
- MCP and proxy config surfaces are inconsistent in places, including stale port assumptions and missing launch targets.


<claude-mem-context>
# Memory Context

# [dopemux-mvp] recent context, 2026-04-23 10:42am PDT

Legend: 🎯session 🔴bugfix 🟣feature 🔄refactor ✅change 🔵discovery ⚖️decision 🚨security_alert 🔐security_note
Format: ID TIME TYPE TITLE
Fetch details: get_observations([IDs]) | Search: mem-search skill

Stats: 50 obs (18,808t read) | 1,725,644t work | 99% savings

### Apr 23, 2026
2731 9:33a ✅ Initial repository and branch verification for RTE audit
2732 " ✅ Verification of audit artifact integrity
2733 " ✅ Verification of audit artifact diff
2734 " 🔵 Identified canonical RTE runtime source
2735 " 🔵 Established audit scope boundaries and authority documents
2737 " 🔵 Confirmed project root directory
2740 " ✅ Updated audit plan status
2741 " 🔵 Confirmed repository remote origin
2743 " 🔵 Confirmed presence of .dopetaskroot marker
2744 " 🔵 Confirmed current branch
2750 " 🔵 Repository status indicates divergence from remote
2753 " 🔵 AGENTS.md content analyzed
2755 " 🔵 Truth Canonicals document analyzed
2756 " 🔵 Truth Systems document analyzed
2758 " 🔵 Truth Gaps document analyzed
2759 " 🔵 Truth Interfaces document analyzed
2761 " 🔵 Truth Scope document analyzed
2764 " 🔵 System Boundaries document analyzed
2766 " 🔵 PM Plane document analyzed
2826 9:45a 🔵 Dopemux MVP Project Root Confirmed
2828 " 🔵 Dopemux Documentation Search Yields Relevant Architecture Files
2819 9:46a ⚖️ Adopt Dopemux Adaptive Ingress Plane Architecture
2820 " ⚖️ Dopemux Architecture: Gateway-Shim Split and Authority Separation
2821 " ⚖️ Dopemux Gateway and Shim Responsibilities Defined
2822 " ⚖️ Dopemux Canonical Event Model and Taxonomy
2823 " ⚖️ Dopemux Service-Tier Consolidation Policy
2824 " ⚖️ Dopemux Migration Plan for Adaptive Ingress Gateway
2833 " 🔵 Dopemux ADR Index and PM-Plane Authority Spine
2834 " 🔵 Dopemux ADR Light Template Structure
2836 " 🔵 Dopemux Architecture Documentation Files
2838 " 🔵 Dopemux ADR and Reference Documentation Snippets
2840 " 🔵 Dopemux Multi-Agent Ingress Architecture Design
2841 " 🔵 Dopemux ADR Record Template Structure
2842 " 🔵 Dopemux PM Plane Authority Boundaries Defined
2843 " 🔵 Dopemux Multi-Agent Ingress Architecture - Detailed Implementation and Migration
2844 " 🔵 Dopemux Multi-Agent Ingress Architecture Document Line Count
2848 " 🔵 Dopemux Multi-Agent Ingress Architecture - Failure Modes, Open Questions, and Task Packet Revisions
2849 " 🔵 Dopemux Multi-Agent Ingress Architecture - Failure Modes, Open Questions, and Task Packet Revisions
2892 9:54a ✅ Initializing Gemini Deep PAL Audit for RTE
2893 " ✅ Establishing Audit Target and Scope Boundaries
2894 " ✅ Auditing RTE Execution Logic and Gate Behavior
2895 " ✅ Auditing Prompt Architecture and Canonicality
2896 " ✅ Auditing Model Selection, Routing, and Repair Mechanisms
2897 " ✅ Auditing Operator UX and Observability
2898 " ✅ Finalizing Deep Audit Verdict and Action Map
2899 9:55a 🔵 Repository Identity and State Confirmation
2900 " 🔵 Detailed Repository State and Modified Files
2902 " 🔵 Locating Canonical RTE Runtime and Configuration Directories
S80 Examine `llm_runtime.py` for LLM interaction and routing implementation. (Apr 23 at 10:00 AM)
S81 Audit RTE implementation: LLM interaction, routing, and reporting. (Apr 23 at 10:00 AM)
S82 Audit RTE implementation: Locate UI classes in `run_extraction_v5.py`. (Apr 23 at 10:00 AM)
S83 Audit RTE implementation: Investigate 'UNKNOWN' value handling. (Apr 23 at 10:00 AM)
S84 Audit RTE implementation: Investigate 'UNKNOWN' value usage and provenance integrity. (Apr 23 at 10:00 AM)
S85 Finalize audit report and proof artifact for RTE Gemini Deep PAL. (Apr 23 at 10:01 AM)
S86 Draft final audit report for RTE Gemini Deep PAL. (Apr 23 at 10:01 AM)
S87 Update Task Packet Index after audit completion. (Apr 23 at 10:01 AM)
S88 Update Task Packet Index to reflect audit completion. (Apr 23 at 10:01 AM)
S89 Complete RTE Deep PAL Audit and document findings. (Apr 23 at 10:28 AM)
3039 10:29a 🔵 UI class initialization and rich output configuration
3063 10:42a 🟣 Establish `dopemux rte` as canonical operator entrypoint

Access 1726k tokens of past work via get_observations([IDs]) or mem-search skill.
</claude-mem-context>