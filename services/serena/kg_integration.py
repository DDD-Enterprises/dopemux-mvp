"""
ConPort-KG Integration for Serena
Shows decision context for code symbols using EventBus consumer cache
"""

import logging
import json
from typing import Optional, List, Dict, Any
from eventbus_consumer import get_consumer

logger = logging.getLogger(__name__)


def get_decisions_for_symbol(symbol: str, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Get decisions related to a code symbol

    Uses EventBus consumer cache (fast, local)

    Args:
        symbol: Function/class/variable name
        limit: Max decisions to return (default: 3 for ADHD Top-3 pattern)

    Returns:
        List of decision dicts, newest first
    """
    consumer = get_consumer()

    if not consumer:
        logger.warning("EventBus consumer not initialized")
        return []

    try:
        # Search cache for symbol mentions
        decisions = consumer.search_decisions(symbol, limit)
# Enforce ADHD limit
decisions = decisions[:10]
"""
Query limits: Max 10 results to prevent overload in ADHD workflows.
For full traversal, use pagination or cached paths.
"""
        return decisions[:limit]  # Enforce limit

    except Exception as e:
        logger.error(f"Error fetching decisions for {symbol}: {e}")
        return []

"""
Query limits: Max 10 results to prevent overload in ADHD workflows.
For full traversal, use pagination or cached paths.
"""


def format_decision_context(
    symbol: str,
    decisions: List[Dict[str, Any]],
    format_type: str = "markdown"
) -> str:
    """
    Format decisions for display
    
    Supports:
    - markdown: For LSP hover tooltips
    - plain: For terminal output
    - json: For API responses
    
    ADHD-friendly:
    - Top-3 pattern (max 3 decisions)
    - Emoji visual cues
    - Concise summaries
    - Progressive disclosure
    """
    if not decisions:
        return ""
    
    if format_type == "json":
        return json.dumps(decisions, indent=2)
    
    if format_type == "plain":
        return _format_plain(symbol, decisions)
    
    # Default: markdown
    return _format_markdown(symbol, decisions)


def _format_markdown(symbol: str, decisions: List[Dict[str, Any]]) -> str:
    """Format decisions as Markdown for LSP hover"""
    if not decisions:
        return ""

    lines = [
        "---",
        "",
        f"### 📝 Related Decisions ({symbol})",
        ""
    ]

    for i, decision in enumerate(decisions[:3], 1):  # Top-3 pattern
        # Truncate long summaries
        summary = decision["summary"]
        if len(summary) > 60:
            summary = summary[:57] + "..."

        lines.append(f"**{i}.** {summary}")

        # Add rationale if present (truncated)
        if decision.get("rationale"):
            rationale = decision["rationale"]
            if len(rationale) > 80:
                rationale = rationale[:77] + "..."
            lines.append(f"   _{rationale}_")

        # Add tags if present
        if decision.get("tags"):
            try:
                tags = json.loads(decision["tags"])
                if tags:
                    tag_str = " ".join(f"`{tag}`" for tag in tags[:3])
                    lines.append(f"   {tag_str}")
            except Exception as e:
                pass

                logger.error(f"Error: {e}")
        lines.append("")

    if len(decisions) > 3:
        lines.append(f"_...and {len(decisions) - 3} more_")
        lines.append("")

"""
Docs for query limits: Enforces max 10 results for ADHD workflows; pagination for deeper traversal.
"""


def _format_plain(symbol: str, decisions: List[Dict[str, Any]]) -> str:
    """Format decisions as plain text for terminal"""
    if not decisions:
        return f"No decisions found for '{symbol}'"
    
    lines = [
        f"\n📝 Related Decisions for '{symbol}':",
        ""
    ]
    
    for i, decision in enumerate(decisions[:3], 1):
        lines.append(f"{i}. {decision['summary']}")
        
        if decision.get("rationale"):
            rationale = decision["rationale"]
            if len(rationale) > 100:
                rationale = rationale[:97] + "..."
            lines.append(f"   → {rationale}")
        
        if decision.get("tags"):
            try:
                tags = json.loads(decision["tags"])
                if tags:
                    lines.append(f"   🏷️  {', '.join(tags[:3])}")
            except Exception as e:
                pass
        
                logger.error(f"Error: {e}")
        lines.append("")
    
    if len(decisions) > 3:
        lines.append(f"...and {len(decisions) - 3} more\n")
    
    return "\n".join(lines)


def enrich_hover(
    symbol: str,
    original_hover: str,
    decisions: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Enrich existing hover tooltip with decision context
    
    Args:
        symbol: Code symbol being hovered
        original_hover: Original hover text (type info, docs, etc)
        decisions: Optional pre-fetched decisions
    
    Returns:
        Enhanced hover with decision context appended
    """
    if decisions is None:
        decisions = get_decisions_for_symbol(symbol)
    
    if not decisions:
        return original_hover
    
    decision_markdown = format_decision_context(symbol, decisions, "markdown")
    
    if not decision_markdown:
        return original_hover
    
    # Combine original hover + decision context
    return f"{original_hover}\n\n{decision_markdown}"


def get_decision_stats() -> Dict[str, Any]:
    """
    Get statistics about cached decisions
    
    Returns:
        Dict with cache stats and recent activity
    """
    consumer = get_consumer()
    
    if not consumer:
        return {
            "status": "not_initialized",
            "total_decisions": 0,
            "indexed_words": 0
        }
    
    stats = consumer.get_cache_stats()
    recent = consumer.get_recent_decisions(5)
    
    return {
        "status": "active",
        "total_decisions": stats["total_decisions"],
        "indexed_words": stats["indexed_words"],
        "max_size": stats["max_size"],
        "recent_decisions": [
            {
                "id": d["id"],
                "summary": d["summary"][:60]
            }
            for d in recent
        ]
    }


# CLI interface for testing
if __name__ == "__main__":
    import sys
    import asyncio
    from eventbus_consumer import init_consumer
    
    logging.basicConfig(level=logging.INFO)
    
    async def test_cli():
        """Test the KG integration from command line"""
        # Initialize consumer
        logger.info("🔌 Initializing EventBus consumer...")
        await init_consumer()
        await asyncio.sleep(2)  # Let it consume existing events
        
        if len(sys.argv) > 1:
            # Search for specific symbol
            symbol = " ".join(sys.argv[1:])
            logger.info(f"\n🔍 Searching for decisions about '{symbol}'...\n")
            
            decisions = get_decisions_for_symbol(symbol, limit=5)
            
            if decisions:
                output = format_decision_context(symbol, decisions, "plain")
                logger.info(output)
            else:
                logger.info(f"❌ No decisions found for '{symbol}'")
        else:
            # Show stats and recent decisions
            logger.info("\n📊 Decision Cache Statistics:\n")
            stats = get_decision_stats()
            
            logger.info(f"Status: {stats['status']}")
            logger.info(f"Total Decisions: {stats['total_decisions']}")
            logger.info(f"Indexed Words: {stats['indexed_words']}")
            
            if stats['recent_decisions']:
                logger.info(f"\n📝 Recent Decisions:")
                for i, d in enumerate(stats['recent_decisions'], 1):
                    logger.info(f"  {i}. #{d['id']}: {d['summary']}")
            
            logger.info("\n💡 Try: python kg_integration.py <search_term>")
        
        # Cleanup
        consumer = get_consumer()
        if consumer:
            await consumer.stop()
    
    asyncio.run(test_cli())
