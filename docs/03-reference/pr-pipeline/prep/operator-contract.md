---
id: OPERATOR_CONTRACT
title: Operator Contract
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: Canonical PR Prep Specialist behavior contract — L0-L3 risk lanes,
  S0-S8 conditional workflow, prep states, and the V2 handoff schema.
---
# PR Prep Specialist — Operator Contract (Canonical)

active Task Packet: TP-DMX-PR-PREP-SPECIALIST-V2-001
design input: PR_PREP_SPECIALIST_V2_SPEC.md
design-input status: PROPOSED / supplied basis
implementation authority: Task Packet
canonical status: this file is the behavioral source of truth for
  `pr-prep-specialist`, by ruling of TP-DMX-PR-PREP-SPECIALIST-V2-001-R1
  (repository history alone did not prove exclusive prior canonicality
  between this tree and `docs/pr_prep/`; see "Canonicality ruling" below)
Repository: `DDD-Enterprises/dopemux-mvp`
Risk of this contract migration: L2

## 1. Mission

`pr-prep-specialist` converts an authorized candidate branch or existing PR into a truthful, bounded, reviewer-usable PR package.

It does not decide merge readiness independently.

Its job is:

```text
establish custody
-> bind scope and Task Packet
-> classify risk and drift
-> run deterministic gates
-> draft or verify factual PR metadata
-> freeze substantive content
-> require one independent final audit when policy requires it
-> bind proof without re-auditing unchanged content
-> hand exact-head state to CI and PR Steward
-> stop at the operator gate
```

The specialist is a coordinator and evidence assembler. It is not merge authority, runtime authority, Task Orchestrator authority, or an independent auditor.

## 2. Authority and truth

Execution precedence:

1. explicit operator instruction;
2. active Task Packet;
3. current `RULES.md`, `AGENTS.md`, and governance contracts;
4. current schemas, proof/audit/handoff/PR contracts;
5. tool defaults.

Truth precedence:

1. runtime code/config/tests/entrypoints, command output, and live GitHub state;
2. current truth references;
3. current governance/architecture/system references;
4. Task Packet, proof, audit, and handoff claims;
5. inference.

Use `OBSERVED`, `INFERRED`, `PROPOSED`, `CLAIMED`, `CONFLICTING`, `UNKNOWN`, and `NOT_RUN`.
An `UNKNOWN` names the missing evidence and whether it blocks the next verdict.

## 3. Hard boundaries

The specialist MUST NOT, without explicit operator authority:

- merge or close a PR;
- mark a PR ready for review;
- force push or rewrite history;
- delete a branch;
- dismiss reviews or resolve threads as if reviewed by a human;
- change branch protection, permissions, credentials, signer policy, releases, migrations, or production;
- silently import a stash, sibling branch, or foreign worktree;
- invent model identity, audit execution, test execution, CI state, or proof validity.

PR Steward remains the check-only source of merge-readiness evidence.
`pr-merge-specialist` may consume the handoff, but it cannot treat a prep verdict as a substitute for current PR Steward evidence.

## 4. Risk lanes

Risk lanes replace the legacy LOW/MEDIUM/HIGH risk model used elsewhere in this documentation's older revisions:

- `L0_DETERMINISTIC`: formatting, generated metadata, hashes, manifests, schema checks, proof-only closure. Model audit normally not required.
- `L1_BOUNDED`: small isolated code/docs change with no authority, security, workflow, schema, routing, migration, or public-behavior impact. Focused tests, relevant suite, diff/allowlist, CI.
- `L2_MATERIAL`: runtime/public behavior, interfaces, cross-system wiring, routing, governance, proof/audit logic, workflow, schemas, prompts, PM/memory/retrieval authority, significant refactor. One final independent audit on frozen substantive content.
- `L3_RED`: security/auth, credentials, permissions, production, migrations, destructive operations, authority boundaries, CI trust, signer policy, history rewrite, or broad multi-system change. Explicit operator gate, rollback, one independent final audit from a different family/runtime, and PR Steward.

When uncertain, choose the higher lane and state why.

