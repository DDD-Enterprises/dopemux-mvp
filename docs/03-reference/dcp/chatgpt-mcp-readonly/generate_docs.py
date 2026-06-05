import os
import json

base_dir = "/Users/hue/code/dopemux-mvp/.worktrees/chatgpt-mcp-ro-0002/docs/03-reference/dcp/chatgpt-mcp-readonly"

inventory = {
    "inventory_version": "1.0",
    "surfaces": [
        {
            "name": "Task Orchestrator",
            "type": "WORK_GRAPH_SURFACE",
            "read_only": True,
            "description": "Read-only access to work items and dependencies",
            "tools": ["query_items", "query_notes", "query_dependencies", "get_next_status", "get_context", "get_next_item", "get_blocked_items"]
        },
        {
            "name": "ConPort",
            "type": "CONTEXT_SURFACE",
            "read_only": True,
            "description": "Read-only access to structured context",
            "tools": ["read_context"]
        },
        {
            "name": "dope-memory",
            "type": "MEMORY_SURFACE",
            "read_only": True,
            "description": "Read-only access to chronicle",
            "tools": ["read_chronicle"]
        },
        {
            "name": "dope-context",
            "type": "RETRIEVAL_SURFACE",
            "read_only": True,
            "description": "Read-only access to doc/code context",
            "tools": ["search_docs", "search_code"]
        }
    ],
    "denied_surfaces": [
        {
            "name": "dopecon-bridge",
            "reason": "Denied in Phase 1"
        }
    ]
}

with open(os.path.join(base_dir, "READ_ONLY_SURFACE_INVENTORY.json"), "w") as f:
    json.dump(inventory, f, indent=2)

architecture = """# Architecture: Read-Only MCP Evidence Facade

## 1. Overview
The read-only MCP evidence facade provides a secure, loopback-only projection of repository truth, execution state, and structured context to ChatGPT via the MCP protocol. It does not possess any write authority.

## 2. Component Boundaries
- **Project Registry**: Enforces eligibility of workspaces.
- **Resolver**: Maps requested projects to physical paths.
- **Response Envelope**: Standardizes metadata and structural layout for all responses.
- **Tools**: Exposed as MCP endpoints, strictly bounded to read operations.

## 3. Data Flow
- ChatGPT (Client) -> Secure Tunnel -> Facade (dopemux dcp) -> Internal Adapters -> (TO / dope-memory / ConPort)
- All paths pass through the multi-project registry.

## 4. Phase 1 Limitations
- No live writes.
- `dopecon-bridge` is denied.
- `search_all` is denied.
"""

with open(os.path.join(base_dir, "ARCHITECTURE.md"), "w") as f:
    f.write(architecture)

registry_contract = """# Multi-Project Registry Contract

## 1. Schema
The registry tracks projects by a unique `project_id`.

## 2. Validation Rules
- All incoming requests must supply a valid `project_id` (except `list_projects`).
- If `project_id` is missing or invalid, the facade rejects the request.

## 3. Eligibility vs Exposure
- `dopemux init` provides eligibility for a workspace.
- Explicit approval in the registry configuration is required for exposure via the facade.

## 4. Resolver Flow
- Request `project_id` is passed to the resolver.
- Resolver checks registry and retrieves the canonical path (resolving symlinks).
- Path is validated against the safe-paths allowlist.
"""

with open(os.path.join(base_dir, "MULTI_PROJECT_REGISTRY_CONTRACT.md"), "w") as f:
    f.write(registry_contract)

tool_contract = """# Tool Contract

## 1. Phase-1 Allowed Tools
- `list_projects`: Returns approved projects. No `project_id` required.
- `task_orchestrator_read`: Wraps read tools (`query_items`, etc). Requires `project_id`.
- `conport_read`: Reads structured context. Requires `project_id`.
- `memory_read`: Reads chronicle/memory. Requires `project_id`.

## 2. Denied Tools / Routes
- `dopecon-bridge`: Denied in Phase 1.
- `search_all`: Denied in Phase 1.
- All mutating actions (e.g., `advance_item`, `manage_items`) are denied.

## 3. Authority Labels
- All outputs must retain `OBSERVED`, `PROPOSED`, `UNKNOWN`, or `CONFLICTING` labels.
"""

with open(os.path.join(base_dir, "TOOL_CONTRACT.md"), "w") as f:
    f.write(tool_contract)

response_envelope = """# Response Envelope Schema

## Canonical Envelope
Every successful response from the facade must adhere to the following schema:
```json
{
  "project_id": "string",
  "status": "string (SUCCESS/ERROR)",
  "authority_tier": "string",
  "data": "object"
}
```

## Status Semantics
- `SUCCESS`: The data was successfully retrieved and resolved.
- `ERROR`: Retrieval failed or path was denied.
"""

with open(os.path.join(base_dir, "RESPONSE_ENVELOPE_SCHEMA.md"), "w") as f:
    f.write(response_envelope)

security_model = """# Security Model

## 1. Secure MCP Tunnel
The facade communicates with ChatGPT exclusively via the secure loopback MCP tunnel. No external ingress is allowed.

## 2. Prompt-Injection Controls
All parsed arguments from the client are treated as untrusted and must pass regex/typing validation before being passed to internal adapters.

## 3. Redaction
Sensitive fields (secrets, tokens, PII) are redacted by the facade before inclusion in the response envelope.

## 4. Side-Effect Controls
No mutable operations are permitted. The facade operates entirely in a read-only projection context.
"""

with open(os.path.join(base_dir, "SECURITY_MODEL.md"), "w") as f:
    f.write(security_model)

build_series = """# Build Series

The DCP MCP Read-Only Facade is implemented across the following packet series:
- `TP-DCP-MCP-RO-0002`: Architecture & contracts (this packet)
- `TP-DCP-MCP-RO-0003`: Discovery
- `TP-DCP-MCP-RO-0004`: Scaffold
- `TP-DCP-MCP-RO-0005`: Memory/ConPort adapters
- `TP-DCP-MCP-RO-0006`: Context/TO adapters
- `TP-DCP-MCP-RO-0007`: Integration docs
- `TP-DCP-MCP-RO-0008`: Rollout & completion
"""

with open(os.path.join(base_dir, "BUILD_SERIES.md"), "w") as f:
    f.write(build_series)

decisions = """# Decisions

## Accepted Decisions
- Use MCP protocol for ChatGPT loopback.
- Enforce strict `project_id` requirements on all non-discovery tools.
- Implement explicit registry-based exposure.

## Rejected Alternatives
- **Global search / `search_all`**: Rejected due to high risk of cross-project context pollution.
- **Live Writes**: Rejected for Phase 1 to maintain strict safety boundary.
"""

with open(os.path.join(base_dir, "DECISIONS.md"), "w") as f:
    f.write(decisions)

import shutil
src_load = "/Users/hue/code/dopemux-mvp/dcp_mcp_ro_to_load_temp/dcp_mcp_ro_to_load/TASK_ORCHESTRATOR_LOAD_SHEET.md"
dst_load = os.path.join(base_dir, "TASK_ORCHESTRATOR_LOAD.md")
shutil.copy2(src_load, dst_load)
