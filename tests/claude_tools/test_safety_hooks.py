"""
Unit tests for Claude-Code-Tools safety hooks integration.

Tests command interception, safety rules, and user feedback mechanisms.
"""

import pytest
from pathlib import Path

from dopemux.claude_tools.safety_hooks import SafetyHooks
from dopemux.claude_tools.command_interceptor import CommandInterceptor


class TestSafetyHooks:
    """Test SafetyHooks functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.hooks = SafetyHooks(trash_dir="test_trash")

    def test_rm_interception(self):
        """Test rm command interception."""
        result = self.hooks.check_command("rm test_file.txt")
        assert result['action'] == 'redirect'  # rm commands are redirected to trash
        assert "Redirected to safe deletion" in result['message']

    def test_git_add_interception(self):
        """Test dangerous git add interception."""
        result = self.hooks.check_command("git add .")
        assert not result['allowed']
        assert result['action'] == 'block'
        assert "Dangerous command pattern detected" in result['message']

    def test_env_access_block(self):
        """Test .env file access blocking."""
        result = self.hooks.check_command("cat .env")
        assert not result['allowed']
        assert result['action'] == 'block'
        assert ".env" in result['message']

    def test_grep_suggestion(self):
        """Test grep usage enforcement."""
        result = self.hooks.check_command("grep -r 'pattern' .")
        assert not result['allowed']
        assert result['action'] == 'suggest'  # grep is suggested to be replaced, not blocked
        assert "Use 'rg'" in result['message']

    def test_safe_command_allowance(self):
        """Test safe command allowance."""
        result = self.hooks.check_command("ls -la")
        assert result['allowed']
        assert result['action'] == 'allow'

    def test_trash_redirection(self):
        """Test rm command redirection to trash."""
        # Create a temporary test file
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(delete=False) as f:
            test_file = f.name

        try:
            safe_cmd = self.hooks._redirect_to_trash(f"rm {test_file}")
            assert "mv" in safe_cmd
            assert test_file in safe_cmd
        finally:
            os.unlink(test_file)


class TestCommandInterceptor:
    """Test CommandInterceptor functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interceptor = CommandInterceptor()

    def test_blocked_command(self):
        """Test blocked command interception."""
        from dopemux.claude_tools.command_interceptor import InterceptionResult
        result = self.interceptor.check_command("rm -rf /")
        assert result.result == InterceptionResult.BLOCK
        assert "Attempting to delete root directory" in result.message

    def test_confirmation_required(self):
        """Test confirmation required for git commit."""
        from dopemux.claude_tools.command_interceptor import InterceptionResult
        context = {}
        result = self.interceptor.check_command("git commit -m 'test'", context)
        assert result.result == InterceptionResult.CONFIRM
        assert "Git commit requires confirmation" in result.message

    def test_confirmed_command(self):
        """Test confirmed command allowance."""
        from dopemux.claude_tools.command_interceptor import InterceptionResult
        context = {'confirmed': True}
        result = self.interceptor.check_command("git commit -m 'test'", context)
        assert result.result == InterceptionResult.ALLOW

    def test_safe_command(self):
        """Test safe command allowance."""
        from dopemux.claude_tools.command_interceptor import InterceptionResult
        result = self.interceptor.check_command("echo 'hello world'")
        assert result.result == InterceptionResult.ALLOW

    def test_env_access_interception(self):
        """Test .env access interception."""
        from dopemux.claude_tools.command_interceptor import InterceptionResult
        result = self.interceptor.check_command("cat .env")
        assert result.result == InterceptionResult.BLOCK
        assert ".env" in result.message

    def test_grep_interception(self):
        """Test grep usage interception."""
        from dopemux.claude_tools.command_interceptor import InterceptionResult
        result = self.interceptor.check_command("grep -r 'pattern' src/")
        assert result.result == InterceptionResult.BLOCK
        assert "rg" in result.message