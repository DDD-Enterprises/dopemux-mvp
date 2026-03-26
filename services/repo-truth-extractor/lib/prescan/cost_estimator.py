import logging
from typing import Any, Dict, List
from .models import FileEntry, PrescanConfig

logger = logging.getLogger(__name__)

# xAI Pricing (approximate, based on Grok-1 or similar fast model)
# $0.15 per 1M input tokens
# $0.60 per 1M output tokens
PRICING = {
    "input_1m": 0.15,
    "output_1m": 0.60,
}

class CostEstimator:
    def __init__(self, config: PrescanConfig):
        self.config = config

    def estimate(self, entries: list[FileEntry]) -> dict[str, Any]:
        """Estimate extraction cost based on corpus size and routing hints."""
        included = [e for e in entries if e.include and not e.is_ghost]
        total_bytes = sum(e.size_bytes for e in included)
        
        # Heuristic: 1 token ~= 4 characters (approx 4 bytes for UTF-8 text)
        estimated_input_tokens = total_bytes // 4
        
        # Deduplication savings
        duplicates = [e for e in included if e.is_duplicate]
        dup_bytes = sum(e.size_bytes for e in duplicates)
        dup_tokens = dup_bytes // 4
        
        # Version chain compression (estimated 80% reduction for non-latest)
        version_members = [e for e in included if e.version_chain_id and not e.is_latest_version]
        version_bytes = sum(e.size_bytes for e in version_members)
        version_savings = int((version_bytes // 4) * 0.8)
        
        net_input_tokens = max(estimated_input_tokens - dup_tokens - version_savings, 0)
        
        # Heuristic for output tokens: 10% of input tokens
        estimated_output_tokens = net_input_tokens // 10
        
        input_cost = (net_input_tokens / 1_000_000) * PRICING["input_1m"]
        output_cost = (estimated_output_tokens / 1_000_000) * PRICING["output_1m"]
        
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
                "model": self.config.model,
                "input_1m_usd": PRICING["input_1m"],
                "output_1m_usd": PRICING["output_1m"]
            }
        }
