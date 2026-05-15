# RTE-PKT-02 Secret Fixture Redaction Proof

Raw fixture values are intentionally not quoted in this proof.

Fixture construction:
- The tests generate fake secret-shaped values at runtime from short prefixes plus repeated characters.
- Covered shapes include API-key assignment, authorization bearer header, token assignment, password assignment, webhook-secret assignment, private-key block, AWS-style key prefix, and long mixed-case token-like literal.
- The fixture also includes safe context that must survive redaction: a 64-character hex hash, the model ID `grok-4.20-beta-0309-non-reasoning`, a repo-relative source path, and ordinary prose.

Assertions:
- Every generated raw fixture value is absent from sanitized provider-bound text.
- The bearer token body is absent independently of the full header value.
- A deterministic redaction marker beginning with `[REDACTED` is present.
- Safe hash, model ID, source path, and ordinary prose remain present.
- `.env`, `.env.local`, `deploy.key`, and `id_rsa` are absent from the prescan corpus.
- `.env.example` remains include-eligible, but its provider preview is sanitized.

Result:
- PASS in `pytest services/repo-truth-extractor/tests/test_provider_payload_redaction.py services/repo-truth-extractor/tests/test_output_safety.py services/repo-truth-extractor/tests/test_grok_passes_validation.py -q`.
