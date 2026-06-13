# Stage 2: PAL Challenge Results

## Challenge Context
We map and evaluate cost profile names vs their actual behavior.

## Assertions
1. `optimal` is misleading as it refers to maximum possible spend rather than the best value.
2. `openrouter` implies routing technology but forces a medium-to-high cost ladder (e.g., `gpt-5.2-pro`).
3. Wizard ladders are out-of-sync with runtime ladders.

## Verification
- Confirmed via `run_extraction_v5.py` line 678: `optimal` uses `gpt-5.4`, `claude-opus-4-6`, and `grok-4.20-beta-0309-reasoning`.
- Confirmed via `cost_profiles.py` line 59: `gemini_primary` uses `gemini-3-flash` (wizard) vs `gemini-3-flash-preview` (v5).

## Conclusion
The profiles must be updated to align wizard and v5, and misleading names like `optimal` should be handled carefully (perhaps renaming or adding explicit warnings).
