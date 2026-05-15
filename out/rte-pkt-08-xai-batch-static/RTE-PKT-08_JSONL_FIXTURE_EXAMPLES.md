# RTE-PKT-08 JSONL Fixture Examples

## Output JSONL Shape

```json
{"custom_id":"A_P0001","response":{"status_code":200,"request_id":"req_A_P0001","body":{"id":"chatcmpl_A_P0001","model":"gpt-5-nano","choices":[{"finish_reason":"stop","message":{"role":"assistant","content":"{\"ok\": true}"}}],"usage":{"prompt_tokens":11,"completion_tokens":7,"total_tokens":18}}},"error":null}
```

Accepted metadata:

- `custom_id=A_P0001`
- `response_status_code=200`
- `response_body_present=true`
- `response_id_if_present=chatcmpl_A_P0001`
- `returned_model_id_if_present=gpt-5-nano`
- `finish_reason_if_present=stop`
- `usage_if_present.total_tokens=18`

## Error JSONL Shape

```json
{"custom_id":"A_P0002","response":{"status_code":400},"error":{"type":"invalid_request_error","code":"bad_request","message":"provider rejected Authorization: Bearer [REDACTED]"}}
```

Accepted metadata:

- `custom_id=A_P0002`
- `error_type=invalid_request_error`
- `error_code=bad_request`
- `status_code_if_present=400`
- `failure_type=provider_error`
- `redaction_status=redacted`

## Corrupt Line Example

```text
{not-json
```

The static parser records the corrupt line with a redacted preview and fails closed when discarded nonblank lines exceed 5 percent of nonblank JSONL lines.

## Missing Row Example

Requests:

```text
A_P0001
A_P0002
A_P0003
```

Observed output/error rows:

```text
A_P0001 output row
A_P0002 error row
```

Static proof result:

```json
{"missing_custom_ids":["A_P0003"],"missing_row_count":1,"missing_rows_are_hard_failure":true,"partial_failure":true,"full_success":false}
```
