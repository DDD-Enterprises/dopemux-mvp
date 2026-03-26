"""JSON / Rich output dispatch layer.

When ``--json`` is active on the CLI, ``emit()`` serialises *data* as JSON
to stdout.  Otherwise it calls the provided *rich_render* callable which
should print Rich output to the console.

Usage::

    from dopemux.ui.output import emit

    emit(
        ctx,
        data={"checks": [{"name": "docker", "passed": True}]},
        rich_render=lambda: console.print(table),
    )
"""

from __future__ import annotations

import json
import sys
from typing import Any, Callable

import click


def emit(
    ctx: click.Context,
    data: dict[str, Any],
    rich_render: Callable[[], None],
) -> None:
    """Dispatch output to JSON or Rich depending on ``--json`` flag.

    Args:
        ctx: Click context (must contain ``json_output`` in ``ctx.obj``).
        data: Serialisable dict emitted when JSON mode is active.
        rich_render: Zero-arg callable that prints Rich output.
    """
    if ctx.obj and ctx.obj.get("json_output"):
        sys.stdout.write(json.dumps(data, default=str, indent=2) + "\n")
        sys.stdout.flush()
    else:
        rich_render()
