---
title: "ADHD Execution Model"
plane: "pm"
component: "dopemux"
status: "proposed"
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
1. **No Wall of Text**: Initial responses MUST NOT exceed 25 lines of text unless explicitly requested via `--verbose` or similar.
2. **One clear next step**: Every Supervisor output MUST highlight exactly ONE recommended next action, even if alternatives are provided.
3. **Mandatory Checkpoints**: Long-running planning or execution sequences MUST pause for user confirmation at least every 25 minutes or 5 major steps.
4. **No Silent Loops**: The system must never enter a retry loop without informing the user after the second attempt.

## FACT ANCHORS (Repo-derived)
- **Output Formatter**: `src/dopemux/ux/renderer.py` (to be verified).
- **Focus Timer**: `src/dopemux/ux/focus_timer.py` (to be verified).

## Open questions
- **Interruptibility**: How do we handle user interrupts during a long TaskX run?
  - *Resolution*: TaskX runs are atomic processes; we kill the process group on Ctrl+C and mark the artifact as "INTERRUPTED".

## Focus windows and checkpointing
- **Length**: Default 25 minutes (configurable).
- **Hard Checkpoint**: At T-0, the Supervisor MUST:
  1. Stop non-critical work.
  2. Save all state to ConPort/SQLite.
  3. Emit a "Focus Window End" bell/notification.
  4. Wait for user acknowledgement to continue or break.
- **"Pause and Checkpoint"**: Behavior available at any prompt. Commands: `wait`, `pause`, `checkpoint`.

## Progressive disclosure rules
To prevent overwhelm:
1. **Summaries First**: Show the high-level plan (3-5 bullets) before showing code.
2. **Diff Caps**: Don't dump 500 lines of diffs. Show the first 3 files and a count. "and 4 more files... (use --show-all to see)".
3. **Log Folding**: Tool outputs > 10 lines should be folded or truncated with a link to the full log file.

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
2. **Choice Test**: Trigger a scenario with multiple paths. Ensure UI highlights ONE primary path.
3. **Complexity Test**: Feed a massive 50-step plan. Ensure Supervisor rejects it with a complexity warning.
