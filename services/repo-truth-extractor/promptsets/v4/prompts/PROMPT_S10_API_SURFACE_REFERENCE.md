# PROMPT_S10

## Goal
Produce `S10` synthesis output for phase `S` with deterministic structure and explicit evidence anchors.
Generate a unified API surface reference document from upstream extraction artifacts. This step does NOT scan the repository directly — it synthesizes from pre-collected artifacts only.

## Inputs
- Required upstream artifacts (consume only, no repo scan):
  - `PYTHON_API_SURFACE.json`
  - `SERVICE_ENDPOINT_SURFACE.json`
  - `CLI_COMMAND_SURFACE.json`
- Optional synthesis helpers:
  - `REPO_MCP_SERVER_DEFS.json`
  - `SERVICE_CATALOG.json`
  - `EDITOR_INTEGRATION_SURFACE.json`
  - `HOOK_CONTRACT_SURFACE.json`
- Runner context artifacts:
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- Constraint:
  - Consume only precollected phase inputs. Do not scan source trees directly.

## Outputs
- `S10_API_SURFACE_REFERENCE.md`

## Schema
- Artifact kind: markdown output with structured reference tables.
- Canonical writer: `S10`
- Required output content contracts:
  - `S10_API_SURFACE_REFERENCE.md`
    - Section 1: **Python API Reference** — public modules and their exports from `PYTHON_API_SURFACE.json`, organized by package hierarchy
    - Section 2: **Service Endpoint Reference** — HTTP routes, MCP tools, eventbus topics from `SERVICE_ENDPOINT_SURFACE.json`, organized by service
    - Section 3: **CLI Command Reference** — command tree with arguments and descriptions from `CLI_COMMAND_SURFACE.json`
    - Section 4: **Cross-Reference Matrix** — table mapping CLI commands → Python APIs → service endpoints for integrated features
    - Each entry must cite the upstream artifact item ID
- Required citation shape:
  - `EVIDENCE: <artifact_filename>#<item_id>`

## Extraction Procedure
1. Load all required upstream artifacts as specified in the inputs section
2. **Python API Reference**: group items from `PYTHON_API_SURFACE.json` by package/module hierarchy; for each public symbol, include name, type, signature, and docstring summary
3. **Service Endpoint Reference**: group items from `SERVICE_ENDPOINT_SURFACE.json` by service_id; for each endpoint, include type, path/name, method, and handler
4. **CLI Command Reference**: build command tree from `CLI_COMMAND_SURFACE.json`; for each command, include name, arguments, description, and parent command
5. **Cross-Reference Matrix**: match items across the three surfaces by symbol name, handler function, or shared module path
6. For each entry, include the upstream artifact item ID for traceability
7. If a required artifact is missing, emit the section header with `⚠️ Source artifact not available`
8. Emit exactly the declared output and no additional files

## Evidence Rules
- Every reference entry must cite the specific item ID from its source artifact.
- Evidence anchors use the form: `EVIDENCE: <artifact_filename>#<item_id>`
- Cross-reference matrix entries must cite items from both/all surfaces being connected.
- Do not include entries that cannot be traced to upstream artifact items.

## Determinism Rules
- Do not include `generated_at`, `timestamp`, `created_at`, `updated_at`, or `run_id`.
- Use fixed heading order and fixed table row ordering by deterministic keys.
- Sort Python API entries by module path, then symbol name alphabetically.
- Sort service endpoints by service_id, then endpoint_path alphabetically.
- Sort CLI commands by command hierarchy depth, then name alphabetically.

## Anti-Fabrication Rules
- Do not invent API entries, endpoints, or CLI commands not present in upstream artifacts.
- Do not scan the repository directly — all information must come from declared inputs.
- Do not add usage examples or tutorial content; this is a factual reference only.
- If upstream data is incomplete, note gaps with `UNKNOWN` rather than inferring.

## Failure Modes
- Missing required upstream artifacts: emit the section header with `⚠️ Source artifact not available` and continue.
- Empty upstream artifacts: emit the section with `⚠️ Source artifact empty — no reference entries generated`.
- No cross-references found: emit the matrix section with a note that no matches were detected.
- Very large API surface (>500 items): include all items but collapse implementation details; note `[DETAIL_COLLAPSED]`.
