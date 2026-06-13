# Stage 2: Cost Profile Matrix

## Matrix

| Profile Name | Expected Spend Class | Primary Provider | Required Credentials | Fallback Behavior | Verdict | Notes |
|---|---|---|---|---|---|---|
| `cost` | lowest | OpenAI, Gemini | `OPENAI_API_KEY`, `GEMINI_API_KEY`, `XAI_API_KEY` | Routes to cheap mini/flash models first. | PARTIAL | `gpt-5-nano`, `gemini-2.5-flash`. Matches "cost" intent, but requires 3 API keys. |
| `balanced` | low_to_medium | OpenAI | `OPENAI_API_KEY`, `GEMINI_API_KEY`, `XAI_API_KEY` | Upgrades to `gpt-5.2` and `gemini-2.5-pro` for synthesis. | PARTIAL | Safe, but requires 3 API keys. |
| `balanced_openrouter` | low_to_medium | OpenRouter | `OPENROUTER_API_KEY`, `XAI_API_KEY` | Pure OpenRouter (plus XAI fallback) for unified billing. | PASS | Wizard default, reliable billing. |
| `balanced_grok_openrouter`| medium_to_high | XAI, OpenRouter | `XAI_API_KEY`, `OPENROUTER_API_KEY` | Fast Grok for bulk, OpenRouter `gpt-5.2` / Opus for synthesis. | PASS | Clear provider requirements, accurate name. |
| `quality` | medium | OpenAI, Gemini, Anthropic | `OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY` | Uses `gpt-5.1` and `claude-sonnet-4-5`. | PARTIAL | "Quality" is vague. High token cost risk. |
| `openrouter` | medium_to_high | OpenRouter | `OPENROUTER_API_KEY` | Single provider billing, climbs to `gpt-5.2-pro`. | PARTIAL | Name implies "routing method" but behaves as premium "quality". |
| `gemini_primary` | low_to_medium | Gemini, OpenRouter | `GEMINI_API_KEY`, `OPENROUTER_API_KEY` | `gemini-3-flash-preview` / `gemini-3.1-pro-preview` with OpenRouter fallbacks. | PARTIAL | Wizard has `gemini-3-flash`, v5 has `gemini-3-flash-preview`. Out of sync. |
| `optimal` | highest | XAI, OpenRouter | `XAI_API_KEY`, `OPENROUTER_API_KEY` | `grok-4.20-reasoning` and `gpt-5.4` / `claude-opus-4-6`. | BLOCKED | "Optimal" implies "best value", but is actually maximum spend. Dangerous naming. |

## Profile naming risks
- `openrouter` is named after a provider, but acts as a medium/high tier profile with `gpt-5.2-pro`.
- `optimal` implies the best balance but actually means "highest quality / highest cost".
- `quality` uses Anthropic and OpenAI directly.

## Pricing Authority
Pricing lookup occurs via `baseline_v1` in `route_registry_baseline`, `openrouter.ai` fetch, and fallback policies for unknown models.
