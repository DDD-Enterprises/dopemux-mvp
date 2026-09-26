"""MCP response-size control with conservative token-aware truncation.

This module budgets generated MCP payloads. It is intentionally separate from
Voyage request tokenization, which is model-specific and lives in
``utils.model_tokenizer``.
"""

from __future__ import annotations

import json
import logging
import math
import re
from dataclasses import dataclass
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

MCP_MAX_TOKENS = 10_000
SAFE_TOKEN_BUDGET = 9_000
BASE_OVERHEAD_TOKENS = 200
_TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


@dataclass
class TruncationResult:
    truncated: bool
    original_count: int
    final_count: int
    items_removed: int
    chars_removed: int
    estimated_tokens: int
    budget_used_pct: float
    # F-017 / profile-path compatibility: surface budget starvation vs empty.
    budget_starvation: bool = False
    degraded_guarantee_applied: bool = False


def estimate_tokens(text: str) -> int:
    """Conservatively estimate tokens in an MCP response.

    A generic output budget cannot know the downstream model tokenizer. We use
    the larger of a UTF-8 byte heuristic and a lexical/code-punctuation count,
    avoiding the old English-only ``len(text) // 4`` assumption.
    """

    if not text:
        return 0
    byte_estimate = math.ceil(len(text.encode("utf-8")) / 3)
    lexical_estimate = len(_TOKEN_RE.findall(text))
    return max(1, byte_estimate, lexical_estimate)


def estimate_dict_tokens(data: Dict[str, Any]) -> int:
    """Estimate the serialized JSON payload, including keys and separators."""

    try:
        serialized = json.dumps(
            data,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
            default=str,
        )
    except (TypeError, ValueError) as exc:
        logger.warning("Falling back to repr() for token estimation: %s", exc)
        serialized = repr(data)
    return estimate_tokens(serialized)


def truncate_text(
    text: str, max_chars: int, suffix: str = "... [truncated]"
) -> tuple[str, bool]:
    """Backward-compatible character cap used by external callers."""

    if len(text) <= max_chars:
        return text, False
    if max_chars <= len(suffix):
        return suffix[:max_chars], True
    return text[: max_chars - len(suffix)] + suffix, True


def truncate_text_to_tokens(
    text: str,
    max_tokens: int,
    suffix: str = "... [truncated]",
) -> tuple[str, bool]:
    """Truncate at a Unicode-safe character boundary under a token estimate."""

    if estimate_tokens(text) <= max_tokens:
        return text, False
    if max_tokens <= 0:
        return "", True

    suffix_tokens = estimate_tokens(suffix)
    if suffix_tokens >= max_tokens:
        low = 0
        high = len(suffix)
        best_suffix = ""
        while low <= high:
            middle = (low + high) // 2
            candidate = suffix[:middle]
            if estimate_tokens(candidate) <= max_tokens:
                best_suffix = candidate
                low = middle + 1
            else:
                high = middle - 1
        return best_suffix, True

    low = 0
    high = len(text)
    best = ""
    while low <= high:
        middle = (low + high) // 2
        candidate = text[:middle].rstrip() + suffix
        if estimate_tokens(candidate) <= max_tokens:
            best = candidate
            low = middle + 1
        else:
            high = middle - 1

    return best, True


def _cap_oversized_siblings(
    item: Dict[str, Any], *, content_field: str, per_item_tokens: int
) -> int:
    """Trim any other string field so it alone cannot blow the item budget.

    ``search_code`` payloads carry an unbounded ``context`` sibling next to
    the already-truncated content field; without this, one oversized sibling
    makes ``estimate_dict_tokens`` measure the whole dict as over budget and
    the caller silently drops the result (F-017).
    """

    chars_removed = 0
    for key, value in list(item.items()):
        if key == content_field or not isinstance(value, str):
            continue
        if estimate_tokens(value) <= per_item_tokens:
            continue
        shortened, _ = truncate_text_to_tokens(value, per_item_tokens)
        chars_removed += len(value) - len(shortened)
        item[key] = shortened
    return chars_removed


