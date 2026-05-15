# RTE-PKT-15 Secret Fixture Redaction Proof

Generated tests construct secret-shaped values at runtime and assert absence from persisted `.FAILED.txt` and `.FAILED.json` outputs.

The raw generated fixture values are not quoted in this proof.

Covered assertions:

- Worker exception text: generated secret-shaped exception content is absent from `.FAILED.txt` and paired `.FAILED.json`; redaction markers remain.
- Parse failure response text: generated secret-shaped model response content is absent from `.FAILED.txt` and paired `.FAILED.json`; `failure_type`, `status_code`, phase, step, and partition remain.
- Schema failure response text: generated secret-shaped response content is absent from `.FAILED.txt` and paired `.FAILED.json`; schema context remains visible.
- Batch provider error text: generated secret-shaped provider error content is absent from `.FAILED.txt` and paired `.FAILED.json`; provider, model, and batch ID remain.
- Batch terminal text helper: generated secret-shaped terminal text is absent from `.FAILED.txt`; terminal failure class text remains.
- Output safety helper: provider-token-shaped text and private-key-block-shaped text are removed; safe SHA text remains.

Observed redaction markers:

- `[REDACTED]`
- `[REDACTED PRIVATE KEY]`
- `REDACTED` for query parameter values
