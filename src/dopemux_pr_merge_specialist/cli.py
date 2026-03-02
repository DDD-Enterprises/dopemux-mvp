from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

from .schema import PRState, PRMergeReport, BlockerEvidence


def _run_id() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def _get_open_prs() -> List[Dict[str, Any]]:
    """Fetch open PRs using gh CLI."""
    cmd = [
        "gh", "pr", "list",
        "--json", "number,title,author,state,statusCheckRollup,mergeable,labels,reviewDecision,updatedAt",
        "--limit", "20"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error fetching PRs: {result.stderr}", file=sys.stderr)
        return []
    return json.loads(result.stdout)


def _map_to_state(raw: Dict[str, Any]) -> PRState:
    # Determine CI status
    checks = raw.get("statusCheckRollup", [])
    ci_status = "SUCCESS"
    if any(c.get("conclusion") == "FAILURE" for c in checks):
        ci_status = "FAILURE"
    elif any(c.get("status") == "IN_PROGRESS" for c in checks):
        ci_status = "PENDING"

    return PRState(
        pr_id=str(raw["number"]),
        title=raw["title"],
        author=raw["author"]["login"],
        state=raw["state"],
        ci_status=ci_status,
        mergeable=raw["mergeable"] == "MERGEABLE",
        labels=[l["name"] for l in raw.get("labels", [])],
        updated_at=raw["updatedAt"]
    )


def cmd_scan(args: argparse.Namespace) -> int:
    """Scan PR queue and prioritize."""
    print("🔍 Scanning GitHub PR queue...")
    raw_prs = _get_open_prs()
    states = [_map_to_state(r) for r in raw_prs]

    # Priority ranking
    # 1. SUCCESS + MERGEABLE + APPROVED
    # 2. FAILURE (obvious)
    # 3. CONFLICTS
    
    print(f"Found {len(states)} open PRs.\n")
    for s in states:
        status_icon = "✅" if s.ci_status == "SUCCESS" else "❌" if s.ci_status == "FAILURE" else "⏳"
        merge_icon = "🔗" if s.mergeable else "🚫"
        print(f"{s.pr_id:>4} | {status_icon} {merge_icon} | {s.author: <12} | {s.title[:50]}")
    
    return 0


def cmd_fix(args: argparse.Namespace) -> int:
    """Execute fix loop in isolated worktree."""
    pr_id = args.id
    run_id = _run_id()
    print(f"🚀 Starting fix loop for PR {pr_id} (Run: {run_id})")

    # 1. Fetch PR details to get branch
    cmd = ["gh", "pr", "view", pr_id, "--json", "headRefName"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error viewing PR: {res.stderr}", file=sys.stderr)
        return 1
    branch = json.loads(res.stdout)["headRefName"]

    # 2. Setup Worktree
    worktree_path = Path("/tmp") / f"dopemux-merge-{pr_id}-{run_id}"
    print(f"📂 Creating isolated worktree at {worktree_path}")
    
    subprocess.run(["git", "worktree", "add", str(worktree_path), branch], check=True)

    # 3. Create Proof Bundle
    out_dir = Path("proof/pr_merge") / f"PR-{pr_id}" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # 4. Trigger GitHub Specialist for CI analysis (Mocked for now)
    print(f"🔬 Analyzing CI failures for PR {pr_id}...")
    
    report = PRMergeReport(
        run_id=run_id,
        pr_id=pr_id,
        initial_state=PRState(pr_id=pr_id, title="...", author="...", state="...", ci_status="FAILURE", mergeable=True),
        status="merge_ready",
        status_reason="Worktree initialized. Ready for specialist intervention."
    )

    (out_dir / "RESULT.json").write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    
    print(f"✅ Specialist intervention staged. Worktree: {worktree_path}")
    print(f"💡 Run: cd {worktree_path} && dopemux-github run ...")
    
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
    try:
        sys.exit(args.func(args))
    except Exception as e:
        print(f"Unhandled error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
