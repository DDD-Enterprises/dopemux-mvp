"""Transient message overlay system for ADHD-friendly nudges."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional

from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget


class TransientPriority(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


PRIORITY_STYLES = {
    TransientPriority.CRITICAL: ("red", "bold white"),
    TransientPriority.WARNING: ("yellow", "black"),
    TransientPriority.INFO: ("cyan", "white"),
}


@dataclass(slots=True)
class TransientMessagePayload:
    """Represents a single transient message."""

    message_id: str
    title: str
    body: List[str]
    priority: TransientPriority
    actions: Dict[str, str] = field(default_factory=dict)
    auto_dismiss_seconds: Optional[int] = None


class TransientActivated(Message):
    """Textual message fired when a transient becomes active."""

    def __init__(self, payload: Optional[TransientMessagePayload]):
        super().__init__()
        self.payload = payload


class TransientMessagesWidget(Widget):
    """Widget that renders the current transient message when present."""

    DEFAULT_CSS = """
    TransientMessagesWidget {
        dock: top;
        height: auto;
    }
    """

    payload: reactive[Optional[TransientMessagePayload]] = reactive(None)

    def render(self):
        payload = self.payload
        if not payload:
            return ""
        border_style, text_style = PRIORITY_STYLES[payload.priority]
        table = Table.grid(expand=True)
        table.add_column(justify="left")
        table.add_row(Text(payload.title, style=text_style))
        for line in payload.body:
            table.add_row(Text(line))
        if payload.actions:
            actions = "  ".join(f"[{key}] {label}" for key, label in payload.actions.items())
            table.add_row(Text(actions, style="italic"))
        return Panel(table, border_style=border_style, title="⚡ Attention")


class TransientMessageManager:
    """Priority-aware message queue with auto-dismiss support."""

    def __init__(self, widget: TransientMessagesWidget):
        self.widget = widget
        self._queue: List[TransientMessagePayload] = []
        self._current: Optional[TransientMessagePayload] = None
        self._auto_dismiss_task: Optional[asyncio.Task] = None
        self._listeners: List[Callable[[Optional[TransientMessagePayload]], None]] = []

    def add_listener(self, callback: Callable[[Optional[TransientMessagePayload]], None]) -> None:
        self._listeners.append(callback)

    def _notify(self) -> None:
        for callback in list(self._listeners):
            try:
                callback(self._current)
            except Exception as e:
                continue

                logger.error(f"Error: {e}")
    def enqueue(self, payload: TransientMessagePayload) -> None:
        """Add a message honouring priority ordering."""
        # Remove existing message with same id
        self._queue = [item for item in self._queue if item.message_id != payload.message_id]
        # Insert maintaining priority (critical > warning > info)
        priority_order = {
            TransientPriority.CRITICAL: 0,
            TransientPriority.WARNING: 1,
            TransientPriority.INFO: 2,
        }
        inserted = False
        for idx, existing in enumerate(self._queue):
            if priority_order[payload.priority] < priority_order[existing.priority]:
                self._queue.insert(idx, payload)
                inserted = True
                break
        if not inserted:
            self._queue.append(payload)
        self._advance_queue()

    def dismiss_current(self) -> None:
        if self._current:
            self._current = None
            self.widget.payload = None
            self._cancel_auto_dismiss()
            self._advance_queue()

    def _advance_queue(self) -> None:
        if self._current is not None:
            return
        if not self._queue:
            self.widget.payload = None
            self._notify()
            return
        self._current = self._queue.pop(0)
        self.widget.payload = self._current
        self._schedule_auto_dismiss(self._current)
        self.widget.post_message(TransientActivated(self._current))
        self._notify()

    def _schedule_auto_dismiss(self, payload: TransientMessagePayload) -> None:
        self._cancel_auto_dismiss()
        if payload.priority != TransientPriority.INFO:
            return
        if payload.auto_dismiss_seconds is None:
            payload.auto_dismiss_seconds = 10

        async def _dismiss_later(seconds: int) -> None:
            try:
                await asyncio.sleep(seconds)
                if self._current and self._current.message_id == payload.message_id:
                    self.dismiss_current()
            except asyncio.CancelledError:  # pragma: no cover
                return

        self._auto_dismiss_task = asyncio.create_task(_dismiss_later(payload.auto_dismiss_seconds))

    def _cancel_auto_dismiss(self) -> None:
        task = self._auto_dismiss_task
        if task and not task.done():
            task.cancel()
        self._auto_dismiss_task = None

    @property
    def current(self) -> Optional[TransientMessagePayload]:
        return self._current

