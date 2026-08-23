"""Capability reporting — configured vs live/callable separation (TP-DCP-MCP-RO-0010).

Distinguishes "configured" (a service family is declared present AND
policy-enabled in the registry — see ``registry_v2.ServicePolicy.configured``)
from "discovered", "live", and "callable". Determining whether a runtime is
actually live, owned, or reachable requires a backend/socket/container call,
which is explicitly out of scope for this packet (ADR-DCP-MCP-RO-0009
"Capability Reporting"; TP-DCP-MCP-RO-0010 invariants). Accordingly, every
entry reports ``live == "UNKNOWN"`` and ``callable is False`` — configured
capability NEVER implies callable capability.

Pure: no outbound network calls, no external process spawned, no container
runtime inspected.
"""

from __future__ import annotations

from typing import Any

from .resolver_core import ResolvedTarget


def capability_report(resolved: ResolvedTarget) -> list[dict[str, Any]]:
    """Return one capability entry per service family bound to ``resolved``.

    Each entry: ``{family, configured, resolution_class, chatgpt_posture,
    live, callable}``. ``live`` is always the string ``"UNKNOWN"`` and
    ``callable`` is always ``False`` in this packet.
    """
    report: list[dict[str, Any]] = []
    for family in sorted(resolved.service_policies):
        policy = resolved.service_policies[family]
        report.append(
            {
                "family": family,
                "configured": policy.configured,
                "resolution_class": policy.resolution_class,
                "chatgpt_posture": policy.chatgpt_posture,
                "live": "UNKNOWN",
                "callable": False,
            }
        )
    return report
