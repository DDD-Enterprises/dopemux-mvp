---
id: fast-dev-os-template-task-packet
title: Fast Dev OS — Task Packet Template (annotated)
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-23'
last_review: '2026-05-23'
next_review: '2026-08-21'
prelude: Annotated walkthrough of the Fast Dev OS canonical Task Packet template — explains each field, the schema constraints, and the common pitfalls.
---
# Fast Dev OS — Task Packet Template (annotated)

## Relationship to governance

This template **operationalizes** [`codex-authority-refresh.md`](../governance/codex-authority-refresh.md) and the canonical schema at [`docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`](../spec/dopetask/dopetask-canonical-spec.json); it **does not override** them.

## Lane

**L2** — templates have downstream blast radius; changes here affect every subsequent Fast Dev OS packet.

## Companion file

Use this annotated walkthrough alongside the schema-valid skeleton at [`task-packet-template.json`](task-packet-template.json). Copy the skeleton, fill the slots, and validate against `dopetask-canonical-spec.json`.

## Field-by-field walkthrough

### Required root fields (per schema)

#### `id`
- Format: `TP-DMX-<SERIES>-<NNN>-<SLUG>` (e.g., `TP-DMX-FDOS-004-AUTHORITY-REFRESH`).
- Must be unique across the repo.
- Used as the filename for both the TP JSON and the PROOF directory.

#### `project`
- Always `"dopemux-mvp"` for this repo.

#### `target`
- One sentence describing what the packet installs/modifies/removes.
- Concrete and grep-able — reviewers should find the packet by searching for keywords here.

#### `repo_binding`
- `project_id`: `"dopemux-mvp"`
- `repo_marker`: `".dopetaskroot"` (the per-repo marker file)
- `origin_hint`: `"DDD-Enterprises/dopemux-mvp"`
- `require_identity_match`: `true` (always; prevents accidental cross-repo execution)

#### `series`
- `id`: short series identifier (e.g., `"DMX-FDOS"`, `"DMX-CODEX-REFRESH"`).
- `base_branch`: usually `"main"`.
- `parent_tp_id`: TP ID of the previous packet in the series, or `null` if this is the first.
- `final_packet`: `true` if this closes the series, else `false`.

#### `commit`
- `message`: conventional-commits format (`type(scope): description`).
- `allowlist`: **explicit list of all paths this commit may touch**. No globs. Every path must be enumerated.
- `verify`: list of validation commands (typically `json.tool`, `jsonschema`, `git diff --check`, packet-specific checks).

#### `pr`
- `title`: short (under 70 chars), matches commit message style.
- `body`: Markdown PR description. Required sections: Summary, Scope, Validation, NOT_RUN, Residual Risks.
- `base`: usually `"main"`.

#### `steps`
- Array of execution slices.
- Each step has `id` (e.g., `"S1"`), `task` (one-line description), and `validation` (list of pass criteria).
- May include `commands`, `expected_files`, `context_files`.

### Optional root fields

#### `invariants`
- List of constraints the implementer must not violate.
- Examples: "Do not modify runtime code", "Do not override governance docs", "No live provider calls".

#### `depends_on`
- List of TP IDs this packet depends on.
- Use `[]` if no dependencies. Phantom dependencies are forbidden — every declared dependency must actually exist.

#### `execution`
- `agent`: enum `{gemini, codex, vibe, shell}`. **Does not include `claude_code`** — use `"codex"` for Claude Code work and document the real implementer in PR body + PROOF `context_at_authoring.implementer`.
- `branch`: full branch name including prefix (e.g., `"codex/dmx-fdos-NNN-slug"`).
- `base_branch`: usually `"main"`.

#### `pal_chain`
- `enabled`: `true` if PAL chain should run.
- `steps`: array of PAL steps in order (e.g., `["analyze", "planner", "codereview", "precommit"]`).
- **Required** if `execution.agent == "gemini"` (per schema rule).

## Common pitfalls

1. **Forgetting `series.parent_tp_id`**: must be the previous packet's ID, not `null`, unless this is the first in the series.
2. **Globs in `commit.allowlist`**: not allowed; enumerate every path explicitly.
3. **`execution.agent` outside enum**: use `"codex"` for Claude Code / Grok / Jules / GitHub Copilot work and document actual implementer elsewhere.
4. **Missing `pal_chain.enabled: true` when `agent: "gemini"`**: schema-required.
5. **TP not validated against schema before committing**: run `python -m jsonschema -i <TP> <schema>` before staging.
6. **PR body lacks required sections**: see [`template-pr-body.md`](template-pr-body.md).

## How to use this template

1. Copy [`task-packet-template.json`](task-packet-template.json) to `task-packets/generated/TP-<SERIES>-<NNN>-<SLUG>.json`.
2. Fill each slot — do not leave placeholders.
3. Validate: `python -m jsonschema -i <TP-path> docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`.
4. Commit the TP and proceed with the packet's execution per AGENTS.md §4 lifecycle.

## Cross-references

- Schema: [`docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`](../spec/dopetask/dopetask-canonical-spec.json).
- Skeleton: [`task-packet-template.json`](task-packet-template.json).
- PR body template: [`template-pr-body.md`](template-pr-body.md).
- PROOF bundle template: [`templates-proof/proof-bundle-template.json`](templates-proof/proof-bundle-template.json).
- Validation library: [`validation-command-library.md`](validation-command-library.md).
- Lane taxonomy: [`project-constitution.md`](project-constitution.md).
- AGENTS.md §4 lifecycle: [../../../AGENTS.md](../../../AGENTS.md).

## Truth posture

> Never invent paths, commands, branches, PRs, tests, capabilities, or tool behavior. Never say done/complete/no issues without evidence. Distinguish observed vs inferred vs proposed vs unknown.
