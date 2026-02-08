"""
Background Auto-Detection Service for Profile Suggestions.

ADHD-optimized with gentle prompts, debouncing, and quiet hours.
Runs detection every 5 minutes and suggests profile switches when confidence >0.85.
"""

import time

import logging

logger = logging.getLogger(__name__)

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Set
import json

from rich.console import Console
from rich.prompt import Confirm

from .profile_detector import ProfileDetector, DetectionContext, format_match_summary
from .config.manager import ConfigManager

console = Console()


class AutoDetectionConfig:
    """Configuration for auto-detection service."""

    def __init__(self, config_file: Optional[Path] = None):
        """
        Load auto-detection configuration.

        Args:
            config_file: Path to profile-settings.yaml (optional)
        """
        self.enabled = True
        self.check_interval_seconds = 300  # 5 minutes
        self.confidence_threshold = 0.85  # High confidence only
        self.debounce_minutes = 30  # Don't suggest same profile within 30 min
        self.quiet_hours_start = "22:00"  # No suggestions 10pm-8am
        self.quiet_hours_end = "08:00"
        self.never_suggest = set()  # Profiles user said "never" to

        if config_file and config_file.exists():
            self._load_from_file(config_file)

    def _load_from_file(self, config_file: Path) -> None:
        """Load config from YAML file."""
        import yaml

        try:
            with open(config_file, 'r') as f:
                data = yaml.safe_load(f)

            if data:
                self.enabled = data.get('enabled', self.enabled)
                self.check_interval_seconds = data.get('check_interval_seconds', self.check_interval_seconds)
                self.confidence_threshold = data.get('confidence_threshold', self.confidence_threshold)
                self.debounce_minutes = data.get('debounce_minutes', self.debounce_minutes)
                self.quiet_hours_start = data.get('quiet_hours_start', self.quiet_hours_start)
                self.quiet_hours_end = data.get('quiet_hours_end', self.quiet_hours_end)
                self.never_suggest = set(data.get('never_suggest', []))

        except Exception as e:
            console.print(f"[yellow]⚠️  Could not load config from {config_file}: {e}[/yellow]")

    def save(self, config_file: Path) -> None:
        """Save configuration to file."""
        import yaml

        data = {
            'enabled': self.enabled,
            'check_interval_seconds': self.check_interval_seconds,
            'confidence_threshold': self.confidence_threshold,
            'debounce_minutes': self.debounce_minutes,
            'quiet_hours_start': self.quiet_hours_start,
            'quiet_hours_end': self.quiet_hours_end,
            'never_suggest': sorted(list(self.never_suggest))
        }

        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'w') as f:
            f.write("# Dopemux Auto-Detection Settings\n")
            f.write("# ADHD-friendly profile switching with gentle suggestions\n\n")
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def is_quiet_hours(self) -> bool:
        """Check if current time is in quiet hours."""
        now = datetime.now()
        current_time = now.strftime("%H:%M")

        # Handle overnight quiet hours (e.g., 22:00-08:00)
        if self.quiet_hours_start > self.quiet_hours_end:
            return current_time >= self.quiet_hours_start or current_time <= self.quiet_hours_end
        else:
            return self.quiet_hours_start <= current_time <= self.quiet_hours_end


