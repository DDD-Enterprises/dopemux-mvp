"""
Token Budget Manager for MCP Response Size Control

Prevents MCP responses from exceeding Claude Code's 10K token limit.
Uses conservative estimation (1 token ≈ 4 chars) for safety.

ADHD Design:
- Progressive truncation (keeps highest-scored results intact)
- Clear truncation indicators (transparency)
- Budget headroom (target 9K to leave margin)
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


# Token estimation constants
CHARS_PER_TOKEN = 4  # Conservative estimate (OpenAI uses ~4 for English)
MCP_MAX_TOKENS = 10000  # Hard limit enforced by Claude Code
SAFE_TOKEN_BUDGET = 9000  # Target budget (10% headroom for safety)
BASE_OVERHEAD_TOKENS = 200  # JSON structure, field names, etc.


@dataclass
class TruncationResult:
    """Result of truncation operation."""

    truncated: bool
    original_count: int
    final_count: int
    items_removed: int
    chars_removed: int
    estimated_tokens: int
    budget_used_pct: float


def estimate_tokens(text: str) -> int:
    """
    Estimate token count from text.

    Uses conservative 1 token ≈ 4 chars for safety.
    Real tokenization varies, but this prevents overruns.

    Args:
        text: Text to estimate

    Returns:
        Estimated token count
    """
    return len(text) // CHARS_PER_TOKEN


def estimate_dict_tokens(data: Dict[str, Any]) -> int:
    """
    Estimate tokens in a dictionary (JSON serialization).

    Args:
        data: Dictionary to estimate

    Returns:
        Estimated token count
    """
    # Serialize to string and estimate
    import json
    try:
        json_str = json.dumps(data)
        return estimate_tokens(json_str)
    except Exception as e:
        # Fallback: rough estimate from string representation
        return estimate_tokens(str(data))


        logger.error(f"Error: {e}")
def truncate_text(text: str, max_chars: int, suffix: str = "... [truncated]") -> tuple[str, bool]:
    """
    Truncate text to maximum character count.

    Args:
        text: Text to truncate
        max_chars: Maximum characters (including suffix)
        suffix: Truncation indicator

    Returns:
        (truncated_text, was_truncated)
    """
    if len(text) <= max_chars:
        return text, False

    # Reserve space for suffix
    available = max_chars - len(suffix)
    if available < 0:
        return suffix, True

    return text[:available] + suffix, True


def truncate_code_results(
    results: List[Dict[str, Any]],
    budget_tokens: int = SAFE_TOKEN_BUDGET,
    per_item_max_chars: int = 2000,
) -> tuple[List[Dict[str, Any]], TruncationResult]:
    """
    Truncate code search results to fit token budget.

    Strategy:
    1. Estimate base overhead (JSON structure)
    2. Process results in order (highest-scored first)
    3. Truncate 'code' field per item to per_item_max_chars
    4. Stop adding results if budget would be exceeded
    5. Mark truncated items with 'truncated' flag

    Args:
        results: Search results with 'code' field
        budget_tokens: Total token budget (default 9K)
        per_item_max_chars: Max chars per code snippet (default 2000 ≈ 500 tokens)

    Returns:
        (truncated_results, truncation_info)
    """
    if not results:
        return results, TruncationResult(
            truncated=False,
            original_count=0,
            final_count=0,
            items_removed=0,
            chars_removed=0,
            estimated_tokens=BASE_OVERHEAD_TOKENS,
            budget_used_pct=0.0,
        )

    original_count = len(results)
    truncated_results = []
    total_tokens = BASE_OVERHEAD_TOKENS
    total_chars_removed = 0

    for result in results:
        # Create copy to avoid modifying original
        truncated_item = result.copy()

        # Truncate 'code' field if present
        if "code" in truncated_item:
            original_code = truncated_item["code"]
            truncated_code, was_truncated = truncate_text(
                original_code,
                per_item_max_chars,
                suffix="\n... [code truncated for token budget]"
            )

            truncated_item["code"] = truncated_code
            truncated_item["code_truncated"] = was_truncated

            if was_truncated:
                chars_removed = len(original_code) - len(truncated_code)
                total_chars_removed += chars_removed

        # Estimate tokens for this item
        item_tokens = estimate_dict_tokens(truncated_item)

        # Check if adding this item would exceed budget
        if total_tokens + item_tokens > budget_tokens:
            logger.warning(
                f"Token budget exceeded after {len(truncated_results)} results. "
                f"Stopping (budget={budget_tokens}, used={total_tokens}, next={item_tokens})"
            )
            break

        truncated_results.append(truncated_item)
        total_tokens += item_tokens

    final_count = len(truncated_results)
    items_removed = original_count - final_count
    budget_used_pct = (total_tokens / budget_tokens) * 100

    return truncated_results, TruncationResult(
        truncated=(items_removed > 0 or total_chars_removed > 0),
        original_count=original_count,
        final_count=final_count,
        items_removed=items_removed,
        chars_removed=total_chars_removed,
        estimated_tokens=total_tokens,
        budget_used_pct=budget_used_pct,
    )


def truncate_docs_results(
    results: List[Dict[str, Any]],
    budget_tokens: int = SAFE_TOKEN_BUDGET,
    per_item_max_chars: int = 2000,
) -> tuple[List[Dict[str, Any]], TruncationResult]:
    """
    Truncate document search results to fit token budget.

    Same strategy as code results, but truncates 'text' field.

    Args:
        results: Search results with 'text' field
        budget_tokens: Total token budget (default 9K)
        per_item_max_chars: Max chars per doc snippet (default 2000)

    Returns:
        (truncated_results, truncation_info)
    """
    if not results:
        return results, TruncationResult(
            truncated=False,
            original_count=0,
            final_count=0,
            items_removed=0,
            chars_removed=0,
            estimated_tokens=BASE_OVERHEAD_TOKENS,
            budget_used_pct=0.0,
        )

    original_count = len(results)
    truncated_results = []
    total_tokens = BASE_OVERHEAD_TOKENS
    total_chars_removed = 0

    for result in results:
        truncated_item = result.copy()

        # Truncate 'text' field if present
        if "text" in truncated_item:
            original_text = truncated_item["text"]
            truncated_text, was_truncated = truncate_text(
                original_text,
                per_item_max_chars,
                suffix="\n... [text truncated for token budget]"
            )

            truncated_item["text"] = truncated_text
            truncated_item["text_truncated"] = was_truncated

            if was_truncated:
                chars_removed = len(original_text) - len(truncated_text)
                total_chars_removed += chars_removed

        # Estimate tokens
        item_tokens = estimate_dict_tokens(truncated_item)

        # Check budget
        if total_tokens + item_tokens > budget_tokens:
            logger.warning(
                f"Token budget exceeded after {len(truncated_results)} doc results. "
                f"Stopping (budget={budget_tokens}, used={total_tokens})"
            )
            break

        truncated_results.append(truncated_item)
        total_tokens += item_tokens

    final_count = len(truncated_results)
    items_removed = original_count - final_count
    budget_used_pct = (total_tokens / budget_tokens) * 100

    return truncated_results, TruncationResult(
        truncated=(items_removed > 0 or total_chars_removed > 0),
        original_count=original_count,
        final_count=final_count,
        items_removed=items_removed,
        chars_removed=total_chars_removed,
        estimated_tokens=total_tokens,
        budget_used_pct=budget_used_pct,
    )
