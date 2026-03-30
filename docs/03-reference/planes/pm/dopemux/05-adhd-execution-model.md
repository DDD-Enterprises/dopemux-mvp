---
title: ADHD Execution Model
plane: pm
component: dopemux
status: proposed
id: 05_ADHD_EXECUTION_MODEL
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-16'
last_review: '2026-02-16'
next_review: '2026-05-17'
prelude: ADHD Execution Model (explanation) for dopemux documentation and developer
  workflows.
---
# ADHD Cognitive Loop and UX Contracts

## Purpose
Dopemux UX constraints that preserve focus, reduce decision fatigue, and checkpoint progress. This document defines the "human interface" side of the Supervisor.

## Scope
- Output verbosity and progressive disclosure.
- Focus window management (Pomodoro-style).
- Decision complexity gating.
- Checkpointing and resumption behavior.

## Non-negotiable invariants

### INV-ADHD-001: Progressive Disclosure Caps Default Output
**Statement**
- MUST limit initial output to 25 lines (or top 3 items) unless verbose mode provides explicit override.

**Owner**
- Supervisor

**Scope**
- Applies to: per-turn
- Surfaces: `src/dopemux/ux/renderer.py`

**Evidence**
- FACT ANCHORS:
- `src/dopemux/ux/renderer.py` (to be verified)

**Enforcement**
- Mechanism:
- Runtime: Output buffer truncation just before TTY flush.

**Test**
- Local command(s):
- `dmux plan --verbose=false`
- Expected signals:
- Output is short. "...and 10 more items".
- Failure signature:
- Scrollback wall of text.
- Exit behavior:
- N/A.

**Failure modes**
- If violated:
- Impact: cognitive overload, detail blindness.
- Severity: S2 medium.
- Containment: Clear screen and summarize.

### INV-ADHD-002: No Choice Paralysis (1 Rec + 2 Alts)
**Statement**
- MUST present exactly ONE recommended next action (Primary), even if valid alternatives exist. Max 2 alternatives shown.

**Owner**
- Supervisor

**Scope**
- Applies to: per-turn
- Surfaces: `src/dopemux/supervisor/policy.py`

**Evidence**
- FACT ANCHORS:
- `src/dopemux/supervisor/policy.py` (TBD implied)

**Enforcement**
- Mechanism:
- Runtime: Policy engine filter forces ranking.

**Test**
- Local command(s):
- Trigger ambiguous state (e.g., git conflict).
- Expected signals:
- "Recommended: [A]. Alternatives: [B], [C]."
- Failure signature:
- "Please choose from A, B, C, D, E..."
- Exit behavior:
- Wait for user.

**Failure modes**
- If violated:
- Impact: stall, decision fatigue.
- Severity: S2 medium.
- Containment: Supervisor auto-picks "Safe" option if idle > 5m.

### INV-ADHD-003: Checkpointing and Session Cadence
**Statement**
- MUST halt for user confirmation at least every 25 minutes or 5 major steps.

**Owner**
- Supervisor

**Scope**
- Applies to: per-run
- Surfaces: `src/dopemux/ux/focus_timer.py`

**Evidence**
- FACT ANCHORS:
- `src/dopemux/ux/focus_timer.py` (to be verified)

**Enforcement**
- Mechanism:
- Runtime: Sentinel check in main dispatch loop.

**Test**
- Local command(s):
- `dmux run --mock-time=26m`
- Expected signals:
- "Focus Window ended. Break or Continue?"
- Failure signature:
- Runs for 2 hours uninterrupted.
- Exit behavior:
- Pause (SIGSTOP logic or internal loop wait).

**Failure modes**
- If violated:
- Impact: burnout, drift.
- Severity: S2 medium.
- Containment: Force break on next turn.

### INV-ADHD-004: Complexity Gating Reduces Chunk Size
**Statement**
- If complexity score > 0.6, MUST reject plan or force decomposition into smaller chunks.

**Owner**
- Supervisor

**Scope**
- Applies to: per-packet
- Surfaces: `src/dopemux/supervisor/complexity.py`

**Evidence**
- FACT ANCHORS:
- `src/dopemux/supervisor/complexity.py` (TBD check)

**Enforcement**
- Mechanism:
- Gate: Plan validator.

**Test**
- Local command(s):
- Submit 50-step plan.
- Expected signals:
- "Plan too complex (0.8). Decomposing..."
- Failure signature:
- Accepts massive batch job.
- Exit behavior:
- Refusal.

**Failure modes**
- If violated:
- Impact: context window overflow, error cascade.
- Severity: S1 high.
- Containment: Kill run, revert state.

### INV-ADHD-005: Fatigue Mode Prefers Safe Stops
**Statement**
- If fatigue signal detected (late hours, thrashing), MUST default to "Pause" or "Safe" actions, limiting high-risk writes.

