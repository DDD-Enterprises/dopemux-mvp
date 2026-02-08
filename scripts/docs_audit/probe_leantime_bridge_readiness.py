#!/usr/bin/env python3
"""
Probe Leantime bridge readiness from live containers and emit a strict-closure
evidence artifact.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, Tuple


def _run(cmd: list[str]) -> Tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def _json_or_text(text: str) -> Any:
    try:
        return json.loads(text)
    except Exception:
        return text


def _extract_fail_counts(log_text: str) -> Dict[str, int]:
    return {
        "emails_fail": len(re.findall(r"queue:emails\].*FAIL", log_text)),
        "httprequests_fail": len(re.findall(r"queue:httprequests\].*FAIL", log_text)),
        "default_fail": len(re.findall(r"queue:default\].*FAIL", log_text)),
        "get_index_303": len(re.findall(r'GET /index\.php" 303', log_text)),
        "post_index_303": len(re.findall(r'POST /index\.php" 303', log_text)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe Leantime bridge runtime readiness.")
    parser.add_argument(
        "--bridge-container",
        default="dopemux-mcp-leantime-bridge",
        help="Leantime bridge container name.",
    )
    parser.add_argument(
        "--leantime-container",
        default="leantime",
        help="Leantime app container name.",
    )
    parser.add_argument(
        "--output-json",
        default="reports/strict_closure/leantime_bridge_readiness_2026-02-07.json",
        help="Output artifact path.",
    )
    parser.add_argument(
        "--log-tail",
        type=int,
        default=120,
        help="Number of log lines to inspect for queue/redirect signals.",
    )
    args = parser.parse_args()

    # Bridge health probes from inside bridge container to avoid host networking variance.
    rc_health, out_health, err_health = _run(
        [
            "docker",
            "exec",
            args.bridge_container,
            "sh",
            "-lc",
            "curl -s http://127.0.0.1:3015/health",
        ]
    )
    rc_health_deep, out_health_deep, err_health_deep = _run(
        [
            "docker",
            "exec",
            args.bridge_container,
            "sh",
            "-lc",
            "curl -s 'http://127.0.0.1:3015/health?deep=1'",
        ]
    )
    rc_list_projects, out_list_projects, err_list_projects = _run(
        [
            "docker",
            "exec",
            args.bridge_container,
            "sh",
            "-lc",
            "curl -s -X POST http://127.0.0.1:3015/api/tools/list_projects "
            "-H 'Content-Type: application/json' -d '{}'",
        ]
    )

    rc_env, out_env, err_env = _run(
        [
            "docker",
            "exec",
            args.bridge_container,
            "sh",
            "-lc",
            "echo LEANTIME_API_URL=$LEANTIME_API_URL; "
            "if [ -n \"$LEANTIME_API_TOKEN\" ]; then "
            "echo LEANTIME_API_TOKEN=set; else echo LEANTIME_API_TOKEN=unset; fi",
        ]
    )

    rc_logs, out_logs, err_logs = _run(
        ["docker", "logs", f"--tail={args.log_tail}", args.leantime_container]
    )

    log_text = "\n".join(part for part in (out_logs, err_logs) if part)
    fail_counts = _extract_fail_counts(log_text)

    artifact: Dict[str, Any] = {
        "artifact": args.output_json,
        "generated_at_utc": "2026-02-07T00:00:00Z",
        "probe": {
            "bridge_container": args.bridge_container,
            "leantime_container": args.leantime_container,
            "health": {
                "return_code": rc_health,
                "output": _json_or_text(out_health),
                "stderr": err_health,
            },
            "health_deep": {
                "return_code": rc_health_deep,
                "output": _json_or_text(out_health_deep),
                "stderr": err_health_deep,
            },
            "list_projects": {
                "return_code": rc_list_projects,
                "output": _json_or_text(out_list_projects),
                "stderr": err_list_projects,
            },
            "bridge_env": {
                "return_code": rc_env,
                "raw_output": out_env,
                "stderr": err_env,
            },
            "leantime_log_tail": {
                "return_code": rc_logs,
                "stderr": err_logs,
                "stdout": out_logs,
                "fail_counts": fail_counts,
            },
        },
        "summary": {
            "bridge_liveness": "ok" if rc_health == 0 else "probe_failed",
            "deep_health_status": (
                _json_or_text(out_health_deep).get("status")
                if isinstance(_json_or_text(out_health_deep), dict)
                else "unknown"
            ),
            "list_projects_error": (
                (_json_or_text(out_list_projects) or {}).get("error")
                if isinstance(_json_or_text(out_list_projects), dict)
                else str(_json_or_text(out_list_projects))
            ),
            "token_status": "set" if "LEANTIME_API_TOKEN=set" in out_env else "unset",
            "setup_required_signal_present": (
                (
                    isinstance(_json_or_text(out_health_deep), dict)
                    and _json_or_text(out_health_deep).get("status") == "needs_setup"
                )
                or "/install" in str(_json_or_text(out_health_deep)).lower()
                or "/install" in str(_json_or_text(out_list_projects)).lower()
            ),
            "queue_fail_signal_present": (
                fail_counts["emails_fail"] > 0
                or fail_counts["httprequests_fail"] > 0
                or fail_counts["default_fail"] > 0
            ),
            "redirect_signal_present": (
                fail_counts["get_index_303"] > 0 or fail_counts["post_index_303"] > 0
            ),
        },
    }

    out_path = Path(args.output_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(json.dumps(artifact["summary"], indent=2))
    print(f"Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
