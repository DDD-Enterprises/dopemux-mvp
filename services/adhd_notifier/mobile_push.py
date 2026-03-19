"""Compatibility wrapper for the hyphenated ADHD notifier package."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "adhd-notifier" / "mobile_push.py"
SPEC = spec_from_file_location("services.adhd_notifier._mobile_push_impl", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Unable to load mobile_push implementation from {MODULE_PATH}")

MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

MobilePushNotifier = MODULE.MobilePushNotifier
NotificationPriority = MODULE.NotificationPriority
PushConfig = MODULE.PushConfig
send_adhd_notification = MODULE.send_adhd_notification

__all__ = [
    "MobilePushNotifier",
    "NotificationPriority",
    "PushConfig",
    "send_adhd_notification",
]
