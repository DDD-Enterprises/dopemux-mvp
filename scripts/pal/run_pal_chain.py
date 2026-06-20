#!/usr/bin/env python3
"""Invoke PAL MCP tools via docker stdio and write proof/pal artifacts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTAINER = "pal-mcp-server"
DEFAULT_PYTHON = "/opt/venv/bin/python"
DEFAULT_SERVER = "/app/server.py"


def _mcp_call(tool: str, arguments: dict[str, Any], *, container: str, timeout: int) -> dict[str, Any]:
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "run-pal-chain", "version": "1.0"},
        },
    }
    notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    call_req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments},
    }
    payload = "\n".join(json.dumps(x) for x in (init_req, notif, call_req)) + "\n"
    cmd = ["docker", "exec", "-i", container, DEFAULT_PYTHON, DEFAULT_SERVER]
    proc = subprocess.run(
        cmd,
        input=payload,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"PAL docker exec failed rc={proc.returncode}: {proc.stderr[-2000:]}")
    # Last JSON line with matching result id
    candidates: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("id") == 2:
            candidates.append(obj)
    if not candidates:
        raise RuntimeError(f"No tool result in stdout: {proc.stdout[-4000:]}")
    last = candidates[-1]
    if "error" in last:
        raise RuntimeError(f"PAL tool error: {last['error']}")
    return last


def _extract_text(result: dict[str, Any]) -> str:
    content = result.get("result", {}).get("content", [])
    chunks: list[str] = []
    for item in content:
        if item.get("type") != "text":
            continue
        text = item.get("text", "")
        try:
            inner = json.loads(text)
            if isinstance(inner, dict) and "content" in inner:
                chunks.append(str(inner["content"]))
            else:
                chunks.append(text)
        except json.JSONDecodeError:
            chunks.append(text)
    return "\n\n".join(chunks).strip()


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one PAL tool and write a proof artifact")
    parser.add_argument("--tool", required=True, help="PAL tool name (analyze, challenge, ...)")
    parser.add_argument("--packet", required=True, help="Task packet id for proof path")
    parser.add_argument("--step", required=True, help="Artifact step label e.g. 01_ANALYZE")
    parser.add_argument("--prompt", required=True, help="Primary prompt/statement for the tool")
    parser.add_argument("--container", default=DEFAULT_CONTAINER)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--model", default="auto")
    parser.add_argument(
        "--files",
        default="",
        help="Comma-separated repo-relative paths for workflow tools requiring relevant_files",
    )
    args = parser.parse_args()

    rel_files = [p.strip() for p in args.files.split(",") if p.strip()]
    repo_files = [str((REPO_ROOT / p).resolve()) for p in rel_files]

    file_bundle = ""
    if rel_files:
        parts: list[str] = []
        for rel in rel_files:
            path = REPO_ROOT / rel
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if len(text) > 12000:
                text = text[:12000] + "\n... [truncated] ..."
            parts.append(f"### {rel}\n```\n{text}\n```")
        file_bundle = "\n\n".join(parts)

    enriched_prompt = args.prompt
    if file_bundle:
        enriched_prompt = f"{args.prompt}\n\n## Files for inspection\n\n{file_bundle}"

    tool_args: dict[str, Any] = {"model": args.model}
    if args.tool == "challenge":
        tool_args = {"prompt": args.prompt}
    elif args.tool == "version":
        tool_args = {}
    elif args.tool == "planner":
        tool_args = {
            "step": enriched_prompt,
            "step_number": 1,
            "total_steps": 1,
            "next_step_required": False,
            "model": args.model,
        }
    elif args.tool in {"analyze", "thinkdeep", "codereview", "precommit"}:
        if not repo_files:
            raise SystemExit(f"--files required for PAL tool '{args.tool}'")
        tool_args = {
            "step": enriched_prompt,
            "step_number": 1,
            "total_steps": 1,
            "next_step_required": False,
            "findings": enriched_prompt[:12000],
            "files_checked": repo_files,
            "relevant_files": repo_files,
            "relevant_context": [],
            "issues_found": [],
            "model": args.model,
        }
    else:
        tool_args = {
            "prompt": args.prompt,
            "step_number": 1,
            "total_steps": 1,
            "next_step_required": False,
            "model": args.model,
        }

    try:
        raw = _mcp_call(args.tool, tool_args, container=args.container, timeout=args.timeout)
        body = _extract_text(raw)
        status = "PASS"
        err = None
    except Exception as exc:  # noqa: BLE001
        body = f"PAL invocation failed: {exc}"
        status = "NOT_RUN"
        err = str(exc)

    out_dir = REPO_ROOT / "proof" / args.packet / "pal"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.step}.md"
    header = f"# {args.step} — PAL `{args.tool}`\n\n**Status**: {status}\n\n"
    if err:
        header += f"**Error**: {err}\n\n"
    header += f"**Prompt focus**:\n\n{args.prompt}\n\n---\n\n## PAL output\n\n"
    out_path.write_text(header + body + "\n", encoding="utf-8")
    print(f"wrote {out_path.relative_to(REPO_ROOT)} status={status}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())