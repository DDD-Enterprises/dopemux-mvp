---
id: PR_PREP_SPECIALIST_CONTRACT_V2
title: PR Prep Specialist Contract V2
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: Canonical V2 contract for pr-prep-specialist — mission, authority, risk lanes,
  conditional workflow, prep states, and the V2 handoff schema. Supersedes the
  legacy seven-step / LOW-MEDIUM-HIGH contract docs in this directory.
---
# PR Prep Specialist — Canonical V2 Contract

active Task Packet: TP-DMX-PR-PREP-SPECIALIST-V2-001 (packet content not
located in-repo as of 2026-08-11; see repair notes below)
design input: PR_PREP_SPECIALIST_V2_SPEC.md
design-input status: PROPOSED / supplied basis
implementation authority: Task Packet
Repository: `DDD-Enterprises/dopemux-mvp`
Risk of this contract migration: L2

This is the single canonical definition of `pr-prep-specialist` behavior. Other
files in `docs/pr_prep/` and `docs/pr_merge/` either point here, or cover a
narrower topic (e.g. base-branch detection heuristics, obligation severity)
that remains compatible with this contract without restatement. Where a
narrower doc conflicts with this one, this contract governs.

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

Risk lanes replace the legacy LOW/MEDIUM/HIGH risk model used elsewhere in this directory's older docs:

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

## 8. Handoff V2

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
bundle previously documented in `handoff-contract.md` and
`handoff-to-prms-contract.md`. It carries no fixed artifact count or fixed
`authoritative_artifacts` list — the artifacts that exist are whatever the
actual run produced, not a mandated seven.

The V2 handoff does not require the legacy seven PRPS artifact names.
If a current consumer still requires them, emit a compatibility adapter derived deterministically from canonical evidence rather than maintaining a second truth system.

## 9. Compatibility migration

The current repository contains duplicate PR-prep documentation surfaces.

Implementation must:

1. determine which paths are consumed by runtime/tooling/adapters;
2. select one canonical contract path (this file);
3. prevent independent hand-edited divergence;
4. either make compatibility copies deterministic or replace legacy copies with explicit pointers;
5. update the PR-merge receiving contract in the same content change;
6. scan adapters for forbidden legacy semantics:
   - exact seven-step requirement;
   - LOW/MEDIUM/HIGH risk;
   - `GO_DIRECT`;
   - PRPS-produced `MERGE_READY`;
   - mandatory seven-artifact bundle.

Archive material is historical and must not be rewritten merely to erase old terminology.

## 10. Acceptance

The V2 migration is acceptable only when:

- current repo consumers are inventoried;
- canonical and compatibility paths are explicit;
- old seven-step behavior no longer governs active adapters;
- risk lanes L0-L3 are used;
- ordinary main drift is resiliently classified;
- pre-push gate matches current repository policy;
- L2/L3 final-audit semantics are frozen-content only;
- proof-only successors do not trigger redundant audit;
- PR Prep cannot claim merge readiness independently;
- downstream handoff agrees with current PR Steward;
- changed paths remain allowlisted;
- relevant docs/governance tests and pre-commit pass;
- one independent audit passes against the frozen content head;
- exact-head CI and PR Steward are current;
- the PR remains unmerged pending explicit operator authority.

## Migration notes (2026-08-11)

No runtime code, hook, or `.claude/skills/` entry consumes `docs/pr_prep/` today —
it is operator/agent reference documentation only, not a wired skill. This
migration therefore replaces stale content in-place rather than touching a
code adapter layer.

### Repair status (2026-08-11, TP-DMX-PR-PREP-SPECIALIST-V2-001)

Two items remain **UNKNOWN** and block freezing a repaired content head:

1. **Task Packet not located.** `TP-DMX-PR-PREP-SPECIALIST-V2-001` was not
   found anywhere in this repository (`task-packets/`, full-tree grep) or in
   task-orchestrator (FTS search, zero hits). Its claimed allowlist — which
   would determine whether this file is in-scope — cannot be verified
   against evidence.
2. **A second, near-complete duplicate tree exists and was missed by the
   original consumer sweep**: `docs/03-reference/pr-pipeline/prep/**` and
   `docs/03-reference/pr-pipeline/merge/**` mirror `docs/pr_prep/**` and
   `docs/pr_merge/**` almost file-for-file (46/47 and equivalent content,
   only cosmetic kebab-case filename differences). Neither tree has a
   runtime/code consumer, a `docs/00-MASTER-INDEX.md` or `docs/INDEX.md`
   entry, or a docs-hygiene duplicate-detection flag naming one canonical.
   The `03-reference` copy's last edit (`09b648f176`, 2026-03-30) is more
   recent than `docs/pr_prep`'s pre-repair last edit (`bfdff9f481`), but that
   commit was a large multi-topic "consolidate everything" batch (mostly
   unrelated extraction/prompt work) — not a decision record naming
   `03-reference/pr-pipeline` canonical. This is circumstantial, not
   decisive. **Canonicality classification: UNKNOWN for both trees.**

Per the repair instruction, canonicality is not being invented. The
`docs/03-reference/pr-pipeline/{prep,merge}/**` tree has **not** been touched
by this migration and still carries every legacy split-brain defect this
contract retires (mandatory 7-step, fixed seven-artifact bundle,
`risk_hint` LOW/MEDIUM/HIGH, `GO_DIRECT`, PRPS-produced `MERGE_READY`) —
regardless of which tree turns out to be canonical, that tree needs the same
treatment this one received, once a canonical path is confirmed.

Files replaced with pointers to this contract:
- `skill-model.md` (superseded LOW/MEDIUM/HIGH risk model, six-step lifecycle)
- `workflow-sequence.md` (superseded mandatory 7-step ceremony)
- `operator-contract.md` (superseded fixed-workflow / fixed-artifact contract)
- `handoff-to-prms-contract.md` and `handoff-contract.md` (two competing legacy
  handoff schemas, both superseded by §8 above)

Files updated in place (compatible topic, incompatible field values):
- `branch-state-schema.md` (`risk_hint` LOW/MEDIUM/HIGH/UNKNOWN → `risk_lane` L0-L3)
- `consensus-gate-rules.md` (trigger/outcome vocabulary aligned to §6 audit states)
- `../pr_merge/handoff-from-prps-contract.md` (receiving contract updated to §8 schema)

Files left unchanged (false positives against the forbidden-token sweep, or
narrower topics that remain compatible with this contract):
- `base-branch-detection-rules.md`, `obligation-severity-rules.md` — use
  HIGH/MEDIUM/LOW as *confidence*/*severity* scales, not the PR risk model.
- `operator-review-form.md` — uses INFO/LOW/MEDIUM/HIGH/CRITICAL as pilot
  *override severity*, a different axis from PR risk lane; historical pilot
  artifact (TP-PRPS-008/009), not live operational contract.
- `docs/pr_merge/workflow-sequence.md`, `docs/pr_merge/operator-contract.md` —
  own internal `merge_ready`/`not_ready`/`blocked` status vocabulary for the
  separate `pr-merge-specialist` skill; not the PRPS-side `MERGE_READY`
  next-step token this contract forbids PRPS from emitting.
