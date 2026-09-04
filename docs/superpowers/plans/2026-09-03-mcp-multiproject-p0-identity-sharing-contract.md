---
id: 2026-09-03-mcp-multiproject-p0-identity-sharing-contract
title: 2026 09 03 Mcp Multiproject P0 Identity Sharing Contract
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-09-03'
last_review: '2026-09-03'
next_review: '2026-12-02'
prelude: 2026 09 03 Mcp Multiproject P0 Identity Sharing Contract (explanation) for
  dopemux documentation and developer workflows.
---
# MCP Multi-Project P0 Identity + Sharing Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish and mechanically freeze the ratified R2 multi-project MCP identity/sharing contracts without changing live fleet behavior.

**Architecture:** P0 adds a parallel design-contract layer: strict v2 schemas, an ADR, exact R2 topology/falsification references, and negative architecture tests. Current v1 catalog, path-derived identity, lease allocator, launchers, services, and runner configuration remain byte-unmodified. P1 later implements the frozen contracts.

**Tech Stack:** Python 3.12+, JSON Schema Draft 2020-12, pytest, jsonschema, YAML/JSON reference artifacts, Git, pre-commit.

**Spec:** `docs/90-adr/adr-dmx-mcp-multiproject-identity-sharing-contract-001.md`, derived exactly from the frozen `04_CONTRACT_SPEC.md` in the P0 authoring package and the ratified R2 package SHA-256 `fa78556b2d51cd3b22d8c42ff36bd6c3964172ddee6a75662cde61db438e3996`.

## Global Constraints

- Risk lane is L2.
- Runtime effect is zero.
- G0 ratifies architecture only; P0 execution needs a separate operator gate.
- ConPort Wave 2 remains unauthorized.
- Canonical identity is registry-issued; path/CWD/env/port/container/session/clientInfo are evidence only.
- The only sharing classes are `HOST_SINGLETON`, `PROJECT_SCOPED`, `WORKTREE_SCOPED`, `RETIRED`.
- dope-memory V1 target is `PROJECT_SCOPED`; host-singleton is deferred.
- Serena V1 stays `WORKTREE_SCOPED`; host-singleton is deferred.
- P5 redis-events isolation precedes P4 dope-memory consolidation.
- Normal worktree switching may not rewrite shared global runner config.
- MCP protocol/session identity never substitutes for tenancy.
- Do not edit `mcp_catalog.yaml`, `src/dopemux/mcp/**`, `src/dopemux/commands/mcp_commands.py`, `services/**`, `docker/**`, compose, `.mcp.json`, lockfiles, or home/global runner config.
- Use an isolated worktree created via the required git-worktree skill at execution time.
- One implementer; one final independent L2 audit after substantive content freeze.
- Merge and activation remain operator-only.

---

### Task 1: Publish packet, ADR, immutable R2 references, and first red test

**Files:**
- Create: `task-packets/TP-DMX-MCP-MULTIPROJECT-P0-IDENTITY-SHARING-CONTRACT-001.json`
- Create: `task-packets/TP-DMX-MCP-MULTIPROJECT-P0-IDENTITY-SHARING-CONTRACT-001.md`
- Modify: `task-packets/INDEX.md`
- Create: `docs/90-adr/adr-dmx-mcp-multiproject-identity-sharing-contract-001.md`
- Create: `docs/03-reference/mcp/multiproject-service-topology.json`
- Create: `docs/03-reference/mcp/multiproject-falsification-contract.md`
- Create: `docs/superpowers/plans/2026-09-03-mcp-multiproject-p0-identity-sharing-contract.md`
- Create: `tests/arch/test_mcp_multiproject_contracts.py`

**Interfaces:**
- Consumes: frozen R2 package `fa78556b2d51cd3b22d8c42ff36bd6c3964172ddee6a75662cde61db438e3996` and G0 operator ratification.
- Produces: immutable repo-local P0 architecture spine that all later schema tasks reference.

- [ ] **Step 1: Create the isolated worktree and bind authority before edits**

Run:

```bash
git fetch origin main
git rev-parse origin/main
git status --short
git worktree list --porcelain
```

Expected: exact current main is recorded; worktree is isolated; no inherited edits are present. If current main moved, classify overlap rather than failing merely on SHA inequality.

- [ ] **Step 2: Write the first failing architecture test**

Create `tests/arch/test_mcp_multiproject_contracts.py`:

