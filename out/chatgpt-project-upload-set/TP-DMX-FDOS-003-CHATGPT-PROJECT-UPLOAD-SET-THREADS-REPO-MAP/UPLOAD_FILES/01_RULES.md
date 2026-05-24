---
id: rules
title: Rules
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-01'
last_review: '2026-05-01'
next_review: '2026-07-30'
prelude: Rules (reference) for dopemux documentation and developer workflows.
---
# RULES.md

This document defines the rules of engagement for the `dopemux-mvp` repository.

These rules are constraints on reasoning, implementation, validation, and completion. They are not suggestions.

---

## 1. Truth Hierarchy

When sources conflict, use this order:

1. Active Task Packet for the current work slice, for execution control, allowlists, validation obligations, stop conditions, and repo-changing scope
2. Runtime code, config, compose wiring, tests, and active entrypoints, for behavior claims and implemented system truth
3. Standard workspace truth artifacts: root `TRUTH_*.md` files when present, otherwise tracked equivalents under `docs/03-reference/truth/`
4. Canonical documentation: root `RULES.md`, `PROJECT.md`, `ARCHITECTURE.md`, `SYSTEM_BOUNDARIES.md`, `PM_PLANE.md`, `SERVICE_CATALOG.md`, and `SYSTEM_*.md` files when present, otherwise tracked equivalents under `docs/03-reference/`
5. Historical, advisory, exploratory, generated, external, or design docs

Active Task Packets control what the implementer may change and how the current slice is
validated. They do not authorize unsupported claims about runtime behavior.

Historical, advisory, exploratory, generated, external, or design docs are treated as
untrusted until runtime or source truth supports them.

Never let extracted artifacts outrank the runtime they describe.

---

## 2. Evidence-Based Reasoning

Required:

- Cite or name the artifact behind every success claim.
- Distinguish observed fact from inference.
- Mark unresolved truth as `UNKNOWN`.
- Preserve contradiction when contradiction exists.
- Prefer exact paths, commands, ports, service names, branch names, and PR URLs.
- Do not infer implementation from intent, README prose, naming, diagrams, or package presence.

Forbidden:

- “No issues” without checks.
- “Done” without evidence.
- Normalizing drift into a cleaner story.
- Promoting mirrors, adapters, shims, or proxies into authority.

---

## 3. System Boundary Discipline

Dopemux is a multi-system workspace, not a unified monolith.

Keep these authority slices distinct:

- `dopemux`: operator control, CLI, startup, routing, MCP/service coordination
- `dopetask`: external execution runtime reached through `scripts/dopetask`
- Leantime: passive PM metadata and project/ticket snapshots
- task-orchestrator: workflow-significant transitions and workflow views
- ConPort: structured decisions, progress, project context, custom data
- dope-memory: chronicle, historical receipts, evidence-preserving memory
- dope-context: code/docs indexing and retrieval
- dopecon-bridge: adapter, proxy, event transport, compatibility routing
- ADHD Engine: operator-support and cognitive-state surfaces
- Repo Truth Extractor: extraction/audit artifacts about the repo

Rules:

- Planes are not services.
- Services can span planes.
- Authority is per domain, not per service.
- Name the canonical writer before any write.
- Do not collapse PM, memory, retrieval, execution, bridge, agents, or operator support into one system.
- Do not treat bridge/proxy routes as source truth.
- Do not treat derived retrieval output as source truth.
- Do not treat mirrors as canonical unless the canonical writer and mirror receipt are explicit.

---

## 4. PM, Memory, Retrieval, And Bridge Rules

PM authority is split:

- metadata -> Leantime
- workflow transitions -> task-orchestrator
- decisions/progress/context -> ConPort
- historical receipts -> dope-memory

Memory and retrieval are split:

- chronicle -> dope-memory
- structured memory/context -> ConPort
- code/docs retrieval -> dope-context

Bridge rules:

- dopecon-bridge routes, adapts, proxies, and transports events.
- dopecon-bridge must not become task, workflow, decision, progress, PM, chronicle, or retrieval authority.
- Any bridge-mediated write must still identify the upstream canonical writer.

---

## 5. Task Packet Contract

All non-trivial implementation or repo-changing work requires a Task Packet conforming to `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`.

Required fields:

- `id`
- `project`
- `target`
- `repo_binding`
- `series`
- `commit`
- `pr`
- `steps`

Rules:

- No missing required fields.
- No undeclared fields.
- Every step includes `task` and `validation`.
- Every packet is repo-bound, series-bound, commit-sized, and verifiable.
- Task Packets control scoped execution and allowlists; they do not make unsupported runtime behavior claims true.
- If `execution.agent = "gemini"`, then `pal_chain.enabled = true` is required.
- Codex work follows `analyze -> planner -> codereview -> precommit` unless the packet requires a stricter PAL chain.

---

