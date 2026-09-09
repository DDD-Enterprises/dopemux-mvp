# Audit Invocation Record

Formal content audit used AGY with:

- exact model `gemini-3.1-pro-high`
- effort `high`
- sandbox enabled
- slash-command expansion disabled
- absolute worktree added read-only
- external issued packet directory added read-only
- no fallback
- no provider-runtime calls
- no container start
- no credentials
- no live route reload

Conversation: `f30ad87b-79c5-416c-8853-65ee03e03b61`

Audit target:

- root `/Users/hue/code/dopemux-mvp/.worktrees/feat-pal-model-routing-modernization-001`
- staged tree `1fdef10ee7e59c30f8ecf3c495b50f5133cab02d`
- staged binary diff SHA-256 `7ea9003a3b52b0888c384cffa60422b59ee22ef6207fbea384004d6cf9455038`

Final response metadata reported requested and actual model as `gemini-3.1-pro-high`, `fallback_used=false`, exit 0, and verdict `PASS`.

Preflight history:

- Claude Sonnet: HTTP 429 before inference; zero tokens/model use/cost; no verdict.
- AGY timeout syntax attempt: CLI exit 2 before inference.
- AGY wrong-root probe: inspected primary checkout, not frozen diff; unusable as content verdict.
- Formal AGY conversation: exact worktree target; first turn requested missing external packet; second turn supplied same immutable packet and returned replacement PASS without content change.
