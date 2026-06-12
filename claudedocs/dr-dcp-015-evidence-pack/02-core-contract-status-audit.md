# DCP Five Core-Contract Status Audit

| | |
|---|---|
| **Date** | 2026-06-11 |
| **Author** | Claude (Opus 4.8) synthesis over 3 read-only sub-audits (Sonnet×2, Haiku×1) |
| **Type** | Read-only audit (no source changes) |
| **Purpose** | Evaluate the `BUILD_AFTER_CORE_CONTRACTS` gate from DR-DCP-015 — are the 5 prerequisite contracts locked? |
| **Branch** | `claude/intelligent-banach-8426ff` (worktree) |

## Headline

**All 5 core contracts are at `.v0` / PROVISIONAL. None are "locked." The `BUILD_AFTER_CORE_CONTRACTS` gate is real and currently CLOSED.**

The DCP schema directory enforces its own rule (`schemas/dcp/README.md`): *"No schema in this directory should be treated as the authoritative source for runtime enforcement until upgraded past `.v0` by a subsequent task packet."* Every one of the 5 contract schemas is still `.v0`, so by the repo's own definition none is authoritative yet.

A second, cross-cutting problem: **schema↔runtime decoupling.** Where enforcement exists at all, it does *not* read the contract schema — it runs a parallel hand-coded implementation. Promoting a schema past `.v0` will therefore not, by itself, make it enforced.

## Status table

| # | Contract | Schema | Schema state | Runtime enforcement | Tests | Verdict |
|---|---|---|---|---|---|---|
| 1 | **Red-lane taxonomy** | `schemas/dcp/dcp_red_lane_taxonomy.schema.json` | `.v0` (self-marked "unstable, not authority") | **Yes, but decoupled** — `RedLaneScanner` in `src/dopemux/dcp/red_lane_scanner.py` enforces equivalent lanes via hardcoded `red_lane_rules.py`; the JSON taxonomy is **not loaded** | 18 scanner + 18 contract tests | **PARTIAL** |
| 2 | **Receipt schema** | `schemas/dcp/dcp_helper_receipt.schema.json` | `.v0`, `EXTERNAL_PROPOSED`, `PROVISIONAL_UNVERIFIED_ENFORCEMENT`; schema desc admits *"no repo-runtime helper-receipt artifact exists"* | **None** — no producer/validator in `src/`. (Note: schema lacks `signer`/`signature`/`verdict` fields the receipt spec calls for) | structural only (`test_dcp_contracts.py`, 8 fns) | **PARTIAL (weakest — stub)** |
| 3 | **Mutation classes** | `schemas/dcp/dcp_mutation_class.schema.json` | `.v0`, fixture `contract_status: PROVISIONAL`; tier vocab `REPO_CROSS_CHECKED` vs `approval_policy.yaml`/`policy.py` | **None** — no code loads/applies it | 17 contract-derivation tests (schema/fixture validation only) | **PARTIAL** |
| 4 | **Approval artifact** | `schemas/dcp/dcp_approval_artifact.schema.json` | `.v0`, envelope `SYNTHESIS_INVENTED`, `PROVISIONAL_UNVERIFIED_ENFORCEMENT`; *"supervisor identity resolution is PROVISIONAL — not proven wired"* | **None** — orchestrator `approval_id` on `TransitionReceipt` is an unrelated pattern, not an instance of this schema | 17 tests incl. `requester != approver` invariant (`test_14`) | **PARTIAL** |
| 5 | **Project path+resource maps** | `schemas/dcp/dcp_project_resource_map.schema.json` | `.v0`, `PROVISIONAL_UNVERIFIED_ENFORCEMENT`, provenance `REPO_VALIDATED` | **Yes, via a real pre-existing analog** — `config/repo_hygiene/root_hygiene_policy.json` (v1, blocked patterns) + `policy.py` canonical-writers + `scripts/verify_runtime_authority.py` (forbidden_authority_paths). The DCP schema itself is still provisional and is *not* the enforced artifact | `test_dcp_0002_contract_derivation.py` asserts 12–16 + fixtures | **PARTIAL (strongest)** |

