"""Deterministic render model for the Dopemux Cockpit TUI.

This module is the single source of truth for the architecture-safe PM
cockpit slice. It produces deterministic text output for tests and for
plain / audit modes, and it provides the structured data the Textual
shell consumes.

Authority model (per
``docs/03-reference/Dopemux Cockpit TUI Design System/ARCHITECTURE_SAFETY_OVERLAY.md``):

- Leantime owns PM metadata.
- task-orchestrator owns workflow transitions, queue, blockers.
- ConPort owns decisions / progress / project context.
- dope-memory owns chronicle / receipts.
- dope-context owns retrieval surfaces.
- dopecon-bridge is adapter / proxy only -- never canonical authority.
- dopemux is the operator control surface. It does NOT own PM truth.

This slice emits NO live writes and NO PM mutations. All values are
static demo data clearly labeled as such.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence


# ---------------------------------------------------------------------------
# Top-level modes (exactly five)
# ---------------------------------------------------------------------------

TOP_LEVEL_MODES: tuple[str, ...] = (
    "PM",
    "Implementer",
    "Overview",
    "Services",
    "Events",
)

STATIC_DEMO_BANNER: str = "STATIC DEMO  NO WRITES  no live PM mutations"

TOO_SMALL_MESSAGE: str = "[BLOCKER] terminal too small (minimum 80x24)"

# Smallest supported viewport
MIN_COLS: int = 80
MIN_ROWS: int = 24


# ---------------------------------------------------------------------------
# Pane and Top-3 data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PaneDeclaration:
    """Four-field pane declaration required by the safety overlay."""

    domain: str
    authority: str
    role: str  # canonical | derived | mirrored | proxied | authoring | chrome
    next_action: str

    def header_lines(self) -> tuple[str, str, str, str]:
        return (
            f"domain: {self.domain}",
            f"authority: {self.authority}",
            f"role: {self.role}",
            f"next_action: {self.next_action}",
        )


@dataclass(frozen=True)
class Top3Block:
    """ADHD output contract for list-like PM surfaces."""

    items: tuple[str, ...]
    more_count: int
    next_token: str | None

    def to_lines(self) -> list[str]:
        out: list[str] = []
        for index, item in enumerate(self.items[:3], start=1):
            out.append(f"  {index}. {item}")
        out.append(f"  more_count: {self.more_count}")
        out.append(f"  next_token: {self.next_token if self.next_token else 'none'}")
        return out


@dataclass(frozen=True)
class PaneRender:
    """A single PM pane: declaration, body lines, optional SRC tag."""

    title: str
    declaration: PaneDeclaration
    body: tuple[str, ...]
    src: str | None = None  # provenance only, never on chrome


# ---------------------------------------------------------------------------
# Static PM model (demo data; no backend calls)
# ---------------------------------------------------------------------------


def _workflow_slice_map() -> PaneRender:
    block = Top3Block(
        items=(
            "[LIVE]    DMX-COCKPIT-PM-TEXTUAL-001 -- ready_for_triage",
            "[LOGGED]  DMX-PM-PLANE-AUDIT-014 -- adjudication",
            "[EDGE]    DMX-BRIDGE-PROXY-AUDIT-002 -- waiting_on_proxy_review",
        ),
        more_count=4,
        next_token="slice_cursor_DMX-PM-PLANE-AUDIT-019",
    )
    return PaneRender(
        title="LEFT RAIL  workflow / slice map",
        declaration=PaneDeclaration(
            domain="workflow_slice",
            authority="task-orchestrator workflow transitions",
            role="derived",
            next_action="open",
        ),
        body=tuple(block.to_lines()),
        src="task-orchestrator",
    )


def _readiness_queue() -> PaneRender:
    block = Top3Block(
        items=(
            "[LIVE]    DMX-COCKPIT-PM-TEXTUAL-001  legality=ok  blockers=0",
            "[LOGGED]  DMX-PM-PLANE-AUDIT-014     legality=ok  blockers=1",
            "[EDGE]    DMX-BRIDGE-PROXY-AUDIT-002 legality=UNKNOWN  blockers=0",
        ),
        more_count=2,
        next_token="queue_cursor_priority=2",
    )
    return PaneRender(
        title="CENTER UPPER  workflow triage / readiness queue",
        declaration=PaneDeclaration(
            domain="readiness_queue",
            authority="task-orchestrator workflow transitions",
            role="canonical",
            next_action="triage",
        ),
        body=tuple(block.to_lines()),
        src="task-orchestrator",
    )


def _adjudication_context() -> PaneRender:
    body = (
        "blocker:        UNKNOWN -- needs verification from task-orchestrator",
        "transitions:    triage -> ready -> handoff",
        "linked_decision SRC=conport  D-2026.04-PM-014  status=LOGGED",
        "linked_decision SRC=conport  D-2026.04-PM-019  status=LOGGED",
        "chronicle SRC=dope-memory     R-2026.04-CHRON-882  status=AFTERCARE",
        "metadata SRC=leantime         LT-1422  ticket_age=3d",
        "handoff_ready:  false (acceptance subset incomplete)",
    )
    return PaneRender(
        title="CENTER LOWER  adjudication context",
        declaration=PaneDeclaration(
            domain="adjudication",
            authority="task-orchestrator workflow transitions",
            role="canonical",
            next_action="inspect",
        ),
        body=body,
        src=None,  # SRC appears inline per record (see body)
    )


def _selected_slice_detail() -> PaneRender:
    body = (
        "slice_id:        DMX-COCKPIT-PM-TEXTUAL-001",
        "metadata SRC=leantime         LT-1422  owner=hu3mann",
        "context  SRC=conport          PC-DMX-COCKPIT  scope=cockpit pm tui",
        "progress SRC=conport          P-2026.04-PM-022  status=in_progress",
        "transitions: open|triage|handoff  current=triage",
    )
    return PaneRender(
        title="INSPECTOR UPPER  selected slice detail",
        declaration=PaneDeclaration(
            domain="slice_detail",
            authority="task-orchestrator workflow transitions",
            role="canonical",
            next_action="inspect",
        ),
        body=body,
        src=None,
    )


def _canonical_actions() -> PaneRender:
    body = (
        "action: log_decision     SRC=conport            via=conport_action_surface",
        "action: log_progress     SRC=conport            via=conport_action_surface",
        "action: workflow.advance SRC=task-orchestrator  via=task_orchestrator_api",
        "action: chronicle.read   SRC=dope-memory        via=dope_memory_api",
        "action: retrieval.query  SRC=dope-context       via=dope_context_api",
        "note: canonical writes route through their own service surface; not via bridge",
    )
    return PaneRender(
        title="INSPECTOR LOWER UPPER  canonical actions",
        declaration=PaneDeclaration(
            domain="decisions",
            authority="conport decisions/progress context",
            role="authoring",
            next_action="log_decision",
        ),
        body=body,
        src=None,  # body rows carry SRC per record
    )


def _bridge_segregator() -> PaneRender:
    body = (
        "Bridge adapter/proxy: dopecon-bridge",
        "[EDGE] adapter-only segregated",
        "transport_ref: bridge.adapter.kg.read_decisions",
        "transport_ref: bridge.adapter.task_orchestrator.list_blockers",
        "note: adapter actions only; canonical writes route through their owners.",
    )
    return PaneRender(
        title="INSPECTOR LOWER LOWER  bridge segregator (adapter/proxy only)",
        declaration=PaneDeclaration(
            domain="bridge_transport",
            authority="dopecon-bridge adapter/proxy routing",
            role="proxied",
            next_action="inspect_adapter_ref",
        ),
        body=body,
        src="dopecon-bridge",
    )


def _command_status_rail() -> tuple[str, ...]:
    # Chrome: no SRC, no canonical data, no transition controls.
    return (
        "[chrome]  filter=triage  legality=ok  warnings=0  ctrl+k=palette",
        "[chrome]  cue: ADHD_engine: focused; suggest 25-min focus block (advisory only)",
    )


def pm_panes() -> list[PaneRender]:
    """Return the canonical ordered PM pane list (excluding chrome rail)."""
    return [
        _workflow_slice_map(),
        _readiness_queue(),
        _adjudication_context(),
        _selected_slice_detail(),
        _canonical_actions(),
        _bridge_segregator(),
    ]


# ---------------------------------------------------------------------------
# Viewport handling
# ---------------------------------------------------------------------------


def viewport_supported(cols: int, rows: int) -> bool:
    """Return True iff the viewport meets the minimum 80x24 contract."""
    return cols >= MIN_COLS and rows >= MIN_ROWS


def _bridge_role_for_viewport(cols: int, rows: int) -> str:
    """Per-Viewport Degradation Law from ARCHITECTURE_SAFETY_OVERLAY.md.

    - 120 x 40: dedicated bridge segregator pane allowed.
    - 100 x 32: bridge lives in inspector / lower detail (no segregator pane).
    - 80 x 24:  bridge collapses into inspector detail only (no peer pane).
    """
    if cols >= 120 and rows >= 40:
        return "segregator-pane"
    if cols >= 100 and rows >= 32:
        return "inspector-lower-detail"
    return "inspector-detail-collapsed"


# ---------------------------------------------------------------------------
# Deterministic text render
# ---------------------------------------------------------------------------


def _format_pane(pane: PaneRender) -> list[str]:
    out: list[str] = []
    out.append(f"## {pane.title}")
    for line in pane.declaration.header_lines():
        out.append(line)
    if pane.src is not None:
        out.append(f"SRC={pane.src}")
    out.append("")
    out.extend(pane.body)
    return out


def render_pm(cols: int = 120, rows: int = 40, *, plain: bool = False) -> str:
    """Render PM mode deterministically for the given viewport.

    The output is plain text, ANSI-free, and stable across calls with
    identical inputs. Tests rely on this stability.
    """
    if not viewport_supported(cols, rows):
        return TOO_SMALL_MESSAGE

    bridge_role = _bridge_role_for_viewport(cols, rows)

    lines: list[str] = []
    lines.append("# Dopemux Cockpit  mode=PM")
    lines.append(STATIC_DEMO_BANNER)
    lines.append(f"viewport: {cols}x{rows}  bridge_placement: {bridge_role}")
    lines.append(f"modes: {' | '.join(TOP_LEVEL_MODES)}")
    lines.append("")

    panes = pm_panes()

    if bridge_role == "inspector-detail-collapsed":
        # 80x24: bridge is collapsed into inspector detail only -- not a peer pane.
        primary_panes = [p for p in panes if p.declaration.domain != "bridge_transport"]
        for pane in primary_panes:
            lines.extend(_format_pane(pane))
            lines.append("")
        # Collapsed inline detail (one annotated line, NOT a pane).
        lines.append("[inspector-detail] bridge collapsed: dopecon-bridge adapter/proxy ref only")
    else:
        for pane in panes:
            lines.extend(_format_pane(pane))
            lines.append("")

    # Chrome rail: no SRC, no authority claim on data.
    lines.append("---")
    lines.extend(_command_status_rail())
    return "\n".join(lines).rstrip() + "\n"


def render_audit(cols: int = 120, rows: int = 40) -> str:
    """Audit-mode render: identical contract, log-safe (alias of plain)."""
    return render_pm(cols=cols, rows=rows, plain=True)


# ---------------------------------------------------------------------------
# Helpers exposed for the Textual shell
# ---------------------------------------------------------------------------


def iter_top_level_modes() -> Iterable[str]:
    return iter(TOP_LEVEL_MODES)


def pane_titles() -> Sequence[str]:
    return tuple(p.title for p in pm_panes())
