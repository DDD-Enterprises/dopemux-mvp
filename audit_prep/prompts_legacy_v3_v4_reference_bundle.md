# Prompt Bundle: Legacy v3 Reference Bundle

## Prompt
- prompt_id: rte_v3_prompt_a0_repo_control_inventory___partition_plan
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: A
- step: A0
- short_name: Repo Control Inventory / Partition Plan
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_A0_REPO_CONTROL_INVENTORY___PARTITION_PLAN.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: routing/classification
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
MODE: Mechanical extractor, zero interpretation.
INPUT: repo working tree (top-level), include hidden dirs shown in ls -la (not .git contents).
OUTPUT:
- REPOCTRL_INVENTORY.json: list files (path, ext, size, mtime, sha256 if available), plus first 30 non-empty lines for text.
- REPOCTRL_PARTITIONS.json: partitions by type:
  - instructions/prompts (CLAUDE.md, AGENTS.md, .claude/**, docs/** instruction files)
  - mcp/proxy configs (mcp-proxy-config*, start-mcp-servers.sh, compose/**)
  - hooks (.githooks/**, scripts called by hooks)
  - routers/provider ladders (litellm.config*, any router yaml/toml/json)
  - compose/service graphs (compose.yml, docker-compose*.yml, compose/**)
  - CI/gates (.github/**, pre-commit, ruff/mypy/pytest configs)
  - taskx surfaces (.taskx/**, .taskx-pin, task packets in repo)
RULES: JSON only. Every item must include path + line_range (or null if binary).

---

## Prompt
- prompt_id: rte_v3_prompt_a1_instruction_surfaces
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: A
- step: A1
- short_name: Instruction Surfaces
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_A1_INSTRUCTION_SURFACES.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: routing/classification
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PHASE A1 — INSTRUCTION SURFACES (REPO)
Model: Gemini Flash 3
Goal: Produce REPO_INSTRUCTION_SURFACE.json + REPO_INSTRUCTION_REFERENCES.json

Hard rules:
- Extract ONLY what is explicitly present in files.
- Every extracted item MUST include evidence: {path, anchor_excerpt<=200 chars}.
- No guessing. If unclear, record UNKNOWN with evidence showing ambiguity.

Inputs:
- Partition content from A0 P0 partitions: instruction docs, agent files, custom instructions directories.

Task:
1) Build REPO_INSTRUCTION_SURFACE.json:
   Identify all instruction-bearing files and normalize into:
   - instruction_sources[] items:
     - id (stable, e.g., INSTR_0001)
     - path
     - kind (one of: "claude_system", "agent_profile", "tooling_instructions", "prompt_template", "workflow_playbook", "other")
     - scope (repo-wide / project-specific / tool-specific)
     - referenced_tools (list of strings found literally: e.g., "conport", "serena", "mcp", "litellm", "taskx")
     - declared_behaviors (list of short literal statements, each with anchor_excerpt)
     - declared_boundaries (list, each with anchor_excerpt)
     - declared_dataflows (list, each with anchor_excerpt)
   Determinism: sort by path, then by first appearance.

2) Build REPO_INSTRUCTION_REFERENCES.json:
   A cross-reference map of “instruction mentions -> targets”.
   Extract literal references to:
   - services (conport, serena, dope-context, dashboard, orchestrator, proxy)
   - MCP servers/tools
   - router/provider ladders
   - scripts/commands
   Output:
   - references[]:
     - ref_type ("service"|"command"|"file_path"|"env_var"|"mcp_server"|"model"|"other")
     - ref_value (literal string)
     - source_path
     - anchor_excerpt

Output files:
- REPO_INSTRUCTION_SURFACE.json
- REPO_INSTRUCTION_REFERENCES.json

---

## Prompt
- prompt_id: rte_v3_prompt_a2_mcp_server_defs
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: A
- step: A2
- short_name: Mcp Server Defs
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_A2_MCP_SERVER_DEFS.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: routing/classification
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT: A2 - MCP Server Definitions

Phase: A
Step: A2

Outputs:
- REPO_MCP_SERVER_DEFS.json

Mode: extraction
Strict: evidence_only
Format: JSON only (no markdown fences)

Hard rules:
1) Do NOT invent. If not present, write "UNKNOWN".
2) Every non-trivial field must include "evidence" with source_path and either key_path or excerpt.
3) Emit ONLY valid JSON. No commentary.

Input:
You will receive repo control-plane files. Extract only what is explicitly evidenced.

Required JSON shape:
{
  "artifact": "REPO_MCP_SERVER_DEFS.json",
  "phase": "A",
  "step": "A2",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "mcp:<name>",
      "server_name": "...",
      "command": "...",
      "args": ["..."],
      "env": ["..."],
      "enabled": true,
      "source_path": "...",
      "evidence": [
        {
          "source_path": "...",
          "key_path": "...",
          "excerpt": "..."
        }
      ]
    }
  ],
  "unknowns": ["..."]
}

Extract:
- MCP server definitions: name, command, args, env var names, enabled/disabled, cwd/root/allowed paths if present
- Any explicit per-server capabilities/notes
- Source locations and config keys

---

## Prompt
- prompt_id: rte_v3_prompt_a3_mcp_proxy_surface
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: A
- step: A3
- short_name: Mcp Proxy Surface
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_A3_MCP_PROXY_SURFACE.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: routing/classification
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT: A3 - MCP Proxy Surface

Phase: A
Step: A3

Outputs:
- REPO_MCP_PROXY_SURFACE.json

Mode: extraction
Strict: evidence_only
Format: JSON only (no markdown fences)

Hard rules:
1) Do NOT invent. If not present, write "UNKNOWN".
2) Every non-trivial field must include "evidence" with source_path and either key_path or excerpt.
3) Emit ONLY valid JSON. No commentary.

Input:
You will receive repo control-plane files. Extract only what is explicitly evidenced.

Required JSON shape:
{
  "artifact": "REPO_MCP_PROXY_SURFACE.json",
  "phase": "A",
  "step": "A3",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "mcp-proxy:<name_or_path>",
      "proxy_name": "...",
      "endpoint": "...",
      "upstream_targets": ["..."],
      "routes": ["..."],
      "auth_method": "...",
      "evidence": [
        {
          "source_path": "...",
          "key_path": "...",
          "excerpt": "..."
        }
      ]
    }
  ],
  "unknowns": ["..."]
}

Extract:
- Proxy config between clients/Dopemux and MCP servers
- Endpoints, routing rules, upstream targets, auth handling (only if explicit)
- Config search order hints only if explicit

---

## Prompt
- prompt_id: rte_v3_prompt_a4_router_surface
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: A
- step: A4
- short_name: Router Surface
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_A4_ROUTER_SURFACE.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: routing/classification
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT: A4 - Repo Router Surface

Phase: A
Step: A4

Outputs:
- REPO_ROUTER_SURFACE.json

Mode: extraction
Strict: evidence_only
Format: JSON only (no markdown fences)

Hard rules:
1) Do NOT invent. If not present, write "UNKNOWN".
2) Every non-trivial field must include "evidence" with source_path and either key_path or excerpt.
3) Emit ONLY valid JSON. No commentary.

Input:
You will receive repo control-plane files. Extract only what is explicitly evidenced.

Required JSON shape:
{
  "artifact": "REPO_ROUTER_SURFACE.json",
  "phase": "A",
  "step": "A4",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "route:<stable_id>",
      "provider": "...",
      "model": "...",
      "trigger": "...",
      "fallback_ladder": ["..."],
      "retry_policy": "...",
      "rate_limit_policy": "...",
      "profile": "...",
      "evidence": [
        {
          "source_path": "...",
          "key_path": "...",
          "excerpt": "..."
        }
      ]
    }
  ],
  "unknowns": ["..."]
}

Extract:
- Provider/model routing tables, fallback ladders, profiles, routing rules
- Any retry/backoff/rate-limit knobs if present
- Routing policy files if present

---

## Prompt
- prompt_id: rte_v3_prompt_a5_hooks_surface
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: A
- step: A5
- short_name: Hooks Surface
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_A5_HOOKS_SURFACE.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: routing/classification
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT: A5 - Repo Hooks Surface

Phase: A
Step: A5

Outputs:
- REPO_HOOKS_SURFACE.json

Mode: extraction
Strict: evidence_only
Format: JSON only (no markdown fences)

Hard rules:
1) Do NOT invent. If not present, write "UNKNOWN".
2) Every non-trivial field must include "evidence" with source_path and either key_path or excerpt.
3) Emit ONLY valid JSON. No commentary.

Input:
You will receive repo control-plane files. Extract only what is explicitly evidenced.

Required JSON shape:
{
  "artifact": "REPO_HOOKS_SURFACE.json",
  "phase": "A",
  "step": "A5",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "hook:<type>:<name>",
      "hook_type": "...",
      "trigger": "...",
      "command": "...",
      "invoked_paths": ["..."],
      "evidence": [
        {
          "source_path": "...",
          "key_path": "...",
          "excerpt": "..."
        }
      ]
    }
  ],
  "unknowns": ["..."]
}

Extract:
- Git hooks, pre-commit hooks, CI hooks, taskx/dopemux hooks
- Literal commands invoked, source file locations, triggering conditions if defined

---

## Prompt
- prompt_id: rte_v3_prompt_a6_compose_service_graph
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: A
- step: A6
- short_name: Compose Service Graph
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_A6_COMPOSE_SERVICE_GRAPH.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: routing/classification
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT: A6 - Compose Service Graph

Phase: A
Step: A6

Outputs:
- REPO_COMPOSE_SERVICE_GRAPH.json

Mode: extraction
Strict: evidence_only
Format: JSON only (no markdown fences)

Hard rules:
1) Do NOT invent. If not present, write "UNKNOWN".
2) Every non-trivial field must include "evidence" with source_path and either key_path or excerpt.
3) Emit ONLY valid JSON. No commentary.

Input:
You will receive repo control-plane files. Extract only what is explicitly evidenced.

Required JSON shape:
{
  "artifact": "REPO_COMPOSE_SERVICE_GRAPH.json",
  "phase": "A",
  "step": "A6",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "service:<name>",
      "service_name": "...",
      "image": "...",
      "build": "...",
      "env": ["..."],
      "ports": ["..."],
      "volumes": ["..."],
      "depends_on": ["..."],
      "networks": ["..."],
      "evidence": [
        {
          "source_path": "...",
          "key_path": "...",
          "excerpt": "..."
        }
      ]
    }
  ],
  "unknowns": ["..."]
}

Extract:
- Compose services: image/build, env names, volumes, ports, depends_on
- Networks and volumes
- Do not infer service meaning unless explicitly named

---

## Prompt
- prompt_id: rte_v3_prompt_a7_litellm_surface
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: A
- step: A7
- short_name: Litellm Surface
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_A7_LITELLM_SURFACE.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: routing/classification
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT: A7 - Repo LiteLLM Surface

Phase: A
Step: A7

Outputs:
- REPO_LITELLM_SURFACE.json

Mode: extraction
Strict: evidence_only
Format: JSON only (no markdown fences)

Hard rules:
1) Do NOT invent. If not present, write "UNKNOWN".
2) Every non-trivial field must include "evidence" with source_path and either key_path or excerpt.
3) Emit ONLY valid JSON. No commentary.

Input:
You will receive repo control-plane files. Extract only what is explicitly evidenced.

Required JSON shape:
{
  "artifact": "REPO_LITELLM_SURFACE.json",
  "phase": "A",
  "step": "A7",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "litellm:<stable_id>",
      "config_file": "...",
      "provider": "...",
      "model": "...",
      "env_var_requirements": ["..."],
      "budgets": ["..."],
      "rate_limits": ["..."],
      "cache_settings": ["..."],
      "logging_or_db": ["..."],
      "evidence": [
        {
          "source_path": "...",
          "key_path": "...",
          "excerpt": "..."
        }
      ]
    }
  ],
  "unknowns": ["..."]
}

Extract:
- LiteLLM config files/references, model/provider declarations
- Expected env var names only, budgets/rate limits/cache/logging/db settings if present

---

## Prompt
- prompt_id: rte_v3_prompt_a8_taskx_surface
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: A
- step: A8
- short_name: Taskx Surface
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_A8_TASKX_SURFACE.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: routing/classification
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT: A8 - Repo TaskX Surface

Phase: A
Step: A8

Outputs:
- REPO_TASKX_SURFACE.json

Mode: extraction
Strict: evidence_only
Format: JSON only (no markdown fences)

Hard rules:
1) Do NOT invent. If not present, write "UNKNOWN".
2) Every non-trivial field must include "evidence" with source_path and either key_path or excerpt.
3) Emit ONLY valid JSON. No commentary.

Input:
You will receive repo control-plane files. Extract only what is explicitly evidenced.

Required JSON shape:
{
  "artifact": "REPO_TASKX_SURFACE.json",
  "phase": "A",
  "step": "A8",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "taskx:<stable_id>",
      "invocation": "...",
      "config_file": "...",
      "packet_path": "...",
      "operator_surface": "...",
      "evidence": [
        {
          "source_path": "...",
          "key_path": "...",
          "excerpt": "..."
        }
      ]
    }
  ],
  "unknowns": ["..."]
}

Extract:
- .taskx files, taskx config, scripts/workflows invoking taskx
- Packet paths, instruction compilation/injection surfaces, operator profile surfaces

---

## Prompt
- prompt_id: rte_v3_prompt_a9_implicit_behavior_hints
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: A
- step: A9
- short_name: Implicit Behavior Hints
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_A9_IMPLICIT_BEHAVIOR_HINTS.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: routing/classification
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT: A9 - Repo Implicit Behavior Hints

Phase: A
Step: A9

Outputs:
- REPO_IMPLICIT_BEHAVIOR_HINTS.json

Mode: extraction
Strict: evidence_only
Format: JSON only (no markdown fences)

Hard rules:
1) Do NOT invent. If not present, write "UNKNOWN".
2) Every non-trivial field must include "evidence" with source_path and either key_path or excerpt.
3) Emit ONLY valid JSON. No commentary.

Input:
You will receive repo control-plane files. Extract only what is explicitly evidenced.

Required JSON shape:
{
  "artifact": "REPO_IMPLICIT_BEHAVIOR_HINTS.json",
  "phase": "A",
  "step": "A9",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "hint:<stable_id>",
      "hint_type": "...",
      "description": "...",
      "toggle_or_path": "...",
      "evidence": [
        {
          "source_path": "...",
          "key_path": "...",
          "excerpt": "..."
        }
      ]
    }
  ],
  "unknowns": ["..."]
}

Extract:
- Explicitly documented implicit behavior: config search order, default paths, if-file-exists toggles, env-var toggles, hidden coupling points when directly stated

---

## Prompt
- prompt_id: rte_v3_prompt_a99_merge___qa
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: A
- step: A99
- short_name: Merge / Qa
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_A99_MERGE___QA.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: routing/classification
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT: A99 - Merge + QA (Repo Control Plane)

Phase: A
Step: A99

Outputs:
- REPO_INSTRUCTION_SURFACE.json
- REPO_INSTRUCTION_REFERENCES.json
- REPO_MCP_SERVER_DEFS.json
- REPO_MCP_PROXY_SURFACE.json
- REPO_ROUTER_SURFACE.json
- REPO_HOOKS_SURFACE.json
- REPO_IMPLICIT_BEHAVIOR_HINTS.json
- REPO_COMPOSE_SERVICE_GRAPH.json
- REPO_LITELLM_SURFACE.json
- REPO_TASKX_SURFACE.json
- REPOCTRL_NORM_MANIFEST.json
- REPOCTRL_QA.json

Mode: merge_qa
Strict: evidence_only
Format: JSON only (no markdown fences)

Hard rules:
1) Do NOT invent. If not present, write "UNKNOWN".
2) Every non-trivial field must include "evidence" with source_path and either key_path or excerpt.
3) Emit ONLY valid JSON. No commentary.

Input:
You will receive raw outputs from steps A0-A99. Merge and normalize into the exact output artifact names above.
Summarize only what is present.

Required JSON shape:
{
  "artifact": "REPOCTRL_NORM_MANIFEST.json",
  "phase": "A",
  "step": "A99",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "manifest:<artifact_name>",
      "artifact_name": "...",
      "count": 0,
      "sha256": "...",
      "evidence": [
        {
          "source_path": "...",
          "key_path": "...",
          "excerpt": "..."
        }
      ]
    }
  ],
  "unknowns": ["..."]
}

Task:
1) Produce deterministic manifest of artifacts (name/count/sha256 when available).
2) Produce REPOCTRL_QA.json with:
- expected artifacts present/missing by filename
- empty artifact detection (0 items)
- duplicate evidence detection
- partition coverage counts (ok/failed)
- parse failures referenced by filename when present

Rules:
- No inference; summarize only provided artifacts.

---

## Prompt
- prompt_id: rte_v3_prompt_h0_inventory___partition_plan
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: H
- step: H0
- short_name: Inventory / Partition Plan
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_H0_INVENTORY___PARTITION_PLAN.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: routing/classification
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# Phase H0: Home Control Plane Inventory + Partition Plan

You are running inside the Dopemux extraction pipeline.

Goal:
- Inventory only the HOME control-plane relevant files found in the provided context.
- Produce a deterministic partition plan for subsequent Phase H steps.

Hard rules:
- Do NOT invent paths or contents not present in the provided context.
- If something is commonly expected (~/.config/mcp, ~/.dopemux) but not present in context, record it as MISSING (not guessed).
- Output valid JSON only, no markdown fences.

Inputs:
- The runner provides a set of home-control-plane candidate files (safe mode filtering may already have excluded sensitive areas).

Outputs:
- HOME_INVENTORY.json
- HOME_PARTITIONS.json

HOME_INVENTORY.json format:
{
  "inventory_version": "H0.v1",
  "generated_at": "<iso8601>",
  "root_hint": "<string or empty>",
  "items": [
    {
      "path": "<string>",
      "ext": "<string>",
      "bytes": <int>,
      "mtime_epoch": <int>,
      "category_hint": "<one of: mcp|router|litellm|profiles|tmux|sqlite|shell|other|unknown>",
      "notes": "<string>"
    }
  ],
  "missing_expected_roots": [
    {"path": "<string>", "reason": "<string>"}
  ]
}

HOME_PARTITIONS.json format:
{
  "partition_version": "H0.v1",
  "generated_at": "<iso8601>",
  "max_files_per_partition": <int>,
  "partitions": [
    {
      "partition_id": "H_P0001",
      "focus": "<mcp|router|litellm|profiles|tmux|sqlite|mixed>",
      "paths": ["<path1>", "<path2>"],
      "notes": "<string>"
    }
  ],
  "determinism_notes": [
    "Paths sorted ascending before partitioning",
    "Stable partition_ids"
  ]
}

Partitioning requirements:
- Sort all paths ascending (bytewise).
- Group by category_hint when possible.
- Keep partitions small enough that downstream prompts won’t overflow context windows.

---

## Prompt
- prompt_id: rte_v3_prompt_h1_keys___references
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: H
- step: H1
- short_name: Keys / References
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_H1_KEYS___REFERENCES.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: routing/classification
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# Phase H1: Home Keys + References Surface (Safe)

Goal:
- Extract references to environment variables, API keys, token paths, credential file paths, and configuration include-chains that appear in the provided home control-plane files.
- Do NOT output secrets. Only output key NAMES, referenced FILE PATHS, and reference locations.

Hard rules:
- Never print actual secret values.
- Prefer explicit evidence: show (path, line_range, snippet_redacted) for each reference.
- Output valid JSON only.

Outputs:
- HOME_KEYS_SURFACE.json
- HOME_REFERENCES.json

HOME_KEYS_SURFACE.json:
{
  "surface_version": "H1.v1",
  "generated_at": "<iso8601>",
  "env_vars_referenced": [
    {
      "name": "<ENV_VAR_NAME>",
      "refs": [{"path":"<path>","line_range":"Lx-Ly","snippet":"<redacted snippet>"}]
    }
  ],
  "credential_paths_referenced": [
    {
      "path": "<string>",
      "refs": [{"path":"<path>","line_range":"Lx-Ly","snippet":"<redacted snippet>"}]
    }
  ],
  "notes": []
}

HOME_REFERENCES.json:
{
  "refs_version": "H1.v1",
  "generated_at": "<iso8601>",
  "includes_and_imports": [
    {
      "source_path": "<path>",
      "kind": "<include|import|source|extends|loads>",
      "target": "<string>",
      "evidence": {"line_range":"Lx-Ly","snippet":"<redacted snippet>"}
    }
  ]
}

---

## Prompt
- prompt_id: rte_v3_prompt_h2_mcp_surface
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: H
- step: H2
- short_name: Mcp Surface
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_H2_MCP_SURFACE.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: routing/classification
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# Phase H2: Home MCP Surface

Goal:
- Extract MCP server definitions, client configs, and any local MCP wiring present in home control-plane files.

Hard rules:
- Evidence-only.
- If MCP appears only as a hint (string mention) but no structured config is present, record as "hint_only".

Outputs:
- HOME_MCP_SURFACE.json

HOME_MCP_SURFACE.json:
{
  "surface_version": "H2.v1",
  "generated_at": "<iso8601>",
  "servers": [
    {
      "name": "<string>",
      "command": "<string or empty>",
      "args": ["<string>"],
      "env_keys": ["<ENV_VAR_NAME>"],
      "config_path": "<path>",
      "evidence": {"line_range":"Lx-Ly","snippet":"<redacted snippet>"},
      "confidence": "<high|medium|low|hint_only>"
    }
  ],
  "clients": [
    {
      "name": "<string>",
      "config_path": "<path>",
      "evidence": {"line_range":"Lx-Ly","snippet":"<redacted snippet>"},
      "notes": "<string>"
    }
  ],
  "notes": []
}

---

## Prompt
- prompt_id: rte_v3_prompt_h3_router___provider_ladders
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: H
- step: H3
- short_name: Router / Provider Ladders
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_H3_ROUTER___PROVIDER_LADDERS.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: routing/classification
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# Phase H3: Home Router + Provider Ladder Hints

Goal:
- Extract any router configuration, model/provider selection ladders, fallback chains, or policy-like directives found in home control plane configs.

Outputs:
- HOME_ROUTER_SURFACE.json
- HOME_PROVIDER_LADDER_HINTS.json

HOME_ROUTER_SURFACE.json:
{
  "surface_version": "H3.v1",
  "generated_at": "<iso8601>",
  "router_configs": [
    {
      "path": "<path>",
      "router_type_hint": "<string>",
      "model_selection_rules": ["<string>"],
      "evidence": {"line_range":"Lx-Ly","snippet":"<redacted snippet>"}
    }
  ],
  "notes":[]
}

HOME_PROVIDER_LADDER_HINTS.json:
{
  "hints_version": "H3.v1",
  "generated_at": "<iso8601>",
  "ladders": [
    {
      "name": "<string>",
      "providers_or_models": ["<string>"],
      "evidence": {"path":"<path>","line_range":"Lx-Ly","snippet":"<redacted snippet>"},
      "confidence": "<high|medium|low|hint_only>"
    }
  ]
}

---

## Prompt
- prompt_id: rte_v3_prompt_h4_litellm_surfaces
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: H
- step: H4
- short_name: Litellm Surfaces
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_H4_LITELLM_SURFACES.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: routing/classification
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# Phase H4: Home LiteLLM Surface

Goal:
- Extract LiteLLM config references, proxy configs, spend/log DB hints, and provider entries from home control-plane.

Outputs:
- HOME_LITELLM_SURFACE.json

HOME_LITELLM_SURFACE.json:
{
  "surface_version": "H4.v1",
  "generated_at": "<iso8601>",
  "configs": [
    {
      "path": "<path>",
      "providers": ["<string>"],
      "models": ["<string>"],
      "db_or_logs": ["<string>"],
      "evidence": {"line_range":"Lx-Ly","snippet":"<redacted snippet>"}
    }
  ],
  "notes":[]
}

---

## Prompt
- prompt_id: rte_v3_prompt_h5_profiles___sessions
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: H
- step: H5
- short_name: Profiles / Sessions
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_H5_PROFILES___SESSIONS.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: routing/classification
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# Phase H5: Home Profiles + Sessions Surface

Goal:
- Extract any operator profiles, session presets, persona configs, or “profile selection” hints from home control-plane.

Outputs:
- HOME_PROFILES_SURFACE.json

HOME_PROFILES_SURFACE.json:
{
  "surface_version": "H5.v1",
  "generated_at": "<iso8601>",
  "profiles": [
    {
      "name": "<string>",
      "path": "<path>",
      "fields": ["<string>"],
      "evidence": {"line_range":"Lx-Ly","snippet":"<redacted snippet>"},
      "notes": "<string>"
    }
  ],
  "notes":[]
}

---

## Prompt
- prompt_id: rte_v3_prompt_h6_tmux___workflow_helpers
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: H
- step: H6
- short_name: Tmux / Workflow Helpers
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_H6_TMUX___WORKFLOW_HELPERS.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: routing/classification
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# Phase H6: Home TMUX + Workflow Helpers Surface

Goal:
- Extract tmux session definitions, scripts, aliases, and helper commands that appear to bootstrap Dopemux/TaskX workflows.

Outputs:
- HOME_TMUX_WORKFLOW_SURFACE.json

HOME_TMUX_WORKFLOW_SURFACE.json:
{
  "surface_version": "H6.v1",
  "generated_at": "<iso8601>",
  "workflows": [
    {
      "name": "<string>",
      "kind": "<tmux|shell|alias|script>",
      "entrypoint": "<string>",
      "paths_involved": ["<path>"],
      "commands": ["<command string>"],
      "evidence": {"path":"<path>","line_range":"Lx-Ly","snippet":"<redacted snippet>"}
    }
  ],
  "notes":[]
}

---

## Prompt
- prompt_id: rte_v3_prompt_h7_sqlite___state_db_metadata
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: H
- step: H7
- short_name: Sqlite / State Db Metadata
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_H7_SQLITE___STATE_DB_METADATA.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: routing/classification
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# Phase H7: Home SQLite + State DB Metadata

Goal:
- Detect references to sqlite DB files, schema files, migrations, or state directories in home control plane configs.
- If you have actual sqlite schema text in context, extract table/index names as metadata only (no secret contents).

Outputs:
- HOME_SQLITE_SCHEMA.json

HOME_SQLITE_SCHEMA.json:
{
  "surface_version": "H7.v1",
  "generated_at": "<iso8601>",
  "db_files": [
    {
      "path": "<path>",
      "evidence": {"path":"<path>","line_range":"Lx-Ly","snippet":"<redacted snippet>"},
      "notes":"<string>"
    }
  ],
  "schema_hints": [
    {
      "source_path": "<path>",
      "tables": ["<string>"],
      "indexes": ["<string>"],
      "triggers": ["<string>"],
      "evidence": {"line_range":"Lx-Ly","snippet":"<redacted snippet>"}
    }
  ],
  "notes":[]
}

---

## Prompt
- prompt_id: rte_v3_prompt_h9_merge___qa
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: H
- step: H9
- short_name: Merge / Qa
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_H9_MERGE___QA.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: routing/classification
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# Phase H9: Merge + QA (Home Control Plane)

Goal:
- Merge all Phase H raw outputs into deterministic normalized artifacts.
- Emit a QA report: missing expected artifacts, empty artifacts, and evidence quality warnings.

Hard rules:
- Deterministic ordering: sort keys where applicable; sort arrays by stable keys (path/name) when possible.
- No invention.

Outputs:
- HOMECTRL_NORM_MANIFEST.json
- HOMECTRL_QA.json

HOMECTRL_NORM_MANIFEST.json:
{
  "manifest_version": "H9.v1",
  "generated_at": "<iso8601>",
  "inputs": ["<raw json file names>"],
  "outputs": [
    "HOME_KEYS_SURFACE.json",
    "HOME_REFERENCES.json",
    "HOME_MCP_SURFACE.json",
    "HOME_ROUTER_SURFACE.json",
    "HOME_PROVIDER_LADDER_HINTS.json",
    "HOME_LITELLM_SURFACE.json",
    "HOME_PROFILES_SURFACE.json",
    "HOME_TMUX_WORKFLOW_SURFACE.json",
    "HOME_SQLITE_SCHEMA.json"
  ],
  "notes":[]
}

HOMECTRL_QA.json:
{
  "qa_version": "H9.v1",
  "generated_at": "<iso8601>",
  "missing_expected_raw_steps": ["<string>"],
  "empty_outputs": ["<string>"],
  "evidence_warnings": ["<string>"],
  "safe_mode_observations": ["<string>"]
}

---

## Prompt
- prompt_id: rte_v3_prompt_d0_inventory___partition_plan
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: D
- step: D0
- short_name: Inventory / Partition Plan
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_D0_INVENTORY___PARTITION_PLAN.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
OUTPUTS:
- DOC_INVENTORY.json
- DOC_PARTITIONS.json
- DOC_TODO_QUEUE.json

Hard rules:
- Output JSON only. No prose, markdown fences, commentary, or multiple JSON objects.
- Treat the runner context as line-numbered evidence. Every cited line_range MUST use the line numbers shown in the provided excerpt.
- Every items[] entry MUST include id, path, and line_range.
- Every evidence object MUST include repo-relative path, integer line_range, and exact excerpt.
- If a value cannot be grounded from the provided excerpt, return valid JSON with UNKNOWN or fail-closed placeholders; never invent line numbers.

Goal: DOC_INVENTORY.json, DOC_PARTITIONS.json, DOC_TODO_QUEUE.json

Prompt:
- Scan docs/** (include archive dirs but tag them as archive).
- For each doc:
  - path, size, mtime, top headings, first 40 non-empty lines, token count estimate.
  - tag: ACTIVE vs ARCHIVE vs QUARANTINE based on path + in-doc markers.
- Create partitions:
  - core architecture
  - planes (pm/memory/orchestrator/mcp/hooks)
  - services (dope-memory, eventbus, dashboards, etc.)
  - task-packets + governance
  - research/audits
  - archives (split into manageable buckets)
- Output a queue of partitions with recommended run order.
```markdown

OUTPUTS:
	•	DOC_INVENTORY.json
	•	DOC_PARTITIONS.json
	•	DOC_TODO_QUEUE.json
```

---

## Prompt
- prompt_id: rte_v3_prompt_d1_claims___boundaries___supersession
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: D
- step: D1
- short_name: Claims / Boundaries / Supersession
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_D1_CLAIMS___BOUNDARIES___SUPERSESSION.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
OUTPUTS:
- DOC_INDEX.partX.json
- DOC_CONTRACT_CLAIMS.partX.json
- DOC_BOUNDARIES.partX.json
- DOC_SUPERSESSION.partX.json
- CAP_NOTICES.partX.json

Hard rules:
- Output JSON only. No prose, markdown fences, commentary, or multiple JSON objects.
- Treat the runner context as line-numbered evidence. Every cited line_range MUST use the line numbers shown in the provided excerpt.
- Every items[] entry MUST include id, path, and line_range.
- Every evidence object MUST include repo-relative path, integer line_range, and exact excerpt.
- If a value cannot be grounded from the provided excerpt, return valid JSON with UNKNOWN or fail-closed placeholders; never invent line numbers.

Goal (per partition):
- DOC_INDEX.partX.json
- DOC_CONTRACT_CLAIMS.partX.json
- DOC_BOUNDARIES.partX.json
- DOC_SUPERSESSION.partX.json
- CAP_NOTICES.partX.json (what didn't fit, what needs D2)

Prompt:
- Extract only "normative" and "boundary" statements:
  - MUST/SHALL/DO NOT, invariants, failure modes, interfaces, "authority" language
  - plane boundaries and what enforces them (even if just planned)
  - supersession markers: ACTIVE/DEPRECATED, version headers, timestamps, "supersedes"
- Cite everything: file + line_range + short quote.
```markdown

OUTPUTS:
	•	DOC_INDEX.partX.json
	•	DOC_CONTRACT_CLAIMS.partX.json
	•	DOC_BOUNDARIES.partX.json
	•	DOC_SUPERSESSION.partX.json
	•	CAP_NOTICES.partX.json
```

---

## Prompt
- prompt_id: rte_v3_prompt_d2_deep_extraction
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: D
- step: D2
- short_name: Deep Extraction
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_D2_DEEP_EXTRACTION.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
OUTPUTS:
- DOC_INTERFACES.partX.json
- DOC_WORKFLOWS.partX.json
- DOC_DECISIONS.partX.json
- DOC_GLOSSARY.partX.json

Hard rules:
- Output JSON only. No prose, markdown fences, commentary, or multiple JSON objects.
- Treat the runner context as line-numbered evidence. Every cited line_range MUST use the line numbers shown in the provided excerpt.
- Every items[] entry MUST include id, path, and line_range.
- Every evidence object MUST include repo-relative path, integer line_range, and exact excerpt.
- If a value cannot be grounded from the provided excerpt, return valid JSON with UNKNOWN or fail-closed placeholders; never invent line numbers.

Goal (per partition):
- DOC_INTERFACES.partX.json
- DOC_WORKFLOWS.partX.json
- DOC_DECISIONS.partX.json
- DOC_GLOSSARY.partX.json

Prompt:
- Extract structured interface/workflow details:
  - service responsibilities
  - dataflow steps
  - event names mentioned
  - state DBs and schema references
  - operational workflows, multi-service pipelines
  - instruction-file-driven workflows
- Again: cite everything.
```markdown

OUTPUTS:
	•	DOC_INTERFACES.partX.json
	•	DOC_WORKFLOWS.partX.json
	•	DOC_DECISIONS.partX.json
	•	DOC_GLOSSARY.partX.json
```

---

## Prompt
- prompt_id: rte_v3_prompt_d3_citation___reference_graph
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: D
- step: D3
- short_name: Citation / Reference Graph
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_D3_CITATION___REFERENCE_GRAPH.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
OUTPUTS:
- DOC_CITATION_GRAPH.json

Hard rules:
- Output JSON only. No prose, markdown fences, commentary, or multiple JSON objects.
- Treat the runner context as line-numbered evidence. Every cited line_range MUST use the line numbers shown in the provided excerpt.
- When emitting items[], every entry MUST include id, path, and line_range.
- Every evidence object MUST include repo-relative path, integer line_range, and exact excerpt.
- If a value cannot be grounded from the provided excerpt, return valid JSON with UNKNOWN or fail-closed placeholders; never invent line numbers.

Goal: DOC_CITATION_GRAPH.json

Prompt:
- Build graph edges:
  - doc A references doc B (links, filenames, "see also", explicit citations)
  - doc A references code path
  - doc A references service name/config name
- Output top referenced docs, hub docs, cross-plane edges.
```markdown

OUTPUTS:
	•	DOC_CITATION_GRAPH.json
```

---

## Prompt
- prompt_id: rte_v3_prompt_d4_merge___normalize___coverage_qa
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: D
- step: D4
- short_name: Merge / Normalize / Coverage Qa
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_D4_MERGE___NORMALIZE___COVERAGE_QA.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
Goal:
- merged: DOC_INDEX.json, DOC_CONTRACT_CLAIMS.json, DOC_SUPERSESSION.json, DOC_TOPIC_CLUSTERS.json, DUPLICATE_DRIFT_REPORT.json
- optional alternate duplicate artifact: DOC_RECENCY_DUPLICATE_REPORT.json
- QA: DOC_COVERAGE_REPORT.json

Hard rules:
- Output JSON only. No prose, markdown fences, commentary, or multiple JSON objects.
- Treat the runner context as line-numbered evidence. Every cited line_range MUST use the line numbers shown in the provided excerpt.
- Every items[] entry MUST include id, path, and line_range.
- Every evidence object MUST include repo-relative path, integer line_range, and exact excerpt.
- If a value cannot be grounded from the provided excerpt, return valid JSON with UNKNOWN or fail-closed placeholders; never invent line numbers.

Prompt:
- Merge all part files.
- Dedup rules:
  - prefer newer timestamps when same doc appears in multiple buckets
  - preserve both if content differs materially
- Coverage gates:
  - all docs indexed
  - no pending partitions
  - all CAP_NOTICES resolved or explicitly waived
  - citation graph present

```markdown

OUTPUTS:
	•	DOC_CONTRACT_CLAIMS.json
	•	DOC_COVERAGE_REPORT.json
	•	DOC_INDEX.json
	•	DOC_RECENCY_DUPLICATE_REPORT.json
	•	DOC_SUPERSESSION.json
	•	DOC_TOPIC_CLUSTERS.json
	•	DUPLICATE_DRIFT_REPORT.json
```

---

## Prompt
- prompt_id: rte_v3_prompt_d5_doc_topic_clusters_json
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: D
- step: D5
- short_name: Doc Topic Clusters Json
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_D5_DOC_TOPIC_CLUSTERS_JSON.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
OUTPUTS:
- DOC_TOPIC_CLUSTERS.json

Hard rules:
- Output JSON only. No prose, markdown fences, commentary, or multiple JSON objects.
- Treat the runner context as line-numbered evidence. Every cited line_range MUST use the line numbers shown in the provided excerpt.
- Every items[] entry MUST include id, path, and line_range.
- Every evidence object MUST include repo-relative path, integer line_range, and exact excerpt.
- If a value cannot be grounded from the provided excerpt, return valid JSON with UNKNOWN or fail-closed placeholders; never invent line numbers.

Goal: DOC_TOPIC_CLUSTERS.json

Prompt:
- Input: merged docs index (plus optionally raw text samples).
- Cluster by token overlap (no semantic labeling).
- Output:
  - cluster_id
  - doc_paths
  - top_tokens (weighted)
  - doc_count
  - newest_mtime + oldest_mtime (for recency awareness)
- No "this cluster is architecture" labeling.
```markdown

OUTPUTS:
	•	DOC_TOPIC_CLUSTERS.json
```

---

## Prompt
- prompt_id: rte_v3_prompt_c0_code_inventory___partition_plan
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: C
- step: C0
- short_name: Code Inventory / Partition Plan
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_C0_CODE_INVENTORY___PARTITION_PLAN.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_C0 - CODE INVENTORY + PARTITION PLAN

GOAL:
- Build deterministic code inventory and partition plan artifacts.

OUTPUTS:
- CODE_INVENTORY.json
- CODE_PARTITIONS.json

INPUT SCOPE:
- services/**
- src/**
- shared/**
- scripts/**
- tools/**
- compose.yml
- docker-compose*.yml
- services/registry.yaml

EXTRACTION PROCEDURE:
1) Scan in-scope sources and collect candidate code artifacts with path and type metadata.
2) Classify each artifact into a subsystem category using direct evidence from code or config.
3) Build CODE_PARTITIONS by grouping artifacts into stable partition buckets with explicit rationale.
4) For each CODE_INVENTORY item, populate id/path/kind/summary/evidence.
5) For each CODE_PARTITIONS item, populate id/partition_id/files/reason/evidence.
6) Enumerate candidate facts only from in-scope files and provided runner context.
7) Build deterministic IDs from stable keys (path, symbol, service name).
8) Attach evidence for every non-trivial field.
9) Sort arrays deterministically and deduplicate by stable IDs.
10) Emit only declared outputs.

PARTITION HINTS:
- services/** entrypoints
- shared/**
- src/**
- workflow scripts
- eventbus modules
- dope-memory modules
- boundary/guardrail modules
- taskx bridges

---

## Prompt
- prompt_id: rte_v3_prompt_c1_service_entrypoints
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: C
- step: C1
- short_name: Service Entrypoints
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_C1_SERVICE_ENTRYPOINTS.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
OUTPUTS:
- SERVICE_ENTRYPOINTS.json

Goal: SERVICE_ENTRYPOINTS.json

Prompt:
- Find how services start:
  - main modules, cli entrypoints, compose commands, uvicorn/gunicorn, scripts.
- Extract exact invocation strings + module symbols.
```markdown

OUTPUTS:
	•	SERVICE_ENTRYPOINTS.json
```

---

## Prompt
- prompt_id: rte_v3_prompt_c2_eventbus_wiring_truth_surfaces
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: C
- step: C2
- short_name: Eventbus Wiring Truth Surfaces
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_C2_EVENTBUS_WIRING_TRUTH_SURFACES.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
OUTPUTS:
- EVENTBUS_SURFACE.json
- EVENT_PRODUCERS.json
- EVENT_CONSUMERS.json

Goals: EVENTBUS_SURFACE.json, EVENT_PRODUCERS.json, EVENT_CONSUMERS.json

Prompt:
- Extract:
  - event bus implementations/adapters
  - literal event names/topics (string constants)
  - producer call sites
  - consumer registration/handlers
```markdown

OUTPUTS:
	•	EVENTBUS_SURFACE.json
	•	EVENT_CONSUMERS.json
	•	EVENT_PRODUCERS.json
```

---

## Prompt
- prompt_id: rte_v3_prompt_c3_dope_memory_surfaces
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: C
- step: C3
- short_name: Dope Memory Surfaces
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_C3_DOPE_MEMORY_SURFACES.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
OUTPUTS:
- DOPE_MEMORY_CODE_SURFACE.json
- DOPE_MEMORY_SCHEMAS.json
- DOPE_MEMORY_DB_WRITES.json

Goals: DOPE_MEMORY_CODE_SURFACE.json, DOPE_MEMORY_SCHEMAS.json, DOPE_MEMORY_DB_WRITES.json

Prompt:
- Extract:
  - storage backends
  - schema sources (SQL, migrations)
  - all DB write locations (insert/update/delete) with context
  - TTL/retention enforcement points
```markdown

OUTPUTS:
	•	DOPE_MEMORY_CODE_SURFACE.json
	•	DOPE_MEMORY_DB_WRITES.json
	•	DOPE_MEMORY_SCHEMAS.json
```

---

## Prompt
- prompt_id: rte_v3_prompt_c4_trinity_boundary_enforcement_surfaces
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: C
- step: C4
- short_name: Trinity Boundary Enforcement Surfaces
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_C4_TRINITY_BOUNDARY_ENFORCEMENT_SURFACES.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
OUTPUTS:
- TRINITY_ENFORCEMENT_SURFACE.json
- REFUSAL_AND_GUARDRAILS_SURFACE.json

Goals: TRINITY_ENFORCEMENT_SURFACE.json, REFUSAL_AND_GUARDRAILS_SURFACE.json

Prompt:
- Extract:
  - boundary checks, refusal artifacts, gating chains
  - where it's invoked (middleware, validators, routers, CLI paths)
```markdown

OUTPUTS:
	•	REFUSAL_AND_GUARDRAILS_SURFACE.json
	•	TRINITY_ENFORCEMENT_SURFACE.json
```

---

## Prompt
- prompt_id: rte_v3_prompt_c5_taskx_integration_surfaces
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: C
- step: C5
- short_name: Taskx Integration Surfaces
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_C5_TASKX_INTEGRATION_SURFACES.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
OUTPUTS:
- TASKX_INTEGRATION_SURFACE.json

Goal: TASKX_INTEGRATION_SURFACE.json

Prompt:
- Extract:
  - any calls to taskx
  - packet read/write paths
  - operator instruction compilation/injection in code
```markdown

OUTPUTS:
	•	TASKX_INTEGRATION_SURFACE.json
```

---

## Prompt
- prompt_id: rte_v3_prompt_c6_workflow_runners___multi_service_coordination
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: C
- step: C6
- short_name: Workflow Runners / Multi Service Coordination
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_C6_WORKFLOW_RUNNERS___MULTI_SERVICE_COORDINATION.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
OUTPUTS:
- WORKFLOW_RUNNER_SURFACE.json

Goal: WORKFLOW_RUNNER_SURFACE.json

Prompt:
- Extract:
  - scripts, tmux configs, orchestrator yaml, make targets
  - what starts what, and in what order
```markdown

OUTPUTS:
	•	WORKFLOW_RUNNER_SURFACE.json
```

---

## Prompt
- prompt_id: rte_v3_prompt_c7_api___dashboards
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: C
- step: C7
- short_name: Api / Dashboards
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_C7_API___DASHBOARDS.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
OUTPUTS:
- API_DASHBOARD_SURFACE.json

Goal: API_DASHBOARD_SURFACE.json

Prompt:
- Extract API routes, dashboard definitions, and monitoring endpoints.
- Cite file and line ranges.
```markdown

OUTPUTS:
	•	API_DASHBOARD_SURFACE.json
```

---

## Prompt
- prompt_id: rte_v3_prompt_c8_determinism___idempotency___concurrency_location_scans
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: C
- step: C8
- short_name: Determinism / Idempotency / Concurrency Location Scans
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_C8_DETERMINISM___IDEMPOTENCY___CONCURRENCY_LOCATION_SCANS.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
OUTPUTS:
- DETERMINISM_RISK_LOCATIONS.json
- IDEMPOTENCY_RISK_LOCATIONS.json
- CONCURRENCY_RISK_LOCATIONS.json
- SECRETS_RISK_LOCATIONS.json

Goal: DETERMINISM_RISK_LOCATIONS.json, IDEMPOTENCY_RISK_LOCATIONS.json, CONCURRENCY_RISK_LOCATIONS.json, SECRETS_RISK_LOCATIONS.json

Prompt:
- Scan for:
  - Non-deterministic functions (random, time, uuid) in critical paths.
  - Concurrency risks (global state mutation, race conditions).
  - Idempotency risks (DB writes without keys, retries with side effects).
  - Secrets patterns (APi keys, tokens).
```markdown

OUTPUTS:
	•	CONCURRENCY_RISK_LOCATIONS.json
	•	DETERMINISM_RISK_LOCATIONS.json
	•	IDEMPOTENCY_RISK_LOCATIONS.json
	•	SECRETS_RISK_LOCATIONS.json
```

---

## Prompt
- prompt_id: rte_v3_prompt_c9_merge___normalize___qa
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: C
- step: C9
- short_name: Merge / Normalize / Qa
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_C9_MERGE___NORMALIZE___QA.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
Goal:
- merged: SERVICE_ENTRYPOINTS.json, EVENTBUS_SURFACE.json, EVENT_PRODUCERS.json, EVENT_CONSUMERS.json
- merged: DOPE_MEMORY_CODE_SURFACE.json, DOPE_MEMORY_SCHEMAS.json, DOPE_MEMORY_DB_WRITES.json
- merged: TRINITY_ENFORCEMENT_SURFACE.json, REFUSAL_AND_GUARDRAILS_SURFACE.json, TASKX_INTEGRATION_SURFACE.json
- merged: WORKFLOW_RUNNER_SURFACE.json
- merged: DETERMINISM_RISK_LOCATIONS.json, IDEMPOTENCY_RISK_LOCATIONS.json, CONCURRENCY_RISK_LOCATIONS.json
- QA: CODE_SURFACES_QA.json

Prompt:
- Merge all C1-C8 outputs.
- QA: Ensure all artifacts present, no secrets, coverage complete.

```markdown

OUTPUTS:
	•	CODE_SURFACES_QA.json
	•	CONCURRENCY_RISK_LOCATIONS.json
	•	DETERMINISM_RISK_LOCATIONS.json
	•	DOPE_MEMORY_CODE_SURFACE.json
	•	DOPE_MEMORY_DB_WRITES.json
	•	DOPE_MEMORY_SCHEMAS.json
	•	EVENTBUS_SURFACE.json
	•	EVENT_CONSUMERS.json
	•	EVENT_PRODUCERS.json
	•	IDEMPOTENCY_RISK_LOCATIONS.json
	•	REFUSAL_AND_GUARDRAILS_SURFACE.json
	•	SERVICE_ENTRYPOINTS.json
	•	TASKX_INTEGRATION_SURFACE.json
	•	TRINITY_ENFORCEMENT_SURFACE.json
	•	WORKFLOW_RUNNER_SURFACE.json
```

---

## Prompt
- prompt_id: rte_v3_prompt_e0_execution_inventory___partition_plan
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: E
- step: E0
- short_name: Execution Inventory / Partition Plan
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_E0_EXECUTION_INVENTORY___PARTITION_PLAN.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: tool_orchestration
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_E0 — EXECUTION INVENTORY + PARTITION PLAN

TASK: Build inventory + partitions for execution plane.
SCAN TARGETS: Makefile, package.json, pyproject.toml, scripts/, tools/, compose/, .github/, docker*/, *.sh, *.zsh, justfile*, *.mk.

OUTPUTS:
	•	EXEC_INVENTORY.json
	•	EXEC_PARTITIONS.json

RULES:
	•	Identify every file in the scan targets.
	•	Chunk sources into tractable partitions for the following prompts.
	•	Ensure partitions are deterministic.

---

## Prompt
- prompt_id: rte_v3_prompt_e1_bootstrap_commands_surface
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: E
- step: E1
- short_name: Bootstrap Commands Surface
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_E1_BOOTSTRAP_COMMANDS_SURFACE.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: tool_orchestration
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_E1 — BOOTSTRAP COMMANDS SURFACE

TASK: Enumerate canonical “what starts what” commands.

MUST EXTRACT (literal strings):
	•	make targets and recipes
	•	npm scripts
	•	python entrypoints / CLI invocations
	•	compose up/down targets
	•	tmux wrappers invoked from repo side

OUTPUTS:
	•	EXEC_BOOTSTRAP_COMMANDS.json

---

## Prompt
- prompt_id: rte_v3_prompt_e2_env_loading___config_chain
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: E
- step: E2
- short_name: Env Loading / Config Chain
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_E2_ENV_LOADING___CONFIG_CHAIN.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: tool_orchestration
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_E2 — ENV LOADING / CONFIG CHAIN

TASK: Map env var sources and config precedence chain.

MUST EXTRACT:
	•	.env loading behavior and where it occurs
	•	config file resolution order
	•	env var names and their consumers (by reference only, no guessing)

OUTPUTS:
	•	EXEC_ENV_CHAIN.json

---

## Prompt
- prompt_id: rte_v3_prompt_e3_service_startup_graph
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: E
- step: E3
- short_name: Service Startup Graph
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_E3_SERVICE_STARTUP_GRAPH.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: tool_orchestration
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_E3 — SERVICE STARTUP GRAPH

TASK: Produce a service start graph from compose/scripts.

OUTPUTS:
	•	EXEC_STARTUP_GRAPH.json

---

## Prompt
- prompt_id: rte_v3_prompt_e4_runtime_modes___delta_report
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: E
- step: E4
- short_name: Runtime Modes / Delta Report
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_E4_RUNTIME_MODES___DELTA_REPORT.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: tool_orchestration
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_E4 — RUNTIME MODES / DELTA REPORT

TASK: Identify runtime “modes” (dev/prod/smoke/local) + deltas.

OUTPUTS:
	•	EXEC_RUNTIME_MODES.json
	•	EXEC_MODE_DELTA_REPORT.json

---

## Prompt
- prompt_id: rte_v3_prompt_e5_artifact_outputs___logs___state
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: E
- step: E5
- short_name: Artifact Outputs / Logs / State
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_E5_ARTIFACT_OUTPUTS___LOGS___STATE.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: tool_orchestration
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_E5 — ARTIFACT OUTPUTS / LOGS / STATE

TASK: List artifact outputs: logs, db files, cache dirs, out dirs.

OUTPUTS:
	•	EXEC_ARTIFACT_SURFACE.json

---

## Prompt
- prompt_id: rte_v3_prompt_e6_execution_risks___ordering___state_dependency
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: E
- step: E6
- short_name: Execution Risks / Ordering / State Dependency
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_E6_EXECUTION_RISKS___ORDERING___STATE_DEPENDENCY.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: tool_orchestration
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_E6 — EXECUTION RISKS / ORDERING / STATE DEPENDENCY

TASK: Extract ordering hazards and state coupling points.

OUTPUTS:
	•	EXEC_RISK_FACTS.json

---

## Prompt
- prompt_id: rte_v3_prompt_e9_merge___normalize___qa
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: E
- step: E9
- short_name: Merge / Normalize / Qa
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_E9_MERGE___NORMALIZE___QA.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: tool_orchestration
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_E9 — Execution merge + normalize + QA

ROLE: Deterministic normalizer + QA bot.
GOAL: merge all EXEC_* outputs, report coverage and suspicious gaps.

OUTPUTS:
  • EXEC_MERGED.json
  • EXEC_QA.json (counts_by_filekind, partitions_covered, missing_expected_outputs[], suspicious_empty[])

RULES:
  • Normalize arrays by stable sort, remove duplicate rows.
  • Preserve exact field names from upstream prompts.

---

## Prompt
- prompt_id: rte_v3_prompt_w0_workflow_inventory___partition_plan
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: W
- step: W0
- short_name: Workflow Inventory / Partition Plan
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_W0_WORKFLOW_INVENTORY___PARTITION_PLAN.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_W0 — WORKFLOW INVENTORY + PARTITION PLAN

TASK: Build inventory and partition plan for workflows.

OUTPUTS:
	•	WORKFLOW_INVENTORY.json
	•	WORKFLOW_PARTITIONS.json

---

## Prompt
- prompt_id: rte_v3_prompt_w1_workflow_catalog___runbook_facts
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: W
- step: W1
- short_name: Workflow Catalog / Runbook Facts
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_W1_WORKFLOW_CATALOG___RUNBOOK_FACTS.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_W1 — WORKFLOW CATALOG / RUNBOOK FACTS

TASK: Enumerate workflows W1..Wn with literal steps.

OUTPUTS:
	•	WORKFLOW_CATALOG.json

---

## Prompt
- prompt_id: rte_v3_prompt_w2_workflow_inputs_outputs___artifacts
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: W
- step: W2
- short_name: Workflow Inputs Outputs / Artifacts
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_W2_WORKFLOW_INPUTS_OUTPUTS___ARTIFACTS.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_W2 — WORKFLOW INPUTS / OUTPUTS / ARTIFACTS

TASK: Extract workflow I/O and artifact production.

OUTPUTS:
	•	WORKFLOW_IO_MAP.json

---

## Prompt
- prompt_id: rte_v3_prompt_w3_multi_service_coordination___compose_tmux
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: W
- step: W3
- short_name: Multi Service Coordination / Compose Tmux
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_W3_MULTI_SERVICE_COORDINATION___COMPOSE_TMUX.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_W3 — MULTI-SERVICE COORDINATION / COMPOSE / TMUX

TASK: Tie compose + tmux + scripts into a coordination view.

OUTPUTS:
	•	WORKFLOW_COORDINATION_SURFACE.json

---

## Prompt
- prompt_id: rte_v3_prompt_w4_workflow_failure_modes___recovery
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: W
- step: W4
- short_name: Workflow Failure Modes / Recovery
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_W4_WORKFLOW_FAILURE_MODES___RECOVERY.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_W4 — WORKFLOW FAILURE MODES / RECOVERY

TASK: Identify workflow failure modes and recovery paths.

OUTPUTS:
	•	WORKFLOW_FAILURE_RECOVERY.json

---

## Prompt
- prompt_id: rte_v3_prompt_w5_workflow_state_dependencies___home_vs_repo
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: W
- step: W5
- short_name: Workflow State Dependencies / Home Vs Repo
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_W5_WORKFLOW_STATE_DEPENDENCIES___HOME_VS_REPO.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_W5 — WORKFLOW STATE DEPENDENCIES / HOME VS REPO

TASK: Extract workflow state coupling points.

OUTPUTS:
	•	WORKFLOW_STATE_COUPLING.json

---

## Prompt
- prompt_id: rte_v3_prompt_w9_merge___qa
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: W
- step: W9
- short_name: Merge / Qa
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_W9_MERGE___QA.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_W9 — Workflows merge + QA

ROLE: Deterministic normalizer + QA bot.
GOAL: merge workflow artifacts and report coverage.

OUTPUTS:
  • WORKFLOW_MERGED.json
  • WORKFLOW_QA.json

RULES:
  • Normalize arrays by stable sort and remove duplicates.

---

## Prompt
- prompt_id: rte_v3_prompt_b0_boundary_inventory___partition_plan
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: B
- step: B0
- short_name: Boundary Inventory / Partition Plan
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_B0_BOUNDARY_INVENTORY___PARTITION_PLAN.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_B0 — BOUNDARY INVENTORY + PARTITION PLAN

TASK: Build inventory and partition plan for the boundary plane.

OUTPUTS:
	•	BOUNDARY_INVENTORY.json
	•	BOUNDARY_PARTITIONS.json

---

## Prompt
- prompt_id: rte_v3_prompt_b1_boundary_assertions___code_enforcement_points
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: B
- step: B1
- short_name: Boundary Assertions / Code Enforcement Points
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_B1_BOUNDARY_ASSERTIONS___CODE_ENFORCEMENT_POINTS.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_B1 — BOUNDARY ASSERTIONS / CODE ENFORCEMENT POINTS

TASK: Find boundary checks in code/config/docs (facts only).

OUTPUTS:
	•	BOUNDARY_ENFORCEMENT_POINTS.json

---

## Prompt
- prompt_id: rte_v3_prompt_b2_refusal_rails___guardrails_surface
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: B
- step: B2
- short_name: Refusal Rails / Guardrails Surface
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_B2_REFUSAL_RAILS___GUARDRAILS_SURFACE.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_B2 — REFUSAL RAILS / GUARDRAILS SURFACE

TASK: Extract refusal rails and guardrails.

OUTPUTS:
	•	REFUSAL_GUARDRAILS_SURFACE.json

---

## Prompt
- prompt_id: rte_v3_prompt_b3_bypass_paths___weak_guards
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: B
- step: B3
- short_name: Bypass Paths / Weak Guards
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_B3_BYPASS_PATHS___WEAK_GUARDS.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_B3 — BYPASS PATHS / WEAK GUARDS

TASK: Identify bypass paths and weak guards.

RULE: only report bypass when evidenced by an alternate path or missing check near a sensitive operation.

OUTPUTS:
	•	BOUNDARY_BYPASS_RISKS.json

---

## Prompt
- prompt_id: rte_v3_prompt_b9_merge___qa
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: B
- step: B9
- short_name: Merge / Qa
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_B9_MERGE___QA.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_B9 — Boundary merge + QA

ROLE: Deterministic normalizer + QA bot.
GOAL: merge boundary artifacts and confirm coverage.

OUTPUTS:
  • BOUNDARY_MERGED.json
  • BOUNDARY_QA.json

RULES:
  • Apply stable sort and deduplicate like-for-like entries.

---

## Prompt
- prompt_id: rte_v3_prompt_g0_governance_inventory___partition_plan
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: G
- step: G0
- short_name: Governance Inventory / Partition Plan
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_G0_GOVERNANCE_INVENTORY___PARTITION_PLAN.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_G0 — GOVERNANCE INVENTORY + PARTITION PLAN

TASK: Build inventory and partition plan for the governance plane.

OUTPUTS:
	•	GOV_INVENTORY.json
	•	GOV_PARTITIONS.json

---

## Prompt
- prompt_id: rte_v3_prompt_g1_ci_gates___quality_bars
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: G
- step: G1
- short_name: Ci Gates / Quality Bars
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_G1_CI_GATES___QUALITY_BARS.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_G1 — CI GATES / QUALITY BARS

TASK: Extract CI gates and quality bars.

OUTPUTS:
	•	GOV_CI_GATES.json

---

## Prompt
- prompt_id: rte_v3_prompt_g2_repo_hygiene___allowlists___policies
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: G
- step: G2
- short_name: Repo Hygiene / Allowlists / Policies
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_G2_REPO_HYGIENE___ALLOWLISTS___POLICIES.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_G2 — REPO HYGIENE / ALLOWLISTS / POLICIES

TASK: Extract repo hygiene policies and allowlists.

OUTPUTS:
	•	GOV_HYGIENE_POLICIES.json

---

## Prompt
- prompt_id: rte_v3_prompt_g3_policy_files___enforcement
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: G
- step: G3
- short_name: Policy Files / Enforcement
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_G3_POLICY_FILES___ENFORCEMENT.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_G3 — Policy files + enforcement

ROLE: Governance extractor.
GOAL: catalog policy files and the enforcement mechanisms they trigger.

OUTPUTS:
  • GOV_POLICIES.json

RULES:
  • Document each policy file and any hooks/scripts that enforce it.

---

## Prompt
- prompt_id: rte_v3_prompt_g4_security___secrets___reduction_facts
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: G
- step: G4
- short_name: Security / Secrets / Reduction Facts
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_G4_SECURITY___SECRETS___REDUCTION_FACTS.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_G4 — SECURITY / SECRETS / REDUCTION FACTS

TASK: Extract security and secrets reduction facts.

RULE: No secret contents; extract paths + patterns + loaders only.

OUTPUTS:
	•	GOV_SECRETS_SURFACE.json

---

## Prompt
- prompt_id: rte_v3_prompt_g9_merge___qa
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: G
- step: G9
- short_name: Merge / Qa
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_G9_MERGE___QA.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_G9 — Governance merge + QA

ROLE: Deterministic normalizer + QA bot.
GOAL: merge governance outputs and provide coverage/consistency checks.

OUTPUTS:
  • GOV_MERGED.json
  • GOV_QA.json

RULES:
  • Sort arrays stably and remove duplicates.

---

## Prompt
- prompt_id: rte_v3_prompt_x0_feature_index_inventory___partition_plan
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: X
- step: X0
- short_name: Feature Index Inventory / Partition Plan
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_X0_FEATURE_INDEX_INVENTORY___PARTITION_PLAN.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_X0_FEATURE_INDEX_INVENTORY___PARTITION_PLAN

TASK: Build feature-index inventory and deterministic partition plan.

SCAN TARGETS:
- services/
- src/
- docs/
- config/
- scripts/
- Makefile
- docker-compose*.yml

OUTPUTS:
- FEATURE_INDEX_INVENTORY.json
- FEATURE_INDEX_PARTITIONS.json

RULES:
- Enumerate candidate feature surfaces, owning code paths, and related docs.
- Partition deterministically for downstream X1 extraction.
- Preserve literal evidence and source paths.

---

## Prompt
- prompt_id: rte_v3_prompt_x1_feature_surface_extract
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: X
- step: X1
- short_name: Feature Surface Extract
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_X1_FEATURE_SURFACE_EXTRACT.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_X1_FEATURE_SURFACE_EXTRACT

TASK: Extract feature surfaces from each partition.

OUTPUTS:
- FEATURE_SURFACE.json

REQUIREMENTS:
- Capture feature id/name, entrypoints, triggers, service touchpoints, and user-visible outcomes.
- Include provenance with file path and evidence snippets.
- Do not infer behavior without direct evidence.

---

## Prompt
- prompt_id: rte_v3_prompt_x2_feature_to_code_map
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: X
- step: X2
- short_name: Feature To Code Map
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_X2_FEATURE_TO_CODE_MAP.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_X2_FEATURE_TO_CODE_MAP

TASK: Build deterministic map from feature surface to code implementation loci.

OUTPUTS:
- FEATURE_CODE_MAP.json

REQUIREMENTS:
- For each feature, map to concrete modules/functions/scripts/services.
- Include coupling points to control-plane and runtime config where present.
- Retain unresolved mappings in unknowns with reasons.

---

## Prompt
- prompt_id: rte_v3_prompt_x3_feature_to_doc_map
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: X
- step: X3
- short_name: Feature To Doc Map
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_X3_FEATURE_TO_DOC_MAP.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_X3_FEATURE_TO_DOC_MAP

TASK: Map features to documentation coverage and drift signals.

OUTPUTS:
- FEATURE_DOC_MAP.json

REQUIREMENTS:
- Link features to docs pages, ADR/RFC references, and runbooks.
- Flag missing or stale docs links as explicit gaps.
- Keep mapping deterministic and evidence-based.

---

## Prompt
- prompt_id: rte_v3_prompt_x4_feature_dependency_graph
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: X
- step: X4
- short_name: Feature Dependency Graph
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_X4_FEATURE_DEPENDENCY_GRAPH.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_X4_FEATURE_DEPENDENCY_GRAPH

TASK: Build feature dependency graph across services, configs, and workflows.

OUTPUTS:
- FEATURE_DEP_GRAPH.json

REQUIREMENTS:
- Emit directed dependencies between features and critical infra/services.
- Include runtime-mode and environment dependencies where observable.
- Preserve cycle information; do not collapse conflicting edges.

---

## Prompt
- prompt_id: rte_v3_prompt_x9_merge___qa
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: X
- step: X9
- short_name: Merge / Qa
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_X9_MERGE___QA.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: field_extraction
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_X9_MERGE___QA

TASK: Merge Feature Index outputs and emit QA.

INPUTS:
- Raw/partition outputs from X0..X4.

OUTPUTS:
- FEATURE_INDEX_MERGED.json
- FEATURE_INDEX_QA.json

RULES:
- Deterministic merge only; no rescans.
- Deduplicate by stable feature identity keys.
- Report coverage, unresolved mappings, and schema/required-field checks.

---

## Prompt
- prompt_id: rte_v3_prompt_q0_pipeline_completeness___manifest
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: Q
- step: Q0
- short_name: Pipeline Completeness / Manifest
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_Q0_PIPELINE_COMPLETENESS___MANIFEST.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: json_repair
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_Q0 — PIPELINE COMPLETENESS / MANIFEST

TASK: Build a manifest of pipeline completeness.

INPUTS: current run dirs */raw, */norm, */qa.

OUTPUTS:
	•	QA_RUN_MANIFEST.json

---

## Prompt
- prompt_id: rte_v3_prompt_q1_missing_artifacts___recovery_plan
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: Q
- step: Q1
- short_name: Missing Artifacts / Recovery Plan
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_Q1_MISSING_ARTIFACTS___RECOVERY_PLAN.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: json_repair
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_Q1 — MISSING ARTIFACTS / RECOVERY PLAN

TASK: Identify missing artifacts and propose a recovery plan.

OUTPUTS:
	•	QA_MISSING_ARTIFACTS.json

---

## Prompt
- prompt_id: rte_v3_prompt_q11_artifact_collision_report
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: Q
- step: Q11
- short_name: Artifact Collision Report
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_Q11_ARTIFACT_COLLISION_REPORT.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: json_repair
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_Q11 - ARTIFACT COLLISION REPORT

TASK: Detect declared artifact collisions across the pipeline promptpack.

GOAL:
- Produce a deterministic collision report from declared outputs per step.
- Use promptpack declarations only when determining writers.

OUTPUTS:
- QA_ARTIFACT_COLLISION_REPORT.json

HARD RULES:
1) Do not rescan repository files.
2) Compute collisions from promptpack declarations, not filesystem-only observations.
3) No invention. If a writer is not provable from promptpack, omit it and add UNKNOWN in notes.
4) Deterministic ordering is required.

