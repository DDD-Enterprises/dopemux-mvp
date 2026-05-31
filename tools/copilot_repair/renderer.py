"""Render Copilot repair packets with the repo-governed Jinja2 template."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Template


TEMPLATE_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "03-reference"
    / "templates"
    / "copilot"
    / "pr-repair-packet.md"
)


def render_repair_packet(
    repair_packet: dict[str, Any],
    *,
    template_path: Path = TEMPLATE_PATH,
) -> str:
    """Render a CopilotRepairPacket to Markdown without side effects."""
    template = Template(template_path.read_text(encoding="utf-8"))
    return template.render(**repair_packet).rstrip() + "\n"
