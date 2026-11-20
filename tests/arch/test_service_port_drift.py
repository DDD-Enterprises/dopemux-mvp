"""
Architecture Test: Service Port Drift

services/registry.yaml is the source of truth for service ports. This test
checks that the other places that carry a port agree with it:

- mcp_catalog.yaml (reserved_port, default_port_base, or the port in url)
- compose.yml host ports (non-smoke services; smoke services are covered by
  test_registry_compose_alignment.py)
- hard-coded localhost / 127.0.0.1 URLs in a few scripts and modules
- the Dope layout defaults in src/dopemux/config/manager.py
- DEFAULT_ADHD_ENGINE_PORT in dopemux.commands.adhd_commands

Known, accepted differences live in EXCEPTIONS. Each entry needs a reason and
a follow_up, and test_no_stale_exceptions fails when an entry no longer
matches a live difference, so the table cannot rot.

Static parsing only; nothing here starts a service.
"""

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pytest

yaml = pytest.importorskip("yaml")

from dopemux.commands.adhd_commands import DEFAULT_ADHD_ENGINE_PORT  # noqa: E402
from tests.arch.test_registry_compose_alignment import (  # noqa: E402
    load_compose,
    load_registry,
    parse_port_mapping,
)

REPO_ROOT = Path(__file__).parent.parent.parent
CATALOG_PATH = REPO_ROOT / "mcp_catalog.yaml"
MANAGER_REL = "src/dopemux/config/manager.py"

SCANNED_FILES = [
    MANAGER_REL,
    "scripts/dopemux_dashboard.py",
    ".claude/statusline.sh",
    "mcp_server_health_report.sh",
    "scripts/mcp_health_check.sh",
    "src/dopemux/ui/service_endpoints.py",
    "src/dopemux/profile_detector.py",
]

LITERAL_RE = re.compile(r"(?:localhost|127\.0\.0\.1):(\d{2,5})\b")
ENV_DEFAULT_RE = re.compile(r"\$\{[^:}]+:-(\d+)\}")
URL_PORT_RE = re.compile(r"(?:localhost|127\.0\.0\.1):(?:\$\{[^:}]+:-)?(\d{2,5})\b")

# (config key on a line in manager.py, registry service name)
NAMED_DEFAULTS = {
    "adhd_engine_url": "adhd-engine",
    "leantime_url": "leantime",
    "serena_url": "serena",
    "litellm_url": "litellm",
}

# Known, accepted differences. Every entry needs a reason and a follow_up.
# Keys: ("catalog", service_name), ("compose", service_name), ("literal", (file, port)).
EXCEPTIONS: Dict[Tuple[str, Any], Dict[str, str]] = {
    ("catalog", "task-orchestrator"): {
        "reason": (
            "Two processes share the name: the Python orchestrator on 8000 "
            "(registry) and the Kotlin MCP server on 7890 (catalog)."
        ),
        "follow_up": "Map item S2 (task-orchestrator identity split).",
    },
    ("compose", "dopecon-bridge-alt"): {
        "reason": (
            "Registry alt entry says 3000; its compose service dopecon-bridge "
            "publishes only 3016."
        ),
        "follow_up": "Decide whether the alt entry is retired or gets a compose mapping.",
    },
    ("literal", ("scripts/dopemux_dashboard.py", 8095)): {
        "reason": "Stale script uses the adhd-engine container port, not the host port.",
        "follow_up": "Retire or repair scripts/dopemux_dashboard.py.",
    },
    ("literal", ("scripts/dopemux_dashboard.py", 8005)): {
        "reason": "Same script; ConPort port that appears in no registry or compose entry.",
        "follow_up": "Retire or repair scripts/dopemux_dashboard.py.",
    },
    ("literal", ("scripts/dopemux_dashboard.py", 8003)): {
        "reason": "Same script; Serena port that appears in no registry or compose entry.",
        "follow_up": "Retire or repair scripts/dopemux_dashboard.py.",
    },
}


def test_exceptions_are_documented() -> None:
    for key, entry in EXCEPTIONS.items():
        assert entry.get("reason"), f"EXCEPTIONS{key} has no reason"
        assert entry.get("follow_up"), f"EXCEPTIONS{key} has no follow_up"


# ---------------------------------------------------------------- helpers


def _registry_services() -> List[Dict[str, Any]]:
    return load_registry().get("services", [])


def _registry_ports() -> Dict[str, int]:
    return {s["name"]: s["port"] for s in _registry_services()}


def _load_catalog() -> Dict[str, Any]:
    assert CATALOG_PATH.exists(), f"Catalog not found: {CATALOG_PATH}"
    with open(CATALOG_PATH) as f:
        return yaml.safe_load(f)


