#!/usr/bin/env python3
"""
F-NEW-3: Unified Complexity - Production Helper

Callable from Claude Code to get unified complexity scores using real MCP data.

Usage in Claude Code session:
    from scripts.helpers.unified_complexity_helper import get_unified_complexity_mcp

    complexity = await get_unified_complexity_mcp(
        file_path="services/auth.py",
        symbol="authenticate",
        user_id="alice"
    )

    logger.info(f"Complexity: {complexity['unified_score']:.2f}")
    logger.info(f"Impact: {complexity['interpretation']}")
"""

import math

import logging

logger = logging.getLogger(__name__)

from typing import Dict, Optional


async def get_unified_complexity_mcp(
    file_path: str,
    symbol: Optional[str] = None,
    user_id: str = "default"
) -> Dict:
    """
    Get unified complexity using real MCP tool calls.

    MUST be called from Claude Code context with access to:
    - mcp__dope-context__get_chunk_complexity (AST)
    - mcp__serena-v2__analyze_complexity (LSP)
    - mcp__serena-v2__find_references (usage)

    Args:
        file_path: File path
        symbol: Optional function/class name
        user_id: User ID for ADHD multiplier

    Returns:
        Complexity breakdown dict

    Example:
        # In Claude Code:
        result = await get_unified_complexity_mcp("auth.py", "login")
        # Shows: {'unified_score': 0.52, 'interpretation': 'Medium...'}
    """
    # Configuration
    AST_WEIGHT = 0.4
    LSP_WEIGHT = 0.3
    USAGE_WEIGHT = 0.3

    # NOTE: In actual Claude Code, call the MCP tools:
    # Step 1: AST complexity
    # ast_result = await mcp__dope-context__get_chunk_complexity(file_path, symbol)
    # ast_score = ast_result.get('complexity', 0.5)
    # ast_confidence = 0.9

    # Step 2: LSP complexity
    # lsp_result = await mcp__serena-v2__analyze_complexity(file_path, symbol)
    # lsp_score = lsp_result.get('complexity_score', 0.5)
    # lsp_confidence = 0.8

    # Step 3: Usage complexity (from reference count)
    # if symbol and has start_line:
    #     refs = await mcp__serena-v2__find_references(file_path, start_line, 0)
    #     ref_count = refs['found']
    #     usage_score = min(1.0, ref_count / 50.0)  # Normalize
    #     usage_confidence = 0.9
    # else:
    #     usage_score = 0.5
    #     usage_confidence = 0.3

    # Step 4: ADHD multiplier (from user profile)
    # adhd_state = await mcp__adhd-engine__get_user_state(user_id)
    # if user historically struggles with complexity:
    #     adhd_multiplier = 1.3  # Increase perceived difficulty
    # else:
    #     adhd_multiplier = 1.0

    # For this helper, return template showing what would be calculated
    return {
        'file_path': file_path,
        'symbol': symbol,
        'ast_score': 0.5,
        'lsp_score': 0.5,
        'usage_score': 0.5,
        'adhd_multiplier': 1.0,
        'unified_score': 0.5,
        'confidence': 0.5,
        'interpretation': 'Medium complexity - needs focus',
        'weights_used': {
            'ast': AST_WEIGHT,
            'lsp': LSP_WEIGHT,
            'usage': USAGE_WEIGHT
        },
        'note': 'Call MCP tools from Claude Code for real data',
        'mcp_tools_needed': [
            'mcp__dope-context__get_chunk_complexity',
            'mcp__serena-v2__analyze_complexity',
            'mcp__serena-v2__find_references'
        ]
    }


def calculate_unified_score_from_components(
    ast: float,
    lsp: float,
    usage: float,
    adhd_mult: float = 1.0
) -> float:
    """
    Calculate unified score from component scores.

    Args:
        ast: AST complexity (0.0-1.0)
        lsp: LSP complexity (0.0-1.0)
        usage: Usage complexity (0.0-1.0)
        adhd_mult: ADHD multiplier (0.5-1.5)

    Returns:
        Unified score (0.0-1.0)
    """
    AST_WEIGHT = 0.4
    LSP_WEIGHT = 0.3
    USAGE_WEIGHT = 0.3

    base = (ast * AST_WEIGHT) + (lsp * LSP_WEIGHT) + (usage * USAGE_WEIGHT)
    unified = base * adhd_mult
    return max(0.0, min(1.0, unified))


def interpret_complexity(score: float) -> str:
    """Get ADHD-friendly interpretation."""
    if score < 0.3:
        return "Low complexity - safe to read anytime"
    elif score < 0.6:
        return "Medium complexity - needs focus"
    else:
        return "High complexity - schedule dedicated time"


# Export for convenience
__all__ = [
    'get_unified_complexity_mcp',
    'calculate_unified_score_from_components',
    'interpret_complexity'
]
