---
id: DMX-DCP-MODEL-ROUTING-MVP-0007
title: DCP Trusted Input-Provenance Contract
type: how-to
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-16'
last_review: '2026-06-16'
next_review: '2026-09-14'
prelude: Defines the trust boundary for constructing classifier inputs. Execution-eligibility for mutating work must be conferred by an unforgeable in-process capability minted by a trusted adapter that DERIVES provenance from authoritative signals — never by any value present in serialized/caller-supplied input. Closes the lie-by-omission gap left open by 0006. BLOCKING co-requisite (with 0006) before any DCP execution surface; does not gate the execution-inert 0005 lane-engine MVP.
---

# DMX-DCP-MODEL-ROUTING-MVP-0007 — DCP Trusted Input-Provenance Contract

**Series**: DMX-DCP-MODEL-ROUTING-MVP
**Packet**: 0007 (design + thin implementation)
**Status**: DESIGN / PROPOSED — **BLOCKING co-requisite (with 0006)** before any execution surface. Open to revision; alternatives noted.
**Depends on**: 0006 classifier provenance-hardening ([PR #908](https://github.com/DDD-Enterprises/dopemux-mvp/pull/908)); 0005 lane engine ([PR #907](https://github.com/DDD-Enterprises/dopemux-mvp/pull/907)).
**Origin**: the "facade / input-provenance trust contract" gap (Prompt-5 audit F8), confirmed by PAL consensus (gpt-5.5-pro + gemini-2.5-pro, 2026-06-16) as the necessary second half of the provenance defense.

---

## Why this exists (the gap 0006 leaves open)

0006 makes the classifier *honor* provenance signals (they can only lower trust). But those signals are only protective if something sets them truthfully. **Today the classifier input is 100% caller-asserted:** the only construction site is `src/dopemux/commands/dcp_commands.py::_input_from_dict(data: dict)` (line 36–37), which builds a `RoutingClassificationInput` verbatim from an **arbitrary user-supplied JSON file** (`dopemux dcp classify --input-path …`). A caller can assert `authority_class=AUTOMATED_SAFE`, omit every 0006 provenance flag, and the classifier trusts it.

This is harmless **now** because `classify` is read-only (it prints the decision; nothing executes). It is catastrophic the moment any executor reads `LaneDecision.is_executable`. 0006 alone does not fix it: a caller lies by **omission** (never setting the risk flags) — or, if attestation were a mere field, by **commission** (setting `attested=True` directly).

## Core contract — attestation is a capability, not data

**Execution-eligibility for mutating work MUST be conferred by an unforgeable, in-process capability minted by a trusted adapter — never by any value present in serialized/caller-supplied input.** A serializable boolean/enum (`provenance_attested=True`, `input_provenance=TRUSTED`) is forgeable by anyone who can write JSON, so it CANNOT be the gate. JSON/dict deserialization must be incapable of manufacturing the capability.

Concretely (implementer may choose the mechanism; the invariant is fixed):
- **Untrusted path (default):** `classify_route(input)` treats every `RoutingClassificationInput` as untrusted. For any **mutating/executable** scope it caps the result at non-executable (`UNKNOWN`/`NEEDS_SUPERVISOR`, never `ALLOWED`-runnable). Read-only/classify is unaffected. `_input_from_dict` (raw JSON) flows here → always untrusted.
- **Trusted path:** a small, audited module `src/dopemux/dcp/input_adapters.py` exposes the ONLY sanctioned constructors of execution-eligible inputs (e.g. `from_authenticated_operator(...)`, `from_github_pr(...)`, `from_task_packet(...)`). Each **derives** the 0006 provenance fields from authoritative signals (authenticated source, actual transport, selected backend) — the raw caller cannot override them — and returns an `AttestedInput` (a frozen object / capability that is NOT produced by `from_dict`). The executable classifier entrypoint requires that capability by **type/identity**, not by reading a field.

This composes with 0006:
- **0006** — provenance signals can only LOWER trust (blocks lie-by-commission: provenance can never raise trust).
- **0007** — execution-eligibility requires a trusted-minted capability (blocks lie-by-omission: omission ⇒ untrusted ⇒ not executable).

## Honest limitation
This roots trust in *some* authority (the authenticated operator; a verified transport) and in the **correctness + audit of the trusted adapters**. It makes the trust boundary **explicit, minimal, and fail-closed** — it does not eliminate root trust. A bug in a trusted adapter (mis-deriving provenance) re-opens the gap; hence each adapter requires its own review when added. Do not claim this makes inputs "trusted" in the absolute — only "attested by a named, audited adapter."

## Invariants (non-negotiable)
1. No value present in serialized/caller input can confer execution-eligibility for mutating scope.
2. The default (raw / `from_dict` / hand-constructed) input is UNTRUSTED → non-executable for mutating scope; read-only routes are unaffected (no regression to the classify CLI).
3. Trusted adapters DERIVE provenance from authoritative signals; they never accept a caller-asserted provenance/authority override that raises trust.
4. Deterministic, fail-closed, pure (no I/O in the classifier; adapters may read only their authoritative signal source, no execution).
5. Adding a new trusted adapter is a reviewed, audited change (each is a trust-boundary surface).

## MVP scope
**IN**:
- `InputProvenance` marker + the capability mechanism (frozen `AttestedInput` or equivalent) in `src/dopemux/dcp/`.
- Classifier cap rule: untrusted input + mutating scope ⇒ not executable.
- `src/dopemux/dcp/input_adapters.py` with at least: the UNATTESTED/raw path (explicit) and one trusted constructor (`from_authenticated_operator`) as the reference pattern.
- Update `dcp_commands.py::_input_from_dict` to flow through the explicit UNTRUSTED path (documents that `--input-path` JSON is never execution-eligible).
- Tests below.

**OUT**: per-transport adapters for every source (GitHub/bridge/task-orchestrator/etc.) — each lands with its own execution surface + review; no execution; no connector/runner/live calls.

## Required tests (`tests/unit/dcp/`)
1. `test_untrusted_input_not_executable_for_mutating` — raw input, mutating scope, otherwise-ALLOWED dims ⇒ not runnable/executable.
2. `test_untrusted_input_ok_for_read_only` — raw input, read-only ⇒ classifies normally (no regression).
3. `test_from_dict_path_is_untrusted` — `_input_from_dict` output is never execution-eligible.
4. `test_serialized_field_cannot_confer_trust` — an input whose JSON tries to self-assert attestation/trusted-provenance is STILL untrusted (the forgery attempt fails).
5. `test_trusted_adapter_mints_attested_input` — `from_authenticated_operator(...)` yields an execution-eligible capability and derives provenance fields.
6. `test_trusted_adapter_cannot_raise_above_signals` — an adapter given risky authoritative signals does not produce an executable result (defense composes with 0006).
7. **Regression** — full `tests/unit/dcp/` green; read-only classify behavior unchanged.

## Validation gates
- `compileall src/dopemux/dcp` PASS; all tests + regression PASS; `ruff` clean; `git diff --check` clean; diff scope only.

## Proof / embedded audit
Standard proof bundle (branch, SHA, PR, diff, command outputs + exit codes, residual risks, UNKNOWNs). Independent Opus audit: confirm no serialized value confers execution-eligibility; `from_dict` is always untrusted; adapters only derive (never accept trust-raising overrides); zero regression to read-only classify. PASS / PASS_WITH_RISKS / FAIL; FAIL ⟹ stop.

## Rollback
```bash
git checkout main -- src/dopemux/dcp/ tests/unit/dcp/
# or: git branch -D feat/dcp-0007-input-provenance-contract
```

## Stop conditions
Stop if: the capability mechanism cannot be expressed without I/O or non-determinism in the classifier; enforcing the cap regresses read-only classify; the design requires a connector/runner surface to test; embedded audit returns FAIL.

## Blocking-gate declaration
**No DCP execution surface (connector, runner, live-write, ECC adoption, backend invocation) may be wired to `LaneDecision.is_executable` until BOTH 0006 AND this contract (0007) are merged to `main` and independently audited.** The 0005 lane-engine MVP is exempt (execution-inert).

## Alternatives considered (open to revision)
- **(A) Serializable `provenance_attested` flag** — REJECTED: forgeable by any JSON caller; fails the core threat.
- **(B) Capability/typed `AttestedInput` (this packet)** — PREFERRED: trust by construction, unforgeable across the serialization boundary.
- **(C) Enforce attestation only at the lane-engine/execution boundary** — weaker: the classifier (the authoritative gate) would still emit `is_runnable()=True`, so any other consumer is exposed. Prefer enforcing in the classifier.