```python
from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
R2_TOPOLOGY_SHA256 = "df8636983e23c273eeb8eb517ea4019653b4c6bcb50cae344cde2e847214d4c2"
R2_FALSIFICATION_SHA256 = "84b6e68f929e5b3f3ad37e9c2843755cc38a3a119fc87b5af057505d8ed83bcb"

def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def test_ratified_r2_references_are_byte_exact():
    topology = REPO_ROOT / "docs/03-reference/mcp/multiproject-service-topology.json"
    falsification = REPO_ROOT / "docs/03-reference/mcp/multiproject-falsification-contract.md"
    assert _sha256(topology) == R2_TOPOLOGY_SHA256
    assert _sha256(falsification) == R2_FALSIFICATION_SHA256

def test_service_topology_has_exact_contract_shape():
    topology = json.loads(
        (REPO_ROOT / "docs/03-reference/mcp/multiproject-service-topology.json").read_text()
    )
    assert len(topology["services"]) == 26
    assert set(topology["sharing_classes"]) == {
        "HOST_SINGLETON",
        "PROJECT_SCOPED",
        "WORKTREE_SCOPED",
        "RETIRED",
    }
```

- [ ] **Step 3: Run the test to prove the references are absent**

Run:

```bash
uv run --extra test pytest -q tests/arch/test_mcp_multiproject_contracts.py
```

Expected: FAIL because the two frozen reference files do not yet exist.

- [ ] **Step 4: Copy immutable R2 references and publish packet/spec bytes**

Copy the exact frozen topology and falsification files from the P0 authoring package, not by manual retyping:

```bash
cp <P0_AUTHORING_PACKAGE>/sources/02_SERVICE_TOPOLOGY.json   docs/03-reference/mcp/multiproject-service-topology.json
cp <P0_AUTHORING_PACKAGE>/sources/04_FALSIFICATION_CONTRACT.md   docs/03-reference/mcp/multiproject-falsification-contract.md
```

Copy `01_TASK_PACKET.json`, `02_TASK_PACKET.md`, and this plan to their repo paths. Write the ADR from `04_CONTRACT_SPEC.md`, preserving all ten G0 binding conditions and the P0 no-runtime-effect boundary. Add one `Active` row for `TP-DMX-MCP-MULTIPROJECT-P0-IDENTITY-SHARING-CONTRACT-001` to `task-packets/INDEX.md`.

- [ ] **Step 5: Verify exact source hashes and Task Packet schema**

Run:

```bash
shasum -a 256 docs/03-reference/mcp/multiproject-service-topology.json
shasum -a 256 docs/03-reference/mcp/multiproject-falsification-contract.md
python -m jsonschema   -i task-packets/TP-DMX-MCP-MULTIPROJECT-P0-IDENTITY-SHARING-CONTRACT-001.json   docs/03-reference/spec/dopetask/dopetask-canonical-spec.json
```

Expected hashes:

```text
df8636983e23c273eeb8eb517ea4019653b4c6bcb50cae344cde2e847214d4c2  multiproject-service-topology.json
84b6e68f929e5b3f3ad37e9c2843755cc38a3a119fc87b5af057505d8ed83bcb  multiproject-falsification-contract.md
```

Task Packet validation expected: exit 0.

- [ ] **Step 6: Run the architecture test**

Run:

```bash
uv run --extra test pytest -q tests/arch/test_mcp_multiproject_contracts.py
```

Expected: PASS for the exact-reference tests.

- [ ] **Step 7: Commit the architecture spine**

```bash
git add   task-packets/TP-DMX-MCP-MULTIPROJECT-P0-IDENTITY-SHARING-CONTRACT-001.json   task-packets/TP-DMX-MCP-MULTIPROJECT-P0-IDENTITY-SHARING-CONTRACT-001.md   task-packets/INDEX.md   docs/90-adr/adr-dmx-mcp-multiproject-identity-sharing-contract-001.md   docs/03-reference/mcp/multiproject-service-topology.json   docs/03-reference/mcp/multiproject-falsification-contract.md   docs/superpowers/plans/2026-09-03-mcp-multiproject-p0-identity-sharing-contract.md   tests/arch/test_mcp_multiproject_contracts.py
git commit -m "docs(mcp): publish multiproject P0 contract spine"
```

---

### Task 2: Freeze resolved execution identity schema