> **Correction logged:** the Haiku sub-audit graded Contract 5 `LOCKED`. Downgraded to `PARTIAL (strongest)` on review: its own evidence shows the DCP schema is `.v0 / PROVISIONAL_UNVERIFIED_ENFORCEMENT`, and what's enforced at runtime is a *separate* repo-hygiene/policy analog, not the DCP contract. Per the repo's own `.v0`-not-authoritative rule, it cannot be "locked." It is, however, the only contract with a genuine runtime enforcement substrate.

## What "PARTIAL across the board" means

- **The schemas are real and tested** — but tested for *structural* correctness (round-trip, provenance tags, invariants), not for runtime production/consumption. They are contract **stubs** that establish provenance and shape conventions, deliberately marked non-authoritative.
- **The enforcement that exists is not driven by the contracts.** Contract 1's scanner is hardcoded; Contract 5's enforcement is the older repo-hygiene/policy layer. Contracts 2/3/4 have no enforcement at all.
- **Therefore the gate is closed.** DR-DCP-015 says "lock the 5 contracts FIRST." They are not locked. Building the broader tooling layer (plugin package, `dopemux dcp` CLI, the full §7 helper suite) now would violate the ingested directive and risk the "vibe plane, not a red-lane gate" failure mode the synthesis warns against.

## Promotion path (per contract, smallest correct next step)

| Contract | To reach "locked" (`.v0` → stable + enforced) |
|---|---|
| 1. Red-lane taxonomy | Make `RedLaneScanner` **load** the taxonomy schema instead of hardcoded `red_lane_rules.py` (couple schema→runtime), then promote past `.v0`. Highest-value fix — it already has enforcement + tests. |
| 5. Path+resource maps | Reconcile `dcp_project_resource_map` schema with the live `root_hygiene_policy.json` + `policy.py`; make one the canonical writer of the other; promote. Closest to done. |
| 3. Mutation classes | Wire a classifier that maps a write/tool-call to a mutation class at runtime (PreToolUse), consuming the schema. Currently declarative only. |
| 4. Approval artifact | Resolve supervisor-identity wiring (`supervisor_accepted` is unplumbed per DX-overhaul Phase-1 finding); produce/validate a real instance at an approval gate. |
| 2. Receipt schema | Add `signer`/`signature`/`verdict` fields; make at least one helper (e.g. `/proof:bundle` from PR #858) emit a conforming instance. Currently a pure stub. |

## Evidence & confidence

| Claim | Confidence | Basis |
|---|---|---|
| All 5 schemas exist at `.v0` | **high** | sub-audit reads of `schemas/dcp/*.schema.json` + Haiku schema inventory |
| None is authoritative per repo rule | **high** | `schemas/dcp/README.md` quoted by sub-audits |
| Contracts 2/3/4 have zero runtime enforcement | **high** | grep of `src/` returned no producer/validator (sub-audits) |
| Contract 1 enforcement is decoupled (hardcoded, not schema-loaded) | **high** | `red_lane_scanner.py` + `red_lane_rules.py` read directly by sub-audit |
| Contract 5 has a real enforcement analog (repo_hygiene/policy.py) | **high** | sub-audit read of `root_hygiene_policy.json`, `policy.py`, `verify_runtime_authority.py` |
| Contract 5 ≠ LOCKED | **high** | corrected on review of the sub-audit's own `.v0/PROVISIONAL` evidence |
| Exact test counts | **medium** | relayed from sub-audits; not independently re-counted |

**Remaining uncertainty:** test counts and a few fixture details are relayed, not re-verified by me. PR #858's shipped guards (e.g. `/proof:bundle`, `dcp_surface_guard`) may already partially satisfy Contracts 1/2 in ways this static-schema audit did not cross-check against that PR's branch.
