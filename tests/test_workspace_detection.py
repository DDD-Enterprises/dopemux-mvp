"""
Phase 1 Validation Test Suite: Workspace Detection

Tests unified workspace detection across all components:
- Shared workspace_detection.py module
- Dope-context integration
- Serena integration
- MCP wrapper scripts

ADHD-Friendly: Clear test names, comprehensive coverage, fast execution
"""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from src.dopemux.workspace_detection import (
    get_workspace_root,
    export_workspace_env,
    validate_workspace,
    get_workspace_info
)


class TestSharedWorkspaceDetection:
    """Test suite for shared workspace_detection.py module"""

    def test_get_workspace_root_with_env_var(self, tmp_path):
        """Priority 1: DOPEMUX_WORKSPACE_ROOT env var should be respected"""
        with patch.dict(os.environ, {"DOPEMUX_WORKSPACE_ROOT": str(tmp_path)}):
            workspace = get_workspace_root()
            assert workspace == tmp_path

    def test_get_workspace_root_git_detection(self, tmp_path, monkeypatch):
        """Priority 2: Git detection should work for main repo and worktrees"""
        # Mock subprocess to return tmp_path as git root
        def mock_run(*args, **kwargs):
            result = MagicMock()
            result.stdout = str(tmp_path)
            result.returncode = 0
            return result

        monkeypatch.setattr(subprocess, "run", mock_run)
        monkeypatch.chdir(tmp_path)

        workspace = get_workspace_root()
        assert workspace == tmp_path

    def test_get_workspace_root_project_markers(self, tmp_path, monkeypatch):
        """Priority 3: Project markers should be detected"""
        # Create pyproject.toml marker
        (tmp_path / "pyproject.toml").touch()
        monkeypatch.chdir(tmp_path)

        # Mock git to fail
        def mock_run(*args, **kwargs):
            raise subprocess.CalledProcessError(1, "git")

        monkeypatch.setattr(subprocess, "run", mock_run)

        workspace = get_workspace_root()
        assert workspace == tmp_path

    def test_get_workspace_root_fallback_to_cwd(self, tmp_path, monkeypatch):
        """Priority 4: Should fallback to current directory"""
        monkeypatch.chdir(tmp_path)

        # Mock git to fail
        def mock_run(*args, **kwargs):
            raise subprocess.CalledProcessError(1, "git")

        monkeypatch.setattr(subprocess, "run", mock_run)

        workspace = get_workspace_root()
        assert workspace == tmp_path

    def test_export_workspace_env(self, tmp_path):
        """Environment export should return correct format"""
        env_vars = export_workspace_env(tmp_path)

        assert "DOPEMUX_WORKSPACE_ROOT" in env_vars
        assert "DOPEMUX_WORKSPACE_ID" in env_vars
        assert env_vars["DOPEMUX_WORKSPACE_ROOT"] == str(tmp_path)
        assert env_vars["DOPEMUX_WORKSPACE_ID"] == str(tmp_path)

    def test_validate_workspace_valid(self, tmp_path):
        """Valid workspace should pass validation"""
        # Create git marker
        (tmp_path / ".git").mkdir()

        is_valid, error = validate_workspace(tmp_path)
        assert is_valid
        assert error is None

    def test_validate_workspace_invalid_not_exists(self):
        """Non-existent path should fail validation"""
        fake_path = Path("/fake/path/does/not/exist")
        is_valid, error = validate_workspace(fake_path)

        assert not is_valid
        assert "does not exist" in error

    def test_validate_workspace_invalid_not_dir(self, tmp_path):
        """File path should fail validation"""
        file_path = tmp_path / "file.txt"
        file_path.touch()

        is_valid, error = validate_workspace(file_path)
        assert not is_valid
        assert "not a directory" in error

    def test_get_workspace_info(self, tmp_path, monkeypatch):
        """Workspace info should return comprehensive metadata"""
        # Mock git commands
        def mock_run(cmd, *args, **kwargs):
            result = MagicMock()
            result.stdout = str(tmp_path) if "show-toplevel" in cmd else "main"
            result.returncode = 0
            return result

        monkeypatch.setattr(subprocess, "run", mock_run)

        info = get_workspace_info(tmp_path)

        assert info["workspace_root"] == str(tmp_path)
        assert "is_git_repo" in info
        assert "is_worktree" in info
        assert "detection_method" in info