**Files:**
- Create: `schemas/mcp/resolved-execution-identity.schema.json`
- Modify: `tests/arch/test_mcp_multiproject_contracts.py`

**Interfaces:**
- Consumes: ADR identity rules.
- Produces: JSON Schema contract `dopemux.mcp.resolved-execution-identity.v1`.

- [ ] **Step 1: Add failing positive and negative identity tests**

Append:

```python
import jsonschema

def _load_schema(name: str) -> dict:
    return json.loads((REPO_ROOT / "schemas/mcp" / name).read_text())

def _verified_identity() -> dict:
    return {
        "schema_version": "dopemux.mcp.resolved-execution-identity.v1",
        "resolution_status": "VERIFIED",
        "project_id": "project-registry-id",
        "workspace_id": "workspace-registry-id",
        "instance_id": "instance-registry-id",
        "actor_id": "operator",
        "client_id": "codex-cli",
        "registry_generation": 7,
        "mutable_routing_allowed": True,
        "aliases": [
            {
                "kind": "git_common_dir",
                "value": "/Users/example/repo/.git",
                "role": "EVIDENCE_ONLY",
            }
        ],
    }

def test_verified_identity_requires_registry_ids():
    schema = _load_schema("resolved-execution-identity.schema.json")
    jsonschema.validate(_verified_identity(), schema)

def test_unknown_identity_cannot_allow_mutation():
    schema = _load_schema("resolved-execution-identity.schema.json")
    bad = _verified_identity()
    bad["resolution_status"] = "UNKNOWN"
    bad["mutable_routing_allowed"] = True
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)

def test_alias_never_becomes_authority():
    schema = _load_schema("resolved-execution-identity.schema.json")
    bad = _verified_identity()
    bad["aliases"][0]["role"] = "AUTHORITY"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)
```

Also import `pytest`.

- [ ] **Step 2: Run the identity tests and verify failure**

```bash
uv run --extra test pytest -q tests/arch/test_mcp_multiproject_contracts.py -k identity
```

Expected: FAIL because the schema does not exist.

- [ ] **Step 3: Create the strict schema**

Create a Draft 2020-12 schema with:
- `additionalProperties: false`;
- exact schema version constant;
- `resolution_status` enum `VERIFIED|CONFLICTING|UNKNOWN`;
- nullable IDs in the base shape;
- `aliases[].role` constant `EVIDENCE_ONLY`;
- conditional `VERIFIED` branch requiring nonempty `project_id`, `workspace_id`, `instance_id`, `actor_id`, `client_id`, integer `registry_generation >= 0`;
- conditional non-VERIFIED branch requiring `mutable_routing_allowed: false`;
- optional SCM evidence fields such as `git_common_dir`, `worktree_path`, `origin`, `worktree_ref`, `branch_ref`, and 40-hex `commit_sha`, all under evidence objects rather than ID fields.

- [ ] **Step 4: Run identity tests**

```bash
uv run --extra test pytest -q tests/arch/test_mcp_multiproject_contracts.py -k identity
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add schemas/mcp/resolved-execution-identity.schema.json tests/arch/test_mcp_multiproject_contracts.py
git commit -m "feat(mcp): freeze resolved identity contract"
```

---

### Task 3: Freeze service topology and design-only fleet catalog v2 schema

**Files:**
- Create: `schemas/mcp/service-topology.schema.json`
- Create: `schemas/mcp/fleet-catalog-v2.schema.json`
- Modify: `tests/arch/test_mcp_multiproject_contracts.py`

**Interfaces:**
- Consumes: exact R2 service topology and current v1 catalog schema as syntax donor only.
- Produces: strict topology schema and a non-runtime v2 catalog schema.

- [ ] **Step 1: Add failing topology/catalog tests**

Add tests that:
- validate the exact R2 topology against `service-topology.schema.json`;
- assert 26 services and four sharing classes;
- validate a minimal v2 synthetic server;
- reject `scope`, `state_scope`, `port_policy`, and `multi_project_singleton`.

Example synthetic v2 server:

```python
def _v2_catalog() -> dict:
    return {
        "version": 2,
        "defaults": {"worktree": ["serena"]},
        "servers": {
            "serena": {
                "sharing_class": "WORKTREE_SCOPED",
                "target_class": "WORKTREE_SCOPED",
                "transport": "http",
                "plane": "code-intelligence",
                "authority_role": "code-intelligence",
                "lifecycle": "active",
                "management_model": "compose-service",
                "identity_scope": "per-instance",
                "state_authority": "derived",
                "mutation_class": "scoped",
                "endpoint_policy": "leased",
                "probe": "mcp",
                "idle_policy": "instance_idle",
                "flip_gate": ["concurrency-safe per-request workspace implementation"],
            }
        },
    }
```

