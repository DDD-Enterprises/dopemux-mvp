"""Pure static cockpit rendering."""

from __future__ import annotations

from typing import Any

from .frame import LAYOUTS, SUPPORTED_SIZES, FrameBuffer, Layout, draw_static_grid
from .model import SnapshotState, state_from_seed
from .seed import load_seed
from .tokens import normalize_status_chip, validate_rendered_text

UNSUPPORTED_SIZE_MESSAGE = (
    "[BLOCKER] terminal size unsupported. Problem: cockpit snapshot supports "
    "120x40, 100x32, or 80x24. Why: layout invariants are size-bound in slice 1. "
    "Fix: choose a supported size. NEXT: rerun with --snapshot 120x40."
)
TOO_SMALL_MESSAGE = (
    "[BLOCKER] terminal too small.\n"
    "Problem: cockpit requires at least 80x24.\n"
    "Why: layout invariants cannot be honored below this size.\n"
    "Fix: resize to 80x24 or larger.\n"
    "NEXT: rerun with --snapshot 80x24."
)


def render_snapshot(size: str, *, mode: str = "Services", seed: dict[str, Any] | None = None) -> str:
    """Render a supported named snapshot or return a blocker for unsupported sizes."""

    if size in LAYOUTS:
        return render_cockpit(LAYOUTS[size].width, LAYOUTS[size].height, mode=mode, seed=seed)
    try:
        width_text, height_text = size.lower().split("x", 1)
        width = int(width_text)
        height = int(height_text)
    except ValueError:
        return UNSUPPORTED_SIZE_MESSAGE
    if width < 80 or height < 24:
        return TOO_SMALL_MESSAGE
    return UNSUPPORTED_SIZE_MESSAGE


def render_cockpit(
    width: int,
    height: int,
    *,
    mode: str = "Services",
    seed: dict[str, Any] | None = None,
) -> str:
    """Render seed state into a deterministic framebuffer string."""

    size = f"{width}x{height}"
    layout = LAYOUTS.get(size)
    if layout is None:
        return TOO_SMALL_MESSAGE if width < 80 or height < 24 else UNSUPPORTED_SIZE_MESSAGE

    state = state_from_seed(seed or load_seed())
    frame = FrameBuffer(width, height, layout)
    draw_static_grid(frame, layout)
    _render_header(frame, layout, state, mode)
    _render_modes(frame, layout, state, mode)
    if mode == "Services":
        _render_services(frame, layout, state)
    else:
        _render_placeholder(frame, layout, state, mode)
    _render_status(frame, layout, state, mode)
    output = frame.render()
    validate_rendered_text(output)
    return output


def _write_in(frame: FrameBuffer, row: int, start: int, end: int, text: str) -> None:
    if end <= start:
        return
    frame.write(row, start, text[: end - start])


def _render_header(frame: FrameBuffer, layout: Layout, state: SnapshotState, mode: str) -> None:
    workspace = state.data["workspace"]
    _write_in(frame, 1, 2, layout.left_divider, "dopemux cockpit static")
    _write_in(frame, 1, layout.left_divider + 2, layout.right_divider, f"workspace {workspace['id']} SRC={workspace['SRC']}")
    _write_in(frame, 1, layout.right_divider + 2, layout.width - 2, f"mode {mode} SRC={workspace['SRC']}")


def _render_modes(frame: FrameBuffer, layout: Layout, state: SnapshotState, mode: str) -> None:
    labels = []
    for index, name in enumerate(state.modes, start=1):
        marker = "*" if name == mode else " "
        labels.append(f"{index} {marker}{name} SRC=dopemux")
    _write_in(frame, 3, 2, layout.left_divider, labels[0])
    _write_in(frame, 3, layout.left_divider + 2, layout.right_divider, " | ".join(labels[1:3]))
    selected_services = "4 *Services SRC=dopemux" if mode == "Services" else "4  Services SRC=dopemux"
    _write_in(frame, 3, layout.right_divider + 2, layout.width - 2, f"{selected_services} | 5 Events")


def _render_services(frame: FrameBuffer, layout: Layout, state: SnapshotState) -> None:
    services = state.services
    rte = state.rte_child_surface
    _write_in(frame, 5, 2, layout.left_divider, f"Services authority: {services['authority']}")
    _write_in(frame, 5, layout.left_divider + 2, layout.right_divider, f"Services -> {services['selected']} authority: {rte['authority']}")
    _write_in(frame, 5, layout.right_divider + 2, layout.width - 2, f"Inspector authority: {services['inspector']['authority']}")

    row = 6
    for service in services["rows"]:
        chip = normalize_status_chip(service["status"])
        prefix = ">" if service["name"] == services["selected"] else " "
        text = f"{prefix} SRC={service['SRC']} [{chip}] {service['name']} {service['kind']}"
        _write_in(frame, row, 2, layout.left_divider, text)
        row += 1

    _render_rte_runs(frame, layout, rte)
    _render_inspector(frame, layout, services["inspector"])


