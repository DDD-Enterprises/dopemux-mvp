---
id: PROPOSED_FACADE_TOOLS
title: Proposed Facade Tools
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-11'
last_review: '2026-06-11'
next_review: '2026-09-09'
prelude: Proposed Facade Tools (reference) for dopemux documentation and developer
  workflows.
---
# Proposed Facade Tools

## Version A - Minimal Search / Fetch

Phase 2 only unless provenance and authority labels are strict.

- `search_evidence(query, sources, limit)` -> derived hits with source path, authority label, freshness, redaction state.
- `fetch_evidence(ref, max_bytes)` -> one allowlisted artifact excerpt or structured payload.

## Version B - Dopemux-Specific Evidence Tools


### `list_projects`

- Purpose: expose a bounded read-only evidence view for `list_projects`.
- Input schema: JSON object with explicit project/workspace scope and optional query/limit fields.
- Output schema: JSON object containing `items`, `source_system`, `authority_label`, `freshness`, `redaction_state`, and `warnings`.
- Source system: dopemux/proof filesystem.
- Authority label: surface-specific; never inferred from tool name alone.
- Allowed backends: allowlisted read handlers only.
- Denied backends/routes: mutating routes, raw MCP tools, raw filesystem browsing, tunnel/client config.
- Side-effect policy: fail closed on any write, cache mutation, indexing trigger, or hidden live call.
- Redaction policy: redact secrets, tokens, local auth paths, and oversized private payloads.
- Freshness behavior: include branch/head or runtime timestamp.
- DCP usefulness: supports GPT-5.5 synthesis with bounded evidence.
- Phase-1 suitability: Maybe after stricter source review.

### `get_project_capabilities`

- Purpose: expose a bounded read-only evidence view for `get_project_capabilities`.
- Input schema: JSON object with explicit project/workspace scope and optional query/limit fields.
- Output schema: JSON object containing `items`, `source_system`, `authority_label`, `freshness`, `redaction_state`, and `warnings`.
- Source system: dopemux/proof filesystem.
- Authority label: surface-specific; never inferred from tool name alone.
- Allowed backends: allowlisted read handlers only.
- Denied backends/routes: mutating routes, raw MCP tools, raw filesystem browsing, tunnel/client config.
- Side-effect policy: fail closed on any write, cache mutation, indexing trigger, or hidden live call.
- Redaction policy: redact secrets, tokens, local auth paths, and oversized private payloads.
- Freshness behavior: include branch/head or runtime timestamp.
- DCP usefulness: supports GPT-5.5 synthesis with bounded evidence.
- Phase-1 suitability: Maybe after stricter source review.

### `get_repo_state_snapshot`

- Purpose: expose a bounded read-only evidence view for `get_repo_state_snapshot`.
- Input schema: JSON object with explicit project/workspace scope and optional query/limit fields.
- Output schema: JSON object containing `items`, `source_system`, `authority_label`, `freshness`, `redaction_state`, and `warnings`.
- Source system: dopemux/proof filesystem.
- Authority label: surface-specific; never inferred from tool name alone.
- Allowed backends: allowlisted read handlers only.
- Denied backends/routes: mutating routes, raw MCP tools, raw filesystem browsing, tunnel/client config.
- Side-effect policy: fail closed on any write, cache mutation, indexing trigger, or hidden live call.
- Redaction policy: redact secrets, tokens, local auth paths, and oversized private payloads.
- Freshness behavior: include branch/head or runtime timestamp.
- DCP usefulness: supports GPT-5.5 synthesis with bounded evidence.
- Phase-1 suitability: Yes with wrapper.

### `list_proof_bundles`