- [ ] **Step 2: Run and prove schemas are absent**

```bash
uv run --extra test pytest -q tests/arch/test_mcp_multiproject_contracts.py -k "topology or catalog_v2"
```

Expected: FAIL.

- [ ] **Step 3: Create `service-topology.schema.json`**

Match the actual R2 topology JSON shape. Require every service row to carry:

```text
SERVICE_ID
CURRENT_CLASS
TARGET_CLASS
FLIP_GATE
CANONICAL_AUTHORITY
IDENTITY_SCOPE
STORAGE_SCOPE
PORT_POLICY
FAIL_CLOSED_RULE
```

Preserve any additional R2 fields explicitly present in the frozen source instead of using an open-ended schema.

- [ ] **Step 4: Create `fleet-catalog-v2.schema.json`**

Start from the current v1 schema **as a syntax donor**, then explicitly change the version and topology fields. Keep current runner/profile/tool syntax only where still applicable. Do not replace the live v1 schema in this packet.

The v2 server object must reject unknown properties and require:

```text
sharing_class
target_class
transport
plane
authority_role
lifecycle
management_model
identity_scope
state_authority
mutation_class
endpoint_policy
probe
idle_policy
flip_gate
```

- [ ] **Step 5: Run topology/catalog tests**

```bash
uv run --extra test pytest -q tests/arch/test_mcp_multiproject_contracts.py -k "topology or catalog_v2"
```

Expected: PASS.

- [ ] **Step 6: Prove live v1 files remain unchanged**

```bash
git diff --exit-code origin/main -- mcp_catalog.yaml schemas/mcp/fleet-catalog.schema.json src/dopemux/mcp/fleet_catalog.py
```

Expected: exit 0.

- [ ] **Step 7: Commit**

```bash
git add schemas/mcp/service-topology.schema.json schemas/mcp/fleet-catalog-v2.schema.json tests/arch/test_mcp_multiproject_contracts.py
git commit -m "feat(mcp): freeze sharing and catalog v2 contracts"
```

---

### Task 4: Freeze service lease and ownership evidence schemas

**Files:**
- Create: `schemas/mcp/service-lease-v2.schema.json`
- Create: `schemas/mcp/ownership-evidence.schema.json`
- Modify: `tests/arch/test_mcp_multiproject_contracts.py`

**Interfaces:**
- Consumes: identity schema and R2 ownership/lease rules.
- Produces: endpoint lease and mutation-eligibility contracts for P1.

- [ ] **Step 1: Write failing lease scope tests**

Create fixtures for:
- valid project-scoped lease with project_id;
- valid worktree-scoped lease with project_id+instance_id;
- invalid worktree lease missing instance_id;
- invalid RETIRED lease;
- stale lease mutation attempt.

- [ ] **Step 2: Write failing ownership tests**

Use:

```python
def _owned_evidence() -> dict:
    return {
        "schema_version": "dopemux.mcp.ownership-evidence.v1",
        "classification": "OWNED",
        "mutation_eligible": True,
        "registry": {"verified": True, "project_id": "p", "registry_generation": 3},
        "lease": {"verified": True, "lease_id": "lease-1"},
        "probe": {"verified": True, "service_family": "conport"},
        "storage": {"verified": True, "evidence": "project-bound mount"},
    }
```

Then remove each evidence block in separate parametrized tests and assert validation failure.

- [ ] **Step 3: Run and prove failure**

```bash
uv run --extra test pytest -q tests/arch/test_mcp_multiproject_contracts.py -k "lease or ownership"
```

Expected: FAIL.

- [ ] **Step 4: Create `service-lease-v2.schema.json`**

Use conditional schema branches for sharing class:
- host: no tenant requirement;
- project: nonempty project_id;
- worktree: nonempty project_id + instance_id;
- retired: rejected.

Status enum:

```text
active | stale | released | unknown | conflicting
```

No field names a path hash or port formula as authority.

- [ ] **Step 5: Create `ownership-evidence.schema.json`**

Require:
- `classification`;
- `mutation_eligible`;
- closed typed evidence blocks.