def _render_rte_runs(frame: FrameBuffer, layout: Layout, rte: dict[str, Any]) -> None:
    center_start = layout.left_divider + 2
    center_end = layout.right_divider
    _write_in(frame, 6, center_start, center_end, "Tabs SRC=repo-truth-extractor R1 Runs | R2 Active")
    _write_in(frame, 7, center_start, center_end, "Tabs SRC=repo-truth-extractor R3 Prescan | R4 Doctor")
    _write_in(frame, 8, center_start, center_end, "Tabs SRC=repo-truth-extractor R5 Coverage | R6 Audit")
    _write_in(frame, 9, center_start, center_end, "R1 Runs authority: repo-truth-extractor")
    row = 10
    for run in rte["runs"]:
        chip = normalize_status_chip(run["status"])
        _write_in(frame, row, center_start, center_end, f"SRC={run['SRC']} [{chip}] {run['run_id']}")
        row += 1
        _write_in(
            frame,
            row,
            center_start,
            center_end,
            f"SRC={run['SRC']} phase={run['phase']} repo={run['repo']} alerts={run['alerts']}",
        )
        row += 1


def _render_inspector(frame: FrameBuffer, layout: Layout, inspector: dict[str, Any]) -> None:
    start = layout.right_divider + 2
    end = layout.width - 2
    _write_in(frame, 6, start, end, f"subject SRC={inspector['authority']} {inspector['subject']}")
    _write_in(frame, 7, start, end, f"provenance={inspector['provenance']} SRC={inspector['authority']}")
    row = 8
    for item in inspector["rows"]:
        _write_in(frame, row, start, end, f"SRC={item['SRC']} {item['label']}={item['value']}")
        row += 1

    bridge = inspector["bridge"]
    chip = normalize_status_chip(bridge["status_chip"])
    bridge_row = layout.inspector_split + 1
    _write_in(frame, bridge_row, start, end, f"Bridge actions authority: dopecon-bridge")
    _write_in(frame, bridge_row + 1, start, end, f"SRC=dopecon-bridge [{chip}] adapter-only segregated")
    _write_in(frame, bridge_row + 2, start, end, "WRITE -> <service> : <action>")
    action = bridge["actions"][0]
    _write_in(frame, bridge_row + 3, start, end, f"SRC={action['SRC']} {action['label']}")
    _write_in(frame, bridge_row + 4, start, end, bridge["footer"])


def _render_placeholder(frame: FrameBuffer, layout: Layout, state: SnapshotState, mode: str) -> None:
    placeholder = state.placeholder_modes[mode]
    _write_in(frame, 5, 2, layout.left_divider, f"{mode} authority: {placeholder['authority']}")
    _write_in(frame, 5, layout.left_divider + 2, layout.right_divider, f"{mode} placeholder authority: {placeholder['authority']}")
    _write_in(frame, 5, layout.right_divider + 2, layout.width - 2, f"Inspector authority: {placeholder['authority']}")
    _write_in(frame, 7, layout.left_divider + 2, layout.right_divider, f"SRC=dopemux [{placeholder['status_chip']}] placeholder mode.")
    _write_in(frame, 8, layout.left_divider + 2, layout.right_divider, f"SRC=dopemux UNKNOWN: {mode} renderer not wired in slice 1.")
    if mode == "Implementer":
        next_text = "NEXT: implement focus and retrieval panes."
    elif mode == "Overview":
        next_text = "NEXT: implement rollup view."
    elif mode == "Events":
        next_text = "NEXT: implement per-event SRC stream."
    else:
        next_text = "NEXT: implement PM mode."
    _write_in(frame, 9, layout.left_divider + 2, layout.right_divider, f"SRC=dopemux {next_text}")


def _render_status(frame: FrameBuffer, layout: Layout, state: SnapshotState, mode: str) -> None:
    rail = state.status_rail
    left = rail["left"]
    middle = f"mode {mode}"
    right = rail["right"]
    _write_in(frame, layout.command_row, 2, layout.left_divider, "command authority: dopemux")
    _write_in(frame, layout.command_row, layout.left_divider + 2, layout.right_divider, "SRC=dopemux snapshot-only")
    _write_in(frame, layout.command_row, layout.right_divider + 2, layout.width - 2, "no writes no shellouts")
    _write_in(frame, layout.status_row, 2, layout.left_divider, left)
    _write_in(frame, layout.status_row, layout.left_divider + 2, layout.right_divider, middle)
    _write_in(frame, layout.status_row, layout.right_divider + 2, layout.width - 2, right)


def supported_sizes() -> tuple[str, ...]:
    return SUPPORTED_SIZES
