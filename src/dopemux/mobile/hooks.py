"""Helpers for wiring mobile notifications into Dopemux workflows."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Optional

import click

from ..config import ConfigManager
from .runtime import notify_mobile_event


def _get_config_manager(ctx: Optional[click.Context]) -> ConfigManager:
    if ctx and ctx.obj and isinstance(ctx.obj.get("config_manager"), ConfigManager):
        return ctx.obj["config_manager"]
    return ConfigManager()


@contextmanager
def mobile_task_notification(
    ctx: Optional[click.Context],
    task_label: str,
    *,
    success_message: Optional[str] = None,
    failure_message: Optional[str] = None,
):
    """Context manager that sends mobile notifications on completion/failure."""

    config_manager = _get_config_manager(ctx)
    success_template = success_message or f"✅ {task_label}"
    failure_template = failure_message or f"❌ {task_label}"

    try:
        yield
    except SystemExit as exc:  # pragma: no cover - behavior validated indirectly
        message = success_template if (exc.code is None or exc.code == 0) else failure_template
        notify_mobile_event(config_manager, message)
        raise
    except Exception:
        notify_mobile_event(config_manager, failure_template)
        raise
    else:
        notify_mobile_event(config_manager, success_template)