REQUIRED INPUTS:
- Q_PROMPTPACK_DECLARED_OUTPUTS.json

OPTIONAL INPUTS:
- QA_PROMPT_COLLISIONS.json
- QA_RUN_MANIFEST.json

OUTPUT SCHEMA:
{
  "collisions": [
    {
      "artifact_name": "DOC_TOPIC_CLUSTERS.json",
      "writers": [
        {"phase": "D", "step_id": "D4", "prompt_file": "PROMPT_D4_...md"},
        {"phase": "D", "step_id": "D5", "prompt_file": "PROMPT_D5_...md"}
      ],
      "risk": "overwrites_in_norm",
      "recommendation": "LATEST_WINS|APPEND_LEDGER|MERGE_BY_ID",
      "notes": ["..."]
    }
  ]
}

DETERMINISM:
- Sort collisions by artifact_name.
- Sort writers by (phase, step_id, prompt_file).
- Sort notes lexicographically where possible.
- Do not emit timestamps or runtime identity fields.

---

## Prompt
- prompt_id: rte_v3_prompt_q2_duplicate_ids___prompt_collisions
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: Q
- step: Q2
- short_name: Duplicate Ids / Prompt Collisions
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_Q2_DUPLICATE_IDS___PROMPT_COLLISIONS.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: json_repair
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_Q2 — DUPLICATE IDS / PROMPT COLLISIONS

