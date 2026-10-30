# MACRO-DMX-MEMORY-BRIDGE-001-R5 — Issuance Record (repair of R4 audit finding N12)

**Issued**: 2026-10-30 by the Control Tower supervisor session (Claude Code desktop, `claude-opus-5-5`).
**Operator instruction**: "Repair N12" (answer after the R4 audit).
**State at issuance**: branch head `e0b90f5f2` (R4 closure, unsigned `PROOF.json`); R4 audited content head `88e7b7de3` (Grok `PASS_WITH_RISKS`, Q1-Q14 PASS). PR #1483 is a draft at `bff3fd46e`. `origin/main` is `93050d135`. Authority: NONE. Earlier records stay unchanged.

## Execution gate

```
AUTHORIZE_MACRO_DMX_MEMORY_BRIDGE_001_R5_EXECUTION=YES
```

A new audited subject needs its own audit route line:

```
AUTHORIZE_MACRO_DMX_MEMORY_BRIDGE_001_R5_AUDIT_ROUTE=grok-cli:grok-4.5:ONE_ATTEMPT
```

## Package members (the macro pins each by SHA-256)

| Member | SHA-256 |
|---|---|
| `MACRO_PACKET.json` | `0e304de1c7a315820aca2012afeb328b817e09eb78f20142bcaea80bef623c4e` |
| `EXECUTION_BINDING.json` (coordinator) | `30c31df0875a861bbd60665d1ef75a68936aee294e2de55ccd598a339b7a352c` |
| `WORKSTREAMS/W01/TASK_PACKET.json` | `7d86d0f5f07e6eba7f2c0f49f23e9ff5c342ed0980252546229213cd722d0879` |
| `WORKSTREAMS/W02/TASK_PACKET.json` | `66ea395f5164d77a969c91bff8b6ec35895cd79022491ac4da5a2cc43af548b2` |

## What changes

### W01 (`register.tsx`, `register.test.ts`; Haiku → Sonnet fallback)

| | Before (`register.tsx:266-269`) | After |
|---|---|---|
| Ordinary id (`/^[A-Za-z0-9_-]{1,80}$/`, e.g. Claude Code's UUID-shaped ids) | key = id | key = id (unchanged; no file is renamed, no migration) |
| Any other id | every character outside `[A-Za-z0-9_-]` becomes `_`, cut to 80: `a/b` and `a:b` both become `a_b` and share one file and one `$.store` key | `<prefix>~<h>`: the sanitized id cut to 56 characters, `~`, and a 16-hex hash of the WHOLE original id; at most 73 characters |
| Empty id | `unknown` (collides with an id literally named `unknown`) | `~<h>` |

Why it is injective: ordinary keys never contain `~`, so the two forms cannot meet; two keys of the second form meet only on a 64-bit hash collision. The hash is synchronous because `safeId` runs in synchronous paths: two 32-bit FNV-1a passes with `Math.imul` (the second over the id prefixed by NUL), 8 hex digits each. No callers change; the `readPrior` file-name pattern already accepts `~`.
Tests (failing run first): UUID unchanged; `a/b` vs `a:b`; two ids longer than 80 characters with a shared prefix; empty vs `unknown`; the key alphabet and length; an exotic-id session writes, reloads and is found (and relayed) by another session.

### W02 (`README.md`, `docs/02-how-to/memory-bridge.md`; Haiku → Sonnet fallback; after W01)

One sentence in each file next to `outbox-<sessionId>.jsonl`: the key is the session id itself for ordinary ids; any other id gets a sanitized prefix plus `~` and a 16-hex hash of the whole id, so two sessions never share a file. The how-to stays at 149 lines or fewer.

Not in scope: N7-N11 stay accepted notes; the relay, replay, ring format, band and `/bridge-note` are unchanged.

```
TP_ROUTE   (W01, W02)
runner=claude-code-agent
model=claude-haiku-5-5   (fallback claude-sonnet-5-5 on an evidence-backed STOP only)
effort=UNKNOWN
skills=NONE
why=a fully specified pure-function change with tests, then a docs sentence; cheapest adequate; the coordinator (Opus) designed the rule and reviews the diff
```

## PROPOSED allowances (accepted by authorizing R5)

| Scope | Elapsed | Subagent tokens | Tool uses | Attempts |
|---|---|---|---|---|
| W01 | 20 min | 250,000 | 80 | 1 Haiku + 1 Sonnet fallback |
| W02 | 15 min | 150,000 | 50 | 1 Haiku + 1 Sonnet fallback |
| **Macro** | 2 h | 600,000 | — | 4 dispatches; 1 correction round |

Basis: R4's children used 160k (Sonnet, relay) and 132k (Haiku, docs). Caps, not forecasts; cost UNKNOWN. Audit outside the budget: 1 attempt, 0 retries (the earlier runs cost about $0.08 each).

## Validation at issuance

`ct validate-macro` STATIC_VALID; `ct bind-record` + `ct validate-binding` PASS; `task_packet.v2` schema PASS ×2; pins MATCH. Child bindings, DCP route, Task Orchestrator: NOT_RUN.

## Note

Each repaired head makes the earlier unsigned proofs obsolete and needs its own attestation and signature before a push. After R5 the open list is N7-N11, all INFO disclosures.
