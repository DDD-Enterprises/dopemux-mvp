"""Static boundary contract for Task Orchestrator workflow persistence."""

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_PATH = REPO_ROOT / "compose.yml"
CONPORT_REST_URL = "http://conport:3004"
REQUIRED_BRIDGE_TOKEN = (
    "${DOPECON_BRIDGE_TOKEN:?DOPECON_BRIDGE_TOKEN must be set to an authenticated bridge JWT}"
)


def _service_environment(service_name: str) -> dict[str, str]:
    compose = yaml.safe_load(COMPOSE_PATH.read_text(encoding="utf-8"))
    raw_environment = compose["services"][service_name]["environment"]
    return dict(item.split("=", 1) for item in raw_environment)


def test_task_orchestrator_inherits_only_external_bridge_token() -> None:
    environment = _service_environment("task-orchestrator")

    assert environment["DOPECON_BRIDGE_TOKEN"] == REQUIRED_BRIDGE_TOKEN


def test_task_orchestrator_rest_client_targets_conport_rest_port() -> None:
    environment = _service_environment("task-orchestrator")

    assert environment["CONPORT_URL"] == CONPORT_REST_URL


def test_dopecon_bridge_proxy_targets_conport_rest_port() -> None:
    environment = _service_environment("dopecon-bridge")

    assert environment["CONPORT_URL"] == CONPORT_REST_URL
