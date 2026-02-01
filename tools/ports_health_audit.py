#!/usr/bin/env python3
"""
Ports and Health Audit Tool

Validates that services/registry.yaml, docker-compose.smoke.yml, and runtime all agree
on ports and health endpoints.

Usage:
    # Static validation (no runtime required)
    python tools/ports_health_audit.py --mode static

    # Runtime health checks
    python tools/ports_health_audit.py --mode runtime

    # Explain drift between registry and compose
    python tools/ports_health_audit.py --mode static --explain-drift

    # Check specific services
    python tools/ports_health_audit.py --mode runtime --services conport,dopecon-bridge
"""
import argparse
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)


class RegistryLoader:
    """Load and parse registry.yaml."""
    
    def __init__(self, registry_path: Path):
        self.registry_path = registry_path
        self.registry = self._load()
    
    def _load(self) -> Dict[str, Any]:
        if not self.registry_path.exists():
            print(f"ERROR: Registry not found at {self.registry_path}", file=sys.stderr)
            sys.exit(1)
        
        with open(self.registry_path) as f:
            return yaml.safe_load(f)
    
    def get_services(self, smoke_only: bool = False) -> List[Dict[str, Any]]:
        """Get services from registry."""
        services = self.registry.get("services", [])
        if smoke_only:
            return [s for s in services if s.get("enabled_in_smoke", False)]
        return services
    
    def get_service(self, name: str) -> Optional[Dict[str, Any]]:
        """Get specific service by name."""
        for svc in self.get_services():
            if svc["name"] == name:
                return svc
        return None


class ComposeLoader:
    """Load and parse docker-compose.smoke.yml."""
    
    def __init__(self, compose_path: Path):
        self.compose_path = compose_path
        self.compose = self._load()
    
    def _load(self) -> Dict[str, Any]:
        if not self.compose_path.exists():
            print(f"WARNING: Compose file not found at {self.compose_path}", file=sys.stderr)
            return {"services": {}}
        
        with open(self.compose_path) as f:
            return yaml.safe_load(f)
    
    def get_service_ports(self, service_name: str) -> List[str]:
        """Get published ports for a service."""
        services = self.compose.get("services", {})
        if service_name not in services:
            return []
        
        ports = services[service_name].get("ports", [])
        return ports


class StaticValidator:
    """Validate registry completeness and detect drift with compose."""
    
    def __init__(self, registry: RegistryLoader, compose: ComposeLoader):
        self.registry = registry
        self.compose = compose
        self.issues = []
    
    def validate(self, explain_drift: bool = False) -> bool:
        """Run static validation."""
        print("🔍 Static Validation")
        print("=" * 60)
        
        smoke_services = self.registry.get_services(smoke_only=True)
        print(f"Services enabled in smoke stack: {len(smoke_services)}")
        print()
        
        all_valid = True
        
        for svc in smoke_services:
            name = svc["name"]
            valid = self._validate_service(svc)
            all_valid = all_valid and valid
        
        if explain_drift:
            self._explain_drift()
        
        return all_valid
    
    def _validate_service(self, svc: Dict[str, Any]) -> bool:
        """Validate a single service has required fields."""
        name = svc["name"]
        issues = []
        
        # Check required fields
        if "port" not in svc:
            issues.append("Missing 'port' field")
        if svc.get("health_path") is None and svc.get("category") not in ["infrastructure"]:
            issues.append("Missing 'health_path' field")
        
        if issues:
            print(f"❌ {name}: {', '.join(issues)}")
            self.issues.extend([(name, issue) for issue in issues])
            return False
        else:
            print(f"✅ {name}: port={svc['port']}, health={svc.get('health_path', 'N/A')}")
            return True
    
    def _explain_drift(self):
        """Explain drift between registry and compose."""
        print()
        print("🔄 Drift Analysis")
        print("=" * 60)
        
        smoke_services = self.registry.get_services(smoke_only=True)
        drift_found = False
        
        for svc in smoke_services:
            name = svc["name"]
            compose_name = svc.get("compose_service_name", name)
            
            # Get compose ports
            compose_ports = self.compose.get_service_ports(compose_name)
            
            if not compose_ports:
                print(f"⚠️  {name}: Not found in docker-compose.smoke.yml")
                drift_found = True
                continue
            
            # Parse first port mapping (host:container)
            registry_port = svc["port"]
            registry_container_port = svc.get("container_port", registry_port)
            
            # Check if ports match
            expected_mapping = f"{registry_port}:{registry_container_port}"
            actual_mapping = compose_ports[0] if compose_ports else "None"
            
            # Handle env var placeholders in compose
            if "${" in actual_mapping:
                print(f"ℹ️  {name}: Using env vars - {actual_mapping} (expected {expected_mapping})")
            elif actual_mapping.replace("${", "").replace("}", "") == expected_mapping:
                print(f"✅ {name}: Ports aligned - {expected_mapping}")
            else:
                print(f"❌ {name}: Drift detected!")
                print(f"   Registry: {expected_mapping}")
                print(f"   Compose:  {actual_mapping}")
                drift_found = True
        
        if not drift_found:
            print("✅ No drift detected between registry and compose")


