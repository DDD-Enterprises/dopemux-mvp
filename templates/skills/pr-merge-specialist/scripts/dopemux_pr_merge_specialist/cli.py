from __future__ import annotations

import argparse

from . import engine


def _run_with_execute_preflight(args: argparse.Namespace, target) -> int:
    if getattr(args, "execute", False):
        preflight_rc = engine.preflight(args)
        if preflight_rc != 0:
            return preflight_rc
    return target(args)


def _pr_fix(args: argparse.Namespace) -> int:
    print("Deprecated: `pr-fix` now maps to `pr-plan` and, with `--execute`, `pr-apply`. It never performs `pr-merge`.")
    plan_rc = engine.pr_plan(args)
    if plan_rc != 0 or not getattr(args, "execute", False):
        return plan_rc
    return _run_with_execute_preflight(args, engine.pr_apply)


def _preflight_then_apply(args: argparse.Namespace) -> int:
    return _run_with_execute_preflight(args, engine.pr_apply)


def _preflight_then_merge(args: argparse.Namespace) -> int:
    return _run_with_execute_preflight(args, engine.pr_merge)


def _preflight_then_queue_drain(args: argparse.Namespace) -> int:
    return _run_with_execute_preflight(args, engine.queue_drain)


# Compatibility exports for existing callers/tests that import helpers from cli.
_classify_pr = engine.classify_pr
_risk_score = engine.risk_score
_sort_states = engine.sort_states
_decide_thread_disposition = engine.decide_thread_disposition
_build_conflict_analysis = engine.build_conflict_analysis
_run_merge_with_fallback = engine.run_merge_with_fallback
_queue_scan = engine.queue_scan
_queue_drain = engine.queue_drain


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dopemux-pr-merge")
    parser.add_argument("--policy", help="Optional path to a policy YAML file.")
    parser.add_argument("--repo", help="Optional OWNER/REPO override.")
    parser.add_argument("--out-dir", default="proof/pr_merge", help="Artifact output directory.")
    parser.add_argument("--allow-dirty", action="store_true", help="Allow execute-mode runs from a dirty repo root.")
    parser.add_argument("--run-id", help="Override run id (primarily for resume/testing).")

    def add_common_arguments(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--policy", help="Optional path to a policy YAML file.")
        subparser.add_argument("--repo", help="Optional OWNER/REPO override.")
        subparser.add_argument("--out-dir", default="proof/pr_merge", help="Artifact output directory.")
        subparser.add_argument("--allow-dirty", action="store_true", help="Allow execute-mode runs from a dirty repo root.")
        subparser.add_argument("--run-id", help="Override run id (primarily for resume/testing).")

    sub = parser.add_subparsers(dest="cmd", required=True)

    preflight = sub.add_parser("preflight", help="Run environment and policy checks without mutating the repo.")
    add_common_arguments(preflight)
    preflight.set_defaults(func=engine.preflight)

    queue_scan = sub.add_parser("queue-scan", help="Inspect the open PR queue and compute ordering/artifacts.")
    add_common_arguments(queue_scan)
    queue_scan.add_argument("--limit", type=int, default=50, help="Max open PRs to inspect.")
    queue_scan.add_argument("--strategy", choices=["simple", "hybrid"], default="hybrid")
    queue_scan.add_argument("--prioritize", action="append", default=[], help="Comma-separated PR ids to move to the front.")
    queue_scan.add_argument("--only", action="append", default=[], help="Comma-separated PR ids to include exclusively.")
    queue_scan.set_defaults(func=engine.queue_scan)

    pr_plan = sub.add_parser("pr-plan", help="Produce a decision-complete, non-mutating plan for one PR.")
    add_common_arguments(pr_plan)
    pr_plan.add_argument("--id", required=True, type=int, help="Pull request number.")
    pr_plan.set_defaults(func=engine.pr_plan)

    pr_apply = sub.add_parser("pr-apply", help="Refresh/rebase/apply safe fixes for one PR without merging it.")
    add_common_arguments(pr_apply)
    pr_apply.add_argument("--id", required=True, type=int, help="Pull request number.")
    pr_apply.add_argument("--execute", action="store_true", help="Actually mutate local/remote PR state.")
    pr_apply.set_defaults(func=_preflight_then_apply)

    pr_merge = sub.add_parser("pr-merge", help="Revalidate and merge one PR if all gates are green.")
    add_common_arguments(pr_merge)
    pr_merge.add_argument("--id", required=True, type=int, help="Pull request number.")
    pr_merge.add_argument("--execute", action="store_true", help="Actually mutate remote PR state.")
    pr_merge.set_defaults(func=_preflight_then_merge)

    queue_drain = sub.add_parser("queue-drain", help="Orchestrate queue-scan, plan, apply, and merge across the queue.")
    add_common_arguments(queue_drain)
    queue_drain.add_argument("--execute", action="store_true", help="Actually mutate local/remote PR state.")
    queue_drain.add_argument("--limit", type=int, default=50, help="Max open PRs to inspect.")
    queue_drain.add_argument("--max-prs", type=int, default=0, help="Maximum PRs to process; 0 drains all discovered PRs.")
    queue_drain.add_argument("--max-passes", type=int, default=3, help="Maximum queue passes before stopping.")
    queue_drain.add_argument("--strategy", choices=["simple", "hybrid"], default="hybrid")
    queue_drain.add_argument("--prioritize", action="append", default=[], help="Comma-separated PR ids to move to the front.")
    queue_drain.add_argument("--only", action="append", default=[], help="Comma-separated PR ids to include exclusively.")
    queue_drain.set_defaults(func=_preflight_then_queue_drain)

    pr_fix = sub.add_parser("pr-fix", help="Deprecated compatibility wrapper around pr-plan and pr-apply for a single PR.")
    add_common_arguments(pr_fix)
    pr_fix.add_argument("--id", required=True, type=int, help="Pull request number to process.")
    pr_fix.add_argument("--execute", action="store_true", help="Actually mutate local/remote PR state.")
    pr_fix.set_defaults(func=_pr_fix)

    self_check = sub.add_parser("self-check", help="Verify the package layout, policy bundle, and installed smoke contract.")
    add_common_arguments(self_check)
    self_check.set_defaults(func=engine.preflight)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
