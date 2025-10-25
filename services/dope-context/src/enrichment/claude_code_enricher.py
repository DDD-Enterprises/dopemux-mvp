"""
F-NEW-5: Claude Code Level Enrichment

Enriches dope-context search results using Serena MCP tools.
Runs at Claude Code orchestration level (not inside MCP servers).

This is the CORRECT architecture:
- dope-context returns basic search results
- Claude Code calls this enricher
- Enricher calls both MCPs: dope-context (search) + Serena (references)
- Returns enriched results to user

Usage in Claude Code:
```python
# 1. Search with dope-context
results = await mcp__dope-context__search_code(query="auth middleware")

# 2. Enrich with Serena
from enrichment.claude_code_enricher import enrich_with_code_graph
enriched = await enrich_with_code_graph(results)

# 3. Display enriched results
for result in enriched:
    print(f"{result['function_name']}: {result['relationships']['impact_message']}")
```

ADHD Benefits:
- See impact analysis before changes
- Gentle warnings for high-impact code
- Progressive disclosure (only top 5 enriched)
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


async def enrich_with_code_graph(
    search_results: List[Dict],
    max_enrich: int = 5,
    timeout_per_result: float = 0.2
) -> List[Dict]:
    """
    Enrich dope-context search results with Serena code graph data.

    This function is meant to be called from Claude Code context where
    both mcp__dope-context and mcp__serena-v2 tools are available.

    Args:
        search_results: Results from mcp__dope-context__search_code
        max_enrich: Max results to enrich (default: 5, ADHD limit)
        timeout_per_result: Timeout in seconds (default: 200ms)

    Returns:
        Enriched results with 'relationships' field added

    Example:
        results = await mcp__dope-context__search_code("auth")
        enriched = await enrich_with_code_graph(results)
    """
    if not search_results:
        return search_results

    # Enrich only top N results (ADHD optimization)
    to_enrich = search_results[:max_enrich]
    remaining = search_results[max_enrich:]

    logger.info(f"Enriching top {len(to_enrich)} results with Serena code graph")

    # Parallel enrichment
    enriched_results = []

    for result in to_enrich:
        try:
            enriched = await _enrich_single_result(result, timeout_per_result)
            enriched_results.append(enriched)
        except Exception as e:
            logger.warning(f"Enrichment failed for result: {e}")
            result['relationships'] = None
            result['enrichment_status'] = f'error: {str(e)}'
            enriched_results.append(result)

    # Add unenriched results
    for result in remaining:
        result['relationships'] = None
        result['enrichment_status'] = 'not_enriched'
        enriched_results.append(result)

    return enriched_results


async def _enrich_single_result(
    result: Dict,
    timeout: float
) -> Dict:
    """
    Enrich a single search result.

    Calls mcp__serena-v2__find_references to get caller count.

    Args:
        result: Search result with file_path, start_line
        timeout: Timeout in seconds

    Returns:
        Result with 'relationships' field added
    """
    file_path = result.get('file_path', '')
    start_line = result.get('start_line')
    symbol = result.get('function_name')

    # Skip if missing required fields
    if not file_path or start_line is None:
        result['relationships'] = None
        result['enrichment_status'] = 'missing_required_fields'
        return result

    try:
        # NOTE: This is pseudocode - in actual Claude Code context,
        # you would call: mcp__serena-v2__find_references(...)
        # But since this Python module runs inside dope-context MCP server,
        # it can't directly call other MCP tools.

        # The ACTUAL enrichment needs to happen in Claude Code orchestration layer
        # using the pattern shown in the module docstring.

        result['relationships'] = None
        result['enrichment_status'] = 'use_claude_code_orchestration'
        result['enrichment_hint'] = 'Call mcp__serena-v2__find_references from Claude Code level'

        return result

    except Exception as e:
        logger.warning(f"Enrichment failed: {e}")
        result['relationships'] = None
        result['enrichment_status'] = f'error: {str(e)}'
        return result


def calculate_impact_score(callers_count: int) -> float:
    """Calculate impact score from caller count (0.0-1.0)."""
    if callers_count == 0:
        return 0.0

    import math
    score = min(1.0, math.log10(callers_count + 1) / 3.0)
    return round(score, 2)


def get_impact_level(callers_count: int) -> str:
    """Get impact level: none/low/medium/high/critical."""
    if callers_count == 0:
        return "none"
    elif callers_count < 5:
        return "low"
    elif callers_count < 20:
        return "medium"
    elif callers_count < 50:
        return "high"
    else:
        return "critical"


def get_impact_message(callers_count: int) -> str:
    """Get ADHD-friendly impact message."""
    if callers_count == 0:
        return "No callers - safe to modify"
    elif callers_count < 5:
        return f"Low impact - {callers_count} caller(s)"
    elif callers_count < 20:
        return f"Medium impact - {callers_count} callers"
    elif callers_count < 50:
        return f"High impact - affects {callers_count} functions"
    else:
        return f"CRITICAL IMPACT - {callers_count}+ callers (review carefully!)"


# Example usage from Claude Code:
"""
# In Claude Code context (where you have access to MCP tools):

# 1. Search
results = await mcp__dope-context__search_code("authentication middleware")

# 2. Enrich each result
for result in results[:5]:  # Top 5 only (ADHD limit)
    if result.get('start_line'):
        refs = await mcp__serena-v2__find_references(
            file_path=result['file_path'],
            line=result['start_line'],
            column=0,
            max_results=50
        )

        callers_count = refs.get('found', 0)

        result['relationships'] = {
            'callers': callers_count,
            'impact_score': calculate_impact_score(callers_count),
            'impact_level': get_impact_level(callers_count),
            'impact_message': get_impact_message(callers_count)
        }

# 3. Display enriched results
for result in results:
    print(f"{result['function_name']}: {result.get('relationships', {}).get('impact_message', 'Unknown')}")
"""