class RuntimeHealthChecker:
    """Check service health at runtime."""
    
    def __init__(self, registry: RegistryLoader):
        self.registry = registry
    
    def check(self, service_filter: Optional[List[str]] = None) -> bool:
        """Run runtime health checks."""
        print("🏥 Runtime Health Checks")
        print("=" * 60)
        
        smoke_services = self.registry.get_services(smoke_only=True)
        
        if service_filter:
            smoke_services = [s for s in smoke_services if s["name"] in service_filter]
        
        if not smoke_services:
            print("No services to check")
            return True
        
        all_healthy = True
        results = []
        
        for svc in smoke_services:
            status, msg = self._check_service(svc)
            results.append((svc["name"], status, msg))
            all_healthy = all_healthy and status
        
        # Print summary
        print()
        print("Summary:")
        print("-" * 60)
        for name, status, msg in results:
            symbol = "✅" if status else "❌"
            print(f"{symbol} {name:20s} {msg}")
        
        return all_healthy
    
    def _check_service(self, svc: Dict[str, Any]) -> Tuple[bool, str]:
        """Check health of a single service."""
        name = svc["name"]
        health_path = svc.get("health_path")
        
        # Infrastructure services use command-based health checks
        if not health_path:
            return True, "SKIP (infrastructure)"
        
        port = svc["port"]
        timeout_ms = svc.get("health_timeout_ms", 5000)
        expected_status = svc.get("health_expected_status", 200)
        
        url = f"http://localhost:{port}{health_path}"
        
        try:
            resp = requests.get(url, timeout=timeout_ms / 1000)
            if resp.status_code == expected_status:
                return True, f"UP (HTTP {resp.status_code})"
            else:
                return False, f"UNHEALTHY (HTTP {resp.status_code}, expected {expected_status})"
        except requests.exceptions.ConnectionError:
            return False, f"DOWN (connection refused on :{port})"
        except requests.exceptions.Timeout:
            return False, f"TIMEOUT (>{timeout_ms}ms)"
        except Exception as e:
            return False, f"ERROR ({type(e).__name__})"


def main():
    parser = argparse.ArgumentParser(description="Audit service ports and health endpoints")
    parser.add_argument(
        "--mode",
        choices=["static", "runtime"],
        required=True,
        help="Validation mode"
    )
    parser.add_argument(
        "--explain-drift",
        action="store_true",
        help="Show drift between registry and compose (static mode)"
    )
    parser.add_argument(
        "--services",
        help="Comma-separated list of services to check (runtime mode)"
    )
    parser.add_argument(
        "--registry",
        default="services/registry.yaml",
        help="Registry file path"
    )
    parser.add_argument(
        "--compose",
        default="docker-compose.smoke.yml",
        help="Compose file path"
    )
    args = parser.parse_args()
    
    # Resolve paths
    repo_root = Path(__file__).parent.parent
    registry_path = repo_root / args.registry
    compose_path = repo_root / args.compose
    
    # Load registry
    registry = RegistryLoader(registry_path)
    
    # Run validation based on mode
    if args.mode == "static":
        compose = ComposeLoader(compose_path)
        validator = StaticValidator(registry, compose)
        success = validator.validate(explain_drift=args.explain_drift)
    else:  # runtime
        service_filter = args.services.split(",") if args.services else None
        checker = RuntimeHealthChecker(registry)
        success = checker.check(service_filter)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