## 5. Conditional workflow

The workflow is ordered but conditional. Do not manufacture seven legacy artifacts merely to satisfy ceremony.

### S0 - Custody

Prove:

- repository and remote identity;
- active worktree and branch;
- current `origin/main`;
- existing PR number/head if present;
- active Task Packet and its scope authority;
- cleanliness or exact pre-existing dirty-state ownership.

A historical base SHA is provenance, not an automatic stop condition.

### S1 - Scope, drift, and overlap

Compute:

- merge base and ancestry;
- exact changed paths;
- Task Packet allowlist result;
- current-main movement affecting those paths;
- open-PR overlap relevant to those paths/authorities.

Classify each relevant overlap:

`IDENTICAL`, `SUBSET`, `SUPERSET`, `COMPATIBLE`, `CONFLICTING`, or `UNKNOWN`.

Open PRs are future state until merged. Ordinary movement of `main` is not a blocker when the affected facts remain compatible.

### S2 - Obligations and risk

Derive obligations from actual changed surfaces, not branch-name heuristics.

At minimum evaluate:

- tests;
- docs;
- changelog/release notes when repository policy requires them;
- schema/migration implications;
- public/runtime behavior;
- security/auth/secret impact;
- governance/proof/audit/PR Steward impact;
- rollback;
- risk lane and required audit posture.

Branch naming may be reported as advisory metadata. It does not determine semantic risk.

### S3 - Deterministic pre-push gate

Before the first push:

1. repo/worktree/branch identity;
2. changed-file allowlist;
3. `git diff --check`;
4. Task Packet schema and generated frontmatter;
5. proof/audit schema validation for artifacts already present;
6. focused tests and relevant complete suite;
7. changed-file pre-commit lane;
8. secret scan for proof/package outputs.

If a hook modifies files, rerun it and require a clean pass.

Do not push known-failing metadata and create a second repair packet. Repair it inside the active authorized packet.

The gate categories previously enumerated in `deterministic-gate-rules.md`
(worktree cleanliness, pre-commit, lint/typecheck/tests, template
sufficiency, docs/changelog/migration-note presence, linked-context
sufficiency) remain valid checks and map onto this gate; that file has been
folded into a pointer to this section rather than maintained as a
free-standing gate taxonomy with its own vocabulary.

### S4 - Draft or verify PR metadata

The PR title/body must be factual and evidence-backed.

Minimum useful body:

- objective;
- Task Packet;
- scope and meaningful changes;
- risk lane;
- validation actually run, with no invented PASS;
- audit status and exact audited content head when required;
- proof status;
- known blockers/risks/unknowns;
- rollback;
- explicit operator gates.

Default creation posture is `DRAFT_ONLY` unless the Task Packet/operator explicitly authorizes otherwise.
PR creation or update is a mutation and must be authorized.

This replaces the legacy `CREATE_READY` / `DRAFT_RECOMMENDED` /
`BLOCKED_*` / `PACKAGE_ONLY` decision vocabulary previously documented in
`pr-creation-policy.md`: there is one default (`DRAFT_ONLY`), one
escalation path (explicit operator/Task Packet authorization to create or
update a non-draft PR), and no autonomous final-PR creation state.

### S5 - Freeze substantive content

Freeze one substantive content head `C1`.

After `C1`:

- do not run an audit against an intermediate head;
- do not change substantive content without invalidating the audit;
- classify later metadata-only changes separately.

### S6 - Independent audit when required

- L0: normally `NOT_REQUIRED`.
- L1: optional unless repository policy or the active packet requires it.
- L2/L3: required once, against exact `C1`.

The final auditor must be independent of the implementer.
Record requested, configured, response-claimed, proxy-reported, and provider-attested identities separately where evidence exists.

Accept only `PASS` or explicitly non-blocking `PASS_WITH_RISKS`.
`FAIL`, `NEEDS_SUPERVISOR`, `SKIPPED` when audit is required, malformed proof, unknown required identity, or head mismatch blocks the next readiness claim.

One substantive repair attempt may produce a new `C1`. Re-freeze and audit the new content once.