- Purpose: expose a bounded read-only evidence view for `list_proof_bundles`.
- Input schema: JSON object with explicit project/workspace scope and optional query/limit fields.
- Output schema: JSON object containing `items`, `source_system`, `authority_label`, `freshness`, `redaction_state`, and `warnings`.
- Source system: dopemux/proof filesystem.
- Authority label: surface-specific; never inferred from tool name alone.
- Allowed backends: allowlisted read handlers only.
- Denied backends/routes: mutating routes, raw MCP tools, raw filesystem browsing, tunnel/client config.
- Side-effect policy: fail closed on any write, cache mutation, indexing trigger, or hidden live call.
- Redaction policy: redact secrets, tokens, local auth paths, and oversized private payloads.
- Freshness behavior: include branch/head or runtime timestamp.
- DCP usefulness: supports GPT-5.5 synthesis with bounded evidence.
- Phase-1 suitability: Yes with wrapper.

### `fetch_proof_bundle`

- Purpose: expose a bounded read-only evidence view for `fetch_proof_bundle`.
- Input schema: JSON object with explicit project/workspace scope and optional query/limit fields.
- Output schema: JSON object containing `items`, `source_system`, `authority_label`, `freshness`, `redaction_state`, and `warnings`.
- Source system: dopemux/proof filesystem.
- Authority label: surface-specific; never inferred from tool name alone.
- Allowed backends: allowlisted read handlers only.
- Denied backends/routes: mutating routes, raw MCP tools, raw filesystem browsing, tunnel/client config.
- Side-effect policy: fail closed on any write, cache mutation, indexing trigger, or hidden live call.
- Redaction policy: redact secrets, tokens, local auth paths, and oversized private payloads.
- Freshness behavior: include branch/head or runtime timestamp.
- DCP usefulness: supports GPT-5.5 synthesis with bounded evidence.
- Phase-1 suitability: Yes with wrapper.

### `search_decisions`

- Purpose: expose a bounded read-only evidence view for `search_decisions`.
- Input schema: JSON object with explicit project/workspace scope and optional query/limit fields.
- Output schema: JSON object containing `items`, `source_system`, `authority_label`, `freshness`, `redaction_state`, and `warnings`.
- Source system: ConPort.
- Authority label: surface-specific; never inferred from tool name alone.
- Allowed backends: allowlisted read handlers only.
- Denied backends/routes: mutating routes, raw MCP tools, raw filesystem browsing, tunnel/client config.
- Side-effect policy: fail closed on any write, cache mutation, indexing trigger, or hidden live call.
- Redaction policy: redact secrets, tokens, local auth paths, and oversized private payloads.
- Freshness behavior: include branch/head or runtime timestamp.
- DCP usefulness: supports GPT-5.5 synthesis with bounded evidence.
- Phase-1 suitability: Maybe after stricter source review.

### `search_progress`

- Purpose: expose a bounded read-only evidence view for `search_progress`.
- Input schema: JSON object with explicit project/workspace scope and optional query/limit fields.
- Output schema: JSON object containing `items`, `source_system`, `authority_label`, `freshness`, `redaction_state`, and `warnings`.
- Source system: ConPort.
- Authority label: surface-specific; never inferred from tool name alone.
- Allowed backends: allowlisted read handlers only.
- Denied backends/routes: mutating routes, raw MCP tools, raw filesystem browsing, tunnel/client config.
- Side-effect policy: fail closed on any write, cache mutation, indexing trigger, or hidden live call.
- Redaction policy: redact secrets, tokens, local auth paths, and oversized private payloads.
- Freshness behavior: include branch/head or runtime timestamp.
- DCP usefulness: supports GPT-5.5 synthesis with bounded evidence.
- Phase-1 suitability: Maybe after stricter source review.

### `search_chronicle`

- Purpose: expose a bounded read-only evidence view for `search_chronicle`.
- Input schema: JSON object with explicit project/workspace scope and optional query/limit fields.
- Output schema: JSON object containing `items`, `source_system`, `authority_label`, `freshness`, `redaction_state`, and `warnings`.
- Source system: dope-memory.
- Authority label: surface-specific; never inferred from tool name alone.
- Allowed backends: allowlisted read handlers only.
- Denied backends/routes: mutating routes, raw MCP tools, raw filesystem browsing, tunnel/client config.
- Side-effect policy: fail closed on any write, cache mutation, indexing trigger, or hidden live call.
- Redaction policy: redact secrets, tokens, local auth paths, and oversized private payloads.
- Freshness behavior: include branch/head or runtime timestamp.
- DCP usefulness: supports GPT-5.5 synthesis with bounded evidence.
- Phase-1 suitability: Maybe after stricter source review.

