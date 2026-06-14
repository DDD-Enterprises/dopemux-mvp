# Stage 6: Consensus on Launch-Profile Strategy

## 1. Strategy Candidates
1. **Cost-First Default**
   - **Pros:** Lowest initial friction, protects budget, encourages trial runs.
   - **Cons:** Result quality may suffer in advanced phases. Confusing if validators or wizard overrides it silently.

2. **Balanced-OpenRouter Default**
   - **Pros:** A strong middle ground offering consistent quality. Predictable consolidated billing via OpenRouter.
   - **Cons:** Requires explicit opt-in to a paid tier (via API key), potentially blocking users who only have basic free tier access.

3. **Explicit-No-Default Profile Selection**
   - **Pros:** Maximum clarity. Forces the operator to consciously select a budget/provider profile before execution. No hidden default drift.
   - **Cons:** Higher initial friction. Breaks existing "zero-config" scripts that assume a default.

## 2. Evaluation
- **Spend Predictability:** Explicit-No-Default is the safest. Cost-First is safe but might result in unexpected low quality. Balanced-OpenRouter is stable but has higher spend bounds.
- **Credential Burden:** Cost-First requires OpenAI, Gemini, and XAI keys. Balanced-OpenRouter requires an OpenRouter key.
- **Validator/Runtime Equivalence:** A single agreed-upon default or forced-explicit choice unifies `run_extraction_v5.py` and `validate_pre_live_gate_v25.py`.

## 3. Conclusion & Chosen Strategy
**Strategy:** Explicit-No-Default Profile Selection (with a fallback error).
However, to maintain backward compatibility for automated tests and scripts, we must choose a default. Given the wizard's "v5 default" labeling and the validator's target policy, **`balanced_openrouter`** is the consensus choice for the single unified default. We must update `run_extraction_v5.py` to match `validate_pre_live_gate_v25.py` and the wizard. If `balanced_openrouter` is chosen, the documentation must make OpenRouter a prerequisite.
If operators prefer an explicit choice, we will enforce it in the wizard (removing the default parameter value and forcing selection).

**Final Decision:** Align `run_extraction_v5.py` `DEFAULT_ROUTING_POLICY` to `balanced_openrouter`.
