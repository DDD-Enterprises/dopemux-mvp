#!/usr/bin/env python3
import os
import re
import sys
import yaml
import json
import argparse
import subprocess
import socket
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Tuple

# Import registry module
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.dopemux.registry import load_registry, get_smoke_services
from enum import Enum

from src.dopemux.health.errors import (
    HealthCheckStatus,
    classify_health_response,
    classify_docker_status,
    get_classification_message,
    get_suggested_action,
)


class HealthCheckError(str, Enum):
    PASS = "PASS"
    TIMEOUT = "TIMEOUT"
    PORT_CLOSED = "PORT_CLOSED"
    HTTP_FAIL = "HTTP_FAIL"
    INVALID_JSON = "INVALID_JSON"
    SHAPE_FAIL = "SHAPE_FAIL"
    CONTAINER_NOT_FOUND = "CONTAINER_NOT_FOUND"
    CONTAINER_EXITED = "CONTAINER_EXITED"
    DEP_MISSING = "DEP_MISSING"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    CONFIG_MISSING = "CONFIG_MISSING"
    CONTAINER_UNHEALTHY = "CONTAINER_UNHEALTHY"


@dataclass
class ServiceCheck:
    service: str
    ok: bool
    error: Optional[HealthCheckError] = None
    info: Optional[str] = None


def check_port_open(host: str, port: int, timeout: float = 2.0) -> Tuple[bool, Optional[HealthCheckError]]:
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return True, None
    except socket.timeout:
        return False, HealthCheckError.TIMEOUT
    except ConnectionRefusedError:
        return False, HealthCheckError.PORT_CLOSED
    except OSError:
        return False, HealthCheckError.PORT_CLOSED


