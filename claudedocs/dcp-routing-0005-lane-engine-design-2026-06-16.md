# DMX-DCP-MODEL-ROUTING-MVP-0005 — Lane Engine (design spec, execution-ready)

**Date:** 2026-06-16 · **Author:** Opus (design) · **Status:** ⛔ SUPERSEDED as the lane-engine spec
**Scope:** the 6 lane-concept cases deferred from 0002R.

> **SUPERSEDED 2026-06-16 (reconciliation verdict).** The canonical **0005 lane engine** is the
> runway-session packet `task-packets/DMX-DCP-MODEL-ROUTING-MVP-0005.md` — a pure `decide_lane(decision,
> input) -> LaneDecision` consumer of `RouteDecision`, sibling to `routing_backend_policy.py`, with
> **no new classifier fields**. It is build-ready, runtime-grounded, lower-blast-radius, and fits the
> existing module pattern (verified: `routing_backend_policy.select_backend_policy()` is the exact
> precedent — a pure `RouteDecision` consumer).
>
> This document's substance — **5 new `RoutingClassificationInput` fields + derive rules** for
> bridge-proxy / retrieval-derived / ECC-intake / OpenCode-Grok-wrapper-proof — is **NOT a lane engine**;
> it is *classifier safety-hardening* for execution surfaces that do not exist yet. The classifier
> **already fails closed** on those cases via conservative defaults (`authority_class=UNKNOWN`,
> `has_unknown_authority=True` → status UNKNOWN → not runnable), so adding the fields is
> hardening/explicitness, not a safety-hole fix. **Defer** to a future, renumbered MODEL-ROUTING packet
> (do NOT reuse 0005), gated on the connector/runner/ECC surfaces actually being built. Retained only as
> the salvage source for that future packet.
>
> **PAL consensus (2026-06-16, gpt-5.5-pro + gemini-2.5-pro) sharpened this:** the classifier
> provenance-hardening here is **NOT optional-defer — it is a BLOCKING PREREQUISITE** before any
> execution surface (connector/runner/live-write/ECC/backend) is wired to `is_executable`. (Latent now
> because `is_executable` is inert; active the moment an executor lands.) Canonical 0005 lane-engine
> packet committed to main via **PR #907**.

> **Numbering note:** the gate called this "0003 Lane Engine," but `0003` is the
> already-shipped **Routing Backend Policy Map** (PR #895) and `0004` is the
> read-only classify CLI (PR #901). This is a NEW packet → **0005**.

## Build gate (operator-set)

Do **NOT** start implementation until BOTH have merged to `main`:
1. PR #902 (`feat/dcp-routing-0002R-reconciliation`) — 0002R tests.
2. The precedence fix (`dcp/model-routing-0003-status-precedence`, task_c360358c).

Both edit/append to `routing_classifier.py` + `test_routing_classifier.py`; building
the lane engine before they land risks a 3-way conflict. Build on **clean `main`**.

## Decisions baked in

- **Case 6 (secure-MCP-readonly): NO classifier softening.** The current hard
  `requires_mcp_call → RED_LANE` (routing_classifier.py:184–186) STAYS. Secure
  read-only MCP is enforced at the **facade ACL layer**, not the classifier. The
  test asserts the RED_LANE block remains and documents the layer boundary. → no new field.
- **Deterministic-first preserved**; no model-assisted logic.
- **Fail-closed**: every new lane defaults conservative (block/UNKNOWN).

## New fields on `RoutingClassificationInput` (4)

| Field | Default | Lane |
|-------|---------|------|
| `authority_via_bridge_proxy: bool` | `False` | 2 |
| `evidence_is_retrieval_derived: bool` | `False` | 3 |
| `exact_source_fetched: bool` | `False` | 3 |
| `is_ecc_external_intake: bool` | `False` | 7 |
| `has_backend_wrapper_proof: bool` | `False` | 11/12 |

(5 fields; case 6 needs none.)

## Deterministic rules (in `_derive_*`)

| # | Rule | Effect |
|---|------|--------|
| 2 | `authority_via_bridge_proxy=True` → coerce effective `authority_class` to `UNKNOWN` | non-runnable for mutation; bridge/proxy/adapter/shim/mirror output never becomes authority |
| 3 | `evidence_is_retrieval_derived=True and not exact_source_fetched` → evidence is derived → cannot raise authority/confidence; mutation blocked | retrieval output is advisory until exact source fetched |
| 6 | `requires_mcp_call=True` → `RED_LANE` (UNCHANGED) | documenting test only |
| 7 | `is_ecc_external_intake=True` → only `TaskType.READ_ONLY`/static allowed; any `requires_runner_execution`/`requires_live_write`/`touches_destructive_path`/copy/import → `BLOCKED` | ECC archive is untrusted; static-only |
| 11 | `backend_kind==OPENCODE and not has_backend_wrapper_proof` → block mutation | OpenCode backend-only until wrapper proof |
| 12 | `backend_kind==GROK and not has_backend_wrapper_proof` → block mutation | Grok backend-only until wrapper proof |

## Required tests (tests/unit/dcp/test_routing_classifier.py)

`test_bridge_proxy_not_authority`, `test_retrieval_output_is_derived`,
`test_secure_mcp_readonly_only` (asserts RED_LANE stays + documents ACL-layer boundary),
`test_ecc_external_intake_static_only`, `test_opencode_backend_requires_wrapper_proof`,
`test_grok_backend_requires_wrapper_proof`.
Plus negative tests: each new field defaulting `False` must NOT change existing classifications (no regression to the 191 baseline).

## Allowlist

```
src/dopemux/dcp/routing_model.py          # if any new enum value needed (likely none)
src/dopemux/dcp/routing_classifier.py     # +4 fields, +derive rules
tests/unit/dcp/test_routing_classifier.py # +6 tests + regression guards
tests/fixtures/dcp/routing_corpus/*       # optional fixtures per lane
task-packets/DMX-DCP-MODEL-ROUTING-MVP-0005.md
```

## Scope OUT

No MCP softening · no runner/connector/backend invocation · no wrapper-proof
*verification* logic (only the presence flag gates) · no live writes · no CI edits.

## Invariants (carry from 0002/0003)

Runtime truth > docs · deterministic-first · model-assisted cannot override
red-lane/UNKNOWN · UNKNOWN authority blocks mutation · bridge/proxy/retrieval
never become authority · OpenCode/Grok backend-only · no live writes.
