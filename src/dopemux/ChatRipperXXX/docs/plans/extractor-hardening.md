# Extractor Hardening — PR-X1 → PR-X6

## Master “Codex System Prompt” (paste once at session start)

You are implementing extractor hardening for ChatX/XtractXact. Follow these rules:

- Contract: Every emitted row MUST validate against `message.schema.json`. Quarantine invalids to `./out/quarantine/messages_bad.jsonl` and continue.
- Required fields: `msg_id, conv_id, platform, timestamp (ISO-8601 UTC), sender, sender_id, is_me, text, reactions[], attachments[], source_ref{path, guid?}`.
- Fold reactions under parents; resolve replies with stable `reply_to_msg_id`.
- Attachments: metadata only; never upload binaries.
- Determinism/UX: same inputs → same outputs; structured logs; machine-readable errors; perf smoke present.
- Coverage: new code ≥90%; mypy/ruff clean; no network calls.

If a spec point is ambiguous, choose the safer local-only option and leave a TODO(spec).

---

## PR-X1 — Timestamp Normalization Hardening

- Implement robust conversion of iMessage time fields to ISO-8601 UTC with support for seconds/micro/nano Apple-epoch variants.

Touch
- `src/chatx/imessage/time.py` (new): `to_iso_utc(raw: int|float|None) -> str|None`
- `src/chatx/imessage/extract.py` and `src/chatx/extractors/imessage.py`: use helper for all timestamps.
- Tests: `tests/imessage/test_time_normalization.py` (property + fixtures).

Requirements
- Accept Apple epoch variants; clamp impossible; ISO-8601 UTC only.

---

## PR-X2 — Idempotent Reactions & Reply Resolution

- Make folding idempotent and order-independent; dedupe tapbacks; reply resolution maps GUID → parent `msg_id`.

Touch
- `src/chatx/imessage/extract.py`
- Tests: `tests/imessage/test_reactions_replies_idempotent.py` (shuffle order; duplicate protection).

---

## PR-X3 — Row Validation + Quarantine

- Validate each row against `message.schema.json`. On error, append row + reason to `./out/quarantine/messages_bad.jsonl` and continue; return exit 0 if at least one valid row was written.

Touch
- `src/chatx/validate/jsonschema.py` (new)
- `src/chatx/imessage/extract.py` (invoke validator)
- Tests: `tests/validate/test_quarantine.py`.

---

## PR-X4 — Run Manifest + Minimal Run Report

- Emit `out/manifest.json` (inputs + hashes + extractor version) and ensure `out/run_report.json` is written with counts/elapsed already present.

Touch
- `src/chatx/obs/run_artifacts.py` (new)
- `src/chatx/cli/main.py` (write at end)
- Tests: `tests/obs/test_run_artifacts.py`.

Shape
- Manifest: `{ inputs: {db_path, attachments_dir?}, input_hashes: {db_sha256}, version, schema_v }`.

---

## PR-X5 — Machine-Readable CLI Errors (RFC-7807-style)

- Standardize fatal CLI errors as JSON (stderr) with codes like `INVALID_INPUT`, `MISSING_MANIFEST_DB`, `ENCRYPTED_BACKUP_PASSWORD_REQUIRED`. Redact paths. Provide `--error-format json|text` (default text).

Touch
- `src/chatx/cli_errors.py` (new)
- Use in backup + local (preflights + extraction path)
- Tests: `tests/cli/test_error_model.py`.

---

## PR-X6 — Attributed Body → Clean Text (preserve raw)

- Normalize `attributedBody` (RTF/HTML-ish) to clean `text`. Preserve original under `source_meta.raw.attributed_body`.

Touch
- `src/chatx/imessage/body_normalize.py` (new)
- `src/chatx/imessage/extract.py` (wire in)
- Tests: `tests/imessage/test_body_normalize.py`.

---

## Strategy

1. Branch `feat/extractor-hardening` and open micro-PRs X1 → X6.
2. After X3 & X4, run a golden extraction on fixtures; assert schema pass + quarantine presence (if any), manifest + run_report present, perf smoke meets target.
3. Verify ACs: ISO timestamps, folded reactions, stable replies, attachment refs, provenance.
4. Greenlight: once CI gates are green, hand off to transform → redact → index.

