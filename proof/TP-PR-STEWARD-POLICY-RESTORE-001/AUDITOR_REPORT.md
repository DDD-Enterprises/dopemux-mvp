# Formal Auditor Report — PR #1187 / TP-PR-STEWARD-POLICY-RESTORE-001

## Authority

`SUPERVISOR_DECISION=AUTHORIZE_CODEX_AS_FORMAL_AUDITOR_EXCEPTION_1187_1188`
Limited to PR #1187 (this report) and later PR #1188. Not a repo-wide Codex audit policy.

`SUPERVISOR_DECISION=AUTHORIZE_POLICY_ONLY_EXCEPTION_REPAIR_1187`
Schema enum extension is **NOT INCLUDED / DEFERRED** to a separate governance packet. This audit does **not** cover any schema change.

## Independence

| Role | Identity |
|---|---|
| Implementer | Grok-4.5 (prior session); restored policy + doctor receipt |
| Formal auditor | OpenAI Codex CLI (did not implement or repair #1187) |

## Model identity (this run only)

| Field | Observed value |
|---|---|
| runner / version | OpenAI Codex **v0.146.0** (`codex-cli 0.146.0`) |
| requested | `codex exec review --base main -m gpt-5.6-terra` |
| configured | `gpt-5.6-terra` (CLI `-m` and `~/.codex/config.toml`) |
| response_claimed | `model: gpt-5.6-terra` |
| proxy_reported | `provider: openai` |
| provider_attested | **UNKNOWN** (accepted non-blocking residual for PR #1187 only per AUTHORIZE_POLICY_ONLY_EXCEPTION_REPAIR_1187) |
| session_id | `019fc4f2-698e-7b00-b668-56d829746a36` |

## Frozen content head audited

**`c9038b5a1e2031e19b7245b8ac5e0dd8761b3be3`**

### Audit scope (three original files only)

1. `config/pr_steward/policy.json`
2. `proof/TP-PR-STEWARD-POLICY-RESTORE-001/SUMMARY.md`
3. `proof/TP-PR-STEWARD-POLICY-RESTORE-001/doctor.txt`

### Explicitly out of scope

- Schema enum extension for `codex-cli` / `gpt-5.6-terra` — **DEFERRED**, not in this PR after policy-only repair
- PR #1188 ConPort L3 recovery
- Any claim that Codex audited a schema change

## Independent verification

- `cmp` policy.json == packaged scaffold → PASS (SHA-256 `41d28d3e…`)
- policy content byte-identical to `c9038b5a1e:config/pr_steward/policy.json` → PASS
- `mode=check_only`, `mutates_github=false`, no automerge → PASS
- jsonschema vs `schemas/pr_steward/config.schema.json` → PASS
- `dopemux-pr-steward doctor` → PASS (config_schema + scaffold_skew)
- Non-proof repository config beyond policy.json → none (schema restored to main)

## A) VERDICT

# **PASS_WITH_RISKS**

Policy restoration is correct. Residual risks are non-blocking under the #1187 exceptions.

## C) FINDINGS

| ID | Severity | Status | Title | Body |
|---|---|---|---|---|
| F-1187-PROOF-GAP | HIGH | RESOLVED | Pre-audit SUMMARY overclaimed readiness | Fixed: SUMMARY states not operator-merged; formal PROOF + AUDITOR_REPORT present. |
| F-1187-PROVIDER-ATTEST | LOW | ACCEPTED_RISK | provider_attested UNKNOWN | Accepted for PR #1187 only with recorded runner/model/proxy/session and independence. Does not transfer to #1188. |
| F-1187-SCHEMA-ENUM-DEFERRED | INFO | ACCEPTED_RISK | Trusted-main enums lack Codex identity | Schema extension removed from this PR (deferred). CI independent embedded audit may stay red solely because trusted-main cannot name Codex honestly. Explicitly overridden for #1187 merge posture only. |

## D) INDEPENDENCE

Codex did not author content commits for the policy restore. Auditor is independent of implementer Grok-4.5.

## E) RECOMMENDATION

After repaired tip validation, operator may merge under
`PR_1187_READY_FOR_OPERATOR_MERGE_WITH_CODEX_EXCEPTION`
with expected remaining reds limited to independent embedded audit / Steward inheritance of that status due to trusted-main enum lag.

**Do not auto-merge.** Stage 2 (#1188) waits for operator merge of #1187.
