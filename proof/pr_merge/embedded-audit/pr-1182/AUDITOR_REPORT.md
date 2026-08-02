# Formal Embedded Audit Report — PR #1182

**Supervisor decision:** `AUTHORIZE_CODEX_AS_FORMAL_AUDITOR_EXCEPTION` (operator choice `1`, 2026-08-02)

## Authority

- User/supervisor authorized Codex as formal auditor for **this packet only**.
- AGENTS.md normally forbids Codex as formal auditor; latest supervisor instruction outranks for this slice.
- Schema enum on `main` still lacks `codex-cli` / `gpt-5.5`. Local signed-attestation CI path cannot honestly encode this identity until main schema is extended. This report records the authorized exception and the real identity ledger.

## Identity ledger

| Field | Value |
|---|---|
| runner | codex-cli 0.146.0 |
| configured_model | default/unset |
| response_claimed_model | gpt-5.5 |
| proxy_reported_identity | provider: openai (Codex CLI banner) |
| provider_attested_identity | OpenAI Codex sessions below |
| implementer | grok-4.5-xai (different family) |

## Sessions (content head `2cb743117d2d6689bf9394e3c7b492fccbd958e1`)

| Round | Head | Session | Result |
|---|---|---|---|
| R1 | d3dbe23a42 | 019fc4cf-6a3c-7130-9383-0741d90c9971 | P2 Luna demotion routing — fixed in 2cb743117d |
| R2 | 2cb743117d2d6689bf9394e3c7b492fccbd958e1 | 019fc4d4-f83d-7802-b56d-ee49b5b1d8d6 | No clear actionable breakage |

Invocation:
```
codex review --base origin/main
```

## Deterministic validation

See `review_bundle/DETERMINISTIC_VALIDATION.json` — **PASS**.

## Findings

### F-001 (RESOLVED) — Demoted items retained Luna primary
R1 finding. Fixed: only 12 `luna-ready` items keep `gpt-5-6-luna`; 35 demoted re-routed.

### F-002 (ACCEPTED_RISK / INFO) — Formal schema enum gap
Codex is not in `embedded_audit.auditor_tool` / `auditor_model` enums on main. Supervisor exception authorizes operator-merge readiness on this packet without pretending the identity was Claude/Gemini.

### F-003 (INFO) — Six-file docs/export only
No runtime code in delta. Risk surface limited to operator dispatch mis-use of export; routing invariants now hold.

## Verdict

**PASS_WITH_RISKS** under `AUTHORIZE_CODEX_AS_FORMAL_AUDITOR_EXCEPTION`.

Risk retained: automated CI formal-auditor enum cannot name Codex until main schema update; operator merge authorized by supervisor exception + known Codex identity + deterministic PASS.
