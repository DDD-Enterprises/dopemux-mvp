from __future__ import annotations

import json
from dataclasses import asdict

from .models import PortfolioProjection


def canonical_portfolio_bytes(portfolio: PortfolioProjection) -> bytes:
    """Serialize a portfolio as stable compact UTF-8 JSON with one final LF."""

    payload = {
        "schema_version": "pcp.repository_planner_portfolio.v1",
        **asdict(portfolio),
    }
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
