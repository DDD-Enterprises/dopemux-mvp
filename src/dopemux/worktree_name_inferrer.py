"""
Worktree Name Inference for ADHD-Optimized Naming.

Automatically infers good worktree names from context to reduce
decision paralysis and naming cognitive load.

ADHD Optimization: Smart defaults > manual naming decisions.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import subprocess
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class NameSuggestion:
    """
    A suggested worktree name with confidence score.

    ADHD Context: Provides best suggestion first to minimize choices.
    """

    name: str
    source: str  # Where suggestion came from
    confidence: float  # 0.0-1.0, higher is better
    description: str  # Why this name

    def format_for_display(self, index: int) -> str:
        """Format suggestion for ADHD-friendly display."""
        return f"  {index}. {self.name} ({self.source})"


class WorktreeNameInferrer:
    """
    Infers worktree names from git context and file changes.

    ADHD Optimization:
    - Provides 1-3 suggestions (never overwhelming)
    - Best suggestion first (highest confidence)
    - Automatic fallback to timestamp if needed
    """

    def __init__(self, workspace_path: str):
        """
        Initialize name inferrer.

        Args:
            workspace_path: Absolute path to workspace root
        """
        self.workspace_path = Path(workspace_path)

    def _run_git_command(self, args: List[str]) -> Optional[str]:
        """Run git command and return output."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception as e:
            logger.debug(f"Git command failed: {e}")
            return None

    def _sanitize_name(self, name: str) -> str:
        """
        Sanitize name for git worktree compatibility.

        Args:
            name: Raw name suggestion

        Returns:
            Sanitized name safe for git worktree
        """
        # Convert to lowercase
        name = name.lower()

        # Replace spaces and special chars with hyphens
        name = re.sub(r'[^\w\-/]', '-', name)

        # Remove multiple consecutive hyphens
        name = re.sub(r'-+', '-', name)

        # Remove leading/trailing hyphens
        name = name.strip('-')

        # Ensure not empty
        if not name:
            name = "worktree"

        return name

    def _extract_from_branch_name(self) -> Optional[NameSuggestion]:
        """Extract suggestion from current branch name."""
        branch = self._run_git_command(["branch", "--show-current"])
        if not branch or branch in ("main", "master"):
            return None

        # Already on a feature branch - use similar name
        sanitized = self._sanitize_name(branch)

        return NameSuggestion(
            name=sanitized,
            source="current branch",
            confidence=0.8,
            description=f"Based on current branch: {branch}"
        )

    def _extract_from_commit_message(self) -> Optional[NameSuggestion]:
        """Extract suggestion from recent commit messages."""
        log = self._run_git_command(["log", "-1", "--pretty=format:%s"])
        if not log:
            return None

        # Extract first few meaningful words
        words = log.split()[:3]
        if not words:
            return None

        name = "-".join(words)
        sanitized = self._sanitize_name(name)

        return NameSuggestion(
            name=sanitized,
            source="recent commit",
            confidence=0.6,
            description=f"From commit: {log[:40]}..."
        )

    def _extract_from_modified_files(self) -> Optional[NameSuggestion]:
        """Extract suggestion from modified file paths."""
        status = self._run_git_command(["status", "--porcelain"])
        if not status:
            return None

        # Parse modified files
        files = []
        for line in status.splitlines():
            if len(line) > 3:
                # Extract filename (after status codes)
                filename = line[3:].strip()
                files.append(Path(filename))

        if not files:
            return None

        # Find common directory or file pattern
        if len(files) == 1:
            # Single file - use filename
            name = files[0].stem
        else:
            # Multiple files - use common directory
            common_parts = []
            for part in files[0].parts[:-1]:  # Exclude filename
                if all(part in f.parts for f in files):
                    common_parts.append(part)
                else:
                    break

            if common_parts:
                name = "-".join(common_parts)
            else:
                name = "changes"

        sanitized = self._sanitize_name(name)

        return NameSuggestion(
            name=sanitized,
            source="modified files",
            confidence=0.5,
            description=f"Based on {len(files)} modified file(s)"
        )

    def _extract_from_issue_pr_number(self) -> Optional[NameSuggestion]:
        """
        Extract suggestion from issue/PR numbers in branch or commits.

        Looks for patterns like:
        - issue-123
        - pr-456
        - GH-789
        - JIRA-123
        """
        # Check branch name
        branch = self._run_git_command(["branch", "--show-current"])
        if branch:
            # Look for issue/PR patterns
            patterns = [
                r'(issue|pr|gh|jira|fix|feat|bug)[-_]?(\d+)',
                r'([a-z]+-\d+)',  # PROJ-123 style
            ]

            for pattern in patterns:
                match = re.search(pattern, branch, re.IGNORECASE)
                if match:
                    name = match.group(0)
                    sanitized = self._sanitize_name(name)

                    return NameSuggestion(
                        name=sanitized,
                        source="issue/PR",
                        confidence=0.9,
                        description=f"From issue/PR reference in branch"
                    )

        return None

    def _generate_timestamp_fallback(self) -> NameSuggestion:
        """Generate timestamp-based fallback name."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        name = f"work-{timestamp}"

        return NameSuggestion(
            name=name,
            source="timestamp",
            confidence=0.3,
            description="Auto-generated timestamp-based name"
        )

    def suggest_names(self, max_suggestions: int = 3) -> List[NameSuggestion]:
        """
        Suggest worktree names based on context.

        ADHD Optimization: Returns 1-3 suggestions, best first.

        Args:
            max_suggestions: Maximum number of suggestions (default 3 for ADHD)

        Returns:
            List of NameSuggestion objects, sorted by confidence (best first)
        """
        suggestions = []

        # Try different extraction methods
        extractors = [
            self._extract_from_issue_pr_number,
            self._extract_from_branch_name,
            self._extract_from_commit_message,
            self._extract_from_modified_files,
        ]

        for extractor in extractors:
            try:
                suggestion = extractor()
                if suggestion:
                    suggestions.append(suggestion)
            except Exception as e:
                logger.debug(f"Extractor {extractor.__name__} failed: {e}")

        # Always include timestamp fallback
        suggestions.append(self._generate_timestamp_fallback())

        # Sort by confidence (highest first)
        suggestions.sort(key=lambda s: s.confidence, reverse=True)

        # Deduplicate by name
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion.name not in seen:
                seen.add(suggestion.name)
                unique_suggestions.append(suggestion)

        # Limit to max_suggestions
        return unique_suggestions[:max_suggestions]

    def get_best_suggestion(self) -> NameSuggestion:
        """
        Get single best name suggestion.

        ADHD Optimization: One clear choice, no decisions needed.

        Returns:
            Best NameSuggestion (highest confidence)
        """
        suggestions = self.suggest_names(max_suggestions=1)
        return suggestions[0]

    def check_name_available(self, name: str) -> bool:
        """
        Check if worktree name is available (not already in use).

        Checks both:
        - Existing worktree branches
        - All git branches (even those without worktrees)

        Args:
            name: Proposed worktree name

        Returns:
            True if name is available
        """
        existing_names = set()

        # Check existing worktrees
        output = self._run_git_command(["worktree", "list", "--porcelain"])
        if output:
            for line in output.splitlines():
                if line.startswith("branch "):
                    branch_ref = line.split(" ", 1)[1]
                    branch_name = branch_ref.replace("refs/heads/", "")
                    existing_names.add(branch_name)

        # Check all git branches (includes branches without worktrees)
        branches_output = self._run_git_command(["branch", "--list"])
        if branches_output:
            for line in branches_output.splitlines():
                # Remove leading '*' and whitespace
                branch_name = line.strip().lstrip("* ").strip()
                if branch_name:
                    existing_names.add(branch_name)

        # Check if name conflicts
        return name not in existing_names

    def resolve_conflict(self, base_name: str) -> str:
        """
        Resolve naming conflict by adding suffix.

        Args:
            base_name: Original name that conflicts

        Returns:
            Available name with suffix
        """
        counter = 2
        while True:
            candidate = f"{base_name}-{counter}"
            if self.check_name_available(candidate):
                return candidate
            counter += 1
            if counter > 99:  # Safety limit
                # Use timestamp as ultimate fallback
                timestamp = datetime.now().strftime("%H%M%S")
                return f"{base_name}-{timestamp}"

    def get_available_name(self, preferred_name: Optional[str] = None) -> str:
        """
        Get available worktree name, resolving conflicts if needed.

        Args:
            preferred_name: User's preferred name (optional)

        Returns:
            Available worktree name
        """
        if preferred_name:
            sanitized = self._sanitize_name(preferred_name)
            if self.check_name_available(sanitized):
                return sanitized
            else:
                return self.resolve_conflict(sanitized)
        else:
            # Use best suggestion
            suggestion = self.get_best_suggestion()
            if self.check_name_available(suggestion.name):
                return suggestion.name
            else:
                return self.resolve_conflict(suggestion.name)


# Synchronous helper functions

def suggest_worktree_name(workspace_path: str) -> str:
    """
    Get suggested worktree name.

    ADHD Helper: One function call, one good name.

    Args:
        workspace_path: Absolute path to workspace root

    Returns:
        Suggested worktree name (sanitized and available)
    """
    inferrer = WorktreeNameInferrer(workspace_path)
    return inferrer.get_available_name()


def get_name_suggestions(workspace_path: str, max_suggestions: int = 3) -> List[str]:
    """
    Get multiple name suggestions.

    Args:
        workspace_path: Absolute path to workspace root
        max_suggestions: Maximum number of suggestions

    Returns:
        List of suggested names (best first)
    """
    inferrer = WorktreeNameInferrer(workspace_path)
    suggestions = inferrer.suggest_names(max_suggestions)
    return [s.name for s in suggestions]
