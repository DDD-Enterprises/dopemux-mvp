"""
Shared MCP response token-budget utilities.

These helpers provide consistent token estimation and truncation behavior
across MCP servers while preserving compatibility-friendly output.
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Dict, List, Tuple


def estimate_tokens(value: Any) -> int:
    """
    Conservative token estimate used by multiple MCP servers.

    We intentionally keep this simple and deterministic:
    ~1 token per 4 characters.
    """
    if value is None:
        return 0
    return len(str(value)) // 4


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

