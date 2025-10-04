"""
ConPort Task Matching for Untracked Work Detection

Matches git work against ConPort tasks to identify orphaned work.

Part of Feature 1: Untracked Work Detection
"""

from pathlib import Path
from typing import List, Dict, Optional, Set
import logging
import re

logger = logging.getLogger(__name__)


class ConPortTaskMatcher:
    """Match git work against ConPort tasks"""

    def __init__(self, workspace_id: str):
        """
        Initialize ConPort matcher

        Args:
            workspace_id: Absolute path to workspace (for ConPort queries)
        """
        self.workspace_id = workspace_id

    async def find_matching_tasks(
        self,
        git_detection: Dict,
        conport_client = None
    ) -> Dict:
        """
        Find ConPort tasks that might match detected git work

        Args:
            git_detection: Output from GitWorkDetector.detect_uncommitted_work()
            conport_client: Optional ConPort MCP client (for querying)

        Returns:
            {
                "has_matching_task": bool,
                "matched_tasks": List[Dict],
                "confidence_scores": Dict[int, float],
                "is_orphaned": bool,
                "orphan_reason": str
            }
        """
        if not git_detection.get("has_uncommitted"):
            return {
                "has_matching_task": False,
                "matched_tasks": [],
                "confidence_scores": {},
                "is_orphaned": False,
                "orphan_reason": "no_uncommitted_work"
            }

        # Get IN_PROGRESS tasks from ConPort
        in_progress_tasks = await self._get_in_progress_tasks(conport_client)

        if not in_progress_tasks:
            # No tasks at all → definitely orphaned
            return {
                "has_matching_task": False,
                "matched_tasks": [],
                "confidence_scores": {},
                "is_orphaned": True,
                "orphan_reason": "no_in_progress_tasks"
            }

        # Match git work against each task
        matches = []
        for task in in_progress_tasks:
            match_score = self._calculate_match_score(git_detection, task)

            if match_score > 0.3:  # Threshold for considering a match
                matches.append({
                    "task": task,
                    "match_score": match_score,
                    "match_reasons": self._get_match_reasons(git_detection, task)
                })

        # Sort by match score (best first)
        matches.sort(key=lambda m: m["match_score"], reverse=True)

        # Determine if orphaned
        is_orphaned = len(matches) == 0 or (matches[0]["match_score"] < 0.6)

        orphan_reason = None
        if is_orphaned:
            if len(matches) == 0:
                orphan_reason = "no_matching_tasks"
            else:
                orphan_reason = f"weak_match (best: {matches[0]['match_score']:.2f})"

        return {
            "has_matching_task": len(matches) > 0 and matches[0]["match_score"] >= 0.6,
            "matched_tasks": [m["task"] for m in matches],
            "confidence_scores": {m["task"]["id"]: m["match_score"] for m in matches},
            "match_details": matches,
            "is_orphaned": is_orphaned,
            "orphan_reason": orphan_reason
        }

    async def _get_in_progress_tasks(self, conport_client) -> List[Dict]:
        """
        Query ConPort for IN_PROGRESS tasks

        Returns:
            List of task dictionaries with id, description, etc.
        """
        if not conport_client:
            # No ConPort client → simulate for now
            logger.warning("No ConPort client provided - cannot query tasks")
            return []

        try:
            # Query ConPort MCP for IN_PROGRESS tasks
            # This would use: mcp__conport__get_progress with status_filter="IN_PROGRESS"

            # TODO: Integrate with actual ConPort MCP client
            # For now, return empty to indicate no tasks found
            return []

        except Exception as e:
            logger.error(f"Failed to query ConPort tasks: {e}")
            return []

    def _calculate_match_score(self, git_detection: Dict, task: Dict) -> float:
        """
        Calculate match score between git work and ConPort task

        Scoring factors:
        - Branch name matches task description (0.4)
        - File paths mentioned in task description (0.3)
        - Common directory matches task context (0.2)
        - Time correlation (0.1)

        Returns:
            0.0-1.0 match confidence score
        """
        score = 0.0
        task_desc = task.get("description", "").lower()

        # Factor 1: Branch name match (weight: 0.4)
        branch = git_detection.get("branch", "")
        if branch and self._matches_text(branch, task_desc):
            score += 0.4
        elif branch and self._fuzzy_matches(branch, task_desc):
            score += 0.2

        # Factor 2: File path mentions (weight: 0.3)
        files = git_detection.get("files", [])
        file_mentions = sum(
            1 for f in files
            if self._file_mentioned_in_task(f, task_desc)
        )
        if file_mentions > 0:
            # Proportional: 1 file = 0.15, 2+ files = 0.3
            score += min(file_mentions / len(files) * 0.3, 0.3) if files else 0

        # Factor 3: Common directory match (weight: 0.2)
        common_dir = git_detection.get("common_directory")
        if common_dir and common_dir != "." and common_dir.lower() in task_desc:
            score += 0.2

        # Factor 4: Partial keyword overlap (weight: 0.1)
        git_keywords = self._extract_keywords(git_detection)
        task_keywords = self._extract_keywords_from_text(task_desc)

        overlap = len(git_keywords & task_keywords)
        if overlap > 0 and task_keywords:
            score += min(overlap / len(task_keywords) * 0.1, 0.1)

        return min(score, 1.0)

    def _matches_text(self, branch: str, text: str) -> bool:
        """Check if branch name appears in text (exact or normalized)"""
        # Normalize: "feature/auth-system" → "auth system"
        normalized = branch.split("/")[-1].replace("-", " ").replace("_", " ").lower()
        return normalized in text or branch.lower() in text

    def _fuzzy_matches(self, branch: str, text: str) -> bool:
        """Fuzzy match: at least 2 words from branch in text"""
        words = branch.split("/")[-1].replace("-", " ").replace("_", " ").lower().split()
        matches = sum(1 for word in words if len(word) > 2 and word in text)
        return matches >= 2

    def _file_mentioned_in_task(self, filepath: str, task_desc: str) -> bool:
        """Check if file path or name is mentioned in task"""
        # Check full path
        if filepath.lower() in task_desc:
            return True

        # Check filename only
        filename = Path(filepath).name.lower()
        if filename in task_desc:
            return True

        # Check stem (without extension)
        stem = Path(filepath).stem.lower()
        if len(stem) > 3 and stem in task_desc:  # Avoid short stems like "a", "b"
            return True

        return False

    def _extract_keywords(self, git_detection: Dict) -> Set[str]:
        """
        Extract meaningful keywords from git detection

        Returns:
            Set of lowercase keywords (min 3 chars)
        """
        keywords = set()

        # From branch name
        branch = git_detection.get("branch", "")
        if branch:
            words = branch.split("/")[-1].replace("-", " ").replace("_", " ").split()
            keywords.update(w.lower() for w in words if len(w) >= 3)

        # From common directory
        common_dir = git_detection.get("common_directory")
        if common_dir and common_dir != ".":
            dir_parts = Path(common_dir).parts
            keywords.update(p.lower() for p in dir_parts if len(p) >= 3)

        # From filenames
        for filepath in git_detection.get("files", [])[:5]:  # Limit to first 5 files
            stem = Path(filepath).stem.lower()
            if len(stem) >= 3:
                # Split camelCase and snake_case
                parts = re.split(r'[_-]|(?<=[a-z])(?=[A-Z])', stem)
                keywords.update(p.lower() for p in parts if len(p) >= 3)

        return keywords

    def _extract_keywords_from_text(self, text: str) -> Set[str]:
        """
        Extract meaningful keywords from task description

        Returns:
            Set of lowercase keywords (min 3 chars, no stop words)
        """
        # Simple stop words
        stop_words = {
            "the", "and", "for", "with", "from", "that", "this", "into",
            "are", "was", "were", "been", "have", "has", "had", "will",
            "would", "could", "should", "may", "might", "must", "can"
        }

        # Split on non-alphanumeric
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())

        return set(w for w in words if w not in stop_words)

    def _get_match_reasons(self, git_detection: Dict, task: Dict) -> List[str]:
        """
        Get human-readable reasons for match

        Returns:
            ["Branch name matches", "2 files mentioned", etc.]
        """
        reasons = []
        task_desc = task.get("description", "").lower()

        # Check branch match
        branch = git_detection.get("branch", "")
        if branch and self._matches_text(branch, task_desc):
            reasons.append(f"Branch '{branch}' matches task")

        # Check file mentions
        files = git_detection.get("files", [])
        mentioned = [f for f in files if self._file_mentioned_in_task(f, task_desc)]
        if mentioned:
            reasons.append(f"{len(mentioned)} file(s) mentioned in task")

        # Check directory match
        common_dir = git_detection.get("common_directory")
        if common_dir and common_dir != "." and common_dir.lower() in task_desc:
            reasons.append(f"Directory '{common_dir}' mentioned")

        # Check keyword overlap
        git_keywords = self._extract_keywords(git_detection)
        task_keywords = self._extract_keywords_from_text(task_desc)
        overlap = git_keywords & task_keywords
        if overlap:
            reasons.append(f"Keywords match: {', '.join(list(overlap)[:3])}")

        return reasons if reasons else ["Weak/no match"]
