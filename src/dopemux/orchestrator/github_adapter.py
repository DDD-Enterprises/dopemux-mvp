import os
import subprocess
import json
import yaml
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


class GithubAdapterError(Exception):
    """Custom error raised by the GithubAdapter."""
    pass


class GithubAdapter:
    """GitHub adapter utilizing gh CLI subprocess calls under strict safety invariants."""

    def __init__(self, allowlist: Optional[List[str]] = None):
        self.allowlist = allowlist
        if self.allowlist is None:
            self.allowlist = self._load_allowlist()

    def _load_allowlist(self) -> List[str]:
        default_repo = "DDD-Enterprises/dopemux-mvp"
        path = os.path.expanduser("~/.config/dopemux/github_allowlist.yaml")
        if not os.path.exists(path):
            path = "config/orchestrator/github_allowlist.yaml"
            
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if isinstance(data, dict) and "allowlist" in data:
                        return data["allowlist"]
                    elif isinstance(data, list):
                        return data
            except Exception:
                pass
        return [default_repo]

    def is_repo_allowed(self, repo: str) -> bool:
        if not self.allowlist:
            return False
        return repo in self.allowlist

    def _run_gh(self, cmd: List[str], repo: str) -> str:
        """Run gh CLI command with environment hardening and allowlist enforcement."""
        if not self.is_repo_allowed(repo):
            raise GithubAdapterError(f"unauthorized repo: {repo}")

        # Construct hardened environment
        env = os.environ.copy()
        env["GH_NONINTERACTIVE"] = "1"

        full_cmd = ["gh"] + cmd + ["--repo", repo]

        try:
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                env=env,
                check=False,
                timeout=15.0
            )
        except subprocess.TimeoutExpired as e:
            raise GithubAdapterError("GitHub CLI command timed out after 15 seconds") from e
        except FileNotFoundError as e:
            raise GithubAdapterError("GitHub CLI is not installed or not in PATH") from e

        if result.returncode != 0:
            raise GithubAdapterError(
                f"GitHub CLI command failed with exit code {result.returncode}: {result.stderr.strip()}"
            )

        return result.stdout

    def list_prs(self, repo: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List open pull requests with their checks/reviews."""
        cmd = ["pr", "list"]
        state = "open"
        limit = "30"
        if filters:
            if "state" in filters:
                state = filters["state"]
            if "limit" in filters:
                limit = str(filters["limit"])
            if "base" in filters:
                cmd.extend(["--base", filters["base"]])
            if "head" in filters:
                cmd.extend(["--head", filters["head"]])

        cmd.extend(["--state", state, "--limit", limit, "--json", "number,title,state,statusCheckRollup,reviews,headRefName,headRepositoryOwner,createdAt"])
        output = self._run_gh(cmd, repo)
        try:
            return json.loads(output)
        except Exception as e:
            raise GithubAdapterError(f"Failed to parse pull requests JSON: {e}") from e

    def get_pr(self, repo: str, number: int) -> Dict[str, Any]:
        """Get details for a specific pull request."""
        output = self._run_gh(
            ["pr", "view", str(number), "--json", "number,title,state,statusCheckRollup,reviews,headRefName,headRepositoryOwner,createdAt"],
            repo
        )
        try:
            return json.loads(output)
        except Exception as e:
            raise GithubAdapterError(f"Failed to parse pull request JSON: {e}") from e

    def get_checks(self, repo: str, number: int) -> List[Dict[str, Any]]:
        """Get checks status for a pull request."""
        pr = self.get_pr(repo, number)
        return pr.get("statusCheckRollup") or []

    def get_reviews(self, repo: str, number: int) -> List[Dict[str, Any]]:
        """Get reviews status for a pull request."""
        pr = self.get_pr(repo, number)
        return pr.get("reviews") or []

    def get_branch_age(self, repo: str, number: int) -> float:
        """Get pull request branch age in days since creation."""
        pr = self.get_pr(repo, number)
        created_at_str = pr.get("createdAt")
        if not created_at_str:
            return 0.0
        if created_at_str.endswith("Z"):
            created_at_str = created_at_str[:-1] + "+00:00"
        try:
            created_at = datetime.fromisoformat(created_at_str)
            now = datetime.now(timezone.utc)
            delta = now - created_at
            return delta.total_seconds() / 86400.0
        except Exception as e:
            raise GithubAdapterError(f"Failed to parse branch age: {e}") from e

    def find_proof_path(self, repo: str, number: int) -> Optional[str]:
        """Find the path to the PROOF.json file in the PR's files."""
        output = self._run_gh(
            ["pr", "view", str(number), "--json", "files"],
            repo
        )
        try:
            data = json.loads(output)
            files = data.get("files", [])
            for f in files:
                path = f.get("path", "")
                if path.endswith("PROOF.json"):
                    return path
            return None
        except Exception as e:
            raise GithubAdapterError(f"Failed to find proof path: {e}") from e

    def comment(self, repo: str, pr_number: int, body: str, approval_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a comment on a pull request."""
        self._run_gh(
            ["pr", "comment", str(pr_number), "--body", body],
            repo
        )
        return {
            "success": True,
            "pr_number": pr_number,
            "comment_body_length": len(body),
            "approval_id": approval_id,
            "canonical_writer": "github-api"
        }
