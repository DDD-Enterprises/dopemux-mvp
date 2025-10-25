#!/usr/bin/env python3
"""
F-NEW-5 Code Graph Enrichment - Claude Code Orchestration Example

Demonstrates how to enrich search results with impact analysis.
CORRECT architecture: Claude Code orchestrates both MCPs.

ADHD Benefit: See blast radius before making changes (reduces anxiety)

Performance: ~80ms for top 5 results (parallel)
"""

import asyncio
import sys
from pathlib import Path

# Add helper path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "helpers"))
from serena_enrichment import (
    calculate_impact_score,
    get_impact_level,
    get_impact_message
)


async def demonstrate_impact_analysis():
    """
    Demonstrate F-NEW-5 code graph enrichment.

    CORRECT Architecture:
    - Claude Code has access to BOTH MCPs
    - Call dope-context for search
    - Call Serena for references
    - Combine results at Claude Code level
    """
    print("="*80)
    print("F-NEW-5: CODE GRAPH ENRICHMENT EXAMPLE")
    print("Architecture: Claude Code orchestrates both MCPs")
    print("="*80)

    # Simulated search results (in real Claude Code, from mcp__dope-context__search_code)
    search_results = [
        {
            'file_path': 'services/auth/middleware.py',
            'function_name': 'authenticate_request',
            'start_line': 42,
            'code': 'async def authenticate_request(request): ...',
            'relevance_score': 0.92
        },
        {
            'file_path': 'services/api/routes.py',
            'function_name': 'protected_route',
            'start_line': 105,
            'code': '@app.route("/api/protected") ...',
            'relevance_score': 0.85
        },
        {
            'file_path': 'services/db/connection.py',
            'function_name': 'get_connection',
            'start_line': 15,
            'code': 'async def get_connection(): ...',
            'relevance_score': 0.78
        }
    ]

    print(f"\n📊 Search returned {len(search_results)} results")
    print(f"   Enriching top {min(5, len(search_results))} with impact analysis...\n")

    # Simulated reference counts (in real Claude Code, from mcp__serena-v2__find_references)
    reference_counts = {
        'authenticate_request': 23,  # High impact
        'protected_route': 8,         # Medium impact
        'get_connection': 47          # High impact (almost critical)
    }

    # Enrich each result
    for i, result in enumerate(search_results, 1):
        symbol = result['function_name']
        file_path = result['file_path']
        start_line = result['start_line']

        print(f"Result {i}: {symbol}")
        print(f"   File: {file_path}:{start_line}")
        print(f"   Relevance: {result['relevance_score']:.2f}")

        # In real Claude Code, you would call:
        # refs = await mcp__serena-v2__find_references(
        #     file_path=file_path,
        #     line=start_line,
        #     column=0,
        #     max_results=50
        # )
        # callers = refs['found']

        # Simulated:
        callers = reference_counts.get(symbol, 0)

        # Calculate impact
        impact_score = calculate_impact_score(callers)
        impact_level = get_impact_level(callers)
        impact_message = get_impact_message(callers)

        # Add to result
        result['relationships'] = {
            'callers': callers,
            'impact_score': impact_score,
            'impact_level': impact_level,
            'impact_message': impact_message
        }

        print(f"\n   📊 Impact Analysis:")
        print(f"      Callers: {callers} functions")
        print(f"      Impact Level: {impact_level.upper()}")
        print(f"      Impact Score: {impact_score:.2f}/1.0")
        print(f"      💬 {impact_message}")
        print()

    print("="*80)
    print("SUMMARY: Enrichment Complete")
    print("="*80)

    for result in search_results:
        rel = result['relationships']
        symbol = f"{result['function_name']:30}"
        level = f"{rel['impact_level']:8}"
        print(f"  {symbol} {level} ({rel['callers']} callers)")

    print("\n" + "="*80)
    print("ADHD BENEFITS:")
    print("  - See impact BEFORE making changes (reduces anxiety)")
    print("  - Gentle warnings for high-impact code (>20 callers)")
    print("  - Progressive disclosure (only top 5 enriched)")
    print("  - Clear action guidance (safe to modify vs review carefully)")
    print("="*80)


async def demonstrate_claude_code_usage():
    """Show actual Claude Code usage pattern"""
    print("\n\n" + "="*80)
    print("ACTUAL CLAUDE CODE USAGE:")
    print("="*80)

    print("""
# Step 1: Search for code
results = await mcp__dope-context__search_code(
    query="authentication middleware",
    top_k=5
)

# Step 2: Enrich with impact analysis
for result in results:
    if result.get('start_line'):
        # Get references from Serena
        refs = await mcp__serena-v2__find_references(
            file_path=result['file_path'],
            line=result['start_line'],
            column=0,
            max_results=50
        )

        callers = refs['found']

        # Calculate impact
        result['impact'] = {
            'callers': callers,
            'level': get_impact_level(callers),
            'message': get_impact_message(callers),
            'score': calculate_impact_score(callers)
        }

# Step 3: Display enriched results
for r in results:
    impact = r.get('impact', {})
    print(f"{r['function_name']}: {impact.get('message', 'Unknown')}")

# Output example:
# authenticate_request: High impact - affects 23 functions
# protected_route: Medium impact - 8 callers
# get_connection: High impact - affects 47 functions
    """)

    print("="*80)
    print("Helper functions available in scripts/helpers/serena_enrichment.py:")
    print("  - calculate_impact_score(callers) → 0.0-1.0")
    print("  - get_impact_level(callers) → none/low/medium/high/critical")
    print("  - get_impact_message(callers) → ADHD-friendly message")
    print("="*80)


if __name__ == "__main__":
    result = asyncio.run(demonstrate_impact_analysis())
    asyncio.run(demonstrate_claude_code_usage())
