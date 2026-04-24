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

# [dopemux-mvp] recent context, 2026-04-23 5:04pm PDT

Legend: 🎯session 🔴bugfix 🟣feature 🔄refactor ✅change 🔵discovery ⚖️decision 🚨security_alert 🔐security_note
Format: ID TIME TYPE TITLE
Fetch details: get_observations([IDs]) | Search: mem-search skill

Stats: 50 obs (15,626t read) | 1,599,237t work | 99% savings

### Apr 23, 2026
3175 12:28p ✅ Refactored Phase S Prompt Mode Handling in `rte_promptset.py`
3177 " ✅ Read Code Snippet from `run_extraction_v5.py`
3178 " ✅ Read Snippet of `run_extraction_v5.py` (Lines 1030-1055)
3180 " ✅ Updated `get_phase_prompts` for Phase S Registry Resolution
3208 12:35p 🔴 Add debug print to PAL file discovery logic
3210 " 🔴 Add debug print to PAL file discovery logic in build_config
3211 12:36p ✅ Rerun validator with debug print enabled
3212 " 🔵 PAL validation file successfully discovered
3214 " 🔵 Locate PAL validation evaluator function
3215 " 🔵 Locate PAL validation evaluator function
3216 " 🔵 Examine PAL validation evaluator function
3217 " 🔵 Examine PAL validation evaluator function
3218 " ✅ Refine PAL file discovery and condition reporting
3219 " ✅ Enhance PAL validation condition with file path
3207 12:39p 🔵 pal_validation.json file confirmed to exist
3227 12:44p 🔵 Audit target and scope established
S241 Search for the definition of `prompt_root` in `services/repo-truth-extractor/rte_promptset.py`. (Apr 23 at 12:53 PM)
S242 List the contents of the `services/repo-truth-extractor/rte_promptset.py` file. (Apr 23 at 12:53 PM)
S243 List the contents of the `services/repo-truth-extractor/promptsets/v4/prompts` directory. (Apr 23 at 12:53 PM)
S244 Read the content of `services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_A1_INSTRUCTION_SURFACES.md`. (Apr 23 at 12:53 PM)
S245 Read the content of the prompt file `services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_A1_INSTRUCTION_SURFACES.md`. (Apr 23 at 12:53 PM)
S246 Analyze the relationship between phase definitions and prompt markdown files. (Apr 23 at 12:53 PM)
S247 Analyze the architecture of the Repo Truth Extractor (RTE) based on the provided files. (Apr 23 at 12:53 PM)
S248 Read the first 200 lines of `services/repo-truth-extractor/promptsets/v4/promptset.yaml`. (Apr 23 at 12:53 PM)
S249 Read the first 200 lines of `services/repo-truth-extractor/promptsets/v4/promptset.yaml`. (Apr 23 at 12:53 PM)
S250 Perform final mapping of prompt/runtime contracts and assess Phase S version-mix risk. (Apr 23 at 12:53 PM)
3242 1:03p 🔵 MCP Analyze Tool Request Timed Out
3243 " 🔵 Prompt Architecture Analysis Confirmed
3235 1:04p ✅ Initiate Gemini Deep PAL Audit for RTE Implementation
3236 " ✅ Define Initial Audit Setup and Scope Boundaries
3237 " ✅ Audit RTE Execution Logic and Gate Behavior
3238 " ✅ Audit Prompt Architecture and Canonicality
3239 " ✅ Audit Model Selection, Routing, and Repair Mechanisms
3240 " ✅ Audit Operator User Experience and Observability
3241 " ✅ Finalize Audit Verdict and Corrective Actions
3252 1:13p 🔵 MCP Analyze Tool Request Timed Out Again
3244 1:14p ✅ Initiate Gemini Deep PAL Audit for RTE Implementation
3245 " ✅ Define Initial Audit Setup and Scope Boundaries
3246 " ✅ Audit RTE Execution Logic and Gate Behavior
3247 " ✅ Audit Prompt Architecture and Canonicality
3248 " ✅ Audit Model Selection, Routing, and Repair Mechanisms
3249 " ✅ Audit Operator User Experience and Observability
3250 " ✅ Finalize Audit Verdict and Corrective Actions
3251 " 🔵 MCP Analyze Tool Request Timed Out
3253 " 🔵 Prompt Architecture Analysis Simplified
3261 1:24p 🔵 MCP Analyze Tool Timeout
3254 " ✅ RTE Gemini Deep PAL Audit Task Packet
3255 " ✅ RTE Audit Task Packet - Step 1: Establish Audit Target and Scope
3256 " ✅ RTE Audit Task Packet - Step 2: Audit Execution Logic and Gates
3257 " ✅ RTE Audit Task Packet - Step 3: Audit Prompt Architecture and Canonicality
3258 " ✅ RTE Audit Task Packet - Step 4: Audit Model Selection, Routing, and Repair
3259 " ✅ RTE Audit Task Packet - Step 5: Audit Operator UX and Observability
3260 " ✅ RTE Audit Task Packet - Step 6: Produce Final Verdict and Action Map
3262 " 🔵 RTE Prompt and Gating Assessment
3264 1:34p 🔵 MCP Thinkdeep Tool Timeout
3263 " 🔵 RTE Prompt and Gating Assessment
3265 " 🔵 RTE Prompt Audit Finalization
3267 1:44p 🔵 MCP Tool Timeout During Prompt Audit
3266 " ✅ RTE Gemini Deep PAL Audit Task Packet
3268 " 🔵 Prompt Audit Findings for RTE

Access 1599k tokens of past work via get_observations([IDs]) or mem-search skill.
</claude-mem-context>