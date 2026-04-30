from __future__ import annotations

import re
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_ORCHESTRATOR_PORT = 8000


def _read_text(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_task_orchestrator_dockerfile_uses_supported_runtime_and_port() -> None:
    dockerfile = _read_text("services/task-orchestrator/Dockerfile")

    assert '"app.main:app"' in dockerfile
    assert "task_orchestrator.app:app" not in dockerfile
    assert re.search(r"\bPORT=8000\b", dockerfile)
    assert "EXPOSE 8000" in dockerfile
    assert "http://localhost:8000/health" in dockerfile
    assert (
        'CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]'
        in dockerfile
    )


def test_task_orchestrator_app_default_port_matches_runtime_config() -> None:
    app_main = _read_text("services/task-orchestrator/app/main.py")
    unsupported_runtime = _read_text("services/task-orchestrator/task_orchestrator/app.py")

    assert f"DEFAULT_PORT = {TASK_ORCHESTRATOR_PORT}" in app_main
    assert 'os.getenv("PORT", str(DEFAULT_PORT))' in app_main
    assert "3014" not in app_main
    assert "app/main.py (Port 8000)" in unsupported_runtime
    assert "app/main.py (Port 3014)" not in unsupported_runtime


def test_task_orchestrator_compose_and_registry_ports_are_single_valued() -> None:
    compose = yaml.safe_load(_read_text("compose.yml"))
    registry = yaml.safe_load(_read_text("services/registry.yaml"))

    compose_service = compose["services"]["task-orchestrator"]
    registry_service = next(
        service
        for service in registry["services"]
        if service["name"] == "task-orchestrator"
    )

    assert compose_service["ports"] == ["${TASK_ORCHESTRATOR_PORT:-8000}:8000"]
    assert f"PORT={TASK_ORCHESTRATOR_PORT}" in compose_service["environment"]
    assert registry_service["port"] == TASK_ORCHESTRATOR_PORT
    assert registry_service["container_port"] == TASK_ORCHESTRATOR_PORT
