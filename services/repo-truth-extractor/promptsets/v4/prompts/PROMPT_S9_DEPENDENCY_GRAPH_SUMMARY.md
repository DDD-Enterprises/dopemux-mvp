# PROMPT_S9

## Goal
Produce `S9` synthesis output for phase `S` with deterministic structure and explicit evidence anchors.
Analyze dependency graphs to identify hotspots, circular dependencies, coupling metrics, and architectural risk areas. This step does NOT scan the repository directly — it synthesizes from pre-collected artifacts only.

## Inputs
- Required upstream artifacts (consume only, no repo scan):
  - `MODULE_DEPENDENCY_GRAPH.json`
  - `SERVICE_DEPENDENCY_GRAPH.json`
- Optional synthesis helpers:
  - `SERVICE_CATALOG.json`
  - `CODE_INVENTORY.json`
  - `PYTHON_API_SURFACE.json`
  - `S8_ARCHITECTURE_DIAGRAMS.md`
- Runner context artifacts:
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- Constraint:
  - Consume only precollected phase inputs. Do not scan source trees directly.

## Outputs
- `S9_DEPENDENCY_GRAPH_SUMMARY.md`

## Schema
- Artifact kind: markdown output with tables and analysis.
- Canonical writer: `S9`
- Required output content contracts:
  - `S9_DEPENDENCY_GRAPH_SUMMARY.md`
    - Section 1: **Graph Statistics** — node count, edge count, density, average degree for both module and service graphs
    - Section 2: **Dependency Hotspots** — top 10 most-depended-upon modules/services ranked by in-degree, with evidence
    - Section 3: **Circular Dependencies** — all detected cycles listed with full cycle path and evidence for each edge
    - Section 4: **Coupling Analysis** — afferent/efferent coupling metrics per top-level module, instability index (Ce/(Ca+Ce))
    - Section 5: **Architectural Risk Summary** — modules/services with high coupling, high fan-in, or cycle participation flagged as risks
    - Section 6: **Cross-Boundary Dependencies** — service-to-service edges that cross architectural boundaries (e.g., agent calling internal API directly)
    - Each item in tables must cite the source edge IDs from upstream dependency graphs
- Required citation shape:
  - `EVIDENCE: <artifact_filename>#<edge_id>`

## Extraction Procedure
1. Load `MODULE_DEPENDENCY_GRAPH.json` and `SERVICE_DEPENDENCY_GRAPH.json` as edge lists
2. Build adjacency structures: for each graph, compute in-degree and out-degree per node
3. **Graph Statistics**: count nodes, edges, compute density = edges / (nodes * (nodes-1))
4. **Hotspots**: sort nodes by in-degree descending, report top 10 with evidence for each incoming edge
5. **Cycle detection**: run DFS-based cycle detection on both graphs; report all cycles with complete edge paths
6. **Coupling metrics**: for each top-level module, compute Ca (afferent = in-degree), Ce (efferent = out-degree), instability I = Ce/(Ca+Ce)
7. **Risk assessment**: flag modules where I > 0.8 (highly unstable), I < 0.2 and Ce > 5 (rigid), or cycle participation
8. **Cross-boundary**: identify service graph edges where source and target belong to different architectural tiers
9. Cross-reference with `SERVICE_CATALOG.json` (if available) for service categorization
10. Emit exactly the declared output and no additional files

## Evidence Rules
- Every metric and finding must trace back to specific edges or nodes in the upstream dependency graphs.
- Evidence anchors use the form: `EVIDENCE: <artifact_filename>#<edge_id>`
- Cycle claims must list every edge ID in the cycle path.
- Hotspot rankings must cite the specific incoming edge IDs counted.

## Determinism Rules
- Do not include `generated_at`, `timestamp`, `created_at`, `updated_at`, or `run_id`.
- Use fixed heading order and fixed table row ordering by deterministic keys.
- Sort hotspot tables by in-degree descending, then alphabetical by node name.
- Sort cycle reports by cycle length ascending, then alphabetical by first node in cycle.

## Anti-Fabrication Rules
- Do not invent dependencies, cycles, or coupling metrics not supported by upstream graph data.
- Do not scan the repository directly — all information must come from declared inputs.
- Do not speculate about the impact of dependencies; only report structural facts with evidence.
- If a metric cannot be computed due to missing data, report `UNKNOWN` with explanation.

## Failure Modes
- Missing required upstream artifacts: emit `⚠️ Source artifact not available` and skip dependent sections.
- Empty dependency graph: emit `⚠️ Graph is empty — no analysis possible`.
- Very large graphs (>1000 edges): report aggregate statistics and top-N items with truncation notes.
- Disconnected components: report as separate subgraph analysis within each section.
