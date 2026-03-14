## PM-Pack Canonical Integration Design

This design is derived from the PM workflow packs only.

## 1. Canonical ownership model

- `Leantime` is the canonical PM-facing record.
- `Task Orchestrator` is the canonical workflow-law, blocker, and next-action engine.
- Canonical decisions remain `Unresolved` from PM-pack evidence alone.
- Chronicle remains dual-ledger by design.

## 2. Non-negotiable operating policy

If a change affects legality, blockers, or next-step readiness, it must be processed through Task Orchestrator’s validated transition paths, then mirrored into Leantime.

This policy is required because:

- Leantime mostly does not enforce workflow legality centrally.
- Task Orchestrator does, but only on the transition-path tools.
- Both repos contain bypass paths that would otherwise undermine the intended split.

Evidence: `reports/leantime-pm-workflow-pack/02-workflow-and-transition-analysis.md`, `reports/task-orchestrator-pm-workflow-pack/02-workflow-legality-and-transition-analysis.md`, `reports/task-orchestrator-pm-workflow-pack/05-runtime-variants-and-local-split-brain-risks.md`.

## 3. Canonical write/read rules by domain

### PM-facing record state

Write canon: `Leantime`

Leantime remains the surface where projects, tickets, milestones, sprints, comments, and PM-visible record fields are ultimately reflected.

### Workflow legality

Write canon: `Task Orchestrator transition tools only`

Specifically, legality should be adjudicated through the sanctioned transition paths, not through raw role assignment.

### Blockers / dependencies

Write canon: `Task Orchestrator`

Leantime blocker and dependency signals should be treated as display/advisory state, not gate law.

### Next-action computation

Read canon: `Task Orchestrator`

Leantime may render the result, but should not originate a separate recommendation model.

### Decisions / progress

Use a split model:

- PM progress, reporting, and PM-visible progress narratives remain in `Leantime`.
- Workflow progression and readiness remain in `Task Orchestrator`.
- Do not force one system to become the canonical decision register without additional evidence.

### Chronicle / history / audit

Use a linked-dual-ledger model:

- `Leantime` for PM chronology.
- `Task Orchestrator` for workflow transition chronology.

## 4. Required integration guardrails

- Forbid direct role changes through Task Orchestrator `manage_items` if legality matters.
- Treat direct Leantime status/state mutation surfaces as reconciliation-only for workflow-significant fields unless they are mediated by Task Orchestrator.
- Pin Task Orchestrator deployment to a single runtime variant, ideally v3 `current`, to avoid internal runtime split-brain.
- Require stable cross-links between Leantime records and Task Orchestrator items so split history can be reconstructed.
- Do not infer canonical decisions from comments, notes, or canvas content alone.

## 5. Recommended minimal flow

1. A PM change request starts from Leantime or an external client.
2. If the request is workflow-significant, Task Orchestrator evaluates legality and readiness first.
3. Task Orchestrator computes blockers, next status, or next item as needed.
4. Accepted workflow outcomes are mirrored back into Leantime as PM-facing state.
5. Leantime retains the user-facing record; Task Orchestrator retains workflow justification and transition history.

## 6. Why this is the optimal PM-pack model

This model fits the evidence better than any single-owner design:

- It respects Leantime’s proven strength as the PM record owner.
- It respects Task Orchestrator’s proven strength as the workflow engine.
- It explicitly compensates for the fact that both repos expose bypasses.
- It avoids pretending that either repo already owns a complete decision register.

## 7. Explicit unresolved items

- Canonical decision ownership remains unresolved.
- A fully unified cross-system history model is not evidenced.
- Any integration that needs universal write-boundary legality must add policy or guardrails beyond what the repos enforce today.
