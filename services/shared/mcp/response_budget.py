"""
Shared MCP response token-budget utilities.

These helpers provide consistent token estimation and truncation behavior
across MCP servers while preserving compatibility-friendly output.
"""

from __future__ import annotations

import json
from collections import defaultdict
from copy import deepcopy
from typing import Any, Dict, List, Tuple

_BUDGET_STATS: Dict[str, Dict[str, int]] = defaultdict(
    lambda: {"calls": 0, "truncated_calls": 0}
)


def estimate_tokens(value: Any) -> int:
    """
    Conservative token estimate used by multiple MCP servers.

    We intentionally keep this simple and deterministic:
    ~1 token per 4 characters.
    """
    if value is None:
        return 0
    return len(str(value)) // 4


def budget_usage_pct(tokens_used: int, max_tokens: int) -> float:
    """Return token-budget usage percentage."""
    if max_tokens <= 0:
        return 0.0
    return round((tokens_used / max_tokens) * 100, 2)


def record_budget_outcome(
    tool_name: str,
    tokens_used: int,
    max_tokens: int,
    was_truncated: bool,
) -> Dict[str, Any]:
    """
    Record budget usage/truncation telemetry for a tool call.

    Returns a telemetry dictionary ready to log.
    """
    stats = _BUDGET_STATS[tool_name]
    stats["calls"] += 1
    if was_truncated:
        stats["truncated_calls"] += 1

    calls = stats["calls"]
    truncated_calls = stats["truncated_calls"]
    truncation_rate_pct = round((truncated_calls / calls) * 100, 2) if calls else 0.0

    return {
        "tool_name": tool_name,
        "tokens_used": tokens_used,
        "max_tokens": max_tokens,
        "usage_pct": budget_usage_pct(tokens_used, max_tokens),
        "truncated": was_truncated,
        "calls": calls,
        "truncated_calls": truncated_calls,
        "truncation_rate_pct": truncation_rate_pct,
    }


def get_budget_stats(tool_name: str | None = None) -> Dict[str, Any]:
    """Read in-memory budget telemetry stats."""
    if tool_name is not None:
        entry = _BUDGET_STATS.get(tool_name, {"calls": 0, "truncated_calls": 0})
        calls = entry["calls"]
        truncated_calls = entry["truncated_calls"]
        truncation_rate_pct = round((truncated_calls / calls) * 100, 2) if calls else 0.0
        return {
            "tool_name": tool_name,
            "calls": calls,
            "truncated_calls": truncated_calls,
            "truncation_rate_pct": truncation_rate_pct,
        }

    total_calls = sum(v["calls"] for v in _BUDGET_STATS.values())
    total_truncated = sum(v["truncated_calls"] for v in _BUDGET_STATS.values())
    total_rate = round((total_truncated / total_calls) * 100, 2) if total_calls else 0.0

    return {
        "tools": dict(_BUDGET_STATS),
        "total_calls": total_calls,
        "total_truncated_calls": total_truncated,
        "total_truncation_rate_pct": total_rate,
    }


def _clean_for_json(obj: Any) -> Any:
    """Normalize values so json.dumps works predictably."""
    if obj is None:
        return "None"
    if isinstance(obj, dict):
        return {k: _clean_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean_for_json(item) for item in obj]
    if isinstance(obj, (str, int, float, bool)):
        return obj
    return str(obj)


def truncate_numbered_lines(
    lines: List[str],
    max_tokens: int,
    start_line_num: int = 1,
    base_overhead_tokens: int = 50,
) -> Tuple[List[str], bool]:
    """
    Format numbered lines and truncate to a token budget.

    Returns:
        (formatted_lines, was_truncated)
    """
    result_lines: List[str] = []
    estimated = base_overhead_tokens
    truncated = False

    for i, line in enumerate(lines):
        line_num = start_line_num + i
        formatted = f"{line_num:6d}→{line}"
        line_tokens = estimate_tokens(formatted + "\n")

        if estimated + line_tokens > max_tokens:
            truncated = True
            result_lines.append(
                f"{line_num:6d}→... [truncated: {len(lines) - i} more lines, exceeded {max_tokens} token budget]"
            )
            break

        result_lines.append(formatted)
        estimated += line_tokens

    return result_lines, truncated


def enforce_dict_token_budget(
    result: Dict[str, Any],
    tool_name: str,
    max_tokens: int,
    max_results: int = 5,
    max_sources: int = 10,
    max_findings: int = 5,
    max_answer_chars: int = 1000,
    max_summary_chars: int = 2000,
) -> Dict[str, Any]:
    """
    Enforce a token budget on dictionary-shaped tool results.

    Strategy:
    - If already under budget, return original result as-is.
    - Otherwise truncate known verbose fields and attach metadata.
    """
    try:
        clean = _clean_for_json(result)
        current_tokens = estimate_tokens(json.dumps(clean, indent=2))
    except Exception as exc:
        return {
            "error": f"Token budget enforcement failed: {exc}",
            "tool_name": tool_name,
            "_token_budget_failed": True,
        }

    if current_tokens <= max_tokens:
        return result

    truncated = deepcopy(result)

    if isinstance(truncated.get("results"), list):
        for item in truncated["results"]:
            if isinstance(item, dict) and isinstance(item.get("answer"), str):
                answer = item["answer"]
                if len(answer) > max_answer_chars:
                    item["answer"] = answer[:max_answer_chars] + "... [truncated]"
        if len(truncated["results"]) > max_results:
            original_count = len(truncated["results"])
            truncated["results"] = truncated["results"][:max_results]
            truncated["results_truncated"] = True
            truncated["original_result_count"] = original_count

    if isinstance(truncated.get("sources"), list) and len(truncated["sources"]) > max_sources:
        truncated["sources"] = truncated["sources"][:max_sources]
        truncated["sources_truncated"] = True

    if isinstance(truncated.get("summary"), str) and len(truncated["summary"]) > max_summary_chars:
        truncated["summary"] = (
            truncated["summary"][:max_summary_chars]
            + "\n\n... [truncated to fit MCP token budget]"
        )

    if isinstance(truncated.get("key_findings"), list) and len(truncated["key_findings"]) > max_findings:
        truncated["key_findings"] = truncated["key_findings"][:max_findings]

    truncated["_token_budget_enforced"] = True
    truncated["_original_tokens"] = current_tokens
    truncated["_truncated_tokens"] = estimate_tokens(json.dumps(_clean_for_json(truncated)))

    return truncated
