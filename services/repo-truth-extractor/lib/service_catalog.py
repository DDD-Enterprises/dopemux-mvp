import json
import yaml
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

# Constants moved from run_extraction_v4.py or defined here
ROOT = Path(__file__).resolve().parents[3]
SERVICES_REGISTRY = ROOT / "services" / "registry.yaml"
COMPOSE_FILES = [
    ROOT / "compose.yml",
    ROOT / "docker-compose.dev.yml",
    ROOT / "docker-compose.prod.yml",
    ROOT / "docker-compose.smoke.yml",
]

def read_yaml(path: Path) -> Any:
    if not path.exists():
        return {}
    return yaml.safe_all_load(path.read_text(encoding="utf-8")) if hasattr(yaml, "safe_all_load") else yaml.safe_load(path.read_text(encoding="utf-8"))

def repo_relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)

def evidence_for(path: Path, needle: str, fallback_excerpt: str = "") -> Dict[str, Any]:
    # Placeholder for the evidence_for logic from the original script
    # In a real refactor, we would import this from a common utility lib
    return {
        "path": repo_relative(path),
        "line_range": [1, 1], # Placeholder
        "excerpt": fallback_excerpt or needle,
    }

def normalize_evidence(evidence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: Set[Tuple[str, int, int, str]] = set()
    unique: List[Dict[str, Any]] = []
    for item in evidence:
        key = (
            str(item.get("path", "")),
            int(item.get("line_range", [0, 0])[0]),
            int(item.get("line_range", [0, 0])[1]),
            str(item.get("excerpt", "")),
        )
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique

def _depends_on_names(depends_on: Any) -> List[str]:
    if isinstance(depends_on, dict):
        return sorted(str(k) for k in depends_on.keys())
    if isinstance(depends_on, list):
        return sorted(str(v) for v in depends_on)
    return []

def _env_required_from_expr(expr: str) -> bool:
    text = str(expr or "").strip()
    if not text:
        return False
    # Simple heuristic: if it has a default value or is optional in shell style
    if ":-" in text or ":?" in text:
        return False
    return True

def _extract_env_rows(env: Any) -> List[Tuple[str, bool, str]]:
    rows: List[Tuple[str, bool, str]] = []
    if isinstance(env, dict):
        for k, v in env.items():
            name = str(k).strip()
            required = _env_required_from_expr(str(v)) if v is not None else True
            rows.append((name, required, f"{name}={v}" if v is not None else name))
    elif isinstance(env, list):
        for item in env:
            text = str(item).strip()
            if "=" in text:
                name, value = text.split("=", 1)
                name = name.strip()
                required = _env_required_from_expr(value)
            else:
                name = text
                required = True
            if not name:
                continue
            rows.append((name, required, text))
    return rows

def load_compose_surface() -> Dict[str, Dict[str, Any]]:
    surface: Dict[str, Dict[str, Any]] = {}
    for compose_file in COMPOSE_FILES:
        if not compose_file.exists():
            continue
        # Use simple safe_load for single document compose files
        with open(compose_file, "r", encoding="utf-8") as f:
            payload = yaml.safe_load(f)
        services = payload.get("services", {})
        if not isinstance(services, dict):
            continue
        for compose_service_name, service_cfg in services.items():
            if not isinstance(service_cfg, dict):
                continue
            name = str(compose_service_name).strip()
            if not name:
                continue
            slot = surface.setdefault(
                name,
                {
                    "depends_on": {},
                    "entrypoints": {},
                    "env_vars": {},
                    "config_files": set(),
                },
            )
            slot["config_files"].add(repo_relative(compose_file))

            for dep_name in _depends_on_names(service_cfg.get("depends_on")):
                slot["depends_on"][dep_name] = evidence_for(
                    compose_file,
                    dep_name,
                    fallback_excerpt=f"depends_on: {dep_name}",
                )

            for key in ("entrypoint", "command"):
                value = service_cfg.get(key)
                if value in (None, "", []):
                    continue
                if isinstance(value, list):
                    text = " ".join(str(item) for item in value if str(item).strip()).strip()
                else:
                    text = str(value).strip()
                if not text:
                    continue
                entry_key = f"{key}:{text}"
                slot["entrypoints"][entry_key] = {
                    "type": key,
                    "value": text,
                    "evidence": [evidence_for(compose_file, key, fallback_excerpt=f"{key}: {text}")],
                }

            for env_name, required, needle in _extract_env_rows(service_cfg.get("environment")):
                previous = slot["env_vars"].get(env_name)
                evidence = evidence_for(compose_file, needle, fallback_excerpt=needle)
                if previous is None:
                    slot["env_vars"][env_name] = {
                        "name": env_name,
                        "required": bool(required),
                        "evidence": [evidence],
                    }
                    continue
                previous["required"] = bool(previous.get("required", False) or required)
                previous["evidence"] = normalize_evidence(list(previous.get("evidence", [])) + [evidence])

    return surface

def build_service_catalog() -> Dict[str, Any]:
    with open(SERVICES_REGISTRY, "r", encoding="utf-8") as f:
        payload = yaml.safe_load(f)
    services = payload.get("services", [])
    compose_surface = load_compose_surface()
    compose_to_registry: Dict[str, str] = {}
    for row in services if isinstance(services, list) else []:
        if not isinstance(row, dict):
            continue
        service_id = str(row.get("name", "")).strip()
        if not service_id:
            continue
        compose_name = str(row.get("compose_service_name", "") or service_id).strip()
        if compose_name:
            compose_to_registry[compose_name] = service_id

    items: List[Dict[str, Any]] = []
    for row in services if isinstance(services, list) else []:
        if not isinstance(row, dict):
            continue
        service_id = str(row.get("name", "")).strip()
        if not service_id:
            continue
        compose_name = str(row.get("compose_service_name", "") or service_id).strip()
        compose_info = compose_surface.get(compose_name, {})
        locations: List[str] = []
        for candidate in [f"services/{service_id}", f"services/{compose_name}"]:
            if (ROOT / candidate).exists():
                locations.append(candidate)

        entrypoints = sorted(
            compose_info.get("entrypoints", {}).values(),
            key=lambda value: (str(value.get("type", "")), str(value.get("value", ""))),
        )
        if not entrypoints:
            entrypoints = [
                {
                    "type": "compose_service_name",
                    "value": compose_name,
                    "evidence": [evidence_for(SERVICES_REGISTRY, f"name: {service_id}", fallback_excerpt=f"name: {service_id}")],
                }
            ]

        interfaces: List[Dict[str, Any]] = []
        health_path = row.get("health_path")
        health_method = row.get("health_method")
        if health_path not in (None, ""):
            interfaces.append(
                {
                    "kind": "http",
                    "method": str(health_method or "GET"),
                    "path": str(health_path),
                    "evidence": [evidence_for(SERVICES_REGISTRY, f"name: {service_id}", fallback_excerpt=f"name: {service_id}")],
                }
            )
        port = row.get("port")
        if port not in (None, ""):
            interfaces.append(
                {
                    "kind": "tcp",
                    "port": int(port),
                    "evidence": [evidence_for(SERVICES_REGISTRY, f"name: {service_id}", fallback_excerpt=f"name: {service_id}")],
                }
            )
        category = str(row.get("category", "")).strip() or "unknown"
        if category == "mcp":
            interfaces.append(
                {
                    "kind": "mcp",
                    "protocol": "sse_or_stdio",
                    "tool_names": [],
                    "evidence": [evidence_for(SERVICES_REGISTRY, f"name: {service_id}", fallback_excerpt=f"name: {service_id}")],
                }
            )
        interfaces.sort(
            key=lambda value: (
                str(value.get("kind", "")),
                str(value.get("path", "")),
                str(value.get("port", "")),
                str(value.get("method", "")),
            )
        )

        dependencies: List[Dict[str, Any]] = []
        dep_map = compose_info.get("depends_on", {})
        if isinstance(dep_map, dict):
            for dep_compose in sorted(dep_map.keys()):
                dependency_service = compose_to_registry.get(dep_compose, dep_compose)
                dependency_value = {
                    "kind": "compose_depends_on",
                    "service_id": dependency_service,
                    "compose_service_name": dep_compose,
                    "evidence": [dep_map[dep_compose]],
                }
                dependencies.append(dependency_value)

        env_vars: List[Dict[str, Any]] = []
        env_map = compose_info.get("env_vars", {})
        if isinstance(env_map, dict):
            for env_name in sorted(env_map.keys()):
                env_row = env_map[env_name]
                env_vars.append(
                    {
                        "name": env_row.get("name", env_name),
                        "required": bool(env_row.get("required", False)),
                        "evidence": normalize_evidence(list(env_row.get("evidence", []))),
                    }
                )

        config_files: List[Dict[str, Any]] = []
        for config_rel in sorted(compose_info.get("config_files", set())):
            config_path = ROOT / config_rel
            config_files.append(
                {
                    "path": config_rel,
                    "evidence": [evidence_for(config_path, compose_name, fallback_excerpt=compose_name)],
                }
            )
        for local_candidate in [f"services/{service_id}/.env.example", f"services/{compose_name}/.env.example"]:
            full = ROOT / local_candidate
            if not full.exists():
                continue
            config_files.append(
                {
                    "path": local_candidate,
                    "evidence": [evidence_for(full, "", fallback_excerpt=local_candidate)],
                }
            )
        dedup_config: Dict[str, Dict[str, Any]] = {}
        for row_config in config_files:
            dedup_config[row_config["path"]] = row_config
        config_files = [dedup_config[key] for key in sorted(dedup_config.keys())]

        description = str(row.get("description", "")).strip() or f"Service {service_id} (description missing in registry)"

        item = {
            "id": f"SERVICE:{service_id}",
            "service_id": service_id,
            "category": category,
            "description": description,
            "ports": {
                "container_port": row.get("container_port"),
                "port": row.get("port"),
            },
            "health": {
                "expected_status": row.get("health_expected_status"),
                "method": row.get("health_method"),
                "path": row.get("health_path"),
                "timeout_ms": row.get("health_timeout_ms"),
            },
            "repo_locations": sorted(locations),
            "entrypoints": entrypoints,
            "interfaces": interfaces,
            "dependencies": dependencies,
            "config": {
                "env_vars": env_vars,
                "config_files": config_files,
                "env_contract_exceptions": row.get("env_contract_exceptions", []),
                "enabled_in_smoke": row.get("enabled_in_smoke"),
            },
            "evidence": [
                evidence_for(SERVICES_REGISTRY, f"name: {service_id}", fallback_excerpt=f"name: {service_id}")
            ],
        }
        items.append(item)
    items.sort(key=lambda r: r["service_id"])
    return {"schema": "SERVICE_CATALOG@v1", "items": items}
