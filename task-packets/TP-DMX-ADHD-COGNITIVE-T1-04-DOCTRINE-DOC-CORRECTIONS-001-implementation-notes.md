---
id: TP-DMX-ADHD-COGNITIVE-T1-04-DOCTRINE-DOC-CORRECTIONS-001-implementation-notes
title: Tp Dmx Adhd Cognitive T1 04 Doctrine Doc Corrections 001 Implementation Notes
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-02'
last_review: '2026-06-02'
next_review: '2026-08-31'
prelude: Tp Dmx Adhd Cognitive T1 04 Doctrine Doc Corrections 001 Implementation Notes
  (explanation) for dopemux documentation and developer workflows.
---
# TP-DMX-ADHD-COGNITIVE-T1-04-DOCTRINE-DOC-CORRECTIONS-001 Implementation Notes

## Authority and Scope

- Worktree: `/Users/hue/code/dopemux-mvp/.worktrees/adhd-doctrine-doc-corrections-001`
- Branch: `codex/adhd-doctrine-doc-corrections-001`
- Base: `origin/codex/adhd-trendspanel-demo-gate-001`
- Primary checkout dirty state was not modified.
- Active task-orchestrator item: `16737f5d-102f-4b5d-8105-8bab50c7c891`
- Observed hook registration: `.claude/settings.json` dispatches lifecycle events through `src/dopemux/claude/native_hooks.py`.
- Observed hook scripts: `.claude/hooks/save_context.sh`, `check_energy.sh`, `log_progress.sh`, and `track_file_edit.sh` provide graceful best-effort context/energy/progress/edit signals.
- Unsupported active-doc claims observed: automatic 25-minute focus timers, 5-minute auto-save loops, 25-minute break reminders, and forced 90-minute hyperfocus breaks described as current runtime behavior.

## Initial Validation

- `python -m jsonschema -i task-packets/TP-DMX-ADHD-COGNITIVE-T1-04-DOCTRINE-DOC-CORRECTIONS-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` passed after packet creation.
- `python scripts/validate_adhd_doctrine_docs.py` failed before documentation edits, as expected, on unsupported active-doc automation claims and missing runtime/planned labels.

## Planned Slice

- Add deterministic active-doc stale-claim validator.
- Update active Claude doctrine surfaces so observed runtime support and planned/specification behavior are separated.
- Do not change runtime code or hook configuration.

## Final Proof

- Runtime code changed: NO.
- Hook registration changed: NO.
- Active doctrine docs now include explicit `Observed runtime support`, `Planned/specification behavior`, and `not proven wired` labels.
- Stale active-doc claim scan: `python scripts/validate_adhd_doctrine_docs.py` PASS.
- Task Packet schema: `python -m jsonschema -i task-packets/TP-DMX-ADHD-COGNITIVE-T1-04-DOCTRINE-DOC-CORRECTIONS-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` PASS.
- Whitespace diff: `git diff --check` PASS.
- Targeted pre-commit hooks over changed files: PASS after frontmatter normalization.
- Residual UNKNOWN: whether future or external Claude runtimes wire timers/save loops/break enforcement outside the inspected repo surfaces.
