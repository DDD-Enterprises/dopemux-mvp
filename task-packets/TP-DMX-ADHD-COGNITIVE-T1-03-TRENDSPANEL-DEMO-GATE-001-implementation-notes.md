---
id: TP-DMX-ADHD-COGNITIVE-T1-03-TRENDSPANEL-DEMO-GATE-001-implementation-notes
title: Tp Dmx Adhd Cognitive T1 03 Trendspanel Demo Gate 001 Implementation Notes
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-02'
last_review: '2026-06-02'
next_review: '2026-08-31'
prelude: Tp Dmx Adhd Cognitive T1 03 Trendspanel Demo Gate 001 Implementation Notes
  (explanation) for dopemux documentation and developer workflows.
---
# TP-DMX-ADHD-COGNITIVE-T1-03-TRENDSPANEL-DEMO-GATE-001 Implementation Notes

## Authority and Scope

- Worktree: `/Users/hue/code/dopemux-mvp/.worktrees/adhd-trendspanel-demo-gate-001`
- Branch: `codex/adhd-trendspanel-demo-gate-001`
- Base: `origin/codex/adhd-status-attention-fail-honest-001`
- Primary checkout dirty state was not modified.
- Active task-orchestrator item: `113a7e3f-4005-4feb-9c8f-be54b06f86d8`
- Live dashboard surface observed: `src/dopemux/ui/dashboard.py` `TrendsPanel`.
- Current live default observed: `TrendsPanel` reactive histories initialize from demo constants without checking `app.demo`.

## Initial Validation

- `python -m pytest tests/unit/test_dashboard_operator_ui.py`
  - Result: PASS, `4 passed in 0.12s`
- Plain `TrendsPanel()` inspection:
  - Result: demo histories are present by default.

## Planned Slice

- Add targeted failing tests for:
  - default/live TrendsPanel does not expose demo histories;
  - unavailable live trend rows render fail-honest no-signal text;
  - explicit demo application still uses demo histories.
- Implement only TrendsPanel demo gating and render behavior.

## Final Proof

- RED validation:
  - `python -m pytest tests/unit/test_dashboard_operator_ui.py`
  - Result: FAIL as expected, `2 failed, 4 passed`; plain `TrendsPanel()` exposed demo histories and `apply_demo_trends()` did not exist.
- GREEN validation:
  - `python -m pytest tests/unit/test_dashboard_operator_ui.py`
  - Result: PASS, `6 passed in 0.17s`
- Packet schema:
  - `python -m jsonschema -i task-packets/TP-DMX-ADHD-COGNITIVE-T1-03-TRENDSPANEL-DEMO-GATE-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
  - Result: PASS; jsonschema CLI deprecation warning only.
- Syntax:
  - `python -m py_compile src/dopemux/ui/dashboard.py`
  - Result: PASS
- Diff hygiene:
  - `git diff --check`
  - Result: PASS
- PAL codereview:
  - Result: PASS, no findings.
  - Residual uncertainty: live historical trend retrieval remains `UNKNOWN` because no runtime endpoint contract was found; live mode fails honest instead of inventing one.
- Precommit:
  - Initial run updated this notes file with required frontmatter; all other hooks passed.
  - Final rerun result: PASS across all configured hooks for touched files.