TASK: Detect duplicate IDs and prompt collisions.

OUTPUTS:
	•	QA_PROMPT_COLLISIONS.json

---

## Prompt
- prompt_id: rte_v3_prompt_q3_drift_detection___norm_diffs
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: Q
- step: Q3
- short_name: Drift Detection / Norm Diffs
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_Q3_DRIFT_DETECTION___NORM_DIFFS.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: json_repair
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_Q3 — DRIFT DETECTION / NORM DIFFS

TASK: compare raw vs norm counts + schema sanity + truncation flags.

OUTPUTS:
	•	QA_NORM_DRIFT_REPORT.json

---

## Prompt
- prompt_id: rte_v3_prompt_q9_merge___qa
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: Q
- step: Q9
- short_name: Merge / Qa
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_Q9_MERGE___QA.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: json_repair
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: high
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_Q9 — Pipeline doctor merge + QA

ROLE: Deterministic normalizer + QA bot.
GOAL: merge pipeline doctor outputs into a single report.

OUTPUTS:
  • PIPELINE_DOCTOR_REPORT.json

RULES:
  • Maintain deterministic ordering and mark any empty sections explicitly.

---

## Prompt
- prompt_id: rte_v3_prompt_r0_control_plane_truth_map
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: R
- step: R0
- short_name: Control Plane Truth Map
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_R0_CONTROL_PLANE_TRUTH_MAP.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: cross-source_synthesis
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
OUTPUTS:
- CONTROL_PLANE_TRUTH_MAP.md

