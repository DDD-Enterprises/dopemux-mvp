from services.shared.mcp.response_budget import (
    budget_usage_pct,
    enforce_dict_token_budget,
    estimate_tokens,
    get_budget_stats,
    record_budget_outcome,
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


def test_budget_usage_pct_handles_zero_budget():
    assert budget_usage_pct(50, 0) == 0.0
    assert budget_usage_pct(50, 100) == 50.0


def test_record_budget_outcome_tracks_truncation_frequency():
    tool = "unit_test_budget_tracking_tool"
    baseline = get_budget_stats(tool)
    base_calls = baseline["calls"]
    base_truncated = baseline["truncated_calls"]

    event1 = record_budget_outcome(tool, tokens_used=90, max_tokens=100, was_truncated=False)
    event2 = record_budget_outcome(tool, tokens_used=120, max_tokens=100, was_truncated=True)

    assert event1["tool_name"] == tool
    assert event1["usage_pct"] == 90.0
    assert event2["usage_pct"] == 120.0
    assert event2["truncated"] is True

    updated = get_budget_stats(tool)
    assert updated["calls"] == base_calls + 2
    assert updated["truncated_calls"] == base_truncated + 1
