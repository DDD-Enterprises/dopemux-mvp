#!/usr/bin/env python3
"""Extract dependency and environment-variable artifacts for Codex setup.

The script scans repo manifests and docs, then writes normalized, deterministic
artifacts under ``scripts/env_outputs/`` by default.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - defensive fallback
    import tomli as tomllib  # type: ignore[no-redef]


IGNORED_PARTS = {
    ".git",
    ".venv",
    ".worktrees",
    ".claude",
    "__pycache__",
    "build",
    "dist",
    "env_outputs",
    "node_modules",
    "reports",
    "archive",
    "SYSTEM_ARCHIVE",
    "quarantine",
}

ENV_NAME_PATTERN = (
    r"(?:[A-Z][A-Z0-9_]*_[A-Z0-9_]+|HOME|LANG|LOGNAME|PATH|PWD|SHELL|TEMP|TERM|TMP|"
    r"TMPDIR|USER|USERPROFILE|XDG_CONFIG_HOME)"
)
ENV_ASSIGNMENT_RE = re.compile(
    rf"^\s*(?:export\s+)?({ENV_NAME_PATTERN})\s*=\s*(.*?)\s*(?:#.*)?$"
)
ENV_GETENV_RE = re.compile(rf"""os\.getenv\(\s*['"]({ENV_NAME_PATTERN})['"]""")
ENV_FIELD_RE = re.compile(rf"""env\s*=\s*['"]({ENV_NAME_PATTERN})['"]""")
ENV_REF_RE = re.compile(rf"\$(?:\{{)?({ENV_NAME_PATTERN})(?:\}})?")
ENV_TOKEN_RE = re.compile(rf"\b{ENV_NAME_PATTERN}\b")
ENV_PREFIX_HINTS = (
    "ADHD_",
    "AGE_",
    "ALTP_",
    "ANTHROPIC_",
    "API_",
    "ATTENTION_",
    "AUTO_",
    "AZURE_",
    "BACKUP_",
    "BATCH_",
    "CACHE_",
    "CALDAV_",
    "CCR_",
    "CLAUDE_",
    "CONPORT_",
    "CONTEXT7_",
    "CORS_",
    "CODEX_",
    "CUSTOM_",
    "DASHBOARD_",
    "DB_",
    "DD_",
    "DEEPSEEK_",
    "DESKTOP_",
    "DIAL_",
    "DOPECON_",
    "DOPEMUX_",
    "ENVIRONMENT",
    "FRONTEND_",
    "GEMINI_",
    "GITHUB_",
    "GROQ_",
    "HOST_",
    "LEANTIME_",
    "LOG_",
    "MCP_",
    "MINIO_",
    "MYSQL_",
    "OPENAI_",
    "OPENROUTER_",
    "QDRANT_",
    "REDIS_",
    "SERENA_",
    "TASK_",
    "TASK_ORCHESTRATOR_",
    "TAVILY_",
    "VOYAGE_",
    "WORKSPACE_",
    "XAI_",
)
ENV_SUFFIX_HINTS = (
    "API_KEY",
    "BASE_URL",
    "COUNT",
    "DATABASE",
    "DIR",
    "ENABLED",
    "ENDPOINT",
    "ENV",
    "ENVIRONMENT",
    "ECHO",
    "FILE",
    "FLAGS",
    "HOST",
    "ID",
    "INTERVAL",
    "KEY",
    "LEVEL",
    "LIMIT",
    "MODE",
    "NAME",
    "ORIGINS",
    "PASSWORD",
    "PATH",
    "PORT",
    "POOL_MAX",
    "POOL_MIN",
    "POOL_SIZE",
    "ROOT",
    "SECONDS",
    "SECRET",
    "SIZE",
    "SSLMODE",
    "STATE",
    "STATUS",
    "THRESHOLD",
    "TIMEOUT",
    "TOKEN",
    "TTL",
    "TYPE",
    "URL",
    "URLS",
    "USER",
    "VERSION",
    "WEBHOOK",
    "WORKSPACE",
)

SAFE_DEFAULT_PATTERNS = (
    re.compile(r"^https?://localhost(?::\d+)?(?:/.*)?$", re.IGNORECASE),
    re.compile(r"^(true|false|0|1|\d+)$", re.IGNORECASE),
    re.compile(r"^[a-z][a-z0-9._-]*$"),
)
PLACEHOLDER_HINTS = (
    "your_",
    "your-",
    "your key",
    "replace",
    "placeholder",
    "secret",
    "token here",
    "<",
    "changeme",
)


@dataclass(frozen=True)
class DependencyRecord:
    ecosystem: str
    display: str
    sources: tuple[str, ...]


@dataclass
class EnvRecord:
    name: str
    sources: set[str] = field(default_factory=set)
    explicit_required: bool = False
    explicit_optional: bool = False
    example_values: set[str] = field(default_factory=set)


def _is_ignored(path: Path, root: Path) -> bool:
    rel_parts = path.relative_to(root).parts
    return any(part in IGNORED_PARTS for part in rel_parts)


def _iter_files(root: Path, names: Sequence[str]) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file() or _is_ignored(path, root):
            continue
        if path.name in names:
            yield path


def _iter_requirement_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("requirements*.txt")):
        if not path.is_file() or _is_ignored(path, root):
            continue
        yield path


