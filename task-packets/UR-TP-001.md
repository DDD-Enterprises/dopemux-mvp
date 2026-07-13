---
id: UR-TP-001
title: Universal Router Strict Contracts and Typed Governance References
type: explanation
owner: '@hu3mann'
author: 'GPT-5.6 Pro'
date: '2026-07-13'
last_review: '2026-07-13'
next_review: '2026-10-11'
prelude: Binding first implementation packet for strict Universal Router contracts without CLI, state, or execution.
---
# Task Packet: UR-TP-001

## Packet identity

| Field | Value |
|---|---|
| Packet | `UR-TP-001` |
| Series | `UR-ROUTER-IMPL-001` |
| Dependency | `TP-DMX-UR-ARTIFACT-INTAKE-001` merged |
| Base | Fresh `origin/main` locked after dependency merge |
| Branch | `codex/ur-tp-001-contracts` |
| Risk | Medium, authority/schema-sensitive |
| Status | `READY_AFTER_DEPENDENCY_AND_BASE_LOCK` |

## Objective

Define all 26 Universal Router contracts as immutable, side-effect-free Pydantic v2 records with strict checked-in JSON Schemas, fixtures, and contract tests. Preserve every external subsystem's authority through typed references only. Enable no CLI, journal, policy activation, provider access, runner access, handoff, workflow transition, or execution.

## Current-runtime corrections to the architecture macro-packet

- `pyproject.toml` is allowlisted because the repository uses an explicit setuptools package list. Without adding `dopemux.universal_router`, the wheel silently omits the package.
- `contracts/openclaw-dcp-routing/` already owns canonical OpenClaw/DCP machine contracts. This packet references that tree and must not create a second mutable DCP policy/schema surface.
- The current PR Steward surface is `python -m dopemux.cli pr-steward`; no substitute is permitted.

## Scope IN

- `src/dopemux/universal_router/{__init__,models}.py`.
- Strict JSON Schema 2020-12 artifacts and schema manifest.
- Valid, invalid, `UNKNOWN`, and `CONFLICTING` fixtures.
- Focused model/schema/authority-boundary tests.
- One minimal package registration in `pyproject.toml`.
- Proof, embedded audit, and PR Steward evidence.

## Scope OUT

- CLI registration or commands.
- SQLite, journal, filesystem writes, environment reads, subprocesses, network, provider, or runner calls.
- Candidate ranking or executable policy evaluation.
- Active-policy files or policy promotion.
- Mutation of DCP, Freeflow, LiteLLM, RTE, Task Orchestrator, dopetask, proof, handoff, audit, approval, or PR Steward state.
- Any new dependency or non-allowlisted file.

## Required public contract inventory

- `TaskEnvelope`
- `DCPClassificationRef`
- `RiskPrivacyClassification`
- `RunnerCapabilitySnapshot`
- `ProviderHealthSnapshot`
- `ModelCapabilityRecord`
- `RoutePolicy`
- `RouteCandidate`
- `UniversalRouteDecision`
- `SubsystemDecisionRef`
- `ExecutionRecommendation`
- `ExecutionRequest`
- `RunnerResult`
- `ModelIdentityObservation`
- `UsageObservation`
- `ContainmentDeclaration`
- `NetworkPosture`
- `ValidationResult`
- `EscalationDecision`
- `AuditAssignment`
- `AuditResultRef`
- `HumanApprovalRef`
- `BenchmarkCertification`
- `ProofBundleRef`
- `DopetaskHandoffRef`
- `PRStewardReadinessRef`

Private helper enums/value objects are allowed but are not additional public contracts.

## Binding contract rules