def _port_from_url(value: str) -> Optional[int]:
    """Port in a URL; `${VAR:-N}` resolves to N."""
    match = re.search(r":(?:\$\{[^:}]+:-)?(\d{2,5})(?:\}|\b)", value)
    return int(match.group(1)) if match else None


def _catalog_port(entry: Dict[str, Any]) -> Optional[int]:
    """reserved_port, else default_port_base, else the port in url/url_template."""
    for key in ("reserved_port", "default_port_base"):
        if isinstance(entry.get(key), int):
            return entry[key]
    for key in ("url", "url_template"):
        if isinstance(entry.get(key), str):
            port = _port_from_url(entry[key])
            if port is not None:
                return port
    return None


def _catalog_ports() -> Dict[str, int]:
    servers = _load_catalog().get("servers", {})
    ports = {}
    for name, entry in servers.items():
        port = _catalog_port(entry or {})
        if port is not None:
            ports[name] = port
    return ports


def _all_catalog_port_values() -> Set[int]:
    """Every port the catalog mentions, including aux_surfaces URLs."""
    found: Set[int] = set(_catalog_ports().values())

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key in ("reserved_port", "default_port_base"):
                if isinstance(node.get(key), int):
                    found.add(node[key])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
        elif isinstance(node, str):
            found.update(int(m) for m in URL_PORT_RE.findall(node))

    walk(_load_catalog().get("servers", {}))
    return found


def _compose_host_ports(compose_svc: Dict[str, Any]) -> List[int]:
    ports = []
    for item in compose_svc.get("ports", []) or []:
        if isinstance(item, str):
            parsed = parse_port_mapping(item)
            if parsed:
                ports.append(parsed[0])
        elif isinstance(item, dict) and item.get("published") is not None:
            published = str(item["published"])
            published = ENV_DEFAULT_RE.sub(r"\1", published)
            if published.isdigit():
                ports.append(int(published))
    return ports


def _catalog_differences() -> Dict[str, Tuple[int, int]]:
    catalog = _catalog_ports()
    registry = _registry_ports()
    return {
        name: (registry[name], catalog[name])
        for name in sorted(set(registry) & set(catalog))
        if registry[name] != catalog[name]
    }


def _compose_differences() -> Tuple[Dict[str, Tuple[int, List[int]]], List[str]]:
    """Return ({service: (registry port, compose host ports)}, not-comparable notes)."""
    compose_services = load_compose().get("services", {})
    differences: Dict[str, Tuple[int, List[int]]] = {}
    not_comparable: List[str] = []
    for svc in _registry_services():
        if svc.get("enabled_in_smoke", False):
            continue
        name = svc["name"]
        compose_name = svc.get("compose_service_name", name)
        compose_svc = compose_services.get(compose_name)
        if compose_svc is None:
            # Reported by _missing_compose_services(); a failure, not a note.
            continue
        if compose_svc.get("network_mode"):
            not_comparable.append(f"{name}: compose service uses network_mode")
            continue
        host_ports = _compose_host_ports(compose_svc)
        if not host_ports:
            not_comparable.append(f"{name}: compose service publishes no host ports")
            continue
        if svc["port"] not in host_ports:
            differences[name] = (svc["port"], host_ports)
    return differences, not_comparable


def _missing_compose_services() -> List[Tuple[str, str]]:
    """(registry service, compose name) for non-smoke services absent from compose.yml."""
    compose_services = load_compose().get("services", {})
    return [
        (svc["name"], svc.get("compose_service_name", svc["name"]))
        for svc in _registry_services()
        if not svc.get("enabled_in_smoke", False)
        and svc.get("compose_service_name", svc["name"]) not in compose_services
    ]


def _literal_hits() -> Dict[Tuple[str, int], List[str]]:
    """Map (file, port) -> 'line N' locations for localhost:PORT literals."""
    known = set(_registry_ports().values()) | _all_catalog_port_values()
    hits: Dict[Tuple[str, int], List[str]] = {}
    for rel in SCANNED_FILES:
        path = REPO_ROOT / rel
        assert path.exists(), f"Scanned file missing: {rel} (update SCANNED_FILES)"
        for lineno, line in enumerate(path.read_text().splitlines(), start=1):
            for match in LITERAL_RE.findall(line):
                port = int(match)
                if port not in known:
                    hits.setdefault((rel, port), []).append(f"line {lineno}")
    return hits


# ------------------------------------------------------------------ tests


