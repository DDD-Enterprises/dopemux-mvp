---
id: TP-DMX-REPO-EVIDENCE-ECONOMY-001
title: Repository evidence-economy repair
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-02'
last_review: '2026-08-02'
next_review: '2026-10-31'
prelude: Repository evidence-economy repair (reference) for dopemux documentation and developer workflows.
---
# Task Packet: TP-DMX-REPO-EVIDENCE-ECONOMY-001

## Repository evidence-economy repair

### Objective

Stop token-heavy audit recursion without weakening real safety gates.

This packet changes governance and local tooling so the default workflow becomes:

```text
deterministic preflight
→ one bounded implementer
→ relevant tests
→ frozen content head
→ one independent audit only when L2/L3
→ proof-only successor
→ CI and PR Steward
```

### IN

- Risk lanes L0-L3.
- One-final-audit policy.
- Deterministic handling of frontmatter, schema, proof, manifest, hash, and proof-only closure.
- Changed-contract preflight script and tests.
- Pre-commit integration.
- Resilient drift and overlap classification.
- Compact proof and handoff expectations.
- Cost-first routing language.

### OUT

- Runtime services or product behavior.
- Workflow YAML.
- Proof or Task Packet schema changes.
- Signer or credential policy.
- Production, migration, permissions, merge, closure, mark-ready, or destructive actions.
- Rewriting historical packets or proof bundles.

## Execution recommendation

```yaml
execution_recommendation:
  stage: implementation
  runner:
    preferred: Codex
    availability: PROPOSED
  agent:
    logical_role: governance_tooling_developer
    custom_agent: null
    authority_ceiling: allowlisted repository write; human-gated merge
  model:
    preferred: UNKNOWN
    effort: high
  fallback:
    runner: Claude Code
    model: sonnet
    trigger: Codex unavailable|substantive implementation failure
  audit:
    required: true
    runner: AGY
    model: <live-listed independent Gemini selector>
    independence: UNKNOWN until preflight
```

Reasons:

- Codex is suited to bounded tooling, tests, and PR execution.
- Exact selectors must be discovered live and recorded.
- AGY/Gemini is preferred for independent review of a Codex governance change.
- Claude Code Sonnet is the authorized fallback auditor.
- No audit runs before the final content head.

## Economy acceptance

Default model-call budgets:

| Lane | Default model calls |
|---|---:|
| L0 deterministic | 0 |
| L1 bounded | 1 implementer |
| L2 material | 1 implementer + 1 final auditor |
| L3 red lane | 1 implementer + 1 final auditor, plus explicit operator gate |

Exceptions require a recorded reason.

## Required deterministic preflight

Before first push:

```bash
python3 scripts/governance/validate_change_contract.py   --base origin/main   --head HEAD   --format text

pre-commit run --from-ref origin/main --to-ref HEAD
git diff --check
```

A hook that modifies a file must be rerun and pass cleanly.

## Stop conditions

Stop and return `NEEDS_SUPERVISOR` for:

- conflicting open PR changes to authority/security semantics;
- validator network or model dependency;
- weakening L2/L3 audit requirements;
- weakening operator gates;
- proof validation that accepts escaped paths or stale heads;
- runner/model provenance that cannot be identified;
- scope outside the allowlist.

Do not stop for ordinary main movement or non-conflicting overlap. Reharvest affected files.

## Terminal verdicts

Return exactly one:

```text
EVIDENCE_ECONOMY_READY_FOR_OPERATOR_MERGE_DECISION
EVIDENCE_ECONOMY_BLOCKED
EVIDENCE_ECONOMY_CONFLICTING_NEEDS_SUPERVISOR
EVIDENCE_ECONOMY_INVALID_EVIDENCE
```

No merge is authorized.
