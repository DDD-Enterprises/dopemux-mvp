---
id: DMX-DCP-MODEL-ROUTING-MVP-0005
title: DCP Lane Engine MVP
type: how-to
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-16'
last_review: '2026-06-16'
next_review: '2026-09-14'
prelude: Implementation packet for the DCP lane engine MVP — a pure function mapping a RouteDecision into an explicit LaneDecision (lane, executability, allowed/forbidden actions, proof/audit/escalation, stop conditions, rationale). Consumes the classifier decision as the authoritative gate; never re-derives safety; raw MCP / live-write / dopetask / runner / connector / Secure-MCP-facade remain BLOCKED or deferred.
---

# DMX-DCP-MODEL-ROUTING-MVP-0005 — DCP Lane Engine MVP

**Series**: DMX-DCP-MODEL-ROUTING-MVP
**Packet**: 0005 (implementation)
**Authored by**: PRE-PROMPT6-0003 (design-only)
**Executed by**: PRE-PROMPT6-0004 (implementation)
**Depends on**: precedence fix `DMX-DCP-PRE-PROMPT6-0002` merged onto `main` (PR #904); clean `main`.
**Base**: cut from `main` AFTER #904 merges.

---

## Objective

Implement a **pure** DCP lane engine that maps a deterministic `RouteDecision` (from
`classify_route`) into an explicit `LaneDecision`: which lane the task belongs to, whether
it is executable **now**, its allowed/forbidden actions, proof/audit/escalation
obligations, stop conditions, and a rationale.

The lane engine is the substrate that later backend-runner and connector lanes will plug
into. This MVP ships **classification only** — no execution, no runner/connector/MCP/live
calls.

## Architectural placement (observed)

`src/dopemux/dcp/routing_backend_policy.py` is the existing sibling: a pure function that
consumes a `RouteDecision` (`decision.status`, `stop_conditions`, forbidden markers) and
returns an inert `BackendPolicyRecommendation`. The lane engine occupies the **same slot** —
a second pure consumer of `RouteDecision`. Model it on `routing_backend_policy.py`'s import
and purity discipline. (CLI wiring in `commands/dcp_commands.py` is **out of scope** for this
packet — future work.)

---

## Scope

### IN
- New `src/dopemux/dcp/lane_model.py` — `LaneKind` enum + `LaneDecision` dataclass.
- New `src/dopemux/dcp/lane_engine.py` — `decide_lane(decision, classification_input) -> LaneDecision` (pure) + helpers.
- New `tests/unit/dcp/test_lane_engine.py` — the tests pinned below.
- Touch `src/dopemux/dcp/__init__.py` **only if** exporting `LaneKind` / `LaneDecision` / `decide_lane`.

### OUT (do not implement)
- No runner backend execution.
- No connector calls.
- No Secure MCP facade implementation (constant/blocked-lane representation only).
- No raw MCP.
- No dopetask execution.
- No Task Orchestrator writes.
- No OpenCode/Grok wrapper.
- No live-write lane beyond a blocked/design-only representation.
- No CLI wiring (`dopemux dcp lane`) — future packet.
- No broad refactor of `routing_classifier.py` / `routing_model.py` (no field additions, no enum changes). If an integration bug appears to require a classifier change, **STOP** (see Stop Conditions).

---

## Invariants (non-negotiable)

1. **Classifier decides safety first.** The lane engine reads `decision.status` and
   `decision.red_lane_state` as the **authoritative gate**. It MUST NOT re-derive safety,
   re-classify, or override the decision.
2. **No blocked→runnable conversion.** `decision.red_lane_state is RED_LANE` OR
   `decision.status is RouteStatus.BLOCKED` ⟹ `lane == LaneKind.BLOCKED` AND
   `is_executable is False` AND `allowed_actions == ()`.
3. **`requires_mcp_call → RED_LANE → BLOCKED` stays hard-blocked.** The lane engine never
   produces a Secure-MCP-facade *executable* lane. `SECURE_MCP_FACADE` may appear **only**
   as a deferred/design-only constant or an explicit non-executable BLOCKED mapping — never
   `is_executable=True`.
4. **Live-write stays blocked** without an explicit `LIVE_WRITE_READY` contract (absent in
   this MVP). Any live-write-shaped decision is already `BLOCKED` by the classifier.
5. **Dopetask execution remains forbidden** — never executable, token stays in
   `forbidden_actions`.
6. **Unknown authority cannot grant mutation.** A non-BLOCKED but non-runnable decision
   (`status in {UNKNOWN, NEEDS_SUPERVISOR}`) yields `is_executable=False` and
   `allowed_actions` with **no** mutating tokens.
7. **`allowed_actions` is inherited, never widened.** `LaneDecision.allowed_actions ⊆
   decision.allowed_actions`. The lane engine may only narrow.
8. **Proof/audit/escalation are surfaced, not flattened.** `LaneDecision` carries the
   decision's `proof_requirements`, `audit_requirement`, `escalation_requirement` —
   unchanged (lane-specific additions only *strengthen*).
9. **Pure function.** No I/O, shell, network, filesystem, connector, MCP, runner, or
   dopetask calls. Imports limited to stdlib + `dopemux.dcp` model/classifier.
10. **No new model fields / no public enum changes** in `routing_model.py` /
    `routing_classifier.py`.

---

## Lane model

```python
class LaneKind(Enum):
    READ_ONLY_EVIDENCE = "read_only_evidence"
    DOCS_ONLY = "docs_only"
    PROOF_ONLY = "proof_only"
    CLASSIFIER_ROUTING = "classifier_routing"
    LOCAL_CODE_IMPLEMENTATION = "local_code_implementation"
    TEST_VALIDATION = "test_validation"
    EMBEDDED_AUDIT = "embedded_audit"
    PR_STEWARD_READINESS = "pr_steward_readiness"
    EXTERNAL_INTAKE = "external_intake"
    BLOCKED = "blocked"
```

**Deferred (do NOT add as executable lanes in this MVP):** `SECURE_MCP_FACADE`,
`FUTURE_LIVE_WRITE`, `RUNNER_BACKEND_EXECUTION`, `CONNECTOR_CALL_EXECUTION`. If represented
at all, only as a module-level commented constant or doc note — never an executable
`LaneKind` member. **Raw MCP remains BLOCKED.**

```python
@dataclass(frozen=True)
class LaneDecision:
    lane: LaneKind
    route_status: RouteStatus
    is_executable: bool
    allowed_actions: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    proof_requirements: tuple[ProofRequirement, ...]
    audit_requirement: AuditRequirement
    escalation_requirement: EscalationRequirement
    stop_conditions: tuple[str, ...]
    rationale: tuple[str, ...]
```

## Engine contract

```python
def decide_lane(
    decision: RouteDecision,
    classification_input: RoutingClassificationInput,
) -> LaneDecision: ...
```

- `decision` = **authoritative safety gate** (status, red_lane_state, allowed/forbidden,
  proof/audit/escalation, stop_conditions).
- `classification_input` = **intent signals only** (task_type, task_source, touches_*,
  is_repo_changing, requested_actions). Used to pick the lane KIND — **never** to override
  the gate.

### Lane assignment (precedence-ordered, first match wins)

| # | Condition | LaneKind | is_executable |
|---|---|---|---|
| 1 | `decision.red_lane_state is RED_LANE` **or** `decision.status is BLOCKED` | `BLOCKED` | `False` (allowed=()) |
| 2 | `inp.task_type is AUDIT` | `EMBEDDED_AUDIT` | gate† |
| 3 | `"pr_steward_readiness" in inp.requested_actions` | `PR_STEWARD_READINESS` | gate† (read-only) |
| 4 | `inp.task_source` ∈ external agents **and** `task_type is READ_ONLY` **and** `evidence_refs` **and** no code/test/docs scope | `EXTERNAL_INTAKE` | `False` (no execute/import/install) |
| 5 | `inp.task_type is PROOF_BUNDLE` | `PROOF_ONLY` | gate† |
| 6 | `inp.touches_tests` and not `inp.touches_files` | `TEST_VALIDATION` | gate† |
| 7 | `inp.touches_docs` and not (`touches_files`/`touches_tests`) and `task_type` ∉ {CODE_CHANGE, SCHEMA_ONLY} | `DOCS_ONLY` | gate† |
| 8 | `inp.task_type` ∈ {CODE_CHANGE, SCHEMA_ONLY} **or** (`is_repo_changing` and `touches_files`) | `LOCAL_CODE_IMPLEMENTATION` | gate† (audit_requirement preserved) |
| 9 | `inp.task_type is DESIGN_ONLY` | `CLASSIFIER_ROUTING` | gate† |
| 10 | fallback | `READ_ONLY_EVIDENCE` | gate† |

† **gate** = `is_executable = (decision.status is ALLOWED) and (decision.red_lane_state is
CLEAR) and (lane ∈ _EXECUTABLE_LANES)`. `EXTERNAL_INTAKE` and `BLOCKED` are **never**
executable. Mirrors `RouteDecision.is_runnable()` — a non-ALLOWED status yields
`is_executable=False` for every lane.

### Field derivation
- `allowed_actions` = `tuple(decision.allowed_actions)` (inherited; classifier already
  returns read-only/empty for non-ALLOWED) — **never widened**. `EXTERNAL_INTAKE` narrows
  to `()`.
- `forbidden_actions` = `tuple(decision.forbidden_actions)` + lane extras (e.g.
  `EXTERNAL_INTAKE` adds `"execute"`, `"import"`, `"install"`).
- `proof_requirements` / `audit_requirement` / `escalation_requirement` = inherited from
  `decision`, unchanged.
- `stop_conditions` = `tuple(decision.stop_conditions)` (+ lane-specific where stronger).
- `rationale` = ordered tuple of labels explaining the lane + gate (e.g.
  `("red_lane_blocked",)`, `("status_allowed", "task_type_code_change")`).

---

## Required tests (exact — 0004 MUST add all; each constructs a `RoutingClassificationInput`, runs `classify_route`, then `decide_lane`)

1. `test_blocked_route_maps_to_blocked_lane_not_executable` — a `BLOCKED` route (e.g.
   `has_stale_proof=True`) → `lane is LaneKind.BLOCKED`, `is_executable is False`,
   `allowed_actions == ()`.
2. `test_red_lane_mcp_route_blocked_no_facade_bypass` — `requires_mcp_call=True` →
   `LaneKind.BLOCKED`, not executable, **no** SECURE_MCP_FACADE lane; `"call_mcp"` /
   `"call_mcp_live"` present in `forbidden_actions`.
3. `test_live_write_route_blocked` — `requires_live_write=True` → `LaneKind.BLOCKED`, not executable.
4. `test_dopetask_execution_route_blocked` — `requires_dopetask_execution=True` →
   `LaneKind.BLOCKED`, not executable; dopetask token in `forbidden_actions`.
5. `test_unknown_authority_route_non_mutating_not_executable` — default input
   (`has_unknown_authority=True`, no hard block) → `is_executable is False` AND no mutating
   token (`edit_allowlisted_files`/`open_pr`) in `allowed_actions`.
6. `test_docs_only_safe_route_maps_to_docs_only` — a safe docs-only route
   (`touches_docs=True`, OPERATOR authority, known dims) → `LaneKind.DOCS_ONLY`.
7. `test_proof_only_fresh_proof_route` — a safe `PROOF_BUNDLE` task (no stale/missing proof)
   → `LaneKind.PROOF_ONLY`. **Policy:** stale/missing proof is `BLOCKED` by the classifier
   (precedence fix 0002), so it maps to `LaneKind.BLOCKED`, **not** PROOF_ONLY — assert that
   in a companion case `test_proof_only_stale_proof_is_blocked`.
8. `test_classifier_routing_task_maps_to_classifier_routing` — a `DESIGN_ONLY` routing task
   (safe) → `LaneKind.CLASSIFIER_ROUTING`.
9. `test_test_validation_task_maps_to_test_validation` — `touches_tests=True`,
   `touches_files=False`, safe → `LaneKind.TEST_VALIDATION`.
10. `test_local_code_implementation_preserves_audit` — non-trivial repo-changing safe route
    (`task_type=CODE_CHANGE`, `is_repo_changing`, `is_non_trivial`, OPERATOR) →
    `LaneKind.LOCAL_CODE_IMPLEMENTATION` AND `audit_requirement` equals the decision's
    (EMBEDDED_AUDITOR/SUPERVISOR_AUDIT — preserved, not flattened).
11. `test_external_intake_no_execution` — external-agent READ_ONLY evidence-intake task →
    `LaneKind.EXTERNAL_INTAKE`, `is_executable is False`, and `allowed_actions` contains no
    execute/import/install token.

Plus structural guards:
12. `test_allowed_actions_never_widen_decision` — for a sample of routes, assert
    `set(lane.allowed_actions) ⊆ set(decision.allowed_actions)`.
13. `test_no_forbidden_imports_in_lane_engine_source` — assert the module source contains no
    `subprocess`/`socket`/`requests`/`httpx`/`open(`/`mcp`/`connector`/`runner` execution
    imports (mirror `test_no_forbidden_imports_in_classifier_source`).
14. `test_lane_engine_does_not_mutate_inputs` — `decide_lane` does not mutate `decision` or
    `classification_input`.

---

## Exact commands (0004)

```bash
git checkout main
git pull --ff-only          # must include #904 (precedence fix)
git status --short
git switch -c feat/dcp-lane-engine-0005
PYTHONPATH=src python -m compileall -q src/dopemux/dcp
PYTHONPATH=src python -m pytest -q tests/unit/dcp/test_routing_classifier.py
PYTHONPATH=src python -m pytest -q tests/unit/dcp/test_lane_engine.py
PYTHONPATH=src python -m pytest -q tests/unit/dcp/ tests/dcp/test_dcp_model_routing_0001_domain.py
git diff --check
git diff --stat
git diff
```

## Validation gates
- `compileall src/dopemux/dcp` PASS.
- All required lane tests (1–14) PASS.
- Existing `test_routing_classifier.py` still PASS (no regression).
- Full `tests/unit/dcp/` + `tests/dcp/test_dcp_model_routing_0001_domain.py` PASS.
- `git diff --check` clean.
- Diff touches only allowed files.

## Proof requirements
Return: branch, commit SHA, PR URL (or exact blocker), `git diff --stat` + full diff, all
command outputs **with exit codes**, embedded-audit report, residual risks, UNKNOWNs.

## Embedded audit requirement
After implementation run an **independent Opus audit** (separate subagent) with this question:

> Audit the 0005 lane engine for: classifier bypass; red-lane weakening; raw-MCP permission
> leakage; live-write leakage; dopetask execution leakage; runner/connector execution
> leakage; proof/audit flattening; authority confusion; overbroad allowed_actions; missing
> tests. Confirm `allowed_actions ⊆ decision.allowed_actions` for all routes and that no
> BLOCKED/red-lane route is executable. Return PASS / PASS_WITH_RISKS / FAIL.

Acceptance: PASS or PASS_WITH_RISKS with non-blocking risks. FAIL ⟹ stop, do not open PR.

## PR Steward readiness requirement
Before requesting merge, the PR must satisfy PR-Steward-style readiness: green required
checks, scoped diff (allowed files only), no unresolved blocking review threads, proof
bundle current to head SHA. **Merge remains operator-only.**

## Rollback
```bash
git rm -f src/dopemux/dcp/lane_engine.py src/dopemux/dcp/lane_model.py tests/unit/dcp/test_lane_engine.py
git checkout main -- src/dopemux/dcp/__init__.py task-packets/DMX-DCP-MODEL-ROUTING-MVP-0005.md
# or: git branch -D feat/dcp-lane-engine-0005
```

## Stop conditions
Stop if:
- lane engine requires a classifier field expansion or enum change (outside scope);
- implementation needs connector/runner/live-write/MCP/dopetask execution to test;
- tests reveal classifier ambiguity not resolved by 0002;
- embedded audit returns FAIL;
- diff escapes the allowed files.

## Expected output
```
TP: DMX-DCP-MODEL-ROUTING-MVP-0005
STATUS: IMPLEMENTED / BLOCKED
BRANCH:
COMMIT:
PR:
VALIDATION:
AUDIT_VERDICT:
RESIDUAL_RISKS:
UNKNOWNs:
```

---

## Consensus review addendum — 2026-06-16 (Opus adjudication + PAL consensus: gpt-5.5-pro `against`, gemini-2.5-pro `neutral`)

This packet is the **canonical 0005 lane engine** (pure `decide_lane` consumer of `RouteDecision`; clean policy-decision/enforcement split — UNANIMOUS across both review models). The competing `claudedocs/dcp-routing-0005-lane-engine-design-2026-06-16.md` (which proposed adding 5 provenance fields to the classifier) is **superseded as a lane engine**; its content is *classifier provenance-hardening*, addressed below as a separate BLOCKING dependency.

Three binding refinements (fold into the 0004 implementation):

1. **Executable gate — base on `is_runnable()`, do not re-derive.** Implement
   `is_executable = decision.is_runnable() AND lane in _EXECUTABLE_LANES AND set(required_actions) ⊆ set(decision.allowed_actions)`.
   Call `decision.is_runnable()` directly rather than re-deriving `(status==ALLOWED and red_lane==CLEAR)` inline (drift risk if the classifier changes). `EXTERNAL_INTAKE` and `BLOCKED` remain non-executable.

2. **Non-widening guards must cover ALL inherited obligations.** Assert `LaneDecision` never widens `allowed_actions` AND never weakens `proof_requirements` / `audit_requirement` / `escalation_requirement` / `stop_conditions` relative to `decision` (a lane may only strengthen).

3. **Classifier provenance-hardening (the former "Design B") is a BLOCKING PREREQUISITE — not optional future work.** A downstream pure consumer is only as safe as the `RouteDecision` it trusts. The classifier is currently blind to provenance laundering: a caller setting explicit non-default authority (`authority_class=AUTOMATED_SAFE`, `has_unknown_authority=False`) for a task whose TRUE source is a bridge/proxy, retrieval-derived evidence, ECC intake, or an unproven runner backend gets `status=ALLOWED / is_runnable()=True`, and this lane engine would assign an executable lane.
   - **Why 0005 MVP may still ship now:** `is_executable` is INERT — no connector/runner/live-write/ECC executor reads it (only consumer = read-only `dopemux dcp classify`). The hole is latent, not active.
   - **Hard gate:** the classifier provenance-hardening packet (renumbered — NOT 0005) MUST land BEFORE any execution surface (connector / runner / live-write / ECC / backend) is wired to `is_executable`. Track as an explicit blocking dependency on those packets.
   - **Trust boundary:** who populates `RoutingClassificationInput`, and is that population trusted? Same "input/facade provenance trust contract" gap flagged in the Prompt-5 audit. Required before execution.

Acceptance for 0005 itself is unchanged (classification-only, execution-inert) with refinements 1–2 applied.
