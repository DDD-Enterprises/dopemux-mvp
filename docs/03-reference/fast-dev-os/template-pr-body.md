---
id: fast-dev-os-template-pr-body
title: Fast Dev OS — PR Body Template
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-23'
last_review: '2026-05-23'
next_review: '2026-08-21'
prelude: Canonical PR body template for Fast Dev OS packets — required sections (Summary, Scope, Validation, NOT_RUN, Residual Risks), forbidden phrases, and tone discipline.
---
# Fast Dev OS — PR Body Template

## Relationship to governance

This template **operationalizes** [`codex-authority-refresh.md`](../governance/codex-authority-refresh.md) and AGENTS.md §9 proof-and-finality contract; it **does not override** them.

## Lane

**L2** — PR body conventions affect every Fast Dev OS PR. Changes here propagate to all future packets.

## Required sections

Every Fast Dev OS PR body MUST contain these sections, in this order:

1. **Summary** — 2–5 bullets, plain prose, what changed and why.
2. **Scope** — one paragraph stating exactly what is in / out of scope. Cite the TP allowlist path count.
3. **Boundary discipline** — bullets listing the doctrine boundaries this PR honors (governance not overridden, secrets not embedded, etc.).
4. **Task Packet** — TP ID + path + series info + schema validation result + allowlist path count.
5. **Proof** — PROOF.json path + AGENTS.md §9 field-completeness confirmation.
6. **Validation** — exact command outputs with exit codes. Include PASS/FAIL/NOT_RUN buckets explicitly.
7. **NOT_RUN** — list of things not run, with reason for each.
8. **Residual Risks / UNKNOWNs** — list of risks with IDs and references.
9. **Series context** — predecessor + successor TP IDs (if any).
10. **Stacked PR note** (if applicable) — explain that diff includes parent packet content until parent merges.
11. **@codex review** — explicit reviewer request line.

## Template

```markdown
## Summary
- <bullet 1>
- <bullet 2>
- <bullet 3>

## Scope
<single paragraph stating in-scope / out-of-scope; cite allowlist path count>

## Boundary discipline
- <governance untouched / overridden — cite>
- <secrets / credentials / tokens — confirm clean>
- <known dangers carried forward as UNRESOLVED — cite UNKNOWN_CONFLICTING_STALE.md if applicable>
- <execution.agent enum compliance — cite RISK-SCHEMA if non-enum implementer>

## Task Packet
- ID: `<TP-DMX-...>`
- Path: `task-packets/generated/TP-DMX-...-*.json`
- Series: `<SERIES>` (parent: `<parent TP ID or null>`; final_packet: `<true|false>`)
- Schema: validates against `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` (PASS)
- Allowlist: <N> paths

## Proof
- Bundle: `proof/<series>/<TP>/PROOF.json`
- All AGENTS.md §9 required fields populated.

## Validation (exit code 0 unless noted)
- `<command 1>` — PASS
- `<command 2>` — PASS
- `<command 3>` — PASS

## NOT_RUN (with reason)
- `<not-run item 1>` — <reason>
- `<not-run item 2>` — <reason>

## Residual Risks / UNKNOWNs
- **<RISK-ID>**: <description>. <Mitigation or deferral>.
- **<RISK-ID>**: <description>. <Mitigation or deferral>.

## Series context
- Predecessor: `<TP-ID>` (state at PR creation time).
- Successor (planned): `<TP-ID>`.

## Stacked PR note (only if applicable)
This branch is stacked on `<parent branch>`. PR diff includes <N> packets until parent merges; after merge, diff narrows to <M> paths.

@codex review
```

## Forbidden phrases

The following words MUST NOT appear in a PR body **unless** explicitly justified with evidence in the same body:

- **"done"** — implies VERIFIED without proof. Use "complete per PROOF.json" with a link.
- **"complete"** — implies all NOT_RUN items are PASS. List NOT_RUN explicitly.
- **"no issues"** — implies absence of evidence is evidence of absence. List what was checked.
- **"100% secure"**, **"blazingly fast"**, **"production-ready"** — marketing language. Use evidence-based statements.
- **"perfect"**, **"flawless"**, **"bulletproof"** — promotional. Use measured evaluation.
- **"trust me"**, **"obvious"**, **"clearly"** — bypasses evidence requirements.

If you must use any of these words, immediately follow with citation:

> "complete per `proof/<series>/<TP>/PROOF.json` (commit SHA `<SHA>`, codereview status PASS, precommit status PASS)"

## Tone discipline

- **Lead with what changed**, not how impressive it is.
- **Prefer measured, evidence-based statements** ("validated on targeted path") over hype ("comprehensively validated").
- **Surface uncertainty explicitly** — "remaining uncertainty exists around X" beats glossing over Y.
- **Avoid sycophantic phrasing** — "this PR" beats "this excellent PR".
- **Cite line numbers and commands** rather than describing outcomes.

## Cross-references

- TP template: [`template-task-packet.md`](template-task-packet.md) / [`task-packet-template.json`](task-packet-template.json).
- PROOF template: [`templates-proof/proof-bundle-template.json`](templates-proof/proof-bundle-template.json).
- Validation library: [`validation-command-library.md`](validation-command-library.md).
- Authority order (AGENTS.md §2): [../../../AGENTS.md](../../../AGENTS.md).
- Governance: [`../governance/codex-authority-refresh.md`](../governance/codex-authority-refresh.md).

## Truth posture

> Never invent paths, commands, branches, PRs, tests, capabilities, or tool behavior. Never say done/complete/no issues without evidence. Distinguish observed vs inferred vs proposed vs unknown.
