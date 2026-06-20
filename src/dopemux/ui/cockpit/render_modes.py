"""Deterministic five-mode render facade for the Dopemux Cockpit."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .render import (
    STATIC_DEMO_BANNER,
    TOO_SMALL_MESSAGE,
    TOP_LEVEL_MODES,
    Frame,
    PaneDeclaration,
    PaneRender,
    Rule,
    render_pm,
    viewport_supported,
)


SUPPORTED_COCKPIT_MODES: tuple[str, ...] = (
    "pm",
    "implementer",
    "overview",
    "services",
    "events",
)

MODE_TITLES: dict[str, str] = {
    "pm": "PM",
    "implementer": "Implementer",
    "overview": "Overview",
    "services": "Services",
    "events": "Events",
}


@dataclass(frozen=True)
class ModeModel:
    """Static mode body assembled from governed package/remediation surfaces."""

    mode: str
    subtitle: str
    panes: tuple[PaneRender, ...]


def normalize_mode(mode: str) -> str:
    """Normalize a cockpit mode token and fail closed on unsupported modes."""
    normalized = mode.strip().lower()
    if normalized not in SUPPORTED_COCKPIT_MODES:
        raise ValueError(f"unsupported cockpit mode: {mode!r}")
    return normalized


def render_cockpit(
    mode: str = "pm",
    *,
    cols: int = 120,
    rows: int = 40,
    plain: bool = False,
) -> str:
    """Render a deterministic, no-write cockpit mode surface."""
    normalized = normalize_mode(mode)
    if normalized == "pm":
        return render_pm(cols=cols, rows=rows, plain=plain)
    if not viewport_supported(cols, rows):
        return TOO_SMALL_MESSAGE

    model = mode_model(normalized)
    lines: list[str] = [
        f"# Dopemux Cockpit mode={MODE_TITLES[normalized]}",
        STATIC_DEMO_BANNER,
        "runtime_surface: artifact-derived static continuation",
        "READY_FOR_CLAUDE_DESIGN: not approved",
        f"viewport: {cols}x{rows}",
        _mode_bar(normalized),
        Rule(min(cols, 120)).render(),
        f"[chrome] top_level_modes: {' | '.join(TOP_LEVEL_MODES)}",
        "[chrome] secondary_surfaces: Command Palette | Settings/Admin/Runtime | Safe Actions / Proof Gate | Unknown / Drift Queue",
        "[chrome] SRC omitted on chrome; data rows below carry SRC labels",
        f"[{normalized}] {model.subtitle}",
    ]
    for pane in model.panes:
        lines.extend(_render_pane(pane, cols=cols))
    return "\n".join(lines)


def mode_model(mode: str) -> ModeModel:
    """Return the static data model for a supported non-PM mode."""
    normalized = normalize_mode(mode)
    if normalized == "pm":
        raise ValueError("PM mode is rendered by render_pm")
    return _MODE_MODELS[normalized]


def _mode_bar(active: str) -> str:
    cells: list[str] = []
    for key in SUPPORTED_COCKPIT_MODES:
        title = MODE_TITLES[key]
        cells.append(f"[ {title} ]" if key == active else f"  {title}  ")
    return "modes: " + " | ".join(cells)


def _render_pane(pane: PaneRender, *, cols: int) -> list[str]:
    body: list[str] = [*pane.declaration.header_lines()]
    if pane.src:
        body.append(f"SRC={pane.src}")
    body.extend(pane.body)
    return Frame(width=cols, title=pane.title).render(body)


def _pane(
    *,
    title: str,
    domain: str,
    authority: str,
    role: str,
    next_action: str,
    src: str,
    body: Iterable[str],
) -> PaneRender:
    return PaneRender(
        title=title,
        declaration=PaneDeclaration(
            domain=domain,
            authority=authority,
            role=role,
            next_action=next_action,
        ),
        body=tuple(body),
        src=src,
    )


_MODE_MODELS: dict[str, ModeModel] = {
    "implementer": ModeModel(
        mode="implementer",
        subtitle="task packet execution handoff; no runtime mutation",
        panes=(
            _pane(
                title="LEFT RAIL  task packet queue",
                domain="implementation_queue",
                authority="dopetask external execution runtime",
                role="derived",
                next_action="inspect_packet",
                src="dopetask",
                body=(
                    "[LOGGED] task packet TP-DMX-COCKPIT-ELECTRIC-REFRESH-RUNTIME-001 status=planning",
                    "[EDGE] execution agent requires validated packet and clean worktree",
                    "task packet handoff: commit-sized scope, proof bundle required",
                    "UNKNOWN: supervisor approval freshness must be rechecked before mutation",
                ),
            ),
            _pane(
                title="CENTER  proof and validation lane",
                domain="implementation_evidence",
                authority="proof bundle and repo tests",
                role="canonical",
                next_action="validate",
                src="proof-bundle",
                body=(
                    "[LOGGED] proof bundle records commands, exit codes, residual risks",
                    "[BLOCKED] final design readiness remains not approved",
                    "required checks: packet schema, focused pytest, compileall, diff check",
                    "no service start/stop, workflow transition, or PM mutation is executable here",
                ),
            ),
        ),
    ),
    "overview": ModeModel(
        mode="overview",
        subtitle="operator control summary; advisory only",
        panes=(
            _pane(
                title="LEFT RAIL  cockpit topology",
                domain="operator_overview",
                authority="runtime code and governed package matrices",
                role="derived",
                next_action="inspect",
                src="runtime-code",
                body=(
                    "[LIVE] operator control surface renders five top-level modes",
                    "[LOGGED] runtime code owns display, not PM truth",
                    "operator control cannot reclassify UNKNOWN or promote blocked rows",
                    "bridge proxy is route/proxy context only, never canonical PM authority",
                ),
            ),
            _pane(
                title="CENTER  remediation status",
                domain="cockpit_remediation",
                authority="design pack and task packet evidence",
                role="derived",
                next_action="plan_next_packet",
                src="design-pack",
                body=(
                    "[LOGGED] Direction B Electric Refresh is continuation input",
                    "[EDGE] uploaded handback has no editable source files or bundled fonts",
                    "token conflict: uploaded Option E remains advisory until token packet",
                    "READY_FOR_CLAUDE_DESIGN remains not approved",
                ),
            ),
        ),
    ),
    "services": ModeModel(
        mode="services",
        subtitle="service visibility and guarded action policy; no execution",
        panes=(
            _pane(
                title="LEFT RAIL  service inventory",
                domain="service_inventory",
                authority="service catalog and compose wiring",
                role="derived",
                next_action="inspect_service",
                src="service-catalog",
                body=(
                    "[LOGGED] service catalog rows are visibility-only in this packet",
                    "[EDGE] typed service-id required before any future action packet",
                    "policy gate blocks start/stop without explicit packet and operator approval",
                    "UNKNOWN: live container health is not queried by this static renderer",
                ),
            ),
            _pane(
                title="CENTER  safe action gate",
                domain="service_action_gate",
                authority="safe actions / proof gate",
                role="canonical",
                next_action="open_proof_gate",
                src="safe-action-gate",
                body=(
                    "[BLOCKED] T4 remote mutation policy absent",
                    "[BLOCKED] TX/TU tiers never executable",
                    "typed service-id, policy gate, proof receipt, and operator consent required",
                    "this renderer never invokes shell, network, compose, or service commands",
                ),
            ),
        ),
    ),
    "events": ModeModel(
        mode="events",
        subtitle="append-only event and chronicle visibility",
        panes=(
            _pane(
                title="LEFT RAIL  event stream summary",
                domain="event_visibility",
                authority="dope-memory chronicle and event producers",
                role="mirrored",
                next_action="inspect_receipt",
                src="dope-memory",
                body=(
                    "[LOGGED] chronicle receipts are append-only visibility artifacts",
                    "[EDGE] event producers remain upstream authority for emitted facts",
                    "append-only contract: renderer cannot mutate, retry, or backfill events",
                    "UNKNOWN: live event freshness is not queried by this static renderer",
                ),
            ),
            _pane(
                title="CENTER  replay and drift guard",
                domain="event_replay_guard",
                authority="event producers and proof receipts",
                role="derived",
                next_action="trace",
                src="event-producers",
                body=(
                    "[LOGGED] replay safety requires stable ordering and explicit provenance",
                    "[BLOCKED] unknown drift resolution requires a separate packet",
                    "dope-memory records receipts; runtime renderer only presents them",
                    "no hidden retry, implicit coercion, or silent fallback is introduced",
                ),
            ),
        ),
    ),
}
