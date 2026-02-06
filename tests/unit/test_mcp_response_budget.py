from services.shared.mcp.response_budget import (
    enforce_dict_token_budget,
    estimate_tokens,
    truncate_numbered_lines,
)


def test_estimate_tokens_handles_none():
    assert estimate_tokens(None) == 0
    assert estimate_tokens("abcd") == 1


def test_truncate_numbered_lines_enforces_budget():
    lines = [f"line {i} " + ("x" * 80) for i in range(1, 50)]
    formatted, was_truncated = truncate_numbered_lines(lines, max_tokens=120, start_line_num=10)

    assert was_truncated is True
    assert formatted
    assert "truncated" in formatted[-1]
    assert formatted[0].startswith("    10→")


def test_enforce_dict_token_budget_truncates_verbose_fields():
    result = {
        "summary": "s" * 8000,
        "results": [{"answer": "a" * 5000} for _ in range(20)],
        "sources": [f"src-{i}" for i in range(30)],
        "key_findings": [f"finding-{i}" for i in range(20)],
    }

    enforced = enforce_dict_token_budget(result, tool_name="test_tool", max_tokens=500)

    assert enforced.get("_token_budget_enforced") is True
    assert enforced.get("_original_tokens", 0) > enforced.get("_truncated_tokens", 0)
    assert len(enforced["results"]) <= 5
    assert len(enforced["sources"]) <= 10
    assert len(enforced["key_findings"]) <= 5
    assert "truncated" in enforced["summary"]
