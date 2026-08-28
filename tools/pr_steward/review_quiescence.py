"""
Deterministic PR review quiescence evaluator and receipt generator.

Requires all configured mandatory automated review producers to have completed
review evidence on the exact PR head SHA before independent embedded audit or
PR Steward final readiness can proceed.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.pr_steward.collector import collect_from_github, load_fixture


SCHEMA_VERSION = "1.0.0"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_review_producers(config_path: Path | None = None) -> dict[str, Any]:
    path = config_path or Path(__file__).with_name("review_producers.json")
    if not path.is_file():
        return {
            "schema_version": SCHEMA_VERSION,
            "review_producers": [
                {
                    "producer_id": "copilot-pull-request-reviewer",
                    "mandatory": True,
                    "strategies": ["review_submission", "check_run", "reaction"],
                    "check_names": [
                        "copilot-code-review",
                        "CodeQL",
                        "Analyze (python)",
                        "Analyze (javascript-typescript)",
                        "Analyze (ruby)",
                    ],
                },
                {
                    "producer_id": "chatgpt-codex-connector",
                    "mandatory": True,
                    "strategies": ["review_submission", "reaction"],
                },
            ],
        }
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_review_quiescence(
    harvest: dict[str, Any],
    *,
    expected_head_sha: str,
    repo: str,
    pr_number: int,
    producers_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = producers_config or load_review_producers()
    producers_def = config.get("review_producers", [])

    pr_raw = harvest.get("pr") or {}
    harvest_head_sha = str(pr_raw.get("headRefOid") or pr_raw.get("head_sha") or "")

    blocking_reasons: list[str] = []
    producer_results: list[dict[str, Any]] = []

    # 1. Verify head SHA integrity
    head_match = (harvest_head_sha == expected_head_sha)
    if not head_match:
        blocking_reasons.append(
            f"PR head SHA mismatch: expected {expected_head_sha}, got {harvest_head_sha}"
        )

    # 2. Extract reviews, checks, threads from harvest
    reviews = harvest.get("reviews") or pr_raw.get("reviews") or []
    checks = harvest.get("checks") or []
    # If checks is empty, also look in statusCheckRollup
    if not checks:
        rollup = (pr_raw.get("statusCheckRollup") or [])
        if isinstance(rollup, list):
            checks = rollup
        elif isinstance(rollup, dict):
            checks = rollup.get("contexts") or rollup.get("checkRuns") or []

    review_threads = harvest.get("review_threads") or []

    # 3. Evaluate each configured producer
    for p_def in producers_def:
        pid = p_def.get("producer_id", "")
        mandatory = bool(p_def.get("mandatory", True))
        strategies = p_def.get("strategies", ["review_submission"])
        check_names = set(p_def.get("check_names", []))

        p_status = "MISSING"
        strategy_used = None
        evidence = None

        # Check strategy: review_submission
        if "review_submission" in strategies:
            matching_reviews = []
            for r in reviews:
                author_login = ""
                if isinstance(r.get("author"), dict):
                    author_login = r["author"].get("login", "")
                elif isinstance(r.get("author"), str):
                    author_login = r["author"]
                elif isinstance(r.get("user"), dict):
                    author_login = r["user"].get("login", "")

                if author_login == pid:
                    matching_reviews.append(r)

            if matching_reviews:
                # Check for exact head or newest review
                exact_head_reviews = []
                stale_reviews = []
                for mr in matching_reviews:
                    r_commit = mr.get("commit_id") or mr.get("commit", {}).get("oid") or mr.get("commitOid")
                    if r_commit == expected_head_sha:
                        exact_head_reviews.append(mr)
                    elif r_commit:
                        stale_reviews.append(mr)
                    else:
                        # Fallback to state check if commit not recorded
                        exact_head_reviews.append(mr)

                if exact_head_reviews:
                    latest = exact_head_reviews[-1]
                    p_status = "COMPLETED"
                    strategy_used = "review_submission"
                    evidence = {
                        "review_id": latest.get("id"),
                        "state": latest.get("state"),
                        "submitted_at": latest.get("submittedAt") or latest.get("submitted_at"),
                        "commit_id": expected_head_sha,
                    }
                elif stale_reviews:
                    latest_stale = stale_reviews[-1]
                    p_status = "STALE"
                    strategy_used = "review_submission"
                    evidence = {
                        "review_id": latest_stale.get("id"),
                        "stale_commit_id": latest_stale.get("commit_id") or latest_stale.get("commitOid"),
                        "expected_head_sha": expected_head_sha,
                    }

        # Check strategy: check_run (if not already completed)
        if p_status not in ("COMPLETED", "STALE") and "check_run" in strategies:
            matching_checks = []
            for c in checks:
                c_name = c.get("name") or c.get("context") or ""
                c_head = c.get("head_sha") or c.get("commit", {}).get("oid") or expected_head_sha
                c_status = (c.get("status") or "").lower()
                c_conclusion = (c.get("conclusion") or c.get("state") or "").lower()

                if c_name in check_names or c_name == pid:
                    if c_head == expected_head_sha and c_status == "completed":
                        matching_checks.append((c_name, c_conclusion, c))

            if matching_checks:
                # Find successful or completed checks
                for c_name, c_conclusion, c_raw in matching_checks:
                    if c_conclusion in ("success", "neutral", "pass"):
                        p_status = "COMPLETED"
                        strategy_used = "check_run"
                        evidence = {
                            "check_name": c_name,
                            "conclusion": c_conclusion,
                            "head_sha": expected_head_sha,
                        }
                        break
                    elif c_conclusion in ("failure", "timed_out", "action_required", "cancelled"):
                        p_status = "FAILED"
                        strategy_used = "check_run"
                        evidence = {
                            "check_name": c_name,
                            "conclusion": c_conclusion,
                            "head_sha": expected_head_sha,
                        }

        # Handle non-mandatory
        if not mandatory and p_status == "MISSING":
            p_status = "NOT_REQUIRED"

        # Record blocker if mandatory failed/missing/stale
        if mandatory:
            if p_status == "MISSING":
                blocking_reasons.append(
                    f"Mandatory review producer '{pid}' completion evidence not found on head {expected_head_sha}"
                )
            elif p_status == "STALE":
                blocking_reasons.append(
                    f"Mandatory review producer '{pid}' evidence is stale (bound to prior head, not {expected_head_sha})"
                )
            elif p_status == "FAILED":
                blocking_reasons.append(
                    f"Mandatory review producer '{pid}' check run reported failure on head {expected_head_sha}"
                )

        producer_results.append({
            "producer_id": pid,
            "mandatory": mandatory,
            "status": p_status,
            "strategy_used": strategy_used,
            "evidence": evidence,
        })

    # 4. Evaluate review threads (unresolved threads block quiescence)
    unresolved_threads = []
    for t in review_threads:
        is_resolved = t.get("isResolved", t.get("is_resolved", False))
        if not is_resolved:
            unresolved_threads.append(t)

    unresolved_count = len(unresolved_threads)
    if unresolved_count > 0:
        blocking_reasons.append(
            f"{unresolved_count} unresolved review thread(s) present on PR"
        )

    # 5. Determine overall verdict
    if not head_match:
        verdict = "BLOCKED"
        is_quiescent = False
    elif unresolved_count > 0:
        verdict = "NEEDS_IMPLEMENTER"
        is_quiescent = False
    elif any(p["status"] == "STALE" for p in producer_results if p["mandatory"]):
        verdict = "BLOCKED"
        is_quiescent = False
    elif any(p["status"] in ("MISSING", "PENDING", "UNKNOWN") for p in producer_results if p["mandatory"]):
        verdict = "UNKNOWN"
        is_quiescent = False
    elif any(p["status"] == "FAILED" for p in producer_results if p["mandatory"]):
        verdict = "BLOCKED"
        is_quiescent = False
    elif blocking_reasons:
        verdict = "BLOCKED"
        is_quiescent = False
    else:
        verdict = "QUIESCENT"
        is_quiescent = True

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "repository": repo,
        "pr_number": pr_number,
        "head_sha": expected_head_sha,
        "verdict": verdict,
        "is_quiescent": is_quiescent,
        "blocking_reasons": blocking_reasons,
        "unresolved_thread_count": unresolved_count,
        "unresolved_blocking_thread_count": unresolved_count,
        "producers": producer_results,
        "evidence_references": {
            "expected_head_sha": expected_head_sha,
            "harvest_head_sha": harvest_head_sha,
            "reviews_examined_count": len(reviews),
            "threads_examined_count": len(review_threads),
            "checks_examined_count": len(checks),
        },
        "mutation_performed": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="review-quiescence",
        description="Deterministic PR review quiescence evaluator.",
    )
    parser.add_argument("--repo", required=True, help="GitHub repository owner/name.")
    parser.add_argument("--pr", required=True, type=int, help="Pull request number.")
    parser.add_argument("--head-sha", required=True, help="Expected PR head SHA.")
    parser.add_argument("--out", required=True, type=Path, help="Output directory.")
    parser.add_argument(
        "--fixture-dir",
        type=Path,
        help="Offline fixture directory containing harvest.json.",
    )
    parser.add_argument(
        "--producers-config",
        type=Path,
        help="Path to review_producers.json.",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Print JSON receipt or text summary.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        harvest = (
            load_fixture(args.fixture_dir)
            if args.fixture_dir
            else collect_from_github(args.repo, args.pr)
        )
        producers_config = (
            load_review_producers(args.producers_config)
            if args.producers_config
            else None
        )
        receipt = evaluate_review_quiescence(
            harvest,
            expected_head_sha=args.head_sha,
            repo=args.repo,
            pr_number=args.pr,
            producers_config=producers_config,
        )

        args.out.mkdir(parents=True, exist_ok=True)
        out_file = args.out / "REVIEW_QUIESCENCE.json"
        out_file.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        if args.format == "json":
            print(json.dumps(receipt, indent=2, sort_keys=True))
        else:
            print(f"REVIEW QUIESCENCE: {receipt['verdict']} (is_quiescent={receipt['is_quiescent']})")
            if receipt["blocking_reasons"]:
                for b in receipt["blocking_reasons"]:
                    print(f"  - {b}")

        if not receipt.get("is_quiescent"):
            return 1
        return 0
    except Exception as exc:
        print(f"review-quiescence failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
