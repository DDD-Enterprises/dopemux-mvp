# AGY route evidence (route attempted, confirmed unavailable this window)

## agy --version
```
1.1.13
```

## agy models (relevant excerpt, captured 2026-08-15 via `agy models`)
```
gemini-3.7-flash-high	Gemini 3.7 Flash (High)
gemini-3.7-flash-medium	Gemini 3.7 Flash (Medium)
gemini-3.7-flash-low	Gemini 3.7 Flash (Low)
gemini-3.6-flash-high	Gemini 3.6 Flash (High)
gemini-3.6-flash-medium	Gemini 3.6 Flash (Medium)
gemini-3.6-flash-low	Gemini 3.6 Flash (Low)
gemini-3.5-flash-high	Gemini 3.5 Flash (High)
gemini-3.5-flash-medium	Gemini 3.5 Flash (Medium)
gemini-3.5-flash-low	Gemini 3.5 Flash (Low)
gemini-3.1-pro-high	Gemini 3.1 Pro (High)
gemini-3.1-pro-low	Gemini 3.1 Pro (Low)
claude-sonnet-4-6	Claude Sonnet 4.6 (Thinking)
claude-opus-4-6-thinking	Claude Opus 4.6 (Thinking)
gpt-oss-120b-medium	GPT-OSS 120B (Medium)
```
`gemini-3.1-pro-high` confirmed present.

## Fail-closed rejection proof (invalid selector, re-proven at v1.1.13)
```
$ agy --model gemini-3.1-pro-preview --print "ping"
Error: invalid model selection (--model "gemini-3.1-pro-preview" --effort ""): model gemini-3.1-pro-preview is not recognized as a known model or custom model in settings
Available models:
  Gemini 3.7 Flash (High)
  ...
  Gemini 3.1 Pro (High)
  Gemini 3.1 Pro (Low)
  ...
exit code: 1
```
No silent fallback: an invalid selector is rejected outright with the full model list, not silently substituted.

## Attempt 1 (real audit run, first try)
```
Error: timeout waiting for response
```

## Attempt 2 (authorized single retry)
```
Error: timeout waiting for response
```

## Diagnostic probe (minimal prompt, not a third audit attempt)
```
agy --model gemini-3.1-pro-high --print "Reply with exactly the text: PONG"
-> hung with zero output, killed after 3m0s (exit 143 / SIGTERM), while agy --version responded in 0.4s
```
