"""
Architecture Test: Registry ↔ Compose Alignment

Ensures that services/registry.yaml and docker-compose.smoke.yml stay in sync.
This prevents silent drift where registry says one port but compose uses another.

Fails loudly if:
- A smoke-enabled service is missing from compose
- Ports don't match between registry and compose
- Service names don't match

No runtime imports - pure static parsing only.
"""
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pytest

try:
    import yaml
except ImportError:
    pytest.skip("pyyaml required for registry tests", allow_module_level=True)


# Paths relative to repo root
REPO_ROOT = Path(__file__).parent.parent.parent
REGISTRY_PATH = REPO_ROOT / "services" / "registry.yaml"
COMPOSE_PATH = REPO_ROOT / "docker-compose.smoke.yml"


def load_registry() -> Dict[str, Any]:
    """Load registry.yaml."""
    assert REGISTRY_PATH.exists(), f"Registry not found: {REGISTRY_PATH}"
    with open(REGISTRY_PATH) as f:
        return yaml.safe_load(f)


def load_compose() -> Dict[str, Any]:
    """Load docker-compose.smoke.yml."""
    assert COMPOSE_PATH.exists(), f"Compose file not found: {COMPOSE_PATH}"
    with open(COMPOSE_PATH) as f:
        return yaml.safe_load(f)


def get_smoke_services(registry: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get services enabled in smoke stack."""
    services = registry.get("services", [])
    return [s for s in services if s.get("enabled_in_smoke", False)]


def parse_port_mapping(port_str: str) -> Optional[tuple[int, int]]:
    """
    Parse docker port mapping string to (host_port, container_port).
    
    Handles:
    - "3004:3004"
    - "${CONPORT_PORT:-3004}:${CONPORT_CONTAINER_PORT:-3004}"
    - "${CONPORT_PORT:-3004}:3004"
    """
    # Remove env var syntax and extract default values
    cleaned = re.sub(r'\$\{[^:}]+:-([0-9]+)\}', r'\1', port_str)
    cleaned = re.sub(r'\$\{[^}]+\}', '', cleaned)  # Remove remaining vars
    
    parts = cleaned.split(":")
    if len(parts) != 2:
        return None
    
    try:
        host_port = int(parts[0])
        container_port = int(parts[1])
        return (host_port, container_port)
    except ValueError:
        return None


class TestRegistryComposeAlignment:
    """Test that registry and compose stay aligned."""
    
    def test_registry_exists(self):
        """Registry file must exist."""
        assert REGISTRY_PATH.exists(), f"Registry not found at {REGISTRY_PATH}"
    
    def test_compose_exists(self):
        """Smoke compose file must exist."""
        assert COMPOSE_PATH.exists(), f"Compose file not found at {COMPOSE_PATH}"
    
    def test_registry_has_services(self):
        """Registry must define services."""
        registry = load_registry()
        assert "services" in registry, "Registry missing 'services' key"
        assert len(registry["services"]) > 0, "Registry has no services"
    
    def test_smoke_services_exist_in_compose(self):
        """All smoke-enabled services must exist in compose."""
        registry = load_registry()
        compose = load_compose()
        
        smoke_services = get_smoke_services(registry)
        compose_services = set(compose.get("services", {}).keys())
        
        missing = []
        for svc in smoke_services:
            compose_name = svc.get("compose_service_name", svc["name"])
            if compose_name not in compose_services:
                missing.append(svc["name"])
        
        assert not missing, f"Smoke services missing from compose: {missing}"
    
    def test_port_alignment(self):
        """Registry and compose must agree on port mappings."""
        registry = load_registry()
        compose = load_compose()
        
        smoke_services = get_smoke_services(registry)
        compose_services = compose.get("services", {})
        
        mismatches = []
        
        for svc in smoke_services:
            name = svc["name"]
            compose_name = svc.get("compose_service_name", name)
            
            if compose_name not in compose_services:
                continue  # Caught by previous test
            
            # Get registry ports
            registry_host_port = svc["port"]
            registry_container_port = svc.get("container_port", registry_host_port)
            
            # Get compose ports
            compose_svc = compose_services[compose_name]
            compose_ports = compose_svc.get("ports", [])
            
            if not compose_ports:
                mismatches.append(
                    f"{name}: No ports exposed in compose (expected {registry_host_port}:{registry_container_port})"
                )
                continue
            
            # Parse first port mapping
            port_mapping = parse_port_mapping(compose_ports[0])
            
            if not port_mapping:
                mismatches.append(
                    f"{name}: Could not parse compose port: {compose_ports[0]}"
                )
                continue
            
            compose_host, compose_container = port_mapping
            
            # Check alignment
            if compose_host != registry_host_port:
                mismatches.append(
                    f"{name}: Host port mismatch - registry={registry_host_port}, compose={compose_host}"
                )
            
            if compose_container != registry_container_port:
                mismatches.append(
                    f"{name}: Container port mismatch - registry={registry_container_port}, compose={compose_container}"
                )
        
        if mismatches:
            msg = "Port alignment issues:\n" + "\n".join(f"  - {m}" for m in mismatches)
            pytest.fail(msg)
    
    def test_required_fields_present(self):
        """All smoke services must have required registry fields."""
        registry = load_registry()
        smoke_services = get_smoke_services(registry)
        
        required_fields = ["name", "port"]
        missing = []
        
        for svc in smoke_services:
            for field in required_fields:
                if field not in svc:
                    missing.append(f"{svc.get('name', 'UNKNOWN')}: missing '{field}'")
        
        assert not missing, f"Services missing required fields:\n" + "\n".join(f"  - {m}" for m in missing)
    
    def test_health_endpoints_defined(self):
        """Non-infrastructure smoke services must have health endpoints."""
        registry = load_registry()
        smoke_services = get_smoke_services(registry)
        
        missing_health = []
        
        for svc in smoke_services:
            category = svc.get("category", "")
            health_path = svc.get("health_path")
            
            # Infrastructure services can skip health_path (use command checks)
            if category == "infrastructure":
                continue
            
            if not health_path:
                missing_health.append(svc["name"])
        
        assert not missing_health, f"Services missing health_path: {missing_health}"
    
    def test_no_hardcoded_ports_in_compose(self):
        """
        Compose should use env vars for ports, not hardcoded values.
        This test is informational - warns if env vars are missing.
        """
        compose = load_compose()
        services = compose.get("services", {})
        
        hardcoded = []
        
        for svc_name, svc_config in services.items():
            ports = svc_config.get("ports", [])
            for port in ports:
                # If it's a plain string like "3004:3004" instead of "${VAR:-3004}:3004"
                if isinstance(port, str) and "${" not in port:
                    hardcoded.append(f"{svc_name}: {port}")
        
        # This is a warning, not a hard failure (some services like postgres might be hardcoded)
        if hardcoded:
            import warnings
            warnings.warn(f"Hardcoded ports found (consider using env vars):\n" + "\n".join(f"  - {h}" for h in hardcoded))
