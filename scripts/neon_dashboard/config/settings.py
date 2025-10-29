"""
Runtime settings objects for the Dope layout dashboard.

These lightweight dataclasses wrap configuration that ultimately comes
from ``dopemux.toml`` (via :class:`~dopemux.config.manager.ConfigManager`)
and provide convenient defaults for the Textual dashboard runtime.  The
goal is to keep the UI layer decoupled from the Pydantic models that
validate user configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Literal, Optional


ModeLiteral = Literal["implementation", "pm"]


@dataclass(slots=True)
class TransientThresholds:
    """Threshold controls for transient message priority."""

    untracked_warning_days: int = 1
    untracked_critical_days: int = 7
    break_reminder_minutes: tuple[int, int, int] = (25, 45, 90)

    @classmethod
    def from_dict(cls, raw: Optional[Dict[str, object]]) -> "TransientThresholds":
        if not raw:
            return cls()
        warning = int(raw.get("untracked_warning_days", 1) or 1)
        critical = int(raw.get("untracked_critical_days", 7) or 7)
        breaks = raw.get("break_reminder_minutes")
        if isinstance(breaks, Iterable) and not isinstance(breaks, str):
            minutes = tuple(int(x) for x in breaks)
        else:
            minutes = (25, 45, 90)
        return cls(
            untracked_warning_days=warning,
            untracked_critical_days=critical,
            break_reminder_minutes=minutes[:3],
        )


@dataclass(slots=True)
class TransientPreferences:
    """User toggles for transient message categories."""

    enabled: bool = True
    untracked_work: bool = True
    context_switches: bool = True
    task_drift: bool = True
    break_reminders: bool = False
    thresholds: TransientThresholds = field(default_factory=TransientThresholds)

    @classmethod
    def from_dict(cls, raw: Optional[Dict[str, object]]) -> "TransientPreferences":
        if not raw:
            return cls()
        thresholds = TransientThresholds.from_dict(raw.get("thresholds"))
        return cls(
            enabled=bool(raw.get("enabled", True)),
            untracked_work=bool(raw.get("untracked_work", True)),
            context_switches=bool(raw.get("context_switches", True)),
            task_drift=bool(raw.get("task_drift", True)),
            break_reminders=bool(raw.get("break_reminders", False)),
            thresholds=thresholds,
        )


@dataclass(slots=True)
class PMModeSettings:
    """Planning-mode specific configuration."""

    leantime_url: str = "http://localhost:3007"
    conport_url: str = "http://localhost:3009"
    auto_switch: bool = False

    @classmethod
    def from_dict(cls, raw: Optional[Dict[str, object]]) -> "PMModeSettings":
        if not raw:
            return cls()
        return cls(
            leantime_url=str(raw.get("leantime_url", cls.leantime_url)),
            conport_url=str(raw.get("conport_url", cls.conport_url)),
            auto_switch=bool(raw.get("auto_switch", False)),
        )


@dataclass(slots=True)
class ServiceEndpoints:
    """Network endpoints polled by the dashboard."""

    adhd_engine_url: str = "http://localhost:3008"
    activity_capture_url: str = "http://localhost:3006"
    serena_url: str = "http://localhost:3010"
    litellm_url: str = "http://localhost:4000"
    docker_compose_bin: str = "docker-compose"

    @classmethod
    def from_dict(cls, raw: Optional[Dict[str, object]]) -> "ServiceEndpoints":
        if not raw:
            return cls()
        return cls(
            adhd_engine_url=str(raw.get("adhd_engine_url", cls.adhd_engine_url)),
            activity_capture_url=str(raw.get("activity_capture_url", cls.activity_capture_url)),
            serena_url=str(raw.get("serena_url", cls.serena_url)),
            litellm_url=str(raw.get("litellm_url", cls.litellm_url)),
            docker_compose_bin=str(raw.get("docker_compose_bin", cls.docker_compose_bin)),
        )


@dataclass(slots=True)
class DopeLayoutSettings:
    """Aggregated configuration consumed by the Dope layout runtime."""

    default_mode: ModeLiteral = "implementation"
    metrics_bar_enabled: bool = True
    transient_messages: TransientPreferences = field(default_factory=TransientPreferences)
    pm_mode: PMModeSettings = field(default_factory=PMModeSettings)
    services: ServiceEndpoints = field(default_factory=ServiceEndpoints)
    state_file: Path = field(default_factory=lambda: Path.home() / ".cache" / "dopemux" / "dope_dashboard_state.json")

    @classmethod
    def from_dict(cls, raw: Optional[Dict[str, object]]) -> "DopeLayoutSettings":
        if not raw:
            return cls()
        mode = str(raw.get("default_mode", "implementation")).lower()
        if mode not in {"implementation", "pm"}:
            mode = "implementation"
        metrics_enabled = bool(raw.get("metrics_bar_enabled", True))
        transient_cfg = raw.get("transient_messages") or {}
        pm_raw = raw.get("pm_mode") or {}
        services_raw = raw.get("services") or {}
        state_file = raw.get("state_file")
        if state_file:
            state_path = Path(state_file).expanduser()
        else:
            state_path = Path.home() / ".cache" / "dopemux" / "dope_dashboard_state.json"
        return cls(
            default_mode=mode,  # type: ignore[arg-type]
            metrics_bar_enabled=metrics_enabled,
            transient_messages=TransientPreferences.from_dict(transient_cfg),
            pm_mode=PMModeSettings.from_dict(pm_raw),
            services=ServiceEndpoints.from_dict(services_raw),
            state_file=state_path,
        )