Goal: CONTROL_PLANE_TRUTH_MAP.md

ROLE: Supervisor/Auditor. Evidence-first.
HARD RULE: Reason from Phase A/H/D/C normalized artifacts (required). If Phase G (governance) or Phase E (execution) normalized artifacts are present in input, incorporate them as supplemental evidence using the same citation discipline. If evidence is missing, write UNKNOWN and name the missing artifact.

OPTIONAL SURFACES (use when present):
- Phase G: GOV_CI_GATES, GOV_POLICIES, GOV_SECRETS_SURFACE — governance authority, enforcement gates
- Phase E: EXEC_BOOTSTRAP_COMMANDS, EXEC_ENV_CHAIN, EXEC_STARTUP_GRAPH — startup sequences, env precedence
- Phase X: FEATURE_INDEX_MERGED, FEATURE_SURFACE, FEATURE_CODE_MAP — feature-to-code mapping, dependency graph

TASK:
Produce the repo/home control-plane truth map.

MUST INCLUDE:
- Repo control plane surfaces (instructions, hooks, compose, router, litellm, mcp)
- Home control plane surfaces (configs, router, litellm, mcp, sqlite state)
- Invocation graph (what starts what)
- Control-plane to runtime coupling points
- Portability risks

RULES:
- Cite every claim with REPOCTRL:/HOMECTRL:/CODE:/DOC references.
- No repo rescans. No implementation changes.
- Label unevidenced statements UNKNOWN.

