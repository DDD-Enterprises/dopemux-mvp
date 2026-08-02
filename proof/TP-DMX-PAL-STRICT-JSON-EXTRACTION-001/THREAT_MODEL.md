# THREAT_MODEL — strict PAL clink JSON extraction

## Assets

- Audit verdict integrity (PASS / PASS_WITH_RISKS / FAIL / NEEDS_SUPERVISOR)
- Fail-closed mapping from rejected model stdout to status=error

## Threats

1. **Multi-fence / dual-object smuggling** — model emits two fenced blocks; salvage picks a preferred verdict.
   - **Mitigation:** explicit line-structure one-fence rule; any interior exact fence opener/closer raises before `json.loads`.

2. **Brace scraping** — prose wraps a JSON object; parser extracts first/last brace substring.
   - **Mitigation:** only bare full-output object or single full-output fence; no brace scan.

3. **Resource exhaustion** — huge model stdout / nested tool content triggers costly parse work.
   - **Mitigation:** `MAX_AUDIT_OUTPUT_BYTES = 1_048_576` UTF-8 bytes before strip/splitlines/json.loads.

4. **Rejected text becomes PASS/READY** — error path invents success.
   - **Mitigation:** `_rejected_parse_payload` sets status=error without verdict; tests assert normalize never yields PASS/READY.

## Non-claims

- This package does **not** claim independent embedded-audit PASS.
- This package does **not** authorize mark-ready, merge, or PR closure.
