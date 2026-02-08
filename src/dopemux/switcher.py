"""
Programmatic profile switch orchestration.

Maintains a reusable switcher API for Epic-3 integration points while reusing
existing profile/session/Claude managers.
"""

from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Dict, Optional

from .claude_manager import ClaudeProfileManager
from .profile_manager import ProfileManager
from .session_manager import ProfileSessionManager


@dataclass
class ProfileSwitchResult:
    profile_name: str
    success: bool
    previous_profile: Optional[str]
    timings: Dict[str, float] = field(default_factory=dict)
    error: Optional[str] = None


class ProfileSwitcher:
    """Switch profiles with optional config/session orchestration."""

    def __init__(
        self,
        workspace: Optional[Path] = None,
        profile_manager: Optional[ProfileManager] = None,
        session_manager: Optional[ProfileSessionManager] = None,
        claude_manager: Optional[ClaudeProfileManager] = None,
    ):
        self.workspace = (workspace or Path.cwd()).resolve()
        self.profile_manager = profile_manager or ProfileManager()
        self.session_manager = session_manager or ProfileSessionManager(self.workspace)
        self.claude_manager = claude_manager or ClaudeProfileManager()

    def switch(
        self,
        profile_name: str,
        apply_config: bool = True,
        save_session: bool = True,
        restore_session: bool = True,
    ) -> ProfileSwitchResult:
        """Switch to target profile and return step timings."""
        timings: Dict[str, float] = {}
        previous = self.profile_manager.get_active_profile(self.workspace)

        profile = self.profile_manager.get_profile(profile_name)
        if profile is None:
            return ProfileSwitchResult(
                profile_name=profile_name,
                success=False,
                previous_profile=previous,
                error=f"profile not found: {profile_name}",
            )

        backup_path = None
        try:
            if save_session:
                started = perf_counter()
                self.session_manager.save_session(f"profile switch: {previous or 'none'} -> {profile_name}")
                timings["save_session"] = perf_counter() - started

            if apply_config:
                started = perf_counter()
                _, backup_path = self.claude_manager.apply_profile(profile)
                timings["apply_config"] = perf_counter() - started

            started = perf_counter()
            self.profile_manager.set_active_profile(self.workspace, profile_name)
            timings["set_active_profile"] = perf_counter() - started

            if restore_session:
                started = perf_counter()
                self.session_manager.restore_session()
                timings["restore_session"] = perf_counter() - started

            return ProfileSwitchResult(
                profile_name=profile_name,
                success=True,
                previous_profile=previous,
                timings=timings,
            )
        except Exception as exc:
            if backup_path:
                self.claude_manager.rollback(backup_path)
            return ProfileSwitchResult(
                profile_name=profile_name,
                success=False,
                previous_profile=previous,
                timings=timings,
                error=str(exc),
            )