```markdown

OUTPUTS:
	•	TRUTH_MAP.json
```

---

## Prompt
- prompt_id: rte_v3_prompt_r1_dope_memory_implementation_truth
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: R
- step: R1
- short_name: Dope Memory Implementation Truth
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_R1_DOPE_MEMORY_IMPLEMENTATION_TRUTH.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: cross-source_synthesis
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
OUTPUTS:
- DOPE_MEMORY_IMPLEMENTATION_TRUTH.md

Goal: DOPE_MEMORY_IMPLEMENTATION_TRUTH.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason only from normalized A/H/D/C artifacts.

TASK:
Produce memory implementation truth for current system behavior.

MUST INCLUDE:
- Stores/adapters (sqlite/postgres/other)
- Schema objects from DOPE_MEMORY_SCHEMAS.json
- Write paths from DOPE_MEMORY_DB_WRITES.json
- Retention/TTL enforcement points
- Replay/re-derive surfaces (if present)
- Control-plane dependencies (env vars, compose wiring, home DBs)

FORMAT:
1) IMPLEMENTED (CODE evidence)
2) PLANNED (DOC evidence)
3) GAPS/CONFLICTS (both sides cited)
4) Minimal verification command suggestions

RULES:
- Cite statements for tables/triggers/enforcement points.
- If docs conflict, use DOC_SUPERSESSION then recency tie-breaker.

```markdown

OUTPUTS:
	•	DOPE_MEMORY_DB_WRITES.json
	•	DOPE_MEMORY_SCHEMAS.json
```

---

## Prompt
- prompt_id: rte_v3_prompt_r10_two_plane_architecture_truth
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: R
- step: R10
- short_name: Two Plane Architecture Truth
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_R10_TWO_PLANE_ARCHITECTURE_TRUTH.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: cross-source_synthesis
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_R10

## Goal
Produce a deterministic, evidence-backed architecture truth report for the two-plane model currently implemented in the repository.
Focus on explicit boundaries, authority ownership, and integration edges proven by code/config/docs.

## Inputs
- Upstream normalized artifacts (required — from A/H/D/C):
  - `SERVICE_CATALOG.json`
  - `TRINITY_ENFORCEMENT_SURFACE.json`
  - `BOUNDARY_ENFORCEMENT_POINTS.json`
  - `BOUNDARY_MERGED.json`
  - `EVENTBUS_SURFACE.json`
  - `DOPE_MEMORY_CODE_SURFACE.json`
  - `LEANTIME_INTEGRATION_TRUTH.md`
  - `RISK_REGISTER_TOP20.md`
- Optional supplemental artifacts (from B/G — use when present):
  - Phase B: `BOUNDARY_ENFORCEMENT_POINTS.json`, `REFUSAL_GUARDRAILS_SURFACE.json`, `BOUNDARY_BYPASS_RISKS.json` — boundary guard chains, refusal rails
  - Phase G: `GOV_POLICIES.json`, `GOV_CI_GATES.json` — governance authority, enforcement gates
- Supporting source/doc paths for disambiguation:
  - `src/dopemux/**`
  - `services/**`
  - `docs/90-adr/**`
  - `docs/04-explanation/**`
  - `services/registry.yaml`
- Runner context:
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`

## Outputs
- `TWO_PLANE_ARCHITECTURE_TRUTH.md`

## Schema
- Output type: deterministic markdown report (`kind: markdown`, `merge_strategy: markdown_concat`).
- Output contract:
  - `TWO_PLANE_ARCHITECTURE_TRUTH.md`
    - `canonical_writer_step_id`: `R10`
    - `required_sections`: `Plane Definitions, Authority Ownership Matrix, Cross-Plane Integration Paths, Boundary Enforcement and Failure Rails, Current Drift and Risks, Evidence Index`
- Required section order:
  1. `## Plane Definitions`
  2. `## Authority Ownership Matrix`
  3. `## Cross-Plane Integration Paths`
  4. `## Boundary Enforcement and Failure Rails`
  5. `## Current Drift and Risks`
  6. `## Evidence Index`
- Ownership matrix rows must include:
  - `surface`
  - `owner_plane`
  - `evidence`

## Extraction Procedure
1. Extract explicit plane and boundary claims from upstream artifacts.
2. Build ownership rows by matching surfaces to evidenced owner components.
3. Identify cross-plane integration edges with direct evidence.
4. Capture drift/risk items only when explicitly supported by evidence.
5. Emit required sections in deterministic order.

## Evidence Rules
- Every claim and matrix row must include evidence objects:
```json
{
  "path": "<repo-relative-path>",
  "line_range": [<start>, <end>],
  "excerpt": "<exact substring <=200 chars>"
}
```
- Evidence index must include all unique evidence references used above.
- Avoid indirect claims if direct evidence is unavailable.
- Keep all evidence paths repo-relative.

## Determinism Rules
- Output must be timestamp-free and run-id-free.
- Section order and subsection ordering are fixed.
- Matrix rows sorted by `(surface, owner_plane)`.
- Evidence entries sorted by `(path, line_start, excerpt)` with deterministic dedup.

## Anti-Fabrication Rules
- Do not invent plane boundaries or ownership rules.
- Do not infer architectural intent from naming alone.
- If ownership cannot be proven, use `UNKNOWN` with evidence gap note.
- Keep recommendations out of this truth artifact; include only evidenced state.

## Failure Modes
- Missing artifacts: emit skeletal report with required headings and explicit missing-input notes.
- Conflicting evidence: present both sides with conflict markers and evidence references.
- Ambiguous ownership: keep row with `owner_plane: UNKNOWN`.
- Excessive uncertainty: downgrade to concise truth table plus explicit unresolved list.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT: R10 - Two Plane Architecture Truth
Phase: R
Step: R10
Outputs:
- TWO_PLANE_ARCHITECTURE_TRUTH.md
Mode: synthesis
Strict: evidence_only
```

---

## Prompt
- prompt_id: rte_v3_prompt_r2_eventbus_wiring_truth
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: R
- step: R2
- short_name: Eventbus Wiring Truth
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_R2_EVENTBUS_WIRING_TRUTH.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: cross-source_synthesis
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
OUTPUTS:
- EVENTBUS_WIRING_TRUTH.md

Goal: EVENTBUS_WIRING_TRUTH.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason only from normalized A/H/D/C artifacts.

TASK:
Produce event bus wiring truth.

MUST INCLUDE:
- Event bus implementations/adapters
- Event names/topics (literal where evidenced)
- Producer mapping: event -> producers
- Consumer mapping: event -> handlers/subscribers
- Dispatch paths from producer call to consumer execution
- Control-plane impacts on routing

OUTPUT TABLE:
Event | Producers (CODE refs) | Consumers (CODE refs) | Adapter/Bus (CODE refs)

RULES:
- If event name is computed, mark as (computed) with evidence.
- No guessing missing event names.

```markdown

OUTPUTS:
	•	TRUTH_MAP.json
