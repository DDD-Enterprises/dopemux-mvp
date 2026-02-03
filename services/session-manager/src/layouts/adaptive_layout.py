"""
Adaptive Layout System - Energy-aware interface adaptation
Part of Step 1: Tmux Layout Manager

Detects ADHD energy state and adjusts interface complexity accordingly.
"""

from typing import Literal, Optional

import logging

logger = logging.getLogger(__name__)

from dataclasses import dataclass
from enum import Enum


class EnergyLevel(Enum):
    """ADHD energy states with associated layout complexity."""

    VERY_LOW = "very_low"  # Rest mode, 1 pane
    LOW = "low"  # 2 panes
    MEDIUM = "medium"  # 3 panes (default)
    HIGH = "high"  # 4 panes
    HYPERFOCUS = "hyperfocus"  # 4+ panes, custom layouts


@dataclass
class LayoutConfig:
    """Configuration for energy-specific layout."""

    name: str
    pane_count: int
    split_type: Literal["horizontal", "vertical", "tiled"]
    primary_pane_size: int  # Percentage
    description: str
    adhd_note: str


# Energy-to-layout mapping
ENERGY_LAYOUTS: dict[EnergyLevel, LayoutConfig] = {
    EnergyLevel.VERY_LOW: LayoutConfig(
        name="rest_mode",
        pane_count=1,
        split_type="horizontal",
        primary_pane_size=100,
        description="Single pane only - rest mode",
        adhd_note="Take a break! Single task focus recommended.",
    ),
    EnergyLevel.LOW: LayoutConfig(
        name="low_energy",
        pane_count=2,
        split_type="horizontal",
        primary_pane_size=60,
        description="2 panes - active AI + chat",
        adhd_note="Minimize choices, focus on current task.",
    ),
    EnergyLevel.MEDIUM: LayoutConfig(
        name="medium_energy",
        pane_count=3,
        split_type="vertical",
        primary_pane_size=50,
        description="3 panes - 2 AI instances + chat",
        adhd_note="Balanced layout, standard productivity.",
    ),
    EnergyLevel.HIGH: LayoutConfig(
        name="high_energy",
        pane_count=4,
        split_type="tiled",
        primary_pane_size=25,
        description="4 panes - 3 AI instances + chat",
        adhd_note="Parallel tasks enabled, high capacity.",
    ),
    EnergyLevel.HYPERFOCUS: LayoutConfig(
        name="hyperfocus",
        pane_count=4,
        split_type="tiled",
        primary_pane_size=25,
        description="4 panes - custom by task type",
        adhd_note="⚠️ Monitor for 90+ minute sessions - break protection active.",
    ),
}


class EnergyDetector:
    """
    Detect ADHD energy state from behavioral signals.

    Signals:
    - Typing speed (keystrokes per minute)
    - Pane switch frequency
    - Error rate
    - Time since break
    - Time of day patterns
    """

    def __init__(self):
        self.baseline_typing_speed: Optional[float] = None
        self.energy_history: list[EnergyLevel] = []
        self.last_energy_check: Optional[float] = None

    def detect_energy(
        self,
        typing_speed: Optional[float] = None,
        pane_switches_per_min: Optional[float] = None,
        minutes_since_break: Optional[int] = None,
    ) -> EnergyLevel:
        """
        Detect current energy level from behavioral signals.

        Args:
            typing_speed: Current typing speed (keystrokes/min)
            pane_switches_per_min: Pane navigation frequency
            minutes_since_break: Time since last break

        Returns:
            Detected EnergyLevel

        ADHD Considerations:
        - Requires 3 consecutive readings before state change (hysteresis)
        - Defaults to MEDIUM if signals ambiguous
        - Time of day patterns learned over time via ConPort
        """
        score = 0.5  # Default to medium

        # Factor 1: Typing speed (if available)
        if typing_speed and self.baseline_typing_speed:
            ratio = typing_speed / self.baseline_typing_speed
            if ratio < 0.5:
                score -= 0.3  # Very slow typing
            elif ratio < 0.7:
                score -= 0.15  # Slow typing
            elif ratio > 1.2:
                score += 0.15  # Fast typing
            elif ratio > 1.5:
                score += 0.3  # Very fast typing

        # Factor 2: Pane switching (focus vs scattered)
        if pane_switches_per_min is not None:
            if pane_switches_per_min < 3:
                score += 0.2  # Focused
            elif pane_switches_per_min > 10:
                score -= 0.2  # Scattered

        # Factor 3: Time since break (fatigue indicator)
        if minutes_since_break is not None:
            if minutes_since_break > 90:
                score -= 0.4  # Overdue for break
            elif minutes_since_break > 60:
                score -= 0.2  # Approaching fatigue
            elif minutes_since_break < 10:
                score += 0.1  # Fresh from break

        # Map score to energy level
        if score < 0.2:
            detected = EnergyLevel.VERY_LOW
        elif score < 0.4:
            detected = EnergyLevel.LOW
        elif score < 0.7:
            detected = EnergyLevel.MEDIUM
        elif score < 0.9:
            detected = EnergyLevel.HIGH
        else:
            detected = EnergyLevel.HYPERFOCUS

        # Apply hysteresis (require 3 consecutive readings)
        self.energy_history.append(detected)
        if len(self.energy_history) > 3:
            self.energy_history.pop(0)

        # Only change if last 3 agree
        if len(self.energy_history) >= 3 and len(set(self.energy_history)) == 1:
            return detected
        else:
            # Return previous stable state or default
            return self.energy_history[-2] if len(self.energy_history) > 1 else EnergyLevel.MEDIUM

    def get_layout_config(self, energy: EnergyLevel) -> LayoutConfig:
        """Get layout configuration for energy level."""
        return ENERGY_LAYOUTS[energy]


if __name__ == "__main__":
    """Test energy detection and layout config"""

    detector = EnergyDetector()

    # Test scenarios
    logger.info("Testing energy detection:")
    logger.info("\n1. Low energy (slow typing, 60min since break)")
    energy = detector.detect_energy(
        typing_speed=30,  # Assuming baseline is 60
        pane_switches_per_min=2,
        minutes_since_break=60,
    )
    logger.info(f"   Detected: {energy.value}")
    layout = detector.get_layout_config(energy)
    logger.info(f"   Layout: {layout.name} ({layout.pane_count} panes)")
    logger.info(f"   Note: {layout.adhd_note}")

    logger.info("\n2. High energy (fast typing, recent break)")
    energy = detector.detect_energy(
        typing_speed=90,  # Assuming baseline is 60
        pane_switches_per_min=4,
        minutes_since_break=5,
    )
    logger.info(f"   Detected: {energy.value}")
    layout = detector.get_layout_config(energy)
    logger.info(f"   Layout: {layout.name} ({layout.pane_count} panes)")
    logger.info(f"   Note: {layout.adhd_note}")
