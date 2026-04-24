# RTE Pre-Run Hygiene Precommit

Date: 2026-04-23

## Requested Chain

- requested: `precommit:gpt-5.1-codex`
- executed: `precommit:gpt-5-codex`

## Provider Note

`gpt-5.1-codex` was not available in the active PAL model roster. `gpt-5-codex` was used as the closest available Codex precommit model.

## Validation Summary

The staged proof packet was materially truthful with two required qualifications:

- the final packet must state that `AGENTS.md` reappeared as unrelated local drift during validation
- commit readiness depends on isolating `AGENTS.md` again immediately before commit so the committed scope matches the proof packet

## Supporting Evidence

- staged packet size:
  - `13 files changed, 494 insertions(+)`
- full changeset reviewed through:
  - `/Users/hue/code/dopemux-mvp/zen_precommit.changeset`
- post-cleanup transient counts outside excluded env roots:
  - `.DS_Store`: `0`
  - `__pycache__`: `0`
  - `*.pyc`, `*.pyo`, `*.swp`: `0`

## Final Precommit Verdict

Acceptable for commit if and only if:

- `AGENTS.md` is isolated again immediately before commit
- the final report keeps the wider-than-intended cache cleanup visible
