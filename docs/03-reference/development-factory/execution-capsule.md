# Execution Capsule

> **Note:** The formal JSON schema and `EXECUTION_CAPSULE_TEMPLATE.md` are deferred to
> `TP-DMX-EXECUTION-CAPSULE-SCHEMA-001`. This document defines the design and field contract.

---

## Purpose

The Execution Capsule is the atomic unit of factory work. It replaces loose task packets with a
structured, authority-constrained execution contract.

Loose packets lack authority constraints, scope enforcement, and model routing. The capsule format
closes those gaps by making every execution parameter explicit before any code is touched. A capsule
cannot begin execution unless all required fields are present and authority constraints have been
validated by the Factory Controller.

---

## Capsule Fields

```yaml
identity:
  capsule_id           # TP-DMX-* style ID
  version              # semver or date-stamp
  authored_by          # who generated this capsule
  supervisor           # GPT-5.5 Pro or named human

project_workstream:
  project_id           # project registry reference
  workstream_id        # workstream registry reference

authority_constraints:
  allowed_authority    # list of systems this capsule may write
  forbidden_authority  # list of systems this capsule must not touch
  must_consult         # authority files to read before any edit

worktree_branch_policy:
  worktree_path        # isolated worktree path
  branch_name          # branch naming convention
  base_branch          # branch to PR against (usually main)
  lease_expiry         # when the lease expires (hours/date)

scope:
  in_scope             # explicit list of allowed file paths / modules
  out_of_scope         # explicit exclusions
  allowed_files        # grep patterns for permitted edits
  forbidden_files      # hard-blocked paths (secrets, generated artifacts, proof/ of other packets)

commands:
  exact_commands       # ordered list of exact bash commands to run
  commit_plan          # expected commit messages and when to commit

repair_budget:
  max_repair_attempts  # how many times implementer may retry a failing step
  repair_allowed       # bool — is any self-repair allowed

embedded_audit:
  required             # bool (always true for L2+)
  auditor              # PAL codereview or external tool
  self_audit_forbidden # always true — implementer cannot self-audit

pr_plan:
  title                # PR title template
  body_template        # PR body sections required
  auto_merge           # always false until L6 unlocked

proof_requirements:
  proof_path           # proof/TP-DMX-*/PROOF.json
  required_fields      # list of required JSON fields
  head_sha_required    # bool (always true)

follow_up_rules:
  follow_up_packets    # list of packet IDs to generate after success
  obligation_updates   # obligations to close on success

learning_metrics:
  success_criteria     # measurable outcomes for this capsule
  failure_modes        # known failure patterns to log

stop_conditions:
  hard_stops           # conditions that require immediate halt
  escalation_path      # who to notify on stop

model_routing:
  stage_overrides      # per-stage model override if default is wrong
```

---

## Field Group Descriptions

### `identity`

Unique, stable identification for this capsule. `capsule_id` follows the `TP-DMX-*` naming
convention. `authored_by` records the generating agent or human. `supervisor` names the
strong-model or human who approved the capsule before execution began.

### `project_workstream`

Links the capsule to its registry entries. Capsules without a valid `project_id` and
`workstream_id` are rejected by the Factory Controller. See
[project-workstream-registry.md](project-workstream-registry.md).

### `authority_constraints`

The most critical field group. `allowed_authority` is an explicit allowlist — if a system is not
listed, the capsule may not write to it. `forbidden_authority` adds hard exclusions independent of
scope. `must_consult` names the authority files (e.g., `AGENTS.md`, `ARCHITECTURE.md`) that the
implementer must read before making any edit that touches architecture, contracts, or security
boundaries.

Violations of `forbidden_authority` are immediate hard stops and generate an `AUTHORITY_CONFLICT`
obligation.

### `worktree_branch_policy`

Every capsule executes in an isolated worktree. `lease_expiry` prevents stale worktrees from
accumulating. The Factory Controller reclaims expired worktrees and logs an `ORPHAN` obligation
if no proof bundle was filed before expiry.

### `scope`

`in_scope` is an explicit list — broad wildcards are not allowed at L2. `forbidden_files` includes
at minimum: secrets files, generated artifacts (`*.lock`, compiled outputs), and the `proof/`
directories of other packets. Implementers attempting to write outside `allowed_files` receive a
hard stop.

### `commands`

Exact, ordered bash commands. Vagueness is not permitted. The `commit_plan` specifies not just
commit messages but the trigger condition for each commit (e.g., "after tests pass for unit block
A"). Deviation from `exact_commands` requires supervisor authorization logged to the obligation
ledger.

### `repair_budget`

`repair_allowed: false` means the implementer halts on first failure and escalates.
`max_repair_attempts` caps self-repair loops when repair is permitted. Repair attempts beyond the
budget are hard stops.

### `embedded_audit`

Always required for L2 and above. `self_audit_forbidden: true` is not a recommendation — it is a
hard constraint enforced by the Factory Controller. The `auditor` field names the PAL tool or
external service that performs the review. Audit output is included in the proof bundle.

### `pr_plan`

`auto_merge` is always `false` until the Autonomous Merge gate (L6) is unlocked for the workstream.
The `body_template` specifies required sections (e.g., Summary, Test Plan, Obligation Updates,
Proof Reference) so PR Steward can validate completeness.

### `proof_requirements`

`PROOF.json` must be filed at `proof_path` before the capsule can be marked complete. See
[obligation-ledger.md](obligation-ledger.md) for the closure rule. `head_sha_required: true` is
non-negotiable — proofs without a HEAD SHA are rejected.

### `follow_up_rules`

`follow_up_packets` is the list of packet IDs this capsule is responsible for authoring on success.
`obligation_updates` lists obligation IDs to move to `VERIFIED_CLOSED` (each must have a proof
reference). Capsules that succeed but fail to file follow-up packets generate `ORPHAN` obligations.

### `learning_metrics`

`success_criteria` are measurable, not aspirational ("all 47 tests in suite X pass", not "quality
improved"). `failure_modes` are known patterns from prior similar capsules, logged so the Factory
Controller can recognize recurrence and escalate rather than retry.

### `stop_conditions`

`hard_stops` are conditions that require immediate halt regardless of repair budget (e.g.,
"forbidden file written", "secret detected in output", "RED_LINE obligation encountered").
`escalation_path` names the supervisor or Factory Controller endpoint to notify.

### `model_routing`

Stage overrides for this capsule only. Must follow the constraints in
[model-routing.md](model-routing.md) — in particular, `judge_strong` and `plan_challenge` may not
be downgraded to cheap/mid-tier models without supervisor sign-off.
