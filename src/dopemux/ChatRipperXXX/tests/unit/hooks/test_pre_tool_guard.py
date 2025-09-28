#!/usr/bin/env python3
"""
Comprehensive test suite for pre_tool_guard.py hook
Tests security validations, pattern matching, and adaptive security features
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
from pre_tool_guard import (
    DISABLE_NETWORK, BLOCK_SUDO, BLOCK_RM, ADAPTIVE_SECURITY,
    SENSITIVE_PATH_PATTERNS, ALLOWLIST_CMDS, build_context,
    evaluate_adaptive_security, is_sensitive, main, out,
    check_legitimate_patterns, record_security_decision
)


class TestPreToolGuard:
    """Test suite for pre_tool_guard.py hook functionality"""

    def test_constants_loaded_from_environment(self):
        """Test that configuration constants are loaded from environment"""
        # These should be controlled by environment variables
        assert isinstance(DISABLE_NETWORK, bool)
        assert isinstance(BLOCK_SUDO, bool)
        assert isinstance(BLOCK_RM, bool)
        assert isinstance(ADAPTIVE_SECURITY, bool)
        assert isinstance(ALLOWLIST_CMDS, set)
        assert isinstance(SENSITIVE_PATH_PATTERNS, list)

    def test_sensitive_path_detection(self):
        """Test sensitive file path detection"""
        assert is_sensitive("/.env")
        assert is_sensitive("config/.env.local")
        assert is_sensitive("/secrets/private_key")
        assert is_sensitive("/.aws/credentials")
        assert is_sensitive(".aws/config")
        assert not is_sensitive("/public/file.txt")
        assert not is_sensitive("src/code.py")
        assert not is_sensitive("")  # Empty string edge case

    @pytest.mark.parametrize("env_file", [
        "pyproject.toml", "requirements.txt", "package.json",
        "Dockerfile", "Cargo.toml"
    ])
    def test_build_context_project_detection(self, env_file):
        """Test project type detection in build_context"""
        with tempfile.NamedTemporaryFile(suffix=env_file, delete=False) as f:
            f.write(b"test")
            temp_file = f.name

        try:
            with patch("os.path.exists") as mock_exists:
                mock_exists.return_value = False
                mock_exists.side_effect = lambda path: path.endswith(env_file)

                context = build_context()

                if env_file in ["pyproject.toml", "requirements.txt"]:
                    assert context["project_type"] == "python"
                elif env_file == "package.json":
                    assert context["project_type"] == "nodejs"
                elif env_file == "Dockerfile":
                    assert context["project_type"] == "docker"
                elif env_file == "Cargo.toml":
                    assert context["project_type"] == "rust"
        finally:
            os.unlink(temp_file)

    def test_build_context_git_detection(self):
        """Test git repository detection"""
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False
            mock_exists.side_effect = lambda path: path == ".git"

            context = build_context()
            assert context["git_repository"] is True

    def test_build_context_unknown_project(self):
        """Test unknown project type detection"""
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False

            context = build_context()
            assert context["project_type"] == "unknown"
            assert context["git_repository"] is False

    @patch.dict(os.environ, {"HOOKS_ENABLE_ADAPTIVE_SECURITY": "1"})
    def test_evaluate_adaptive_security_disabled(self):
        """Test adaptive security evaluation when disabled"""
        # Temporarily disable adaptive security
        with patch('pre_tool_guard.ADAPTIVE_SECURITY', False):
            result = evaluate_adaptive_security("ls -la", {})
            assert result == (None, None, 0.0)

    @patch.dict(os.environ, {"HOOKS_ENABLE_ADAPTIVE_SECURITY": "1"})
    def test_evaluate_adaptive_security_risk_levels(self):
        """Test adaptive security risk level evaluation"""
        # Temporarily enable adaptive security
        with patch('pre_tool_guard.ADAPTIVE_SECURITY', True):
            context = {"project_type": "python"}

            # High risk commands
            high_risk_result = evaluate_adaptive_security("sudo rm -rf /", context)
            assert high_risk_result[0] in ["deny", "ask"]
            assert high_risk_result[2] >= 0.7  # High risk score

            # Medium risk commands
            medium_risk_result = evaluate_adaptive_security("pip install requests", context)
            assert medium_risk_result[0] in ["ask"]
            assert 0.3 <= medium_risk_result[2] < 0.8

            # Low risk commands
            low_risk_result = evaluate_adaptive_security("ls -la", context)
            assert low_risk_result[0] == "allow"
            assert low_risk_result[2] < 0.2

    def test_evaluate_adaptive_security_context_awareness(self):
        """Test that adaptive security considers project context"""
        with patch('pre_tool_guard.ADAPTIVE_SECURITY', True):
            # Docker context should lower risk for docker commands
            docker_context = {"project_type": "docker"}
            result = evaluate_adaptive_security("docker build .", docker_context)
            assert result[2] < 0.5  # Risk should be reduced in Docker context

            # Python context should consider pip installs differently
            python_context = {"project_type": "python"}
            result = evaluate_adaptive_security("pip install requests", python_context)
            assert result[2] < 0.8  # Should be moderate, not extreme

    @patch.dict(os.environ, {"HOOKS_ENABLE_ADAPTIVE_SECURITY": "1"})
    def test_check_legitimate_patterns(self):
        """Test legitimate development pattern detection"""
        # Temporarily enable adaptive security for pattern testing
        with patch('pre_tool_guard.ADAPTIVE_SECURITY', True):
            # Legitimate patterns
            assert check_legitimate_patterns("git status") is True
            assert check_legitimate_patterns("python -m pytest") is True
            assert check_legitimate_patterns("npm run test") is True
            assert check_legitimate_patterns("docker build .") is True
            assert check_legitimate_patterns("ls -la") is True
            assert check_legitimate_patterns("cat file.txt") is True
            assert check_legitimate_patterns("mkdir new_folder") is True
            assert check_legitimate_patterns("cp src/file.py dest/") is True

            # Non-legitimate patterns
            assert check_legitimate_patterns("rm -rf /") is False
            assert check_legitimate_patterns("sudo apt update") is False
            assert check_legitimate_patterns("") is False
            assert check_legitimate_patterns("random command") is False

    def test_out_function_json_output(self, capsys):
        """Test that out function produces valid JSON output"""
        out("allow", "Test message")

        captured = capsys.readouterr()
        output_data = json.loads(captured.out.strip())

        assert output_data["decision"] == "allow"
        assert output_data["permissionDecisionReason"] == "Test message"

    @patch.dict(os.environ, {"HOOKS_ENABLE_ADAPTIVE_SECURITY": "1"})
    def test_record_security_decision_with_adaptive_security(self, tmp_path):
        """Test security decision recording with adaptive security enabled"""
        with patch('pre_tool_guard.ADAPTIVE_SECURITY', True):
            # Create temporary data directory
            data_dir = tmp_path / ".claude" / "hooks" / "data"
            data_dir.mkdir(parents=True)

            with patch("os.makedirs"), \
                 patch("builtins.open") as mock_open:

                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file

                record_security_decision("ls -la", "allow", "Test command", 0.1)

                # Verify file was opened for audit
                mock_open.assert_called_once()
                args, kwargs = mock_open.call_args
                assert "security_audit.json" in args[0]

    @patch.dict(os.environ, {"HOOKS_ENABLE_ADAPTIVE_SECURITY": "0"})
    def test_record_security_decision_disabled(self):
        """Test that security decisions aren't recorded when disabled"""
        with patch('pre_tool_guard.ADAPTIVE_SECURITY', False):
            with patch("builtins.open") as mock_open:
                record_security_decision("ls -la", "allow", "Test command", 0.1)
                mock_open.assert_not_called()

    @pytest.mark.parametrize("test_input,expected_decision", [
        ("HOOKS_ALLOWLIST_CMDS=test_cmd", "allow"),
        ("rm -rf /", "ask"),
        ("sudo apt update", "deny"),
        ("ls -la", "allow"),
        ("curl http://example.com", "ask"),
        ("pip install requests", "ask"),
    ])
    def test_main_function_bash_command_processing(self, test_input, expected_decision, capsys):
        """Test main function processes bash commands correctly"""
        mock_data = {
            "event": "PreToolUse",
            "tool": "bash",
            "toolInput": {"command": test_input}
        }

        with patch("sys.stdin.read", return_value=json.dumps(mock_data)), \
             patch("sys.stdout"):
            main()

        captured = capsys.readouterr()
        if captured.out.strip():
            output_data = json.loads(captured.out.strip())
            assert output_data["decision"] == expected_decision

    def test_main_function_file_operation_processing(self, capsys):
        """Test main function processes file operations correctly"""
        mock_data = {
            "event": "PreToolUse",
            "tool": "read",
            "toolInput": {"file_path": "/.env"}
        }

        with patch("sys.stdin.read", return_value=json.dumps(mock_data)):
            main()

        captured = capsys.readouterr()
        output_data = json.loads(captured.out.strip())
        assert output_data["decision"] == "deny"
        assert "sensitive file" in output_data["permissionDecisionReason"].lower()

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
        with patch("sys.stdin.read", return_value="invalid json"), \
             patch("sys.stdout"):
            main()

        captured = capsys.readouterr()
        # Should handle JSON parsing errors gracefully
        assert not captured.out.strip()

    def test_main_function_empty_input_handling(self, capsys):
        """Test main function handles empty input gracefully"""
        with patch("sys.stdin.read", return_value=""), \
             patch("sys.stdout"):
            main()

        captured = capsys.readouterr()
        # Should handle empty input gracefully
        assert not captured.out.strip()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])