def _normalize_comment_free_line(line: str) -> str:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return ""
    if stripped.startswith("-r ") or stripped.startswith("--"):
        return ""
    if " #" in stripped:
        stripped = stripped.split(" #", 1)[0].rstrip()
    return stripped


def _dependency_display_from_requirement(raw: str) -> str:
    return " ".join(raw.split())


def _collect_pyproject_dependencies(path: Path) -> List[str]:
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    project = payload.get("project", {})
    deps: List[str] = []

    for dependency in project.get("dependencies", []) or []:
        if isinstance(dependency, str):
            deps.append(_dependency_display_from_requirement(dependency))

    optional = project.get("optional-dependencies", {}) or {}
    for _, dependency_list in sorted(optional.items(), key=lambda item: item[0]):
        for dependency in dependency_list or []:
            if isinstance(dependency, str):
                deps.append(_dependency_display_from_requirement(dependency))

    tool = payload.get("tool", {})
    poetry = tool.get("poetry", {}) if isinstance(tool, dict) else {}
    poetry_deps = poetry.get("dependencies", {}) if isinstance(poetry, dict) else {}
    if isinstance(poetry_deps, dict):
        for name, spec in sorted(poetry_deps.items(), key=lambda item: item[0]):
            if name.lower() == "python":
                continue
            if isinstance(spec, str):
                deps.append(
                    f"{name}{spec if spec.startswith(('>', '<', '=', '!', '~')) else f'=={spec}'}"
                )
            elif isinstance(spec, dict):
                version = spec.get("version")
                extras = spec.get("extras", [])
                extra_suffix = f"[{','.join(extras)}]" if extras else ""
                if version:
                    deps.append(f"{name}{extra_suffix}{version}")
                else:
                    deps.append(f"{name}{extra_suffix}")

    return deps


def _collect_requirements_dependencies(path: Path) -> List[str]:
    deps: List[str] = []
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = _normalize_comment_free_line(raw_line)
        if not line:
            continue
        deps.append(_dependency_display_from_requirement(line))
    return deps


