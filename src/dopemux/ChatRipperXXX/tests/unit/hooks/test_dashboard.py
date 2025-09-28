#!/usr/bin/env python3
"""
Comprehensive test suite for dashboard.py hook
Tests token usage monitoring, pattern analysis, and optimization suggestions
"""

import pytest
import json
import sys
import os
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime

# Import the dashboard module
sys.path.insert(0, '.claude/hooks')
from dashboard import (
    load_patterns, load_session_metrics, format_tokens,
    show_current_usage, show_patterns, show_optimization_suggestions,
    main
)


class TestDashboard:
    """Test suite for dashboard.py hook functionality"""

    def test_load_patterns_empty_directory(self, tmp_path):
        """Test loading patterns from non-existent file"""
        with patch("os.path.exists", return_value=False):
            result = load_patterns()
            assert result == {"sessions": []}

    def test_load_patterns_with_existing_file(self, tmp_path):
        """Test loading patterns from existing file"""
        data_dir = tmp_path / ".claude" / "hooks" / "data"
        data_dir.mkdir(parents=True)

        patterns_file = data_dir / "usage_patterns.json"
        test_data = {
            "sessions": [
                {
                    "timestamp": "2025-01-01T12:00:00",
                    "tool": "test_tool",
                    "estimated_tokens": 1000
                }
            ],
            "last_updated": "2025-01-01T12:00:00"
        }

        with open(patterns_file, 'w') as f:
            json.dump(test_data, f)

        with patch("dashboard.os.path.exists", return_value=True), \
             patch("builtins.open") as mock_open:

            mock_file = MagicMock()
            mock_file.__enter__.return_value = patterns_file.open('r')
            mock_open.return_value = mock_file

            result = load_patterns()
            assert len(result["sessions"]) == 1
            assert result["sessions"][0]["tool"] == "test_tool"

    def test_load_session_metrics_empty_directory(self, tmp_path):
        """Test loading session metrics from non-existent file"""
        with patch("os.path.exists", return_value=False):
            result = load_session_metrics()
            expected = {"current_session": {"current_usage": 0, "tool_calls": []}}
            assert result == expected

    def test_format_tokens_various_sizes(self):
        """Test token formatting for different magnitudes"""
        assert format_tokens(500) == "500"
        assert format_tokens(1500) == "1.5k"
        assert format_tokens(2500) == "2.5k"
        assert format_tokens(100000) == "100.0k"

    @patch('builtins.print')
    def test_show_current_usage_green_status(self, mock_print, capsys):
        """Test current usage display with green status"""
        metrics = {
            "current_session": {
                "current_usage": 10000,
                "token_budget": 200000,
                "tool_calls": []
            }
        }

        with patch("dashboard.load_session_metrics", return_value=metrics):
            show_current_usage()

        captured = capsys.readouterr()
        assert "🟢 GOOD" in captured.out

    @patch('builtins.print')
    def test_show_current_usage_yellow_status(self, mock_print, capsys):
        """Test current usage display with yellow status"""
        metrics = {
            "current_session": {
                "current_usage": 140000,  # 70% usage
                "token_budget": 200000,
                "tool_calls": [
                    {"tool": "zen", "tokens": 29000},
                    {"tool": "task-master-ai", "tokens": 1500}
                ]
            }
        }

        with patch("dashboard.load_session_metrics", return_value=metrics):
            show_current_usage()

        captured = capsys.readouterr()
        assert "🟡 MODERATE" in captured.out
        assert "zen: 29.0k tokens" in captured.out

    @patch('builtins.print')
    def test_show_current_usage_red_status(self, mock_print, capsys):
        """Test current usage display with red status"""
        metrics = {
            "current_session": {
                "current_usage": 180000,  # 90% usage
                "token_budget": 200000,
                "tool_calls": []
            }
        }

        with patch("dashboard.load_session_metrics", return_value=metrics):
            show_current_usage()

        captured = capsys.readouterr()
        assert "🔴 HIGH" in captured.out

    @patch('builtins.print')
    def test_show_patterns_no_data(self, mock_print, capsys):
        """Test patterns display when no data is available"""
        with patch("dashboard.load_patterns", return_value={"sessions": []}):
            show_patterns()

        captured = capsys.readouterr()
        assert "No patterns recorded yet" in captured.out

    @patch('builtins.print')
    def test_show_patterns_with_data(self, mock_print, capsys):
        """Test patterns display with usage data"""
        patterns = {
            "sessions": [
                {
                    "timestamp": "2025-01-01T12:00:00",
                    "tool": "zen",
                    "estimated_tokens": 29000
                },
                {
                    "timestamp": "2025-01-01T12:05:00",
                    "tool": "task-master-ai",
                    "estimated_tokens": 1500
                },
                {
                    "timestamp": "2025-01-01T12:10:00",
                    "tool": "zen",
                    "estimated_tokens": 29000
                }
            ]
        }

        with patch("dashboard.load_patterns", return_value=patterns):
            show_patterns()

        captured = capsys.readouterr()
        assert "Most Used Tools:" in captured.out
        assert "zen: 2x" in captured.out
        assert "task-master-ai: 1x" in captured.out

    @patch('builtins.print')
    def test_show_optimization_suggestions_with_high_usage(self, mock_print, capsys):
        """Test optimization suggestions for high token usage sessions"""
        patterns = {
            "sessions": [
                {
                    "timestamp": "2025-01-01T12:00:00",
                    "tool": "zen",
                    "input": {"files": ["file1.py", "file2.py", "file3.py"]},
                    "estimated_tokens": 29000
                },
                {
                    "timestamp": "2025-01-01T12:05:00",
                    "tool": "task-master-ai",
                    "input": {"withSubtasks": True},
                    "estimated_tokens": 6000
                },
                {
                    "timestamp": "2025-01-01T12:10:00",
                    "tool": "conport",
                    "input": {},
                    "estimated_tokens": 17000
                }
            ]
        }

        with patch("dashboard.load_patterns", return_value=patterns):
            show_optimization_suggestions()

        captured = capsys.readouterr()
        assert "🎯 Use status=pending" in captured.out
        assert "🎯 Add limit=3-5" in captured.out
        assert "🎯 Limit Zen files" in captured.out

    @patch('builtins.print')
    def test_show_optimization_suggestions_no_patterns(self, mock_print, capsys):
        """Test optimization suggestions when no patterns are found"""
        with patch("dashboard.load_patterns", return_value={"sessions": []}):
            show_optimization_suggestions()

        captured = capsys.readouterr()
        assert "No obvious optimizations found" in captured.out

    def test_main_show_current(self, capsys):
        """Test main function with --current argument"""
        with patch("sys.argv", ["dashboard.py", "--current"]), \
             patch("dashboard.show_current_usage"):
            main()

    def test_main_show_patterns(self, capsys):
        """Test main function with --patterns argument"""
        with patch("sys.argv", ["dashboard.py", "--patterns"]), \
             patch("dashboard.show_patterns"):
            main()

    def test_main_show_suggestions(self, capsys):
        """Test main function with --suggestions argument"""
        with patch("sys.argv", ["dashboard.py", "--suggestions"]), \
             patch("dashboard.show_optimization_suggestions"):
            main()

    def test_main_default_show_all(self, capsys):
        """Test main function with no arguments shows all sections"""
        with patch("sys.argv", ["dashboard.py"]), \
             patch("dashboard.show_current_usage"), \
             patch("dashboard.show_patterns"), \
             patch("dashboard.show_optimization_suggestions"):
            main()

    def test_main_show_help(self, capsys):
        """Test main function with --help argument"""
        with patch("sys.argv", ["dashboard.py", "--help"]), \
             patch('builtins.print') as mock_print:
            main()

            # Verify help text is printed
            help_calls = [call for call in mock_print.call_args_list
                         if "🚀 Smart Hooks Dashboard" in str(call)]
            assert len(help_calls) > 0

    def test_main_invalid_argument(self, capsys):
        """Test main function with invalid argument defaults to help"""
        with patch("sys.argv", ["dashboard.py", "--invalid"]), \
             patch('builtins.print') as mock_print:
            main()

            # Should show help for invalid arguments
            help_calls = [call for call in mock_print.call_args_list
                         if "Usage:" in str(call)]
            assert len(help_calls) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])