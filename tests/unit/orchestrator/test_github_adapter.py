import os
import subprocess
from unittest.mock import MagicMock, patch
import pytest

from dopemux.orchestrator.github_adapter import GithubAdapter, GithubAdapterError


class TestGithubAdapter:
    @pytest.fixture
    def mock_run(self):
        with patch("subprocess.run") as mock:
            yield mock

    def test_allowlist_enforcement(self):
        adapter = GithubAdapter(allowlist=["DDD-Enterprises/dopemux-mvp"])
        
        # Enforce allowlist: allowed repo
        assert adapter.is_repo_allowed("DDD-Enterprises/dopemux-mvp") is True
        # Reject unauthorized repo
        assert adapter.is_repo_allowed("attacker/malicious-repo") is False
        
        # When calling methods with unauthorized repo, raise GithubAdapterError
        with pytest.raises(GithubAdapterError, match="unauthorized repo"):
            adapter.list_prs("attacker/malicious-repo")

    def test_noninteractive_env_injected(self, mock_run):
        # Configure mocked subprocess response
        mock_response = MagicMock()
        mock_response.returncode = 0
        mock_response.stdout = "[]"
        mock_run.return_value = mock_response

        adapter = GithubAdapter(allowlist=["DDD-Enterprises/dopemux-mvp"])
        adapter.list_prs("DDD-Enterprises/dopemux-mvp")

        # Verify subprocess.run was called
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        
        # Check env contains GH_NONINTERACTIVE = 1
        env = kwargs.get("env", {})
        assert env.get("GH_NONINTERACTIVE") == "1"

    def test_fail_closed_on_gh_error(self, mock_run):
        # Simulate gh execution failing or returning non-zero (e.g. unauthenticated)
        mock_response = MagicMock()
        mock_response.returncode = 1
        mock_response.stderr = "error: not authenticated"
        mock_run.return_value = mock_response

        adapter = GithubAdapter(allowlist=["DDD-Enterprises/dopemux-mvp"])
        
        with pytest.raises(GithubAdapterError, match="GitHub CLI command failed"):
            adapter.list_prs("DDD-Enterprises/dopemux-mvp")

    def test_fail_closed_on_missing_gh(self, mock_run):
        # Simulate gh CLI missing from PATH
        mock_run.side_effect = FileNotFoundError("gh not found")

        adapter = GithubAdapter(allowlist=["DDD-Enterprises/dopemux-mvp"])
        
        with pytest.raises(GithubAdapterError, match="GitHub CLI is not installed"):
            adapter.list_prs("DDD-Enterprises/dopemux-mvp")

    def test_fail_closed_on_timeout(self, mock_run):
        # Simulate gh execution timing out
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["gh"], timeout=15.0)

        adapter = GithubAdapter(allowlist=["DDD-Enterprises/dopemux-mvp"])
        
        with pytest.raises(GithubAdapterError, match="GitHub CLI command timed out"):
            adapter.list_prs("DDD-Enterprises/dopemux-mvp")