Conditional rules:
- `OWNED + mutation_eligible=true` requires all four evidence blocks verified;
- any non-OWNED classification forces `mutation_eligible=false`.

- [ ] **Step 6: Run tests**

```bash
uv run --extra test pytest -q tests/arch/test_mcp_multiproject_contracts.py -k "lease or ownership"
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add schemas/mcp/service-lease-v2.schema.json schemas/mcp/ownership-evidence.schema.json tests/arch/test_mcp_multiproject_contracts.py
git commit -m "feat(mcp): freeze lease and ownership contracts"
```

---

### Task 5: Freeze runner materialization receipt and project event envelope

**Files:**
- Create: `schemas/mcp/runner-materialization-receipt.schema.json`
- Create: `schemas/mcp/project-event-envelope.schema.json`
- Modify: `tests/arch/test_mcp_multiproject_contracts.py`

**Interfaces:**
- Consumes: P0 identity contract.
- Produces: non-authoritative receipt and transport-envelope contracts consumed later by P7 and P5.

- [ ] **Step 1: Add failing materialization tests**

Test valid strict receipt, then reject:
- `shared_global_config_mutated=true`;
- missing project/workspace/instance;
- strict mode with `inherited_surface_status=UNKNOWN`;
- `authority` other than `PROVENANCE_ONLY`.

- [ ] **Step 2: Add failing event tests**

Test valid explicit identity envelope, then reject:
- missing project_id/workspace_id/instance_id;
- missing registry_generation;
- malformed payload digest;
- empty stream namespace.

- [ ] **Step 3: Run and prove failure**

```bash
uv run --extra test pytest -q tests/arch/test_mcp_multiproject_contracts.py -k "materialization or event"
```

Expected: FAIL.

- [ ] **Step 4: Create the two schemas**

Use closed Draft 2020-12 objects.

Receipt digest patterns:

```json
{"type": "string", "pattern": "^[0-9a-f]{64}$"}
```

Receipt hard constants:

```text
authority=PROVENANCE_ONLY
shared_global_config_mutated=false
```

Event identity fields are required nonempty strings and carry no defaults.

- [ ] **Step 5: Run tests**

```bash
uv run --extra test pytest -q tests/arch/test_mcp_multiproject_contracts.py -k "materialization or event"
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add schemas/mcp/runner-materialization-receipt.schema.json schemas/mcp/project-event-envelope.schema.json tests/arch/test_mcp_multiproject_contracts.py
git commit -m "feat(mcp): freeze runner and event contracts"
```

---

### Task 6: Add cross-contract authority and no-runtime-effect gates

**Files:**
- Modify: `tests/arch/test_mcp_multiproject_contracts.py`
- Modify only if wording alignment is required: `docs/90-adr/adr-dmx-mcp-multiproject-identity-sharing-contract-001.md`

**Interfaces:**
- Consumes: every P0 schema/reference.
- Produces: final static P0 anti-widening gate.

- [ ] **Step 1: Add ratified service-target assertions**

Parse the exact topology and assert by `SERVICE_ID` that:
- ConPort target = project scoped and not eligible now;
- dope-memory V1 target = project scoped and host option deferred;
- Serena V1 target = worktree scoped;
- redis-events target = project scoped;
- no Task Orchestrator row authorizes `multi_project_singleton`.

Use the exact field names found in the frozen topology JSON instead of inventing aliases.

- [ ] **Step 2: Add P5-before-P4 DAG assertion**

Read the repo-local ADR/plan decision and assert the dependency sentence/structured reference records `P5 -> P4`. Do not parse a diagram with a brittle regex when a structured field can be asserted.

- [ ] **Step 3: Add forbidden-current-file diff gate**

Create a test helper that runs:

```python
FORBIDDEN_P0_PATHS = (
    "mcp_catalog.yaml",
    "src/dopemux/mcp/",
    "src/dopemux/commands/mcp_commands.py",
    "services/",
    "docker/",
    ".mcp.json",
)
```

The test uses `git diff --name-only <base>...HEAD` only when the base is explicitly injected by the validation harness. If no trusted base is supplied, mark the test `UNKNOWN`/skip and enforce the same rule in the deterministic pre-push command rather than guessing.

- [ ] **Step 4: Run full focused P0 tests**

