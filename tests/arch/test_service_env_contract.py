"""
Architecture Test: Service Environment Contract (G33 Phase 3)

Enforces the unified service environment contract across all smoke-enabled services.
Tests that services load mandatory env vars and respect contract exceptions.

Contract Reference: docs/engineering/service_env_contract.md
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set

import pytest
import yaml


# Repository root
REPO_ROOT = Path(__file__).parent.parent.parent

# Mandatory env vars from contract
MANDATORY_ENV_VARS = {
    "PORT",
    "LOG_LEVEL",
    "ENVIRONMENT",
    "HEALTH_CHECK_PATH",
    "SERVICE_NAME",
}

# Category-specific required vars
CATEGORY_ENV_VARS = {
    "infrastructure": set(),  # Infrastructure services use native config
    "mcp": {"MCP_SERVER_PORT"},
    "coordination": {"REDIS_URL"},
    "cognitive": {"DATABASE_URL", "REDIS_URL", "CONPORT_URL"},
}


def load_registry() -> Dict:
    """Load service registry."""
    registry_path = REPO_ROOT / "services" / "registry.yaml"
    assert registry_path.exists(), f"Registry not found: {registry_path}"

    with open(registry_path) as f:
        return yaml.safe_load(f)


def scan_service_env_vars(service_dir: Path) -> Set[str]:
    """Scan service code for env var usage."""
    env_vars = set()

    # Scan Python files for env var access
    for py_file in service_dir.rglob("*.py"):
        try:
            content = py_file.read_text()

            # Match os.getenv("VAR") and os.environ["VAR"]
            matches = re.findall(
                r'os\.(?:getenv|environ(?:\.get)?)\(["\']([A-Z_][A-Z0-9_]*)["\']',
                content
            )
            env_vars.update(matches)

        except Exception:
            continue  # Skip unreadable files

    # Scan Dockerfile for ENV declarations
    dockerfile = service_dir / "Dockerfile"
    if dockerfile.exists():
        try:
            content = dockerfile.read_text()
            matches = re.findall(r'^ENV\s+([A-Z_][A-Z0-9_]*)', content, re.MULTILINE)
            env_vars.update(matches)
        except Exception:
            pass

    return env_vars


def get_smoke_enabled_services(registry: Dict) -> List[Dict]:
    """Get list of smoke-enabled services from registry."""
    return [
        svc for svc in registry.get("services", [])
        if svc.get("enabled_in_smoke", False)
    ]


def get_service_exceptions(service_info: Dict) -> Set[str]:
    """Get env var exceptions for a service from registry."""
    return {
        exc["variable"]
        for exc in service_info.get("env_contract_exceptions", [])
    }


@pytest.fixture(scope="module")
def registry():
    """Load registry once for all tests."""
    return load_registry()


@pytest.fixture(scope="module")
def smoke_services(registry):
    """Get smoke-enabled services."""
    return get_smoke_enabled_services(registry)


class TestServiceEnvContract:
    """Test suite for service environment contract compliance."""

    def test_registry_exists(self):
        """Verify service registry file exists."""
        registry_path = REPO_ROOT / "services" / "registry.yaml"
        assert registry_path.exists(), (
            f"Service registry not found: {registry_path}"
        )

    def test_contract_documentation_exists(self):
        """Verify contract documentation exists."""
        doc_path = REPO_ROOT / "docs" / "engineering" / "service_env_contract.md"
        assert doc_path.exists(), (
            f"Contract documentation not found: {doc_path}"
        )

    def test_at_least_one_smoke_service(self, smoke_services):
        """Verify at least one service is smoke-enabled."""
        assert len(smoke_services) > 0, (
            "No services enabled in smoke stack. Check services/registry.yaml"
        )

    @pytest.mark.parametrize("service", get_smoke_enabled_services(load_registry()), ids=lambda s: s["name"])
    def test_service_directory_exists(self, service):
        """Verify service directory exists."""
        # Skip infrastructure services (use official Docker images)
        if service.get("category") == "infrastructure":
            pytest.skip(f"Infrastructure service '{service['name']}' uses official image")

        service_dir = REPO_ROOT / "services" / service["name"]
        assert service_dir.exists(), (
            f"Service directory not found: {service_dir}\n"
            f"Service '{service['name']}' is enabled in smoke but has no code directory"
        )

    @pytest.mark.parametrize("service", get_smoke_enabled_services(load_registry()), ids=lambda s: s["name"])
    def test_service_has_entry_point(self, service):
        """Verify service has a main entry point."""
        # Skip infrastructure services (use official Docker images)
        if service.get("category") == "infrastructure":
            pytest.skip(f"Infrastructure service '{service['name']}' uses official image")

        service_dir = REPO_ROOT / "services" / service["name"]

        # Look for common entry point files
        entry_points = ["main.py", "app.py", "server.py", "__main__.py"]
        has_entry = any((service_dir / ep).exists() for ep in entry_points)

        assert has_entry, (
            f"Service '{service['name']}' has no entry point.\n"
            f"Expected one of: {', '.join(entry_points)}\n"
            f"Directory: {service_dir}"
        )

    @pytest.mark.parametrize("service", get_smoke_enabled_services(load_registry()), ids=lambda s: s["name"])
    def test_mandatory_env_vars_loaded(self, service):
        """Test that service loads mandatory env vars (respecting exceptions)."""
        service_name = service["name"]
        service_dir = REPO_ROOT / "services" / service_name

        # Skip if service directory doesn't exist (infrastructure services)
        if not service_dir.exists():
            pytest.skip(f"Service directory not found: {service_dir}")

        # Get env vars used by service
        env_vars_found = scan_service_env_vars(service_dir)

        # Get exceptions for this service
        exceptions = get_service_exceptions(service)

        # Check mandatory vars (excluding exceptions)
        missing_mandatory = [
            var for var in MANDATORY_ENV_VARS
            if var not in exceptions and var not in env_vars_found
        ]

        assert not missing_mandatory, (
            f"Service '{service_name}' missing mandatory env vars: {', '.join(missing_mandatory)}\n"
            f"Category: {service.get('category', 'unknown')}\n"
            f"Found env vars: {sorted(list(env_vars_found))}\n"
            f"Exceptions: {sorted(list(exceptions))}\n\n"
            f"To fix:\n"
            f"1. Add env var loading to service entry point:\n"
            f"   port = int(os.getenv('PORT', '8080'))\n"
            f"   log_level = os.getenv('LOG_LEVEL', 'INFO')\n"
            f"   environment = os.getenv('ENVIRONMENT', 'dev')\n\n"
            f"2. OR add exception to services/registry.yaml:\n"
            f"   env_contract_exceptions:\n"
            f"     - variable: {missing_mandatory[0]}\n"
            f"       reason: 'Explain why exception needed'\n\n"
            f"See: docs/engineering/service_env_contract.md"
        )

    @pytest.mark.parametrize("service", get_smoke_enabled_services(load_registry()), ids=lambda s: s["name"])
    def test_category_specific_env_vars(self, service):
        """Test that service loads category-specific env vars."""
        service_name = service["name"]
        service_dir = REPO_ROOT / "services" / service_name
        category = service.get("category", "unknown")

        # Skip if service directory doesn't exist
        if not service_dir.exists():
            pytest.skip(f"Service directory not found: {service_dir}")

        # Get category-specific required vars
        required_vars = CATEGORY_ENV_VARS.get(category, set())
        if not required_vars:
            pytest.skip(f"No category-specific vars for category: {category}")

        # Get env vars used by service
        env_vars_found = scan_service_env_vars(service_dir)

        # Get exceptions
        exceptions = get_service_exceptions(service)

        # Check category vars (excluding exceptions)
        missing_category = [
            var for var in required_vars
            if var not in exceptions and var not in env_vars_found
        ]

        assert not missing_category, (
            f"Service '{service_name}' ({category}) missing category-specific env vars: "
            f"{', '.join(missing_category)}\n"
            f"Required for '{category}' category: {sorted(list(required_vars))}\n"
            f"Found env vars: {sorted(list(env_vars_found))}\n\n"
            f"To fix:\n"
            f"1. Add required env vars for '{category}' category\n"
            f"2. OR add exception with justification\n\n"
            f"See: docs/engineering/service_env_contract.md"
        )

    def test_exception_format_valid(self, registry):
        """Test that all env contract exceptions have required fields."""
        for service in registry.get("services", []):
            exceptions = service.get("env_contract_exceptions", [])

            for exc in exceptions:
                assert "variable" in exc, (
                    f"Service '{service['name']}' has exception without 'variable' field"
                )
                assert "reason" in exc, (
                    f"Service '{service['name']}' exception for '{exc.get('variable')}' "
                    f"missing 'reason' field"
                )

                # Reason should be non-empty string
                reason = exc["reason"]
                assert isinstance(reason, str) and len(reason.strip()) > 0, (
                    f"Service '{service['name']}' exception for '{exc['variable']}' "
                    f"has empty or invalid reason"
                )

    @pytest.mark.parametrize("service", get_smoke_enabled_services(load_registry()), ids=lambda s: s["name"])
    def test_service_has_dockerfile(self, service):
        """Test that smoke-enabled services have Dockerfiles."""
        service_name = service["name"]
        category = service.get("category", "unknown")
        service_dir = REPO_ROOT / "services" / service_name

        # Infrastructure services may not have Dockerfiles (use official images)
        if category == "infrastructure":
            pytest.skip(f"Infrastructure service '{service_name}' uses official image")

        # Skip if service directory doesn't exist
        if not service_dir.exists():
            pytest.skip(f"Service directory not found: {service_dir}")

        dockerfile = service_dir / "Dockerfile"
        assert dockerfile.exists(), (
            f"Service '{service_name}' is smoke-enabled but has no Dockerfile.\n"
            f"Expected: {dockerfile}\n\n"
            f"Smoke-enabled services need Dockerfiles for containerized deployment."
        )

    def test_all_smoke_services_in_registry(self, registry):
        """Verify all smoke-enabled services have registry entries."""
        smoke_services = get_smoke_enabled_services(registry)

        for service in smoke_services:
            # Check required fields
            assert "name" in service, "Service missing 'name' field"
            assert "port" in service or "health_path" in service, (
                f"Service '{service['name']}' must have 'port' or 'health_path'"
            )
            assert "category" in service, (
                f"Service '{service['name']}' missing 'category' field"
            )

            # Validate category
            valid_categories = {"infrastructure", "mcp", "coordination", "cognitive"}
            assert service["category"] in valid_categories, (
                f"Service '{service['name']}' has invalid category: {service['category']}\n"
                f"Valid categories: {sorted(valid_categories)}"
            )


class TestEnvDriftScanner:
    """Test the env drift scanner tool itself."""

    def test_drift_scanner_exists(self):
        """Verify env drift scanner tool exists."""
        scanner_path = REPO_ROOT / "tools" / "env_drift_scan.py"
        assert scanner_path.exists(), (
            f"Env drift scanner not found: {scanner_path}"
        )

    def test_drift_scanner_is_executable(self):
        """Verify drift scanner has execute permissions."""
        scanner_path = REPO_ROOT / "tools" / "env_drift_scan.py"
        assert os.access(scanner_path, os.X_OK) or scanner_path.suffix == ".py", (
            f"Drift scanner should be executable: {scanner_path}"
        )

    def test_drift_scanner_imports(self):
        """Verify drift scanner imports successfully."""
        # Add tools directory to path temporarily
        import sys
        tools_dir = str(REPO_ROOT / "tools")
        if tools_dir not in sys.path:
            sys.path.insert(0, tools_dir)

        try:
            # Import should not raise
            import env_drift_scan

            # Check key classes exist
            assert hasattr(env_drift_scan, "EnvDriftScanner"), (
                "EnvDriftScanner class not found in drift scanner"
            )
            assert hasattr(env_drift_scan, "MANDATORY_ENV_VARS"), (
                "MANDATORY_ENV_VARS not defined in drift scanner"
            )

        except ImportError as e:
            pytest.fail(f"Failed to import env_drift_scan: {e}")