```

---

## Prompt
- prompt_id: rte_v3_prompt_r3_trinity_boundary_enforcement_trace
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: R
- step: R3
- short_name: Trinity Boundary Enforcement Trace
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_R3_TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: cross-source_synthesis
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
OUTPUTS:
- TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md

Goal: TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason from normalized A/H/D/C artifacts (required). If Phase B (boundary) normalized artifacts are present in input, incorporate them as supplemental evidence using the same citation discipline.

OPTIONAL SURFACES (use when present):
- Phase B: BOUNDARY_ENFORCEMENT_POINTS, REFUSAL_GUARDRAILS_SURFACE, BOUNDARY_BYPASS_RISKS — guard chains, refusal rails, bypass vectors

TASK:
Produce boundary enforcement trace.

MUST INCLUDE:
- Evidenced boundaries only
- Enforcement points (exact symbols/files)
- Refusal rails and propagation paths
- Bypass paths only when evidenced

OUTPUT:
- Boundary list with enforcement checks
- Guardrail pipeline diagram (text)
- Known bypass risks with evidence

RULES:
- Separate IMPLEMENTED checks from PLANNED doc rules.
- Do not invent boundaries.

```markdown

OUTPUTS:
	•	TRUTH_MAP.json
```

---

## Prompt
- prompt_id: rte_v3_prompt_r4_taskx_integration_truth
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: R
- step: R4
- short_name: Taskx Integration Truth
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_R4_TASKX_INTEGRATION_TRUTH.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: cross-source_synthesis
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
OUTPUTS:
- TASKX_INTEGRATION_TRUTH.md

Goal: TASKX_INTEGRATION_TRUTH.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason only from normalized A/H/D/C artifacts.

TASK:
Produce TaskX integration truth.

MUST INCLUDE:
- How taskx is invoked (scripts/hooks/ci)
- Where packets are read/written
- Operator instruction compile/injection surfaces
- Coupling to ~/.config/taskx and repo .taskx surfaces

OUTPUT:
- IMPLEMENTED integration map
- PLANNED integration map
- GAPS/RISKS

RULES:
- Cite REPO_TASKX_SURFACE and TASKX_INTEGRATION_SURFACE evidence.

```markdown

OUTPUTS:
	•	TRUTH_MAP.json
```

---

## Prompt
- prompt_id: rte_v3_prompt_r5_workflows_truth_graph
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: R
- step: R5
- short_name: Workflows Truth Graph
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_R5_WORKFLOWS_TRUTH_GRAPH.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: cross-source_synthesis
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
OUTPUTS:
- WORKFLOWS_TRUTH_GRAPH.md

Goal: WORKFLOWS_TRUTH_GRAPH.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason from normalized A/H/D/C artifacts (required). If Phase W (workflow) or Phase E (execution) normalized artifacts are present in input, incorporate them as supplemental evidence using the same citation discipline.

OPTIONAL SURFACES (use when present):
- Phase W: WORKFLOW_CATALOG, WORKFLOW_IO_MAP, WORKFLOW_COORDINATION_SURFACE, WORKFLOW_FAILURE_RECOVERY, WORKFLOW_STATE_COUPLING — runbook steps, coordination, failure scenarios
- Phase E: EXEC_STARTUP_GRAPH, EXEC_RUNTIME_MODES — startup sequences, runtime modes
- Phase X: FEATURE_DEP_GRAPH, FEATURE_CODE_MAP — feature dependency chains affecting workflow topology

TASK:
Produce workflow truth graph.

MUST INCLUDE:
- Bootstrap flows (tmux, compose, scripts)
- Multi-service workflows with order/dependencies
- Inputs/outputs/artifacts where explicit
- Instruction-file-driven workflow steps

OUTPUT:
- Workflow list (W1..Wn) with literal steps + citations
- Services involved per workflow
- UNKNOWN markers where evidence is missing

RULES:
- No inferred steps.
- Use WORKFLOW_RUNNER_SURFACE + HOME_TMUX_WORKFLOW_SURFACE + compose graph evidence.

```markdown

OUTPUTS:
	•	TRUTH_MAP.json
```

---

## Prompt
- prompt_id: rte_v3_prompt_r6_portability_and_migration_risk_ledger
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: R
- step: R6
- short_name: Portability And Migration Risk Ledger
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_R6_PORTABILITY_AND_MIGRATION_RISK_LEDGER.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: cross-source_synthesis
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
OUTPUTS:
- PORTABILITY_AND_MIGRATION_RISK_LEDGER.md

Goal: PORTABILITY_AND_MIGRATION_RISK_LEDGER.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason from normalized A/H/D/C artifacts (required). If Phase G (governance) or Phase W (workflow) normalized artifacts are present in input, incorporate them as supplemental evidence using the same citation discipline.

OPTIONAL SURFACES (use when present):
- Phase G: GOV_POLICIES, GOV_CI_GATES — governance scope, enforcement gates
- Phase W: WORKFLOW_STATE_COUPLING — state dependencies affecting portability

TASK:
Produce portability and migration risk ledger.

MUST INCLUDE:
- Home-only dependencies
- Required env vars
- MCP dependencies vs hooks opportunities
- Evidence-based "what breaks if moved to hooks"

RULES:
- Cite every risk.
- No broad refactor proposals.

```markdown

OUTPUTS:
	•	TRUTH_MAP.json
```

---

## Prompt
- prompt_id: rte_v3_prompt_r7_conflict_ledger
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: R
- step: R7
- short_name: Conflict Ledger
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_R7_CONFLICT_LEDGER.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: cross-source_synthesis
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
OUTPUTS:
- CONFLICT_LEDGER.md

Goal: CONFLICT_LEDGER.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason from normalized A/H/D/C artifacts (required). If Phase Q (QA) or Phase G (governance) normalized artifacts are present in input, incorporate them as supplemental evidence using the same citation discipline.

OPTIONAL SURFACES (use when present):
- Phase Q: QA_MISSING_ARTIFACTS, QA_NORM_DRIFT_REPORT, PIPELINE_DOCTOR_REPORT — pipeline health, missing evidence, drift
- Phase G: GOV_POLICIES — governance authority for conflict resolution hierarchy

TASK:
Produce conflict ledger across docs/code/control planes.

MUST INCLUDE:
- doc claim vs code truth
- doc vs doc conflicts
- authority decisions using evidence hierarchy

RULES:
- Use DOC_SUPERSESSION first, then recency tie-breaker for doc-vs-doc only.
- Never override code reality with docs.
- Cite both sides for each conflict.

```markdown

OUTPUTS:
	•	TRUTH_MAP.json
```

---

## Prompt
- prompt_id: rte_v3_prompt_r8_risk_register_top20
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: R
- step: R8
- short_name: Risk Register Top20
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_R8_RISK_REGISTER_TOP20.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: cross-source_synthesis
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
OUTPUTS:
- RISK_REGISTER_TOP20.md

Goal: RISK_REGISTER_TOP20.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason from normalized A/H/D/C artifacts (required). If Phase B (boundary) or Phase E (execution) or Phase Q (QA) normalized artifacts are present in input, incorporate them as supplemental evidence using the same citation discipline.

OPTIONAL SURFACES (use when present):
- Phase B: BOUNDARY_BYPASS_RISKS — bypass vectors with severity ratings
- Phase E: EXEC_RISK_FACTS — execution-layer risk locations
- Phase Q: QA_MISSING_ARTIFACTS — evidence gaps affecting risk ranking
- Phase X: FEATURE_DEP_GRAPH, FEATURE_SURFACE — feature coupling and dependency risks

TASK:
Produce top-20 risk register.

MUST INCLUDE:
- Determinism/idempotency/concurrency risks
- Boundary bypass risks
- Severity ranking with evidence
- Minimal mechanical bounding mechanisms

RULES:
- Cite every risk item.
- No large refactor recommendations.

```markdown

OUTPUTS:
	•	TRUTH_MAP.json
