# RTE Cost Implementation: Deep Audit and Stabilization Plan

## 1. Executive Summary
The current Repo Truth Extractor (RTE) cost implementation relies on placeholder baseline pricing ($0.15/$0.60 per 1M tokens) across several key layers, leading to significant underestimation of actual spend when using premium models (e.g., GPT-5.4 at $2.50/$15.00). Furthermore, the token estimation logic uses simplistic character-to-token division heuristics instead of a proper tokenizer. This plan hardens the cost-tracking system by unifying all components under the authoritative `config/pricing.yaml` catalog and implementing accurate tokenization.

## 2. Identified Deficits
- **Stale Baselines**: `lib/spend_ledger.py` defaults to outdated baseline rates.
- **Disconnected Prescan**: `lib/prescan/cost_estimator.py` uses local hardcoded pricing instead of the global registry.
- **Heuristic Inaccuracy**: Both prescan (`cost_estimator.py`, `token_counter.py`) and runtime (`run_extraction_v5.py`) use a fixed `len(text) // 4` ratio for token counting instead of a real tokenizer like `tiktoken`.
- **Missing Market Rates**: The `config/pricing.yaml` lacks current models like Claude 3.5 Sonnet/Haiku and Gemini 1.5 Pro/Flash.
- **Type Safety**: Runtime spend accumulation uses floating-point math in some areas where `Decimal` is required for fiscal precision.

## 3. Stabilization Architecture

### 3.1 Unify Pricing Authority & Update Market Rates
- **Action**: Modify `lib/spend_ledger.py` and `lib/prescan/cost_estimator.py` to use `benchmarking.pricing.catalog.load_pricing_catalog()` as their primary data source.
- **Action**: Update `config/pricing.yaml` with accurate rates for Claude 3.5, Gemini 1.5, and GPT-4o.
- **Fallback**: Maintain the current baseline only as a "fail-closed" fallback for unknown models.

### 3.2 Proper Tokenizer Integration
- **Action**: Modify `lib/prescan/token_counter.py` to make `tiktoken` the default, mandatory tokenizer for all text payloads (prompts, context, responses).
- **Action**: Refactor `run_extraction_v5.py` to import and use `estimate_tokens` instead of its internal `_estimate_text_tokens` division heuristic.
- **Action**: Update `CostEstimator` to utilize the tokenizer for accurate prescan spend forecasting, trading a minor performance hit on the first scan for massive cost accuracy improvements.

### 3.3 Fiscal Precision
- **Action**: Refactor `SpendLedger` to use `Decimal` for all internal cost accumulations, quantizing to 6 decimal places (`0.000001`) to match provider billing granularity.

## 4. Implementation Slices

| Slice | Description | Target Files |
|---|---|---|
| **Slice 1: Market Rates & Authority** | Update `pricing.yaml` and refactor `spend_ledger.py` and `cost_estimator.py` to load from the canonical pricing catalog. | `config/pricing.yaml`, `lib/spend_ledger.py`, `lib/prescan/cost_estimator.py` |
| **Slice 2: Tokenizer Enforcement** | Upgrade `token_counter.py` to default to `tiktoken` (cl100k_base) and replace division heuristics across the system. | `lib/prescan/token_counter.py`, `run_extraction_v5.py`, `lib/prescan/cost_estimator.py` |
| **Slice 3: Precision Upgrade** | Switch `SpendLedger` and `run_extraction_v5.py` accumulation to `Decimal`. | `lib/spend_ledger.py`, `run_extraction_v5.py` |
| **Slice 4: Audit Verification** | Add a comprehensive test suite verifying tokenizer accuracy, cost cap enforcement, and ledger integrity. | `tests/test_fiscal_safety.py` |

*Plan manually updated by Dopemux CLI / GPT-5.2-Pro following PAL connection failure.*