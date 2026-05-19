---
id: mobile-tmux-tui-source-manifest
title: Mobile Tmux TUI Research Source Manifest
type: reference
owner: '@hu3mann'
author: codex
date: '2026-05-19'
prelude: Source manifest for TP-DMX-MOBILE-TUI-SPEC-001 research intake from Downloads.
last_review: '2026-05-19'
next_review: '2026-08-17'
---
# Source Manifest

This manifest records the local research inputs used by
`TP-DMX-MOBILE-TUI-SPEC-001`. These files are research inputs and derived
guidance only. They do not outrank runtime code, config, schema, tests, active
entrypoints, or repo-truth authority docs.

## Intake Result

| Normalized artifact | Original file | SHA256 | Size | Method | External citations | Redaction / conversion warning | Classification |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| `01-mobile-blink-ssh-constraints.md` | `/Users/hue/Downloads/deep-research-report 15.md` | `15ebfbe00f8a6a968a64d2c8de5a53af9e4289b7bab2250ad25e82dc66a30432` | 22568 bytes | Markdown source summarized and normalized to repo-neutral ASCII. | Yes, source contains citation placeholders. | Secret-pattern scan found no credential material in selected source. | research_input |
| `02-tui-framework-architecture.md` | `/Users/hue/Downloads/deep-research-report 14.md` | `5757d34173f9931aeda6e33db8c3d0f89a984fca3f77c123bebed7843105dc6d` | 22735 bytes | Markdown source summarized and normalized to repo-neutral ASCII. | Yes, source contains citation placeholders. | Secret-pattern scan found no credential material in selected source. | research_input |
| `03-dopemux-cockpit-ux-spec.md` | `/Users/hue/Downloads/deep-research-report 13.md` | `e7550446b250eef4995dc605432342dc1c3c6a9010164479823e7e6105c809f2` | 37037 bytes | Markdown source summarized and reconciled against repo truth. | Yes, source contains citation placeholders. | Secret-pattern scan found no credential material in selected source. | research_input |

## Candidate Notes

The Downloads inventory also surfaced older or unrelated files, including
`Mobile-First Tmux for Dopemux.txt`, `tui-spec-v2.0a.md`, Cockpit design ZIPs,
and multiple older Deep Research reports. They were not ingested as the three
expected reports because content inspection showed the May 19 files above match
the requested categories directly:

- mobile / Blink / SSH constraints
- TUI framework and architecture
- Dopemux Cockpit UX specification

Files such as `/Users/hue/Downloads/ssh.pub` and
`/Users/hue/Downloads/zilliz-cloud-Dopemux-username-password.txt` appeared in
the broad filename inventory but were not inspected or ingested as research
inputs because they are not relevant to this packet and may contain credential
or key material.

## Repo Authority Inputs

The research was reconciled against these repo-truth and Cockpit/TUI surfaces:

- `AGENTS.md`
- `PROJECT.md`
- `ARCHITECTURE.md`
- `PM_PLANE.md`
- `SERVICE_CATALOG.md`
- `docs/03-reference/systems/system-boundaries.md`
- `docs/03-reference/systems/dopemux/system-dopemux.md`
- `docs/03-reference/systems/dopetask/system-dopetask.md`
- `docs/03-reference/systems/task-orchestrator/system-taskorchestrator.md`
- `docs/03-reference/systems/dopecon-bridge/system-dopeconbridge.md`
- `docs/03-reference/systems/dope-context/system-dopecontext.md`
- `docs/03-reference/systems/dopemux/tui-spec-v2-0a.md`
- `docs/03-reference/Dopemux Cockpit TUI Design System/ARCHITECTURE_SAFETY_OVERLAY.md`
- `docs/03-reference/Dopemux Cockpit TUI Design System/PM_IMPLEMENTER_COCKPIT_REDIRECTION.md`
- `docs/03-reference/Dopemux Cockpit TUI Design System/acceptance.md`
- `docs/03-reference/python-tmux-research.md`
- `docs/03-reference/systems/dashboard/tmux-dashboard-design.md`
- `config/mobile/tmux.mobile.conf`
- `.tmux.conf`
- `src/dopemux/ui/cockpit/render.py`
- `src/dopemux/ui/cockpit/app.py`
- `src/dopemux/ui/cockpit/runtime_contract.py`
- `src/dopemux/commands/cockpit_commands.py`
- `tests/unit/dopemux/ui/cockpit/test_cockpit_render.py`
- `tests/unit/dopemux/ui/cockpit/test_cockpit_command.py`

## Authority Note

If this manifest conflicts with runtime code, config, schema, tests, or active
repo-truth docs, the higher authority wins and this manifest should be treated
as stale derived guidance.
