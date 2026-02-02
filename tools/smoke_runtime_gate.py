#!/usr/bin/env python3
"""
Smoke Stack Runtime Gate

Deterministic runtime verification for smoke stack services:
1. Container stability (not restarting)
2. Port connectivity
3. HTTP health endpoint validation
4. Auto-capture logs on failure

Usage:
    python tools/smoke_runtime_gate.py

Exit codes:
    0 = All services healthy
    1 = One or more services failed
"""
import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import urllib.request
import urllib.error
import socket

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


@dataclass
class ServiceHealthConfig:
    """Health configuration for a smoke service."""
    name: str
    container_name: str
    published_port: int
    health_path: str

    @property
    def health_url(self) -> str:
        """Construct health check URL."""
        return f"http://localhost:{self.published_port}{self.health_path}"


@dataclass
class ServiceHealthResult:
    """Health check result for a service."""
    name: str
    container_healthy: bool
    container_status: str
    restart_count: int
    port_open: bool
    http_healthy: bool
    http_status_code: Optional[int]
    error: Optional[str]
    elapsed_ms: float

    @property
    def overall_healthy(self) -> bool:
        """Overall health status."""
        return self.container_healthy and self.port_open and self.http_healthy


class ComposeParser:
    """Parse docker-compose.smoke.yml to extract service configs."""

    def __init__(self, compose_path: Path, env_file: Path):
        self.compose_path = compose_path
        self.env_file = env_file
        self.env_vars = self._load_env()
        self.compose_data = self._load_compose()

    def _load_env(self) -> Dict[str, str]:
        """Load environment variables from .env.smoke."""
        env = {}
        if self.env_file.exists():
            with open(self.env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, _, value = line.partition('=')
                        env[key.strip()] = value.strip()
        return env

    def _load_compose(self) -> dict:
        """Load docker-compose.smoke.yml."""
        with open(self.compose_path) as f:
            return yaml.safe_load(f)

    def _resolve_env_var(self, value: str) -> str:
        """Resolve environment variable placeholders."""
        if not isinstance(value, str):
            return value

        # Handle ${VAR:-default} pattern
        import re
        pattern = r'\$\{([^}:]+)(?::-)([^}]+)\}'

        def replacer(match):
            var_name = match.group(1)
            default_value = match.group(2)
            return self.env_vars.get(var_name, default_value)

        return re.sub(pattern, replacer, value)

    def get_smoke_services(self) -> List[ServiceHealthConfig]:
        """Extract smoke service health configs."""
        services = []
        target_services = ['conport', 'dopecon-bridge', 'task-orchestrator']

        compose_services = self.compose_data.get('services', {})

        for svc_name in target_services:
            if svc_name not in compose_services:
                continue

            svc_data = compose_services[svc_name]

            # Get container name
            container_name = svc_data.get('container_name', f'smoke-{svc_name}')

            # Parse published port
            ports = svc_data.get('ports', [])
            if not ports:
                continue

            port_mapping = self._resolve_env_var(ports[0])
            # Format: "host:container" or just "port"
            if ':' in port_mapping:
                published_port = int(port_mapping.split(':')[0])
            else:
                published_port = int(port_mapping)

            # Get health path from healthcheck
            health_path = '/health'  # Default
            healthcheck = svc_data.get('healthcheck', {})
            if healthcheck:
                test = healthcheck.get('test', [])
                # Extract path from curl command
                for part in test:
                    if part.startswith('http://localhost'):
                        # Extract path portion
                        url_part = part.split('http://localhost')[1]
                        # Remove port if present
                        if '/' in url_part:
                            health_path = '/' + url_part.split('/', 1)[1].split(' ')[0]

            services.append(ServiceHealthConfig(
                name=svc_name,
                container_name=container_name,
                published_port=published_port,
                health_path=health_path
            ))

        return services


class ContainerStabilityChecker:
    """Check container stability via docker compose ps."""

    def __init__(self, compose_file: Path):
        self.compose_file = compose_file

    def check_container(self, container_name: str) -> Tuple[bool, str, int]:
        """
        Check container stability.

        Returns:
            (is_healthy, status, restart_count)
        """
        try:
            # Get container state via docker inspect
            result = subprocess.run(
                ['docker', 'inspect', container_name],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return False, "not_found", 0

            import json
            inspect_data = json.loads(result.stdout)[0]

            state = inspect_data['State']
            status = state.get('Status', 'unknown')
            restart_count = state.get('RestartCount', 0)

            # Container is healthy if running and not restarting excessively
            is_running = status == 'running'
            is_stable = restart_count < 3

            is_healthy = is_running and is_stable

            return is_healthy, status, restart_count

        except Exception as e:
            return False, f"error: {e}", 0


class HealthProber:
    """Probe service health with retry logic."""

    def __init__(self, max_retries: int = 5, timeout_per_probe: float = 2.0):
        self.max_retries = max_retries
        self.timeout_per_probe = timeout_per_probe

    def check_port_open(self, host: str, port: int) -> bool:
        """Check if TCP port is open."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout_per_probe)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def check_http_health(self, url: str) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Check HTTP health endpoint.

        Returns:
            (is_healthy, status_code, error)
        """
        try:
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=self.timeout_per_probe) as response:
                status_code = response.getcode()
                is_healthy = 200 <= status_code < 300
                return is_healthy, status_code, None

        except urllib.error.HTTPError as e:
            return False, e.code, f"HTTP {e.code}"

        except urllib.error.URLError as e:
            return False, None, f"Connection error: {e.reason}"

        except Exception as e:
            return False, None, f"Unexpected error: {e}"

    def probe_service(self, config: ServiceHealthConfig) -> ServiceHealthResult:
        """
        Probe service with retry logic.

        Returns complete health result.
        """
        start_time = time.time()

        # Phase 1: Container stability
        stability_checker = ContainerStabilityChecker(Path('docker-compose.smoke.yml'))
        container_healthy, container_status, restart_count = stability_checker.check_container(
            config.container_name
        )

        # If container is unstable, skip port/http checks
        if not container_healthy:
            elapsed_ms = (time.time() - start_time) * 1000
            return ServiceHealthResult(
                name=config.name,
                container_healthy=False,
                container_status=container_status,
                restart_count=restart_count,
                port_open=False,
                http_healthy=False,
                http_status_code=None,
                error=f"Container unstable: {container_status} (restarts: {restart_count})",
                elapsed_ms=elapsed_ms
            )

        # Phase 2: Port + HTTP with retry
        port_open = False
        http_healthy = False
        http_status_code = None
        last_error = None

        for attempt in range(self.max_retries):
            # Check port
            port_open = self.check_port_open('localhost', config.published_port)

            if port_open:
                # Check HTTP health
                http_healthy, http_status_code, http_error = self.check_http_health(
                    config.health_url
                )

                if http_healthy:
                    # Success!
                    elapsed_ms = (time.time() - start_time) * 1000
                    return ServiceHealthResult(
                        name=config.name,
                        container_healthy=True,
                        container_status=container_status,
                        restart_count=restart_count,
                        port_open=True,
                        http_healthy=True,
                        http_status_code=http_status_code,
                        error=None,
                        elapsed_ms=elapsed_ms
                    )

                last_error = http_error
            else:
                last_error = f"Port {config.published_port} not open"

            # Wait before retry (exponential backoff)
            if attempt < self.max_retries - 1:
                wait_time = 1.0 * (2 ** attempt)
                time.sleep(wait_time)

        # All retries exhausted
        elapsed_ms = (time.time() - start_time) * 1000
        return ServiceHealthResult(
            name=config.name,
            container_healthy=True,
            container_status=container_status,
            restart_count=restart_count,
            port_open=port_open,
            http_healthy=False,
            http_status_code=http_status_code,
            error=last_error or "Health check failed",
            elapsed_ms=elapsed_ms
        )


class EvidenceCollector:
    """Collect evidence on failure."""

    def __init__(self, compose_file: Path, output_dir: Path):
        self.compose_file = compose_file
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def collect_compose_ps(self) -> Path:
        """Capture docker compose ps output."""
        output_file = self.output_dir / "compose_ps.txt"

        try:
            result = subprocess.run(
                ['docker', 'compose', '-f', str(self.compose_file), 'ps', '--all'],
                capture_output=True,
                text=True,
                timeout=10
            )

            with open(output_file, 'w') as f:
                f.write(result.stdout)

            return output_file

        except Exception as e:
            print(f"⚠️ Failed to capture compose ps: {e}", file=sys.stderr)
            return output_file

    def collect_logs(self, container_name: str, tail_lines: int = 200) -> Path:
        """Capture container logs."""
        output_file = self.output_dir / f"logs_{container_name.replace('smoke-', '')}.tail.txt"

        try:
            result = subprocess.run(
                ['docker', 'logs', container_name, '--tail', str(tail_lines)],
                capture_output=True,
                text=True,
                timeout=10
            )

            with open(output_file, 'w') as f:
                f.write(f"=== STDOUT ===\n{result.stdout}\n")
                f.write(f"\n=== STDERR ===\n{result.stderr}\n")

            return output_file

        except Exception as e:
            print(f"⚠️ Failed to capture logs for {container_name}: {e}", file=sys.stderr)
            return output_file


class RuntimeGate:
    """Main runtime gate orchestrator."""

    def __init__(
        self,
        compose_file: Path,
        env_file: Path,
        output_dir: Path,
        max_retries: int = 5,
        timeout_per_probe: float = 2.0
    ):
        self.compose_file = compose_file
        self.env_file = env_file
        self.output_dir = output_dir
        self.max_retries = max_retries
        self.timeout_per_probe = timeout_per_probe

        self.parser = ComposeParser(compose_file, env_file)
        self.prober = HealthProber(max_retries, timeout_per_probe)
        self.evidence = EvidenceCollector(compose_file, output_dir)

    def run(self) -> Tuple[bool, List[ServiceHealthResult]]:
        """
        Run runtime gate checks.

        Returns:
            (all_healthy, results)
        """
        print("🚀 Smoke Stack Runtime Gate")
        print("=" * 60)
        print()

        # Get service configs
        services = self.parser.get_smoke_services()
        print(f"Services to check: {len(services)}")
        for svc in services:
            print(f"  • {svc.name:20s} {svc.health_url}")
        print()

        # Probe each service
        results = []
        for svc in services:
            print(f"🔍 Checking {svc.name}...")
            result = self.prober.probe_service(svc)
            results.append(result)

            # Print immediate feedback
            if result.overall_healthy:
                print(f"   ✅ HEALTHY (HTTP {result.http_status_code} in {result.elapsed_ms:.0f}ms)")
            else:
                print(f"   ❌ FAILED: {result.error}")

        print()

        # Summary
        all_healthy = all(r.overall_healthy for r in results)

        print("📊 Summary")
        print("=" * 60)
        for result in results:
            status_emoji = "✅" if result.overall_healthy else "❌"
            print(f"{status_emoji} {result.name:20s} ", end='')

            if result.overall_healthy:
                print(f"UP (HTTP {result.http_status_code})")
            else:
                print(f"FAILED - {result.error}")

        print()

        # Collect evidence on failure
        if not all_healthy:
            print("📦 Collecting failure evidence...")
            self._collect_evidence(results)
            print()

        return all_healthy, results

    def _collect_evidence(self, results: List[ServiceHealthResult]):
        """Collect evidence for failed services."""
        # Always collect compose ps
        ps_file = self.evidence.collect_compose_ps()
        print(f"   • Compose PS: {ps_file}")

        # Collect logs for failed services
        failed_services = [r for r in results if not r.overall_healthy]
        for result in failed_services:
            # Map service name to container name
            container_name = f"smoke-{result.name}"
            log_file = self.evidence.collect_logs(container_name)
            print(f"   • Logs ({result.name}): {log_file}")

        # Write JSON report
        json_file = self.output_dir / "runtime_gate.json"
        with open(json_file, 'w') as f:
            json.dump([asdict(r) for r in results], f, indent=2)
        print(f"   • JSON report: {json_file}")

        # Write markdown report
        md_file = self.output_dir / "runtime_gate.md"
        self._write_markdown_report(md_file, results)
        print(f"   • Markdown report: {md_file}")

    def _write_markdown_report(self, output_file: Path, results: List[ServiceHealthResult]):
        """Write markdown summary report."""
        with open(output_file, 'w') as f:
            f.write("# Smoke Stack Runtime Gate Report\n\n")
            f.write(f"**Timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("## Summary\n\n")
            total = len(results)
            healthy = sum(1 for r in results if r.overall_healthy)
            f.write(f"**Status**: {healthy}/{total} services healthy\n\n")

            f.write("| Service | Container | Port | HTTP | Status |\n")
            f.write("|---------|-----------|------|------|--------|\n")

            for r in results:
                container_check = "✅" if r.container_healthy else "❌"
                port_check = "✅" if r.port_open else "❌"
                http_check = "✅" if r.http_healthy else "❌"
                overall = "PASS" if r.overall_healthy else "FAIL"

                f.write(f"| {r.name} | {container_check} | {port_check} | {http_check} | {overall} |\n")

            f.write("\n## Failure Details\n\n")
            failed = [r for r in results if not r.overall_healthy]

            if not failed:
                f.write("_No failures detected_\n")
            else:
                for r in failed:
                    f.write(f"### {r.name}\n\n")
                    f.write(f"- **Container Status**: {r.container_status}\n")
                    f.write(f"- **Restart Count**: {r.restart_count}\n")
                    f.write(f"- **Port Open**: {r.port_open}\n")
                    f.write(f"- **HTTP Status**: {r.http_status_code or 'N/A'}\n")
                    f.write(f"- **Error**: {r.error}\n")
                    f.write(f"- **Elapsed**: {r.elapsed_ms:.0f}ms\n\n")


def main():
    parser = argparse.ArgumentParser(description="Smoke stack runtime verification gate")
    parser.add_argument(
        '--compose-file',
        type=Path,
        default=Path('docker-compose.smoke.yml'),
        help='Path to docker-compose.smoke.yml'
    )
    parser.add_argument(
        '--env-file',
        type=Path,
        default=Path('.env.smoke'),
        help='Path to .env.smoke'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('reports/g35'),
        help='Output directory for evidence'
    )
    parser.add_argument(
        '--max-retries',
        type=int,
        default=5,
        help='Max retries per service (default: 5)'
    )
    parser.add_argument(
        '--timeout',
        type=float,
        default=2.0,
        help='Timeout per probe in seconds (default: 2.0)'
    )

    args = parser.parse_args()

    # Resolve paths relative to repo root
    repo_root = Path(__file__).parent.parent
    compose_file = repo_root / args.compose_file
    env_file = repo_root / args.env_file
    output_dir = repo_root / args.output_dir

    # Run gate
    gate = RuntimeGate(
        compose_file=compose_file,
        env_file=env_file,
        output_dir=output_dir,
        max_retries=args.max_retries,
        timeout_per_probe=args.timeout
    )

    all_healthy, results = gate.run()

    # Exit code
    if all_healthy:
        print("✅ All services PASSED runtime gate")
        sys.exit(0)
    else:
        print("❌ One or more services FAILED runtime gate")
        print(f"📁 Evidence bundle: {output_dir}")
        sys.exit(1)


if __name__ == '__main__':
    main()
