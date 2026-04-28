# DR Pack 01: ConPort / Context Portal

Access date: 2026-04-28

## Objective

Research current Context Portal MCP / ConPort and map it to Dopemux ConPort structured context, decision, progress, custom-data, and relationship-query plane.

## Source Seeds

- https://github.com/GreatScottyMac/context-portal
- https://pypi.org/project/context-portal-mcp/
- https://github.com/GreatScottyMac/context-portal/releases
- `docs/research/mcp-customization/data/upstream-source-manifest.json`
- Dopemux runtime seed: `src/conport/memory_server.py`
- Dopemux docs seed: `docs/03-reference/systems/conport/system-conport.md`

Observed source status:

- GitHub: archived=false, pushed_at=2026-01-27T00:06:16Z.
- Latest release: v0.3.13 published 2025-10-29T00:43:41Z.
- PyPI: `context-portal-mcp` version 0.3.13 uploaded 2025-12-31T23:07:11Z.

## Required Extraction Fields

- MCP tools, resources, prompts
- transports
- storage backends
- import/export and migration surfaces
- data model and versioning
- workspace/project scoping
- search/index behavior
- graph/relationship behavior
- auth/security model
- package and release freshness
- archive/fork status
- docs freshness

## Dopemux Boundary Constraints

- ConPort may own structured decisions, progress, project context, custom data, and relationships.
- ConPort must not own passive PM metadata.
- ConPort must not own task-orchestrator workflow legality.
- ConPort must not own dope-memory chronological evidence.
- ConPort retrieval must not replace dope-context deterministic code/docs retrieval.


## Full Boundary Baseline

Every server-specific answer must preserve all of these Dopemux boundaries: dopemux is operator/control only; dopetask is external execution after wrapper handoff; Leantime owns passive PM metadata and snapshots; task-orchestrator owns workflow transitions and workflow views; ConPort owns structured decisions, progress, project context, custom data, and relationships; dope-memory owns chronicle receipts and evidence history; dope-context owns derived code/docs retrieval; dopecon-bridge is adapter/proxy/event transport only; Serena is support/code-intelligence unless runtime authority is proven.

## Authority Conflict Checks

- Does upstream position memory-bank or RAG as a full project truth store?
- Does upstream support mutable memories that conflict with evidence-preserving chronology?
- Does upstream expose task/workflow status semantics that would collide with task-orchestrator?
- Does upstream semantic search have deterministic ordering and source provenance?

## Output Contract

Return exactly:

- `items`: Top-3 actionable findings.
- `more_count`
- `next_token`
- evidence matrix
- fact vs inference separation
- UNKNOWN list
- blocker list
- responsibility collision matrix
- implementation slices with validation

## UNKNOWN / Blocker Handling

If current upstream tools, schema, storage, or release status cannot be verified, mark that field `UNKNOWN` and make customization provisional.

## Adopt / Adapt / Reject / Hide / Defer Table Requirements

Include rows for:

- decision/progress logging
- custom data
- active/project context
- relationship graph
- semantic search
- import/export
- memory-bank style claims
- any task/workflow-like claims

## Validation Requirements

- Verify current upstream source from GitHub/PyPI, not only README text.
- Compare upstream object model to Dopemux ConPort runtime tools: `mem.upsert`, `mem.search`, `graph.link`, `graph.neighbors`.
- Propose contract tests for deterministic IDs, source provenance, and no PM workflow ownership.
