"""Productivity monitor used by interruption shield coordinator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List
from datetime import datetime


@dataclass
class ProductivityMonitor:
    """
    Lightweight productivity monitor.

    Returns normalized productivity scores between 0.0 and 1.0.
    """

    window_minutes: int = 15
    threshold: float = 0.7
    _samples: List[float] = field(default_factory=list)
    _last_sample_at: str = ""

    async def get_current_productivity(self) -> float:
        """
        Get current productivity score.

        Uses recent sample average when available, otherwise returns a neutral baseline.
        """
        if not self._samples:
            score = 0.75
        else:
            score = sum(self._samples) / len(self._samples)
        score = max(0.0, min(1.0, score))
        self._last_sample_at = datetime.now().isoformat()
        return score

    async def add_sample(self, score: float) -> None:
        """Add productivity sample for rolling average calculations."""
        normalized = max(0.0, min(1.0, float(score)))
        self._samples.append(normalized)
        max_samples = max(1, self.window_minutes)
        if len(self._samples) > max_samples:
            self._samples = self._samples[-max_samples:]
        self._last_sample_at = datetime.now().isoformat()