def _collect_package_json_dependencies(path: Path) -> List[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    deps: List[str] = []
    for key in ("dependencies", "devDependencies", "optionalDependencies"):
        block = payload.get(key, {})
        if not isinstance(block, dict):
            continue
        for name, version in sorted(block.items(), key=lambda item: item[0]):
            deps.append(f"{name}@{version}")
    return deps


def discover_dependency_manifests(root: Path) -> List[Path]:
    manifests: List[Path] = []
    manifests.extend(_iter_files(root, ("pyproject.toml", "package.json")))
    manifests.extend(_iter_requirement_files(root))
    return sorted({path.resolve() for path in manifests})


def _dependency_key(ecosystem: str, display: str) -> tuple[str, str]:
    return ecosystem, display


def extract_dependencies(root: Path) -> List[DependencyRecord]:
    records: Dict[tuple[str, str], set[str]] = {}

    for manifest in discover_dependency_manifests(root):
        rel_source = manifest.relative_to(root).as_posix()
        if manifest.name == "pyproject.toml":
            for dependency in _collect_pyproject_dependencies(manifest):
                records.setdefault(_dependency_key("python", dependency), set()).add(rel_source)
        elif manifest.name == "package.json":
            for dependency in _collect_package_json_dependencies(manifest):
                records.setdefault(_dependency_key("node", dependency), set()).add(rel_source)
        elif manifest.name.startswith("requirements") and manifest.suffix == ".txt":
            for dependency in _collect_requirements_dependencies(manifest):
                records.setdefault(_dependency_key("python", dependency), set()).add(rel_source)

    return [
        DependencyRecord(ecosystem=ecosystem, display=display, sources=tuple(sorted(sources)))
        for (ecosystem, display), sources in sorted(records.items(), key=lambda item: item[0])
    ]


def _looks_placeholder(value: str) -> bool:
    candidate = value.strip().strip('"').strip("'")
    if not candidate:
        return True
    lowered = candidate.lower()
    return any(hint in lowered for hint in PLACEHOLDER_HINTS)


def _looks_safe_default(value: str) -> bool:
    candidate = value.strip().strip('"').strip("'")
    return any(pattern.match(candidate) for pattern in SAFE_DEFAULT_PATTERNS)


def _is_env_candidate(name: str) -> bool:
    if name in {"HOME", "LANG", "LOGNAME", "PATH", "PWD", "SHELL", "TEMP", "TERM", "TMP", "TMPDIR", "USER", "USERPROFILE", "XDG_CONFIG_HOME"}:
        return True
    if name.startswith(ENV_PREFIX_HINTS):
        return True
    return name.endswith(ENV_SUFFIX_HINTS)


def _extract_env_names_from_line(
    line: str,
    *,
    allow_assignments: bool,
    allow_generic_tokens: bool,
) -> set[str]:
    names: set[str] = set()
    if allow_assignments:
        for match in ENV_ASSIGNMENT_RE.finditer(line):
            names.add(match.group(1))
    for match in ENV_GETENV_RE.finditer(line):
        names.add(match.group(1))
    for match in ENV_FIELD_RE.finditer(line):
        names.add(match.group(1))
    for match in ENV_REF_RE.finditer(line):
        names.add(match.group(1))
    if allow_generic_tokens and any(
        marker in line for marker in ("Required:", "Optional:", "export ", "API key", "Field(", "env=")
    ):
        names.update(ENV_TOKEN_RE.findall(line))
    return names


def discover_env_sources(root: Path) -> List[Path]:
    candidates: List[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or _is_ignored(path, root):
            continue
        if (
            path.name == ".env"
            or path.name.startswith(".env.")
            or path.name.endswith(".env")
            or path.name.endswith(".env.example")
            or path.name.endswith(".env.template")
        ):
            candidates.append(path)
            continue
        if path.suffix.lower() in {".md", ".txt", ".py", ".yml", ".yaml", ".json", ".sh"}:
            candidates.append(path)
    return candidates


def extract_env_vars(root: Path) -> Dict[str, EnvRecord]:
    records: Dict[str, EnvRecord] = {}

    for path in discover_env_sources(root):
        rel_source = path.relative_to(root).as_posix()
        allow_python_style = path.suffix.lower() in {".py", ".pyi"}
        allow_assignments = not allow_python_style
        allow_generic_tokens = not allow_python_style
        for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            names = _extract_env_names_from_line(
                raw_line,
                allow_assignments=allow_assignments,
                allow_generic_tokens=allow_generic_tokens,
            )
            if not names:
                continue
            is_required_line = "Required" in raw_line
            is_optional_line = "Optional" in raw_line
            assignment_match = ENV_ASSIGNMENT_RE.match(raw_line)
            assignment_value = assignment_match.group(2).strip() if assignment_match else ""
            for name in sorted(names):
                record = records.setdefault(name, EnvRecord(name=name))
                record.sources.add(rel_source)
                if assignment_match and assignment_match.group(1) == name:
                    record.example_values.add(assignment_value.strip())
                    if _looks_placeholder(assignment_value):
                        record.explicit_required = True
                    elif _looks_safe_default(assignment_value):
                        record.explicit_optional = True
                if is_required_line:
                    record.explicit_required = True
                if is_optional_line:
                    record.explicit_optional = True

    filtered = {name: record for name, record in records.items() if _is_env_candidate(name)}
    return dict(sorted(filtered.items(), key=lambda item: item[0]))


def _sorted_values(records: Mapping[str, EnvRecord]) -> List[str]:
    return sorted(records.keys())


def _safe_template_value(record: EnvRecord) -> str:
    if record.example_values:
        for value in sorted(record.example_values):
            if _looks_safe_default(value):
                return value.strip()
        for value in sorted(record.example_values):
            if value:
                return value.strip()
    return ""


def build_template(records: Mapping[str, EnvRecord]) -> List[str]:
    required: List[str] = []
    optional: List[str] = []

    for name in _sorted_values(records):
        record = records[name]
        value = _safe_template_value(record)
        line = f"{name}={value}"
        if record.explicit_required or (_looks_placeholder(value) and not record.explicit_optional):
            required.append(line)
        else:
            optional.append(line)

    template: List[str] = [
        "# Generated by scripts/env_extract.py",
        "# Required environment variables",
    ]
    template.extend(required)
    template.append("")
    template.append("# Optional environment variables and local defaults")
    template.extend(optional)
    template.append("")
    return template


def write_lines(path: Path, lines: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")


def write_outputs(root: Path, *, include_packages: bool, include_env: bool, include_template: bool) -> dict[str, Path]:
    output_dir = root / "scripts" / "env_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_paths = [
        path.relative_to(root).as_posix()
        for path in discover_dependency_manifests(root)
    ]
    write_lines(output_dir / "manifests.txt", manifest_paths)

    outputs: dict[str, Path] = {"manifests": output_dir / "manifests.txt"}

    if include_packages:
        dependencies = extract_dependencies(root)
        package_lines = [
            f"{record.ecosystem}\t{record.display}\t{';'.join(record.sources)}"
            for record in dependencies
        ]
        write_lines(output_dir / "packages.txt", package_lines)
        outputs["packages"] = output_dir / "packages.txt"

    if include_env or include_template:
        env_records = extract_env_vars(root)
        if include_env:
            env_lines = [f"{name}=" for name in _sorted_values(env_records)]
            write_lines(output_dir / "env_vars.txt", env_lines)
            outputs["env_vars"] = output_dir / "env_vars.txt"

        if include_template:
            template_lines = build_template(env_records)
            write_lines(output_dir / ".env.codex", template_lines)
            outputs["template"] = output_dir / ".env.codex"

    return outputs


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract dependency and env artifacts.")
    parser.add_argument("--root", default=".", help="Repository root (default: current directory)")
    parser.add_argument("--packages", action="store_true", help="Write packages.txt")
    parser.add_argument("--env", action="store_true", help="Write env_vars.txt")
    parser.add_argument("--template", action="store_true", help="Write .env.codex")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Write all artifacts (default when no extraction flags are supplied)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    requested = args.packages or args.env or args.template or args.all
    include_packages = args.packages or not requested or args.all
    include_env = args.env or not requested or args.all
    include_template = args.template or not requested or args.all

    outputs = write_outputs(
        root,
        include_packages=include_packages,
        include_env=include_env,
        include_template=include_template,
    )

    print(f"Wrote {len(outputs)} artifact(s) under {root / 'scripts' / 'env_outputs'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
