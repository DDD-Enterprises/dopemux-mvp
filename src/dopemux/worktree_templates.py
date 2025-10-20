#!/usr/bin/env python3
"""
Worktree Template System

Intelligently copies configuration and settings from main repository to new worktrees,
preserving user customizations while providing a consistent baseline.

Key Features:
- Smart file copying with user customization preservation
- Template inheritance from main repo
- .gitignore respect (never copy ignored files)
- ADHD-optimized: Progressive setup, clear feedback

Design Principle: "Copy what makes sense, preserve what's unique"
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .workspace_detection import get_workspace_root


class WorktreeTemplateManager:
    """
    Manages template-based configuration for worktrees.

    **Template Philosophy**:
    - Copy project structure (not personal config)
    - Respect .gitignore (don't copy build artifacts)
    - Preserve user customizations in worktree
    - Provide sane defaults from main repo

    **Files to Copy** (baseline):
    - .dopemux/ project configuration
    - .env.example (not .env - that's personal)
    - Editor configs (.editorconfig, .prettierrc)
    - Linting configs (.eslintrc, .pylintrc)

    **Files to SKIP**:
    - .env (personal secrets)
    - .claude.json (managed by auto-configurator)
    - .git (managed by git worktree)
    - node_modules/, venv/, __pycache__ (build artifacts)
    - Any .gitignore'd files
    """

    def __init__(self):
        """Initialize template manager."""
        self.main_repo = self._get_main_repo()

    def _get_main_repo(self) -> Optional[Path]:
        """
        Get main repository path (not a worktree).

        Returns:
            Main repo path or None if not in git repo
        """
        try:
            import subprocess

            # Get git common dir (points to main .git)
            result = subprocess.run(
                ["git", "rev-parse", "--git-common-dir"],
                capture_output=True,
                text=True,
                check=True,
                timeout=2
            )

            git_common = Path(result.stdout.strip()).resolve()

            # Main repo's .git is a directory, worktree's .git is a file
            if git_common.name == ".git":
                main_repo = git_common.parent
            else:
                # Already in main repo
                main_repo = git_common.parent

            return main_repo

        except Exception:
            return None

    def get_template_files(self, main_repo: Optional[Path] = None) -> List[Path]:
        """
        Get list of files to copy from main repo as templates.

        Args:
            main_repo: Main repository path (default: auto-detect)

        Returns:
            List of file paths relative to repo root
        """
        if main_repo is None:
            main_repo = self.main_repo

        if not main_repo or not main_repo.exists():
            return []

        template_patterns = [
            # Project configuration
            ".dopemux/**/*",
            ".editorconfig",

            # Linting and formatting
            ".prettierrc*",
            ".eslintrc*",
            "eslint.config.*",
            ".pylintrc",
            "pyproject.toml",  # Only if it has linting config
            ".flake8",
            ".black",

            # Type checking
            "tsconfig.json",
            "jsconfig.json",
            "mypy.ini",

            # Example environment
            ".env.example",
            ".env.template",
        ]

        template_files = []

        for pattern in template_patterns:
            if "**" in pattern:
                # Recursive glob
                matched = list(main_repo.glob(pattern))
            else:
                # Direct file match
                file_path = main_repo / pattern
                matched = [file_path] if file_path.exists() else []

            # Convert to relative paths
            for file_path in matched:
                if file_path.is_file():
                    rel_path = file_path.relative_to(main_repo)
                    template_files.append(rel_path)

        return template_files

    def should_copy_file(self, file_path: Path, worktree: Path) -> Tuple[bool, str]:
        """
        Determine if file should be copied to worktree.

        Args:
            file_path: File to check (relative path)
            worktree: Target worktree path

        Returns:
            Tuple of (should_copy, reason)
        """
        target = worktree / file_path

        # Skip if file already exists (preserve user customization)
        if target.exists():
            return False, f"Already exists (preserving customization)"

        # Skip if in .gitignore
        if self._is_gitignored(file_path, worktree):
            return False, "In .gitignore"

        # Skip .env files (personal secrets)
        if file_path.name == ".env":
            return False, "Personal secrets file"

        # Skip .claude.json (managed by auto-configurator)
        if file_path.name == ".claude.json":
            return False, "Managed by auto-configurator"

        return True, "Template file"

    def _is_gitignored(self, file_path: Path, worktree: Path) -> bool:
        """
        Check if file is gitignored.

        Args:
            file_path: File to check (relative path)
            worktree: Worktree path

        Returns:
            True if file is gitignored
        """
        try:
            import subprocess

            result = subprocess.run(
                ["git", "check-ignore", str(file_path)],
                cwd=str(worktree),
                capture_output=True,
                timeout=1
            )

            # Exit code 0 means file is ignored
            return result.returncode == 0

        except Exception:
            return False

    def copy_templates_to_worktree(
        self,
        worktree: Path,
        main_repo: Optional[Path] = None,
        dry_run: bool = False
    ) -> Tuple[int, int, List[str]]:
        """
        Copy template files from main repo to worktree.

        Args:
            worktree: Target worktree path
            main_repo: Main repository path (default: auto-detect)
            dry_run: Preview without copying

        Returns:
            Tuple of (copied_count, skipped_count, messages)
        """
        if main_repo is None:
            main_repo = self.main_repo

        if not main_repo or not main_repo.exists():
            return 0, 0, ["Main repository not found"]

        template_files = self.get_template_files(main_repo)

        copied = 0
        skipped = 0
        messages = []

        for rel_path in template_files:
            source = main_repo / rel_path
            target = worktree / rel_path

            should_copy, reason = self.should_copy_file(rel_path, worktree)

            if should_copy:
                if not dry_run:
                    # Ensure parent directory exists
                    target.parent.mkdir(parents=True, exist_ok=True)

                    # Copy file
                    shutil.copy2(source, target)

                copied += 1
                messages.append(f"✅ Copied: {rel_path}")
            else:
                skipped += 1
                messages.append(f"⏭️  Skipped: {rel_path} ({reason})")

        return copied, skipped, messages

    def get_template_status(self, worktree: Optional[Path] = None) -> Dict:
        """
        Get template application status for a worktree.

        Args:
            worktree: Worktree to check (default: current workspace)

        Returns:
            Dictionary with template status
        """
        if worktree is None:
            worktree = get_workspace_root()

        main_repo = self.main_repo

        if not main_repo:
            return {
                "main_repo_found": False,
                "error": "Not in a git repository"
            }

        template_files = self.get_template_files(main_repo)

        present = []
        missing = []

        for rel_path in template_files:
            target = worktree / rel_path

            if target.exists():
                present.append(str(rel_path))
            else:
                should_copy, _ = self.should_copy_file(rel_path, worktree)
                if should_copy:
                    missing.append(str(rel_path))

        return {
            "main_repo_found": True,
            "main_repo": str(main_repo),
            "worktree": str(worktree),
            "template_files_total": len(template_files),
            "present": present,
            "missing": missing,
            "coverage_percent": (len(present) / len(template_files) * 100) if template_files else 0,
        }
