---
id: DMX-DCP-MODEL-ROUTING-MVP-0006
title: DCP Classifier Provenance Hardening
type: how-to
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-16'
last_review: '2026-06-16'
next_review: '2026-09-14'
prelude: Hardens the DCP routing classifier against provenance laundering. Adds explicit provenance signals (bridge/proxy authority, retrieval-derived evidence, ECC external intake, unproven backend) that can only LOWER trust, never raise it, and override a claimed-but-laundered authority_class. BLOCKING prerequisite before any DCP execution surface is wired to is_executable; does NOT gate the execution-inert 0005 lane-engine MVP.
---

# DMX-DCP-MODEL-ROUTING-MVP-0006 — DCP Classifier Provenance Hardening

**Series**: DMX-DCP-MODEL-ROUTING-MVP
**Packet**: 0006 (implementation)
**Status**: DESIGN — **BLOCKING PREREQUISITE** for execution surfaces. Does NOT gate the 0005 lane-engine MVP (it is execution-inert).
**Depends on**: 0005 lane-engine packet ([PR #907](https://github.com/DDD-Enterprises/dopemux-mvp/pull/907)) on `main`; precedence fix #904 on `main` (already merged, `ba36b58cb`).
**Origin**: salvaged from `claudedocs/dcp-routing-0005-lane-engine-design-2026-06-16.md` (superseded as a lane-engine spec). Reframed by PAL consensus (gpt-5.5-pro `against` + gemini-2.5-pro `neutral`, 2026-06-16) as classifier hardening — NOT a lane engine.

---

## Why this exists (the vulnerability)

The classifier currently trusts caller-supplied `authority_class` / `has_unknown_authority`. A caller can **launder** risky provenance: set `authority_class=AUTOMATED_SAFE`, `has_unknown_authority=False` for a task whose TRUE source is a bridge/proxy, retrieval-derived evidence, ECC external intake, or an unproven OpenCode/Grok backend. The classifier then emits `status=ALLOWED` / `is_runnable()=True`, and a downstream consumer (the 0005 lane engine) faithfully assigns an **executable** lane. A proxied/untrusted task obtains trusted execution.

This is **latent today** — no executor reads `LaneDecision.is_executable` (the only shipped consumer is the read-only `dopemux dcp classify` CLI). It becomes an **active exploit the moment any execution surface is wired**. Hence this packet must land before connector / runner / live-write / ECC / backend execution.

---

## Design — provenance can only LOWER trust

Add explicit provenance signals; evaluate them so they coerce the effective decision **downward** and **override** a claimed `authority_class`. All default to the safe value → zero regression.

### New fields on `RoutingClassificationInput`
| Field | Default | Effect |
|---|---|---|
| `authority_via_bridge_proxy: bool` | `False` | coerce effective `authority_class` → `UNKNOWN` (bridge/proxy/adapter/shim/mirror output is never authority) |
| `evidence_is_retrieval_derived: bool` | `False` | with `not exact_source_fetched` → evidence is advisory; cannot raise authority/confidence; mutation blocked |
| `exact_source_fetched: bool` | `False` | clears the retrieval-derived block ONLY when the exact source was fetched and cited |
| `is_ecc_external_intake: bool` | `False` | only `READ_ONLY`/static allowed; any `requires_runner_execution` / `requires_live_write` / `touches_destructive_path` / copy / import → `BLOCKED` |
| `has_backend_wrapper_proof: bool` | `False` | when `backend_kind ∈ {OPENCODE, GROK}` and `False` → block mutation |

**Case "secure-MCP-readonly": NO new field.** `requires_mcp_call → RED_LANE` stays as-is in the classifier; a secure read-only MCP facade is an ACL/read concern, not classifier permission.

### Coercion precedence (critical)
Provenance coercion MUST run **before** the authority-based `ALLOWED` path — extend the normalization step / the most-severe-first ordering established by the #904 precedence fix. A laundered `authority_class=AUTOMATED_SAFE` + `authority_via_bridge_proxy=True` MUST resolve to effective-`UNKNOWN` → not runnable. **Prefer DERIVING risk from existing authoritative signals where present** (e.g. `backend_kind ∈ {OPENCODE, GROK}`) over trusting a separate caller bool.

---

## Honest limitation — necessary, not sufficient

These fields only protect when a **trusted entity populates the input truthfully**. A caller that lies by **omission** (never sets `authority_via_bridge_proxy=True`) bypasses the check. The complete defense is this packet **PLUS** a trusted input-provenance contract: the entity constructing `RoutingClassificationInput` must itself be trusted/audited to derive provenance from authoritative signals (`task_source`, transport, backend), not accept free caller booleans. That contract is a **separate co-requisite** (the Prompt-5 audit "facade / input-provenance trust contract", F8) and is **also blocking** before execution. Do not over-claim these fields as a complete fix.

---

## Invariants (non-negotiable)
1. Provenance signals can only LOWER trust (coerce to `UNKNOWN` / `BLOCKED` / `RED_LANE`), never raise it.
2. All new fields default to a no-op → zero regression to existing classifications.
3. Provenance coercion overrides a claimed `authority_class`.
4. `requires_mcp_call → RED_LANE` unchanged.
5. Deterministic-first; no model-assisted logic; fail-closed on unknowns.
6. Pure function; no I/O, network, shell, runner, connector, MCP, or dopetask calls.

---

## Required tests (`tests/unit/dcp/test_routing_classifier.py`)
1. `test_bridge_proxy_authority_coerced_to_unknown` — `authority_via_bridge_proxy=True` + `authority_class=AUTOMATED_SAFE` + `has_unknown_authority=False` → status NOT `ALLOWED`, `is_runnable()` False. **(the gemini laundering exploit, explicit)**
2. `test_retrieval_derived_without_source_blocks_mutation`.
3. `test_retrieval_derived_with_source_fetched_permits` — `evidence_is_retrieval_derived=True` + `exact_source_fetched=True` behaves like non-derived.
4. `test_ecc_intake_static_only` — `is_ecc_external_intake=True` + any runner-exec / live-write / destructive / copy / import → `BLOCKED`.
5. `test_opencode_backend_requires_wrapper_proof`.
6. `test_grok_backend_requires_wrapper_proof`.
7. `test_secure_mcp_readonly_still_red_lane` — `requires_mcp_call=True` → `RED_LANE` (unchanged).
8. **Regression** — each new field defaulting `False` does NOT change any existing classification (full existing `tests/unit/dcp/` green).
9. `test_provenance_coercion_overrides_claimed_authority` — generalization of #1 across all four provenance vectors.

---

## Scope
**IN**: `+5` fields + coercion rules in `src/dopemux/dcp/routing_classifier.py` (touch `routing_model.py` only if an enum value is genuinely required — likely none); the 9 tests above + regression guards.
**OUT**: no lane-engine changes; no connector / runner / MCP / live calls; the trusted-adapter input-provenance contract (separate co-requisite packet); no CLI wiring.

---

## Validation gates
- `compileall src/dopemux/dcp` PASS.
- All 9 tests + regression guards PASS.
- Full `tests/unit/dcp/` PASS (no regression).
- `ruff check` clean; `git diff --check` clean; diff touches only allowed files.

## Proof requirements
Branch, commit SHA, PR URL (or exact blocker), `git diff --stat` + full diff, all command outputs **with exit codes**, embedded-audit report, residual risks, `UNKNOWN`s.

## Embedded audit requirement
Independent Opus audit (separate subagent): confirm provenance signals can only lower trust; no field can raise authority/confidence; coercion overrides claimed authority; `requires_mcp_call → RED_LANE` intact; zero regression. Return PASS / PASS_WITH_RISKS / FAIL. FAIL ⟹ stop, do not open PR.

## Rollback
```bash
git checkout main -- src/dopemux/dcp/routing_classifier.py tests/unit/dcp/test_routing_classifier.py
# or: git branch -D feat/dcp-0006-classifier-provenance-hardening
```

## Stop conditions
Stop if: hardening requires a lane-engine or enum change beyond a single additive value; a connector/runner/live-write surface is needed to test; provenance coercion cannot be expressed deterministically; embedded audit returns FAIL; diff escapes allowed files.

## Blocking-gate declaration
**No DCP execution surface (connector, runner, live-write, ECC adoption, backend invocation) may be wired to `LaneDecision.is_executable` until BOTH (a) this packet AND (b) the trusted input-provenance contract are merged to `main` and independently audited.** The 0005 lane-engine MVP is exempt because it is execution-inert.