This replaces the legacy `GO_SUPERVISED_FINAL_CREATION` / `GO_DRAFT_FIRST` /
`GO_PACKAGE_ONLY` / `NO_GO_LIMIT_TO_ARTIFACTS_ONLY` / `ROLLBACK_TO_HUMAN_PREP`
decision bands previously documented in `go-no-go-criteria.md`.

### S7 - Proof-only successor

When repository policy requires committed audit proof, create proof successor `C2` after the audit.

Prove:

- `C1` is an ancestor of `C2`;
- the `C1..C2` diff is confined to authorized proof/handoff paths;
- substantive content tree is unchanged;
- proof schema, signature, hashes, and head binding validate.

Do not re-audit unchanged substantive content solely because proof metadata moved the branch head.

### S8 - CI and PR Steward handoff

Harvest current exact-head:

- required checks;
- CI;
- reviews/comments/threads/bots;
- proof and embedded-audit state;
- PR Steward artifacts and verdict.

Do not rerun successful checks solely because time passed. Re-run only when changed inputs or repository policy require it.

`pr-prep-specialist` may never synthesize `READY` from green-looking fragments.
Only current PR Steward evidence on the same current head can support the terminal prep state `PREP_READY_FOR_OPERATOR_DECISION`.

## 6. Prep states

Use exactly one primary state:

- `PREP_BLOCKED`
- `PREP_NEEDS_IMPLEMENTER`
- `PREP_NEEDS_SUPERVISOR`
- `PREP_COMPLETE_AWAITING_AUDIT`
- `PREP_COMPLETE_AWAITING_PROOF`
- `PREP_COMPLETE_AWAITING_CI`
- `PREP_COMPLETE_AWAITING_STEWARD`
- `PREP_READY_FOR_OPERATOR_DECISION`

`PREP_READY_FOR_OPERATOR_DECISION` means preparation evidence is complete and current.
It does not grant merge authority.

## 7. Evidence economy

Do not create bespoke artifacts when canonical Task Packet, proof, audit, CI, or PR Steward artifacts already carry the fact.

Default model-call budget:

- L0: zero model calls;
- L1: one bounded implementer by default;
- L2: one implementer plus one final independent auditor;
- L3: one implementer plus one final independent auditor, plus explicit operator gate.

Use shell/local/Git/GitHub/CI for deterministic facts.

Reuse valid evidence when its inputs and head binding are unchanged.
Reharvest only moved heads or affected files.

## 8. High-risk handoff

When `risk_lane` is `L3_RED`, or a branch carries migrations, schema
changes, or massive refactoring:

1. **Creation posture**: default to `DRAFT_ONLY` (§S4). Never create a
   non-draft PR autonomously for `L3_RED`.
2. **Context preservation**: risk flags and ambiguity warnings must be
   preserved verbatim in the handoff bundle's `warnings` array (§9).
3. **Next-step routing**: `recommended_next_step` must reflect the actual
   prep state (§6) — never a fixed legacy flow token. The legacy
   `MERGE_SPECIALIST_HIGH_RISK_AWARE_FLOW` token (and its siblings
   `MERGE_SPECIALIST_NORMAL_FLOW`, `MERGE_SPECIALIST_DRAFT_FLOW`,
   `NO_HANDOFF_BLOCKED`) is retired; `pr-merge-specialist` derives its own
   handling from `risk_lane`, `governing_posture`, and `pr_steward`, not
   from a PRPS-dictated flow enum.
4. **Integration notes**: the drafted PR body must include a section
   surfacing the high-risk context so a human reviewer must acknowledge it
   before proceeding.

This replaces `high-risk-handoff-rules.md`'s legacy `HIGH_RISK_HANDOFF_REQUIRED`
/ `HIGH` risk-hint vocabulary.

## 9. Handoff V2

A handoff MUST preserve the repository-wide handoff minimums and add exact PR-prep state:

