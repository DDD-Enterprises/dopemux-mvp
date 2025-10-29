"""Dynamic pane manager coordinating PM/Implementation views."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Tuple, Type

from textual.widget import Widget

from ..config.settings import DopeLayoutSettings
from .state import DashboardState, DashboardStateStore
from ..panes.adhd_monitor import ADHDMonitorPane
from ..panes.pm_hierarchy import PMHierarchyPane
from ..panes.system_monitor import SystemMonitorPane
from ..panes.task_detail import TaskDetailPane


PaneRole = Literal["left", "right"]


@dataclass(slots=True)
class PaneSet:
    """Resolved widget classes for the current mode."""

    left_cls: Type[Widget]
    right_cls: Type[Widget]


class PaneManager:
    """Maps dashboard state to the appropriate widget implementations."""

    def __init__(self, settings: DopeLayoutSettings, state_store: DashboardStateStore):
        self.settings = settings
        self.state_store = state_store

    def current_panes(self) -> PaneSet:
        """Return the widget classes that should be active in each monitor."""
        state: DashboardState = self.state_store.state
        if state.mode == "pm":
            return PaneSet(left_cls=PMHierarchyPane, right_cls=TaskDetailPane)
        return PaneSet(left_cls=ADHDMonitorPane, right_cls=SystemMonitorPane)

    def widget_for_role(self, role: PaneRole) -> Type[Widget]:
        """Return the widget class that should be rendered in a specific pane."""
        panes = self.current_panes()
        return panes.left_cls if role == "left" else panes.right_cls

