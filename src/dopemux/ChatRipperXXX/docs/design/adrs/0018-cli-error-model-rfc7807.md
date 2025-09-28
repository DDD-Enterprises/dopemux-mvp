# ADR-0018: CLI Error Model (RFC-7807 Problem JSON)

Status: Accepted | Date: 2025-09-03

Context
- We need consistent, machine-readable CLI errors to integrate with scripts and CI while preserving good human UX by default.
- Extractor hardening (X3–X6) introduces validation/quarantine and additional preflight checks where structured error signaling helps.
- Project policies require JSON/HTTP errors to follow RFC‑7807.

Decision
- Standardize fatal CLI errors as RFC‑7807 Problem JSON on stderr when `--error-format json` is provided. Default remains human‑readable text.
- Always set a non‑zero exit code on fatal errors (1), even when emitting Problem JSON.
- Redact user paths (home directory) in textual output; include a redacted `instance` path in Problem JSON.

Scope (initial)
- Commands: `imessage pull`, `instagram pull`, `extract`, `transform`, `imessage audit` (for missing DB).
- Codes introduced:
  - `INVALID_INPUT` — invalid arguments or parse failure (e.g., bad ZIP).
  - `MISSING_DB` — Messages `chat.db` not found (iMessage paths).
  - `MISSING_BACKUP_DIR` — backup directory not found.
  - `ENCRYPTED_BACKUP_PASSWORD_REQUIRED` — encrypted backup requires password.
  - `MISSING_ZIP` — Instagram data ZIP not found.
  - `UNSAFE_ZIP_ENTRY` — ZIP contains an unsafe member path (Zip Slip blocked).
  - `NO_VALID_ROWS` — all rows failed schema validation; see `out/quarantine/messages_bad.jsonl`.

Problem JSON shape
```json
{
  "type": "https://chatx.local/problems/<CODE>",
  "title": "<Human summary>",
  "status": 1,
  "detail": "<Short actionable detail>",
  "instance": "<redacted path or context>",
  "code": "<CODE>"
}
```

CLI flag
- `--error-format json|text` (default: `text`) on supported commands.
- When omitted, keep current text UX; preserve exit codes.

Consequences
- Scripts can consume structured errors; humans keep concise text by default.
- `status` in Problem JSON mirrors process exit (1). (We do not embed OS‑specific codes.)
- Path redaction reduces accidental PII leakage in logs.

Alternatives considered
- Ad‑hoc JSON structures per command — rejected (inconsistent, harder to parse).
- Exit codes only — insufficient context; not self‑describing; brittle.
- Environment variable to switch modes — less explicit than per‑command flag.

Rollout
- Initial wiring covers iMessage and Instagram commands and common preflights.
- Next: extend to WhatsApp/TXT subcommands when implemented; add problem catalog to docs site.
- Monitor CI and user feedback; refine `detail` hints and add correlation IDs if needed.

References
- RFC‑7807: Problem Details for HTTP APIs (applies to CLI stderr as a stable JSON envelope)
- Project policy: JSON/HTTP errors follow RFC‑7807

