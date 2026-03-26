---
id: LIVE_PILOT_GUARDRAILS
title: Live Pilot Guardrails
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-14'
last_review: '2026-03-14'
next_review: '2026-06-12'
prelude: Operational safety boundaries for the pr-prep-specialist pilot.
---
# Live Pilot Guardrails

To ensure safety during the live pilot, the following guardrails are strictly enforced:

1. **No Silent Escalation**: A case evaluated as `PACKAGE_ONLY` must never result in a live PR creation. A `DRAFT_FIRST` case must never create a final PR without explicit out-of-band human intervention.
2. **No Silent Adjacent-Work Import**: The skill must not automatically pull in stashes or sibling branch commits to fix an overlap. It may only warn and block.
3. **No Fake Completions**: The skill must not generate hallucinatory docs or changelogs to satisfy an obligation. If it's missing, it stays missing and is flagged.
4. **No Hidden PR Template Edits**: The canonical PR template structure must be respected. Sections cannot be arbitrarily deleted to hide missing information.
5. **No Mutation**: The pilot harness is strictly read-only regarding the local codebase. It must not execute `git commit`, `git rebase`, or similar mutating commands.
