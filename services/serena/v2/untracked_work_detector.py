"""
Untracked Work Detector - Main Feature 1 Logic

Combines git detection + ConPort matching + confidence scoring
to identify orphaned ADHD work and encourage task completion.

Part of Feature 1: Untracked Work Detection
"""

from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import logging
import json

from git_detector import GitWorkDetector
from conport_matcher import ConPortTaskMatcher
from pattern_learner import PatternLearner
from abandonment_tracker import AbandonmentTracker

logger = logging.getLogger(__name__)


class UntrackedWorkDetector:
    """
    Main detector for Feature 1: Untracked Work Detection

    Combines multiple signals to identify ADHD-pattern orphaned work:
    - Git uncommitted files
    - No matching ConPort task
    - Persistence across sessions
    - Time-based grace periods
    """

    def __init__(self, workspace: Path, workspace_id: str):
        """
        Initialize untracked work detector

        Args:
            workspace: Workspace path for git operations
            workspace_id: Workspace ID for ConPort queries
        """
        self.workspace = workspace
        self.workspace_id = workspace_id

        self.git_detector = GitWorkDetector(workspace)
        self.conport_matcher = ConPortTaskMatcher(workspace_id)
        self.pattern_learner = PatternLearner(workspace_id)  # F5: Pattern learning
        self.abandonment_tracker = AbandonmentTracker(workspace_id)  # F6: Abandonment tracking

        # Feature 1 config from spec
        self.grace_period_minutes = 30  # Updated from 15 via consensus
        self.adaptive_thresholds = {
            1: 0.75,  # Session 1: conservative
            2: 0.65,  # Session 2+: increase sensitivity
            3: 0.60   # Session 3+: definitely not temporary
        }

    async def detect(
        self,
        conport_client = None,
        session_number: int = 1
    ) -> Dict:
        """
        Detect untracked work with ADHD-optimized confidence scoring

        Args:
            conport_client: Optional ConPort MCP client for task matching
            session_number: Current session number (1, 2, 3+) for adaptive thresholds

        Returns:
            {
                "has_untracked_work": bool,
                "confidence_score": float,
                "threshold_used": float,
                "passes_threshold": bool,
                "work_name": str,
                "detection_signals": {...},
                "git_detection": {...},
                "conport_matching": {...},
                "should_remind": bool,
                "reminder_reason": str
            }
        """
        # Step 1: Detect git work
        git_detection = await self.git_detector.detect_uncommitted_work()

        if not git_detection.get("has_uncommitted"):
            return {
                "has_untracked_work": False,
                "confidence_score": 0.0,
                "threshold_used": 0.0,
                "passes_threshold": False,
                "work_name": None,
                "detection_signals": {},
                "git_detection": git_detection,
                "conport_matching": None,
                "should_remind": False,
                "reminder_reason": "no_uncommitted_work"
            }

        # Step 2: Match against ConPort tasks
        conport_matching = await self.conport_matcher.find_matching_tasks(
            git_detection, conport_client
        )

        # Step 3: Calculate multi-signal confidence score
        base_confidence = await self._calculate_confidence_score(
            git_detection,
            conport_matching
        )

        # Step 3.5: F5 - Apply pattern-based confidence boost
        pattern_boost_result = await self.pattern_learner.suggest_based_on_patterns(
            git_detection,
            confidence_boost=0.15  # Max boost from planning
        )

        # Combine base confidence with pattern boost
        confidence_score = min(base_confidence + pattern_boost_result["boost_applied"], 1.0)

        # Step 3.75: F6 - Calculate abandonment score
        abandonment_data = self.abandonment_tracker.calculate_abandonment_score(git_detection)

        # Step 4: Apply adaptive threshold
        threshold = self._get_adaptive_threshold(session_number)
        passes_threshold = confidence_score >= threshold

        # Step 5: Generate work name
        work_name = await self.git_detector.generate_work_name(git_detection)

        # Step 6: Determine if should remind
        should_remind, reminder_reason = self._should_remind(
            session_number,
            git_detection,
            conport_matching,
            passes_threshold
        )

        # Step 7: Collect detection signals for transparency
        detection_signals = self._collect_detection_signals(
            git_detection,
            conport_matching,
            confidence_score
        )

        return {
            "has_untracked_work": passes_threshold,
            "confidence_score": confidence_score,
            "base_confidence": base_confidence,  # F5: Base score before boost
            "pattern_boost": pattern_boost_result["boost_applied"],  # F5: Boost amount
            "pattern_boost_details": pattern_boost_result,  # F5: Full pattern analysis
            "abandonment_data": abandonment_data,  # F6: Abandonment tracking
            "threshold_used": threshold,
            "passes_threshold": passes_threshold,
            "work_name": work_name,
            "detection_signals": detection_signals,
            "git_detection": git_detection,
            "conport_matching": conport_matching,
            "should_remind": should_remind,
            "reminder_reason": reminder_reason,
            "session_number": session_number,
            "grace_period_satisfied": self._is_past_grace_period(git_detection)
        }

    async def _calculate_confidence_score(
        self,
        git_detection: Dict,
        conport_matching: Dict
    ) -> float:
        """
        Multi-signal confidence scoring from Feature 1 spec

        Factors:
        - Signal 1: Git activity (weight 0.4)
        - Signal 2: ConPort absence (weight 0.3)
        - Signal 3: Filesystem activity (weight 0.3)
        - Boosters: File count, session duration

        Returns:
            0.0-1.0 confidence score
        """
        score = 0.0

        # Signal 1: Git activity (weight 0.4)
        if git_detection.get("has_uncommitted"):
            score += 0.2  # Base: has uncommitted files

        if git_detection.get("is_feature_branch"):
            score += 0.2  # Feature branch indicates intentional work

        # Signal 2: ConPort absence (weight 0.3)
        if conport_matching.get("is_orphaned"):
            score += 0.15  # No matching ConPort task

        if conport_matching.get("orphan_reason") == "no_in_progress_tasks":
            score += 0.15  # No IN_PROGRESS tasks at all (stronger signal)

        # Signal 3: Filesystem activity (weight 0.3)
        stats = git_detection.get("stats", {})
        if stats.get("new", 0) > 0:
            score += 0.15  # New files created

        if self._is_past_grace_period(git_detection):
            score += 0.15  # Past 30-min grace period

        # Confidence boosters
        file_count = len(git_detection.get("files", []))
        if file_count > 3:
            score += 0.15  # Multiple files = substantial work

        # Time-based booster
        first_change = git_detection.get("first_change_time")
        if first_change:
            duration = datetime.now() - first_change
            if duration > timedelta(minutes=30):
                score += 0.1  # Session duration > 30 min

        return min(score, 1.0)

    def _get_adaptive_threshold(self, session_number: int) -> float:
        """
        Get adaptive threshold based on session persistence

        Session 1: 0.75 (conservative)
        Session 2: 0.65 (increase sensitivity)
        Session 3+: 0.60 (definitely not temporary)
        """
        if session_number <= 1:
            return self.adaptive_thresholds[1]
        elif session_number == 2:
            return self.adaptive_thresholds[2]
        else:
            return self.adaptive_thresholds[3]

    def _is_past_grace_period(self, git_detection: Dict) -> bool:
        """
        Check if work is past 30-minute grace period

        ADHD accommodation: Quick experiments < 30 min ignored
        """
        first_change = git_detection.get("first_change_time")
        if not first_change:
            return False

        duration = datetime.now() - first_change
        return duration > timedelta(minutes=self.grace_period_minutes)

    def _should_remind(
        self,
        session_number: int,
        git_detection: Dict,
        conport_matching: Dict,
        passes_threshold: bool
    ) -> tuple[bool, str]:
        """
        Determine if reminder should be shown

        Rules from Feature 1 spec:
        1. Never remind on first detection (session 1)
        2. Only remind if past grace period
        3. Only remind if passes threshold
        4. Only remind if truly orphaned

        Returns:
            (should_remind: bool, reason: str)
        """
        # Rule 1: Never remind during first detection
        if session_number < 2:
            return (False, "needs_persistence_check (session 1)")

        # Rule 2: Check grace period
        if not self._is_past_grace_period(git_detection):
            return (False, "within_grace_period")

        # Rule 3: Check threshold
        if not passes_threshold:
            return (False, "below_confidence_threshold")

        # Rule 4: Check if truly orphaned
        if not conport_matching.get("is_orphaned"):
            return (False, "has_matching_task")

        # All checks passed - should remind
        return (True, "new_detection (session 2+)")

    def _collect_detection_signals(
        self,
        git_detection: Dict,
        conport_matching: Dict,
        confidence_score: float
    ) -> Dict:
        """
        Collect all detection signals for transparency

        Used in UI to show "Why am I seeing this?" explanation
        """
        signals = {
            "git": {
                "uncommitted_files": len(git_detection.get("files", [])),
                "is_feature_branch": git_detection.get("is_feature_branch"),
                "branch": git_detection.get("branch"),
                "stats": git_detection.get("stats", {}),
                "common_directory": git_detection.get("common_directory")
            },
            "conport": {
                "is_orphaned": conport_matching.get("is_orphaned"),
                "orphan_reason": conport_matching.get("orphan_reason"),
                "matched_tasks": len(conport_matching.get("matched_tasks", []))
            },
            "timing": {
                "first_change_time": git_detection.get("first_change_time").isoformat()
                    if git_detection.get("first_change_time") else None,
                "past_grace_period": self._is_past_grace_period(git_detection)
            },
            "confidence": {
                "score": confidence_score,
                "breakdown": self._explain_confidence_score(git_detection, conport_matching)
            }
        }

        return signals

    def _explain_confidence_score(
        self,
        git_detection: Dict,
        conport_matching: Dict
    ) -> List[str]:
        """
        Generate human-readable confidence score explanation

        Returns:
            ["Has uncommitted files (+0.2)", "Feature branch (+0.2)", ...]
        """
        explanations = []

        # Git activity
        if git_detection.get("has_uncommitted"):
            explanations.append("Has uncommitted files (+0.2)")

        if git_detection.get("is_feature_branch"):
            explanations.append(f"Feature branch '{git_detection.get('branch')}' (+0.2)")

        # ConPort absence
        if conport_matching.get("is_orphaned"):
            reason = conport_matching.get("orphan_reason", "unknown")
            explanations.append(f"No matching ConPort task: {reason} (+0.15-0.3)")

        # Filesystem activity
        stats = git_detection.get("stats", {})
        if stats.get("new", 0) > 0:
            explanations.append(f"{stats.get('new')} new file(s) created (+0.15)")

        if self._is_past_grace_period(git_detection):
            explanations.append("Past 30-min grace period (+0.15)")

        # Boosters
        file_count = len(git_detection.get("files", []))
        if file_count > 3:
            explanations.append(f"{file_count} files changed (+0.15)")

        first_change = git_detection.get("first_change_time")
        if first_change:
            duration = datetime.now() - first_change
            if duration > timedelta(minutes=30):
                mins = int(duration.total_seconds() / 60)
                explanations.append(f"Session duration {mins}min (+0.1)")

        return explanations

    def create_tracking_suggestion(self, detection: Dict) -> Dict:
        """
        Create pre-filled ConPort task suggestion

        Returns dictionary ready for ConPort log_progress
        """
        git_detection = detection["git_detection"]
        files = git_detection.get("files", [])
        stats = git_detection.get("stats", {})

        # Estimate complexity from file count
        file_count = len(files)
        if file_count <= 2:
            complexity = 0.3
        elif file_count <= 5:
            complexity = 0.5
        else:
            complexity = 0.7

        return {
            "status": "IN_PROGRESS",
            "description": detection["work_name"],
            "linked_item_type": "untracked_work_detection",
            "linked_item_id": None,  # Will be filled when saved
            "metadata": {
                "detected_at": datetime.now().isoformat(),
                "git_branch": git_detection.get("branch"),
                "files_changed": file_count,
                "stats": stats,
                "common_directory": git_detection.get("common_directory"),
                "confidence_score": detection["confidence_score"],
                "auto_generated": True
            },
            "suggested_complexity": complexity
        }
