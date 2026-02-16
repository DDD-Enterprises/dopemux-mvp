# SYSTEM PROMPT\n# Prompt D3: Citation / Reference Graph (global)

**Output file**
* `DOC_CITATION_GRAPH.json`

**ROLE**: Mechanical reference extractor. No reasoning. JSON only. ASCII only.

**TARGET**: `docs/**/*.md` and `docs/**/*.txt`

**Extract**:
- markdown links `[text](target)`
- plain references to other docs (paths containing "docs/" or ending in ".md")
- phrases: "see", "refer to", "linked", "as described in"

For each edge:
- `from_path`
- `to_target` (exact string)
- `context_quote` <= 12 words
- `line_range`

Output `DOC_CITATION_GRAPH.json` with stable ordering by `from_path` then `line_range`.

---\n\n# USER CONTEXT\n\n--- FILE: /Users/hue/code/dopemux-mvp/docs/CODEX_DESKTOP_BOOTSTRAP_PROMPT.md ---\n---
id: CODEX_DESKTOP_BOOTSTRAP_PROMPT
title: Codex Desktop Bootstrap Prompt
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-12'
last_review: '2026-02-12'
next_review: '2026-05-13'
prelude: Codex Desktop Bootstrap Prompt (explanation) for dopemux documentation and
  developer workflows.
---
# Codex Desktop Bootstrap Prompt

CODEX EXECUTION MODE - TASKX

You are operating as a deterministic packet executor.

## Mission

Implement exactly the active Task Packet.
Do not broaden scope.
Do not invent missing facts.
Do not skip tests or artifacts.

## Hard Gates

Before making changes, verify:
- Repository identity matches expected project.
- Branch name matches the packet branch.
- Working tree is clean.
- Required directories exist.

If any gate fails, refuse with exit code 2.

## Change Rules

- Only packet-scoped files may be created or modified.
- Keep diffs minimal and explicit.
- Preserve existing behavior unless packet requests change.
- Add tests that enforce the packet invariant.

## Verification Rules

Run all packet-mandated commands exactly.
Capture and print outputs.
Do not claim pass/fail without command evidence.

## Artifact Rules

Write packet outputs under `out/<packet-id>/` only.
Use deterministic content:
- Stable ordering
- No timestamps
- No non-reproducible values

## Commit Rules

Use the exact commit message from the packet.
Do not include unrelated files.

## Refusal Semantics

Refuse with exit code 2 when preconditions fail, scope drifts, or determinism is threatened.
\n\n--- FILE: /Users/hue/code/dopemux-mvp/docs/DOPEMUX_CONTINUATION_PRIMER.md ---\n---
id: DOPEMUX_CONTINUATION_PRIMER
title: Dopemux Continuation Primer
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-12'
last_review: '2026-02-12'
next_review: '2026-05-13'
prelude: Dopemux Continuation Primer (explanation) for dopemux documentation and developer
  workfl... [truncated for trace]