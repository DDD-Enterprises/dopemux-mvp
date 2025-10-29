"""PM hierarchy pane built with Textual's Tree widget."""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Optional

from rich.text import Text
from textual.app import ComposeResult
from textual.widgets import Tree
from textual.containers import ScrollableContainer
from textual.widget import Widget


class PMHierarchyPane(Widget):
    """Displays epics/tasks/subtasks using a navigable tree."""

    BINDINGS = [
        ("up", "cursor_up", "Up"),
        ("down", "cursor_down", "Down"),
        ("left", "collapse", "Collapse"),
        ("right", "expand", "Expand"),
        ("enter", "select", "Select"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._tree: Optional[Tree] = None
        self._items: Dict[str, Dict[str, Any]] = {}
        self.on_task_selected: Optional[Callable[[Dict[str, Any]], None]] = None
        self._pending_epics: Optional[list[Dict[str, Any]]] = None

    def compose(self) -> ComposeResult:
        with ScrollableContainer(id="pm-hierarchy-scroll"):
            tree = Tree("Sprint", id="pm-hierarchy-tree")
            tree.show_root = True
            self._tree = tree
            yield tree
        if self._pending_epics is not None:
            self.update_epics(self._pending_epics)
            self._pending_epics = None

    async def on_mount(self) -> None:
        if self._pending_epics is not None:
            self.update_epics(self._pending_epics)
            self._pending_epics = None

    def update_epics(self, epics: Iterable[Dict[str, Any]]) -> None:
        tree = self._tree
        if tree is None:
            self._pending_epics = list(epics)
            return
        tree.clear()
        tree.root.label = Text("Sprint", style="bold cyan")
        self._items.clear()

        for epic in epics:
            epic_id = str(epic.get("id"))
            epic_label = Text.assemble(
                (" ", "cyan"),
                (epic.get("name", "Epic"), "bold"),
                (f" [{epic.get('completion', 0)}%]", "cyan"),
            )
            epic_node = tree.root.add(epic_label, expand=True, data=epic)
            self._items[epic_id] = epic

            for task in epic.get("tasks", []):
                node = epic_node.add(self._task_label(task), data=task)
                task_id = str(task.get("id"))
                self._items[task_id] = task
                for sub in task.get("subtasks", []):
                    sub_id = str(sub.get("id"))
                    sub_node = node.add(self._task_label(sub), data=sub)
                    self._items[sub_id] = sub
                    sub_node.expand()
                node.expand()
            epic_node.expand()

        tree.root.expand()
        tree.refresh(layout=True)

    def _task_label(self, task: Dict[str, Any]) -> Text:
        status = (task.get("status") or "TODO").upper()
        icon = {
            "DONE": ("", "green"),
            "IN_PROGRESS": ("", "yellow"),
            "BLOCKED": ("", "red"),
        }.get(status, ("", "grey50"))
        estimate = task.get("estimate")
        parts = [
            (f"{icon[0]} ", icon[1]),
            (task.get("name", "Task"), "white"),
        ]
        if estimate:
            parts.append((f" ({estimate}h)", "dim"))
        return Text.assemble(*parts)

    def action_cursor_up(self) -> None:
        tree = self._tree
        if tree is None:
            return
        tree.cursor_up()

    def action_cursor_down(self) -> None:
        tree = self._tree
        if tree is None:
            return
        tree.cursor_down()

    def action_collapse(self) -> None:
        tree = self._tree
        if tree is None:
            return
        node = tree.cursor_node
        if node:
            node.collapse()

    def action_expand(self) -> None:
        tree = self._tree
        if tree is None:
            return
        node = tree.cursor_node
        if node:
            node.expand()

    def action_select(self) -> None:
        tree = self._tree
        if tree is None:
            return
        node = tree.cursor_node
        if node and self.on_task_selected:
            self.on_task_selected(node.data or {})
