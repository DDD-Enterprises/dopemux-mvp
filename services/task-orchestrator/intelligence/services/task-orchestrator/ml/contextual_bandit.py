"""
Contextual Bandits - Week 4 (Thompson Sampling + UCB)

Safe exploration-exploitation for task recommendations.
Zen consensus upgrade from GradientBoosting.

Created: 2025-10-20
"""

import logging
from dataclasses import dataclass
from typing import List
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class BanditArm:
    """A single arm (task) in contextual bandit."""
    arm_id: str
    successes: int = 0
    failures: int = 0
    
    @property
    def total_pulls(self) -> int:
        return self.successes + self.failures


class ThompsonSamplingBandit:
    """Thompson Sampling for safe task exploration."""

    def __init__(self):
        self.arms: List[BanditArm] = []
        logger.info("ThompsonSamplingBandit initialized")

    def add_arm(self, arm_id: str):
        """Add a new arm (task)."""
        self.arms.append(BanditArm(arm_id=arm_id))

    def select_arm(self) -> int:
        """Select arm using Thompson Sampling."""
        if not self.arms:
            return 0
        
        # Sample from Beta distribution for each arm
        samples = []
        for arm in self.arms:
            alpha = arm.successes + 1
            beta = arm.failures + 1
            sample = np.random.beta(alpha, beta)
            samples.append(sample)
        
        return int(np.argmax(samples))

    def update(self, arm_idx: int, reward: float):
        """Update arm with reward (1.0 = success, 0.0 = failure)."""
        if reward >= 0.5:
            self.arms[arm_idx].successes += 1
        else:
            self.arms[arm_idx].failures += 1


class UCBBandit:
    """Upper Confidence Bound for task recommendations."""

    def __init__(self, alpha: float = 2.0):
        self.alpha = alpha
        self.arms: List[BanditArm] = []
        self.total_rounds = 0
        logger.info(f"UCBBandit initialized (alpha={alpha})")

    def add_arm(self, arm_id: str):
        """Add a new arm (task)."""
        self.arms.append(BanditArm(arm_id=arm_id))

    def select_arm(self) -> int:
        """Select arm using UCB."""
        if not self.arms:
            return 0
        
        # Explore arms that haven't been pulled yet
        for i, arm in enumerate(self.arms):
            if arm.total_pulls == 0:
                return i
        
        # UCB: mean + exploration bonus
        ucb_values = []
        for arm in self.arms:
            mean = arm.successes / max(arm.total_pulls, 1)
            bonus = self.alpha * np.sqrt(np.log(self.total_rounds + 1) / arm.total_pulls)
            ucb_values.append(mean + bonus)
        
        return int(np.argmax(ucb_values))

    def update(self, arm_idx: int, reward: float):
        """Update arm with reward."""
        if reward >= 0.5:
            self.arms[arm_idx].successes += 1
        else:
            self.arms[arm_idx].failures += 1
        self.total_rounds += 1
