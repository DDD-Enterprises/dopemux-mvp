import logging
from typing import Any, Dict, List
from .models import FileEntry, PrescanConfig

logger = logging.getLogger(__name__)

def _get_pricing_rate(provider: str, model_id: str) -> dict[str, Any]:
    """Resolve prescan's pricing rate through the single pricing authority
    (lib.spend_ledger.get_model_cost_rate -> config/pricing.yaml).

    TP-RTE-TRUTH-R2-001 (F-10): this used to catch ANY exception — including
    a catalog load failure (missing/corrupt config/pricing.yaml) — and
    silently substitute a $0.15/$0.60 baseline, indistinguishable from a real
    priced model. A catalog load failure is a startup blocker for costed
    operations, so it now propagates instead of being swallowed. Only an
    UNKNOWN MODEL (catalog loaded fine, this specific route just isn't
    priced) is handled here, marked explicitly rather than given a
    fabricated rate.
    """
    from lib.spend_ledger import get_model_cost_rate

    rate = get_model_cost_rate(provider=provider, model_id=model_id)
    if rate.get("unknown_model"):
        logger.warning(
            "CostEstimator: no priced route for provider=%s model=%s — "
            "reporting UNPRICED, not a fabricated rate.",
            provider,
            model_id,
        )
        return {
            "input_1m": 0.0,
            "output_1m": 0.0,
            "source": str(rate.get("pricing_source", "unpriced_no_catalog_entry")),
            "pricing_key": str(rate.get("pricing_key", "unknown")),
            "unpriced": True,
        }
    return {
        "input_1m": float(rate.get("input_cost_per_1m_usd", 0.0)),
        "output_1m": float(rate.get("output_cost_per_1m_usd", 0.0)),
        "source": str(rate.get("pricing_source", "unknown")),
        "pricing_key": str(rate.get("pricing_key", "unknown")),
        "unpriced": False,
    }

