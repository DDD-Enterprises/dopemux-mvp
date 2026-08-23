from __future__ import annotations

import json
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from .models import PortfolioProjection

_PORTFOLIO_SCHEMA = (
    Path(__file__).parents[3]
    / "schemas"
    / "project_control_plane"
    / "repository_planner_portfolio.schema.json"
)


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    try:
        schema = json.loads(_PORTFOLIO_SCHEMA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("portfolio schema is unavailable") from exc
    return Draft202012Validator(schema, format_checker=FormatChecker())


def canonical_portfolio_bytes(portfolio: PortfolioProjection) -> bytes:
    """Serialize a portfolio as stable compact UTF-8 JSON with one final LF."""

    if portfolio.authority != "NONE":
        raise ValueError("portfolio authority must be NONE")
    if portfolio.surface_class != "PROJECTION":
        raise ValueError("portfolio surface_class must be PROJECTION")
    if portfolio.is_proof is not False:
        raise ValueError("portfolio is_proof must be false")

    PortfolioProjection(
        authority=portfolio.authority,
        surface_class=portfolio.surface_class,
        is_proof=portfolio.is_proof,
        sources=portfolio.sources,
        lanes=portfolio.lanes,
        conflicts=portfolio.conflicts,
        recommendations=portfolio.recommendations,
    )

    payload = {
        "schema_version": "pcp.repository_planner_portfolio.v1",
        **asdict(portfolio),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    json_payload = json.loads(encoded)
    errors = sorted(
        _validator().iter_errors(json_payload), key=lambda error: list(error.path)
    )
    if errors:
        raise ValueError(f"portfolio schema validation failed: {errors[0].message}")
    return (encoded + "\n").encode("utf-8")
