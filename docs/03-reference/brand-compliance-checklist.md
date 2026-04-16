---
id: brand-compliance-checklist
title: Brand Compliance Checklist
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-18'
last_review: '2026-03-18'
next_review: '2026-06-16'
prelude: Brand Compliance Checklist (reference) for dopemux documentation and developer
  workflows.
---
# ━━━◆ Ø ◆━━━

Status: [LOGGED] Brand compliance reference

## Dopemux Production Brand Compliance Checklist

This checklist is the production release checklist for operator-facing Dopemux CLI and TUI surfaces.

Authority order for production surfaces:
- Visual and layout authority: [CLI UX Design Spec](../04-explanation/branding/cli-ux-design-spec.md)
- Voice authority: [src/dopemux/voice/core.py](../../src/dopemux/voice/core.py) and [services/shared/brand_voice.py](../../services/shared/brand_voice.py)
- Moodboard and non-runtime flavor guidance: [dopemux-brand-system.md](../04-explanation/branding/dopemux-brand-system.md)

- Tokens come from [src/dopemux/ui/theme.py](../../src/dopemux/ui/theme.py), [src/dopemux/ui/dopemux.tcss](../../src/dopemux/ui/dopemux.tcss), [src/dopemux/ui/voice.py](../../src/dopemux/ui/voice.py), or [ui-dashboard/src/theme.ts](../../ui-dashboard/src/theme.ts).
- No hardcoded hex colors live outside the approved theme files.
- Rich CLI and TUI surfaces use `styled_panel()`, `styled_table()`, semantic style names, or `StatusChip` helpers instead of raw `Panel()` and `Table()` styling.
- User-facing copy passes `validate_output()` directly or through a shared fail-closed helper.
- Notifications and alerts use bracket-chip notation such as `[LIVE]`, `[BLOCKER]`, `[LOGGED]`, or `[AFTERCARE]`.
- ADHD recommendations keep one clear next step visible and avoid filler such as `maybe`, `probably`, or `as an AI`.
- Agent prompts prepend a Dopemux voice header before the task-specific instructions.
- Mobile, desktop, tmux, and dashboard surfaces reuse shared voice adapters rather than inventing local phrasing rules.
- Flight deck docs begin with the `━━━◆ Ø ◆━━━` brand mark and expose status with chip notation.
- Successful completion flows end with aftercare copy instead of generic `done` messaging.
- Phase verification includes `python scripts/brand_lint.py` plus surface-specific compile, build, or test checks.
