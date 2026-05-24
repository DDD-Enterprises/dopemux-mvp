---
id: fast-dev-os-template-audit-prompt
title: Fast Dev OS — Audit Prompt Template
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-23'
last_review: '2026-05-23'
next_review: '2026-08-21'
prelude: Standard shape for an auditor's review prompt. Used by Gemini (per gemini-auditor-prompt.md) or any second-model audit pass to surface contradictions, missing evidence, and unresolved gaps between implementer claims and live repo state.
---
# Fast Dev OS — Audit Prompt Template

## Relationship to governance

This template **operationalizes** [`codex-authority-refresh.md`](../../governance/codex-authority-refresh.md); it **does not override** that layer.

## Lane

**L0–L6 (audit any lane)** — but audit is mandatory for L3+, optional for L0–L2.

## When to use

After the implementer emits their PROOF.json + implementation report, and before the operator makes an acceptance decision. The auditor consumes this template + the implementer's outputs and produces a findings register.

## Template (operator fills these slots)

```markdown
# Audit Prompt — <TP-ID>

## Audit target
- TP path: `<task-packets/generated/TP-*.json>`
- PROOF path: `<proof/<series>/TP-*/PROOF.json>`
- PR URL: `<https://github.com/DDD-Enterprises/dopemux-mvp/pull/NNN>`
- Implementer report path or inline: `<path or pasted content>`
- Lane: `<L0|L1|L2|L3|L4|L5|L6>`

## Authority for audit
Per AGENTS.md §2:
1. Latest user instruction
2. Active Task Packet
3. Runtime code / config / tests / compose / entrypoints  ← runtime beats docs
4. TRUTH_*.md / docs/03-reference/truth/*
5. RULES.md / PROJECT.md / ARCHITECTURE.md / SYSTEM_BOUNDARIES.md / PM_PLANE.md / SERVICE_CATALOG.md
6. Historical / generated / advisory / uploaded / external docs

If the implementer's claims contradict runtime code, runtime wins.

## Audit objectives (cover all)
1. Allowlist compliance — does the diff match the TP allowlist exactly?
   - Command: `git diff --stat origin/main..<branch>` cross-referenced with TP `commit.allowlist`.
2. PROOF.json AGENTS.md §9 completeness — are all required fields populated?
3. NOT_RUN scrutiny — are NOT_RUN items genuinely out of scope, or skipped to avoid effort?
4. Validation re-run — for the reproducible validations, run them locally; do exit codes match?
5. Truth posture — does the implementer claim things not visible in the repo? Did they invent paths/commands/branches/PRs/tests/capabilities?
6. Residual risk honesty — are residual risks enumerated, or smoothed over?
7. AGENTS.md §10 dangers carryover — are known dangers still UNRESOLVED, or silently dropped?
8. For L4+: does the change actually pass tests/lint/typecheck when re-run live?
9. For L6: are schema/contract migration safety properties preserved?
10. Security — any secrets / credentials / tokens / user-specific paths leaked?

## Findings format (per finding)
```
ID: F<N>-<SEVERITY>-<short-slug>
Severity: CRITICAL | HIGH | MEDIUM | LOW | OBSERVED
File: <path>:<line>
Evidence: <exact quote or diff snippet>
Claim audited: <what implementer claimed>
Audit verdict: <what audit found>
Remediation: <recommended fix OR NEEDS_OPERATOR_DECISION>
Confidence: exploring | low | medium | high | very_high | certain
```

## Verdict options
- **PASS** — safe to merge, no blocking findings.
- **PASS_WITH_NOTES** — safe to merge, some MEDIUM/LOW findings to track.
- **PARTIAL** — implementer claims partial completion that's honest and accurately scoped.
- **FAIL** — blocking findings; do not merge until remediated.
- **NOT_READY** — implementer's PROOF.json is incomplete or evidence base insufficient.

## Truth posture for auditor
> Never invent paths, commands, branches, PRs, tests, capabilities, or tool behavior. Never say PASS without evidence. Distinguish observed vs inferred vs proposed vs unknown.

> If a finding requires evidence you cannot reproduce, mark it INFERRED, not OBSERVED.

> Surface true contradictions, not just stylistic preferences. Cite line numbers and run output for every finding.

> Silence ≠ approval. If you have not examined an area, say so explicitly.

## Forbidden for auditor
- No author-code (audit is read-only).
- No rubber-stamp.
- No waiving NOT_RUN items into PASS.
- No accepting the work (acceptance is the operator's role; you advise).
- No revealing secrets / credentials / tokens you encounter (report exposure WITHOUT repeating values).

## Output
1. Findings register (table or list per the format above).
2. Per-objective coverage table (which of the 10 audit objectives were checked).
3. Verdict (one of the 5 options above).
4. Recommended next action for the operator.
```

## Truth posture (operator dispatching this prompt)

Pair this template with the implementer's PROOF.json + implementation report. Do not summarize the implementer's claims; give the auditor the raw artifacts and let them form their own conclusions.

## After audit

- Audit findings → [`template-acceptance-decision.md`](template-acceptance-decision.md) (operator decides).
- If audit verdict is FAIL / NOT_READY: send back to implementer for remediation; new implementation report required.
- If audit verdict is PARTIAL: document residual scope in acceptance decision.
- If audit verdict is PASS / PASS_WITH_NOTES: proceed to acceptance decision.