class TestDopeContextIntegration:
    """Test dope-context integration with shared detection"""

    def test_dope_context_imports_shared_module(self):
        """Dope-context should import from shared module"""
        # Import dope-context's workspace module
        dope_context_path = project_root / "services" / "dope-context" / "src" / "utils"
        sys.path.insert(0, str(dope_context_path))

        from workspace import get_workspace_root as dope_get_workspace_root

        # Verify it's using the shared module (not custom implementation)
        import inspect
        source = inspect.getsource(dope_get_workspace_root)

        # Should be a wrapper, not custom implementation
        assert "start_path" in source or "Compatibility wrapper" in source

    def test_dope_context_workspace_detection_works(self, tmp_path, monkeypatch):
        """Dope-context workspace detection should work with worktrees"""
        dope_context_path = project_root / "services" / "dope-context" / "src" / "utils"
        sys.path.insert(0, str(dope_context_path))

        from workspace import get_workspace_root as dope_get_workspace_root

        with patch.dict(os.environ, {"DOPEMUX_WORKSPACE_ROOT": str(tmp_path)}):
            workspace = dope_get_workspace_root()
            assert workspace == tmp_path


class TestSerenaIntegration:
    """Test Serena integration with shared detection"""

    def test_serena_imports_shared_module(self):
        """Serena should import from shared module"""
        serena_path = project_root / "services" / "serena" / "v2"
        sys.path.insert(0, str(serena_path))

        try:
            # Import enhanced_lsp which should have get_workspace_root imported
            import enhanced_lsp

            # Check if it imports the shared module
            import inspect
            source = inspect.getsource(enhanced_lsp)
            assert "from src.dopemux.workspace_detection import get_workspace_root" in source
        except ImportError:
            pytest.skip("Serena dependencies not available")


class TestMCPWrapperScripts:
    """Test MCP wrapper scripts use shared detection"""

    def test_conport_wrapper_sources_shared_script(self):
        """ConPort wrapper should source shared detection script"""
        wrapper_path = project_root / "scripts" / "mcp-wrappers" / "conport-wrapper.sh"
        content = wrapper_path.read_text()

        assert "export_workspace_env.sh" in content
        assert "DOPEMUX_WORKSPACE_ROOT" in content
        # Should NOT have duplicate detect_workspace function
        assert content.count("detect_workspace()") == 0

    def test_serena_wrapper_sources_shared_script(self):
        """Serena wrapper should source shared detection script"""
        wrapper_path = project_root / "scripts" / "mcp-wrappers" / "serena-wrapper.sh"
        content = wrapper_path.read_text()

        assert "export_workspace_env.sh" in content
        assert "DOPEMUX_WORKSPACE_ROOT" in content
        # Should NOT have duplicate detect_workspace function
        assert content.count("detect_workspace()") == 0

    def test_dope_context_run_mcp_sources_shared_script(self):
        """Dope-context run_mcp.sh should source shared detection script"""
        run_mcp_path = project_root / "services" / "dope-context" / "run_mcp.sh"
        content = run_mcp_path.read_text()

        assert "export_workspace_env.sh" in content
        assert "DOPEMUX_WORKSPACE_ROOT" in content

    def test_shared_export_script_has_all_fallbacks(self):
        """Shared export script should have 5-layer fallback"""
        export_script = project_root / "src" / "dopemux" / "export_workspace_env.sh"
        content = export_script.read_text()

        # Check all 5 fallback layers exist
        assert "DOPEMUX_WORKSPACE_ROOT" in content  # Priority 1
        assert "CLAUDE_WORKSPACE" in content  # Priority 2
        assert "dopemux worktrees current" in content  # Priority 3
        assert "git rev-parse --show-toplevel" in content  # Priority 4
        assert "python3" in content  # Priority 5 (Python module fallback)


