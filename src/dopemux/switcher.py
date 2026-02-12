"""Compatibility profile switch orchestration helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter


@dataclass
class SwitchResult:
    """Result envelope for profile switch attempts."""

    success: bool
    profile_name: str | None = None
    previous_profile: str | None = None
    error: str | None = None
    timings: dict[str, float] = field(default_factory=dict)


class ProfileSwitcher:
    """Coordinate profile switch, session handoff, and rollback."""

    def __init__(self, workspace: Path, profile_manager, session_manager, claude_manager):
        self.workspace = Path(workspace).resolve()
        self.profile_manager = profile_manager
        self.session_manager = session_manager
        self.claude_manager = claude_manager

    def switch(self, profile_name: str) -> SwitchResult:
        previous = self.profile_manager.get_active_profile(self.workspace)
        profile = self.profile_manager.get_profile(profile_name)
        if profile is None:
            return SwitchResult(success=False, previous_profile=previous, error=f"profile not found: {profile_name}")

        self.session_manager.save_session(f"profile switch {previous} -> {profile_name}")

        applied, backup_path = self.claude_manager.apply_profile(profile)
        if not applied:
            return SwitchResult(success=False, profile_name=profile_name, previous_profile=previous, error="apply failed")

        timings: dict[str, float] = {}
        start = perf_counter()
        try:
            self.profile_manager.set_active_profile(self.workspace, profile_name)
            timings["set_active_profile"] = perf_counter() - start
        except Exception as exc:  # pylint: disable=broad-except
            self.claude_manager.rollback(backup_path)
            return SwitchResult(
                success=False,
                profile_name=profile_name,
                previous_profile=previous,
                error=str(exc),
                timings=timings,
            )

        self.session_manager.restore_session()
        return SwitchResult(
            success=True,
            profile_name=profile_name,
            previous_profile=previous,
            timings=timings,
        )

