# Review Bundle — TP-DMX-UR-ARTIFACT-INTAKE-001 (Embedded Audit)

Single review unit for the embedded audit of the Universal Router evidence intake.

- **Verdict:** `PASS_WITH_RISKS`
- **Audited base HEAD:** `45b5ee3f320e777111a6f00227072efeb725996b` (branch `codex/ur-artifact-intake-001`) — the base the staged diff sits on; changes are uncommitted.
- **Auditor:** primary = Claude Code Opus objective evidence battery (mechanical: recomputed hashes, `shasum -c`, schema validate, allowlist regex); soft corroboration = independent Claude Code Sonnet run via the `claude-audit` clink route (leading-prompt second look). Both are separate from the `codex` implementer.

## Contents

| File | What it is |
|---|---|
| `INDEPENDENT_AUDITOR_PROMPT.txt` | Exact prompt delivered to the Sonnet corroboration run (stdin). Note: it pre-states the expected invariants, so the run is a leading-prompt second look |
| `CLINK_AUDIT_RAW.json` | Sanitized normalized output of the clink corroboration run (exit 0, 118.5s). `stdout` = verdict; `stderr` excluded to avoid local-path/env leakage |
| `../AUDITOR_REPORT.md` | Full human-readable auditor report (findings, evidence battery, gate status) |
| `../PROOF.json` | Schema-valid `embedded_audit` proof object (validated by `scripts/audit/validate_audit_proof.py` → PASS) |

## Excluded (with reason)

- Scratchpad driver `run_clink_audit.py` and `assemble_proof.py` — throwaway harness under the session scratchpad; not part of the review unit.
- Auditor `stderr` — excluded to prevent local-path/environment leakage; run metadata (exit code, duration, timed_out) is preserved in `CLINK_AUDIT_RAW.json`.

No secrets, tokens, credentials, private keys, or raw auth headers are included in this bundle.

## Gate status

- Embedded audit: **PASS_WITH_RISKS**, current to the audited HEAD.
- PR Steward intake/gate (packet step S4): **NOT_RUN** — no PR yet; regenerate proof and re-pin to the PR head SHA before the FINALIZATION gate (proof TTL is 1h).