```bash
uv run --extra test pytest -q tests/arch/test_mcp_multiproject_contracts.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/arch/test_mcp_multiproject_contracts.py docs/90-adr/adr-dmx-mcp-multiproject-identity-sharing-contract-001.md
git commit -m "test(mcp): enforce P0 authority boundaries"
```

---

### Task 7: Pre-push gate, freeze, audit, proof-only closure, PR finality

**Files:**
- Create/update only the exact proof paths in the packet allowlist after content freeze.

**Interfaces:**
- Consumes: complete substantive P0 content.
- Produces: exact-head implementation proof and independent L2 audit result.

- [ ] **Step 1: Reharvest main and exact changed-file allowlist**

Run:

```bash
git fetch origin main
git diff --name-only origin/main...HEAD | sort
```

Then compare exactly against the packet allowlist, excluding proof-only paths not yet created. Any substantive path outside the allowlist is a blocker.

- [ ] **Step 2: Run Task Packet validation**

```bash
python -m jsonschema   -i task-packets/TP-DMX-MCP-MULTIPROJECT-P0-IDENTITY-SHARING-CONTRACT-001.json   docs/03-reference/spec/dopetask/dopetask-canonical-spec.json
```

Expected: exit 0.

- [ ] **Step 3: Run focused and relevant complete tests**

```bash
uv run --extra test pytest -q   tests/arch/test_mcp_multiproject_contracts.py   tests/arch/test_mcp_fleet_catalog_contract.py   tests/unit/test_mcp_runtime_registry.py
```

Expected: exit 0. A repository-wide unrelated failure may be classified only with reproducible baseline evidence; never turn a nonzero gate into PASS by prose.

- [ ] **Step 4: Run diff/pre-commit/secret gates**

```bash
git diff --check
pre-commit run --files $(git diff --name-only origin/main...HEAD)
```

Run the current repository-approved secret scan for the exact changed range. If the repository command has changed since this plan was authored, reharvest the current documented/pre-push command rather than inventing a substitute.

- [ ] **Step 5: Freeze substantive content**

Record:

```bash
git rev-parse HEAD
git rev-parse HEAD^{tree}
git diff --name-status origin/main...HEAD
```

After this point, no substantive P0 file changes until the final audit result is known.

- [ ] **Step 6: Run one independent final L2 audit**

Live-discover an auditor independent of the implementer. Preferred routing follows repository policy; exact runner/model is recorded as `UNKNOWN` until preflight proves it. The audit subject is the frozen content head and exact changed-file set.

Mandatory challenge set:
- path/env/clientInfo/session authority creep;
- mutable routing under UNKNOWN/CONFLICTING identity;
- fifth sharing class or `multi_project_singleton`;
- lease/ownership laundering;
- global runner-config rewrite allowance;
- ConPort Wave 2 leakage;
- dope-memory/Serena target drift;
- service topology/falsification hash drift;
- accidental runtime effect.

Accepted verdicts: `PASS` or `PASS_WITH_RISKS` only when every risk is explicit and nonblocking. `FAIL`, `NEEDS_SUPERVISOR`, stale audit, unknown identity, or head mismatch blocks readiness.

- [ ] **Step 7: Apply at most one bounded substantive repair if required**

Only if the finding is inside the existing P0 contract and exact allowlist. After repair, make a new content commit, rerun all gates, freeze the new content head, and run one fresh independent final audit. Do not audit intermediate repair commits.

- [ ] **Step 8: Create proof-only successor artifacts**

Populate only the fixed proof paths in the packet allowlist. Capture validation commands with the repo's current proof tooling, for example:

```bash
scripts/proof_bundle.sh --tp TP-DMX-MCP-MULTIPROJECT-P0-IDENTITY-SHARING-CONTRACT-001 --cmd   "uv run --extra test pytest -q tests/arch/test_mcp_multiproject_contracts.py"
```

Validate proof with the current canonical proof validator. If the validator path/CLI differs at execution time, use the current repo-tracked contract, not an invented command.

- [ ] **Step 9: Verify proof-only closure**

Prove the proof head descends from the audited content head and changes only allowed proof paths. A proof-only successor does not require re-auditing unchanged substantive content when schema, signature/identity, ancestry, and path closure pass.

- [ ] **Step 10: Run PR Steward exact-head finality**

Do not mark ready or merge automatically. Final output is an operator merge decision packet/state.

- [ ] **Step 11: Stop**

Return the packet's required return block. `P1`, `PX`, Wave 2, runtime migration, merge, and activation remain separately gated.
