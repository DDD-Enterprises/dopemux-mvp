---
id: BRAND_SYSTEM
title: Brand System
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-02'
last_review: '2026-04-02'
next_review: '2026-07-01'
prelude: Brand System (explanation) for dopemux documentation and developer workflows.
---
# BRAND_SYSTEM

## 1. Purpose

This document defines the dopemux experience layer: voice, naming, interaction style, and operator-facing presentation.

It does not define architecture, runtime authority, or system boundaries.

## 2. Voice And Tone

- Write for operators, not spectators.
- Prefer direct statements over explanation-heavy prose.
- Use plain technical language.
- Be calm, specific, and unsentimental.
- Default to command, status, result, and next action.
- Avoid hype, jokes, mascot language, and visionary framing.
- Avoid vague reassurance such as "all set" or "everything looks good" unless backed by evidence.

### Tone rules

- Good: "Bridge health check failed on port 3016."
- Good: "Started indexing for current workspace."
- Good: "Task not routed. Missing required project id."
- Bad: "Your workflow is now supercharged."
- Bad: "Something went wrong. Please try again."

## 3. Naming Conventions

- Prefer short, hard-edged names over abstract platform language.
- Use `dopemux` as the primary product name in operator-facing surfaces.
- Use lowercase monospace for commands, env vars, paths, and identifiers.
- Use Title Case for document headings and dashboard labels.
- Use verbs for commands and nouns for entities.
- Prefer one canonical operator term per action. Do not alternate between synonyms in the same surface.

### Naming rules

- Commands should read as actions: `start`, `status`, `health`, `resume`.
- Status labels should be explicit: `healthy`, `degraded`, `blocked`, `unknown`.
- Prefer `operator`, `workspace`, `run`, `task`, `service`, `route`, `health`, `context`.
- Avoid inflated terms such as `magic`, `brain`, `autonomous`, `smart`, `seamless`, `next-gen`.
- Avoid decorative renaming of normal actions. Use `delete` only when something is actually deleted, `archive` only when it is preserved, and `retry` only when a prior attempt is known.

## 4. CLI Interaction Style

- The CLI should feel procedural, not conversational.
- Lead with the result, then the minimum context needed to act.
- Prefer stable, scannable output over personality.
- Keep success output short.
- Keep failure output precise and actionable.
- Show exact identifiers, paths, ports, and commands when relevant.

### Output shape

- One-line success by default.
- Multi-line output only when listing state, blockers, or next steps.
- Use consistent labels when structure helps: `Status:`, `Reason:`, `Next:`.
- Prefer bullets or aligned lists over dense paragraphs.
- Preserve deterministic ordering in lists and tables.

### CLI copy rules

- Use imperative help text: "Start local services." not "Starts up everything for you."
- Prefer "not started" over "inactive" when the distinction matters.
- Prefer "missing" over "not found" for required local inputs.
- Prefer "blocked" when an operator action is prevented by a gate.
- Prefer "unknown" when state cannot be proven.

## 5. Error And Feedback Style

- Errors must identify what failed, where it failed, and what the operator can do next.
- Do not hide uncertainty.
- Do not report success before the check has completed.
- Do not soften critical failures with casual phrasing.
- Warnings should indicate degraded but still readable state.
- Success messages should confirm only what was actually done.

### Error rules

- Include the failing surface when known: command, path, service, port, endpoint, or file.
- Include the missing prerequisite when known.
- Keep remediation concrete.
- Preserve operator trust by separating observed failure from inferred cause.

### Preferred patterns

- `Failed: task-orchestrator health check returned 503.`
- `Blocked: missing workspace id.`
- `Warning: ConPort reachable, but decision history query timed out.`
- `Started: MCP services for current workspace.`
- `Unknown: dashboard state could not be verified.`

## 6. UI And Dashboard Visual Language

This applies only where operator dashboards or visual surfaces exist.

- Design for operational reading, not brand theater.
- Prioritize signal density, legibility, and state contrast.
- Use restrained color with clear meaning.
- Make the primary view feel like a control surface, not a marketing site.

### Visual rules

- Backgrounds should be quiet and low-gloss.
- Use color to encode state, not decoration.
- Green means healthy or complete.
- Yellow means degraded, delayed, or attention needed.
- Red means failed, blocked, or urgent operator action required.
- Gray means inactive, unavailable, or unknown.
- Typography should be plain, compact, and easy to scan.
- Charts and panels should emphasize trend, threshold, and current state.
- Avoid oversized hero elements, soft gradients, glassmorphism, and ornamental motion.
- Motion, if present, should indicate refresh, transition, or changed state only.

### Dashboard copy rules

- Panel titles should be literal: `Service Health`, `Queue State`, `Recent Failures`, `Attention State`.
- Empty states should explain absence, not apologize for it.
- Prefer "No active alerts." over "You're all caught up!"
- Prefer timestamps and counts over qualitative summaries when both are available.

## 7. Consistency Rule

If a choice must be made between sounding polished and sounding exact, choose exact.

If a surface cannot prove status, label it `unknown`.
