# RTE-PKT-15 Redaction Matrix

| Surface | Secret-shaped input class | Expected output behavior | Validation |
| --- | --- | --- | --- |
| Failed text helper | Provider-token-shaped text, bearer header text, private-key-block-shaped text, generic long mixed token text | Secret-shaped value absent; redaction marker present; safe digest text preserved. | `test_failed_sidecar_text_redacts_provider_tokens_and_private_key_blocks` |
| Failed JSON helper | Generic long mixed token in non-sensitive failure field | Secret-shaped value absent; redaction marker present; `api_key_env` and digest metadata preserved. | `test_failed_sidecar_payload_redacts_generic_secret_shapes_but_preserves_env_metadata` |
| Worker exception sidecars | Exception text containing generated secret-shaped content | `.FAILED.txt` and `.FAILED.json` omit secret-shaped value; failure class and partition metadata remain. | `test_worker_exception_failed_sidecars_redact_secret_text` |
| Parse failure sidecars | Raw provider response text containing generated secret-shaped content | `.FAILED.txt` and `.FAILED.json` omit secret-shaped value; parse failure metadata remains. | `test_parse_failure_failed_sidecars_redact_raw_response_text` |
| Schema failure sidecars | Schema-failed response payload containing generated secret-shaped content | `.FAILED.txt` and `.FAILED.json` omit secret-shaped value; schema gate context remains. | `test_schema_failure_failed_sidecars_redact_response_and_preserve_context` |
| Batch provider sidecars | Batch result error containing generated secret-shaped content | `.FAILED.txt` and `.FAILED.json` omit secret-shaped value; provider, model, and batch id remain. | `test_batch_watch_failure_sidecars_redact_provider_error_text` |
| Batch terminal text helper | Terminal-state text containing generated secret-shaped content | `.FAILED.txt` omits secret-shaped value; terminal class text remains. | `test_failed_sidecar_text_writer_redacts_batch_terminal_text` |
| Failed JSON direct writer | `.FAILED.json` payload with generic long mixed token | Token absent from persisted JSON; safe env and digest metadata preserved. | `test_failed_sidecar_json_writer_redacts_generic_secret_shape` |

## Boundary

RTE-PKT-15 handles post-failure artifact redaction. RTE-PKT-02 provider-bound payload redaction remains separate and was not changed.
