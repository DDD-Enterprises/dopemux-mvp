import subprocess

from dopemux.coldstart.network import ensure_docker_networks


def completed(stdout: str = "", returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["docker"], returncode, stdout=stdout, stderr="")


def test_ensure_docker_networks_creates_missing_networks() -> None:
    calls: list[list[str]] = []

    def runner(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        if args[:3] == ["docker", "network", "ls"]:
            return completed("dopemux-network\n")
        return completed()

    ensure_docker_networks(["dopemux-network", "mcp-network"], runner=runner)

    assert ["docker", "network", "create", "mcp-network"] in calls
    assert ["docker", "network", "create", "dopemux-network"] not in calls


def test_ensure_docker_networks_is_idempotent_when_network_exists() -> None:
    calls: list[list[str]] = []

    def runner(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return completed("dopemux-network\nmcp-network\n")

    ensure_docker_networks(["dopemux-network", "mcp-network"], runner=runner)

    assert calls == [["docker", "network", "ls", "--format", "{{.Name}}"]]
