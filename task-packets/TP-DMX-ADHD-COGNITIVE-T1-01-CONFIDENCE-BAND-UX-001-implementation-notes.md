---
id: TP-DMX-ADHD-COGNITIVE-T1-01-CONFIDENCE-BAND-UX-001-implementation-notes
title: Tp Dmx Adhd Cognitive T1 01 Confidence Band Ux 001 Implementation Notes
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-02'
last_review: '2026-06-02'
next_review: '2026-08-31'
prelude: Tp Dmx Adhd Cognitive T1 01 Confidence Band Ux 001 Implementation Notes (explanation)
  for dopemux documentation and developer workflows.
---
# TP-DMX-ADHD-COGNITIVE-T1-01-CONFIDENCE-BAND-UX-001 Implementation Notes

## Authority and Scope

- Worktree: `/Users/hue/code/dopemux-mvp/.worktrees/adhd-confidence-band-ux-001`
- Branch: `codex/adhd-confidence-band-ux-001`
- Base: `origin/codex/adhd-hyperfocus-latch-001`
- Primary checkout dirty state was not modified.
- Active task-orchestrator item: `4f839f2a-8369-4c84-9724-f5cbfd594e5c`
- Live status surface observed: `src/dopemux/cli.py` `status --attention`.

## Initial Validation

- `python -m pytest tests/test_cli.py tests/test_attention_monitor.py`
  - Result: NOT_RUN/HUNG. The command emitted partial progress only and was terminated after exceeding the useful narrow baseline window.
- `python -m pytest tests/test_cli.py::TestCLI::test_status_command_all_metrics tests/test_cli.py::TestCLI::test_attention_emoji_mapping`
  - Result: PASS, `2 passed in 0.49s`
- `python -m pytest tests/test_attention_monitor.py`
  - Result: PASS, `35 passed in 1.36s`

## Planned Slice

- Add targeted failing tests for:
  - confidence-band renderer states: measured, inferred, low-confidence, calibrating, unavailable;
  - no renderer output equals a bare numeric or percent string;
  - `status --attention` focus score value includes confidence-band evidence label.
- Implement only the primitive and focused CLI wiring.

## Final Proof

- RED validation:
  - `python -m pytest tests/unit/test_confidence_band_ux.py tests/test_cli.py::TestCLI::test_status_command_all_metrics`
  - Result: FAIL as expected, 8 failures covering missing primitive module and missing `INFERRED` status output label.
- Implementation:
  - `src/dopemux/ux/confidence_band.py` adds a deterministic confidence-band renderer for measured, inferred, low-confidence, calibrating, and unavailable states.
  - `src/dopemux/ux/__init__.py` exports the primitive.
  - `src/dopemux/cli.py` routes `status --attention` focus score through the primitive as `INFERRED`.
- GREEN validation:
  - `python -m pytest tests/unit/test_confidence_band_ux.py tests/test_cli.py::TestCLI::test_status_command_all_metrics`
    - Result: PASS, `8 passed in 0.51s`
  - `python -m jsonschema -i task-packets/TP-DMX-ADHD-COGNITIVE-T1-01-CONFIDENCE-BAND-UX-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
    - Result: PASS
  - `python -m py_compile src/dopemux/ux/confidence_band.py src/dopemux/cli.py`
    - Result: PASS
  - `git diff --check`
    - Result: PASS
  - `python -m pytest tests/unit/test_confidence_band_ux.py tests/test_cli.py::TestCLI::test_status_command_all_metrics tests/test_cli.py::TestCLI::test_attention_emoji_mapping tests/test_attention_monitor.py`
    - Result: PASS, `44 passed in 1.88s`
- PAL codereview:
  - Tool/model: `mcp__pal.codereview`, `gpt-5-codex`
  - Result: PASS, no blocking issues.
  - Residual note: full `status --attention` fail-honest rewiring remains downstream; this slice targets the confidence-band primitive and focus-score wiring only.
- NOT_RUN:
  - Full `python -m pytest tests/test_cli.py tests/test_attention_monitor.py`: terminated after partial progress because it exceeded the useful narrow baseline window.
  - Live Redis/EventBus/provider/notifier/dashboard/shell-hook validation: not authorized by packet.
