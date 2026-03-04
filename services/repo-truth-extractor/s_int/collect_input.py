from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import sys
from typing import Any, Dict, Iterable, List, Optional, Sequence

if __package__ in {None, ""}:
    service_root = Path(__file__).resolve().parents[1]
    if str(service_root) not in sys.path:
        sys.path.insert(0, str(service_root))
    from s_int.s_int_paths import ensure_s_int_dirs
    from s_int.schema_validate import load_schema, validate_payload_or_raise
else:
    from .s_int_paths import ensure_s_int_dirs
    from .schema_validate import load_schema, validate_payload_or_raise

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None  # type: ignore[assignment]


TEXT_EXTENSIONS = {
    ".py",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".sh",
    ".env",
}
HOOK_TERMS = ("hook", "callback", "webhook", "retry", "escalate", "mcp", "tools/list")
CLI_NAMES = (
    ("gemini_cli", [".gemini", "gemini"]),
    ("claude_code", [".claude", ".claude.json", "claude"]),
    ("copilot_cli", [".github", "copilot"]),
    ("vibe_cli", [".vibe", "vibe"]),
)


def _is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS or path.name in {"Dockerfile", "compose.yml"}


def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _extract_env_names(text: str) -> List[str]:
    names = sorted(
        {
            token
            for token in re.findall(r"\b[A-Z][A-Z0-9_]{2,}\b", text)
            if not token.startswith("HTTP")
        }
    )
    return names


def _repo_text_files(repo_root: Path, roots: Sequence[str]) -> List[Path]:
    files: List[Path] = []
    for rel in roots:
        base = repo_root / rel
        if not base.exists():
            continue
        if base.is_file():
            if _is_text_file(base):
                files.append(base)
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file() and _is_text_file(path):
                files.append(path)
    return sorted(set(files), key=lambda p: str(p.relative_to(repo_root)))


def _hook_hits(repo_root: Path) -> List[Dict[str, Any]]:
    hits: List[Dict[str, Any]] = []
    for path in _repo_text_files(repo_root, ["docker", "services", ".claude", ".vibe", "src", "scripts", "config"]):
        text = _safe_read(path)
        if not text:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            lowered = line.lower()
            for term in HOOK_TERMS:
                if term in lowered:
                    hits.append(
                        {
                            "path": str(path.relative_to(repo_root)),
                            "line": line_no,
                            "term": term,
                            "excerpt": line.strip()[:200],
                        }
                    )
    return sorted(hits, key=lambda row: (row["path"], row["line"], row["term"]))


def _collect_cli_clients(repo_root: Path) -> List[Dict[str, Any]]:
    files = _repo_text_files(repo_root, [".claude", ".vibe", "scripts", "config", "src", "services", "docker"])
    rows: List[Dict[str, Any]] = []
    for cli_name, markers in CLI_NAMES:
        evidence_paths: List[str] = []
        env_names: List[str] = []
        for path in files:
            rel = str(path.relative_to(repo_root))
            lowered = rel.lower()
            text = _safe_read(path)
            if any(marker in lowered or marker in text.lower() for marker in markers):
                evidence_paths.append(rel)
                env_names.extend(_extract_env_names(text))
        rows.append(
            {
                "name": cli_name,
                "status": "observed" if evidence_paths else "UNKNOWN",
                "config_paths": sorted(set(evidence_paths)),
                "env_names": sorted(set(env_names)),
                "tool_discovery": "UNKNOWN",
                "auth_mode": "UNKNOWN",
                "notes": [] if evidence_paths else ["No repo-local evidence found."],
            }
        )
    return rows


def _parse_compose_services(path: Path, repo_root: Path) -> List[Dict[str, Any]]:
    if yaml is None:
        return []
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return []
    services = payload.get("services", {})
    if not isinstance(services, dict):
        return []
    rows: List[Dict[str, Any]] = []
    for name in sorted(services.keys()):
        entry = services[name]
        if not isinstance(entry, dict):
            continue
        env_names: List[str] = []
        raw_env = entry.get("environment")
        if isinstance(raw_env, dict):
            env_names.extend(str(key) for key in raw_env.keys())
        elif isinstance(raw_env, list):
            for row in raw_env:
                token = str(row).split("=", 1)[0].strip()
                if token:
                    env_names.append(token)
        rows.append(
            {
                "service_id": str(name),
                "source": str(path.relative_to(repo_root)),
                "entrypoints": [str(entry.get("command"))] if entry.get("command") else [],
                "config_paths": [str(path.relative_to(repo_root))],
                "ports": [str(port) for port in entry.get("ports", []) if isinstance(port, (str, int))],
                "env_names": sorted(set(env_names)),
                "dependencies": sorted(str(dep) for dep in entry.get("depends_on", []) if dep),
            }
        )
    return rows


