#!/usr/bin/env python3
"""
F-NEW-3 Unified Complexity - Claude Code Orchestration Example

Demonstrates how to use unified complexity intelligence by calling
multiple MCP tools from Claude Code level.

ADHD Benefit: Get accurate cognitive load assessment combining:
- AST complexity (structure)
- LSP complexity (usage patterns)
- ADHD personal adjustments

Performance: <200ms per file analysis
"""

import asyncio
import sys
from pathlib import Path

# Add helper path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "helpers"))
from serena_enrichment import calculate_impact_score, get_impact_level


async def demonstrate_unified_complexity():
    """
    Demonstrate F-NEW-3 unified complexity calculation.

    In actual Claude Code session, you would:
    1. Call mcp__dope-context__get_chunk_complexity (AST score)
    2. Call mcp__serena-v2__analyze_complexity (LSP score)
    3. Call mcp__serena-v2__find_references (usage score)
    4. Combine using weighted formula
    """
    print("="*80)
    print("F-NEW-3: UNIFIED COMPLEXITY INTELLIGENCE EXAMPLE")
    print("="*80)

    # Example file to analyze
    file_path = "services/serena/v2/mcp_server.py"
    symbol = "SerenaV2MCPServer"

    print(f"\nAnalyzing: {file_path}:{symbol}")
    print("\nStep 1: Get AST Complexity (Tree-sitter structural analysis)")
    print("   Call: mcp__dope-context__get_chunk_complexity()")
    print("   Returns: {complexity: 0.45, confidence: 0.9}")
    ast_score = 0.45

    print("\nStep 2: Get LSP Complexity (usage patterns, nesting)")
    print("   Call: mcp__serena-v2__analyze_complexity()")
    print("   Returns: {complexity_score: 0.52, metrics: {...}}")
    lsp_score = 0.52

    print("\nStep 3: Get Usage Complexity (reference count)")
    print("   Call: mcp__serena-v2__find_references()")
    print("   Returns: {found: 15}")
    refs_count = 15
    usage_score = min(1.0, refs_count / 50.0)  # Normalize: 50 refs = 1.0

    print("\nStep 4: Get ADHD Multiplier (personal tolerance)")
    print("   From: ADHD Engine user profile")
    print("   Returns: 1.0 (baseline, could be 0.5-1.5)")
    adhd_mult = 1.0

    print("\nStep 5: Calculate Unified Score")
    print("   Formula: (AST*0.4 + LSP*0.3 + Usage*0.3) × ADHD_multiplier")

    # Weighted combination
    AST_WEIGHT = 0.4
    LSP_WEIGHT = 0.3
    USAGE_WEIGHT = 0.3

    base_score = (ast_score * AST_WEIGHT +
                  lsp_score * LSP_WEIGHT +
                  usage_score * USAGE_WEIGHT)
    unified = base_score * adhd_mult

    print(f"\n   Calculation:")
    print(f"   ({ast_score:.2f} × 0.4) + ({lsp_score:.2f} × 0.3) + ({usage_score:.2f} × 0.3) × {adhd_mult:.1f}")
    print(f"   = {base_score:.3f} × {adhd_mult:.1f}")
    print(f"   = {unified:.3f}")

    # Interpretation
    if unified < 0.3:
        interpretation = "Low complexity - safe to read anytime"
    elif unified < 0.6:
        interpretation = "Medium complexity - needs focus"
    else:
        interpretation = "High complexity - schedule dedicated time"

    print(f"\n✅ Result:")
    print(f"   Unified Complexity: {unified:.3f}")
    print(f"   Interpretation: {interpretation}")
    print(f"   AST: {ast_score:.2f}, LSP: {lsp_score:.2f}, Usage: {usage_score:.2f}")
    print(f"   ADHD Multiplier: {adhd_mult:.1f}x")

    print("\n" + "="*80)
    print("ADHD BENEFITS:")
    print("  - Single unified score (no confusion from multiple sources)")
    print("  - Personalized to your tolerance (ADHD multiplier)")
    print("  - Considers both structure AND real-world usage")
    print("  - 0.0-1.0 scale consistent with other tools")
    print("="*80)

    return unified


if __name__ == "__main__":
    print("\nF-NEW-3: Unified Complexity Intelligence")
    print("Combining AST + LSP + Usage + ADHD for accurate cognitive load\n")

    result = asyncio.run(demonstrate_unified_complexity())

    print(f"\n📊 Final Score: {result:.3f}")

    print("\n💡 To use in Claude Code:")
    print("   1. Search for code: mcp__dope-context__search_code('auth')")
    print("   2. Get AST complexity: mcp__dope-context__get_chunk_complexity(file, symbol)")
    print("   3. Get LSP complexity: mcp__serena-v2__analyze_complexity(file, symbol)")
    print("   4. Get usage: mcp__serena-v2__find_references(file, line, 0)")
    print("   5. Combine using weights: AST(40%) + LSP(30%) + Usage(30%) × ADHD")
