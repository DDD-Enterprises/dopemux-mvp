# Independent Embedded Audit — PR #1088

**Packet**: `PR-MERGE-STEWARD-1088`
**Repo**: `DDD-Enterprises/dopemux-mvp`
**Audited head**: `26dd93931bf01db133b07e1571d03f8809026746`
**Auditor**: Claude Code CLI (Sonnet)
**Verdict**: `PASS_WITH_RISKS`

## Scope

Exact-head diff against base `5a9f8f7b5d4a03be323723a92baf3c4e162d5b65` was compared,
path-for-path, against `task-packets/TP-DMX-PAL-MODEL-REFRESH-001.json`'s
`commit.allowlist` (22 paths). The two sets are identical — no scope drift.

## What changed since the prior audit round (head `d52b594bcd29a7c659455cffe321ab08c22e37cb`)

A GitHub review thread (`chatgpt-codex-connector`, P2) correctly flagged that the new
`grok-4.5` catalog entry in `conf/xai_models.json` omitted `default_reasoning_effort`,
so unconfigured Responses-API calls fell back to PAL's generic `"medium"` instead of
xAI's documented Grok 4.5 default of `"high"`. This was fixed in commit `26dd93931`:
`default_reasoning_effort: "high"` added to the `grok-4.5` entry, and the one test
(`test_xai_provider.py::test_generate_content_resolves_alias_before_api_call`) that
had hardcoded the incorrect `"medium"` expectation was corrected to assert `"high"`.
Verified directly: `providers/openai_compatible.py`'s `_generate_with_responses_endpoint`
reads `capabilities.default_reasoning_effort` and only falls back to `"medium"` when
the field is absent — confirmed by reading the code, not by trusting the review comment.

## Checks performed this round

- `git diff --name-status` scope-equality vs the task packet allowlist (see above) — PASS.
- `python -m pytest tests/arch/test_pal_model_catalog_contract.py` — 6/6 passed.
- `python -m pytest tests/test_xai_provider.py tests/test_openai_provider.py
  tests/test_auto_mode_comprehensive.py tests/test_auto_mode_model_listing.py
  tests/test_auto_mode_provider_selection.py tests/test_intelligent_fallback.py
  tests/test_per_tool_model_defaults.py tests/test_supported_models_aliases.py`
  (pal-mcp-server tree) — 111/111 passed.
- Direct read of `providers/openai_compatible.py`'s reasoning-effort injection logic
  to confirm the fix takes effect as claimed.
- No live provider API calls were made (rule: NOT_RUN, not assumed PASS).

## Findings carried forward (all `ACCEPTED_RISK`, none blocking)

1. **MEDIUM** — `pal-stdio`'s Docker build context (`.`, repo root) is not covered by
   the new `docker/mcp-servers-source/pal/.dockerignore` secret-file patterns; it's
   governed by the pre-existing root `.dockerignore`, which lacks `*.key`/`*.pem`/etc.
   Not a regression introduced by this PR (root context predates it), and `.env` stays
   excluded either way. Untested by the contract suite for the `pal-stdio` service.
2. **LOW** — Standalone reference repo `/tmp/pal-model-refresh` @
   `eccf09a236c429eadbe0732d845ecd42eedefbbb` carries materially more OpenAI models
   (37 vs. 13) and a dynamic-selection preference system not ported here. Scope-bounded
   to the packet's 22-path allowlist; flagged for drift awareness only.
3. **INFO** — `_extract_usage`'s `total_tokens` fallback returns `0` instead of the
   input+output sum in one edge case (attribute present but non-int). Not exercised by
   any observed provider response shape.

## Explicitly out of scope, not fixed

A separate P2 review comment noted that OpenRouter's `x-ai/grok-4` catalog entry
(`conf/openrouter_models.json`) still exposes the retired `grok-4`/`grok4`/`grok`
aliases, so a rejected native-provider request for those aliases could still fall
through to OpenRouter and reach a retired model. **`conf/openrouter_models.json` is
not in the task packet's `commit.allowlist`** — editing it would break the exact-scope
match this and the prior audit round both certified. This is a real gap, but fixing it
requires a scope decision (extending the packet or filing a follow-up), not a unilateral
edit under this packet. Left as an open, human-decision item.

## Remaining risks (unchanged from prior round)

- The task packet's `runtime-proof` step (bounded live Grok 4.5 / GPT-5.6 probes) was
  not executed by this or the prior audit — verification remains static. NOT_RUN.
- Grok 4.5 (500K context) and GPT-5.6 (1.05M context, 128K max output) catalog figures
  are not independently confirmed against current vendor documentation under this
  audit's no-live-call constraint.
- `conf/xai_models.json`'s `grok-4.5` entry intentionally omits `max_output_tokens`
  (no officially documented limit to encode); the provider only sets the param when
  truthy, so the omission is safe.
