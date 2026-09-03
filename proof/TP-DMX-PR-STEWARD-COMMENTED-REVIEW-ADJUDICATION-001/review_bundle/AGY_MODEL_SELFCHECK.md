# AGY model-selection no-fallback evidence

Two probes run before the formal audit invocation, confirming exact model
selection and no silent fallback.

## Probe 1: trivial echo
Command: `agy --model gemini-3.1-pro-high --output-format json --print-timeout 60s --print='Reply with exactly: MODEL_CHECK_OK'`
Result: `{"conversation_id":"2799ba1f-651d-41b7-b9fc-d4051e6ac7ec","status":"SUCCESS","response":"MODEL_CHECK_OK\n", ...}`

## Probe 2: self-identification
Command: `agy --model gemini-3.1-pro-high --output-format json --print-timeout 60s --print='State your exact underlying model identifier/version string as you understand it, one line, nothing else.'`
Result: `{"conversation_id":"67ef9f9c-4e31-47b3-bc35-dab309d6ac35","status":"SUCCESS","response":"Gemini 3.1 Pro (High)\n", ...}`

`agy models` (captured same session, see AGY_MODELS.txt) lists `gemini-3.1-pro-high`
unambiguously as `Gemini 3.1 Pro (High)` among 14 entries — matches the self-report
exactly. No fallback indication in any of the three calls.
