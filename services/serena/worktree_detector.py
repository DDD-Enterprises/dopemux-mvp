"""
Worktree Detector - F002 Component 2

Detects git worktree information and maps all worktrees to main repository.
All worktrees share the same workspace_id (main repo path) for unified
knowledge graph while maintaining worktree-specific metadata.

Part of F002: Multi-Session Support
"""

import subprocess
from pathlib import Path
from typing import Optional, NamedTuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class WorktreeInfo:
    """
    Comprehensive worktree information.

    workspace_id: Always the main repository path (for ConPort unity)
    worktree_path: Current worktree path (None if main)
    branch: Current git branch
    worktree_type: main | worktree | single | not_git
    is_worktree: Whether this is a secondary worktree
    """
    workspace_id: str
    worktree_path: Optional[str]
    branch: Optional[str]
    worktree_type: str
    is_worktree: bool

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "workspace_id": self.workspace_id,
            "worktree_path": self.worktree_path,
            "branch": self.branch,
            "worktree_type": self.worktree_type,
            "is_worktree": self.is_worktree
        }


class WorktreeDetector:
    """
    Detect git worktree information for multi-session support.

    Key Principle: All worktrees → same workspace_id (main repo path)

    ADHD Benefit: Unified knowledge graph across parallel work contexts
    """

    def __init__(self, current_dir: Optional[Path] = None):
        """
        Initialize worktree detector.

        Args:
            current_dir: Directory to analyze (defaults to cwd)
        """
        self.current_dir = current_dir or Path.cwd()

    def detect(self) -> WorktreeInfo:
        """
        Detect worktree information for current directory.

        Returns:
            WorktreeInfo with workspace_id (main repo) and worktree metadata

        Logic:
            1. Check if in git repo → not_git
            2. Get worktree list → single vs multi
            3. Identify main repo path
            4. Determine current worktree type
        """
        try:
            # Step 1: Check if in git repository
            if not self._is_git_repo():
                return self._not_git_result()

            # Step 2: Get current branch
            current_branch = self._get_current_branch()

            # Step 3: Check for worktrees
            worktree_list = self._get_worktree_list()

            if not worktree_list or len(worktree_list) == 1:
                # Single repository (no worktrees)
                return self._single_repo_result(current_branch)

            # Step 4: Multi-worktree setup - identify main repo
            main_repo_path = self._extract_main_repo_path(worktree_list)
            current_path_str = str(self.current_dir.resolve())

            # Step 5: Determine if current dir is main or secondary worktree
            if current_path_str == main_repo_path:
                return self._main_worktree_result(main_repo_path, current_branch)
            else:
                return self._secondary_worktree_result(
                    main_repo_path,
                    current_path_str,
                    current_branch
                )

        except Exception as e:
            logger.error(f"Worktree detection failed: {e}")
            return self._fallback_result()

    def _is_git_repo(self) -> bool:
        """Check if current directory is in a git repository."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.current_dir,
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"Git repo check failed: {e}")
            return False

    def _get_current_branch(self) -> Optional[str]:
        """Get current git branch name."""
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=self.current_dir,
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                branch = result.stdout.strip()
                return branch if branch else None
            return None
        except Exception as e:
            logger.debug(f"Branch detection failed: {e}")
            return None

    def _get_worktree_list(self) -> Optional[list]:
        """
        Get list of all worktrees.

        Returns:
            List of worktree info lines or None
        """
        try:
            result = subprocess.run(
                ['git', 'worktree', 'list'],
                cwd=self.current_dir,
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                lines = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
                return lines if lines else None
            return None
        except Exception as e:
            logger.debug(f"Worktree list failed: {e}")
            return None

    def _extract_main_repo_path(self, worktree_list: list) -> str:
        """
        Extract main repository path from worktree list.

        The main worktree is always the first line in git worktree list.
        """
        if not worktree_list:
            return str(self.current_dir.resolve())

        # First line format: "/path/to/repo  abc1234 [branch-name]"
        first_line = worktree_list[0]
        main_path = first_line.split()[0]  # First token is path
        return main_path

    def _not_git_result(self) -> WorktreeInfo:
        """Result when not in git repository."""
        workspace = str(self.current_dir.resolve())
        logger.info(f"Not in git repo, using current dir as workspace: {workspace}")

        return WorktreeInfo(
            workspace_id=workspace,
            worktree_path=None,
            branch=None,
            worktree_type="not_git",
            is_worktree=False
        )

    def _single_repo_result(self, branch: Optional[str]) -> WorktreeInfo:
        """Result for single repository (no worktrees)."""
        workspace = str(self.current_dir.resolve())
        logger.info(f"Single repo detected: {workspace} (branch: {branch})")

        return WorktreeInfo(
            workspace_id=workspace,
            worktree_path=None,
            branch=branch,
            worktree_type="single",
            is_worktree=False
        )

    def _main_worktree_result(self, main_path: str, branch: Optional[str]) -> WorktreeInfo:
        """Result for main worktree."""
        logger.info(f"Main worktree detected: {main_path} (branch: {branch})")

        return WorktreeInfo(
            workspace_id=main_path,
            worktree_path=main_path,  # Main worktree path same as workspace
            branch=branch,
            worktree_type="main",
            is_worktree=False  # Main worktree is not a "secondary" worktree
        )

    def _secondary_worktree_result(
        self,
        main_path: str,
        current_path: str,
        branch: Optional[str]
    ) -> WorktreeInfo:
        """Result for secondary worktree."""
        logger.info(
            f"Secondary worktree detected: {current_path} "
            f"(main: {main_path}, branch: {branch})"
        )

        return WorktreeInfo(
            workspace_id=main_path,  # All worktrees share main repo workspace_id
            worktree_path=current_path,
            branch=branch,
            worktree_type="worktree",
            is_worktree=True
        )

    def _fallback_result(self) -> WorktreeInfo:
        """Fallback result on detection failure."""
        workspace = str(self.current_dir.resolve())
        logger.warning(f"Worktree detection failed, using fallback: {workspace}")

        return WorktreeInfo(
            workspace_id=workspace,
            worktree_path=None,
            branch=None,
            worktree_type="fallback",
            is_worktree=False
        )

    @staticmethod
    def auto_detect() -> WorktreeInfo:
        """
        Auto-detect worktree info from current working directory.

        Convenience method for common use case.

        Returns:
            WorktreeInfo for current directory
        """
        detector = WorktreeDetector()
        return detector.detect()

    def get_all_worktrees(self) -> list:
        """
        Get list of all worktrees for this repository.

        Returns:
            List of {path, branch, is_current} dicts

        ADHD Use Case: Show all parallel work contexts at startup
        """
        try:
            worktree_list = self._get_worktree_list()
            if not worktree_list:
                return []

            current_path = str(self.current_dir.resolve())
            worktrees = []

            for line in worktree_list:
                # Parse: "/path/to/worktree  abc1234 [branch-name]"
                parts = line.split()
                if len(parts) >= 1:
                    path = parts[0]

                    # Extract branch (between brackets)
                    branch = None
                    if '[' in line and ']' in line:
                        branch_part = line[line.index('[') + 1:line.index(']')]
                        branch = branch_part.strip()

                    worktrees.append({
                        "path": path,
                        "branch": branch,
                        "is_current": path == current_path
                    })

            return worktrees

        except Exception as e:
            logger.error(f"Failed to get all worktrees: {e}")
            return []