1. Pydantic v2 only; `frozen=True`, `extra='forbid'`, defaults validated, and authority identifiers/statuses/hashes use strict constrained types.
2. Contract-set version is `1.0.0`; timestamps must be timezone-aware; SHA-256 values are lowercase 64-hex strings; monetary values use decimal strings/`Decimal`, never binary floats.
3. Authority-bearing schemas set `additionalProperties: false`.
4. `UNKNOWN` and `CONFLICTING` are explicit states and cannot be converted to PASS, READY, selected, attested, approved, or certified.
5. `ExecutionRecommendation` is not `ExecutionRequest`; `UniversalRouteDecision` is not authorization; `RunnerResult.SUCCEEDED` is not validation or audit pass.
6. `ProofBundleRef`, `DopetaskHandoffRef`, `AuditResultRef`, `HumanApprovalRef`, `DCPClassificationRef`, and `PRStewardReadinessRef` contain identifiers, versions, artifact refs/hashes, freshness, and owner metadata only. Embedded foreign bodies are rejected.
7. Model identity keeps requested, configured, response-claimed, proxy-reported, provider-attested, and attested-actual values separate. A provider request ID alone cannot attest a model.
8. Usage keeps visible input, effective input, cache, output, reasoning, runner overhead, plan credits, actual API cost, estimated cost, source, confidence, pricing version, scope, and exactness separate.
9. Containment controls record `requested_value`, `effective_value`, enforcement source, evidence ref, and confidence. `PROMPT_REQUESTED` cannot satisfy an enforced-control requirement.
10. `BenchmarkCertification` includes the audit repair tuple: task class, identity confidence, containment profile, and network posture in addition to policy, adapter, runner, provider path, configured model, and reasoning.
11. `RoutePolicy.policy_domain` is the constant `UNIVERSAL_ORCHESTRATION`; its `$id`, schema namespace, and body remain distinct from `contracts/openclaw-dcp-routing/`.
12. Importing `dopemux.universal_router` performs no I/O and reads no time, environment, files, network, subprocess, Git, provider, runner, or service state.

## Existing authority references

Read and reference these tracked paths at the locked implementation commit:

```text
PROJECT.md
ARCHITECTURE.md
SERVICE_CATALOG.md
PM_PLANE.md
AGENTS.md
docs/03-reference/governance/rules.md
docs/03-reference/systems/system-boundaries.md
docs/governance/proof-contract.md
docs/governance/proof-bundle-schema.md
docs/03-reference/governance/handoff-contract.md
docs/02-how-to/integrations/dopetask/adapter-contract.md
docs/02-how-to/integrations/dopetask/adapter-schema.md
docs/03-reference/spec/dopetask/dopetask-canonical-spec.json
docs/ops/embedded-audit.md
docs/ops/pr-steward-cli.md
tools/pr_steward/classifier.py
contracts/openclaw-dcp-routing/
docs/03-reference/dcp/openclaw-routing/README.md
src/dopemux/dcp/routing_model.py
src/dopemux/dcp/routing_classifier.py
```

Treat imported `TRUTH_*` copies as research-tier context only.

## Allowed files

```text
pyproject.toml
src/dopemux/universal_router/__init__.py
src/dopemux/universal_router/models.py
schemas/universal-router/contracts.schema.json
schemas/universal-router/route-policy.schema.json
schemas/universal-router/schema-manifest.json
tests/universal_router/test_models.py
tests/universal_router/fixtures/contracts/**
proof/UR-TP-001/**
```

## Mechanical slices

### Slice 1: baseline and collision check

Lock a clean dedicated worktree to current `origin/main` after the intake packet merges. Verify the package/schema/test roots are absent or intentionally empty. Inspect current DCP, proof, handoff, audit, task-packet, and PR Steward contracts. Stop on any ownership or path collision.

### Slice 2: pure contract models

Implement exactly the 26 public models plus private support types. Add only the `dopemux.universal_router` package entry to `pyproject.toml`. Validate imports are side-effect-free.

### Slice 3: strict checked-in schemas

Generate/check in `contracts.schema.json`, a standalone `route-policy.schema.json`, and `schema-manifest.json`. Manifest entries include contract name, schema pointer, schema version, and content hash. Generated and checked-in schema structures must match after deterministic normalization.

### Slice 4: adversarial fixture corpus

For every contract, add one minimal valid fixture. Add invalid fixtures for missing required fields, extra fields, bad enums, malformed hashes/timestamps, body embedding, semantic authority elevation, and cross-contract confusion. Add explicit `UNKNOWN` and `CONFLICTING` fixtures wherever permitted.

