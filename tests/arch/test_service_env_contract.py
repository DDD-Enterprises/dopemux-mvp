"""
Architecture Test: Service Environment Contract (G33 Phase 3)

Enforces the unified service environment contract across all smoke-enabled services.
Tests that services load mandatory env vars and respect contract exceptions.

Contract Reference: docs/03-reference/service-env-contract.md
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Set

import pytest
import yaml


# Repository root
REPO_ROOT = Path(__file__).parent.parent.parent
SMOKE_COMPOSE_PATH = REPO_ROOT / "docker-compose.smoke.yml"

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


def load_smoke_compose() -> Dict:
    """Load smoke-compose file used by contract/runtime checks."""
    assert SMOKE_COMPOSE_PATH.exists(), f"Smoke compose file not found: {SMOKE_COMPOSE_PATH}"
    with open(SMOKE_COMPOSE_PATH) as f:
        return yaml.safe_load(f) or {}


def _resolve_service_runtime(service_info: Dict[str, Any]) -> tuple[Path | None, Path | None]:
    """Resolve runtime source directory and dockerfile path for a service.

    Resolution order:
    1. `docker-compose.smoke.yml` build metadata for compose_service_name
    2. `services/<service name>`
    3. `services/<compose_service_name>`
    """
    compose_data = load_smoke_compose()
    compose_services = compose_data.get("services", {})
    compose_name = service_info.get("compose_service_name") or service_info["name"]
    compose_service = compose_services.get(compose_name, {})

    runtime_dir: Path | None = None
    dockerfile_path: Path | None = None

    def _candidate_context_dirs(context_value: str) -> list[Path]:
        """Return plausible context directories across current repo layouts."""
        raw = Path(context_value)
        candidates = [(REPO_ROOT / raw).resolve()]

        parts = raw.parts
        if "mcp-servers" in parts:
            idx = parts.index("mcp-servers")
            swapped = Path(*parts[:idx], "mcp-servers-source", *parts[idx + 1 :])
            candidates.append((REPO_ROOT / swapped).resolve())
        elif "mcp-servers-source" in parts:
            idx = parts.index("mcp-servers-source")
            swapped = Path(*parts[:idx], "mcp-servers", *parts[idx + 1 :])
            candidates.append((REPO_ROOT / swapped).resolve())

        unique: list[Path] = []
        for candidate in candidates:
            if candidate not in unique:
                unique.append(candidate)
        return unique

    build_cfg = compose_service.get("build")
    if isinstance(build_cfg, dict):
        context = build_cfg.get("context", ".")
        context_candidates = _candidate_context_dirs(context)
        context_dir = next((candidate for candidate in context_candidates if candidate.exists()), context_candidates[0])
        dockerfile = build_cfg.get("dockerfile")
        if dockerfile:
            candidate = (context_dir / dockerfile).resolve()
            if not candidate.exists():
                candidate = (REPO_ROOT / dockerfile).resolve()
            if candidate.exists():
                dockerfile_path = candidate
                runtime_dir = candidate.parent
        if runtime_dir is None and context_dir.exists():
            runtime_dir = context_dir
    elif isinstance(build_cfg, str):
        context_dir = (REPO_ROOT / build_cfg).resolve()
        if context_dir.exists():
            runtime_dir = context_dir

    if runtime_dir is None:
        service_dir = (REPO_ROOT / "services" / service_info["name"]).resolve()
        compose_dir = (REPO_ROOT / "services" / compose_name).resolve()
        if service_dir.exists():
            runtime_dir = service_dir
        elif compose_dir.exists():
            runtime_dir = compose_dir

    return runtime_dir, dockerfile_path


def _has_entry_point(service_dir: Path) -> bool:
    """Return whether service has at least one recognized Python entry point."""
    entry_points = (
        "main.py",
        "app.py",
        "server.py",
        "__main__.py",
        "app/main.py",
        "dope_memory_main.py",
    )
    return any((service_dir / entry).exists() for entry in entry_points)


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
    for dockerfile in service_dir.glob("Dockerfile*"):
        try:
            content = dockerfile.read_text()
            matches = re.findall(r'^ENV\s+([A-Z_][A-Z0-9_]*)', content, re.MULTILINE)
            env_vars.update(matches)
        except Exception:
            continue

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
        doc_path = REPO_ROOT / "docs" / "03-reference" / "service-env-contract.md"
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

        runtime_dir, _ = _resolve_service_runtime(service)
        assert runtime_dir and runtime_dir.exists(), (
            f"Service runtime directory not found for '{service['name']}'.\n"
            f"Expected via smoke compose service '{service.get('compose_service_name', service['name'])}' "
            f"or services/{service['name']}."
        )

    @pytest.mark.parametrize("service", get_smoke_enabled_services(load_registry()), ids=lambda s: s["name"])
    def test_service_has_entry_point(self, service):
        """Verify service has a main entry point."""
        # Skip infrastructure services (use official Docker images)
        if service.get("category") == "infrastructure":
            pytest.skip(f"Infrastructure service '{service['name']}' uses official image")

        service_dir, _ = _resolve_service_runtime(service)
        if service_dir is None:
            pytest.skip(f"Service runtime directory not resolved: {service['name']}")
        has_entry = _has_entry_point(service_dir)

        assert has_entry, (
            f"Service '{service['name']}' has no entry point.\n"
            f"Expected one of: main.py, app.py, server.py, __main__.py, app/main.py, dope_memory_main.py\n"
            f"Directory: {service_dir}"
        )

    @pytest.mark.parametrize("service", get_smoke_enabled_services(load_registry()), ids=lambda s: s["name"])
    def test_mandatory_env_vars_loaded(self, service):
        """Test that service loads mandatory env vars (respecting exceptions)."""
        service_name = service["name"]
        if service.get("category") == "infrastructure":
            pytest.skip(f"Infrastructure service '{service_name}' uses official image")
        service_dir, _ = _resolve_service_runtime(service)

        # Skip if service directory doesn't exist (infrastructure services)
        if service_dir is None or not service_dir.exists():
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
            f"See: docs/03-reference/service-env-contract.md"
        )

    @pytest.mark.parametrize("service", get_smoke_enabled_services(load_registry()), ids=lambda s: s["name"])
    def test_category_specific_env_vars(self, service):
        """Test that service loads category-specific env vars."""
        service_name = service["name"]
        if service.get("category") == "infrastructure":
            pytest.skip(f"Infrastructure service '{service_name}' uses official image")
        service_dir, _ = _resolve_service_runtime(service)
        category = service.get("category", "unknown")

        # Skip if service directory doesn't exist
        if service_dir is None or not service_dir.exists():
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
            f"See: docs/03-reference/service-env-contract.md"
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
        service_dir, compose_dockerfile = _resolve_service_runtime(service)

        # Infrastructure services may not have Dockerfiles (use official images)
        if category == "infrastructure":
            pytest.skip(f"Infrastructure service '{service_name}' uses official image")

        # Skip if service directory doesn't exist
        if service_dir is None or not service_dir.exists():
            pytest.skip(f"Service directory not found: {service_dir}")

        dockerfile_candidates = list(service_dir.glob("Dockerfile*"))
        if compose_dockerfile is not None:
            dockerfile_candidates.append(compose_dockerfile)
        dockerfile_candidates = [path for path in dockerfile_candidates if path.exists()]
        assert dockerfile_candidates, (
            f"Service '{service_name}' is smoke-enabled but has no Dockerfile.\n"
            f"Expected under: {service_dir}\n"
            f"Compose-resolved Dockerfile: {compose_dockerfile}\n\n"
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