### `replay_chronicle_session`

- Purpose: expose a bounded read-only evidence view for `replay_chronicle_session`.
- Input schema: JSON object with explicit project/workspace scope and optional query/limit fields.
- Output schema: JSON object containing `items`, `source_system`, `authority_label`, `freshness`, `redaction_state`, and `warnings`.
- Source system: dope-memory.
- Authority label: surface-specific; never inferred from tool name alone.
- Allowed backends: allowlisted read handlers only.
- Denied backends/routes: mutating routes, raw MCP tools, raw filesystem browsing, tunnel/client config.
- Side-effect policy: fail closed on any write, cache mutation, indexing trigger, or hidden live call.
- Redaction policy: redact secrets, tokens, local auth paths, and oversized private payloads.
- Freshness behavior: include branch/head or runtime timestamp.
- DCP usefulness: supports GPT-5.5 synthesis with bounded evidence.
- Phase-1 suitability: Maybe after stricter source review.

### `search_code_docs`

- Purpose: expose a bounded read-only evidence view for `search_code_docs`.
- Input schema: JSON object with explicit project/workspace scope and optional query/limit fields.
- Output schema: JSON object containing `items`, `source_system`, `authority_label`, `freshness`, `redaction_state`, and `warnings`.
- Source system: dope-context.
- Authority label: surface-specific; never inferred from tool name alone.
- Allowed backends: allowlisted read handlers only.
- Denied backends/routes: mutating routes, raw MCP tools, raw filesystem browsing, tunnel/client config.
- Side-effect policy: fail closed on any write, cache mutation, indexing trigger, or hidden live call.
- Redaction policy: redact secrets, tokens, local auth paths, and oversized private payloads.
- Freshness behavior: include branch/head or runtime timestamp.
- DCP usefulness: supports GPT-5.5 synthesis with bounded evidence.
- Phase-1 suitability: Yes with wrapper.

### `get_index_status`

- Purpose: expose a bounded read-only evidence view for `get_index_status`.
- Input schema: JSON object with explicit project/workspace scope and optional query/limit fields.
- Output schema: JSON object containing `items`, `source_system`, `authority_label`, `freshness`, `redaction_state`, and `warnings`.
- Source system: dope-context.
- Authority label: surface-specific; never inferred from tool name alone.
- Allowed backends: allowlisted read handlers only.
- Denied backends/routes: mutating routes, raw MCP tools, raw filesystem browsing, tunnel/client config.
- Side-effect policy: fail closed on any write, cache mutation, indexing trigger, or hidden live call.
- Redaction policy: redact secrets, tokens, local auth paths, and oversized private payloads.
- Freshness behavior: include branch/head or runtime timestamp.
- DCP usefulness: supports GPT-5.5 synthesis with bounded evidence.
- Phase-1 suitability: Yes with wrapper.

### `get_workflow_status_snapshot`

- Purpose: expose a bounded read-only evidence view for `get_workflow_status_snapshot`.
- Input schema: JSON object with explicit project/workspace scope and optional query/limit fields.
- Output schema: JSON object containing `items`, `source_system`, `authority_label`, `freshness`, `redaction_state`, and `warnings`.
- Source system: task-orchestrator.
- Authority label: surface-specific; never inferred from tool name alone.
- Allowed backends: allowlisted read handlers only.
- Denied backends/routes: mutating routes, raw MCP tools, raw filesystem browsing, tunnel/client config.
- Side-effect policy: fail closed on any write, cache mutation, indexing trigger, or hidden live call.
- Redaction policy: redact secrets, tokens, local auth paths, and oversized private payloads.
- Freshness behavior: include branch/head or runtime timestamp.
- DCP usefulness: supports GPT-5.5 synthesis with bounded evidence.
- Phase-1 suitability: Yes with wrapper.
