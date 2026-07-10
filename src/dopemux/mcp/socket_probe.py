"""Bounded TCP socket probes for MCP port allocation (read-only).

Never starts processes. Timeout-bounded connect checks only.
"""

from __future__ import annotations

import socket
from typing import Optional


DEFAULT_TIMEOUT_S = 0.25
DEFAULT_HOST = "127.0.0.1"


def port_is_free(port: int, host: str = DEFAULT_HOST, *, timeout_s: float = DEFAULT_TIMEOUT_S) -> bool:
    """True if nothing accepts TCP connections on (host, port)."""
    if not (1 <= int(port) <= 65535):
        return False
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout_s)
    try:
        return sock.connect_ex((host, int(port))) != 0
    except OSError:
        # Treat probe failure as unknown/occupied to fail closed for allocation
        return False
    finally:
        try:
            sock.close()
        except OSError:
            pass


def port_is_listening(
    port: int, host: str = DEFAULT_HOST, *, timeout_s: float = DEFAULT_TIMEOUT_S
) -> bool:
    """True if something accepts TCP connections on (host, port)."""
    return not port_is_free(port, host, timeout_s=timeout_s)


def probe_port(
    port: int,
    host: str = DEFAULT_HOST,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
) -> dict:
    """Return a structured probe result for doctor/allocator reports."""
    free = port_is_free(port, host, timeout_s=timeout_s)
    return {
        "port": int(port),
        "host": host,
        "free": free,
        "listening": not free,
        "timeout_s": timeout_s,
    }
