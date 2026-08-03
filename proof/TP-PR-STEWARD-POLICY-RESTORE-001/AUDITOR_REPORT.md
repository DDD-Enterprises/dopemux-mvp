# Formal Auditor Report — PR #1187 / TP-PR-STEWARD-POLICY-RESTORE-001

## Authority

`SUPERVISOR_DECISION=AUTHORIZE_CODEX_AS_FORMAL_AUDITOR_EXCEPTION_1187_1188`
Scope limited to PR #1187 (this report) and later PR #1188. **Not** a repo-wide Codex audit policy.

## Independence

| Role | Identity |
|---|---|
| Implementer | Grok-4.5 (prior session); restored policy + doctor receipt |
| Formal auditor | OpenAI Codex CLI (did **not** implement or repair #1187) |

## Model identity (this run only — not copied from PR #1182)

| Field | Observed value |
|---|---|
| runner / version | OpenAI Codex **v0.146.0** (`codex-cli 0.146.0`) |
| requested | Formal audit via `codex exec review --base main -m gpt-5.6-terra` |
| configured | `~/.codex/config.toml` model=`gpt-5.6-terra`; CLI `-m gpt-5.6-terra` |
| response_claimed | Header of session: `model: gpt-5.6-terra` |
| proxy_reported | `provider: openai` (Codex session header) |
| provider_attested | UNKNOWN (no separate provider attestation artifact beyond Codex session header) |
| session_id | `019fc4f2-698e-7b00-b668-56d829746a36` |

All identity fields recorded from **this** run’s `review_bundle/codex_formal_audit_extract.md (+ stdout.sha256)` lines 1–11.

## Frozen content head audited

`c9038b5a1e2031e19b7245b8ac5e0dd8761b3be3`

Changed files vs `main` at audit time:

1. `config/pr_steward/policy.json`
2. `proof/TP-PR-STEWARD-POLICY-RESTORE-001/SUMMARY.md`
3. `proof/TP-PR-STEWARD-POLICY-RESTORE-001/doctor.txt`

## Independent verification performed

- `cmp` policy.json == packaged scaffold → exit 0; SHA-256 both `41d28d3e…`
- jsonschema validate against `schemas/pr_steward/config.schema.json` → PASS
- `dopemux_pr_steward.cli doctor --format json` → status PASS, scaffold_skew PASS
- `pytest -q tests/dopemux_cli/test_doctor.py tests/dopemux_init/test_pr_steward_scaffold.py` → 7 passed (Codex session)
- `git diff --check` base…HEAD → clean
- Policy keys: `mode=check_only`, `mutates_github=false`, no automerge field

## A) VERDICT

# **PASS_WITH_RISKS**

Non-blocking residual risks only (see findings). Policy restoration is correct and fail-closed governance posture preserved.

## C) FINDINGS

| ID | Severity | Status | Title | Body |
|---|---|---|---|---|
| F-1187-PROOF-GAP | HIGH | **RESOLVED** | Pre-audit SUMMARY overclaimed readiness | Codex P1: SUMMARY said recovery prerequisite READY without embedded audit. Fixed in this proof successor: SUMMARY states NOT operator-merged; full PROOF + AUDITOR_REPORT + review bundle added. |
| F-1187-PROVIDER-ATTEST | LOW | ACCEPTED_RISK | provider_attested UNKNOWN | Codex session reports provider=openai and model=gpt-5.6-terra; no separate OpenAI API attestation token captured. Acceptable for L2 policy restore under recorded session header. |
| F-1187-SCHEMA-ENUM | INFO | RESOLVED | Schema lacked codex-cli / gpt-5.6-terra | Under supervisor Codex-auditor exception, enum extended in `schemas/proof/embedded_audit.schema.json` so formal identity can be recorded honestly. |

## D) INDEPENDENCE

Confirmed: Codex did not author commits `2a96b0cfb0` or `c9038b5a1e`. Auditor is independent of implementer (Grok-4.5).

## E) RECOMMENDATION

After this proof-only tip is pushed, CI is green, and PR Steward is **READY** on the exact proof tip, operator may merge PR #1187. **Do not auto-merge.**

## Codex primary review output (summary)

Codex confirmed policy matches scaffold and doctor validation passes. Its only P1 was missing formal audit bundle / overclaim of READY — addressed by this packet.