def _collect_service_inventory(repo_root: Path) -> List[Dict[str, Any]]:
    rows: Dict[str, Dict[str, Any]] = {}
    services_root = repo_root / "services"
    if services_root.exists():
        for child in sorted(p for p in services_root.iterdir() if p.is_dir()):
            files = [path for path in sorted(child.rglob("*")) if path.is_file() and _is_text_file(path)]
            env_names: List[str] = []
            config_paths: List[str] = []
            entrypoints: List[str] = []
            for path in files:
                rel = str(path.relative_to(repo_root))
                config_paths.append(rel)
                env_names.extend(_extract_env_names(_safe_read(path)))
                if path.name in {"main.py", "app.py", "server.py", "Dockerfile"} or path.name.startswith("run_"):
                    entrypoints.append(rel)
            rows[str(child.name)] = {
                "service_id": str(child.name),
                "source": str(child.relative_to(repo_root)),
                "entrypoints": sorted(set(entrypoints)),
                "config_paths": sorted(set(config_paths)),
                "ports": [],
                "env_names": sorted(set(env_names)),
                "dependencies": [],
            }

    compose_candidates = [
        path
        for path in sorted(repo_root.glob("*.yml")) + sorted(repo_root.glob("*.yaml"))
        if "compose" in path.name
    ]
    compose_candidates.extend(
        path
        for path in _repo_text_files(repo_root, ["docker"])
        if "compose" in path.name and path.suffix.lower() in {".yml", ".yaml"}
    )
    for compose_path in sorted(set(compose_candidates)):
        for row in _parse_compose_services(compose_path, repo_root):
            service_id = row["service_id"]
            if service_id not in rows:
                rows[service_id] = row
                continue
            rows[service_id]["config_paths"] = sorted(set(rows[service_id]["config_paths"] + row["config_paths"]))
            rows[service_id]["entrypoints"] = sorted(set(rows[service_id]["entrypoints"] + row["entrypoints"]))
            rows[service_id]["ports"] = sorted(set(rows[service_id]["ports"] + row["ports"]))
            rows[service_id]["env_names"] = sorted(set(rows[service_id]["env_names"] + row["env_names"]))
            rows[service_id]["dependencies"] = sorted(set(rows[service_id]["dependencies"] + row["dependencies"]))

    return [rows[key] for key in sorted(rows)]


def _collect_mcp_servers(repo_root: Path) -> List[Dict[str, Any]]:
    candidates: Dict[str, Dict[str, Any]] = {}
    for path in _repo_text_files(repo_root, ["docker", "services", ".claude", ".vibe", "config", "scripts"]):
        rel = str(path.relative_to(repo_root))
        text = _safe_read(path)
        lowered = f"{rel.lower()}\n{text.lower()}"
        if "mcp" not in lowered and "tools/list" not in lowered:
            continue
        key = rel.replace("/", "__")
        transport = "UNKNOWN"
        if "stdio" in lowered:
            transport = "stdio"
        elif "sse" in lowered or "http" in lowered:
            transport = "http"
        env_names = _extract_env_names(text)
        candidates[key] = {
            "id": key,
            "path": rel,
            "transport": transport,
            "command_or_endpoint": "UNKNOWN",
            "env_names": env_names,
            "tool_list": "UNKNOWN",
            "health": "UNKNOWN",
        }
    return [candidates[key] for key in sorted(candidates)]


def collect_input_payload(repo_root: Path, run_id: str) -> Dict[str, Any]:
    return {
        "schema_version": "S_INT_INPUT_V1",
        "run_id": str(run_id),
        "repo_root": str(repo_root.resolve()),
        "repo_layout": {
            "services_root": str((repo_root / "services").resolve()),
            "docker_root": str((repo_root / "docker").resolve()),
            "claude_root": str((repo_root / ".claude").resolve()),
            "vibe_root": str((repo_root / ".vibe").resolve()),
        },
        "cli_clients": _collect_cli_clients(repo_root),
        "mcp_servers": _collect_mcp_servers(repo_root),
        "services": _collect_service_inventory(repo_root),
        "hook_surfaces": _hook_hits(repo_root),
    }


def collect_input_bundle(repo_root: Path, run_id: str, out_root: Optional[Path] = None) -> Dict[str, Any]:
    dirs = ensure_s_int_dirs(repo_root, run_id, out_root=out_root)
    payload = collect_input_payload(repo_root, run_id)
    schema = load_schema(Path(__file__).resolve().parent / "schema_input.json")
    validate_payload_or_raise(payload, schema, label="S_INT_INPUT")

    dirs["raw"].mkdir(parents=True, exist_ok=True)
    (dirs["raw"] / "cli_clients.json").write_text(
        json.dumps(payload["cli_clients"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (dirs["raw"] / "mcp_servers.json").write_text(
        json.dumps(payload["mcp_servers"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (dirs["raw"] / "services.json").write_text(
        json.dumps(payload["services"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (dirs["raw"] / "hook_surfaces.json").write_text(
        json.dumps(payload["hook_surfaces"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    dirs["input"].write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser("S_INT input collector")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--repo-root", type=str, default=".")
    parser.add_argument("--out-root", type=str, default="")
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    out_root = Path(args.out_root).resolve() if str(args.out_root).strip() else None
    payload = collect_input_bundle(repo_root, args.run_id, out_root=out_root)
    print(json.dumps({"status": "OK", "output": str((out_root or (repo_root / 'proof' / 's_int')).resolve())}))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