**Owner**
- Supervisor

**Scope**
- Applies to: per-session
- Surfaces: `src/dopemux/ux/fatigue.py`

**Evidence**
- FACT ANCHORS:
- `config/limits.yaml` (working hours config)

**Enforcement**
- Mechanism:
- Runtime: Action filter removes `DELETE/OVERWRITE` verbs from options.

**Test**
- Local command(s):
- `dmux run --time "03:00"`
- Expected signals:
- "Late night mode active. Refactors disabled."
- Failure signature:
- Allows `rm -rf` at 3 AM.
- Exit behavior:
- Block action.

**Failure modes**
- If violated:
- Impact: regretful mistakes.
- Severity: S2 medium.
- Containment: Rollback via git.

## FACT ANCHORS (Repo-derived)

- **OBSERVED: Focus Sessions**: `services/task-orchestrator/app/services/task_coordinator.py` implements 25-minute focus sessions (`focus_session_duration = 1500`).
- **OBSERVED: Batch Limits**: `services/task-orchestrator/app/services/task_coordinator.py` enforces `max_batch_size = 3` for ADHD-friendly scheduling.
- **OBSERVED: Attention Monitoring**: `services/adhd_engine/core/engine.py` tracks `AttentionState` and `EnergyLevel` with real-time monitors.
- **OBSERVED: Accommodation Engine**: `services/adhd_engine/core/engine.py` generates specific recommendations for hyperfocus, energy mismatch, and complexity.
- **DOC-CLAIM: Output Formatting**: `src/dopemux/ux/renderer.py` is referenced but its truncation logic is not yet verified in the current subset.

## Open questions
- **Interruptibility**: How do we handle user interrupts during a long TaskX run?
- *Resolution*: TaskX runs are atomic processes; we kill the process group on Ctrl+C and mark the artifact as "INTERRUPTED".

## Focus windows and checkpointing
- **Length**: Default 25 minutes (configurable).
- **Hard Checkpoint**: At T-0, the Supervisor MUST:
1. Stop non-critical work.
1. Save all state to ConPort/SQLite.
1. Emit a "Focus Window End" bell/notification.
1. Wait for user acknowledgement to continue or break.
- **"Pause and Checkpoint"**: Behavior available at any prompt. Commands: `wait`, `pause`, `checkpoint`.

## Progressive disclosure rules
To prevent overwhelm:
1. **Summaries First**: Show the high-level plan (3-5 bullets) before showing code.
1. **Diff Caps**: Don't dump 500 lines of diffs. Show the first 3 files and a count. "and 4 more files... (use --show-all to see)".
1. **Log Folding**: Tool outputs > 10 lines should be folded or truncated with a link to the full log file.

## Complexity score gating
**Score Range**: 0.0 (Trivial) to 1.0 (Cognitive Overload)

**Computation Inputs**:
- Number of files touched.
- Number of distinct steps in the plan.
- New concepts introduced (jargon density).

**Gates**:
- **< 0.3**: Auto-proceed allowed.
- **0.3 - 0.6**: Ask for confirmation.
- **> 0.6**: **REJECT PLAN**. Require breaking it down into smaller Task Packets. "This plan is too complex (Score: 0.8). Please break it down."

## Result caps
- **Search**: `top_k=3` default.
- **File Diffs**: Max 50 lines per file in inline output.
- **Plan Steps**: Max 7 steps per packet.

## Supervisor behavior from ADHD signals
- **Signal**: "I'm tired" / "Brain fog" / Late night timestamp.
- **Response**: Switch to **Low-Cognitive-Load Mode**:
- Shorter outputs.
- More frequent checkpoints.
- Suggest only "safe" actions (no major refactors).
- **Signal**: Rapid-fire short queries (anxiety/confusion).
- **Response**: **PAUSE**. Suggest a "Breath Check". Summarize current status clearly.

## Failure modes
- **Output Flood**: Supervisor dumps 5 screens of text.
- *Mitigation*: Output buffer hard limit in `renderer.py`.
- **Decision Fatigue**: Supervisor offers 5 equal options.
- *Correction*: Policy engine must force a ranking and present only Top 1 + "Other options".
- **Context Switching**: User jumps between 3 different tasks.
- *Mitigation*: Supervisor detects context thrashing and prompts: "You seem to be switching tasks. Shall we park 'Task A' and officially switch to 'Task B'?"

## Acceptance criteria
1. **Verbosity Test**: Run a "Plan" command. Ensure output is < 25 lines.
1. **Choice Test**: Trigger a scenario with multiple paths. Ensure UI highlights ONE primary path.
1. **Complexity Test**: Feed a massive 50-step plan. Ensure Supervisor rejects it with a complexity warning.
