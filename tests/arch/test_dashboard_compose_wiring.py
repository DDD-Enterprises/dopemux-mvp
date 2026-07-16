from pathlib import Path

import yaml

from shared.service_discovery import ServiceDiscovery


ROOT = Path(__file__).resolve().parents[2]


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _environment(values: list[str]) -> dict[str, str]:
    return dict(value.split("=", 1) for value in values)


def test_dashboard_compose_service_is_loopback_bound_and_dependency_complete():
    compose = _load_yaml(ROOT / "compose.yml")
    service = compose["services"]["adhd-dashboard"]

    assert service["build"] == {
        "context": ".",
        "dockerfile": "services/adhd-dashboard/Dockerfile",
    }
    assert service["ports"] == [
        "127.0.0.1:${ADHD_DASHBOARD_PORT:-8097}:8097"
    ]

    environment = _environment(service["environment"])
    engine_environment = _environment(
        compose["services"]["adhd-engine"]["environment"]
    )
    assert environment["REDIS_URL"] == "redis://redis-primary:6379"
    assert environment["ADHD_ENGINE_URL"] == "http://adhd-engine:8095"
    assert (
        environment["ADHD_ENGINE_REDIS_PREFIX"]
        == engine_environment["ADHD_ENGINE_REDIS_PREFIX"]
    )
    assert service["depends_on"]["redis-primary"]["condition"] == "service_healthy"
    assert service["depends_on"]["adhd-engine"]["condition"] == "service_healthy"
    assert service["healthcheck"]["test"][:2] == ["CMD", "python"]
    assert "urllib.request.urlopen" in service["healthcheck"]["test"][-1]


def test_dashboard_registry_entry_matches_compose_contract():
    registry = _load_yaml(ROOT / "services" / "registry.yaml")
    services = {service["name"]: service for service in registry["services"]}
    dashboard = services["adhd-dashboard"]

    assert dashboard["port"] == 8097
    assert dashboard["container_port"] == 8097
    assert dashboard["health_path"] == "/health"
    assert dashboard["compose_service_name"] == "adhd-dashboard"
    assert dashboard["category"] == "cognitive"
    assert dashboard["enabled_in_smoke"] is False


def test_dashboard_image_declares_runtime_dependencies():
    requirements = (
        ROOT / "services" / "adhd-dashboard" / "requirements.txt"
    ).read_text(encoding="utf-8").splitlines()

    assert any(requirement.startswith("rich>=") for requirement in requirements)
    assert any(
        requirement.startswith("websockets>=") for requirement in requirements
    )


def test_deleted_activity_capture_is_not_discoverable():
    discovery = ServiceDiscovery()

    assert "activity-capture" not in discovery.dns_mappings
    assert "activity-capture" not in discovery.default_ports
    assert discovery.default_ports["adhd-dashboard"] == 8097
