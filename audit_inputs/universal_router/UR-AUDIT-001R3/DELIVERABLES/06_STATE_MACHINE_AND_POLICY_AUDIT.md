# 06 — State Machine, Routing Policy & Executable Policy Audit

## A. Route state machine (`08`)

States present: all 14 required (`INTAKE, CLASSIFIED, CAPABILITIES_RESOLVED, POLICY_CHECKED,
ROUTE_RECOMMENDED, OPERATOR_ACCEPTED, HANDOFF_PREPARED, EXECUTION_ACCEPTED, EXECUTING, VALIDATING,
AUDITING, COMPLETED, ESCALATED, BLOCKED`). **Match: complete.**

| Check | Result | Notes |
|---|---|---|
| First-release stops at ROUTE_RECOMMENDED / explicit OPERATOR_ACCEPTED | PASS | "No release-one code may transition to `HANDOFF_PREPARED` or beyond"; roadmap M1-M9; packets 001-009 scope-OUT execution |
| No first-release path reaches handoff/execution states | PASS | Hard invariant (`14`) + state limit + adapter `EXECUTE` "must not exist behind a hidden flag in release one" (`10`) |
| Illegal transitions rejected | PASS (design) | Legal-transition table is explicit; illegal transitions absent; UR-TP-002 gate: "any route can enter handoff/execution states" is a stop condition |
| Terminal states | PASS | COMPLETED/BLOCKED/ESCALATED terminal; continuation creates new attempt with `parent_decision_id` |
| Retry counters / same-tier retry | PASS | Per-operation retry table (`08`): intake 0, DCP 1, policy 0, env-failure 1 same-tier |
| Model/reasoning escalation | PASS | ≤1 reasoning + ≤1 model tier; security/authority may start high without consuming a step |
| Demotion | PASS | cost/latency/cert-driven only; never weakens containment/audit/identity/validation |
| Stale snapshots | PASS | low-risk read may use STALE-marked candidate (refresh next action); write/security/release block |
| Identity conflicts | PASS | any mismatch → CONFLICTING; pinned/benchmark/audit/security/release → BLOCKED/ESCALATED |
| Policy conflicts | PASS | invalid/duplicate-active/loosening-overlay → BLOCKED; hints never override |
| Freeflow denial | PASS | ADMISSION_DENIED blocks that candidate; not rewritten as provider failure |
| Audit failure | PASS | FAIL→BLOCKED; NEEDS_SUPERVISOR→ESCALATED; REQUIRED_NOT_RUN/SKIPPED block protected completion |
| Operator override | PASS | scoped external HumanApprovalRef; new attempt; cannot legalize leakage/fake identity/skipped-audit-as-pass/bypass current-head proof |
| Environment failure | PASS | separate path; never premium escalation |
| Cancellation / disablement / replay | PASS (modeled outside graph) | cancellation is a future RunnerResult status; disablement = kill switch / READ_ONLY_DEGRADED (mode, not state); replay = deterministic by sequence_id |

**Verdict:** legal, terminal, and first-release-limited state machine. No illegal or execution-reaching
first-release transition. No P0/P1.

## B. Routing policy per required route class (`09`,`11`,`13`)

Each class was checked for prerequisites, candidate generation, exclusions, cost/reasoning/network/
containment handling, audit assignment, validation, fallback/escalation/demotion, blocking, evidence:

| Route class | Verdict | Key guard verified |
|---|---|---|
| cheap read | PASS | LOW reasoning; OFFLINE for repo facts; audit NOT_REQUIRED unless authority/security |
| repository investigation | PASS | read-only worktree; MEDIUM→HIGH only on contradiction; no implementation |
| ordinary implementation | PASS | Codex primary; worktree+allowlists; embedded audit (future execution) |
| multi-file implementation | PASS | HIGH; planner for arch-sensitive; **no subagent fanout** |
| difficult diagnosis | PASS | escalate only after root-cause confidence fails; not after env failure |
| architecture | PASS | supervisor route; no code implementation |
| security & authority | PASS | OS/wrapper enforcement required; prompt-only ineligible; independent audit mandatory; unknown identity blocks |
| release judgment | PASS | route selection cannot approve release; PR Steward + current proof/head |
| desktop advisory | PASS | consoles only; output advisory; no attestation/promotion/approval by itself |
| API automation | PASS | explicit path/ceiling/posture/credential-presence; consumer plan ≠ API entitlement; Freeflow admission authority |
| runner unavailability | PASS | same-tier certified alternative or BLOCK; **no premium jump** |
| unknown cost | PASS | not zero; low-risk with operator confirm; cost-capped/security/release block |
| unknown credits | PASS | not inferred from tokens; plan-sensitive block |
| unknown model identity | PASS | low-risk advisory may proceed with visible uncertainty; pinned/benchmark/audit/security/release block |
| stale capability / health snapshots | PASS | STALE not UNAVAILABLE; write/security/release block on required stale |
| provider drift | PASS | CONFLICTING; protected routes block/escalate; no certification claim |
| environment failure | PASS | classify separately; retry ≤1; **never premium escalation** (hard invariant) |
| policy conflict | PASS | invalid active policy blocks recommend; `explain` diagnoses via safe built-in policy |
| identity conflict | PASS | CONFLICTING preserved; sensitive routes block |
| audit failure | PASS | FAIL/skip never pass |

**Environment-failure → premium escalation** was specifically tested across `06`,`08`,`09`,`11`,`13`,`14`,
`17` and is uniformly forbidden. No route class violates the first-release invariants.

## C. Executable policy & precedence (`14`,`05`)

- Owner: Dopemux Universal Router owns parse/invariants/validation/eval only — **not** availability/admission/
  benchmark/approval/release. Correct.
- Proposed paths challenged: `config/universal-router/policies/<id>.yaml`, `config/universal-router/active-policy.json`,
  `schemas/universal-router/route-policy.schema.json` — **all absent at census (greenfield, no collision).**
- Precedence: compiled hard invariants > active certified policy > tightening-only local overlay > packet/operator
  constraints > operator hints. Higher layers unweakenable; overlay can only tighten (disable routes, lower ceilings,
  stronger containment/audit, shorter TTLs). **Correct.**
- Activation atomicity: active pointer is a tracked JSON edited only by reviewed merge; decisions capture policy
  hash/version so historical decisions preserve their policy version. **Correct.**
- Unverified policy cannot activate; rollback = revert to prior certified hash; journal never deleted. **Correct.**
- Worktree race: workspace-scoped advisory lock + WAL single-writer; per-worktree overlay/journal (see P3-006).
- CLI flag precedence: operator hints "do not weaken higher layers" — explicit and safe.
- Policy owns recommendation logic only — no execution/promotion authority.

## D. READ_ONLY precise semantics (prompt requirement)
The architecture defines READ_ONLY as: no external-system writes, no tracked-repository writes, no execution
handoff, **append-only local journal writes permitted**, capability-snapshot ingestion permitted, operator
acceptance journaled without becoming approval authority. Independently verified: the journal path
`<repo_root>/.dopemux/universal-router/router.sqlite3` is **gitignored** (`.gitignore:299 '.dopemux/'`), so
`recommend`'s default write does not touch tracked repository state. **No ambiguity authorizing broader writes
was found.** Preferred operator surface (`route explain/recommend/inspect/validate`) matches the prompt; no
service/daemon (justified). No P0/P1 in this domain.
