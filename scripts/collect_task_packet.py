#!/usr/bin/env python3
"""Collect multi-layer debugging artifacts into a portable investigation packet."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import tarfile
import textwrap
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dopemux.logging import bind_task_packet, configure_logging
from dopemux.logging.packet import (
    build_datadog_series,
    build_prometheus_export,
    log_line_to_json_record,
    summarize_service_lines,
)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Collect compose/local logs, health snapshots, and metrics into a "
            "task-scoped debug packet."
        )
    )
    parser.add_argument(
        "--task-id",
        default="investigation",
        help="Task identifier used in packet naming and metadata.",
    )
    parser.add_argument(
        "--since",
        default="2h",
        help="Compose log window passed to `docker compose logs --since`.",
    )
    parser.add_argument(
        "--tail",
        type=int,
        default=4000,
        help="Max log lines per compose service.",
    )
    parser.add_argument(
        "--services",
        default="all",
        help="Comma-separated compose service names. Use `all` for every service.",
    )
    parser.add_argument(
        "--compose-file",
        default="compose.yml",
        help="Compose file relative to repository root.",
    )
    parser.add_argument(
        "--registry-file",
        default="services/registry.yaml",
        help="Service registry YAML for health/metrics lookups.",
    )
    parser.add_argument(
        "--output-root",
        default="reports/task-packets",
        help="Directory where packet folders and archives are written.",
    )
    parser.add_argument(
        "--local-tail",
        type=int,
        default=1500,
        help="Max lines to capture from each local log file under ./logs.",
    )
    parser.add_argument(
        "--max-local-files",
        type=int,
        default=40,
        help="Max number of local files under ./logs to include.",
    )
    parser.add_argument(
        "--emit-datadog",
        action="store_true",
        help="Send packet summary metrics to Datadog v2 API if API key is set.",
    )
    parser.add_argument(
        "--datadog-site",
        default="datadoghq.com",
        help="Datadog site suffix, e.g. datadoghq.com or datadoghq.eu.",
    )
    parser.add_argument(
        "--no-archive",
        action="store_true",
        help="Skip creating .tar.gz archive for the packet folder.",
    )
    return parser.parse_args(argv)


def run_command(
    args: Sequence[str],
    *,
    cwd: Path,
    timeout: int = 90,
) -> Dict[str, Any]:
    start = time.time()
    try:
        result = subprocess.run(
            list(args),
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration_ms": int((time.time() - start) * 1000),
            "command": list(args),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "returncode": -1,
            "stdout": exc.stdout or "",
            "stderr": f"Command timed out after {timeout}s",
            "duration_ms": int((time.time() - start) * 1000),
            "command": list(args),
        }
    except FileNotFoundError as exc:
        return {
            "ok": False,
            "returncode": -1,
            "stdout": "",
            "stderr": str(exc),
            "duration_ms": int((time.time() - start) * 1000),
            "command": list(args),
        }


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True))


def resolve_compose_command(cwd: Path) -> Optional[List[str]]:
    if shutil.which("docker-compose"):
        return ["docker-compose"]
    if shutil.which("docker"):
        probe = run_command(["docker", "compose", "version"], cwd=cwd, timeout=15)
        if probe["ok"]:
            return ["docker", "compose"]
    return None


def compose_command(
    compose_bin: Sequence[str],
    compose_file: Path,
    *args: str,
) -> List[str]:
    return [*compose_bin, "-f", str(compose_file), *args]


def parse_services_arg(raw: str) -> Optional[List[str]]:
    value = raw.strip()
    if value.lower() == "all":
        return None
    services = [item.strip() for item in value.split(",") if item.strip()]
    return services or None


def read_registry(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    content = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return list(content.get("services", []))


def parse_compose_host_ports(compose_file: Path) -> Dict[str, int]:
    """Extract first published host port per service from compose YAML."""
    if not compose_file.exists():
        return {}

    content = yaml.safe_load(compose_file.read_text(encoding="utf-8")) or {}
    services = content.get("services", {}) or {}
    host_ports: Dict[str, int] = {}

    for service_name, service_def in services.items():
        ports = service_def.get("ports", []) or []
        for port_spec in ports:
            published: Optional[int] = None
            if isinstance(port_spec, int):
                published = int(port_spec)
            elif isinstance(port_spec, str):
                left = port_spec.split(":")[0].strip().strip('"').strip("'")
                # Handle host_ip:host_port:container_port.
                if left.count(".") == 3 and ":" in port_spec:
                    parts = port_spec.split(":")
                    if len(parts) >= 2:
                        left = parts[-2].strip()
                if left.isdigit():
                    published = int(left)
            elif isinstance(port_spec, dict):
                if "published" in port_spec:
                    try:
                        published = int(str(port_spec["published"]))
                    except (TypeError, ValueError):
                        published = None

            if published is not None:
                host_ports[service_name] = published
                break

    return host_ports


def select_services(
    compose_services: List[str],
    requested: Optional[List[str]],
) -> List[str]:
    if requested is None:
        return compose_services
    lookup = set(compose_services)
    selected = [service for service in requested if service in lookup]
    missing = [service for service in requested if service not in lookup]
    if missing:
        print(
            "warning: requested services not found in compose output: "
            + ", ".join(missing),
            file=sys.stderr,
        )
    return selected


def fetch_url(url: str, timeout: float = 5.0) -> Dict[str, Any]:
    request = Request(url, method="GET")
    started = time.time()
    try:
        with urlopen(request, timeout=timeout) as response:
            body_bytes = response.read()
            body = body_bytes.decode("utf-8", errors="replace")
            return {
                "ok": 200 <= response.status < 400,
                "status": response.status,
                "body": body,
                "duration_ms": int((time.time() - started) * 1000),
                "url": url,
            }
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {
            "ok": False,
            "status": exc.code,
            "body": body,
            "error": str(exc),
            "duration_ms": int((time.time() - started) * 1000),
            "url": url,
        }
    except URLError as exc:
        return {
            "ok": False,
            "status": None,
            "body": "",
            "error": str(exc),
            "duration_ms": int((time.time() - started) * 1000),
            "url": url,
        }
    except Exception as exc:  # pragma: no cover - transport edge cases
        return {
            "ok": False,
            "status": None,
            "body": "",
            "error": str(exc),
            "duration_ms": int((time.time() - started) * 1000),
            "url": url,
        }


def tail_text_file(path: Path, max_lines: int) -> str:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        return "".join(deque(handle, maxlen=max_lines))


def collect_local_logs(
    packet_dir: Path,
    max_files: int,
    max_lines: int,
) -> List[Dict[str, Any]]:
    source_dir = REPO_ROOT / "logs"
    destination = packet_dir / "local-logs"
    destination.mkdir(parents=True, exist_ok=True)

    if not source_dir.exists():
        return []

    candidates = sorted(
        path
        for path in source_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in {".log", ".json", ".jsonl", ".txt"}
    )
    collected: List[Dict[str, Any]] = []
    for path in candidates[:max_files]:
        relative = path.relative_to(source_dir)
        safe_name = str(relative).replace("/", "__")
        target = destination / safe_name
        try:
            content = tail_text_file(path, max_lines=max_lines)
            write_text(target, content)
            collected.append(
                {
                    "source": str(path),
                    "target": str(target),
                    "size_bytes": path.stat().st_size,
                }
            )
        except OSError as exc:
            collected.append({"source": str(path), "error": str(exc)})
    return collected


def detect_compose_services(compose_bin: Sequence[str], compose_file: Path) -> List[str]:
    command = compose_command(compose_bin, compose_file, "config", "--services")
    result = run_command(command, cwd=REPO_ROOT, timeout=30)
    if not result["ok"]:
        return []
    return [line.strip() for line in result["stdout"].splitlines() if line.strip()]


def collect_compose_snapshot(
    compose_bin: Sequence[str],
    compose_file: Path,
    packet_dir: Path,
) -> Dict[str, Any]:
    outputs: Dict[str, Any] = {}
    commands = {
        "ps.txt": ["ps"],
        "images.txt": ["images"],
        "config_services.txt": ["config", "--services"],
    }
    for filename, args in commands.items():
        result = run_command(
            compose_command(compose_bin, compose_file, *args),
            cwd=REPO_ROOT,
            timeout=60,
        )
        write_text(packet_dir / "compose" / filename, result["stdout"] + result["stderr"])
        outputs[filename] = result
    return outputs


def collect_service_logs(
    *,
    compose_bin: Sequence[str],
    compose_file: Path,
    packet_dir: Path,
    services: List[str],
    since: str,
    tail: int,
    packet_id: str,
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    summaries: Dict[str, Dict[str, Any]] = {}
    command_results: Dict[str, Any] = {}
    jsonl_dir = packet_dir / "normalized"
    jsonl_dir.mkdir(parents=True, exist_ok=True)

    for service in services:
        command = compose_command(
            compose_bin,
            compose_file,
            "logs",
            "--no-color",
            "--timestamps",
            "--since",
            since,
            "--tail",
            str(tail),
            service,
        )
        result = run_command(command, cwd=REPO_ROOT, timeout=180)
        command_results[service] = result

        raw_log_path = packet_dir / "logs" / f"{service}.log"
        write_text(raw_log_path, result["stdout"] + result["stderr"])
        lines = (result["stdout"] + result["stderr"]).splitlines()

        summary = summarize_service_lines(service, lines)
        summary["command_ok"] = result["ok"]
        summary["command_returncode"] = result["returncode"]
        summaries[service] = summary

        jsonl_path = jsonl_dir / f"{service}.jsonl"
        with jsonl_path.open("w", encoding="utf-8") as handle:
            for line_number, line in enumerate(lines, start=1):
                record = log_line_to_json_record(
                    service=service,
                    line=line,
                    packet_id=packet_id,
                    line_number=line_number,
                )
                handle.write(json.dumps(record, default=str) + "\n")

    return summaries, command_results


def collect_health_and_metrics(
    *,
    registry_entries: List[Dict[str, Any]],
    selected_services: List[str],
    compose_host_ports: Dict[str, int],
    packet_dir: Path,
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    selected = set(selected_services)
    health_results: Dict[str, Dict[str, Any]] = {}
    metrics_results: Dict[str, Dict[str, Any]] = {}

    registry_lookup: Dict[str, Dict[str, Any]] = {}
    for entry in registry_entries:
        name = entry.get("name")
        compose_name = entry.get("compose_service_name") or name
        if name:
            registry_lookup[str(name)] = entry
        if compose_name:
            registry_lookup[str(compose_name)] = entry

    for service in sorted(selected):
        entry = registry_lookup.get(service, {})
        canonical_name = entry.get("name", service)
        port = entry.get("port") or compose_host_ports.get(service)
        health_path = entry.get("health_path")

        health_candidates: List[str] = []
        if health_path:
            health_candidates.append(str(health_path))
        health_candidates.extend(path for path in ["/health", "/"] if path not in health_candidates)

        if port:
            last_health = None
            for candidate in health_candidates:
                health_url = f"http://127.0.0.1:{port}{candidate}"
                health = fetch_url(health_url, timeout=5.0)
                last_health = health
                if health.get("ok"):
                    break

            if last_health is None:
                health_results[canonical_name] = {"status": "unknown"}
            else:
                health_results[canonical_name] = {
                    "status": "ok" if last_health.get("ok") else "fail",
                    "url": last_health.get("url"),
                    "http_status": last_health.get("status"),
                    "duration_ms": last_health.get("duration_ms"),
                }
                write_text(
                    packet_dir / "health" / f"{canonical_name}.json",
                    last_health.get("body", ""),
                )

            metrics_url = f"http://127.0.0.1:{port}/metrics"
            metrics = fetch_url(metrics_url, timeout=5.0)
            metrics_results[canonical_name] = {
                "ok": bool(metrics.get("ok")),
                "url": metrics_url,
                "http_status": metrics.get("status"),
                "duration_ms": metrics.get("duration_ms"),
                "body_bytes": len(metrics.get("body", "")),
            }
            if metrics.get("body"):
                write_text(packet_dir / "metrics" / f"{canonical_name}.prom", metrics["body"])
        else:
            health_results[canonical_name] = {
                "status": "unknown",
                "reason": "No host port found in registry or compose definition.",
            }
            metrics_results[canonical_name] = {
                "ok": False,
                "reason": "No host port found in registry or compose definition.",
            }

    return health_results, metrics_results


def collect_git_snapshot(packet_dir: Path) -> Dict[str, Any]:
    commands = {
        "branch": ["git", "branch", "--show-current"],
        "commit": ["git", "rev-parse", "HEAD"],
        "status": ["git", "status", "--short"],
        "diffstat": ["git", "diff", "--stat"],
    }
    results: Dict[str, Any] = {}
    for key, command in commands.items():
        result = run_command(command, cwd=REPO_ROOT, timeout=30)
        results[key] = result
        write_text(packet_dir / "git" / f"{key}.txt", result["stdout"] + result["stderr"])
    return results


def render_summary_markdown(
    *,
    packet_id: str,
    created_at: str,
    services: List[str],
    summary_by_service: Dict[str, Dict[str, Any]],
) -> str:
    lines = [
        f"# Task Packet: {packet_id}",
        "",
        f"- Created (UTC): `{created_at}`",
        f"- Services captured: `{len(services)}`",
        "",
        "## Service Summary",
        "",
        "| Service | Lines | Errors | Warnings | Top Signature |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for service in services:
        summary = summary_by_service.get(service, {})
        top = summary.get("top_signatures", [])
        top_signature = top[0]["signature"] if top else ""
        lines.append(
            "| {service} | {lines_count} | {errors} | {warnings} | {signature} |".format(
                service=service,
                lines_count=summary.get("total_lines", 0),
                errors=summary.get("error_lines", 0),
                warnings=summary.get("warning_lines", 0),
                signature=(top_signature[:90] + "...") if len(top_signature) > 93 else top_signature,
            )
        )

    lines.extend(
        [
            "",
            "## Investigation Flow",
            "",
            "1. Read `summary.json` and `README.md` first for impact triage.",
            "2. Inspect `logs/<service>.log` and `normalized/<service>.jsonl` for exact timeline.",
            "3. Compare `/health` and `/metrics` snapshots for degraded dependencies.",
            "4. Use `analysis/packet_metrics.prom` or `analysis/datadog_series.json` for dashboard ingest.",
        ]
    )
    return "\n".join(lines) + "\n"


def maybe_send_datadog_series(
    *,
    payload: Dict[str, Any],
    site: str,
) -> Dict[str, Any]:
    api_key = os.getenv("DD_API_KEY")
    if not api_key:
        return {"ok": False, "error": "DD_API_KEY is not set"}

    url = f"https://api.{site}/api/v2/series"
    request = Request(
        url,
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "DD-API-KEY": api_key,
        },
    )

    try:
        with urlopen(request, timeout=10.0) as response:
            body = response.read().decode("utf-8", errors="replace")
            return {
                "ok": 200 <= response.status < 300,
                "status": response.status,
                "body": body,
            }
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {"ok": False, "status": exc.code, "body": body, "error": str(exc)}
    except URLError as exc:
        return {"ok": False, "error": str(exc)}


def create_archive(packet_dir: Path) -> Path:
    archive_path = packet_dir.with_suffix(".tar.gz")
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(packet_dir, arcname=packet_dir.name)
    return archive_path


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    logger = configure_logging("task-packet-collector", json_logs=False)

    timestamp = datetime.now(timezone.utc)
    packet_slug = f"{args.task_id}-{timestamp.strftime('%Y%m%dT%H%M%SZ')}"
    output_root = REPO_ROOT / args.output_root
    packet_dir = output_root / packet_slug
    packet_dir.mkdir(parents=True, exist_ok=True)

    bind_task_packet(packet_slug, workspace_id=str(REPO_ROOT))
    logger.info("collecting task packet artifacts")

    compose_file = (REPO_ROOT / args.compose_file).resolve()
    registry_file = (REPO_ROOT / args.registry_file).resolve()
    compose_host_ports = parse_compose_host_ports(compose_file)
    compose_bin = resolve_compose_command(REPO_ROOT)
    registry_entries = read_registry(registry_file)

    compose_services: List[str] = []
    if compose_bin and compose_file.exists():
        compose_services = detect_compose_services(compose_bin, compose_file)
    requested = parse_services_arg(args.services)
    selected_services = select_services(compose_services, requested) if compose_services else (requested or [])

    compose_snapshot = {}
    if compose_bin and compose_file.exists():
        compose_snapshot = collect_compose_snapshot(compose_bin, compose_file, packet_dir)
    else:
        logger.warning("docker compose not available or compose file missing; skipping compose snapshot")

    summary_by_service: Dict[str, Dict[str, Any]] = {}
    compose_log_results: Dict[str, Any] = {}
    if compose_bin and compose_file.exists() and selected_services:
        summary_by_service, compose_log_results = collect_service_logs(
            compose_bin=compose_bin,
            compose_file=compose_file,
            packet_dir=packet_dir,
            services=selected_services,
            since=args.since,
            tail=args.tail,
            packet_id=packet_slug,
        )

    health_results, metrics_results = collect_health_and_metrics(
        registry_entries=registry_entries,
        selected_services=selected_services or compose_services,
        compose_host_ports=compose_host_ports,
        packet_dir=packet_dir,
    )
    local_logs = collect_local_logs(
        packet_dir=packet_dir,
        max_files=args.max_local_files,
        max_lines=args.local_tail,
    )
    git_snapshot = collect_git_snapshot(packet_dir)

    created_at = timestamp.isoformat()
    summary_md = render_summary_markdown(
        packet_id=packet_slug,
        created_at=created_at,
        services=selected_services,
        summary_by_service=summary_by_service,
    )
    write_text(packet_dir / "README.md", summary_md)

    summary_json: Dict[str, Any] = {
        "packet_id": packet_slug,
        "created_at": created_at,
        "task_id": args.task_id,
        "workspace": str(REPO_ROOT),
        "compose_file": str(compose_file),
        "registry_file": str(registry_file),
        "selected_services": selected_services,
        "service_summary": summary_by_service,
        "health": health_results,
        "metrics": metrics_results,
        "local_logs": local_logs,
        "host": {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
        },
        "commands": {
            "compose_snapshot": compose_snapshot,
            "compose_logs": compose_log_results,
            "git": git_snapshot,
        },
    }
    write_json(packet_dir / "summary.json", summary_json)

    prom_export = build_prometheus_export(
        packet_id=packet_slug,
        summary_by_service=summary_by_service,
        health_status=health_results,
        metrics_status=metrics_results,
    )
    write_text(packet_dir / "analysis" / "packet_metrics.prom", prom_export)

    datadog_payload = build_datadog_series(
        packet_id=packet_slug,
        summary_by_service=summary_by_service,
        timestamp=int(timestamp.timestamp()),
    )
    write_json(packet_dir / "analysis" / "datadog_series.json", datadog_payload)

    datadog_result: Optional[Dict[str, Any]] = None
    if args.emit_datadog:
        datadog_result = maybe_send_datadog_series(
            payload=datadog_payload,
            site=args.datadog_site,
        )
        write_json(packet_dir / "analysis" / "datadog_emit_result.json", datadog_result)

    investigation_brief = textwrap.dedent(
        f"""
        # Investigation Packet Brief

        Packet `{packet_slug}` is ready for triage.

        ## Suggested Investigation Task Packet
        - Goal: isolate root cause for high-error services in the current environment.
        - Inputs: `summary.json`, `README.md`, `logs/`, `health/`, `metrics/`.
        - Output: root-cause hypothesis, failing dependency chain, and fix plan.

        ## Fast Start Commands
        - `jq '.service_summary' {packet_dir / 'summary.json'}`
        - `rg -n "error|critical|exception|traceback" {packet_dir / 'logs'}`
        - `cat {packet_dir / 'analysis' / 'packet_metrics.prom'}`
        """
    ).strip() + "\n"
    write_text(packet_dir / "TASK_PACKET.md", investigation_brief)

    archive_path = None
    if not args.no_archive:
        archive_path = create_archive(packet_dir)

    final_report = {
        "packet_id": packet_slug,
        "packet_dir": str(packet_dir),
        "archive_path": str(archive_path) if archive_path else None,
        "selected_services": selected_services,
        "service_count": len(selected_services),
        "health_checks": len(health_results),
        "metrics_checks": len(metrics_results),
        "datadog_emit": datadog_result,
    }
    write_json(packet_dir / "packet_report.json", final_report)

    print(json.dumps(final_report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