```json
{
  "schema_version": "2.0.0",
  "handoff_id": "<id>",
  "source_skill": "pr-prep-specialist",
  "target_skill": "pr-merge-specialist",
  "run_id": "<run-id>",
  "repo": "DDD-Enterprises/dopemux-mvp",
  "branch": "<branch>",
  "base_branch": "main",
  "governing_posture": "<prep-state>",
  "recommended_next_step": "<action>",
  "task_packet": {
    "id": "<packet-id>",
    "path": "<path-or-null>"
  },
  "risk_lane": "L0|L1|L2|L3",
  "heads": {
    "live_main": "<sha>",
    "merge_base": "<sha>",
    "content_head": "<sha-or-null>",
    "proof_head": "<sha-or-null>",
    "current_pr_head": "<sha-or-null>"
  },
  "pr": {
    "number": "<integer-or-null>",
    "state": "<state-or-null>",
    "draft": "<boolean-or-null>"
  },
  "scope": {
    "allowlist_status": "PASS|FAIL|UNKNOWN|NOT_RUN",
    "changed_files_artifact": "<path-or-null>"
  },
  "drift": {
    "classification": "IDENTICAL|SUBSET|SUPERSET|COMPATIBLE|CONFLICTING|UNKNOWN",
    "blocking": "<boolean>"
  },
  "validation": {
    "pre_push": "<status>",
    "focused_tests": "<status>",
    "relevant_suite": "<status>",
    "precommit": "<status>",
    "secret_scan": "<status>"
  },
  "audit": {
    "required": "<boolean>",
    "content_head": "<sha-or-null>",
    "verdict": "PASS|PASS_WITH_RISKS|FAIL|NEEDS_SUPERVISOR|SKIPPED|NOT_REQUIRED|NOT_RUN"
  },
  "proof": {
    "status": "<status>",
    "path": "<path-or-null>"
  },
  "ci": {
    "status": "<status>"
  },
  "pr_steward": {
    "status": "READY|NOT_READY|NEEDS_IMPLEMENTER|NEEDS_SUPERVISOR|BLOCKED|NOT_RUN",
    "head_sha": "<sha-or-null>",
    "merge_readiness_path": "<path-or-null>"
  },
  "authoritative_artifacts": [],
  "supporting_artifacts": [],
  "warnings": [],
  "blocking_reasons": [],
  "unknowns": [],
  "operator_authority": {
    "merge": false,
    "close_pr": false,
    "mark_ready": false,
    "force_push": false,
    "delete_branch": false
  },
  "chain_of_custody": {
    "parent_bundle_ids": [],
    "created_at": "<iso8601>",
    "skill_version": "2.0.0"
  }
}
```

This schema replaces the legacy `TP-PRPS-<n>-HANDOFF-<seq>` / seven-fixed-artifact
bundle previously documented in this tree's `handoff-contract.md` and
`handoff-to-prms-contract.md`. It carries no fixed artifact count or fixed
`authoritative_artifacts` list — the artifacts that exist are whatever the
actual run produced, not a mandated seven.

The receiving side of this contract is
[`../merge/handoff-from-prps-contract.md`](../merge/handoff-from-prps-contract.md).

## 10. Canonicality ruling

`docs/03-reference/pr-pipeline/prep/**` and `docs/03-reference/pr-pipeline/merge/**`
are the canonical PR-pipeline reference-contract surfaces for
`pr-prep-specialist`, by explicit ruling of
TP-DMX-PR-PREP-SPECIALIST-V2-001-R1. `docs/pr_prep/**` and `docs/pr_merge/**`
are compatibility surfaces only: they carry pointer stubs into this tree
and must not define independent behavioral semantics. Repository history
alone (commit recency, placement-policy allowlisting) did not prove
exclusive prior canonicality either way; this file records the ruling as a
decision, not a rediscovered fact.

No runtime code (`src/dopemux_pr_merge_specialist/**`, the actual wired
`pr-merge-specialist` implementation) consumes this documentation tree or
`docs/pr_prep/`/`docs/pr_merge/` — confirmed by direct grep for
`source_skill`, `handoff_id`, and PRPS-specific tokens, zero hits. This
documentation is reference/operator material, not a code adapter surface.
