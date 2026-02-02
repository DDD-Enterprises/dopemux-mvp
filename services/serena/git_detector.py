"""
Git Detection Module for Untracked Work Detection

Detects uncommitted git work without ConPort integration.
Pure git operations, no external dependencies.

Part of Feature 1: Untracked Work Detection
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
import subprocess
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class GitWorkDetector:
    """Detect uncommitted git work in workspace"""

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self._git_available = None

    async def is_git_repo(self) -> bool:
        """Check if workspace is a git repository"""
        if self._git_available is not None:
            return self._git_available

        try:
            result = await self._run_git_command(["rev-parse", "--git-dir"])
            self._git_available = result.returncode == 0
            return self._git_available
        except Exception as e:
            logger.warning(f"Git not available: {e}")
            self._git_available = False
            return False

    async def detect_uncommitted_work(self) -> Dict:
        """
        Detect uncommitted git changes

        Returns:
            {
                "has_uncommitted": bool,
                "branch": str,
                "files": List[str],
                "stats": {"new": int, "modified": int, "deleted": int},
                "common_directory": str,
                "first_change_time": Optional[datetime]
            }
        """
        if not await self.is_git_repo():
            return {
                "has_uncommitted": False,
                "branch": None,
                "files": [],
                "stats": {"new": 0, "modified": 0, "deleted": 0},
                "common_directory": None,
                "first_change_time": None,
                "error": "Not a git repository"
            }

        # Get current branch
        branch = await self._get_current_branch()

        # Get uncommitted files with status
        file_statuses = await self._get_file_statuses()

        # Calculate statistics
        stats = self._calculate_stats(file_statuses)

        # Get files list (names only)
        files = [f["path"] for f in file_statuses]

        # Find common directory
        common_dir = self._find_common_directory(files) if files else None

        # Estimate first change time (oldest modified file)
        first_change = await self._get_oldest_modification_time(files)

        return {
            "has_uncommitted": len(files) > 0,
            "branch": branch,
            "files": files,
            "file_statuses": file_statuses,
            "stats": stats,
            "common_directory": common_dir,
            "first_change_time": first_change,
            "is_feature_branch": self._is_feature_branch(branch)
        }

    async def _get_current_branch(self) -> Optional[str]:
        """Get current git branch name"""
        try:
            result = await self._run_git_command(
                ["branch", "--show-current"]
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception as e:
            logger.warning(f"Failed to get branch: {e}")
            return None

    async def _get_file_statuses(self) -> List[Dict]:
        """
        Get uncommitted files with their status

        Returns:
            [
                {"path": "file.py", "status": "M", "status_name": "modified"},
                {"path": "new.py", "status": "??", "status_name": "new"},
                ...
            ]
        """
        try:
            # Get both staged and unstaged changes
            result = await self._run_git_command(
                ["status", "--porcelain", "--untracked-files=all"]
            )

            if result.returncode != 0:
                return []

            file_statuses = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                # Format: "XY filepath"
                # X = staged status, Y = unstaged status
                status = line[:2].strip()
                filepath = line[3:].strip()

                status_name = self._parse_status_code(status)

                file_statuses.append({
                    "path": filepath,
                    "status": status,
                    "status_name": status_name
                })

            return file_statuses

        except Exception as e:
            logger.warning(f"Failed to get file statuses: {e}")
            return []

    def _parse_status_code(self, status: str) -> str:
        """
        Parse git status code to human-readable name

        Status codes:
        - M: modified
        - A: added
        - D: deleted
        - R: renamed
        - C: copied
        - U: updated but unmerged
        - ??: untracked (new)
        """
        # Check most common cases first
        if status == "M" or status == " M":
            return "modified"
        elif status == "??":
            return "new"
        elif status == "A" or status == " A":
            return "added"
        elif status == "D" or status == " D":
            return "deleted"
        elif status.startswith("R"):
            return "renamed"
        elif status.startswith("C"):
            return "copied"
        elif status == "U":
            return "unmerged"
        else:
            return "unknown"

    def _calculate_stats(self, file_statuses: List[Dict]) -> Dict[str, int]:
        """Calculate file change statistics"""
        stats = {"new": 0, "modified": 0, "deleted": 0, "renamed": 0, "other": 0}

        for file_status in file_statuses:
            status_name = file_status["status_name"]

            if status_name in ["new", "added"]:
                stats["new"] += 1
            elif status_name == "modified":
                stats["modified"] += 1
            elif status_name == "deleted":
                stats["deleted"] += 1
            elif status_name == "renamed":
                stats["renamed"] += 1
            else:
                stats["other"] += 1

        return stats

    def _find_common_directory(self, files: List[str]) -> Optional[str]:
        """
        Find common directory for file list

        Examples:
        - ["src/a.py", "src/b.py"] → "src"
        - ["a.py", "b.py"] → "."
        - ["src/foo/a.py", "src/bar/b.py"] → "src"
        """
        if not files:
            return None

        if len(files) == 1:
            # Single file - return its directory
            path = Path(files[0])
            return str(path.parent) if path.parent != Path(".") else "."

        # Find common prefix
        paths = [Path(f) for f in files]
        parts_list = [p.parts for p in paths]

        # Find common parts
        common_parts = []
        for i in range(min(len(parts) for parts in parts_list)):
            parts_at_i = {parts[i] for parts in parts_list}
            if len(parts_at_i) == 1:
                common_parts.append(parts_at_i.pop())
            else:
                break

        if common_parts:
            return str(Path(*common_parts))
        else:
            return "."

    async def _get_oldest_modification_time(
        self, files: List[str]
    ) -> Optional[datetime]:
        """
        Get modification time of oldest changed file

        Approximates when work started on this set of changes
        """
        if not files:
            return None

        try:
            oldest_time = None

            for filepath in files:
                full_path = self.workspace / filepath
                if not full_path.exists():
                    continue

                mtime = full_path.stat().st_mtime
                file_time = datetime.fromtimestamp(mtime)

                if oldest_time is None or file_time < oldest_time:
                    oldest_time = file_time

            return oldest_time

        except Exception as e:
            logger.warning(f"Failed to get modification times: {e}")
            return None

    def _is_feature_branch(self, branch: Optional[str]) -> bool:
        """
        Check if branch is a feature branch (not main/master/develop)

        Returns True for branches like:
        - feature/auth-system
        - fix/login-bug
        - experimental/new-feature
        - any-custom-branch

        Returns False for:
        - main, master, develop, staging, production
        """
        if not branch:
            return False

        main_branches = ["main", "master", "develop", "development", "staging", "production"]

        return branch.lower() not in main_branches

    async def _run_git_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """
        Run git command asynchronously

        Args:
            args: Git command arguments (e.g., ["status", "--porcelain"])

        Returns:
            CompletedProcess with stdout, stderr, returncode
        """
        cmd = ["git"] + args

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace)
            )

            stdout, stderr = await process.communicate()

            return subprocess.CompletedProcess(
                args=cmd,
                returncode=process.returncode,
                stdout=stdout.decode("utf-8"),
                stderr=stderr.decode("utf-8")
            )

        except Exception as e:
            logger.error(f"Git command failed: {' '.join(cmd)}: {e}")
            raise

    async def generate_work_name(self, detection: Dict) -> str:
        """
        Generate meaningful name for detected work

        Priority cascade:
        1. Branch name (if feature branch)
        2. Common directory
        3. First new file
        4. Timestamp fallback

        Args:
            detection: Result from detect_uncommitted_work()

        Returns:
            Human-readable work name
        """
        # Priority 1: Feature branch name
        if detection.get("is_feature_branch") and detection.get("branch"):
            branch = detection["branch"]
            # "feature/auth-system" → "Auth System Work"
            name = branch.split("/")[-1].replace("-", " ").replace("_", " ")
            return name.title() + " work"

        # Priority 2: Common directory
        if detection.get("common_directory") and detection["common_directory"] != ".":
            dir_name = Path(detection["common_directory"]).name
            return f"{dir_name.title()} changes"

        # Priority 3: First new file
        file_statuses = detection.get("file_statuses", [])
        new_files = [f for f in file_statuses if f["status_name"] in ["new", "added"]]
        if new_files:
            first_file = Path(new_files[0]["path"])
            return f"Experimental work: {first_file.stem}"

        # Priority 4: Timestamp fallback
        timestamp = datetime.now().strftime("%b %d %H:%M")
        return f"Untracked work {timestamp}"

    async def suggest_branch_organization(
        self,
        detection: Dict,
        min_cluster_size: int = 2
    ) -> Dict:
        """
        F4: Auto-Branch Suggestions - Detect when uncommitted work should be split

        Analyzes uncommitted files to detect multiple logical work clusters.
        Suggests creating separate branches for better organization.

        ADHD Benefit: Prevents cognitive overload from mixed contexts

        Args:
            detection: Result from detect_uncommitted_work()
            min_cluster_size: Minimum files per cluster (default 2)

        Returns:
            {
                "should_split": bool (True if 2+ clusters detected),
                "clusters": List[{
                    "name": str (suggested branch name),
                    "files": List[str],
                    "directory": str (common directory),
                    "rationale": str (why this is a cluster)
                }],
                "current_branch": str,
                "suggestion": str (human-readable suggestion)
            }
        """
        file_statuses = detection.get("file_statuses", [])
        files = [f["path"] for f in file_statuses]

        if len(files) < 3:
            # Too few files to suggest splitting
            return {
                "should_split": False,
                "clusters": [],
                "current_branch": detection.get("branch"),
                "suggestion": None,
                "reason": "too_few_files"
            }

        # Cluster files by directory proximity
        clusters = self._cluster_files_by_directory(files, min_cluster_size)

        if len(clusters) < 2:
            # Only one cluster - no need to split
            return {
                "should_split": False,
                "clusters": clusters,
                "current_branch": detection.get("branch"),
                "suggestion": None,
                "reason": "single_cluster"
            }

        # Generate branch names for each cluster
        for cluster in clusters:
            cluster["name"] = self._generate_branch_name(cluster)

        # Create human-readable suggestion
        suggestion = self._format_branch_suggestion(clusters, detection.get("branch"))

        return {
            "should_split": True,
            "clusters": clusters,
            "current_branch": detection.get("branch"),
            "suggestion": suggestion,
            "reason": "multiple_clusters_detected"
        }

    def _cluster_files_by_directory(
        self,
        files: List[str],
        min_size: int = 2
    ) -> List[Dict]:
        """
        Cluster files by directory proximity

        Strategy:
        1. Group files by their parent directory
        2. Merge small groups into larger ones
        3. Return clusters with >= min_size files

        Returns:
            List of clusters: [{
                "files": List[str],
                "directory": str,
                "size": int
            }]
        """
        from collections import defaultdict

        # Group by immediate parent directory
        dir_groups = defaultdict(list)

        for filepath in files:
            path = Path(filepath)
            parent = str(path.parent) if path.parent != Path(".") else "root"
            dir_groups[parent].append(filepath)

        # Convert to cluster format
        clusters = []
        for directory, file_list in dir_groups.items():
            if len(file_list) >= min_size:
                clusters.append({
                    "files": file_list,
                    "directory": directory,
                    "size": len(file_list),
                    "rationale": f"{len(file_list)} files in {directory}"
                })

        # Sort by size (largest first) for better UX
        clusters.sort(key=lambda c: c["size"], reverse=True)

        return clusters

    def _generate_branch_name(self, cluster: Dict) -> str:
        """
        Generate branch name from cluster characteristics

        Priority:
        1. Directory name (services/auth → feature/auth)
        2. File type pattern (all .md files → docs/update)
        3. Fallback to generic name

        Args:
            cluster: Cluster dict with files, directory

        Returns:
            Suggested branch name (e.g., "feature/auth-changes")
        """
        directory = cluster["directory"]
        files = cluster["files"]

        # Priority 1: Use directory name
        if directory != "root" and directory != ".":
            dir_name = Path(directory).name
            # Clean up directory name for branch
            branch_suffix = dir_name.replace("_", "-").replace(" ", "-").lower()
            return f"feature/{branch_suffix}"

        # Priority 2: Detect file type patterns
        extensions = [Path(f).suffix for f in files]
        if len(set(extensions)) == 1:
            ext = extensions[0].lstrip(".")
            if ext == "md":
                return "docs/update"
            elif ext == "py":
                return "refactor/python"
            elif ext in ["ts", "tsx", "js", "jsx"]:
                return "feature/frontend"

        # Priority 3: Generic fallback
        return f"feature/changes-{cluster['size']}-files"

    def _format_branch_suggestion(
        self,
        clusters: List[Dict],
        current_branch: Optional[str]
    ) -> str:
        """
        Format human-readable branch suggestion

        Example output:
        '''
        💡 Suggestion: Split work into 2 focused branches

        Current: main (7 files mixed)

        Suggested organization:
        1. feature/auth (4 files)
           - services/auth/jwt.py
           - services/auth/session.py
           - services/auth/middleware.py
           - tests/auth/test_jwt.py

        2. docs/update (3 files)
           - docs/auth.md
           - docs/api.md
           - README.md

        Benefits:
        ✓ Clearer commit history
        ✓ Easier code review
        ✓ Reduced context switching
        '''
        """
        lines = []
        lines.append(f"💡 Suggestion: Split work into {len(clusters)} focused branches\n")
        lines.append(f"Current: {current_branch or 'unknown'} ({sum(c['size'] for c in clusters)} files mixed)\n")
        lines.append("Suggested organization:")

        for i, cluster in enumerate(clusters, 1):
            lines.append(f"\n{i}. {cluster['name']} ({cluster['size']} files)")
            # Show first 5 files
            for filepath in cluster["files"][:5]:
                lines.append(f"   - {filepath}")
            if len(cluster["files"]) > 5:
                lines.append(f"   ... and {len(cluster['files']) - 5} more")

        lines.append("\nBenefits:")
        lines.append("✓ Clearer commit history")
        lines.append("✓ Easier code review")
        lines.append("✓ Reduced context switching")

        return "\n".join(lines)

    async def check_files_committed(
        self,
        file_list: List[str],
        commit_ref: str = "HEAD"
    ) -> Dict:
        """
        F2: Check if files from tracked work were committed

        Compares file_list against recent commit to detect if work was completed.
        Used to auto-close reminders when work gets committed.

        Args:
            file_list: List of file paths to check (from tracked work)
            commit_ref: Git commit reference (default: HEAD = most recent)

        Returns:
            {
                "committed": bool (True if 80%+ files were committed),
                "commit_percentage": float (0.0-1.0),
                "commit_sha": str (commit hash),
                "commit_message": str,
                "committed_files": List[str] (files from file_list found in commit),
                "commit_date": datetime
            }
        """
        if not file_list:
            return {
                "committed": False,
                "commit_percentage": 0.0,
                "commit_sha": None,
                "commit_message": None,
                "committed_files": [],
                "commit_date": None,
                "error": "No files to check"
            }

        if not await self.is_git_repo():
            return {
                "committed": False,
                "commit_percentage": 0.0,
                "commit_sha": None,
                "commit_message": None,
                "committed_files": [],
                "commit_date": None,
                "error": "Not a git repository"
            }

        try:
            # Get commit SHA
            sha_result = await self._run_git_command(["rev-parse", commit_ref])
            if sha_result.returncode != 0:
                return {
                    "committed": False,
                    "commit_percentage": 0.0,
                    "commit_sha": None,
                    "error": f"Invalid commit ref: {commit_ref}"
                }

            commit_sha = sha_result.stdout.strip()

            # Get files changed in this commit
            diff_result = await self._run_git_command([
                "diff-tree", "--no-commit-id", "--name-only", "-r", commit_ref
            ])

            if diff_result.returncode != 0:
                return {
                    "committed": False,
                    "commit_percentage": 0.0,
                    "commit_sha": commit_sha,
                    "error": "Failed to get commit files"
                }

            commit_files = [
                f.strip() for f in diff_result.stdout.strip().split("\n")
                if f.strip()
            ]

            # Get commit message and date
            log_result = await self._run_git_command([
                "log", "-1", "--format=%s%n%at", commit_ref
            ])

            commit_message = "Unknown"
            commit_date = None

            if log_result.returncode == 0:
                lines = log_result.stdout.strip().split("\n")
                if len(lines) >= 2:
                    commit_message = lines[0]
                    try:
                        commit_timestamp = int(lines[1])
                        commit_date = datetime.fromtimestamp(commit_timestamp)
                    except Exception as e:
                        pass

                        logger.error(f"Error: {e}")
            # Calculate overlap: how many tracked files appear in this commit?
            committed_files = [
                f for f in file_list
                if f in commit_files
            ]

            commit_percentage = len(committed_files) / len(file_list) if file_list else 0.0
            committed = commit_percentage >= 0.8  # 80%+ threshold

            logger.info(
                f"Commit check: {len(committed_files)}/{len(file_list)} files "
                f"({commit_percentage*100:.0f}%) in commit {commit_sha[:8]}"
            )

            return {
                "committed": committed,
                "commit_percentage": commit_percentage,
                "commit_sha": commit_sha,
                "commit_message": commit_message,
                "committed_files": committed_files,
                "commit_date": commit_date.isoformat() if commit_date else None,
                "total_commit_files": len(commit_files),
                "total_tracked_files": len(file_list)
            }

        except Exception as e:
            logger.error(f"Failed to check committed files: {e}")
            return {
                "committed": False,
                "commit_percentage": 0.0,
                "commit_sha": None,
                "error": str(e)
            }
