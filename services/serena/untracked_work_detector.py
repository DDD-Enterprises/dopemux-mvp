"""
Untracked Work Detector

Compatibility implementation for Serena Feature 1 and E1-E4 enhancements.
This detector intentionally provides the data contract expected by
`mcp_server.py` and `http_server.py` while delegating core logic to
existing modules (git detector, ConPort matcher, pattern learner, etc).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import logging

try:
    from .abandonment_tracker import AbandonmentTracker
    from .conport_matcher import ConPortTaskMatcher
    from .design_first_detector import DesignFirstDetector
    from .false_starts_aggregator import FalseStartsAggregator
    from .git_detector import GitWorkDetector
    from .pattern_learner import PatternLearner
    from .priority_context_builder import PriorityContextBuilder
    from .revival_suggester import RevivalSuggester
    from .untracked_work_storage import UntrackedWorkStorage
except ImportError:
    # Script-mode fallback.
    from abandonment_tracker import AbandonmentTracker
    from conport_matcher import ConPortTaskMatcher
    from design_first_detector import DesignFirstDetector
    from false_starts_aggregator import FalseStartsAggregator
    from git_detector import GitWorkDetector
    from pattern_learner import PatternLearner
    from priority_context_builder import PriorityContextBuilder
    from revival_suggester import RevivalSuggester
    from untracked_work_storage import UntrackedWorkStorage

logger = logging.getLogger(__name__)


class UntrackedWorkDetector:
    """Detect untracked work and provide ADHD-friendly recommendation signals."""

    def __init__(self, workspace: Optional[Path | str] = None, workspace_id: Optional[str] = None):
        # Backward compatibility: if only one argument is supplied, treat it as workspace.
        if workspace is None and workspace_id:
            workspace = workspace_id

        if workspace is None:
            workspace_path = Path.cwd()
        else:
            workspace_path = Path(workspace).expanduser().resolve()

        self.workspace = workspace_path
        self.workspace_id = workspace_id or str(workspace_path)

        # Core dependencies used by MCP tools.
        self.git_detector = GitWorkDetector(self.workspace)
        self.conport_matcher = ConPortTaskMatcher(self.workspace_id)
        self.pattern_learner = PatternLearner(self.workspace_id)
        self.abandonment_tracker = AbandonmentTracker(self.workspace_id)
        self.storage = UntrackedWorkStorage(self.workspace_id)

        # Enhancement dependencies (E1-E4).
        self.false_starts_aggregator = FalseStartsAggregator(self.workspace_id)
        self.design_first_detector = DesignFirstDetector(self.workspace)
        self.revival_suggester = RevivalSuggester(self.workspace_id)
        self.priority_context_builder = PriorityContextBuilder(self.workspace_id)

        self.grace_period_minutes = 30

    async def detect(self, conport_client=None, session_number: int = 1, **_: Any) -> Dict[str, Any]:
        """
        Run untracked work detection.

        Returns a stable shape consumed by MCP/HTTP integration code.
        """
        threshold = self._threshold_for_session(session_number)

        git_detection_raw = await self.git_detector.detect_uncommitted_work()
        git_detection = self._serialize_git_detection(git_detection_raw)

        conport_matching = await self.conport_matcher.find_matching_tasks(
            git_detection_raw,
            conport_client=conport_client,
        )

        timing_signals = self._build_timing_signals(git_detection_raw)
        grace_period_satisfied = bool(timing_signals["past_grace_period"])

        base_confidence, confidence_breakdown = self._score_confidence(
            git_detection_raw,
            conport_matching,
        )

        # Keep pattern learner wired to the latest client reference.
        self.pattern_learner.conport_client = conport_client
        pattern_boost_raw = await self.pattern_learner.suggest_based_on_patterns(
            git_detection_raw,
            confidence_boost=0.15,
        )
        pattern_boost = float(pattern_boost_raw.get("boost_applied", 0.0) or 0.0)

        confidence_score = min(1.0, base_confidence + pattern_boost)
        passes_threshold = confidence_score >= threshold

        has_uncommitted = bool(git_detection_raw.get("has_uncommitted"))
        is_orphaned = bool(conport_matching.get("is_orphaned"))
        has_untracked_work = (
            has_uncommitted
            and is_orphaned
            and passes_threshold
            and grace_period_satisfied
        )

        if has_uncommitted:
            work_name = await self.git_detector.generate_work_name(git_detection_raw)
        else:
            work_name = "No uncommitted work"

        should_remind, reminder_reason = await self._compute_reminder_state(
            has_untracked_work=has_untracked_work,
            conport_client=conport_client,
            git_detection=git_detection_raw,
            is_orphaned=is_orphaned,
            passes_threshold=passes_threshold,
            grace_period_satisfied=grace_period_satisfied,
        )

        abandonment_data = self.abandonment_tracker.calculate_abandonment_score(git_detection_raw)
        pattern_boost_details = self._normalize_pattern_boost(pattern_boost_raw)

        return {
            "has_untracked_work": has_untracked_work,
            "work_name": work_name,
            "session_number": int(session_number),
            "confidence_score": round(confidence_score, 3),
            "threshold_used": round(threshold, 3),
            "passes_threshold": passes_threshold,
            "grace_period_satisfied": grace_period_satisfied,
            "should_remind": should_remind,
            "reminder_reason": reminder_reason,
            "git_detection": git_detection,
            "conport_matching": conport_matching,
            "detection_signals": {
                "timing": timing_signals,
                "confidence": {
                    "base_score": round(base_confidence, 3),
                    "pattern_boost": round(pattern_boost, 3),
                    "final_score": round(confidence_score, 3),
                    "breakdown": confidence_breakdown,
                },
                "conport": {
                    "is_orphaned": is_orphaned,
                    "orphan_reason": conport_matching.get("orphan_reason"),
                    "matched_tasks": len(conport_matching.get("matched_tasks", [])),
                },
            },
            "pattern_boost": round(pattern_boost, 3),
            "pattern_boost_details": pattern_boost_details,
            "abandonment_data": abandonment_data,
            "detected_at": datetime.now().isoformat(),
        }

    async def detect_with_enhancements(self, conport_client=None, session_number: int = 1) -> Dict[str, Any]:
        """
        Run base detection plus E1-E4 enhancement analysis.
        """
        detection = await self.detect(
            conport_client=conport_client,
            session_number=session_number,
        )

        enhancements: Dict[str, Any] = {}

        # E1: False-starts dashboard
        false_starts_summary = await self.false_starts_aggregator.get_false_starts_summary(
            conport_client=conport_client
        )
        enhancements["false_starts"] = {
            "summary": false_starts_summary,
            "dashboard_message": self.false_starts_aggregator.format_dashboard_message(
                false_starts_summary,
                detection.get("work_name", "Current work"),
            ),
        }

        # E2: Design-first prompting
        design_detection = self.design_first_detector.should_prompt_for_design(
            detection.get("git_detection", {})
        )
        if design_detection.get("should_prompt"):
            enhancements["design_first"] = {
                "detection": design_detection,
                "prompt_message": self.design_first_detector.format_design_prompt_message(
                    design_detection,
                    detection.get("work_name", "Current work"),
                ),
            }

        # E3: Abandoned work revival
        top_abandoned = await self.false_starts_aggregator.get_top_abandoned(
            conport_client=conport_client,
            limit=5,
        )
        revival_suggestions = self.revival_suggester.suggest_revivals(
            top_abandoned=top_abandoned,
            current_work=detection.get("git_detection", {}),
            max_suggestions=3,
        )
        if revival_suggestions.get("has_suggestions"):
            enhancements["revival"] = {
                "suggestions": revival_suggestions,
                "revival_message": self.revival_suggester.format_revival_message(
                    revival_suggestions.get("suggestions", [])
                ),
            }

        # E4: Prioritization context
        priority_context = await self.priority_context_builder.get_priority_context(
            conport_client=conport_client
        )
        enhancements["priority"] = {
            "context": priority_context,
            "priority_message": self.priority_context_builder.format_priority_message(
                priority_context
            ),
        }

        detection["enhancements"] = enhancements
        return detection

    def suggest_action(self, abandonment_data: Dict[str, Any]) -> str:
        """
        Backward-compatible helper retained from previous stub.
        """
        if abandonment_data.get("is_abandoned"):
            return "review"
        return "monitor"

    def _threshold_for_session(self, session_number: int) -> float:
        if session_number <= 1:
            return 0.75
        if session_number == 2:
            return 0.65
        return 0.60

    def _build_timing_signals(self, git_detection: Dict[str, Any]) -> Dict[str, Any]:
        first_change_raw = git_detection.get("first_change_time")
        first_change = self._coerce_datetime(first_change_raw)
        minutes_since_first_change: Optional[int] = None
        if first_change is not None:
            now = (
                datetime.now(first_change.tzinfo)
                if first_change.tzinfo is not None
                else datetime.now()
            )
            elapsed = now - first_change
            minutes_since_first_change = max(0, int(elapsed.total_seconds() // 60))

        past_grace_period = (
            minutes_since_first_change is None
            or minutes_since_first_change >= self.grace_period_minutes
        )

        return {
            "first_change_time": (
                first_change.isoformat() if first_change is not None else None
            ),
            "minutes_since_first_change": minutes_since_first_change,
            "grace_period_minutes": self.grace_period_minutes,
            "past_grace_period": past_grace_period,
        }

    async def _compute_reminder_state(
        self,
        has_untracked_work: bool,
        conport_client,
        git_detection: Dict[str, Any],
        is_orphaned: bool,
        passes_threshold: bool,
        grace_period_satisfied: bool,
    ) -> Tuple[bool, str]:
        if not has_untracked_work:
            if not is_orphaned:
                return False, "tracked_in_conport"
            if not grace_period_satisfied:
                return False, "within_grace_period"
            if not passes_threshold:
                return False, "below_confidence_threshold"
            return False, "no_uncommitted_work"

        if not conport_client:
            return True, "orphaned_work_detected"

        try:
            existing = await self.storage.find_matching_work(
                git_detection=git_detection,
                conport_client=conport_client,
            )
            if not existing:
                return True, "new_orphaned_work"
            should_remind, reason = await self.storage.should_remind_now(existing)
            return bool(should_remind), reason
        except Exception as exc:
            logger.warning("Reminder state fallback due to storage error: %s", exc)
            return True, "orphaned_work_detected"

    def _score_confidence(
        self,
        git_detection: Dict[str, Any],
        conport_matching: Dict[str, Any],
    ) -> Tuple[float, Dict[str, float]]:
        has_uncommitted = bool(git_detection.get("has_uncommitted"))
        file_count = len(git_detection.get("files", []))
        is_feature_branch = bool(git_detection.get("is_feature_branch"))
        is_orphaned = bool(conport_matching.get("is_orphaned"))

        git_signal = 0.45 if has_uncommitted else 0.0
        orphan_signal = 0.35 if is_orphaned else 0.0
        volume_signal = min((file_count / 10.0) * 0.2, 0.2)
        feature_branch_bonus = 0.05 if is_feature_branch else 0.0

        base_score = min(
            1.0,
            git_signal + orphan_signal + volume_signal + feature_branch_bonus,
        )
        breakdown = {
            "git_signal": round(git_signal, 3),
            "orphan_signal": round(orphan_signal, 3),
            "volume_signal": round(volume_signal, 3),
            "feature_branch_bonus": round(feature_branch_bonus, 3),
        }
        return base_score, breakdown

    def _normalize_pattern_boost(self, pattern_boost_raw: Dict[str, Any]) -> Dict[str, Any]:
        raw_matches = pattern_boost_raw.get("matching_patterns", [])
        normalized_matches: List[Dict[str, Any]] = []

        for item in raw_matches:
            pattern = item.get("pattern", {}) if isinstance(item, dict) else {}
            normalized_matches.append(
                {
                    "type": pattern.get("type", "unknown"),
                    "pattern": pattern.get("value", "unknown"),
                    "probability": round(float(item.get("probability", 0.0) or 0.0), 3),
                }
            )

        return {
            "boost_applied": round(
                float(pattern_boost_raw.get("boost_applied", 0.0) or 0.0), 3
            ),
            "boosted_confidence": round(
                float(pattern_boost_raw.get("boosted_confidence", 0.0) or 0.0), 3
            ),
            "explanation": pattern_boost_raw.get("explanation", ""),
            "matching_patterns": normalized_matches,
        }

    def _serialize_git_detection(self, git_detection: Dict[str, Any]) -> Dict[str, Any]:
        serialized = dict(git_detection)
        first_change = serialized.get("first_change_time")
        if isinstance(first_change, datetime):
            serialized["first_change_time"] = first_change.isoformat()
        return serialized

    def _coerce_datetime(self, value: Any) -> Optional[datetime]:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str) and value:
            normalized = value.replace("Z", "+00:00")
            try:
                return datetime.fromisoformat(normalized)
            except ValueError:
                return None
        return None
