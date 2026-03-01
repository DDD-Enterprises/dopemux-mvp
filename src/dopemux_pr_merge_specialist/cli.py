from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from .schema import PRState, PRMergeReport


def _run_id() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def cmd_scan(args: argparse.Namespace) -> int:
    """Mock queue scanner."""
    print("Scanning PR queue...")
    print("Found 3 open PRs.")
    print("1. PR#125 (feat: neural search) - CI_FAIL")
    print("2. PR#126 (fix: typo) - CONFLICTS")
    print("3. PR#127 (docs: update readme) - READY")
    return 0


def cmd_fix(args: argparse.Namespace) -> int:
    """Mock PR fixer loop."""
    pr_id = args.id
    run_id = _run_id()
    print(f"Starting fix loop for PR {pr_id} (Run: {run_id})")

    out_dir = Path("proof/pr_merge") / f"PR-{pr_id}" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Mock state
    state = PRState(
        pr_id=pr_id,
        title="Sample PR",
        author="bot",
        state="open",
        ci_status="failure",
        mergeable=True,
        diffstat="+10 -2"
    )

    report = PRMergeReport(
        run_id=run_id,
        pr_id=pr_id,
        initial_state=state,
        status="blocked",
        status_reason="Stub implementation: needs GitHub API integration."
    )

    (out_dir / "INTAKE.json").write_text(json.dumps(state.__dict__, indent=2), encoding="utf-8")
    (out_dir / "RESULT.json").write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    (out_dir / "RESULT.md").write_text(f"# Result: {report.status}\n\n{report.status_reason}\n", encoding="utf-8")

    print(f"Proof bundle written to {out_dir}")
    return 0


def main() -> None:
    p = argparse.ArgumentParser(prog="dopemux-pr-merge")
    sub = p.add_subparsers(dest="cmd", required=True)

    s_scan = sub.add_parser("queue-scan", help="Scan the PR queue and rank by priority.")
    s_scan.set_defaults(func=cmd_scan)

    s_fix = sub.add_parser("pr-fix", help="Execute the fix loop for a specific PR.")
    s_fix.add_argument("--id", required=True, help="PR ID or number")
    s_fix.set_defaults(func=cmd_fix)

    args = p.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
