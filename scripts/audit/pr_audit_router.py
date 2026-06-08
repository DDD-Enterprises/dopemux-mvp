"""PR-level multi-model audit router with risk classification.

Classifies a pull-request diff by risk level (LOW / MEDIUM / HIGH) and maps
each level to an ordered set of auditor routes.  Dry-run by default — no live
API calls are made unless ``--live`` is passed explicitly.

Usage:
    python -m scripts.audit.pr_audit_router \\
        --files-changed 4 --lines-added 120 --lines-deleted 30 \\
        --out /tmp/audit-proof --packet-id TP-DMX-PR-AUDIT-ROUTER-001

    # Live run (requires auditor CLIs on PATH):
    python -m scripts.audit.pr_audit_router --live ...
"""

from __future__ import annotations

import argparse
import enum
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from scripts.audit.auditor_router import (
    _CLINK_CONF_DIR,
    default_routes,
    load_route_from_clink_config,
    probe_capability,
)
from scripts.audit.route_schema import AuditRoute

# ---------------------------------------------------------------------------
# Risk classification
# ---------------------------------------------------------------------------

class PrRiskClass(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass(frozen=True)
class PrDiffStats:
    files_changed: int
    lines_added: int
    lines_deleted: int
    touches_schema: bool = False
    touches_migration: bool = False
    touches_secrets_config: bool = False


def classify_pr_risk(diff_stats: PrDiffStats) -> PrRiskClass:
    """Return risk class for a PR based on its diff statistics.

    Rules (evaluated top-to-bottom; first match wins):
    - Any migration or secrets-config touch → HIGH
    - Schema touch → MEDIUM
    - Large diff (>500 net lines or >20 files) → MEDIUM
    - Otherwise → LOW
    """
    if diff_stats.touches_migration or diff_stats.touches_secrets_config:
        return PrRiskClass.HIGH
    if diff_stats.touches_schema:
        return PrRiskClass.MEDIUM
    net_lines = diff_stats.lines_added + diff_stats.lines_deleted
    if net_lines > 500 or diff_stats.files_changed > 20:
        return PrRiskClass.MEDIUM
    return PrRiskClass.LOW


# ---------------------------------------------------------------------------
# Risk → route-name tier mapping
#
# Invariant: free OpenRouter model lists are advisory only — this table maps
# to *named routes* (resolved from clink configs), not to free-tier model IDs.
# xAI/Grok appears in HIGH tier but blocks only when configured as blocking.
# ---------------------------------------------------------------------------

_RISK_TIER_ROUTES: dict[PrRiskClass, tuple[str, ...]] = {
    PrRiskClass.LOW: ("claude-audit",),
    PrRiskClass.MEDIUM: ("claude-audit", "gemini-audit"),
    PrRiskClass.HIGH: ("claude-audit", "gemini-audit", "xai-grok-audit"),
}

# Names that may be loaded from clink config but are treated as non-blocking
# (they add coverage but do not gate the audit result when unavailable).
_NON_BLOCKING_ROUTE_NAMES: frozenset[str] = frozenset({"xai-grok-audit", "openrouter-audit"})


# ---------------------------------------------------------------------------
# Audit plan
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RouteResolution:
    cli_name: str
    available: bool
    blocking: bool


@dataclass(frozen=True)
class MultiModelAuditPlan:
    risk_class: PrRiskClass
    requested_route_names: tuple[str, ...]
    resolutions: tuple[RouteResolution, ...]
    dry_run: bool

    def blocking_available_count(self) -> int:
        return sum(1 for r in self.resolutions if r.available and r.blocking)

    def has_any_available(self) -> bool:
        return any(r.available for r in self.resolutions)


def _load_extra_routes(conf_dir: Path, names: tuple[str, ...]) -> dict[str, AuditRoute]:
    """Load named clink configs that are not in the default route set."""
    routes: dict[str, AuditRoute] = {}
    for name in names:
        cfg = conf_dir / f"{name}.json"
        if not cfg.exists():
            continue
        try:
            route = load_route_from_clink_config(cfg, priority=99)
            routes[route.cli_name] = route
        except (KeyError, ValueError):
            pass
    return routes


def build_audit_plan(
    diff_stats: PrDiffStats,
    *,
    conf_dir: Path = _CLINK_CONF_DIR,
    dry_run: bool = True,
) -> MultiModelAuditPlan:
    """Build a multi-model audit plan for a PR.

    When ``dry_run=True`` (the default), route availability is still probed
    against the host PATH so the proof captures what *would* have run, but no
    audit is executed.
    """
    risk = classify_pr_risk(diff_stats)
    requested = _RISK_TIER_ROUTES[risk]

    # Assemble route registry: default routes + any extras needed for this tier.
    default_route_list = default_routes(conf_dir=conf_dir)
    default_by_name: dict[str, AuditRoute] = {r.cli_name: r for r in default_route_list}
    extra_names = tuple(n for n in requested if n not in default_by_name)
    extra_by_name = _load_extra_routes(conf_dir, extra_names)
    all_routes: dict[str, AuditRoute] = {**default_by_name, **extra_by_name}

    resolutions: list[RouteResolution] = []
    for name in requested:
        route = all_routes.get(name)
        available = route is not None and probe_capability(route)
        blocking = name not in _NON_BLOCKING_ROUTE_NAMES
        resolutions.append(RouteResolution(cli_name=name, available=available, blocking=blocking))

    return MultiModelAuditPlan(
        risk_class=risk,
        requested_route_names=requested,
        resolutions=tuple(resolutions),
        dry_run=dry_run,
    )


# ---------------------------------------------------------------------------
# Proof artifact
# ---------------------------------------------------------------------------

def _build_proof(
    plan: MultiModelAuditPlan,
    *,
    packet_id: str,
    git_sha: Optional[str],
) -> dict:
    return {
        "schema_version": "1.0",
        "packet_id": packet_id,
        "git_sha": git_sha or os.environ.get("GIT_SHA") or "UNKNOWN",
        "dry_run": plan.dry_run,
        "risk_class": plan.risk_class.value,
        "requested_route_names": list(plan.requested_route_names),
        "resolutions": [
            {
                "cli_name": r.cli_name,
                "available": r.available,
                "blocking": r.blocking,
            }
            for r in plan.resolutions
        ],
        "blocking_available_count": plan.blocking_available_count(),
        "has_any_available": plan.has_any_available(),
        "executed": False,
        "execution_results": [],
    }


def _validate_proof(proof: dict) -> None:
    """Fail closed if the proof is missing required fields.

    A schema validator (jsonschema) would be preferable in a full run, but the
    router skeleton performs mandatory-field presence checking to satisfy the
    fail-closed invariant without an optional dependency.
    """
    required = {
        "schema_version", "packet_id", "git_sha", "dry_run",
        "risk_class", "requested_route_names", "resolutions",
        "blocking_available_count", "has_any_available",
        "executed", "execution_results",
    }
    missing = required - proof.keys()
    if missing:
        raise ValueError(f"Proof artifact is schema-invalid — missing fields: {sorted(missing)}")
    if proof["risk_class"] not in {c.value for c in PrRiskClass}:
        raise ValueError(f"Proof artifact has invalid risk_class: {proof['risk_class']!r}")


def write_proof_artifact(
    plan: MultiModelAuditPlan,
    *,
    out: Path,
    packet_id: str,
    git_sha: Optional[str] = None,
) -> Path:
    """Write proof artifact, failing closed if field validation fails.

    ``out`` may be either a directory (writes ``MULTI_MODEL_PR_AUDIT.json``
    into it) or a ``.json`` file path (writes directly to that path).
    """
    proof = _build_proof(plan, packet_id=packet_id, git_sha=git_sha)
    _validate_proof(proof)
    if out.suffix == ".json":
        out.parent.mkdir(parents=True, exist_ok=True)
        out_path = out
    else:
        out.mkdir(parents=True, exist_ok=True)
        out_path = out / "MULTI_MODEL_PR_AUDIT.json"
    out_path.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pr-audit-router",
        description="PR risk classifier and multi-model audit router.",
    )
    p.add_argument("--files-changed", type=int, default=0)
    p.add_argument("--lines-added", type=int, default=0)
    p.add_argument("--lines-deleted", type=int, default=0)
    p.add_argument("--touches-schema", action="store_true")
    p.add_argument("--touches-migration", action="store_true")
    p.add_argument("--touches-secrets-config", action="store_true")
    p.add_argument(
        "--packet-id",
        default=os.environ.get("PACKET_ID", "UNKNOWN"),
        help="Task packet identifier for proof chain.",
    )
    p.add_argument("--git-sha", default=None)
    p.add_argument(
        "--out",
        required=True,
        type=Path,
        help="Output directory or .json file path for proof artifact.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Do not execute live audits (default; opposite of --live).",
    )
    p.add_argument(
        "--live",
        action="store_true",
        help="Execute audits against live routes (overrides --dry-run).",
    )
    p.add_argument("--conf-dir", type=Path, default=None, help="Override clink config directory.")
    p.add_argument("--format", choices=["json", "text"], default="text")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    conf_dir = args.conf_dir if args.conf_dir else _CLINK_CONF_DIR
    diff_stats = PrDiffStats(
        files_changed=args.files_changed,
        lines_added=args.lines_added,
        lines_deleted=args.lines_deleted,
        touches_schema=args.touches_schema,
        touches_migration=args.touches_migration,
        touches_secrets_config=args.touches_secrets_config,
    )

    try:
        plan = build_audit_plan(
            diff_stats,
            conf_dir=conf_dir,
            dry_run=not args.live,
        )
        proof_path = write_proof_artifact(
            plan,
            out=args.out,
            packet_id=args.packet_id,
            git_sha=args.git_sha,
        )
    except Exception as exc:
        print(f"pr-audit-router failed: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(proof_path.read_text(encoding="utf-8"))
    else:
        avail = [r.cli_name for r in plan.resolutions if r.available]
        print(
            f"risk={plan.risk_class.value} dry_run={plan.dry_run} "
            f"available={avail or '(none)'} proof={proof_path}"
        )

    return 0 if plan.has_any_available() else 2


if __name__ == "__main__":
    raise SystemExit(main())
