#!/usr/bin/env python3
"""
Comprehensive test suite for pre_context_budget.py hook
Tests token budget management, MCP server optimization, and usage tracking
"""

import pytest
import json
import sys
import os
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime

# Import the hook module
sys.path.insert(0, '.claude/hooks')
from pre_context_budget import (
    CONPORT_STRICT, EXA_MIN_QUERY_LEN, CLAUDE_CONTEXT_MAX_RESULTS,
    TASKMASTER_DEFAULT_LIMIT, ZEN_MAX_FILES, SMART_OPTIMIZATION,
    GENERIC_TERMS, estimate_token_usage, get_smart_suggestions,
    record_usage, main, out
)


class TestPreContextBudget:
    """Test suite for pre_context_budget.py hook functionality"""

    def test_constants_loaded_from_environment(self):
        """Test that configuration constants are loaded from environment"""
        assert isinstance(CONPORT_STRICT, bool)
        assert isinstance(EXA_MIN_QUERY_LEN, int)
        assert isinstance(CLAUDE_CONTEXT_MAX_RESULTS, int)
        assert isinstance(TASKMASTER_DEFAULT_LIMIT, int)
        assert isinstance(ZEN_MAX_FILES, int)
        assert isinstance(SMART_OPTIMIZATION, bool)
        assert isinstance(GENERIC_TERMS, set)

    def test_estimate_token_usage_high_usage_tools(self):
        """Test token estimation for high-usage MCP tools"""
        # Zen (highest usage)
        assert estimate_token_usage("zen", {}) == 29000

        # TaskMaster get_tasks
        assert estimate_token_usage("task-master-ai", {"withSubtasks": False}) == 1500
        assert estimate_token_usage("task-master-ai", {}) == 6000

        # ConPort
        assert estimate_token_usage("conport", {"limit": 5}) == 3000
        assert estimate_token_usage("conport", {}) == 17000

        # Serena
        assert estimate_token_usage("serena", {}) == 15000

        # Claude Context
        assert estimate_token_usage("claude-context", {}) == 5000

        # Exa
        assert estimate_token_usage("exa", {}) == 3000

    def test_estimate_token_usage_other_tools(self):
        """Test token estimation for other MCP tools"""
        assert estimate_token_usage("openmemory", {}) == 500
        assert estimate_token_usage("cli", {}) == 200
        assert estimate_token_usage("fast-markdown", {}) == 1000
        assert estimate_token_usage("unknown_tool", {}) == 1000

    def test_get_smart_suggestions_taskmaster(self):
        """Test smart suggestions for TaskMaster optimization"""
        # Test with unlimited TaskMaster query
        input_data = {"withSubtasks": True}
        suggestions = get_smart_suggestions("task-master-ai", input_data)

        assert len(suggestions) > 0
        assert any("status=pending" in suggestion for suggestion in suggestions)
        assert any("withSubtasks=false" in suggestion for suggestion in suggestions)

    def test_get_smart_suggestions_conport(self):
        """Test smart suggestions for ConPort optimization"""
        input_data = {}  # No limit specified
        suggestions = get_smart_suggestions("conport", input_data)

        assert len(suggestions) > 0
        assert any("limit=3-5" in suggestion for suggestion in suggestions)

    def test_get_smart_suggestions_zen(self):
        """Test smart suggestions for Zen optimization"""
        input_data = {"files": ["file1.py", "file2.py", "file3.py"]}  # Too many files
        suggestions = get_smart_suggestions("zen", input_data)

        assert len(suggestions) > 0
        assert any("Limit Zen files" in suggestion for suggestion in suggestions)

        # Test Zen without continuation_id
        input_data = {"prompt": "This is a very long prompt that should trigger the continuation_id suggestion"}
        suggestions = get_smart_suggestions("zen", input_data)

        assert len(suggestions) > 0
        assert any("continuation_id" in suggestion for suggestion in suggestions)

    @patch('pre_context_budget.SMART_OPTIMIZATION', False)
    def test_record_usage_with_smart_optimization_disabled(self):
        """Test that usage recording is skipped when smart optimization is disabled"""

        with patch("builtins.open") as mock_open:
            record_usage("test_tool", {}, "allow", "test reason")
            mock_open.assert_not_called()

    @patch('pre_context_budget.SMART_OPTIMIZATION', True)
    def test_record_usage_with_smart_optimization_enabled(self, tmp_path):
        """Test usage recording when smart optimization is enabled"""

        # Create temporary data directory
        data_dir = tmp_path / ".claude" / "hooks" / "data"
        data_dir.mkdir(parents=True)

        with patch("os.makedirs"), \
             patch("builtins.open") as mock_open:

            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            record_usage("test_tool", {"param": "value"}, "allow", "test reason")

            # Verify file operations
            assert mock_open.call_count >= 1

    def test_out_function_json_output(self, capsys):
        """Test that out function produces valid JSON output"""
        out("allow", "Test token budget message")

        captured = capsys.readouterr()
        output_data = json.loads(captured.out.strip())

        assert output_data["decision"] == "allow"
        assert output_data["permissionDecisionReason"] == "Test token budget message"

    def test_main_function_conport_strict_mode(self, capsys):
        """Test main function enforces ConPort strict mode"""
        mock_data = {
            "event": "PreToolUse",
            "tool": "conport",
            "toolInput": {"method": "get_active_context"}
        }

        with patch("sys.stdin.read", return_value=json.dumps(mock_data)), \
             patch('pre_context_budget.CONPORT_STRICT', True):
            main()

        captured = capsys.readouterr()
        output_data = json.loads(captured.out.strip())

        assert output_data["decision"] == "ask"
        assert "Use ConPort summaries" in output_data["permissionDecisionReason"]

    def test_main_function_conport_with_limit(self, capsys):
        """Test main function allows ConPort with proper limits"""
        mock_data = {
            "event": "PreToolUse",
            "tool": "conport",
            "toolInput": {"method": "search_decisions_fts", "limit": 5}
        }

        with patch("sys.stdin.read", return_value=json.dumps(mock_data)), \
             patch('pre_context_budget.CONPORT_STRICT', True):
            main()

        captured = capsys.readouterr()
        output_data = json.loads(captured.out.strip())

        assert output_data["decision"] == "allow"

    def test_main_function_exa_query_validation(self, capsys):
        """Test main function validates Exa queries"""
        # Test too short query
        mock_data = {
            "event": "PreToolUse",
            "tool": "exa",
            "toolInput": {"query": "hi"}
        }

        with patch("sys.stdin.read", return_value=json.dumps(mock_data)):
            main()

        captured = capsys.readouterr()
        output_data = json.loads(captured.out.strip())

        assert output_data["decision"] == "ask"
        assert "too broad" in output_data["permissionDecisionReason"]

        # Test generic term
        mock_data["toolInput"]["query"] = "help"
        with patch("sys.stdin.read", return_value=json.dumps(mock_data)):
            main()

        captured = capsys.readouterr()
        output_data = json.loads(captured.out.strip())

        assert output_data["decision"] == "ask"

    def test_main_function_claude_context_limits(self, capsys):
        """Test main function enforces Claude Context result limits"""
        mock_data = {
            "event": "PreToolUse",
            "tool": "claude-context",
            "toolInput": {"max_results": 10}  # Exceeds CLAUDE_CONTEXT_MAX_RESULTS
        }

        with patch("sys.stdin.read", return_value=json.dumps(mock_data)), \
             patch('pre_context_budget.CLAUDE_CONTEXT_MAX_RESULTS', 3):
            main()

        captured = capsys.readouterr()
        output_data = json.loads(captured.out.strip())

        assert output_data["decision"] == "ask"
        assert "Reduce Claude-Context results" in output_data["permissionDecisionReason"]

    def test_main_function_taskmaster_optimization(self, capsys):
        """Test main function enforces TaskMaster query optimization"""
        # Test unlimited TaskMaster query (no status filter)
        mock_data = {
            "event": "PreToolUse",
            "tool": "task-master-ai",
            "toolInput": {"method": "get_tasks"}
        }

        with patch("sys.stdin.read", return_value=json.dumps(mock_data)):
            main()

        captured = capsys.readouterr()
        output_data = json.loads(captured.out.strip())

        assert output_data["decision"] == "ask"
        assert "status filter" in output_data["permissionDecisionReason"]

    def test_main_function_zen_file_limits(self, capsys):
        """Test main function enforces Zen file limits"""
        mock_data = {
            "event": "PreToolUse",
            "tool": "zen",
            "toolInput": {"files": ["file1.py", "file2.py", "file3.py"]}  # Too many files
        }

        with patch("sys.stdin.read", return_value=json.dumps(mock_data)), \
             patch('pre_context_budget.ZEN_MAX_FILES', 1):
            main()

        captured = capsys.readouterr()
        output_data = json.loads(captured.out.strip())

        assert output_data["decision"] == "ask"
        assert "Limit Zen context files" in output_data["permissionDecisionReason"]

    def test_main_function_smart_suggestions_in_response(self, capsys):
        """Test that smart suggestions are included in responses when enabled"""
        mock_data = {
            "event": "PreToolUse",
            "tool": "task-master-ai",
            "toolInput": {"method": "get_tasks", "withSubtasks": True}
        }

        with patch("sys.stdin.read", return_value=json.dumps(mock_data)), \
             patch('pre_context_budget.SMART_OPTIMIZATION', True):
            main()

        captured = capsys.readouterr()
        output_data = json.loads(captured.out.strip())

        assert output_data["decision"] == "ask"
        assert "💡" in output_data["permissionDecisionReason"]
        assert "status=pending" in output_data["permissionDecisionReason"]

    def test_main_function_invalid_event_handling(self, capsys):
        """Test main function handles invalid events gracefully"""
        mock_data = {
            "event": "InvalidEvent",
            "tool": "bash",
            "toolInput": {"command": "ls -la"}
        }

        with patch("sys.stdin.read", return_value=json.dumps(mock_data)):
            main()

        captured = capsys.readouterr()
        # Should not produce output for invalid events
        assert not captured.out.strip()

    def test_main_function_malformed_input_handling(self, capsys):
        """Test main function handles malformed input gracefully"""
        with patch("sys.stdin.read", return_value="invalid json"):
            main()

        captured = capsys.readouterr()
        # Should handle JSON parsing errors gracefully
        assert not captured.out.strip()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])