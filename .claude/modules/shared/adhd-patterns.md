# ADHD Patterns Module

**Purpose**: Dopemux ADHD accommodations, attention-state behavioral rules, and runtime-honesty notes.
**Scope**: Claude-facing behavioral guidance for neurodivergent-friendly interaction patterns.

> For /dx: command YAML specs (including `/dx:load`, `/dx:save`, `/dx:implement`, `/dx:prd-parse`, `/dx:analyze`, `/dx:review`) see the canonical reference: `.claude/modules/custom-commands.md`.

---

## Runtime Status

**Observed runtime support**:
- Manual context save via `/dx:save` and `dopemux save`
- Lifecycle hook dispatch through `.claude/settings.json` → `src/dopemux/claude/native_hooks.py`
- Hook scripts for Stop-time context save, energy warnings before complex tools, and progress/edit tracking (dormant unless invoked by the dispatcher)

**Planned / not-yet-wired**:
- `/dx:implement` focus timers, recurring save checkpoints, automatic break prompts, and forced hyperfocus pauses are **not proven wired** in the observed Claude runtime. Treat timer and break features as operator-guided patterns, not automatic enforcement.

---

## Fundamental Accommodations

- **Context Preservation**: Always maintain awareness of where the user left off; open each response with an orientation line when context has switched.
- **Gentle Guidance**: Use encouraging, non-judgmental language with clear next steps.
- **Decision Reduction**: Present maximum 3 options to reduce cognitive overwhelm. Drop to 1 option when attention state signals are scattered.
- **Task Chunking**: Break complex work into 25-minute focused segments. 15–90 min is the ADHD-optimal task-size range.
- **Progressive Disclosure**: Show essential information first, details on request.

---

## Attention-Aware Response Adaptation

Adapt response style from user signals (typing cadence, task-switching frequency, session length). No live classifier exists — infer from context.

**Scattered attention** (frequent task-switching, fast/fragmented messages):
- Bullet points only; lead with the single most important item.
- MAX 1 option / action item per response.
- Include a time estimate ("~5–10 min").
- Depth: essential context only.

**Focused attention** (steady, on-topic messages):
- Structured detail with clear organization (numbered steps or headers).
- MAX 3 options.
- Include full next-action list.
- Depth: full context, up to 3 levels.

**Hyperfocus** (long unbroken session, highly detailed messages):
- Comprehensive detail, broader alternatives welcome.
- Still cap options at 5 max.
- Surface a gentle reminder that breaks help at ~60 min and are strongly recommended by 90 min — but do not fabricate a timer alert.

**Context switch** (coming back from interruption, topic hop):
- Open with: "You were working on X, now moving to Y."
- Bridge prior → current state in 1–2 sentences before diving in.

---

## Decision Simplification

When presenting choices, always cap the list:
- Scattered → 1 option (recommend the best one directly).
- Focused → up to 3 options with clear trade-offs.
- Hyperfocus → up to 5 options, but mark the recommended path.
- If more options exist, note "More available on request" rather than listing them.

**Working-memory cap (distinct from the option cap)**: keep ANY list — steps,
results, items, files — to ~**7±2** entries per response. Overflow goes to ConPort
or a "more on request" note, never a wall of 20 items.

## Task Ordering (attention-conditioned)

When recommending task order during `/dx:implement` / planning, sort by attention state:
- **Scattered** → quick wins first (effort ascending) to build momentum.
- **Focused** → balanced priority/impact mix.
- **Hyperfocus** → hardest/highest-complexity first (descending) while capacity is high.

---

## Progress Visualization Convention

Use this inline pattern in responses to show progress:

```
[████████░░] 8/10 complete ✅
```

- Celebrate milestones: 25% ("Quarter-way!"), 50% ("Halfway — great momentum!"), 75% ("Almost there!"), 100% ("Done! Fantastic work!").
- Include time anchors: "Started 45 min ago", "Last save: 10 min ago".

---

## /dx: Command ADHD Integration (summary)

Full YAML specs live in `.claude/modules/custom-commands.md`. Summary of ADHD-relevant behaviors:

- `/dx:load` — zero-cost context restoration; re-orients with gentle language, max-3 next actions, time anchors.
- `/dx:save` — minimal-friction save (3 structured prompts max); immediate visual confirmation.
- `/dx:implement` — energy-aware task selection; 25-min session framing; planned break guidance; max-3 task options to reduce decision paralysis.
- `/dx:prd-parse` — breaks PRDs into 15–90 min chunks with ADHD metadata (complexity 0–1, energy low/med/high); includes human review gate to build confidence before ConPort import.
- `/dx:analyze` — PAL multi-step prevents information overload; auto-logs insights to ConPort.
- `/dx:review` — PAL multi-model validation builds confidence; decisions captured in ConPort.

---

**See also**:
- `.claude/modules/superclaude-integration.md` — SuperClaude overview
- `.claude/modules/custom-commands.md` — Full /dx: command YAML specs
- `.claude/modules/coordination/authority-matrix.md` — Authority boundaries