```

---

## Prompt
- prompt_id: rte_v3_prompt_r9_leantime_integration_truth
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: R
- step: R9
- short_name: Leantime Integration Truth
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_R9_LEANTIME_INTEGRATION_TRUTH.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: cross-source_synthesis
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_R9

## Goal
Synthesize a deterministic, evidence-anchored truth memo that describes how Leantime integration is implemented across the repository today.
This is a reconciliation step over upstream norm artifacts, not freeform analysis.

## Inputs
- Upstream normalized artifacts:
  - `REPO_LEANTIME_SURFACE.json`
  - `LEANTIME_INTEGRATION_SURFACE.json`
  - `SERVICE_ENTRYPOINTS.json`
  - `EVENTBUS_SURFACE.json`
  - `EVENT_PRODUCERS.json`
  - `EVENT_CONSUMERS.json`
  - `SERVICE_CATALOG.json`
  - `RISK_REGISTER_TOP20.md`
- Supporting source files when needed for disambiguation:
  - `services/leantime-bridge/**`
  - `src/dopemux/**`
  - `services/registry.yaml`
- Runner context:
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`

## Outputs
- `LEANTIME_INTEGRATION_TRUTH.md`

## Schema
- Output type: deterministic markdown report (`kind: markdown`, `merge_strategy: markdown_concat`).
- Output contract:
  - `LEANTIME_INTEGRATION_TRUTH.md`
    - `canonical_writer_step_id`: `R9`
    - `required_sections`: `Scope, Confirmed Integration Surfaces, Data and Event Flows, Configuration and Runtime Contracts, Gaps and Unknowns, Evidence Index`
- Required section order:
  1. `## Scope`
  2. `## Confirmed Integration Surfaces`
  3. `## Data and Event Flows`
  4. `## Configuration and Runtime Contracts`
  5. `## Gaps and Unknowns`
  6. `## Evidence Index`
- Every claim section must include explicit evidence bullets (`path`, `line_range`, `excerpt`).

## Extraction Procedure
1. Aggregate and deduplicate relevant items from upstream artifacts.
2. Build claim statements only from evidence-backed facts.
3. Map each claim to one or more evidence records.
4. Emit required sections in the exact order.
5. Keep unresolved items in `Gaps and Unknowns` with `UNKNOWN` labels.

## Evidence Rules
- Each load-bearing statement must cite evidence in this structure:
```json
{
  "path": "<repo-relative-path>",
  "line_range": [<start>, <end>],
  "excerpt": "<exact substring <=200 chars>"
}
```
- Evidence must reference repository files or upstream norm artifacts only.
- No paraphrased quotes in evidence index.
- Evidence paths remain repo-relative for portability.

## Determinism Rules
- Markdown output must not contain timestamps, run IDs, or non-deterministic counters.
- Sort evidence entries by `(path, line_start, excerpt)` and claims by stable claim key.
- Keep heading order fixed exactly as defined in the schema.
- Use deterministic bullet ordering for repeated categories.

## Anti-Fabrication Rules
- Do not invent integration paths, APIs, or runtime behavior.
- Do not promote inferred architecture claims to fact.
- If an expected integration surface has no evidence, mark as `UNKNOWN`.
- Never use `Legacy Context` as evidence.

## Failure Modes
- Missing upstream artifacts: emit report with `Scope` + `Gaps and Unknowns` + `Evidence Index`.
- Conflicting artifact claims: include both with explicit conflict notes and evidence.
- Partial evidence: keep claim as tentative with `status: needs_review`.
- Markdown schema risk: prefer empty section placeholders over dropping required headings.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT: R9 - Leantime Integration Truth
Phase: R
Step: R9
Outputs:
- LEANTIME_INTEGRATION_TRUTH.md
Mode: synthesis
Strict: evidence_only
```

---

## Prompt
- prompt_id: rte_v3_prompt_t0_task_packet_factory
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: T
- step: T0
- short_name: Task Packet Factory
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_T0_TASK_PACKET_FACTORY.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: output_normalization
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
Goal: Produce an implementation-ready top-10 TP backlog from R/X norm artifacts.

Role:
- Arbitration planner only. Do not implement code.
- Truth authority is R norm artifacts.

Inputs:
- R norm artifacts (R0-R8 outputs) from extraction/runs/<run_id>/R_arbitration/norm/
- X feature/risk catalogs from extraction/runs/<run_id>/X_feature_index/norm/
- Repo governance constraints from AGENTS.md and .claude/PROJECT_INSTRUCTIONS.md

Outputs:
- TP_BACKLOG_TOPN.json
- TP_INDEX.json

Required schema keys for TP_BACKLOG_TOPN.json:
- run_id
- generated_at
- packets (array)
- packets[].tp_id
- packets[].title
- packets[].priority
- packets[].problem_statement
- packets[].authority_inputs (array of repo paths to R artifacts)
- packets[].invariants (array)
- packets[].scope_in
- packets[].scope_out
- packets[].acceptance_criteria (array)
- packets[].rollback
- packets[].stop_conditions (array)
- packets[].implementer_target

Hard rules:
- implementer_target must equal "Codex Desktop (GPT-5.3-Codex)" for every packet.
- authority_inputs must reference only R/X norm artifacts by path.
- No packet may require repo re-scan or truth reinterpretation.
- No packet may omit deterministic verification commands.

Stop conditions:
- Any TP missing scope, invariants, commands, acceptance criteria, rollback, or stop conditions.
- Any TP proposes a refactor without evidence-driven necessity.

---

## Prompt
- prompt_id: rte_v3_prompt_t1_emit_task_packets___top10
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: T
- step: T1
- short_name: Emit Task Packets / Top10
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_T1_EMIT_TASK_PACKETS___TOP10.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: output_normalization
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
MODE: Arbitration output only. Do not implement code.
EVIDENCE REQUIRED: Every load-bearing claim must map to authority input paths.
OUTPUT: Markdown packets plus JSON index.
STABLE ORDER: Sort packets by priority, then tp_id.
CHUNKING: If output would exceed context, emit PART files and a CAP_NOTICES file.

# Phase T1: Emit Task Packets (Top 10)

Outputs:
- TP_PACKETS_TOP10.partX.md
- TP_PACKET_IMPLEMENTATION_INDEX.json

Prompt:
ROLE: GPT-5.2 (arbitration).
Inputs:
- TP_BACKLOG_TOPN.json
- R norm artifact paths referenced by each backlog item

Action:
Generate complete Task Packet markdowns for the top 10 items in the backlog.
Each packet must be implementation-ready for Codex Desktop and must not relitigate truth.

Required packet header block (exact keys):
- Implementer: Codex Desktop (GPT-5.3-Codex)
- Authority Inputs: <list of R/X norm artifact paths>
- Forbidden: re-run extraction; reinterpret truth without new evidence
- Required Proofs: git diff --stat, tests run, acceptance checks, rollback verification

Required sections per packet:
- Objective
- Scope (IN / OUT)
- Invariants
- Plan
- Exact commands
- Acceptance criteria
- Rollback
- Stop conditions

Required schema keys for TP_PACKET_IMPLEMENTATION_INDEX.json:
- run_id
- generated_at
- packet_count
- packets (array)
- packets[].tp_id
- packets[].title
- packets[].implementer_target
- packets[].authority_inputs
- packets[].packet_markdown_locator

---

## Prompt
- prompt_id: rte_v3_prompt_t2_packet_schema___authority_rules
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: T
- step: T2
- short_name: Packet Schema / Authority Rules
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_T2_PACKET_SCHEMA___AUTHORITY_RULES.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: output_normalization
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_T2 — PACKET SCHEMA / AUTHORITY RULES

TASK: Define the canonical Task Packet schema and authority hierarchy used by Phase T.

OUTPUTS:
- TP_SCHEMA.json
- TP_AUTHORITY_RULES.json

Rules:
- implementer_target must be exactly `Codex Desktop (GPT-5.3-Codex)`.
- Authority hierarchy is strict: R norm artifacts > X norm artifacts > policy docs.
- Every packet must include evidence-backed `authority_inputs` paths.
- No packet may require re-scan, truth reinterpretation, or undocumented assumptions.
- Define required fields, validation constraints, and failure reasons for schema noncompliance.

---

## Prompt
- prompt_id: rte_v3_prompt_t3_packet_generation___batched
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: T
- step: T3
- short_name: Packet Generation / Batched
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_T3_PACKET_GENERATION___BATCHED.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: output_normalization
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_T3 — PACKET GENERATION / BATCHED

TASK: Generate implementation-ready Task Packets in deterministic batches from R and X norm artifacts.

OUTPUTS:
- TP_BATCHED_PACKETS.partX.md
- TP_BATCH_INDEX.json

Rules:
- Emit packets in stable order by priority, then `tp_id`.
- Each packet must include: objective, scope in/out, invariants, plan, exact commands, acceptance criteria, rollback, stop conditions.
- Each packet must include a commit plan and explicit acceptance gates.
- Every load-bearing claim must cite `authority_inputs` paths.
- If output exceeds context, split into `.partX` artifacts and include full index references in `TP_BATCH_INDEX.json`.

---

## Prompt
- prompt_id: rte_v3_prompt_t4_packet_dedup___collision_resolution
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: T
- step: T4
- short_name: Packet Dedup / Collision Resolution
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_T4_PACKET_DEDUP___COLLISION_RESOLUTION.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: output_normalization
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_T4 — PACKET DEDUP / COLLISION RESOLUTION

TASK: Deduplicate Task Packets and resolve title/id collisions deterministically.

OUTPUTS:
- TP_DEDUPED.json
- TP_COLLISIONS.json

Rules:
- Detect duplicate `tp_id`, duplicate normalized titles, and materially overlapping scopes.
- Resolve collisions with deterministic tie-breaks: higher evidence density, lower blast radius, earlier dependency.
- Preserve traceability from deduped packets to source packet IDs.
- Record dropped/merged packets and reason codes in `TP_COLLISIONS.json`.

---

## Prompt
- prompt_id: rte_v3_prompt_t5_packet_ordering___run_plan
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: T
- step: T5
- short_name: Packet Ordering / Run Plan
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_T5_PACKET_ORDERING___RUN_PLAN.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: output_normalization
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_T5 — PACKET ORDERING / RUN PLAN

TASK: Build the execution order for Task Packets using dependency-aware planning.

OUTPUTS:
- TP_RUN_PLAN.json
- TP_BACKLOG_TOPN.json

Rules:
- Build a dependency graph across packets and topologically sort the plan.
- Default precedence: control plane -> extraction -> arbitration -> synthesis.
- Produce a runnable sequence with blocking dependencies, parallel-safe groups, and gate checks.
- Include explicit prerequisites and postconditions per packet.

---

## Prompt
- prompt_id: rte_v3_prompt_t9_merge___qa
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: T
- step: T9
- short_name: Merge / Qa
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_T9_MERGE___QA.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: output_normalization
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_T9 — MERGE / QA

TASK: Merge all Phase T packet artifacts, run QA, and emit canonical Task Packet outputs.

OUTPUTS:
- TP_INDEX.json
- TP_MERGED.json
- TP_QA.json
- TP_SUMMARY.md
- TP_BACKLOG_TOPN.json

QA requirements:
- Validate required schema fields for every packet.
- Validate implementer target, evidence paths, and acceptance/rollback completeness.
- Emit missing-evidence list and unresolved-collision list.
- Emit packet counts by priority and dependency tier.
- Fail closed if required canonical outputs cannot be produced.

---

## Prompt
- prompt_id: rte_v3_prompt_z0_freeze_inventory___checksums
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: Z
- step: Z0
- short_name: Freeze Inventory / Checksums
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_Z0_FREEZE_INVENTORY___CHECKSUMS.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: output_normalization
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_Z0 — FREEZE INVENTORY / CHECKSUMS

TASK: Build an inventory and checksums for the handoff freeze.

OUTPUTS:
	•	FREEZE_FILE_INDEX.json
	•	FREEZE_CHECKSUMS.json

---

## Prompt
- prompt_id: rte_v3_prompt_z1_proof_pack___runbook
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: Z
- step: Z1
- short_name: Proof Pack / Runbook
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_Z1_PROOF_PACK___RUNBOOK.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: output_normalization
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_Z1 — PROOF PACK / RUNBOOK

TASK: Generate a proof pack snapshot and runbook.

OUTPUTS:
	•	PROOF_PACK.md

---

## Prompt
- prompt_id: rte_v3_prompt_z2_opus_input_bundle___manifest
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: Z
- step: Z2
- short_name: Opus Input Bundle / Manifest
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_Z2_OPUS_INPUT_BUNDLE___MANIFEST.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: output_normalization
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_Z2 — OPUS INPUT BUNDLE / MANIFEST

TASK: Generate a deterministic export bundle manifest for Opus + Codex.

OUTPUTS:
	•	OPUS_INPUT_MANIFEST.json

---

## Prompt
- prompt_id: rte_v3_prompt_z9_freeze_manifest___checksums
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: Z
- step: Z9
- short_name: Freeze Manifest / Checksums
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_Z9_FREEZE_MANIFEST___CHECKSUMS.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: output_normalization
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_Z9 — FREEZE MANIFEST / CHECKSUMS

TASK: Produce a deterministic freeze handoff manifest with verification instructions and QA.

OUTPUTS:
- FREEZE_MANIFEST.json
- FREEZE_README.md
- FREEZE_QA.json

Rules:
- Include SHA-256 for every file in phase `norm/` and `qa/` outputs for A/H/D/C/E/W/B/G/Q/R/X/T/Z when present.
- Include prompt corpus fingerprint entries for active `services/repo-truth-extractor/prompts/v3/PROMPT_*.md` files.
- Record missing expected artifacts and failure counts by phase.
- `FREEZE_README.md` must document deterministic verification commands.

---

## Prompt
- prompt_id: rte_v3_prompt_s0_opus_architecture_synthesis
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: S
- step: S0
- short_name: Opus Architecture Synthesis
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_S0_OPUS_ARCHITECTURE_SYNTHESIS.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: cross-source_synthesis
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_S0 - OPUS ARCHITECTURE + SUBSYSTEM SYNTHESIS (from Truth Pack)

ROLE: Synthesis writer (deep, evidence-bounded).
MODE: Evidence-bounded synthesis. No excavation.

GOAL:
- Produce a decision-grade architecture map for Dopemux using only phase synthesis inputs.
- Preserve implemented vs planned distinctions and fail closed on missing evidence.

OUTPUTS:
- S0_ARCHITECTURE_SYNTHESIS_OPUS.md

HARD RULES:
1) Do not rescan the repo or home. Use only supplied synthesis artifacts.
2) Every non-trivial claim must end with:
   EVIDENCE: <artifact_filename>#<section_heading_or_anchor>
3) If evidence is missing or ambiguous, write UNKNOWN and name the missing artifact(s).
4) Prefer IMPLEMENTED over PLANNED. Label both explicitly. If unclear, mark UNKNOWN.
5) Use deterministic language only. No hedging, no timestamps, no non-auditable claims.

INPUTS (required):
- R0_CONTROL_PLANE_TRUTH_MAP.md
- R1_DOPE_MEMORY_IMPLEMENTATION_TRUTH.md
- R2_EVENTBUS_WIRING_TRUTH.md
- R3_TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md
- R4_TASKX_INTEGRATION_TRUTH.md
- R5_WORKFLOWS_TRUTH_GRAPH.md
- R6_PORTABILITY_AND_MIGRATION_RISK_LEDGER.md
- R7_CONFLICT_LEDGER.md
- R8_RISK_REGISTER_TOP20.md

INPUTS (optional):
- FEATURE_INDEX_MERGED.json
- TP_MERGED.json
- TP_SUMMARY.md
- FREEZE_MANIFEST.json
- FREEZE_README.md

OUTPUT FORMAT (write the full content of S0_ARCHITECTURE_SYNTHESIS_OPUS.md):
1) Architecture Snapshot
- Current implemented control planes, data planes, and operational boundaries.
- Planned or disputed surfaces clearly separated.

2) Subsystem Boundary Map
- control plane
- dope-memory
- eventbus
- trinity, boundaries, and guardrails
- taskx integration
- workflow and automation surfaces

3) Conflict Consumption (from R7)
- For each top conflict, classify as RESOLVED or ESCALATE_TO_PRO.
- Include decision rationale with evidence anchors for both sides.

4) Risk-to-Decision Mapping (from R8)
- Each major decision must cite at least one risk ID from R8.
- Include mitigation notes tied to cited risk evidence.

5) Decision Points
- 2-3 options per decision
- recommendation
- stop conditions
- minimal verification suggestions (commands are suggestions only)

6) UNKNOWN Register
- Strict list of unresolved claims and exact missing evidence artifacts.

7) PRO_ESCALATIONS
- Output a deterministic list sorted by escalation_id.
- Each row must include:
  - escalation_id
  - conflict_id
  - kind (conflict|collision|risk)
  - recommended_manual_prompt (MANUAL_PRO_CONFLICT_RULING.md|MANUAL_PRO_COLLISION_POLICY.md|MANUAL_PRO_RISK_RERANK.md)
  - missing_evidence[]
- If no escalations are needed, output an empty list.

---

## Prompt
- prompt_id: rte_v3_prompt_s1_opus_mcp_to_hooks_migration_plan
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: S
- step: S1
- short_name: Opus Mcp To Hooks Migration Plan
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_S1_OPUS_MCP_TO_HOOKS_MIGRATION_PLAN.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: cross-source_synthesis
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_S1 - OPUS MCP TO HOOKS MIGRATION PLAN (evidence-bounded)

ROLE: Migration planner (audit-grade, conservative).
MODE: Evidence-bounded synthesis. No excavation.

GOAL:
- Produce a staged MCP-to-hooks migration plan using only supplied synthesis artifacts.
- Preserve boundary controls and avoid behavioral drift.

OUTPUTS:
- S1_MCP_TO_HOOKS_MIGRATION_PLAN.md

HARD RULES:
1) Do not rescan the repo or invent components.
2) Every non-trivial claim must end with:
   EVIDENCE: <artifact_filename>#<section_heading_or_anchor>
3) If evidence is missing, write UNKNOWN and exclude the candidate from execution steps.
4) Prefer minimal mechanical moves. No refactors.
5) All no-go gates must tie to R8 risk IDs and R7 conflicts when relevant.

INPUTS (required):
- R0_CONTROL_PLANE_TRUTH_MAP.md
- R3_TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md
- R6_PORTABILITY_AND_MIGRATION_RISK_LEDGER.md
- R7_CONFLICT_LEDGER.md
- R8_RISK_REGISTER_TOP20.md

INPUTS (optional):
- REPO_MCP_SERVER_DEFS.json
- REPO_HOOKS_SURFACE.json
- REPO_MCP_PROXY_SURFACE.json
- REPO_ROUTER_SURFACE.json
- FEATURE_INDEX_MERGED.json

OUTPUT FORMAT (write the full content of S1_MCP_TO_HOOKS_MIGRATION_PLAN.md):
1) Scope and Constraints
- Summarize objective boundaries and guardrails.

2) Candidate Inventory
- Include only candidates with evidence for both current MCP mechanism and target hook surface.
- Mark unsupported candidates as UNKNOWN with missing evidence references.

3) Plan Stages
- Entry criteria (evidence-based)
- Steps (mechanical)
- Verification suggestions
- Rollback path

4) No-Go Triggers Table
- Columns: trigger, linked risk_id (R8), linked conflict_id (R7 if applicable), evidence.

5) UNKNOWN and Missing Evidence Register
- Explicit unresolved items and required artifacts.

---

## Prompt
- prompt_id: rte_v3_prompt_s2_decision_dossier
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: S
- step: S2
- short_name: Decision Dossier
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_S2_DECISION_DOSSIER.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: cross-source_synthesis
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_S2 - DECISION DOSSIER (evidence-bounded)

ROLE: Decision synthesist.
MODE: Compression and arbitration-ready synthesis from trusted artifacts only.

GOAL:
- Convert synthesis findings into a decision dossier that can drive implementation packets.

OUTPUTS:
- S2_DECISION_DOSSIER.md

HARD RULES:
1) Use only supplied synthesis artifacts.
2) Every decision row must include evidence anchors.
3) If evidence is insufficient, output UNKNOWN and required evidence.
4) Keep entries deterministic, concise, and mechanically actionable.

INPUTS (required):
- S0_ARCHITECTURE_SYNTHESIS_OPUS.md
- S1_MCP_TO_HOOKS_MIGRATION_PLAN.md
- R7_CONFLICT_LEDGER.md
- R8_RISK_REGISTER_TOP20.md

INPUTS (optional):
- FEATURE_INDEX_MERGED.json
- TP_MERGED.json

OUTPUT FORMAT (write the full content of S2_DECISION_DOSSIER.md):
1) Decision Table
- decision_id
- context
- options
- recommendation
- evidence anchors
- risk_ids
- verification suggestions
- stop conditions

2) Escalation Queue
- Items requiring PRO rulings with conflict and risk references.

3) UNKNOWN Register
- Explicit unresolved decisions and missing evidence sources.

4) PRO_ESCALATIONS
- Output a deterministic list sorted by escalation_id.
- Each row must include:
  - escalation_id
  - conflict_id
  - kind (conflict|collision|risk)
  - recommended_manual_prompt (MANUAL_PRO_CONFLICT_RULING.md|MANUAL_PRO_COLLISION_POLICY.md|MANUAL_PRO_RISK_RERANK.md)
  - missing_evidence[]
- If no escalations are needed, output an empty list.

---

## Prompt
- prompt_id: rte_v3_prompt_s3_arch_proof_hooks
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: S
- step: S3
- short_name: Arch Proof Hooks
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_S3_ARCH_PROOF_HOOKS.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: cross-source_synthesis
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_S3 - ARCHITECTURE PROOF HOOKS

ROLE: Verification planner.
MODE: Evidence-bounded conversion of claims into proof hooks.

GOAL:
- Produce proof hooks that map architecture claims to minimal verification suggestions.

OUTPUTS:
- S3_ARCH_PROOF_HOOKS.md

HARD RULES:
1) Do not rescan repo or claim commands were executed.
2) Every hook must cite claim evidence and expected verification signal.
3) Keep hooks minimal and deterministic.
4) If a hook cannot be defined from evidence, emit UNKNOWN with missing artifacts.

INPUTS (required):
- S0_ARCHITECTURE_SYNTHESIS_OPUS.md
- S1_MCP_TO_HOOKS_MIGRATION_PLAN.md
- S2_DECISION_DOSSIER.md
- R8_RISK_REGISTER_TOP20.md

INPUTS (optional):
- TP_MERGED.json
- FREEZE_MANIFEST.json

OUTPUT FORMAT (write the full content of S3_ARCH_PROOF_HOOKS.md):
1) Claim to Proof Hook Table
- claim_id
- claim_statement
- evidence
- verification_command_suggestion
- expected_signal
- risk_link

2) Priority Proof Set
- Minimal high-value hooks for first execution.

3) UNKNOWN Hooks
- Claims lacking sufficient evidence to define checks.

---

## Prompt
- prompt_id: rte_v3_prompt_s4_truth_pack_index
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: S
- step: S4
- short_name: Truth Pack Index
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_S4_TRUTH_PACK_INDEX.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: cross-source_synthesis
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_S4 - TRUTH PACK INDEX

ROLE: Provenance index writer.
MODE: Evidence-bounded synthesis from provided phase inputs only.

GOAL:
- Produce a deterministic truth-pack provenance index with checksums when available.

OUTPUTS:
- S4_TRUTH_PACK_INDEX.json

HARD RULES:
1) Consume only provided precollected inputs.
2) Do not rescan repository trees.
3) Do not fabricate hashes, source phases, or file sizes.
4) If sha256 is not available, set sha256 to UNKNOWN and explain briefly.

REQUIRED INPUTS:
- R7_CONFLICT_LEDGER.md
- R8_RISK_REGISTER_TOP20.md

OPTIONAL INPUTS:
- S_PHASE_TRUTH_PACK_PROVENANCE.json
- FEATURE_INDEX_MERGED.json
- TP_MERGED.json
- TP_SUMMARY.md
- FREEZE_MANIFEST.json
- FREEZE_README.md
- PRO_CONFLICT_RULING.<conflict_id>.json
- PRO_COLLISION_POLICY.<artifact_name>.json
- PRO_RISK_RERANK.<batch_id>.json

OUTPUT SCHEMA:
{
  "truth_pack_inputs": [
    {
      "source_phase": "R|X|T|Z|MANUAL",
      "artifact_name": "R7_CONFLICT_LEDGER.md",
      "path": ".../norm/R7_CONFLICT_LEDGER.md",
      "sha256": "...|UNKNOWN",
      "bytes": 12345
    }
  ],
  "missing_expected_inputs": [
    {"artifact_name": "FEATURE_INDEX_MERGED.json", "reason": "not present in X/norm"}
  ]
}

DETERMINISM:
- Sort truth_pack_inputs by (source_phase, artifact_name, path).
- Sort missing_expected_inputs by artifact_name.
- Do not emit timestamps or run_id fields.

---

## Prompt
- prompt_id: rte_v3_prompt_s5_decision_graph
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: S
- step: S5
- short_name: Decision Graph
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_S5_DECISION_GRAPH.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: cross-source_synthesis
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: high
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PROMPT_S5 - DECISION GRAPH

ROLE: Decision graph synthesist.
MODE: Evidence-bounded graph construction.

GOAL:
- Build a deterministic decision/risk/conflict/evidence graph from provided synthesis inputs.

OUTPUTS:
- S5_DECISION_GRAPH.json

HARD RULES:
1) Use only provided inputs.
2) No repository rescans.
3) No fabricated nodes, edges, IDs, or evidence anchors.
4) If an edge cannot be grounded, omit it and capture UNKNOWN in notes.

REQUIRED INPUTS:
- R7_CONFLICT_LEDGER.md
- R8_RISK_REGISTER_TOP20.md

OPTIONAL INPUTS:
- S0_ARCHITECTURE_SYNTHESIS_OPUS.md
- S1_MCP_TO_HOOKS_MIGRATION_PLAN.md
- S2_DECISION_DOSSIER.md
- S4_TRUTH_PACK_INDEX.json
- PRO_CONFLICT_RULING.<conflict_id>.json
- PRO_COLLISION_POLICY.<artifact_name>.json
- PRO_RISK_RERANK.<batch_id>.json

OUTPUT SCHEMA:
{
  "nodes": [
    {"id": "DEC-001", "type": "decision|risk|conflict|evidence", "label": "..."}
  ],
  "edges": [
    {"from": "DEC-001", "to": "RISK-014", "type": "mitigates|blocks|supported_by|references"}
  ],
  "notes": ["..."]
}

DETERMINISM:
- Use stable IDs only.
- Sort nodes by id.
- Sort edges by (from, to, type).
- Sort notes lexicographically when possible.
- Do not emit timestamps or runtime identity keys.

---

## Prompt
- prompt_id: rte_v3_prompt_m0_runtime_export_inventory
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: M
- step: M0
- short_name: Runtime Export Inventory
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_M0_RUNTIME_EXPORT_INVENTORY.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: unknown
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
Goal: M0_RUNTIME_EXPORT_INVENTORY.json

Prompt:
- Task: detect runtime stores and config surfaces only within allowlisted home roots:
  - ~/.dopemux/**
  - ~/.config/dopemux/**
  - ~/.config/taskx/**
  - ~/.config/litellm/**
  - ~/.config/mcp/**
- Identify likely state stores: *.sqlite, *.sqlite3, *.db, context.db, global_index.sqlite.
- Output fields must include for each path:
  - path, size, mtime, classification (sqlite_db|config|cache|unknown), exportability (ok|permission_denied|missing_tool|unsafe).
- Hard rules:
  - No full file content dumps.
  - If caps are hit, emit TRUNCATED marker and counts.
  - Do not include secrets, tokens, or raw message content.

---

## Prompt
- prompt_id: rte_v3_prompt_m1_sqlite_schema_snapshots
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: M
- step: M1
- short_name: Sqlite Schema Snapshots
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_M1_SQLITE_SCHEMA_SNAPSHOTS.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: unknown
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
Goal: M1_SQLITE_SCHEMA_SNAPSHOTS.json

Prompt:
- Task: for each sqlite/db discovered in M0, export schema-only metadata.
- Include:
  - table names
  - index names
  - trigger names
  - PRAGMA user_version
  - PRAGMA foreign_keys
  - sqlite_version when available
- Hard rules:
  - No row dumps.
  - No blob/text content export.
  - Report per-db failures as status/error without guessing.

---

## Prompt
- prompt_id: rte_v3_prompt_m2_sqlite_table_counts
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: M
- step: M2
- short_name: Sqlite Table Counts
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_M2_SQLITE_TABLE_COUNTS.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: unknown
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
Goal: M2_SQLITE_TABLE_COUNTS.json

Prompt:
- Task: for each sqlite table discovered in M1, export count(*) only.
- Include:
  - db path
  - table name
  - row_count
  - status/error when count cannot be computed
- Hard rules:
  - No row-level exports.
  - No text/blob fields.
  - Keep output bounded and deterministic.

---

## Prompt
- prompt_id: rte_v3_prompt_m3_conport_export_safe
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: M
- step: M3
- short_name: Conport Export Safe
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_M3_CONPORT_EXPORT_SAFE.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: unknown
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
Goal: M3_CONPORT_EXPORT_SAFE.json

Prompt:
- Task: produce a safe ConPort runtime export summary using M0/M1/M2 and config references.
- Include:
  - schema summary references
  - table count references
  - config surface references (path + key names only)
  - implementer metadata: implementer="GPT-5.3-Codex", authority="Codex CLI/Desktop"
- Hard rules:
  - Redact all values; keep key names only.
  - Hash stable identifiers as sha256(value)[:12].
  - Never include raw memory/chat/content fields.

---

## Prompt
- prompt_id: rte_v3_prompt_m4_dope_context_export_safe
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: M
- step: M4
- short_name: Dope Context Export Safe
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_M4_DOPE_CONTEXT_EXPORT_SAFE.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: unknown
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
Goal: M4_DOPE_CONTEXT_EXPORT_SAFE.json

Prompt:
- Task: produce a safe dope-context runtime export summary using M0/M1/M2 and config references.
- Include:
  - schema summary references
  - table count references
  - config surface references (path + key names only)
  - implementer metadata: implementer="GPT-5.3-Codex", authority="Codex CLI/Desktop"
- Hard rules:
  - Redact all values; keep key names only.
  - Hash stable identifiers as sha256(value)[:12].
  - Never include raw memory/chat/content fields.

---

## Prompt
- prompt_id: rte_v3_prompt_m5_mcp_health_export_safe
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: M
- step: M5
- short_name: Mcp Health Export Safe
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_M5_MCP_HEALTH_EXPORT_SAFE.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: unknown
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
Goal: M5_MCP_HEALTH_EXPORT_SAFE.json

Prompt:
- Task: export MCP health summary without network calls.
- Include:
  - MCP server definitions (name, command, args count)
  - env keys only (never env values)
  - file/config presence checks and parseability status
  - implementer metadata: implementer="GPT-5.3-Codex", authority="Codex CLI/Desktop"
- Hard rules:
  - Do not perform network probes.
  - Do not expose secrets or values.
  - Keep output bounded; include truncation markers when capped.

---

## Prompt
- prompt_id: rte_v3_prompt_m6_runtime_export_index
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: M
- step: M6
- short_name: Runtime Export Index
- source_path: services/repo-truth-extractor/prompts/v3/PROMPT_M6_RUNTIME_EXPORT_INDEX.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: unknown
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
Goal: M6_RUNTIME_EXPORT_INDEX.json

Prompt:
- Task: write final runtime export index for Phase M.
- Include:
  - attempted exports
  - successful outputs
  - missing prerequisites
  - failures with reason codes
  - redaction rules applied
  - caps/truncation markers
- Include command strings used for verification where applicable.
- Hard rules:
  - No sensitive values.
  - No raw payload dumps.

---

## Prompt
- prompt_id: rte_v3_manual_pro_collision_policy
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: V3
- step: UNKNOWN
- short_name: Manual Pro Collision Policy
- source_path: services/repo-truth-extractor/prompts/v3/manual/MANUAL_PRO_COLLISION_POLICY.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: unknown
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# MANUAL_PRO_COLLISION_POLICY

ROLE: GPT-5.2-pro artifact collision policy judge.
MODE: JSON-only ruling, deterministic, short, manual execution only.

INPUT:
- One collision entry from `QA_ARTIFACT_COLLISION_REPORT.json`.
- Candidate writer steps and evidence anchors.
- Optional risk/conflict anchors from `R7_CONFLICT_LEDGER.md` and `R8_RISK_REGISTER_TOP20.md`.

RULES:
1) Output JSON only.
2) No paragraphs; keep output terse.
3) Choose exactly one policy: `LATEST_WINS|APPEND_LEDGER|MERGE_BY_ID`.
4) Include acceptance tests with expected signals.
5) If evidence is insufficient, set `dedup_rule` to `UNKNOWN` and explain in tests.

OUTPUT SCHEMA:
{
  "artifact_name": "DOC_TOPIC_CLUSTERS.json",
  "policy": "LATEST_WINS|APPEND_LEDGER|MERGE_BY_ID",
  "canonical_key": "id",
  "dedup_rule": "KEEP_NEWEST|KEEP_MOST_EVIDENCED|KEEP_HIGHEST_CONFIDENCE|UNKNOWN",
  "acceptance_tests": [
    {"test": "...", "expected": "..."}
  ]
}

---

## Prompt
- prompt_id: rte_v3_manual_pro_conflict_ruling
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: V3
- step: UNKNOWN
- short_name: Manual Pro Conflict Ruling
- source_path: services/repo-truth-extractor/prompts/v3/manual/MANUAL_PRO_CONFLICT_RULING.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: unknown
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# MANUAL_PRO_CONFLICT_RULING

ROLE: GPT-5.2-pro appellate conflict judge.
MODE: JSON-only ruling, terse, evidence-bounded, manual execution only.

INPUT:
- One conflict entry from `R7_CONFLICT_LEDGER.md`.
- Exact cited snippets/anchors for both sides only.

RULES:
1) Output JSON only. No prose outside JSON.
2) If evidence is insufficient, return `decision: "DEFER"` and populate `missing_evidence`.
3) Maximum 8 `rationale_bullets` entries.
4) No paragraphs; all rationale must be bullets.
5) Every rationale bullet must include one or more evidence anchors.
6) Never invent artifacts, anchors, side claims, or winner IDs.

OUTPUT SCHEMA:
{
  "conflict_id": "CONFLICT-...",
  "decision": "ACCEPT_DOC|ACCEPT_CODE|SPLIT_SCOPE|DEFER",
  "winner": {
    "side": "DOC|CODE|BOTH",
    "winner_item_id": "optional"
  },
  "rationale_bullets": [
    {"bullet": "...", "evidence": ["R7_CONFLICT_LEDGER.md#..."]}
  ],
  "missing_evidence": ["R7_CONFLICT_LEDGER.md#..."]
}

---

## Prompt
- prompt_id: rte_v3_manual_pro_risk_rerank
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: V3
- step: UNKNOWN
- short_name: Manual Pro Risk Rerank
- source_path: services/repo-truth-extractor/prompts/v3/manual/MANUAL_PRO_RISK_RERANK.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: unknown
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# MANUAL_PRO_RISK_RERANK

ROLE: GPT-5.2-pro risk rerank judge.
MODE: JSON-only output, short, evidence-bounded, manual execution only.

INPUT:
- Subset of risk rows and anchors from `R8_RISK_REGISTER_TOP20.md`.

RULES:
1) Output JSON only.
2) No paragraphs; concise bullet entries only.
3) Maximum 10 rerank entries in `rerank`.
4) Each rerank entry must include evidence anchors in `why_bullets`.
5) Re-rank only when evidence supports change.
6) If insufficient evidence, keep prior severity and mark rationale as `UNKNOWN`.

OUTPUT SCHEMA:
{
  "rerank": [
    {
      "risk_id": "RISK-...",
      "new_severity": "low|med|high|critical",
      "why_bullets": [
        {"bullet": "...", "evidence": ["R8_RISK_REGISTER_TOP20.md#..."]}
      ]
    }
  ],
  "notes": ["..."]
}

---

## Prompt
- prompt_id: rte_v3_pro_ruling_ingestion_contract
- canonical_scope: rte_v3_legacy
- version_line: v3
- phase: V3
- step: UNKNOWN
- short_name: Pro Ruling Ingestion Contract
- source_path: services/repo-truth-extractor/prompts/v3/manual/PRO_RULING_INGESTION_CONTRACT.md
- owning_component: repo-truth-extractor
- invoked_by: UNKNOWN
- invokes: Legacy reference only
- status: legacy
- authority_role: legacy_reference
- prompt_kind: legacy_reference
- category: unknown
- purpose: Direct predecessor prompt retained for lineage and migration-drift analysis.
- output_contract: unknown
- validator_dependency: unknown
- model_sensitivity: medium
- route_sensitivity: medium
- openclaw_relevance: none
- notes: Bundled as legacy reference only; not treated as active unless current invocation path is proven separately.

### Full prompt text
# PRO_RULING_INGESTION_CONTRACT

ROLE: Manual ruling ingestion contract for synthesis phases.
MODE: Deterministic, evidence-bounded, manual execution only.

PURPOSE:
- Define where manual PRO rulings are stored.
- Define required keys and sorting rules.
- Define how S-phase synthesis can consume these rulings.

MANUAL RULING FILE LOCATIONS:
- <run_dir>/manual_rulings/PRO_CONFLICT_RULING.<conflict_id>.json
- <run_dir>/manual_rulings/PRO_COLLISION_POLICY.<artifact_name>.json
- <run_dir>/manual_rulings/PRO_RISK_RERANK.<batch_id>.json

REQUIRED KEYS BY FILE:
1) PRO_CONFLICT_RULING
- conflict_id
- decision
- winner
- rationale_bullets
- missing_evidence

2) PRO_COLLISION_POLICY
- artifact_name
- policy
- canonical_key
- dedup_rule
- acceptance_tests

3) PRO_RISK_RERANK
- rerank
- notes

SORTING RULES:
- Sort file processing by path (lexicographic).
- For arrays:
  - rationale_bullets sorted by bullet where possible.
  - acceptance_tests sorted by test.
  - rerank sorted by risk_id.
- Do not include timestamps in normative synthesized outputs.

S-PHASE CONSUMPTION RULES:
- Phase S may ingest manual_rulings/PRO_*.json as optional inputs.
- If rulings exist:
  - S4_TRUTH_PACK_INDEX.json should include them in truth_pack_inputs.
  - S5_DECISION_GRAPH.json should emit edges referencing ruling decisions where evidence anchors exist.
- If rulings are absent, Phase S continues without failure.

EXECUTION RULE:
- This contract does not authorize automatic PRO prompt execution.
- Manual PRO prompts are run by operator decision only.

---
