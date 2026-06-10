# Stage 3: Routing Ladders, Fallback Order, and Behaviors

## Runtime Routing Ladders & Fallbacks

### `cost`
- Primary: `openai/gpt-5-nano` -> Fallback: `gemini-2.5-flash` -> Exhaustion: `xai/grok-code-fast-1`
- Schema capability: Basic.
- Cost-risk: Lowest.

### `balanced_openrouter`
- Primary: `openai/gpt-5-mini` -> Fallback: `gemini-2.5-flash` -> Exhaustion: `xai/grok-code-fast-1`
- Schema capability: Medium.
- Cost-risk: Medium.

### `balanced_grok_openrouter`
- Primary: `xai/grok-code-fast-1` -> Fallback: `openai/gpt-5-mini`
- Schema capability: Medium to High.
- Cost-risk: Medium to High.

### `openrouter`
- Primary: `openai/gpt-5-mini` / `openai/gpt-5.2`
- Schema capability: High.
- Cost-risk: Medium to High (synthesis climbs to `gpt-5.2-pro`).

### `gemini_primary`
- Primary: `gemini-3-flash-preview` / `gemini-3.1-pro-preview` -> Fallback: `openai/gpt-5-mini` / `openai/gpt-5.4`
- Schema capability: High.
- Cost-risk: Medium.

### `optimal`
- Primary: `xai/grok-4.20-beta-0309-reasoning` / `openai/gpt-5.4` -> Fallback: `claude-opus-4-6`
- Schema capability: Highest.
- Cost-risk: Highest.

## Prescan vs Full-Run Equivalence
The strict phase overrides like `BALANCED_GROK_OPENROUTER_DOCS_LADDER` indicate that prescan (D0/D1) and full-run ladders intentionally diverge for certain policies.

## Stale or Aspirational Model IDs
- `openai/gpt-5-nano`, `openai/gpt-5-mini`, `openai/gpt-5.2-chat`, `openai/gpt-5.2-pro`, `openai/gpt-5.4`
- `anthropic/claude-opus-4-6`
These appear to be forward-looking or alias models that may not exist in live OpenRouter configurations.
