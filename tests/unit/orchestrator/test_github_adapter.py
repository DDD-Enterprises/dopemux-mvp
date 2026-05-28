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

    def test_get_pr(self, mock_run):
        mock_response = MagicMock()
        mock_response.returncode = 0
        mock_response.stdout = '{"number": 123, "title": "Test PR", "state": "OPEN"}'
        mock_run.return_value = mock_response

        adapter = GithubAdapter(allowlist=["DDD-Enterprises/dopemux-mvp"])
        res = adapter.get_pr("DDD-Enterprises/dopemux-mvp", 123)
        assert res["number"] == 123
        assert res["title"] == "Test PR"

    def test_get_checks_and_reviews(self, mock_run):
        mock_response = MagicMock()
        mock_response.returncode = 0
        mock_response.stdout = '{"number": 123, "statusCheckRollup": [{"name": "validate", "conclusion": "SUCCESS"}], "reviews": [{"state": "APPROVED"}]}'
        mock_run.return_value = mock_response

        adapter = GithubAdapter(allowlist=["DDD-Enterprises/dopemux-mvp"])
        checks = adapter.get_checks("DDD-Enterprises/dopemux-mvp", 123)
        reviews = adapter.get_reviews("DDD-Enterprises/dopemux-mvp", 123)
        assert len(checks) == 1
        assert checks[0]["name"] == "validate"
        assert len(reviews) == 1
        assert reviews[0]["state"] == "APPROVED"

    def test_get_branch_age(self, mock_run):
        mock_response = MagicMock()
        mock_response.returncode = 0
        from datetime import datetime, timezone, timedelta
        # 3 days ago in ISO 8601
        three_days_ago = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        mock_response.stdout = f'{{"number": 123, "createdAt": "{three_days_ago}"}}'
        mock_run.return_value = mock_response

        adapter = GithubAdapter(allowlist=["DDD-Enterprises/dopemux-mvp"])
        age = adapter.get_branch_age("DDD-Enterprises/dopemux-mvp", 123)
        assert 2.9 < age < 3.1

    def test_find_proof_path(self, mock_run):
        mock_response = MagicMock()
        mock_response.returncode = 0
        mock_response.stdout = '{"files": [{"path": "src/adapter.py"}, {"path": "proof/dmx/TP-013/PROOF.json"}]}'
        mock_run.return_value = mock_response

        adapter = GithubAdapter(allowlist=["DDD-Enterprises/dopemux-mvp"])
        path = adapter.find_proof_path("DDD-Enterprises/dopemux-mvp", 123)
        assert path == "proof/dmx/TP-013/PROOF.json"

    def test_comment(self, mock_run):
        mock_response = MagicMock()
        mock_response.returncode = 0
        mock_response.stdout = "Commented successfully"
        mock_run.return_value = mock_response

        adapter = GithubAdapter(allowlist=["DDD-Enterprises/dopemux-mvp"])
        res = adapter.comment("DDD-Enterprises/dopemux-mvp", 123, "LGTTM!", approval_id="app-123")
        assert res["success"] is True
        assert res["approval_id"] == "app-123"
