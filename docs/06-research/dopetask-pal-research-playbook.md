---
id: dopetask-pal-research-playbook
title: Dopetask Pal Research Playbook
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-29'
last_review: '2026-03-29'
next_review: '2026-06-29'
prelude: Research playbook for using PAL in small, timeout-safe passes while designing
  and validating the next dopeTask architecture.
---

# dopeTask + PAL Research Playbook

## Purpose

This document captures a practical, low-timeout way to use PAL while designing and validating the next `dopeTask` architecture. It is optimized for the current situation:

- PAL requests can time out when prompts are too large
- Gemini CLI is good at repo exploration but can loop when the task is underspecified
- We want architecture/spec validation first, then implementation
- We want a clipboard-first TP workflow that eventually supports:
  - `dopetask tp import`
  - `dopetask tp execute`
  - high-level `dopetask execute --gemini`

---

## Executive summary

The best PAL strategy here is **small-pass orchestration**, not giant omnibus prompts.

Use PAL as a structured set of external validators:

1. **analyze** to map code structure and current behavior
2. **planner** to break the build into phases
3. **challenge** to attack the proposed design and expose weak assumptions
4. **thinkdeep** only for one hard design knot at a time
5. **consensus** only for a few high-leverage decisions that benefit from multiple model perspectives
6. **clink** only when you want a fresh isolated CLI subagent, not as the default for every question

The working rule is:

> PAL should validate one design decision per call.

Do **not** send the whole architecture, repo history, command UX, migration path, and degraded-mode philosophy in one request.

---

## What the PAL docs indicate

### 1. `analyze` is for understanding existing code structure
Use it to inspect the current repo, find architectural seams, and map how behavior actually works before proposing changes.

Use when you need answers like:
- Where does `tp series exec` really branch into worktree setup?
- Where is agent/model resolution happening now?
- Which modules already look like a Supervisor / Executor / Adapter split?

### 2. `planner` is incremental, not a one-shot mega planner
The tool is meant for step-by-step planning. That means it works best when the input is a narrow problem statement with a small number of constraints and a clear requested output.

Use it for:
- phased implementation order
- migration sequence
- feature slicing
- rollout dependencies

Do not use it to first discover the architecture and also validate the architecture and also produce the entire implementation strategy in one call.

### 3. `challenge` is ideal for design pressure-testing
This is the cleanest PAL tool for challenging a preferred design without dumping the whole repo into the prompt.

Use it for:
- “Should `tp import` default to clipboard when no file argument is passed?”
- “Should stale setup branches auto-delete or require explicit cleanup?”
- “Should import own overwrite semantics, or should execute own it?”

### 4. `thinkdeep` is for one hard problem, not all hard problems
Use it when there is a single architectural knot that really benefits from extended reasoning.

Good examples:
- degraded-mode escape hatch design
- how to distinguish setup-failure cleanup from forensic-state preservation
- how to formalize Supervisor vs Executor vs Adapter without overbuilding

Bad use:
- “here is the whole product strategy, think deeply about all of it”

### 5. `consensus` is for a few expensive decisions
Use this only for decisions where you really benefit from multiple model perspectives.

Examples:
- command surface naming (`tp execute` vs `execute --gemini`)
- whether generated prompt pipeline should be canonical with static shims only
- whether clipboard-first import should be implicit or explicit

Avoid using it for simple factual repo-tracing questions.

### 6. `chat` is useful, but lower leverage than the above for this task
Use it only for lightweight brainstorming or quick second opinions after you already have a concrete design question.

### 7. `clink` is useful later, not first
PAL’s `clink` bridge is valuable if you want to launch isolated CLI subagents like Gemini CLI, Codex CLI, or Claude Code without polluting your main session.

That makes it more relevant for:
- implementation isolation
- focused review or bug-hunt subagents
- side investigations

It is not the first tool to reach for when validating architecture.

---

## Timeout-safe operating model

### Golden rule
Each PAL request should answer **one design decision**.

### Recommended request size
For PAL requests, keep inputs to roughly:
- 1 design question
- 3 to 7 constraints
- 1 clear output format

### Keep these out of the prompt unless truly needed
- full repo backstory
- repeated history of earlier failures
- every possible feature idea
- giant architecture manifesto
- raw terminal transcript dumps

### Better pattern
Before every PAL call, Gemini should do this locally:
1. inspect repo truth itself
2. write a 3-line summary of the exact problem
3. reduce the problem to one question
4. send only that question to PAL

---

## Recommended PAL sequence for the current dopeTask architecture work

### Pass 1: validate the role split
**Tool:** `analyze` or `challenge`

Question:
- Is `Supervisor / Executor / Adapter` the right minimum role split for dopeTask?

Wanted output:
- yes/no with caveats
- minimum viable boundaries
- main risks

### Pass 2: validate clipboard-first import semantics
**Tool:** `challenge`

Question:
- Should `dopetask tp import` default to clipboard when no file is given?
- Should overwrite be explicit?

Wanted output:
- UX recommendation
- safety pitfalls
- recommended CLI contract

### Pass 3: validate execute-next semantics
**Tool:** `challenge` or `consensus`

Question:
- What should “next runnable TP” mean?
- What ordering and readiness rules should be deterministic?

Wanted output:
- queue selection contract
- edge cases
- tie-break strategy

### Pass 4: validate stale cleanup policy
**Tool:** `thinkdeep`

Question:
- When should setup-phase stale branches/worktrees auto-delete?
- When should failed state be preserved for forensic/debugging reasons?

