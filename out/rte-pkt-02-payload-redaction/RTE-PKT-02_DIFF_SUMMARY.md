# RTE-PKT-02 Diff Summary

## Runtime Changes

- `services/repo-truth-extractor/output_safety.py`
  - Added provider-bound text/payload sanitizers.
  - Preserves existing output sanitizer entry points while extending provider-only redaction for private-key blocks, common provider token prefixes, and long mixed-case token-like literals.
  - Preserves safe environment metadata keys and hex digests.

- `services/repo-truth-extractor/lib/prescan/grok_passes.py`
  - Sanitizes `_get_file_preview` output.
  - Adds `_build_provider_payload` / `_sanitize_provider_payload`.
  - Ensures Grok pass payloads are sanitized before cache keying, JSON serialization, token estimation, and provider-boundary invocation.

- `services/repo-truth-extractor/run_extraction_v5.py`
  - Sanitizes central sync chat payload construction in `build_chat_payload`.
  - Sanitizes `build_v5_batch_request` system/user content before lower-level batch clients serialize the request.

- `services/repo-truth-extractor/llm_runtime.py`
  - Sanitizes prompts before dependency payload construction.
  - Uses sanitized prompt text for native Gemini SDK contents/system instruction and chat SDK dispatch.

## Test Changes

- `services/repo-truth-extractor/tests/test_provider_payload_redaction.py`
  - Adds local tests for provider sanitizer behavior, Grok preview redaction, Grok pass payload redaction, fake provider-boundary capture, path exclusions, env-template preview sanitization, v5 chat payload construction, v5 batch request construction, and `llm_runtime.call_llm` sanitization.

## Proof Outputs

- `out/rte-pkt-02-payload-redaction/`
  - Contains the canonical task packet and packet proof files for manifest, redaction matrix, test report, no-provider-call attestation, fixture redaction proof, diff summary, remaining unknowns, and implementation notes.

## Scope Boundary

All changed files are inside the packet allowlist or the allowed proof output root.

No forbidden paths were changed:
- promptsets
- prompts
- model maps
- structured-output contracts
- config
- docs
- compose/deployment files
- provider route policy
- pricing/spend behavior
