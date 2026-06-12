# Stage 3: PAL Challenge Results

## Challenge Context
We map the fallback behaviors and strict-schema capabilities of the routing ladders.

## Assertions
1. Models like `gpt-5.4` and `claude-opus-4-6` are aspirational or test fixtures, creating exhaustion risks if used live.
2. Prescan ladders intentionally diverge from full-run ladders in policies like `balanced_grok_openrouter`.

## Verification
- Verified via `run_extraction_v5.py` source: `BALANCED_GROK_OPENROUTER_DOCS_STRICT_LADDER` explicitly enforces stricter routing than the generic ladder for those phases.
- OpenRouter does not currently support `claude-opus-4-6`.

## Conclusion
Routing ladders use aspirational model names which could result in runtime `routing_all_routes_denylisted` or `routing_empty_ladder` exceptions if they are not intercepted or aliased downstream.
