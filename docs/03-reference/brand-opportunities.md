---
id: brand-opportunities
title: Brand Opportunity Map
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-19'
last_review: '2026-03-19'
next_review: '2026-06-17'
prelude: Draft opportunity map that surfaces additional surfaces and UX moments where Dopemux flair can be layered on top of the existing technical integrations.
---
# ━━━◆ Ø ◆━━━

Status: [LOGGED] Brand opportunity map

## Summary

- We already have spokes of the brand anchored in the CLI, dashboard, notifications, agents, and documentation. This reference collects the next set of surfaces that still feel utilitarian and proposes how Dopemux voice, colors, and chips can be layered in without altering contracts.
- Where possible the analysis points to the precise modules that still emit plain English logs or payloads so that each addition can stay audit-friendly while adding personality and UX clarity.

## Opportunity grid

| Surface | Files to inspect | Why it still feels plain | Brand/UX levers |
| --- | --- | --- | --- |
| Activity capture pipeline | `services/activity-capture/activity_tracker.py`, `services/activity-capture/event_subscriber.py`, `services/activity-capture/adhd_client.py` | These modules log status transitions, emit raw counts, and report upstream failure messages without chips, glyphs, or aftercare. | Prefix summaries with `StatusChip` and `Glyphs`, wrap errors/telemetry bursts with `VoiceEngine` aftercare/roasts so the log tail matches the same playful, empathetic tone as the CLI. |
| Workspace watcher | `services/workspace-watcher/main.py`, `event_emitter.py`, `app_detector.py`, `workspace_mapper.py` | Startup logging is functional but not Dopemux-branded; there is no copy that consoles the user when the watcher misses an app or restores it. | Replace the bare `logger.info` statements with `StatusChip.LIVE`/`StatusChip.AFTERCARE` notes, add halting aftercare copy (e.g., use `VOICE.get_aftercare()` on shutdown), and colorize the terminal output to match `theme` tokens. |
| ADHD dashboard backend | `services/adhd-dashboard/backend.py`, `services/adhd-dashboard/task_recommender.py` | Socket notifications and task recommendations are plain strings like “Hyperfocus protection triggered” or “Good time for regular development work”. | Inject bracketed chips (`[LIVE]`, `[BLOCKER]`), include brief aftercare lines when monitoring breaks, and reuse `VOICE` copy when broadcasting hyperfocus or decision logs so the web UI can render those chips with the same palette. |
| ADHD Engine API surface | `services/adhd_engine/api/routes.py` and downstream handlers that build API responses | All HTTP responses and errors are plain JSON (status text, description). Response bodies could subtly annotate status (`status_chip`, `tone`) without changing schemas. | Add optional metadata fields such as `voice_header` or `status_chip` so that clients (dashboard, voice commands) can render the same Dopemux language; align error logs with `VoiceEngine` outcomes and include `[BLOCKER]`/`[LOGGED]` tokens in 4xx/5xx payloads. |
| Workflow automation helpers | `src/dopemux/workflow/service.py`, `models.py`, `orchestration.py`, `service.py` | This new workflow stack currently trades on plain descriptions and logging (e.g., `logger.info("DecompositionCoordinator initialized")`). | Introduce `Glyphs` in log statements (e.g., `Glyphs.WORKFLOW`), output `StatusChip` prefixes to workflow state updates, and pipe the textual workflow briefings through `VoiceEngine` for the planner UI; also consider a `VoiceTone` stub for status channels. |
| Domain-level ADHD assistants | `services/adhd_engine/domains/attention/overwhelm_detector.py`, `.../task_enablement/decomposition_coordinator.py`, `.../break-suggester/engine.py` | These detectors work hard under the hood but export blunt strings like “Task exceeds 2h threshold” or “Paralysis pattern detected.” | Wrap detection reasons with `StatusChip` + `brand_text`, surface the severity or recommendation via `brand_list`, and align their emitted notifications with the same colors/chip labels consumed by the TUI and notifications so every alert feels like part of Dopemux’s voice. |
| Documentation signals | `docs/03-reference/brand-compliance-checklist.md`, `docs/flight_deck/*`, future feature guides | Flight deck docs and the checklist already have brand marks, but the broader reference docs and HOWTOs still read as plain referential text. | Layer the same chip notation, aftercare reminders, and `━━━◆ Ø ◆━━━` header where it makes sense, and link back to this opportunity map so writers know which modules should signal branded behavior. |

## Action recommendations

1. **Instrument a `brand_voice` helper for backend services.** Reuse `VoiceEngine`/`StatusChip` in the activity capture, workspace watcher, and dashboard backend so logs and WebSocket notifications carry the same palette—start with the functions listed above.
2. **Add metadata for brand tokens on API responses.** Introduce optional `status_chip` and `voice_header` fields (defaulting to `null`) in `services/adhd_engine/api/routes.py` so downstream presenters can render chips without altering payloads.
3. **Treat workflow orchestrator events as a Dopemux surface.** When `WorkflowKernel` emits or updates a run, prefix the console debug with glyphs and add voice-aftercare notes in the CLI viewer (maybe in the soon-to-exist `workflow` command panel).
4. **Create a follow-up doc/issue for QA.** Link this opportunity map from the tech radar so designers and devs can mark which suggestions are done, in progress, or deferred; include a rota for re-running the analysis as new modules emerge.

## Next steps

- Share this doc with the team as the current capture of unbranded surfaces.
- Pick one area (e.g., the workspace watcher or API responses) to prototype a branded interaction.
- Update the brand compliance checklist or related docs to cite the new metadata fields once implemented.
