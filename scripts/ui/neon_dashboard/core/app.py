"""Main Textual application powering the Dope layout dashboard."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Type
import inspect

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.reactive import reactive

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dopemux.config import ConfigManager  # noqa: E402

from scripts.neon_dashboard.collectors.impl_collector import ImplementationCollector  # noqa: E402
from scripts.neon_dashboard.collectors.pm_collector import PMCollector  # noqa: E402
from scripts.neon_dashboard.components.transient_messages import (  # noqa: E402
    TransientMessageManager,
    TransientMessagePayload,
    TransientMessagesWidget,
    TransientPriority,
)
from scripts.neon_dashboard.config.settings import DopeLayoutSettings  # noqa: E402
from scripts.neon_dashboard.core.pane_manager import PaneManager, PaneRole  # noqa: E402
from scripts.neon_dashboard.core.state import DashboardState, DashboardStateStore  # noqa: E402
from scripts.neon_dashboard.panes.adhd_monitor import ADHDMonitorPane  # noqa: E402
from scripts.neon_dashboard.panes.pm_hierarchy import PMHierarchyPane  # noqa: E402
from scripts.neon_dashboard.panes.system_monitor import SystemMonitorPane  # noqa: E402
from scripts.neon_dashboard.panes.task_detail import TaskDetailPane  # noqa: E402


def load_settings() -> DopeLayoutSettings:
    cfg_manager = ConfigManager()
    config = cfg_manager.load_config()
    raw = {}
    if hasattr(config, "dope_layout"):
        raw = config.dope_layout.model_dump()  # type: ignore[attr-defined]
    return DopeLayoutSettings.from_dict(raw)


class NeonDashboardApp(App):
    """Textual runtime orchestrating the left/right monitors."""

    CSS = """
    Screen, #dope-body {
        height: 100%;
        background: $panel;
    }
    """

    # Local logger for dashboard events
    import logging
    logger = logging.getLogger("neon_dashboard")

    BINDINGS = [
        Binding("m", "toggle_mode", "Toggle mode"),
        Binding("d", "dismiss_transient", "Dismiss message"),
        Binding("p", "plan_untracked", "Plan untracked"),
        Binding("c", "quick_commit", "Quick commit"),
        Binding("?", "show_help", "Help"),
    ]

    pane_role = reactive("left")

    def __init__(self, pane_role: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.pane_role = (pane_role or os.getenv("NEON_DASHBOARD_PANE_ROLE", "left")).lower()
        if self.pane_role not in {"left", "right"}:
            self.pane_role = "left"
        self.settings = load_settings()
        self.state_store = DashboardStateStore(self.settings)
        self.pane_manager = PaneManager(self.settings, self.state_store)
        self.impl_collector = ImplementationCollector(self.settings.services)
        self.pm_collector = PMCollector(self.settings.pm_mode)
        self.impl_data: Dict[str, Any] = {}
        self.pm_data: Dict[str, Any] = {"epics": [], "sprint": {}}
        self._active_widget: Optional[Any] = None
        self._active_widget_type: Optional[Type[Any]] = None
        self._body_container: Optional[Container] = None
        self._tasks: list[asyncio.Task] = []
        self.transient_widget: Optional[TransientMessagesWidget] = None
        self.transient_manager: Optional[TransientMessageManager] = None

    def compose(self) -> ComposeResult:
        transient_widget = TransientMessagesWidget()
        body = Container(id="dope-body")
        self.transient_widget = transient_widget
        self._body_container = body
        yield transient_widget
        yield body

    async def on_mount(self) -> None:
        await self.state_store.load()
        if self.transient_widget is None:
            self.transient_widget = self.query_one(TransientMessagesWidget)
        self.transient_manager = TransientMessageManager(self.transient_widget)
        self.transient_manager.add_listener(self._on_transient_change)

        await self._apply_state(self.state_store.state)

        # Single refresh loop consolidating all updates to avoid duplicate pane rendering
        self._tasks.append(asyncio.create_task(self._refresh_loop()))

    async def on_unmount(self) -> None:
        for task in self._tasks:
            task.cancel()
        await self.impl_collector.close()
        await self.pm_collector.close()

    async def action_toggle_mode(self) -> None:
        await self.state_store.toggle_mode()
        await self._apply_state(self.state_store.state)

    async def action_dismiss_transient(self) -> None:
        if self.transient_manager:
            self.transient_manager.dismiss_current()

    async def action_plan_untracked(self) -> None:
        await self.state_store.set_mode("pm")
        await self._apply_state(self.state_store.state)

    async def action_quick_commit(self) -> None:
        # Placeholder for future automation
        self.console.logger.info("[dim]Quick commit triggered (stub).[/dim]")

    async def action_show_help(self) -> None:
        self.console.print(
            "[bold]Dope Layout Hotkeys[/bold]: M toggle | P plan | C commit | D dismiss | arrows navigate (PM)"
        )

    async def _refresh_loop(self) -> None:
        impl_interval = 5
        pm_interval = 10
        state_interval = 0.75
        last_impl = last_pm = last_state = 0.0
        while True:
            now = asyncio.get_event_loop().time()
            if now - last_impl >= impl_interval:
                data = await self.impl_collector.get("impl") or {}
                self.impl_data = data
                last_impl = now
            if now - last_pm >= pm_interval:
                data = await self.pm_collector.get("pm") or {"epics": [], "sprint": {}}
                self.pm_data = data
                last_pm = now
            if now - last_state >= state_interval:
                updated = await self.state_store.poll_external_updates()
                if updated:
                    await self._apply_state(updated)
                last_state = now
            await self._apply_current_data()
            self._evaluate_transients()
            await asyncio.sleep(0.25)

    async def _apply_state(self, state: DashboardState) -> None:
        await self._ensure_widget_for_state(state)
        await self._apply_current_data()

    async def _ensure_widget_for_state(self, state: DashboardState) -> None:
        role: PaneRole = "left" if self.pane_role == "left" else "right"
        target_cls = self.pane_manager.widget_for_role(role)
        if target_cls == self._active_widget_type and self._active_widget is not None:
            return

        container = self._body_container or self.query_one("#dope-body", Container)
        for child in list(container.children):
            child.remove()

        widget = target_cls()
        if isinstance(widget, PMHierarchyPane):
            widget.on_task_selected = lambda task: asyncio.create_task(self._handle_pm_selection(task))

        # Mount first so internal widgets exist before updates
        await container.mount(widget)
        self._active_widget = widget
        self._active_widget_type = target_cls

        # Now apply initial data safely
        if isinstance(widget, PMHierarchyPane):
            widget.update_epics(self.pm_data.get("epics", []))
        elif isinstance(widget, ADHDMonitorPane):
            widget.update_from_sources(self.impl_data)
        elif isinstance(widget, TaskDetailPane):
            task = self._resolve_task(self.state_store.state.selected_task_id)
            widget.update_task(task)
        elif isinstance(widget, SystemMonitorPane):
            widget.update_from_sources(self.impl_data)

    async def _apply_current_data(self) -> None:
        if not self._active_widget:
            return
        if isinstance(self._active_widget, ADHDMonitorPane):
            self._active_widget.update_from_sources(self.impl_data)
        elif isinstance(self._active_widget, SystemMonitorPane):
            self._active_widget.update_from_sources(self.impl_data)
        elif isinstance(self._active_widget, PMHierarchyPane):
            self._active_widget.update_epics(self.pm_data.get("epics", []))
        elif isinstance(self._active_widget, TaskDetailPane):
            task = self._resolve_task(self.state_store.state.selected_task_id)
            self._active_widget.update_task(task)

    def _resolve_task(self, task_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not task_id:
            return None
        for epic in self.pm_data.get("epics", []):
            for task in epic.get("tasks", []):
                if str(task.get("id")) == str(task_id):
                    return task
                for sub in task.get("subtasks", []):
                    if str(sub.get("id")) == str(task_id):
                        return sub
        return None

    async def _handle_pm_selection(self, task: Dict[str, Any]) -> None:
        task_id = str(task.get("id")) if task else None
        task_name = task.get("name") if task else None
        await self.state_store.set_selected_task(task_id, task_name)
        if isinstance(self._active_widget, TaskDetailPane) and self.pane_role == "right":
            self._active_widget.update_task(task)

    def _evaluate_transients(self) -> None:
        if not self.settings.transient_messages.enabled or not self.transient_manager:
            return
        thresholds = self.settings.transient_messages.thresholds
        serena = self.impl_data.get("serena") or {}
        age_days = int(serena.get("age_days") or 0)
        file_count = int(serena.get("file_count") or 0)
        if file_count <= 0:
            return

        if age_days >= thresholds.untracked_critical_days and self.settings.transient_messages.untracked_work:
            payload = TransientMessagePayload(
                message_id="untracked-critical",
                title="CRITICAL: Untracked Work Detected",
                body=[
                    f"{file_count} files modified",
                    f"Age: {age_days} days",
                    "No matching task in Leantime/ConPort",
                ],
                priority=TransientPriority.CRITICAL,
                actions={"P": "Plan work", "C": "Commit", "D": "Dismiss"},
            )
            self.transient_manager.enqueue(payload)
        elif age_days >= thresholds.untracked_warning_days and self.settings.transient_messages.untracked_work:
            payload = TransientMessagePayload(
                message_id="untracked-warning",
                title="Warning: Untracked work accumulating",
                body=[
                    f"{file_count} files pending commit",
                    f"Age: {age_days} days",
                    "Press P to plan this work.",
                ],
                priority=TransientPriority.WARNING,
                actions={"P": "Plan work", "D": "Dismiss"},
            )
            self.transient_manager.enqueue(payload)

    def _on_transient_change(self, payload: Optional[TransientMessagePayload]) -> None:
        target = payload.message_id if payload else None
        asyncio.create_task(self.state_store.set_active_transient(target))

    async def on_key(self, event: events.Key) -> None:
        # Let PM hierarchy handle navigation keys
        try:
            handler = super().on_key  # type: ignore[attr-defined]
        except AttributeError:
            handler = None
        if handler:
            result = handler(event)
            if inspect.isawaitable(result):
                await result


def run() -> None:
    pane_role = os.getenv("NEON_DASHBOARD_PANE_ROLE", "left")
    app = NeonDashboardApp(pane_role=pane_role)
    app.run()


if __name__ == "__main__":
    run()
