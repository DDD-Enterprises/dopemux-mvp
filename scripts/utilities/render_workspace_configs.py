#!/usr/bin/env python3
"""Generate per-workspace configuration artifacts under ~/.dopemux.

The script detects (or accepts) a workspace root, ensures it is registered in
the global dopemux config, and writes a small env file that other tooling can
source. These env files live in ``~/.dopemux/workspaces/<slug>/env`` and expose
the canonical ``DOPEMUX_WORKSPACE_*`` variables as well as the slug/hash so
shell scripts, MCP wrappers, and Docker helpers can operate concurrently across
multiple clones.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


import argparse
import importlib.util
from pathlib import Path
import sys
import types

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
PACKAGE_NAME = "dopemux"
PACKAGE_PATH = SRC_PATH / PACKAGE_NAME

if PACKAGE_NAME not in sys.modules:
    pkg = types.ModuleType(PACKAGE_NAME)
    pkg.__path__ = [str(PACKAGE_PATH)]  # type: ignore[attr-defined]
    sys.modules[PACKAGE_NAME] = pkg


def _load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {module_name} from {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[assignment]
    return module


workspace_detection = _load_module(
    f"{PACKAGE_NAME}.workspace_detection",
    PACKAGE_PATH / "workspace_detection.py",
)
workspace_env = _load_module(
    f"{PACKAGE_NAME}.workspace_env",
    PACKAGE_PATH / "workspace_env.py",
)

get_workspace_root = workspace_detection.get_workspace_root
ensure_workspace_artifacts = workspace_env.ensure_workspace_artifacts


TEMPLATES = {
    "mcp-proxy-config.json": PROJECT_ROOT / "mcp-proxy-config.json",
}


def render_templates(workspace_dir: Path, replacements: dict) -> dict[str, Path]:
    rendered: dict[str, Path] = {}
    for name, template_path in TEMPLATES.items():
        if not template_path.exists():
            logger.warning(f"[warn] Template missing: {template_path}", file=sys.stderr)
            continue
        try:
            text = template_path.read_text(encoding="utf-8")
            for placeholder, value in replacements.items():
                text = text.replace(placeholder, value)
            output_path = workspace_dir / name
            output_path.write_text(text, encoding="utf-8")
            rendered[name] = output_path
        except OSError as exc:
            logger.error(f"[warn] Failed to render {template_path}: {exc}", file=sys.stderr)
    return rendered


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, help="Explicit workspace path to render for")
    parser.add_argument(
        "--set-default",
        action="store_true",
        help="Also record this workspace as the default in ~/.dopemux/config.json",
    )
    args = parser.parse_args()

    workspace_path = (args.workspace or get_workspace_root()).expanduser().resolve()
    try:
        artifacts = ensure_workspace_artifacts(workspace_path, set_default=args.set_default)
    except OSError as exc:
        logger.error(f"[error] Unable to persist workspace artifacts: {exc}", file=sys.stderr)
        sys.exit(1)

    entry = artifacts.entry
    workspace_dir = artifacts.env_path.parent
    env_path = artifacts.env_path
    meta_path = artifacts.metadata_path
    rendered_templates = render_templates(
        workspace_dir,
        {
            "__WORKSPACE_ROOT__": str(workspace_path),
        },
    )

    logger.info("Workspace registered ✅")
    logger.info(f"  Root: {workspace_path}")
    logger.info(f"  Slug: {entry.slug}")
    logger.info(f"  Env : {env_path}")
    logger.info(f"  Meta: {meta_path}")
    if rendered_templates:
        for name, path in rendered_templates.items():
            logger.info(f"  Template[{name}]: {path}")


if __name__ == "__main__":
    main()
