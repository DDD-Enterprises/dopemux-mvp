# PROMPT_S8

## Goal
Produce `S8` synthesis output for phase `S` with deterministic structure and explicit evidence anchors.
Generate architecture diagrams in Mermaid format from upstream extraction artifacts. This step does NOT scan the repository directly — it synthesizes from pre-collected artifacts only.

## Inputs
- Required upstream artifacts (consume only, no repo scan):
  - `SERVICE_CATALOG.json`
  - `MODULE_DEPENDENCY_GRAPH.json`
  - `SERVICE_DEPENDENCY_GRAPH.json`
  - `SERVICE_ENTRYPOINTS.json`
  - `REPO_COMPOSE_SERVICE_GRAPH.json`
  - `EVENTBUS_SURFACE.json`
  - `AGENT_ORCHESTRATION_SURFACE.json`
- Optional synthesis helpers:
  - `PYTHON_API_SURFACE.json`
  - `SERVICE_ENDPOINT_SURFACE.json`
  - `WORKFLOW_RUNNER_SURFACE.json`
- Runner context artifacts:
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- Constraint:
  - Consume only precollected phase inputs. Do not scan source trees directly.

## Outputs
- `S8_ARCHITECTURE_DIAGRAMS.md`

## Schema
- Artifact kind: markdown output with embedded Mermaid diagrams.
- Canonical writer: `S8`
- Required output content contracts:
  - `S8_ARCHITECTURE_DIAGRAMS.md`
    - Section 1: **Service Architecture** — Mermaid flowchart showing services, their relationships, and communication patterns from `SERVICE_DEPENDENCY_GRAPH.json`
    - Section 2: **Module Dependency Map** — Mermaid flowchart of top-level module dependencies from `MODULE_DEPENDENCY_GRAPH.json` (collapse leaf modules beyond depth 2)
    - Section 3: **Event Flow Diagram** — Mermaid sequence diagram showing eventbus producer/consumer flows from `EVENTBUS_SURFACE.json`
    - Section 4: **Compose Service Topology** — Mermaid flowchart from `REPO_COMPOSE_SERVICE_GRAPH.json` showing Docker Compose service relationships
    - Section 5: **Agent Orchestration Flow** — Mermaid flowchart of agent types, lifecycle, and communication from `AGENT_ORCHESTRATION_SURFACE.json`
    - Each section must cite the source artifact ID
- Required citation shape for load-bearing claims:
  - `EVIDENCE: <artifact_filename>#<item_id_or_section>`

## Extraction Procedure
1. Load all required upstream artifacts as specified in the inputs section
2. For the Service Architecture diagram: extract all service nodes from `SERVICE_CATALOG.json`, add edges from `SERVICE_DEPENDENCY_GRAPH.json` with edge labels from `edge_type`
3. For the Module Dependency Map: extract top-level modules from `MODULE_DEPENDENCY_GRAPH.json`, collapse leaf nodes beyond depth 2 into aggregate nodes
4. For the Event Flow diagram: build sequence flows from `EVENTBUS_SURFACE.json` producer/consumer pairs
5. For the Compose topology: extract service nodes and `depends_on` edges from `REPO_COMPOSE_SERVICE_GRAPH.json`
6. For the Agent flow: extract agent types and lifecycle states from `AGENT_ORCHESTRATION_SURFACE.json`
7. Each diagram node must include the source artifact item ID for traceability
8. Validate that all referenced item IDs exist in the source artifacts
9. If an artifact is missing or empty, emit the section with a note: `⚠️ Source artifact not available: <filename>`
10. Emit exactly the declared output and no additional files

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.
