from __future__ import annotations

import sqlite3
from typing import Any

from .resolve import duplicate_title_report


def build_collision_report(conn: sqlite3.Connection) -> dict[str, Any]:
    """Return duplicate-title collisions without promoting titles to identity."""
    return duplicate_title_report(conn)
