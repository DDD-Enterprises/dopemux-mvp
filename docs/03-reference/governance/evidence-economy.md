---
id: evidence-economy
title: Evidence Economy
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-02'
last_review: '2026-08-02'
next_review: '2026-10-31'
prelude: Evidence Economy (reference) for dopemux documentation and developer workflows.
---

# Evidence Economy

Canonical policy for economical, fail-closed repository execution.

## Default workflow

```text
deterministic preflight
→ one bounded implementer
→ relevant tests
→ frozen content head
→ one independent audit only when L2/L3
→ proof-only successor
→ CI and PR Steward
```

## Risk lanes

| Lane | Meaning | Default model calls | Independent audit |
|---|---|---:|---|
| L0 deterministic | Frontmatter, hashes, manifests, packaging, schema validation, inventories, proof-only closure | 0 | NOT_REQUIRED |
| L1 bounded | Small isolated code/docs; no authority/security/workflow/schema/public-behavior impact | 1 implementer | optional |
| L2 material | Runtime, public interfaces, governance, routing, proof/audit logic, schemas, significant refactor | 1 implementer + 1 final auditor | required on frozen content head |
| L3 red lane | Security/auth, credentials, permissions, production, migrations, destructive ops, authority boundaries, CI trust, signer policy | 1 implementer + 1 final auditor + operator gate | required; different family/runtime |

When uncertain, use the higher lane and record why. Exceptions to model-call budgets require a recorded reason.

## One-final-audit policy

- No model audits of intermediate commits.
- L2/L3: exactly one independent audit after the content head is frozen.
- Proof-only successors do **not** re-audit unchanged content. Validate schema, signature, ancestry, and path closure deterministically (`scripts/governance/validate_change_contract.py --proof-only`).
- One repair attempt per substantive model failure, then switch family or escalate.
- Bounded metadata failures (frontmatter, schema fields, packaging) are repaired in the active packet with deterministic checks — do not spawn recursive Task Packets.

## Deterministic preflight (required before first push)

```bash
python3 scripts/governance/validate_change_contract.py --base origin/main --head HEAD --format text
pre-commit run --from-ref origin/main --to-ref HEAD
git diff --check
```

A hook that modifies files must be rerun and pass cleanly before push.

## Drift and overlap

Ordinary `main` or PR movement is not a blanket stop. Reharvest affected files only.

Overlap classes: `IDENTICAL`, `SUBSET`, `SUPERSET`, `COMPATIBLE`, `CONFLICTING`, `UNKNOWN`.

`CONFLICTING` authority or security semantics → stop affected-file editing and escalate `NEEDS_SUPERVISOR`.

## Compact proof and handoff

Handoffs carry: decision, evidence, blockers, next action, stop conditions.

Do not emit giant portfolio inventories for two-line fixes.

## Operator gates

Never merge, close, mark-ready, force-push, rewrite history, delete branches, change credentials/permissions, or mutate production without explicit operator authority.
