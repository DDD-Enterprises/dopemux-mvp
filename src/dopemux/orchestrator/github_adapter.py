import os
import subprocess
import json
import yaml
from typing import Dict, Any, List, Optional


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

    def list_prs(self, repo: str) -> List[Dict[str, Any]]:
        """List open pull requests with their checks/reviews."""
        # Use gh pr list with json fields
        output = self._run_gh(
            ["pr", "list", "--state", "open", "--json", "number,title,state,statusCheckRollup,reviews"],
            repo
        )
        try:
            return json.loads(output)
        except Exception as e:
            raise GithubAdapterError(f"Failed to parse pull requests JSON: {e}") from e

    def comment(self, repo: str, pr_number: int, body: str) -> Dict[str, Any]:
        """Create a comment on a pull request."""
        self._run_gh(
            ["pr", "comment", str(pr_number), "--body", body],
            repo
        )
        return {
            "success": True,
            "pr_number": pr_number,
            "comment_body_length": len(body)
        }