Wanted output:
- clear cleanup policy split between setup failures and mid-run failures

### Pass 5: validate degraded recovery mode
**Tool:** `thinkdeep` or `challenge`

Question:
- When may a supervisor or CLI agent bypass TP execution and patch directly?
- What guardrails are required?

Wanted output:
- degraded-mode activation rules
- prohibited actions
- recovery completion criteria

### Pass 6: validate Gemini-specific behavior
**Tool:** `analyze` then `challenge`

Question:
- Should the current Gemini path be formalized as a deterministic shell-backed executor while true CLI integration is being built?

Wanted output:
- honest current-state description
- migration recommendation
- prompt contract guidance

---

## Concrete mini-prompts Gemini can send to PAL

### A. Role split validation
"Repo already has a deterministic JSON TP kernel. We are proposing three abstractions: Supervisor, Executor, and Adapter. Validate whether this is the right minimum split for a system that must support web supervisors, CLI supervisors, CLI executors, and deterministic shell fallback. Return: recommendation, risks, minimum viable boundary."

### B. Clipboard import semantics
"We want `dopetask tp import` to support clipboard-first JSON TP import when no file argument is passed. Overwrite of an already-recorded TP should be explicit, not silent. Challenge this UX. Return: risks, better alternatives if any, and a recommended CLI contract."

### C. Execute-next semantics
"We want `dopetask tp execute` to run the next runnable JSON TP without copy-pasting filenames. Dependencies must be satisfied and ordering must be deterministic. Propose the cleanest selection contract and call out edge cases."

### D. Cleanup policy
"`tp series exec` can fail because stale TP branches/worktrees remain from earlier setup failures. Challenge a cleanup policy that auto-cleans setup-only stale artifacts but preserves branches after meaningful execution or proof generation. Return: recommendation, dangers, safe boundary."

### E. Degraded recovery mode
"When the TP kernel itself is degraded, supervisors or CLI agents may need to patch directly instead of delegating back into broken TP execution. Challenge a degraded recovery mode with tight scope and targeted tests only. Return: activation criteria, guardrails, exit criteria."

---

## Recommended document set to produce after PAL validation

Once the small PAL passes are done, create these project docs:

### 1. Architecture spec
`docs/architecture/dopetask-supervisor-executor-adapter-spec.md`

Contents:
- role definitions
- execution modes
- degraded recovery mode
- queue semantics
- prompt pipeline rules

### 2. Command UX spec
`docs/specs/dopetask-clipboard-import-execute-spec.md`

Contents:
- `tp import`
- `tp series import --overwrite`
- `tp execute`
- `execute --gemini`
- model resolution behavior
- cleanup commands

### 3. Implementation plan
`docs/plans/dopetask-multi-mode-execution-plan.md`

Contents:
- phase order
- files/modules affected
- migration sequence
- test plan

---

## Recommended implementation phases

### Phase 1: kernel ergonomics
- explicit import overwrite/update support
- stale setup-branch/worktree cleanup
- explicit cleanup command

### Phase 2: clipboard-first TP UX
- `tp import` from clipboard
- packet write/update rules
- `tp execute` next-runnable selection

### Phase 3: model/agent resolution
- best/default Gemini model resolution
- visible model print at execution time
- config-backed behavior

### Phase 4: role abstraction
- formal Supervisor / Executor / Adapter interfaces
- make current Gemini path honest

### Phase 5: prompt pipeline normalization
- generated prompt pipeline becomes canonical
- static agent files become thin shims or exports

### Phase 6: real multi-provider execution
- Gemini CLI
- Codex CLI
- Claude Code
- later Copilot / Vibe / Jules as appropriate

---

## Validation checklist for the architecture

The design is acceptable only if all of these are true:

- JSON TP remains the canonical execution contract
- external web supervisors still work cleanly
- CLI supervisors can plan and execute without awkward manual loops
- CLI agent-executor mode is possible through a first-class command
- degraded kernel states do not cause recursive delegation deadlocks
- clipboard-first import and next-TP execution are deterministic and safe
- hidden git mutation is minimized and explicit
- stale setup artifacts no longer strand the user on branch-collision failures

---

## Practical advice for Gemini while PAL is in the loop

Gemini should:
- do local repo tracing itself first
- use PAL to challenge or validate one question at a time
- summarize each PAL output in 3 to 6 lines
- stop rereading the same file ranges unless a new hypothesis appears
- avoid giving PAL giant prompts containing the whole architecture

Gemini should not:
- use PAL as a giant dumping ground for every problem at once
- resend large terminal transcripts
- ask `planner` to do architecture discovery and final implementation sequencing in one shot
- call `consensus` for factual code-tracing questions

---

## Proposed next move

1. Run 5 to 6 narrow PAL passes using the sequence above
2. Summarize the validated design decisions
3. Draft the architecture spec document
4. Draft the command UX spec
5. Draft the phased implementation plan
6. Only then begin implementation packets

That sequence is the highest-signal path and the least likely to waste tokens, time, and your patience.

---

## Research notes

This playbook is based on the PAL MCP docs and README guidance indicating:
- `analyze` is for code structure and architecture understanding
- `planner` is incremental step-by-step planning
- `challenge` is for critical validation rather than agreement
- `thinkdeep` is for extended reasoning on one hard problem
- `consensus` orchestrates multiple model perspectives
- `clink` is the CLI-to-CLI bridge for external AI CLIs and subagents
- PAL clients may need higher timeout ceilings; the docs recommend at least five minutes, and note that setup scripts now configure a 20-minute timeout for Codex
