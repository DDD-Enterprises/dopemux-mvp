#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_LABEL_POLICY = "OBSERVED,INFERRED,PROPOSED,UNKNOWN"
DEFAULT_MAX_QUERY_CHARS = 500
DEFAULT_MAX_EVIDENCE_BYTES = 200_000
SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b([A-Z0-9_]*(?:API_KEY|TOKEN|SECRET|PASSWORD|PRIVATE_KEY|CREDENTIAL)[A-Z0-9_]*)\s*=\s*([^\s]+)"
)
SECRET_VALUE_RE = re.compile(
    r"(sk-proj-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{32,}|tvly-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9_]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----)"
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run GPT Researcher in two phases: concise web query first, "
            "local evidence only in the report synthesis prompt."
        )
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Concise web research query. Do not pass local evidence here.",
    )
    parser.add_argument(
        "--evidence-file",
        action="append",
        default=[],
        help="Local evidence file to include in the report prompt.",
    )
    parser.add_argument(
        "--output-dir",
        default="",
        help="Output directory. Defaults to /tmp/dopemux-gptr-two-phase-<timestamp>.",
    )
    parser.add_argument("--report-type", default="deep")
    parser.add_argument("--report-source", default="web")
    parser.add_argument("--label-policy", default=DEFAULT_LABEL_POLICY)
    parser.add_argument(
        "--max-query-chars",
        type=int,
        default=DEFAULT_MAX_QUERY_CHARS,
        help="Fail closed when --query exceeds this length.",
    )
    parser.add_argument(
        "--max-evidence-bytes",
        type=int,
        default=DEFAULT_MAX_EVIDENCE_BYTES,
        help="Max bytes read from each evidence file.",
    )
    parser.add_argument(
        "--include-env-key",
        action="append",
        default=[],
        help="Record set/unset state for this env var without capturing values.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write report prompt and metadata without importing or invoking GPT Researcher.",
    )
    return parser.parse_args(argv)


def validate_research_query(query: str, *, max_chars: int = DEFAULT_MAX_QUERY_CHARS) -> None:
    normalized = query.strip()
    if not normalized:
        raise ValueError("research query is empty")
    if len(normalized) > max_chars:
        raise ValueError(
            f"research query is too long ({len(normalized)} chars > {max_chars}); "
            "pass local evidence with --evidence-file instead"
        )


def redact_secret_text(text: str) -> str:
    text = SECRET_ASSIGNMENT_RE.sub(r"\1=<redacted>", text)
    return SECRET_VALUE_RE.sub("<redacted>", text)


def read_evidence_file(path: Path | str, *, max_bytes: int = DEFAULT_MAX_EVIDENCE_BYTES) -> str:
    evidence_path = Path(path)
    raw = evidence_path.read_bytes()[:max_bytes]
    body = raw.decode("utf-8", errors="replace")
    redacted = redact_secret_text(body)
    header = f"## Evidence: {evidence_path}\n\n"
    if evidence_path.stat().st_size > max_bytes:
        redacted += f"\n\n[TRUNCATED after {max_bytes} bytes]\n"
    return header + redacted


def build_env_snapshot(names: Iterable[str]) -> dict[str, str]:
    return {name: "<set>" if name in os.environ else "<unset>" for name in names}


def build_report_prompt(args: argparse.Namespace) -> str:
    labels = ", ".join(label.strip() for label in args.label_policy.split(",") if label.strip())
    evidence_sections = [
        read_evidence_file(path, max_bytes=args.max_evidence_bytes)
        for path in args.evidence_file
    ]
    evidence_body = "\n\n---\n\n".join(evidence_sections) if evidence_sections else "No local evidence files were provided."
    return f"""Write a tailored recommendation report using the web research context plus the local evidence below.

Do not treat generic web advice as local repo truth.
Label every material claim as one of: {labels}.
Separate local evidence from external/current web evidence.
Never include secrets, tokens, raw credentials, private keys, or sensitive provider output.
Do not recommend write-capable connector actions without approval gates.
Preserve UNKNOWN where evidence is missing.

Local evidence:

{evidence_body}
"""


def default_output_dir() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path("/tmp") / f"dopemux-gptr-two-phase-{stamp}"


def write_text(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def write_json(path: Path, payload: dict[str, object]) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


async def run_gpt_researcher(args: argparse.Namespace, output_dir: Path, prompt: str) -> None:
    from gpt_researcher import GPTResearcher

    researcher = GPTResearcher(
        query=args.query.strip(),
        report_type=args.report_type,
        report_source=args.report_source,
    )
    await researcher.conduct_research()
    report = await researcher.write_report(custom_prompt=prompt)
    write_text(output_dir / "report.md", report)


def build_metadata(
    args: argparse.Namespace,
    *,
    output_dir: Path,
    status: str,
) -> dict[str, object]:
    return {
        "status": status,
        "query": redact_secret_text(args.query.strip()),
        "report_type": args.report_type,
        "report_source": args.report_source,
        "evidence_files": [redact_secret_text(str(Path(path))) for path in args.evidence_file],
        "env": build_env_snapshot(args.include_env_key),
        "output_dir": str(output_dir),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        validate_research_query(args.query, max_chars=args.max_query_chars)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    output_dir = Path(args.output_dir) if args.output_dir else default_output_dir()
    try:
        prompt = build_report_prompt(args)
        write_text(output_dir / "report_prompt.md", prompt)
    except Exception as exc:
        redacted_error = redact_secret_text(str(exc))
        write_json(
            output_dir / "run.json",
            {
                **build_metadata(args, output_dir=output_dir, status="fail"),
                "error_type": type(exc).__name__,
                "error": redacted_error,
            },
        )
        print(f"ERROR: {type(exc).__name__}: {redacted_error}", file=sys.stderr)
        return 1

    if args.dry_run:
        write_json(output_dir / "run.json", build_metadata(args, output_dir=output_dir, status="dry_run"))
        print(output_dir)
        return 0

    try:
        asyncio.run(run_gpt_researcher(args, output_dir, prompt))
    except Exception as exc:
        redacted_error = redact_secret_text(str(exc))
        write_json(
            output_dir / "run.json",
            {
                **build_metadata(args, output_dir=output_dir, status="fail"),
                "error_type": type(exc).__name__,
                "error": redacted_error,
            },
        )
        print(f"ERROR: {type(exc).__name__}: {redacted_error}", file=sys.stderr)
        return 1

    write_json(output_dir / "run.json", build_metadata(args, output_dir=output_dir, status="pass"))
    print(output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
