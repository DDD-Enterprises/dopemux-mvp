# RTE Pre-Run Hygiene Do-Not-Touch Ledger

Date: 2026-04-23

## Protected Surfaces

- `/Users/hue/code/dopemux-mvp/src/**`
- `/Users/hue/code/dopemux-mvp/services/**`
- `/Users/hue/code/dopemux-mvp/scripts/**`
- `/Users/hue/code/dopemux-mvp/tests/**`
- `/Users/hue/code/dopemux-mvp/compose.yml`
- `/Users/hue/code/dopemux-mvp/services/registry.yaml`
- `/Users/hue/code/dopemux-mvp/docs/03-reference/truth/**`
- `/Users/hue/code/dopemux-mvp/docs/03-reference/systems/system-boundaries.md`
- `/Users/hue/code/dopemux-mvp/docs/03-reference/planes/pm/pm-plane.md`
- `/Users/hue/code/dopemux-mvp/extraction/doctor/**`
- `/Users/hue/code/dopemux-mvp/extraction/v4/doctor/**`
- `/Users/hue/code/dopemux-mvp/extraction/repo-truth-extractor/v5/doctor/**`
- `/Users/hue/code/dopemux-mvp/extraction/repo-truth-extractor/v5/runs/**`
- `/Users/hue/code/dopemux-mvp/extraction/repo-truth-extractor/v5/latest_run_id.txt`
- `/Users/hue/code/dopemux-mvp/proof/**`
- `/Users/hue/code/dopemux-mvp/reports/**`

## Ambiguous But Preserved In Place

- `/Users/hue/code/dopemux-mvp/.claude/**`
- `/Users/hue/code/dopemux-mvp/.dopemux/**`
- `/Users/hue/code/dopemux-mvp/.conport/**`

Reason:

- these trees are ignored by git, but ignore status is not proof of irrelevance
- they may still encode operator context, chronicle state, or split-authority evidence
- they were treated as possible first-pass input exclusions only