class AutoDetectionService:
    """Background service for profile auto-detection."""

    def __init__(self, workspace_root: Optional[Path] = None, config_file: Optional[Path] = None):
        """
        Initialize auto-detection service.

        Args:
            workspace_root: Project root path
            config_file: Path to profile-settings.yaml
        """
        self.workspace_root = workspace_root or Path.cwd()
        self.detector = ProfileDetector()
        self.config = AutoDetectionConfig(config_file)

        # Debouncing state
        self.last_suggestion: Dict[str, datetime] = {}  # profile_name -> timestamp
        self.current_profile: Optional[str] = None

    def should_suggest(self, profile_name: str, confidence: float) -> bool:
        """
        Check if we should suggest this profile.

        Args:
            profile_name: Profile to potentially suggest
            confidence: Detection confidence (0.0-1.0)

        Returns:
            True if should suggest, False otherwise

        Checks:
        - Service enabled
        - Confidence above threshold
        - Not in quiet hours
        - Not debounced (30 min since last suggestion)
        - Not in "never" list
        - Not already active
        """
        # Check enabled
        if not self.config.enabled:
            return False

        # Check confidence
        if confidence < self.config.confidence_threshold:
            return False

        # Check quiet hours
        if self.config.is_quiet_hours():
            return False

        # Check never list
        if profile_name in self.config.never_suggest:
            return False

        # Check if already active
        if profile_name == self.current_profile:
            return False

        # Check debouncing
        if profile_name in self.last_suggestion:
            last_time = self.last_suggestion[profile_name]
            elapsed = datetime.now() - last_time
            if elapsed < timedelta(minutes=self.config.debounce_minutes):
                return False  # Too soon

        return True

    def suggest_profile_switch(self, profile_name: str, match) -> bool:
        """
        Show gentle suggestion prompt to user.

        Args:
            profile_name: Profile to suggest
            match: ProfileMatch with confidence and scores

        Returns:
            True if user accepted, False if declined

        ADHD-Friendly:
        - Non-intrusive prompt (default: No)
        - Clear confidence display
        - Option to never ask again
        """
        console.print(f"\n[cyan]💡 Profile Suggestion[/cyan]")
        console.print(format_match_summary(match))

        # Ask with [y/N/never] options
        console.print(f"\n[bold]Switch to '{profile_name}' profile?[/bold]")
        console.print("[dim]  y = Yes, switch now[/dim]")
        console.print("[dim]  N = No, not now (default)[/dim]")
        console.print("[dim]  never = Never suggest this profile again[/dim]")

        choice = input("\nChoice [y/N/never]: ").strip().lower()

        # Handle "never"
        if choice == "never":
            self.config.never_suggest.add(profile_name)
            console.print(f"[yellow]✓ Will not suggest '{profile_name}' again[/yellow]")
            # Save updated config
            config_file = self.workspace_root / ".dopemux" / "profile-settings.yaml"
            self.config.save(config_file)
            return False

        # Handle yes/no
        accepted = choice in ['y', 'yes']

        # Record suggestion
        self.last_suggestion[profile_name] = datetime.now()

        return accepted

    def run_detection_cycle(self) -> Optional[str]:
        """
        Run one detection cycle.

        Returns:
            Suggested profile name if suggestion made and accepted, None otherwise

        ADHD: Returns immediately if no suggestion needed (non-blocking)
        """
        # Detect best profile for current context
        match = self.detector.detect()

        # Check if we should suggest
        if not self.should_suggest(match.profile_name, match.confidence):
            return None

        # Show suggestion prompt
        if self.suggest_profile_switch(match.profile_name, match):
            # User accepted
            self.current_profile = match.profile_name
            return match.profile_name
        else:
            # User declined
            return None

    def run_loop(self, max_iterations: Optional[int] = None) -> None:
        """
        Run detection service in loop.

        Args:
            max_iterations: Maximum iterations (None = infinite)

        ADHD Warning: This runs indefinitely. Use with dopemux daemon mode.
        """
        iteration = 0

        console.print("[cyan]🔍 Auto-detection service started[/cyan]")
        console.print(f"   Check interval: {self.config.check_interval_seconds}s")
        console.print(f"   Confidence threshold: {self.config.confidence_threshold:.0%}")
        console.print(f"   Quiet hours: {self.config.quiet_hours_start}-{self.config.quiet_hours_end}")

        try:
            while max_iterations is None or iteration < max_iterations:
                # Run detection
                suggested = self.run_detection_cycle()

                if suggested:
                    console.print(f"[green]✓ Switched to '{suggested}' profile[/green]")

                # Wait for next check
                time.sleep(self.config.check_interval_seconds)
                iteration += 1

        except KeyboardInterrupt:
            console.print("\n[yellow]Auto-detection service stopped[/yellow]")


def create_default_settings(output_file: Path) -> None:
    """
    Create default profile-settings.yaml.

    Args:
        output_file: Where to save the settings file
    """
    config = AutoDetectionConfig()
    config.save(output_file)
    console.print(f"[green]✅ Created default settings at {output_file}[/green]")


if __name__ == "__main__":
    # Test the service
    logger.info("Testing auto-detection service...")

    service = AutoDetectionService()

    logger.info("\nRunning 3 detection cycles (Ctrl+C to stop)...")
    service.run_loop(max_iterations=3)
