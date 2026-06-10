# Redaction Test Output

Secret patterns (sk-/ghp_/AKIA/Bearer/KEY=VALUE) and absolute paths are stripped from backend payloads before leaving the facade; categories recorded in envelope.redactions.

```
$ python -m pytest -q services/dcp-readonly-facade/tests/test_redaction.py \
    services/dcp-readonly-facade/tests/test_packet_0008.py -k "redact or secret"
.........                                                                [100%]
```

Tests:
- test_redact_registered_abs_root
- test_redact_generic_home_path
- test_redact_secret_patterns
- test_no_false_change_on_clean_text
- test_redact_deep_absolute_path_not_in_known_roots
- test_short_route_like_path_preserved
- test_redact_secret_in_dict_key
- test_redact_value_walks_nested_and_reports_categories
- test_secrets_and_paths_redacted_in_backend_payload (packet 0008)