### Slice 5: validation, packaging, and proof

Run all packet verification commands; build a wheel and prove the package is present; capture status, full diff, diff stat, outputs, exit codes, inventories, and review bundle.

### Slice 6: independent audit and PR Steward

Open/update the PR only after local gates pass. Require current trusted embedded-audit proof and PR Steward `READY` at the latest head.

## Exact validation commands

```bash
uv run --frozen dopemux orchestrator packet validate task-packets/UR-TP-001.json
uv run --frozen python -m jsonschema \
  -i task-packets/UR-TP-001.json \
  docs/03-reference/spec/dopetask/dopetask-canonical-spec.json
uv run --frozen python -m json.tool schemas/universal-router/contracts.schema.json >/dev/null
uv run --frozen python -m json.tool schemas/universal-router/route-policy.schema.json >/dev/null
uv run --frozen python -m json.tool schemas/universal-router/schema-manifest.json >/dev/null
uv run --frozen pytest -q tests/universal_router/test_models.py
uv run --frozen pytest -q tests/universal_router -k 'contract or model'
uv run --frozen pytest -q tests/contracts/test_openclaw_dcp_routing_contracts.py
uv run --frozen python -m compileall -q src/dopemux/universal_router
uv build --wheel --out-dir proof/UR-TP-001/dist
uv run --frozen python -c "import glob,zipfile; p=glob.glob('proof/UR-TP-001/dist/*.whl'); assert len(p)==1,p; names=set(zipfile.ZipFile(p[0]).namelist()); assert {'dopemux/universal_router/__init__.py','dopemux/universal_router/models.py'} <= names"
git diff --check
git diff --stat
git diff --no-ext-diff
uv run --frozen pre-commit run --files \
  pyproject.toml \
  src/dopemux/universal_router/__init__.py \
  src/dopemux/universal_router/models.py \
  schemas/universal-router/contracts.schema.json \
  schemas/universal-router/route-policy.schema.json \
  schemas/universal-router/schema-manifest.json \
  tests/universal_router/test_models.py \
  $(find tests/universal_router/fixtures/contracts -type f -print | sort)
```

## Acceptance criteria

1. Exactly 26 public contract names are exported and listed once in the manifest.
2. Every required field has an exact type, cardinality, required/optional rule, and closed enum where applicable.
3. All valid fixtures pass both Pydantic and JSON Schema validation.
4. Every invalid fixture fails at the expected path with the expected error class.
5. `UNKNOWN` and `CONFLICTING` preserve uncertainty/conflict without authority elevation.
6. All six external authority refs reject embedded foreign bodies.
7. DCP/OpenClaw canonical contracts remain unchanged and their focused regression suite passes.
8. No runtime side effect, CLI, persistence, policy activation, adapter, provider/runner call, workflow mutation, handoff, or execution path exists.
9. `pyproject.toml` changes only enough to package `dopemux.universal_router`.
10. The built wheel contains both module files.
11. Embedded audit is `PASS` or non-blocking `PASS_WITH_RISKS` and current to head.
12. PR Steward reports `READY` with all review items, bots, threads, checks, proof, and head SHA current.

## Proof minimums

- Git root, origin, branch, worktree, base/head SHA, status before/after.
- Contract, enum, schema, fixture, and wheel inventories.
- Full command log with outputs and exit codes.
- Diff stat and full diff.
- Generated-versus-checked-in schema comparison.
- Authority-reference boundary test results.
- Embedded-audit proof/report.
- PR Steward artifact set and `MERGE_READINESS.json`.

## Rollback

Revert the packet commit. No migration or state exists. Preserve proof according to retention policy.

## Stop conditions

- Intake dependency has not merged.
- `origin/main` advances after the implementation base is locked without packet refresh.
- Wrong repo/worktree/branch or dirty baseline.
- Existing files conflict with the greenfield package/schema/test paths.
- A new dependency or non-allowlisted file is required.
- A required contract cannot remain distinct.
- An existing DCP/proof/handoff/audit/approval/PR Steward body would need to be copied or forked.
- Any required validation, packaging check, embedded audit, or PR Steward gate fails or is unavailable.
