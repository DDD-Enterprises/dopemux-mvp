---
id: CHECKLIST_EVIDENCE_RULES
title: Checklist Evidence Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-14'
last_review: '2026-03-14'
next_review: '2026-06-12'
prelude: Checklist Evidence Rules (explanation) for dopemux documentation and developer
  workflows.
---
# Checklist Evidence Rules

## Canonical Checklist Intents
- summary is accurate
- context is linked
- verification is documented truthfully
- verification gaps are documented
- risks are documented
- rollback is documented
- reviewer guidance exists
- high-risk notes included when required

## State Logic
- **`CHECKED`**: The corresponding section is present, sufficient, and the content is directly supported by upstream artifacts.
- **`UNCHECKED`**: The section is missing, weak, or the needed evidence is not yet present.
- **`BLOCKED`**: Adjacent-work ambiguity or obligation failure explicitly prevents truthful completion of this section.
- **`NOT_APPLICABLE`**: The section is not required for this specific change profile (e.g., High-Risk Notes on a docs-only change).