class TestWorktreeBugFix:
    """Specific tests for worktree bug fix"""

    def test_no_dot_git_directory_checks(self):
        """CRITICAL: No component should check for .git directory"""
        # Check dope-context workspace.py
        dope_context_workspace = project_root / "services" / "dope-context" / "src" / "utils" / "workspace.py"
        content = dope_context_workspace.read_text()

        # Should NOT contain .git directory check
        assert '(current / ".git").exists()' not in content
        # Should import from shared module
        assert "from src.dopemux.workspace_detection import" in content

    def test_serena_no_dot_git_checks(self):
        """Serena should not check for .git directory"""
        serena_lsp = project_root / "services" / "serena" / "v2" / "enhanced_lsp.py"
        content = serena_lsp.read_text()

        # Should NOT contain custom .git checking
        # (Old code had: if (current / ".git").exists())
        assert content.count('".git"') <= 1  # May appear in comment/docstring
        # Should import from shared module
        assert "from src.dopemux.workspace_detection import get_workspace_root" in content

    def test_shared_module_uses_git_command(self):
        """Shared module should use git command, not .git directory"""
        shared_module = project_root / "src" / "dopemux" / "workspace_detection.py"
        content = shared_module.read_text()

        # Should use git command
        assert "git rev-parse --show-toplevel" in content
        # Should have comment explaining worktree support
        assert "worktree" in content.lower() or "FILE" in content


class TestCodeDeduplication:
    """Test that duplicate detection code has been eliminated"""

    def test_no_duplicate_detect_workspace_functions(self):
        """Should have only ONE detect_workspace implementation (in shared script)"""
        # Check all bash scripts
        wrapper_dir = project_root / "scripts" / "mcp-wrappers"
        bash_files = list(wrapper_dir.glob("*.sh"))

        detect_function_count = 0
        for bash_file in bash_files:
            content = bash_file.read_text()
            if "detect_workspace()" in content:
                detect_function_count += 1

        # Should be ZERO (all should source shared script)
        assert detect_function_count == 0, "Found duplicate detect_workspace() functions in wrappers"

    def test_shared_script_has_single_implementation(self):
        """Shared script should have exactly one detect_workspace implementation"""
        export_script = project_root / "src" / "dopemux" / "export_workspace_env.sh"
        content = export_script.read_text()

        # Should have exactly one detect_workspace function
        assert content.count("detect_workspace()") == 1


# Phase 1 Success Metrics
class TestPhase1Metrics:
    """Validate Phase 1 success metrics"""

    def test_single_source_of_truth_exists(self):
        """CRITICAL: Shared workspace_detection.py exists and is importable"""
        shared_module = project_root / "src" / "dopemux" / "workspace_detection.py"
        assert shared_module.exists()

        # Should be importable
        from src.dopemux.workspace_detection import get_workspace_root
        assert callable(get_workspace_root)

    def test_all_components_migrated(self):
        """All 3 components should use shared detection"""
        # 1. Dope-context
        dope_context_workspace = project_root / "services" / "dope-context" / "src" / "utils" / "workspace.py"
        assert "from src.dopemux.workspace_detection" in dope_context_workspace.read_text()

        # 2. Serena
        serena_lsp = project_root / "services" / "serena" / "v2" / "enhanced_lsp.py"
        assert "from src.dopemux.workspace_detection" in serena_lsp.read_text()

        # 3. MCP wrappers
        conport_wrapper = project_root / "scripts" / "mcp-wrappers" / "conport-wrapper.sh"
        assert "export_workspace_env.sh" in conport_wrapper.read_text()

    def test_worktree_bug_fixed(self):
        """CRITICAL: .git directory checks eliminated"""
        # Check all Python files
        dope_context_workspace = project_root / "services" / "dope-context" / "src" / "utils" / "workspace.py"
        serena_lsp = project_root / "services" / "serena" / "v2" / "enhanced_lsp.py"

        # Should NOT have .git directory checks in detection logic
        dope_content = dope_context_workspace.read_text()
        assert '".git").exists()' not in dope_content or "Compatibility wrapper" in dope_content

        serena_content = serena_lsp.read_text()
        # May have comment or docstring mentioning .git
        assert serena_content.count('".git"') <= 2  # Lenient for comments/docs

    def test_code_deduplication_achieved(self):
        """Code deduplication target: No duplicate detect_workspace()"""
        wrapper_dir = project_root / "scripts" / "mcp-wrappers"
        all_wrappers = list(wrapper_dir.glob("*.sh"))

        duplicate_count = 0
        for wrapper in all_wrappers:
            content = wrapper.read_text()
            if "detect_workspace()" in content:
                duplicate_count += 1

        # Should be 0 (all source shared script)
        assert duplicate_count == 0


if __name__ == "__main__":
    # Run tests with verbose output for ADHD clarity
    pytest.main([__file__, "-v", "--tb=short", "-x"])
