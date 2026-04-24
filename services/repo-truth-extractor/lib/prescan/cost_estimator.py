import logging
from typing import Any, Dict, List
from .models import FileEntry, PrescanConfig

logger = logging.getLogger(__name__)

def _get_pricing_rate(provider: str, model_id: str) -> dict[str, Any]:
    try:
        from lib.spend_ledger import get_model_cost_rate
        rate = get_model_cost_rate(provider=provider, model_id=model_id)
        return {
            "input_1m": float(rate.get("input_cost_per_1m_usd", 0.15)),
            "output_1m": float(rate.get("output_cost_per_1m_usd", 0.60)),
            "source": str(rate.get("pricing_source", "unknown")),
            "pricing_key": str(rate.get("pricing_key", "unknown"))
        }
    except Exception as e:
        logger.warning(f"CostEstimator failed to load authoritative pricing: {e}")
        return {"input_1m": 0.15, "output_1m": 0.60, "source": "fallback", "pricing_key": "fallback"}

class CostEstimator:
    def __init__(self, config: PrescanConfig):
        self.config = config

    def estimate(self, entries: list[FileEntry]) -> dict[str, Any]:
        """Estimate extraction cost based on corpus size and routing hints."""
        pricing = _get_pricing_rate(self.config.provider, self.config.model)
        
        included = [e for e in entries if e.include and not e.is_ghost]
        total_bytes = sum(e.size_bytes for e in included)
        
        # Heuristic: 1 token ~= 3.5 characters/bytes
        chars_per_token = 3.5
        estimated_input_tokens = int(total_bytes / chars_per_token)
        
        # Deduplication savings
        duplicates = [e for e in included if e.is_duplicate]
        dup_bytes = sum(e.size_bytes for e in duplicates)
        dup_tokens = int(dup_bytes / chars_per_token)
        
        # Version chain compression (estimated 80% reduction for non-latest)
        version_members = [e for e in included if e.version_chain_id and not e.is_latest_version]
        version_bytes = sum(e.size_bytes for e in version_members)
        version_savings = int((version_bytes / chars_per_token) * 0.8)
        
        net_input_tokens = max(estimated_input_tokens - dup_tokens - version_savings, 0)
        
        # Phase-aware output heuristic: Blended ~15% output ratio
        estimated_output_tokens = int(net_input_tokens * 0.15)
        
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
                "version_chain_tokens": version_savings,
                "total_savings_tokens": dup_tokens + version_savings,
                "savings_pct": round(((dup_tokens + version_savings) / estimated_input_tokens * 100), 2) if estimated_input_tokens > 0 else 0
            },
            "net_estimates": {
                "input_tokens": net_input_tokens,
                "output_tokens": estimated_output_tokens,
                "total_cost_usd": round(input_cost + output_cost, 4)
            },
            "pricing_basis": {
                "provider": self.config.provider,
                "model": self.config.model,
                "pricing_key": pricing["pricing_key"],
                "pricing_source": pricing["source"],
                "input_1m_usd": pricing["input_1m"],
                "output_1m_usd": pricing["output_1m"]
            }
        }
