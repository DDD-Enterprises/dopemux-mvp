from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Optional

from .schema import Report
from .github.render import render_report_md
from .redaction import RedactionPolicy
from .errors import RedactionError, SchemaError
from .gemini.adapter import run_extraction_adapter


def _run_id() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def cmd_run(args: argparse.Namespace) -> int:
    run_id = _run_id()
    out_dir = Path(args.out_dir) / "github_specialist" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: Input file not found: {args.input}", file=sys.stderr)
            return 4
        
        try:
            input_bundle = json.loads(input_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in input file: {e}", file=sys.stderr)
            return 4

        try:
            report = run_extraction_adapter(
                input_bundle=input_bundle,
                run_id=run_id,
                out_dir=out_dir,
                gemini_command=args.gemini_command
            )
        except RedactionError as e:
            print(f"Blocked: Redaction policy triggered: {e}", file=sys.stderr)
            # Create a blocked report
            report = Report(
                run_id=run_id,
                scope=input_bundle.get("scope", "repo"),
                target=input_bundle.get("target", "unknown"),
                blocked=True,
                blocked_reason=str(e)
            )
        except (SchemaError, RuntimeError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 3
    else:
        # Stub run if no input provided
        report = Report(
            run_id=run_id,
            scope=args.scope or "repo",
            target=args.target or "unknown",
            top_k=3,
            actions=[],
            warnings=["Stub run: no input bundle provided. Use --input to run extraction."],
        )

    # Final rendering and persistence
    report_json = json.dumps(report.to_dict(), ensure_ascii=False, sort_keys=True, indent=2)
    report_md = render_report_md(report)

    (out_dir / "REPORT.json").write_text(report_json, encoding="utf-8")
    (out_dir / "REPORT.md").write_text(report_md, encoding="utf-8")
    
    if not report.blocked:
        print(f"Success: Report generated at {out_dir}")
        return 0
    else:
        print(f"Blocked: {report.blocked_reason}")
        return 2


def main() -> None:
    p = argparse.ArgumentParser(prog="dopemux-github")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("run", help="Run GitHub Specialist")
    s.add_argument("--scope", choices=["pr", "issue", "repo", "ci"], help="Scope of the run")
    s.add_argument("--target", help="Target identifier (e.g. PR#123)")
    s.add_argument("--input", help="Path to input JSON bundle")
    s.add_argument("--out-dir", default="proof", help="Output directory for proof artifacts")
    s.add_argument("--gemini-command", help="Optional override for Gemini CLI command")
    s.set_defaults(func=cmd_run)

    args = p.parse_args()
    try:
        sys.exit(args.func(args))
    except Exception as e:
        print(f"Unhandled error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