def _degrade_single_result(
    first: Dict[str, Any],
    *,
    content_field: str,
    truncated_flag: str,
    content_suffix: str,
    budget_tokens: int,
) -> tuple[Dict[str, Any], int]:
    """Degrade the first result rather than return an empty list (F-017).

    Non-empty input must never come back as zero results: a caller cannot
    tell that apart from "no matches". Content and every sibling field share
    half of the remaining budget, well under the normal per-item cap, so the
    forced item still has headroom even against a tight budget.
    """

    item = first.copy()
    remaining = max(1, budget_tokens - BASE_OVERHEAD_TOKENS)
    half_budget = max(1, remaining // 2)
    chars_removed = 0

    content = item.get(content_field)
    if isinstance(content, str):
        shortened, _ = truncate_text_to_tokens(
            content, half_budget, suffix=content_suffix
        )
        chars_removed += len(content) - len(shortened)
        item[content_field] = shortened
    item[truncated_flag] = True

    chars_removed += _cap_oversized_siblings(
        item, content_field=content_field, per_item_tokens=half_budget
    )
    # ADR-226 A5a / E17: token_count is an internal budgeting hint, never a
    # client-facing field.
    item.pop("token_count", None)
    return item, chars_removed


def _truncate_results(
    results: List[Dict[str, Any]],
    *,
    content_field: str,
    truncated_flag: str,
    content_suffix: str,
    budget_tokens: int,
    per_item_max_chars: int,
) -> tuple[List[Dict[str, Any]], TruncationResult]:
    if budget_tokens <= BASE_OVERHEAD_TOKENS:
        raise ValueError(
            f"budget_tokens must exceed base overhead ({BASE_OVERHEAD_TOKENS})"
        )

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
    output: List[Dict[str, Any]] = []
    total_tokens = BASE_OVERHEAD_TOKENS
    total_chars_removed = 0
    per_item_tokens = max(1, estimate_tokens("x" * max(0, per_item_max_chars)))

    for result in results:
        item = result.copy()
        content = item.get(content_field)
        if isinstance(content, str):
            # E17: docs payloads already carry a real Voyage-reported
            # token_count for this exact content (docs_pipeline.py); code
            # payloads carry no such key yet (pending the CHUNKING wave).
            # Trust it over the byte/lexical heuristic to decide whether
            # truncation is needed at all, so a known-good count doesn't
            # get second-guessed into an unnecessary truncation. When it
            # says the content already fits, skip the heuristic entirely;
            # when it's absent or the content doesn't fit, truncate_text_to_
            # tokens' own heuristic still finds the cut point (no exact
            # per-substring count is available to do better).
            exact_count = item.get("token_count")
            # bool is an int subclass in Python (isinstance(True, int) is
            # True) -- exclude it explicitly so a corrupt/malicious payload
            # carrying token_count=True can't be read as 1 and silently
            # disable truncation for arbitrarily large content.
            if (
                isinstance(exact_count, bool)
                or not isinstance(exact_count, int)
                or exact_count <= 0
            ):
                exact_count = None
            if exact_count is not None and exact_count <= per_item_tokens:
                shortened, was_truncated = content, False
            else:
                shortened, was_truncated = truncate_text_to_tokens(
                    content,
                    per_item_tokens,
                    suffix=content_suffix,
                )
            item[content_field] = shortened
            item[truncated_flag] = was_truncated
            if was_truncated:
                total_chars_removed += len(content) - len(shortened)

        # token_count is an internal budgeting hint (ADR-226 A5a / E17),
        # never a client-facing field -- consumed above, stripped here.
        item.pop("token_count", None)

        # An untrimmed sibling (e.g. search_code's "context") can otherwise
        # blow the whole-item budget on its own and starve every result
        # (F-017): cap every other string field to the same per-item share.
        total_chars_removed += _cap_oversized_siblings(
            item, content_field=content_field, per_item_tokens=per_item_tokens
        )

        item_tokens = estimate_dict_tokens(item)
        if total_tokens + item_tokens > budget_tokens:
            logger.warning(
                "Token budget reached after %s results "
                "(budget=%s, used=%s, next=%s)",
                len(output),
                budget_tokens,
                total_tokens,
                item_tokens,
            )
            break
        output.append(item)
        total_tokens += item_tokens

    starved = False
    if not output:
        # Non-empty input must never come back empty: an empty list is
        # indistinguishable from "no matches" (F-017). Degrade the first
        # result instead of dropping it. E2/E4: this is the one path where
        # real matches existed but the budget could not accommodate even
        # one of them normally -- both flags were previously declared and
        # never assigned, leaving a starved response indistinguishable from
        # a merely-truncated one.
        starved = True
        degraded, degraded_chars_removed = _degrade_single_result(
            results[0],
            content_field=content_field,
            truncated_flag=truncated_flag,
            content_suffix=content_suffix,
            budget_tokens=budget_tokens,
        )
        output.append(degraded)
        total_chars_removed += degraded_chars_removed
        total_tokens = BASE_OVERHEAD_TOKENS + estimate_dict_tokens(degraded)

    final_count = len(output)
    return output, TruncationResult(
        truncated=(final_count < original_count or total_chars_removed > 0),
        original_count=original_count,
        final_count=final_count,
        items_removed=original_count - final_count,
        chars_removed=total_chars_removed,
        estimated_tokens=total_tokens,
        budget_used_pct=round((total_tokens / budget_tokens) * 100, 2),
        budget_starvation=starved,
        degraded_guarantee_applied=starved,
    )


def truncate_code_results(
    results: List[Dict[str, Any]],
    budget_tokens: int = SAFE_TOKEN_BUDGET,
    per_item_max_chars: int = 2000,
) -> tuple[List[Dict[str, Any]], TruncationResult]:
    return _truncate_results(
        results,
        content_field="code",
        truncated_flag="code_truncated",
        content_suffix="\n... [code truncated for token budget]",
        budget_tokens=budget_tokens,
        per_item_max_chars=per_item_max_chars,
    )


def truncate_docs_results(
    results: List[Dict[str, Any]],
    budget_tokens: int = SAFE_TOKEN_BUDGET,
    per_item_max_chars: int = 2000,
) -> tuple[List[Dict[str, Any]], TruncationResult]:
    return _truncate_results(
        results,
        content_field="text",
        truncated_flag="text_truncated",
        content_suffix="\n... [text truncated for token budget]",
        budget_tokens=budget_tokens,
        per_item_max_chars=per_item_max_chars,
    )