## 6. Worktree And Branch Discipline

Every TP series starts in a fresh dedicated worktree.

Before implementation in every TP, verify:

- repo identity matches `repo_binding`
- required repo marker exists
- current directory is inside the intended dedicated worktree
- checked-out branch matches TP / series scope
- work is not happening from the primary checkout unless explicitly authorized

If verification fails:

- stop
- report the mismatch
- do not modify files
- do not continue

End-state for completed implementation work:

- codereview complete
- precommit complete
- branch pushed
- PR opened
- dedicated worktree removed

If cleanup is blocked, report the blocker and mark the series incomplete.

---

## 7. PAL Execution Discipline

For non-trivial work, do not skip stage discipline.

Hard rules:

1. No planner before validated understanding.
2. No implementation before plan challenge.
3. No debug without concrete failure, contradiction, or uncertainty.
4. No consensus unless at least two credible approaches exist.
5. No precommit without codereview first.
6. No API guessing; use current API lookup when external behavior matters.
7. No docgen on unstable implementation.
8. Final completion requires an evidence ledger.
9. Final confidence must be `VERIFIED`.

Default chain:

`analyze -> thinkdeep -> challenge -> planner -> challenge -> codereview -> precommit -> challenge`

Minimum Codex chain:

`analyze -> planner -> codereview -> precommit`

Escalate when needed:

- `tracer`: call-flow ambiguity
- `debug`: broken or contradictory runtime behavior
- `testgen`: regression risk or coverage gap
- `secaudit`: auth, secrets, sensitive data, network exposure
- `docgen`: public interfaces, docs acceptance, gotchas
- `apilookup`: external API / SDK / OS behavior

---

## 8. Operational Safety

Required:

- Work in commit-sized slices.
- Run the smallest relevant validation after each slice.
- Inspect diffs before continuing.
- Reproduce bugs empirically before fixing.
- Use deterministic ordering and explicit ranking.
- Preserve idempotency and safe retries.
- Redact before storage and before promotion.
- Fail closed when authority, ownership, or safety is unresolved.

Forbidden:

- Opportunistic cleanup outside scope.
- Silent side effects.
- Duplicate writers for the same domain.
- Silent mirroring without receipts.
- Extraction runner execution unless explicitly instructed.
- Production-code edits in docs/research packets unless explicitly authorized.

---

## 9. Event And Data Rules

All durable state is event-shaped or evidence-backed.

Required event envelope:

- `id`
- `ts`
- `workspace_id`
- `instance_id`
- `type`
- `source`
- `data`

Promotion rules:

- Promote only decisions, task outcomes, errors, and workflow transitions.
- Redact before storage.
- Redact again at promotion.
- Use `event_id` for idempotency.
- Expect duplicates, retries, partial failure, and replay.

Storage rules:

- SQLite is canonical where declared.
- Postgres is a mirror where declared.
- SQLite must succeed independently.
- Postgres mirror writes must be idempotent and failure-tolerant.

---

## 10. Retrieval Rules

Phase 1 retrieval is deterministic and keyword-only.

Rules:

- No semantic magic in Phase 1.
- No LLM scoring in Phase 1.
- Ranking must be stable and explainable.
- Controlled boosts are Phase 2+ only.
- DopeContext owns code/docs retrieval.
- ConPort owns structured/semantic context and relationship surfaces where runtime proves it.
- Retrieval output is derived evidence, not source truth.

---

## 11. Output Contract

Default operator-facing output uses the ADHD contract:

- max Top-3 items
- always include `items`, `more_count`, and `next_token` when listing or summarizing state
- avoid large dumps
- avoid mixed signal/noise

Completion reports must include:

- slices completed
- validations run
- risks
- PR URL
- worktree path
- verified branch
- repo identity result
- cleanup status

No proof means not complete.

---

## 12. Drift Handling

Required:

- Acknowledge drift directly.
- Document docs-vs-runtime divergence.
- Preserve `UNKNOWN`, `split`, and `ambiguous` where truth is unresolved.
- Treat deprecated, duplicate, shadow, or hard-failing paths as risks.
- Do not narratively clean up runtime contradiction.

Known drift classes to watch:

- task-orchestrator runtime/package/port contradictions
- Serena canonical authority ambiguity
- agent authority ambiguity
- ConPort port/client split
- dope-memory vs working-memory-assistant overlap
- TaskX naming vs `dopetask` runtime
- legacy truth runner vs extractor v5
- bridge routes that appear authoritative but are not

---

## 13. Finality Standard

A task is complete only when:

- scope is satisfied
- required validations passed
- codereview passed
- precommit passed
- evidence ledger is complete
- residual risks are explicit
- final confidence is `VERIFIED`
- PR is opened when repo changes are involved
- worktree cleanup is complete or blocked with evidence

Anything less is incomplete, partial, or blocked.
