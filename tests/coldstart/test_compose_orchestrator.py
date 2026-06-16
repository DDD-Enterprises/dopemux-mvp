import subprocess
from pathlib import Path

from dopemux.coldstart.compose_orchestrator import ComposeOrchestrator


def completed(stdout: str = "", returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["docker"], returncode, stdout=stdout, stderr="")


def test_bring_up_invokes_docker_compose_with_profile_and_env_file(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def runner(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return completed()

    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_API_KEY=test\n", encoding="utf-8")
    compose_file = tmp_path / "compose.yml"
    compose_file.write_text("services: {}\n", encoding="utf-8")

    orchestrator = ComposeOrchestrator(runner=runner, env_file=env_file)
    orchestrator.bring_up(compose_file, profile="full", env={"A": "B"})

    assert calls == [
        [
            "docker",
            "compose",
            "--env-file",
            str(env_file),
            "--profile",
            "full",
            "-f",
            str(compose_file),
            "up",
            "-d",
        ]
    ]


def test_wait_healthy_returns_false_on_timeout() -> None:
    calls = 0

    def runner(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        nonlocal calls
        calls += 1
        return completed("svc unhealthy\n")

    orchestrator = ComposeOrchestrator(runner=runner, sleeper=lambda _: None, monotonic_values=iter([0, 1, 3]))

    assert orchestrator.wait_healthy(["svc"], timeout_s=2, interval_s=1) is False
    assert calls >= 1


def test_wait_healthy_ignores_compose_ps_header() -> None:
    output = (
        "NAME      IMAGE     COMMAND   SERVICE   CREATED   STATUS                 PORTS\n"
        "api       image     cmd       api       now       Up 3 seconds (healthy) 8080/tcp\n"
        "worker    image     cmd       worker    now       Up 3 seconds (healthy)\n"
    )

    def runner(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return completed(output)

    orchestrator = ComposeOrchestrator(runner=runner, sleeper=lambda _: None, monotonic_values=iter([0, 1]))

    assert orchestrator.wait_healthy(["api", "worker"], timeout_s=2, interval_s=1) is True


def test_wait_healthy_matches_compose_service_column_exactly() -> None:
    output = (
        "NAME        IMAGE     COMMAND   SERVICE     CREATED   STATUS                 PORTS\n"
        "pal-stdio   image     cmd       pal-stdio   now       Up 3 seconds (healthy)\n"
    )

    def runner(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return completed(output)

    orchestrator = ComposeOrchestrator(runner=runner, sleeper=lambda _: None, monotonic_values=iter([0, 1, 3]))

    assert orchestrator.wait_healthy(["pal"], timeout_s=2, interval_s=1) is False
