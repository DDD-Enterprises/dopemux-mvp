"""
UrgencyScorer - On-device urgency detection using privacy-first approach.

Phase 1: Rule-based scoring with keyword matching and heuristics
Phase 2: Fine-tuned local ML model with user feedback learning
"""

import logging
import re
from typing import List

from .models import SlackMessage, UrgencyLevel

logger = logging.getLogger(__name__)


class UrgencyScorerConfig:
    """Configuration for urgency scoring."""

    def __init__(
        self,
        user_id: str,
        critical_keywords: List[str] = None,
        high_keywords: List[str] = None,
        vip_users: List[str] = None,
    ):
        self.user_id = user_id

        # User-configurable keywords
        self.critical_keywords = critical_keywords or [
            "urgent",
            "asap",
            "emergency",
            "critical",
            "p0",
            "sev0",
            "production down",
            "outage",
            "incident",
            "all hands",
            "security breach",
            "data loss",
        ]

        self.high_keywords = high_keywords or [
            "important",
            "p1",
            "sev1",
            "blocker",
            "high priority",
            "deadline",
            "today",
            "this morning",
            "right now",
        ]

        # User-configurable VIP senders (CEO, manager, oncall)
        self.vip_users = vip_users or []


class UrgencyScorer:
    """
    On-device urgency scoring using keyword matching and heuristics.

    Privacy-first: No cloud message analysis, all processing local.

    Scoring Signals:
    1. Keyword matching (configurable)
    2. Sender importance (VIP list)
    3. Time sensitivity (mentions "today", "now")
    4. Channel type (DMs higher urgency than channels)
    5. @mentions (direct mention = higher urgency)
    """

    def __init__(self, config: UrgencyScorerConfig):
        self.config = config
        logger.info(
            f"UrgencyScorer initialized with {len(config.critical_keywords)} "
            f"critical keywords, {len(config.vip_users)} VIP users"
        )

    async def score(self, message: SlackMessage) -> UrgencyLevel:
        """
        Score message urgency using multiple signals.

        Returns:
            CRITICAL: Immediate interrupt allowed
            HIGH: Notify at next break
            MEDIUM: Batch for break delivery
            LOW: End-of-day summary
        """
        score = 0
        text_lower = message.text.lower()

        # Signal 1: Critical keyword matching (immediate return)
        if any(kw in text_lower for kw in self.config.critical_keywords):
            logger.warning(
                f"CRITICAL urgency detected: '{message.text[:50]}' "
                f"from {message.user} (keyword match)"
            )
            return UrgencyLevel.CRITICAL

        # Signal 2: High keyword matching (+2 points)
        if any(kw in text_lower for kw in self.config.high_keywords):
            score += 2
            logger.debug(f"High keyword match in message from {message.user}")

        # Signal 3: Sender importance (+2 points)
        if message.user in self.config.vip_users:
            score += 2
            logger.debug(f"VIP sender: {message.user}")

        # Signal 4: Time sensitivity (+1 point)
        time_patterns = [
            r"\btoday\b",
            r"\bnow\b",
            r"\basap\b",
            r"\bthis (morning|afternoon)\b",
            r"\bimmediately\b",
            r"\bright now\b",
        ]
        if any(re.search(pattern, text_lower) for pattern in time_patterns):
            score += 1
            logger.debug(f"Time-sensitive language detected")

        # Signal 5: Channel type (+1 point for DMs)
        if message.channel_type == "im":  # Direct message
            score += 1
            logger.debug(f"Direct message urgency boost")

        # Signal 6: @mentions (+1 point)
        if f"<@{self.config.user_id}>" in message.text:
            score += 1
            logger.debug(f"Direct @mention detected")

        # Convert score to urgency level
        urgency = self._score_to_level(score)

        logger.info(
            f"Message from {message.user}: score={score}, urgency={urgency.name}, "
            f"preview='{message.text[:30]}...'"
        )

        return urgency

    def _score_to_level(self, score: int) -> UrgencyLevel:
        """Convert numeric score to urgency level."""
        if score >= 4:
            return UrgencyLevel.HIGH
        elif score >= 2:
            return UrgencyLevel.MEDIUM
        else:
            return UrgencyLevel.LOW

    async def learn_from_feedback(
        self, message: SlackMessage, actual_urgency: UrgencyLevel, user_corrected: bool
    ):
        """
        Learn from user corrections to improve scoring.

        Phase 2: Use this data to fine-tune ML model.
        For now, just log for analysis.
        """
        if user_corrected:
            logger.info(
                f"📊 User correction: '{message.text[:50]}' "
                f"-> {actual_urgency.name} (was auto-scored differently)"
            )

            # TODO: Store in ConPort for future ML training
            # await self._log_correction_to_conport(message, actual_urgency)

    def add_critical_keyword(self, keyword: str):
        """Dynamically add a critical keyword (user customization)."""
        if keyword not in self.config.critical_keywords:
            self.config.critical_keywords.append(keyword)
            logger.info(f"Added critical keyword: '{keyword}'")

    def add_vip_user(self, user_id: str):
        """Dynamically add a VIP user (user customization)."""
        if user_id not in self.config.vip_users:
            self.config.vip_users.append(user_id)
            logger.info(f"Added VIP user: {user_id}")

    def remove_vip_user(self, user_id: str):
        """Remove a VIP user."""
        if user_id in self.config.vip_users:
            self.config.vip_users.remove(user_id)
            logger.info(f"Removed VIP user: {user_id}")