def test_registry_matches_catalog() -> None:
    problems = []
    for name, (reg, cat) in _catalog_differences().items():
        if ("catalog", name) in EXCEPTIONS:
            continue
        problems.append(
            f"{name}: services/registry.yaml port={reg} but mcp_catalog.yaml "
            f"port={cat} (rule: registry port must equal the catalog's "
            "reserved_port / default_port_base / url port). Fix the wrong file, "
            "or add an EXCEPTIONS entry with a reason and follow_up."
        )
    assert not problems, "Registry/catalog port drift:\n  - " + "\n  - ".join(problems)


def test_registry_matches_compose_for_non_smoke() -> None:
    differences, not_comparable = _compose_differences()
    for note in not_comparable:
        print(f"not comparable: {note}")
    problems = []
    for name, (reg, host_ports) in differences.items():
        if ("compose", name) in EXCEPTIONS:
            continue
        problems.append(
            f"{name}: services/registry.yaml port={reg} is not among the compose.yml "
            f"host ports {host_ports} (rule: a non-smoke registry port must be "
            "published by its compose service). Fix the wrong file, or add an "
            "EXCEPTIONS entry with a reason and follow_up."
        )
    assert not problems, "Registry/compose port drift:\n  - " + "\n  - ".join(problems)


def test_registry_services_exist_in_compose() -> None:
    problems = [
        f"{name}: services/registry.yaml names compose service {compose_name!r} "
        "but compose.yml has no such service (rule: a non-smoke registry service "
        "must exist in compose.yml; set compose_service_name or fix the registry)."
        for name, compose_name in _missing_compose_services()
    ]
    assert (
        not problems
    ), "Registry services missing from compose:\n  - " + "\n  - ".join(problems)


def test_missing_compose_service_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sys.modules[__name__],
        "_registry_services",
        lambda: [
            {"name": "ghost", "port": 1234, "compose_service_name": "ghost-compose"},
            {"name": "plain", "port": 1235},
            {"name": "smoke", "port": 1236, "enabled_in_smoke": True},
        ],
    )
    monkeypatch.setattr(
        sys.modules[__name__], "load_compose", lambda: {"services": {"smoke": {}}}
    )
    assert _missing_compose_services() == [
        ("ghost", "ghost-compose"),
        ("plain", "plain"),
    ]


def test_no_unknown_port_literals() -> None:
    problems = []
    for (rel, port), locations in sorted(_literal_hits().items()):
        if ("literal", (rel, port)) in EXCEPTIONS:
            continue
        problems.append(
            f"{rel}: localhost port {port} ({', '.join(locations)}) is in no "
            "registry or catalog entry (rule: hard-coded localhost ports must be "
            "a services/registry.yaml or mcp_catalog.yaml port). Use the right "
            "port, or add an EXCEPTIONS entry with a reason and follow_up."
        )
    assert not problems, "Unknown port literals:\n  - " + "\n  - ".join(problems)


def test_named_defaults_match_registry() -> None:
    registry = _registry_ports()
    lines = (REPO_ROOT / MANAGER_REL).read_text().splitlines()
    problems = []
    for key, service in NAMED_DEFAULTS.items():
        found = 0
        for lineno, line in enumerate(lines, start=1):
            if key not in line:
                continue
            match = LITERAL_RE.search(line)
            if not match:
                continue
            found += 1
            if int(match.group(1)) != registry[service]:
                problems.append(
                    f"{MANAGER_REL}:{lineno}: {key} uses port {match.group(1)} but "
                    f"services/registry.yaml {service} port is {registry[service]} "
                    "(rule: Dope layout service defaults must use the registry port)."
                )
        if not found:
            problems.append(
                f"{MANAGER_REL}: no line defining {key} with a localhost URL was "
                "found; update NAMED_DEFAULTS if the setting was renamed."
            )
    assert not problems, "Stale named defaults:\n  - " + "\n  - ".join(problems)


def test_cli_default_port_matches_registry() -> None:
    expected = _registry_ports()["adhd-engine"]
    assert DEFAULT_ADHD_ENGINE_PORT == expected, (
        "src/dopemux/commands/adhd_commands.py DEFAULT_ADHD_ENGINE_PORT="
        f"{DEFAULT_ADHD_ENGINE_PORT} but services/registry.yaml adhd-engine "
        f"port={expected} (rule: the CLI default must equal the registry port)."
    )


def test_no_stale_exceptions() -> None:
    live: Set[Tuple[str, Any]] = set()
    live.update(("catalog", name) for name in _catalog_differences())
    live.update(("compose", name) for name in _compose_differences()[0])
    live.update(("literal", key) for key in _literal_hits())
    stale = [key for key in EXCEPTIONS if key not in live]
    assert not stale, (
        "EXCEPTIONS entries that no longer match a live difference (remove them): "
        + ", ".join(str(key) for key in stale)
    )