class CostEstimator:
    def __init__(self, config: PrescanConfig):
        self.config = config

    def estimate(self, entries: list[FileEntry]) -> dict[str, Any]:
        """Estimate extraction cost based on corpus size and routing hints.

        TP-RTE-TRUTH-R2-002 (F-12): token counting and output-token
        projection now go through the ONE shared
        extractor.costing.estimate_tokens_from_char_count() /
        project_output_tokens() functions instead of this module's own
        hardcoded chars/3.5 tokenizer + flat-15%-output heuristic, which
        additionally disagreed with run_extraction_v5.py's separate chars/4
        tokenizer and 10%/2% output heuristics (A2 §1.3, ~14% tokenizer
        disagreement + 2-6x output-ratio disagreement on the exact same
        corpus before any model even runs).

        The previous "80% version-chain compression" discount is no longer
        applied to the dollar total: A2 §2.3 found no runtime mechanism that
        achieves it (a pure, unvalidated optimism baked into the estimate).
        Version-chain-eligible bytes are still reported, unpriced-discount,
        under estimated_savings for operator visibility.

        Every assumption behind this estimate (tokenizer used, output-ratio
        lane/family/source) is now printed in the returned ``assumptions``
        block instead of being a hidden constant.
        """
        from extractor.costing import (
            DEFAULT_OUTPUT_LANE,
            HEURISTIC_CHARS_PER_TOKEN,
            estimate_tokens_from_char_count,
            project_output_tokens,
        )

        pricing = _get_pricing_rate(self.config.provider, self.config.model)

        included = [e for e in entries if e.include and not e.is_ghost]
        total_bytes = sum(e.size_bytes for e in included)

        gross_tokens = estimate_tokens_from_char_count(
            total_bytes, provider=self.config.provider, model_id=self.config.model
        )
        estimated_input_tokens = gross_tokens["tokens"]

        # Deduplication savings: is_duplicate is a measured property (real
        # content-hash dedup detection upstream), unlike the version-chain
        # discount below -- duplicate files are genuinely excluded from
        # partitions, so subtracting their tokens from the estimate reflects
        # real behavior, not a guess.
        duplicates = [e for e in included if e.is_duplicate]
        dup_bytes = sum(e.size_bytes for e in duplicates)
        dup_tokens = estimate_tokens_from_char_count(
            dup_bytes, provider=self.config.provider, model_id=self.config.model
        )["tokens"]

        # Version-chain members are NOT excluded or discounted (F-12/A2-5
        # fix): the previous 80%-reduction figure was an unvalidated guess
        # with no corresponding runtime dedup mechanism. Counted at full
        # weight below; the affected byte count is reported separately,
        # unpriced, so the opportunity is visible without silently assuming
        # a discount that was never measured.
        version_members = [e for e in included if e.version_chain_id and not e.is_latest_version]
        version_chain_bytes_unmodeled = sum(e.size_bytes for e in version_members)

        net_input_tokens = max(estimated_input_tokens - dup_tokens, 0)

        output_projection = project_output_tokens(
            net_input_tokens,
            lane=DEFAULT_OUTPUT_LANE,
            provider=self.config.provider,
            model_id=self.config.model,
        )
        estimated_output_tokens = output_projection["output_tokens"]

        input_cost = (net_input_tokens / 1_000_000) * pricing["input_1m"]
        output_cost = (estimated_output_tokens / 1_000_000) * pricing["output_1m"]

        return {
            "corpus_stats": {
                "included_files": len(included),
                "total_bytes": total_bytes,
                "total_tokens_gross": estimated_input_tokens,
            },
            "estimated_savings": {
                "duplicate_tokens": dup_tokens,
                "version_chain_tokens": 0,
                "total_savings_tokens": dup_tokens,
                "savings_pct": round((dup_tokens / estimated_input_tokens * 100), 2) if estimated_input_tokens > 0 else 0,
                # F-12/A2-5: previously this block silently applied an
                # unvalidated 80% "compression" discount to version-chain
                # members. No runtime mechanism measures or achieves that
                # discount, so it is no longer subtracted from
                # net_estimates.input_tokens above. This field reports the
                # affected byte count for operator visibility only.
                "version_chain_bytes_unmodeled": version_chain_bytes_unmodeled,
                "version_chain_note": (
                    "Version-chain members are priced at full weight. A "
                    "prior 80%-reduction assumption was removed (unmeasured, "
                    "no corresponding runtime dedup) -- see A2-5 / F-12."
                ),
            },
            "net_estimates": {
                "input_tokens": net_input_tokens,
                "output_tokens": estimated_output_tokens,
                # UNPRICED means this $0.00 is "we don't know", not "it's
                # free" — see pricing_basis.unpriced (F-10: no fabricated
                # dollar figure for a model with no catalog entry).
                "total_cost_usd": round(input_cost + output_cost, 4)
            },
            "pricing_basis": {
                "provider": self.config.provider,
                "model": self.config.model,
                "pricing_key": pricing["pricing_key"],
                "pricing_source": pricing["source"],
                "input_1m_usd": pricing["input_1m"],
                "output_1m_usd": pricing["output_1m"],
                "unpriced": pricing["unpriced"],
            },
            # F-12 fix: printed assumptions -- every number above is a
            # function of these, made explicit rather than hidden inside a
            # module-local constant.
            "assumptions": {
                "tokenizer": gross_tokens["tokenizer"],
                "tokenizer_confidence": gross_tokens["confidence"],
                "chars_per_token_heuristic": HEURISTIC_CHARS_PER_TOKEN,
                "output_ratio_lane": output_projection["lane"],
                "output_ratio_model_family": output_projection["model_family"],
                "output_ratio": output_projection["output_ratio"],
                "output_ratio_source": output_projection["ratio_source"],
                "note": (
                    "Whole-corpus, single-model prescan estimate "
                    "(PrescanConfig.provider/model), not a per-phase/per-cell "
                    "blended estimate across the active cost profile's "
                    "routing. Treat as rough planning guidance, not the "
                    "runtime --print-cost-preview or ledger authority."
                ),
            },
        }
