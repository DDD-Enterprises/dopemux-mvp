---
id: PROFILE_EPIC_COMPAT_SHIMS_VERIFICATION_2026_02_06
title: Profile Epic Compat Shims Verification 2026 02 06
type: explanation
owner: '@hu3mann'
author: Codex
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-02-20'
status: final
prelude: Verification evidence for ConPort packet rows 2, 3, and 4 compatibility-deliverable module closure.
---
# Profile Epic Compat Shims Verification (2026-02-06)

## Scope

Verify packet rows `2`, `3`, and `4` deliverable module surfaces are present and test-covered:

1. Epic 2 deliverables: `signal_collectors.py`, `scorer.py`
2. Epic 3 deliverables: `session_manager.py`, `claude_manager.py`, `switcher.py`
3. Epic 4 deliverables: `statusline_integration.py`, `suggestion_engine.py`, `analytics.py`, `migration.py`

## Implementation Evidence

1. Added compatibility module paths:
   - `/Users/hue/code/dopemux-mvp/src/dopemux/analytics.py`
   - `/Users/hue/code/dopemux-mvp/src/dopemux/signal_collectors.py`
   - `/Users/hue/code/dopemux-mvp/src/dopemux/scorer.py`
   - `/Users/hue/code/dopemux-mvp/src/dopemux/session_manager.py`
   - `/Users/hue/code/dopemux-mvp/src/dopemux/claude_manager.py`
   - `/Users/hue/code/dopemux-mvp/src/dopemux/switcher.py`
   - `/Users/hue/code/dopemux-mvp/src/dopemux/statusline_integration.py`
   - `/Users/hue/code/dopemux-mvp/src/dopemux/suggestion_engine.py`
   - `/Users/hue/code/dopemux-mvp/src/dopemux/migration.py`
2. Added targeted shim verification tests:
   - `/Users/hue/code/dopemux-mvp/tests/unit/test_profile_epic_compat_shims.py`

## Verification Commands

1. `pytest -q --no-cov tests/unit/test_profile_epic_compat_shims.py`
   - Result: `14 passed`
2. `python -m py_compile src/dopemux/analytics.py src/dopemux/signal_collectors.py src/dopemux/scorer.py src/dopemux/session_manager.py src/dopemux/claude_manager.py src/dopemux/switcher.py src/dopemux/statusline_integration.py src/dopemux/suggestion_engine.py src/dopemux/migration.py`
   - Result: success (no syntax errors)

## Conclusion

Rows `2`, `3`, and `4` compatibility deliverables are now materially implemented and verified in runtime code and tests.