def check_health_endpoint(url: str, timeout: float = 2.0) -> Tuple[bool, HealthCheckError, Optional[Dict[str, Any]], Optional[str]]:
    try:
        result = subprocess.run(
            ["curl", "-fsS", "--max-time", str(timeout), url],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False, HealthCheckError.TIMEOUT, None, "Timeout"
    except Exception as exc:
        return False, HealthCheckError.HTTP_FAIL, None, str(exc)

    if result.returncode != 0:
        info = (result.stderr or result.stdout or "").strip()
        return False, HealthCheckError.HTTP_FAIL, None, info

    raw = result.stdout or ""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return False, HealthCheckError.INVALID_JSON, None, "JSON parse error"

    required_keys = {"status", "service", "ts"}
    missing = required_keys - set(data.keys())
    if missing:
        return False, HealthCheckError.SHAPE_FAIL, None, f"Missing keys: {', '.join(sorted(missing))}"

    return True, HealthCheckError.PASS, data, None


def check_docker_status(service_name: str) -> Tuple[Optional[HealthCheckError], Optional[str]]:
    try:
        result = subprocess.run(
            ["docker", "compose", "ps", "-a", service_name],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except FileNotFoundError:
        return None, None
    except Exception as exc:
        return None, str(exc)

    status_output = (result.stdout or result.stderr or "").strip()
    if not status_output:
        return HealthCheckError.CONTAINER_NOT_FOUND, f"{service_name} not found"

    lower = status_output.lower()
    if "unhealthy" in lower:
        return HealthCheckError.CONTAINER_UNHEALTHY, status_output

    if "exited" in lower:
        logs_output = ""
        try:
            logs = subprocess.run(
                ["docker", "compose", "logs", service_name],
                capture_output=True,
                text=True,
                timeout=5,
            )
            logs_output = (logs.stdout or logs.stderr or "").strip()
        except Exception:
            logs_output = ""

        if re.search(r"modulenotfounderror|no module named|importerror", logs_output, re.IGNORECASE):
            return HealthCheckError.DEP_MISSING, logs_output
        if re.search(r"syntaxerror|invalid syntax", logs_output, re.IGNORECASE):
            return HealthCheckError.SYNTAX_ERROR, logs_output
        if re.search(r"keyerror|config|database_url", logs_output, re.IGNORECASE):
            return HealthCheckError.CONFIG_MISSING, logs_output

        return HealthCheckError.CONTAINER_EXITED, status_output

    return None, status_output

@dataclass
class PortHealthEntry:
    service: str
    registry_port: Optional[int]
    detected_port: Optional[int]
    expose_port: Optional[int]
    protocol_guess: str  # http, mcp, worker
    health_route: Optional[str]
    docker_healthcheck: Optional[str]
    runtime_status: Optional[HealthCheckStatus]  # Use enum
    runtime_health: Optional[str]  # Raw health string for backward compat
    docker_container_status: Optional[str] = None  # Docker container state
    docker_health_status: Optional[str] = None  # Docker health state
    status_flags: List[str] = None
    source_evidence: Dict[str, str] = None
    classification_msg: Optional[str] = None  # Human-readable classification
    suggested_action: Optional[str] = None  # Suggested fix
    
    def __post_init__(self):
        if self.status_flags is None:
            self.status_flags = []
        if self.source_evidence is None:
            self.source_evidence = {}

def find_repo_root():
    cur = Path(__file__).resolve().parent
    for _ in range(5):
        if (cur / "services").is_dir():
            return cur
        cur = cur.parent
    return Path.cwd()

def get_dockerfile_info(df_path: Path):
    if not df_path.exists():
        return None, None
    content = df_path.read_text(errors='ignore')
    
    expose = None
    expose_match = re.search(r'(?i)^EXPOSE\s+(\d+)', content, re.M)
    if expose_match:
        expose = int(expose_match.group(1))
        
    healthcheck = None
    hc_match = re.search(r'(?i)^HEALTHCHECK\s+.*CMD\s+(.*)', content, re.M)
    if hc_match:
        healthcheck = hc_match.group(1).strip()
        
    return expose, healthcheck

def scan_code_for_port_and_health(service_path: Path):
    detected_port = None
    health_route = None
    evidence = {}

    # Scan for port
    port_base = None
    
    for py_file in service_path.rglob("*.py"):
        try:
            content = py_file.read_text(errors='ignore')
            
            # 1. Detect PORT_BASE
            if not port_base:
                base_match = re.search(r'PORT_BASE\s*=\s*int\(os\.get?env\(["\']PORT_BASE["\'],\s*["\'](\d+)["\']\)\)', content)
                if base_match:
                    port_base = int(base_match.group(1))
                    evidence['port_base'] = f"PORT_BASE default {port_base} found in {py_file.name}"

            # 2. Port detection
            if not detected_port:
                # env default (standard)
                env_match = re.search(r'os\.get?env\(["\'](\w*PORT\w*)["\'],\s*(?:default=)?(\d+)\)', content)
                if env_match:
                    detected_port = int(env_match.group(2))
                    evidence['port'] = f"os.getenv({env_match.group(1)}, {detected_port}) in {py_file.name}"
                
                # uvicorn.run
                uv_match = re.search(r'uvicorn\.run\(.*port\s*=\s*(\d+)', content)
                if uv_match:
                    detected_port = int(uv_match.group(1))
                    evidence['port'] = f"uvicorn.run(port={detected_port}) in {py_file.name}"
                
                # Computed port (PORT_BASE + offset)
                if port_base:
                    # Look for things like SERVICE_PORT = PORT_BASE + 16
                    comp_match = re.search(r'(\w*PORT\w*)\s*=\s*PORT_BASE\s*\+\s*(\d+)', content)
                    if comp_match:
                        offset = int(comp_match.group(2))
                        detected_port = port_base + offset
                        evidence['port'] = f"PORT_BASE({port_base}) + {offset} in {py_file.name}"

            # 3. Health route detection (unchanged)
            if not health_route:
                if re.search(r'@(?:app|router|sub_router)\.get\(["\'](/health|/api/health)["\']\)', content):
                    health_route = re.search(r'["\'](/health|/api/health)["\']', content).group(0).strip('"\'')
                    evidence['health'] = f"Route {health_route} found in {py_file.name}"
                elif re.search(r'web\.get\(["\'](/health)["\']', content): # aiohttp
                    health_route = "/health"
                    evidence['health'] = f"aiohttp route /health found in {py_file.name}"

        except Exception:
            continue
            
    return detected_port, health_route, evidence

def get_docker_status(service_name: str, compose_file: Optional[Path] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Get Docker container status and health status.
    
    Args:
        service_name: Docker compose service name
        compose_file: Path to docker-compose file (optional)
    
    Returns:
        Tuple of (container_status, health_status)
        container_status: "running", "exited", etc.
        health_status: "healthy", "unhealthy", "starting", None
    """
    try:
        # Try to find container by service name
        # Use docker compose ps to get status
        cmd = ["docker", "compose"]
        if compose_file:
            cmd.extend(["-f", str(compose_file)])
        cmd.extend(["ps", "-a", "--format", "json", service_name])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0 and result.stdout.strip():
            try:
                # Parse JSON output (one container per line)
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    container_info = json.loads(line)
                    
                    # Extract status
                    state = container_info.get("State", "unknown")
                    health = container_info.get("Health", "")
                    
                    # Health can be empty, "healthy", "unhealthy", "starting"
                    health_status = health if health else None
                    
                    return (state, health_status)
            except json.JSONDecodeError:
                pass
        
        # Fallback: try docker ps with name filter
        cmd = ["docker", "ps", "-a", "--filter", f"name={service_name}", "--format", "{{.Status}}"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0 and result.stdout.strip():
            status_str = result.stdout.strip()
            
            # Parse status string like "Up 2 minutes (healthy)"
            if "Up" in status_str:
                container_status = "running"
                if "(healthy)" in status_str:
                    health_status = "healthy"
                elif "(unhealthy)" in status_str:
                    health_status = "unhealthy"
                elif "(health: starting)" in status_str:
                    health_status = "starting"
                else:
                    health_status = None
                return (container_status, health_status)
            elif "Exited" in status_str:
                return ("exited", None)
        
        return (None, None)
        
    except Exception:
        return (None, None)


def check_runtime_health(port: int, host: str = "127.0.0.1", health_path: str = "/health") -> tuple[HealthCheckStatus, str]:
    """
    Probes the service via curl and validates health response shape.
    
    Returns:
        Tuple of (HealthCheckStatus, raw_response_string)
    """
    if not port:
        return (HealthCheckStatus.UNKNOWN, "NO_PORT")
        
    url = f"http://{host}:{port}{health_path}"
    try:
        # Get full response body to validate shape
        cmd = ["curl", "-fsS", "--max-time", "2", url]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Classify the response
            status = classify_health_response(
                http_status=200,
                response_body=result.stdout,
                error_msg=None
            )
            return (status, result.stdout)
        else:
            # Connection failed
            error_msg = result.stderr or "Connection failed"
            status = classify_health_response(
                http_status=None,
                response_body=None,
                error_msg=error_msg
            )
            return (status, error_msg)
            
    except Exception as e:
        return (HealthCheckStatus.UNKNOWN, str(e))

def audit_service_entry(entry, root: Path, mode: str, host: str, compose_file: Optional[Path] = None) -> PortHealthEntry:
    """Audit a ServiceRegistryEntry."""
    name = entry.name
    svc_path = root / entry.path
    df_path = svc_path / "Dockerfile" if entry.is_docker else None
    
    registry_port = entry.port
    
    # Static Analysis
    expose = None
    docker_health = None
    if df_path and df_path.exists():
        expose, docker_health = get_dockerfile_info(df_path)
    
    det_port, det_health, evidence = scan_code_for_port_and_health(svc_path)
    
    # Use registry protocol
    protocol = entry.protocol
    
    # Runtime Analysis (if enabled)
    runtime_status = None
    runtime_health_raw = None
    classification_msg = None
    suggested_action = None
    docker_container_status = None
    docker_health_status = None
    
    if mode == "runtime" or mode == "both":
        # Check Docker status first (if dockerized service)
        if entry.is_docker and entry.compose_service:
            docker_container_status, docker_health_status = get_docker_status(
                entry.compose_service, 
                compose_file
            )
            
            # Classify based on Docker status
            docker_classification = classify_docker_status(docker_container_status, docker_health_status)
            
            if docker_classification:
                # Docker has a definitive status
                runtime_status = docker_classification
                runtime_health_raw = f"docker:{docker_container_status}/{docker_health_status or 'none'}"
                classification_msg = get_classification_message(docker_classification)
                suggested_action = get_suggested_action(docker_classification)
            else:
                # Container running but no clear issue from Docker, check HTTP health
                target_port = registry_port or det_port or expose
                if target_port:
                    health_path = entry.health_url or det_health or "/health"
                    status_enum, raw_response = check_runtime_health(target_port, host, health_path)
                    runtime_status = status_enum
                    runtime_health_raw = raw_response
                    classification_msg = get_classification_message(status_enum)
                    suggested_action = get_suggested_action(status_enum)
                else:
                    runtime_status = HealthCheckStatus.UNKNOWN
                    runtime_health_raw = "NO_PORT"
        else:
            # Not a Docker service or no compose mapping, just check HTTP
            target_port = registry_port or det_port or expose
            if target_port:
                health_path = entry.health_url or det_health or "/health"
                status_enum, raw_response = check_runtime_health(target_port, host, health_path)
                runtime_status = status_enum
                runtime_health_raw = raw_response
                classification_msg = get_classification_message(status_enum)
                suggested_action = get_suggested_action(status_enum)
            else:
                runtime_status = HealthCheckStatus.UNKNOWN
                runtime_health_raw = "NO_PORT"

    # Flags
    flags = []
    if registry_port and det_port and registry_port != det_port:
        flags.append("REGISTRY_PORT_MISMATCH")
    if not registry_port and (det_port or expose) and protocol != "worker":
        flags.append("REGISTRY_MISSING_PORT")
    if protocol == "http" and not (det_health or docker_health or entry.health_url):
        flags.append("MISSING_HEALTH_SIGNAL")
    if expose and det_port and expose != det_port:
        flags.append("Dockerfile_EXPOSE_MISMATCH")
    if runtime_status == HealthCheckStatus.RUNTIME_DOWN:
        flags.append("RUNTIME_DOWN")
    if runtime_status == HealthCheckStatus.SHAPE_FAIL:
        flags.append("HEALTH_SHAPE_FAIL")
    if runtime_status == HealthCheckStatus.CONTAINER_EXITED:
        flags.append("CONTAINER_EXITED")
    if runtime_status == HealthCheckStatus.CONTAINER_UNHEALTHY:
        flags.append("CONTAINER_UNHEALTHY")

    return PortHealthEntry(
        service=name,
        registry_port=registry_port,
        detected_port=det_port,
        expose_port=expose,
        protocol_guess=protocol,
        health_route=det_health or entry.health_url,
        docker_healthcheck=docker_health,
        runtime_status=runtime_status,
        runtime_health=runtime_health_raw,
        docker_container_status=docker_container_status,
        docker_health_status=docker_health_status,
        status_flags=flags,
        source_evidence=evidence,
        classification_msg=classification_msg,
        suggested_action=suggested_action,
    )

def main():
    parser = argparse.ArgumentParser(description="Dopemux Port & Health Audit")
    parser.add_argument("--mode", choices=["static", "runtime", "both"], default="static", help="Audit mode")
    parser.add_argument("--services", help="Comma-separated list of services to audit")
    parser.add_argument("--host", default="127.0.0.1", help="Host to probe in runtime mode")
    parser.add_argument("--smoke-only", action="store_true", help="Only audit smoke-tier services")
    parser.add_argument("--compose-file", help="Docker compose file path for container status checks")
    args = parser.parse_args()

    root = find_repo_root()
    reports_dir = root / "reports"
    reports_dir.mkdir(exist_ok=True)

    # Parse compose file path
    compose_file = None
    if args.compose_file:
        compose_file = Path(args.compose_file)
    elif args.mode in ["runtime", "both"]:
        # Default to smoke stack for runtime checks
        compose_file = root / "docker-compose.smoke.yml"

    # Load from registry module
    try:
        if args.smoke_only:
            entries = get_smoke_services()
        else:
            entries = load_registry()
    except Exception as e:
        print(f"Error: Failed to load registry: {e}")
        sys.exit(1)

    filter_services = args.services.split(",") if args.services else None
    
    results = []
    for entry in entries:
        if filter_services and entry.name not in filter_services:
            continue
            
        result = audit_service_entry(entry, root, args.mode, args.host, compose_file)
        results.append(result)

    # JSON report
    with open(reports_dir / "ports_health_matrix.json", 'w') as f:
        json.dump([asdict(r) for r in results], f, indent=2)

    # MD report
    md_lines = [
        f"# Port & Health Matrix ({args.mode.upper()})",
        "",
        "| Service | Registry | Detected | Expose | Status | Class | Docker | Flags |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        status_str = str(r.runtime_status.value) if r.runtime_status else "N/A"
        docker_str = f"{r.docker_container_status or '-'}/{r.docker_health_status or '-'}" if r.docker_container_status else "-"
        flags_str = ", ".join(r.status_flags) if r.status_flags else "-"
        
        md_lines.append(
            f"| `{r.service}` | {r.registry_port or '-'} | {r.detected_port or '-'} | "
            f"{r.expose_port or '-'} | {status_str} | {r.classification_msg or 'N/A'} | {docker_str} | {flags_str} |"
        )
    
    # Add action suggestions if runtime mode
    if args.mode != "static":
        md_lines.append("")
        md_lines.append("## Suggested Actions")
        md_lines.append("")
        for r in results:
            if r.runtime_status and r.runtime_status != HealthCheckStatus.HEALTHY:
                md_lines.append(f"### {r.service}")
                md_lines.append(f"**Status**: {r.runtime_status.value}")
                md_lines.append(f"**Action**: {r.suggested_action or 'Check logs'}")
                md_lines.append("")

    with open(reports_dir / "ports_health_matrix.md", 'w') as f:
        f.write("\n".join(md_lines))

    print(f"Audit complete in {args.mode} mode. Reports in {reports_dir}")
    if args.mode != "static":
        # Print runtime summary to stdout for immediate visibility
        print("\nRuntime Summary:")
        for r in results:
            if r.runtime_status:
                class_str = r.runtime_status.value
                print(f"{r.service}: {class_str}")
                if r.runtime_status != HealthCheckStatus.HEALTHY:
                    print(f"  → {r.suggested_action}")

if __name__ == "__main__":
    main()
