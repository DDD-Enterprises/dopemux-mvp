#!/usr/bin/env python3
"""Generate the Docker CI matrix and verify it against canonical Compose wiring."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "config" / "containers.json"
DEFAULT_COMPOSE = ROOT / "compose.yml"
SERVICE_RE = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
REGISTRY_RE = re.compile(
    r"^ghcr\.io/[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?"
    r"(?:/[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?)*$"
)
ALLOWED_CLASSIFICATIONS = {
    "canonical",
    "canonical-support",
    "legacy-compatibility",
    "legacy-unwired",
}
ALLOWED_COMPOSE_PATH_STATUSES = {"aligned", "missing-wrapper"}
REQUIRED_TARGET_FIELDS = {
    "service",
    "image",
    "classification",
    "context",
    "dockerfile",
    "compose_services",
    "publish",
    "smoke_test",
}


class ManifestError(ValueError):
    """Raised when the checked-in container manifest is invalid."""


def _relative_to_root(path: Path) -> str:
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ManifestError(f"Path escapes repository root: {resolved}") from exc
    value = relative.as_posix()
    return value if value else "."


def load_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ManifestError(f"Manifest not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ManifestError(f"Manifest is not valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ManifestError("Manifest root must be an object")
    if data.get("schema_version") != "1.0.0":
        raise ManifestError("schema_version must be 1.0.0")
    registry = data.get("registry")
    if not isinstance(registry, str) or REGISTRY_RE.fullmatch(registry) is None:
        raise ManifestError("registry must be an exact ghcr.io namespace")
    if not isinstance(data.get("platform"), str) or not data["platform"]:
        raise ManifestError("platform must be a non-empty string")
    if not isinstance(data.get("targets"), list) or not data["targets"]:
        raise ManifestError("targets must be a non-empty array")
    return data


def validate_manifest(data: dict[str, Any], *, check_paths: bool = True) -> None:
    seen_services: set[str] = set()
    seen_images: set[str] = set()
    seen_compose_services: set[str] = set()

    for index, target in enumerate(data["targets"]):
        label = f"targets[{index}]"
        if not isinstance(target, dict):
            raise ManifestError(f"{label} must be an object")
        missing = REQUIRED_TARGET_FIELDS - target.keys()
        if missing:
            raise ManifestError(f"{label} missing fields: {sorted(missing)}")

        service = target["service"]
        image = target["image"]
        if not isinstance(service, str) or not SERVICE_RE.fullmatch(service):
            raise ManifestError(f"{label}.service is invalid: {service!r}")
        if not isinstance(image, str) or not SERVICE_RE.fullmatch(image):
            raise ManifestError(f"{label}.image is invalid: {image!r}")
        if service in seen_services:
            raise ManifestError(f"Duplicate service target: {service}")
        if image in seen_images:
            raise ManifestError(f"Duplicate image name: {image}")
        seen_services.add(service)
        seen_images.add(image)

        classification = target["classification"]
        if classification not in ALLOWED_CLASSIFICATIONS:
            raise ManifestError(f"{label}.classification is invalid: {classification!r}")
        if not isinstance(target["publish"], bool):
            raise ManifestError(f"{label}.publish must be boolean")
        if not isinstance(target["smoke_test"], bool):
            raise ManifestError(f"{label}.smoke_test must be boolean")

        compose_services = target["compose_services"]
        if not isinstance(compose_services, list) or not all(
            isinstance(item, str) and SERVICE_RE.fullmatch(item) for item in compose_services
        ):
            raise ManifestError(f"{label}.compose_services must be an array of service names")
        for compose_service in compose_services:
            if compose_service in seen_compose_services:
                raise ManifestError(f"Compose service mapped more than once: {compose_service}")
            seen_compose_services.add(compose_service)

        context = target["context"]
        dockerfile = target["dockerfile"]
        if not isinstance(context, str) or not context:
            raise ManifestError(f"{label}.context must be a non-empty string")
        if not isinstance(dockerfile, str) or not dockerfile:
            raise ManifestError(f"{label}.dockerfile must be a non-empty string")

        compose_context = target.get("compose_context", context)
        compose_dockerfile = target.get("compose_dockerfile", dockerfile)
        compose_path_status = target.get("compose_path_status", "aligned")
        if not isinstance(compose_context, str) or not compose_context:
            raise ManifestError(f"{label}.compose_context must be a non-empty string")
        if not isinstance(compose_dockerfile, str) or not compose_dockerfile:
            raise ManifestError(f"{label}.compose_dockerfile must be a non-empty string")
        if compose_path_status not in ALLOWED_COMPOSE_PATH_STATUSES:
            raise ManifestError(
                f"{label}.compose_path_status is invalid: {compose_path_status!r}"
            )
        if compose_path_status == "missing-wrapper" and not compose_services:
            raise ManifestError(f"{label} cannot declare missing-wrapper without Compose services")

        if check_paths:
            context_path = (ROOT / context).resolve()
            dockerfile_path = (ROOT / dockerfile).resolve()
            _relative_to_root(context_path)
            _relative_to_root(dockerfile_path)
            if not context_path.is_dir():
                raise ManifestError(f"Build context does not exist: {context}")
            if not dockerfile_path.is_file():
                raise ManifestError(f"Dockerfile does not exist: {dockerfile}")

        if target["smoke_test"]:
            for field in ("smoke_port", "smoke_path"):
                if not isinstance(target.get(field), str) or not target[field]:
                    raise ManifestError(f"{label}.{field} is required for smoke-tested targets")


def matrix_payload(data: dict[str, Any]) -> dict[str, Any]:
    include: list[dict[str, Any]] = []
    for target in data["targets"]:
        include.append(
            {
                "service": target["service"],
                "image": target["image"],
                "classification": target["classification"],
                "context": target["context"],
                "dockerfile": target["dockerfile"],
                "publish": target["publish"],
                "smoke_test": target["smoke_test"],
                "smoke_port": target.get("smoke_port", ""),
                "smoke_path": target.get("smoke_path", ""),
                "platform": data["platform"],
            }
        )
    return {"include": include}


def _run_compose_config(compose_path: Path) -> dict[str, Any]:
    command = [
        "docker",
        "compose",
        "-f",
        str(compose_path),
        "config",
        "--format",
        "json",
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy(),
    )
    if completed.returncode != 0:
        raise ManifestError(
            "docker compose config failed with exit code "
            f"{completed.returncode}:\n{completed.stderr.strip()}"
        )
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ManifestError(f"docker compose config returned invalid JSON: {exc}") from exc


def compose_build_map(config: dict[str, Any]) -> dict[str, tuple[str, str]]:
    services = config.get("services")
    if not isinstance(services, dict):
        raise ManifestError("Compose config has no services object")

    result: dict[str, tuple[str, str]] = {}
    for service, definition in services.items():
        if not isinstance(definition, dict) or "build" not in definition:
            continue
        build = definition["build"]
        if isinstance(build, str):
            context_path = Path(build)
            dockerfile_path = context_path / "Dockerfile"
        elif isinstance(build, dict):
            context_value = build.get("context", ".")
            dockerfile_value = build.get("dockerfile", "Dockerfile")
            context_path = Path(context_value)
            if not context_path.is_absolute():
                context_path = ROOT / context_path
            dockerfile_path = Path(dockerfile_value)
            if not dockerfile_path.is_absolute():
                dockerfile_path = context_path / dockerfile_path
        else:
            raise ManifestError(f"Unsupported Compose build value for {service}: {build!r}")

        result[service] = (
            _relative_to_root(context_path),
            _relative_to_root(dockerfile_path),
        )
    return result


def validate_compose_alignment(data: dict[str, Any], config: dict[str, Any]) -> None:
    actual = compose_build_map(config)
    expected: dict[str, tuple[str, str, str]] = {}
    for target in data["targets"]:
        compose_context = target.get("compose_context", target["context"])
        compose_dockerfile = target.get("compose_dockerfile", target["dockerfile"])
        for compose_service in target["compose_services"]:
            expected[compose_service] = (
                compose_context,
                compose_dockerfile,
                target["service"],
            )

    missing = sorted(set(actual) - set(expected))
    stale = sorted(set(expected) - set(actual))
    if missing:
        raise ManifestError(f"Compose build services missing from manifest: {missing}")
    if stale:
        raise ManifestError(f"Manifest references non-build Compose services: {stale}")

    conflicts: list[str] = []
    for service, (actual_context, actual_dockerfile) in actual.items():
        expected_context, expected_dockerfile, target = expected[service]
        if (actual_context, actual_dockerfile) != (expected_context, expected_dockerfile):
            conflicts.append(
                f"{service} -> target {target}: compose=({actual_context}, {actual_dockerfile}) "
                f"manifest=({expected_context}, {expected_dockerfile})"
            )
    if conflicts:
        raise ManifestError("Compose/manifest build conflicts:\n- " + "\n- ".join(conflicts))


def compose_drift_targets(data: dict[str, Any]) -> list[str]:
    return [
        target["service"]
        for target in data["targets"]
        if target.get("compose_path_status", "aligned") != "aligned"
    ]


def _write_github_output(name: str, value: str, output_path: str | None) -> None:
    if output_path:
        with Path(output_path).open("a", encoding="utf-8") as handle:
            handle.write(f"{name}={value}\n")
    else:
        print(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate-manifest")

    matrix_parser = subparsers.add_parser("matrix")
    matrix_parser.add_argument(
        "--github-output",
        default=os.environ.get("GITHUB_OUTPUT"),
        help="Append matrix=<JSON> to this GitHub output file; print JSON when omitted.",
    )

    compose_parser = subparsers.add_parser("validate-compose")
    compose_parser.add_argument("--compose", type=Path, default=DEFAULT_COMPOSE)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        data = load_manifest(args.manifest)
        validate_manifest(data)
        if args.command == "validate-manifest":
            print(f"PASS: {len(data['targets'])} container targets validated")
        elif args.command == "matrix":
            payload = json.dumps(matrix_payload(data), separators=(",", ":"), sort_keys=True)
            _write_github_output("matrix", payload, args.github_output)
        elif args.command == "validate-compose":
            config = _run_compose_config(args.compose)
            validate_compose_alignment(data, config)
            print(f"PASS: {len(compose_build_map(config))} Compose build services mapped")
            drift = compose_drift_targets(data)
            if drift:
                print(
                    "WARNING: Compose still references missing wrapper Dockerfiles for: "
                    + ", ".join(drift),
                    file=sys.stderr,
                )
        else:  # pragma: no cover
            raise AssertionError(f"Unhandled command: {args.command}")
    except ManifestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
