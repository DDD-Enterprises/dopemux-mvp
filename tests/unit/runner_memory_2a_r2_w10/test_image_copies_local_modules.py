"""W10 (Runner Memory Wave 2A, R2): each memory image must COPY the local modules it imports.

Both the dope-memory and the ConPort Dockerfiles copy application modules one file at a
time. A module the entry points import but the Dockerfile does not copy fails at import
time inside a rebuilt image (``ModuleNotFoundError``), which no source-tree test sees.
This static test parses each Dockerfile's ``COPY`` lines and the entry modules' import
statements; it builds, pulls and runs nothing.
"""
from __future__ import annotations

import ast
import shlex
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[3]

# image -> (Dockerfile, service source directory, entry modules), all repo-relative.
IMAGES = {
    "dope-memory": (
        "services/working-memory-assistant/Dockerfile.dope-memory",
        "services/working-memory-assistant",
        ("dope_memory_main.py", "mcp_http.py", "eventbus_consumer.py"),
    ),
    "conport": (
        "docker/mcp-servers-source/conport/Dockerfile",
        "docker/mcp-servers-source/conport",
        ("server.py", "enhanced_server.py", "conport_mcp_stdio.py"),
    ),
}

_WORKDIR = "/app"


def _copied_files(dockerfile: Path) -> dict[str, str]:
    """Map repo-relative COPY source -> destination for single-file ``COPY`` lines."""
    out: dict[str, str] = {}
    for raw in dockerfile.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line.upper().startswith("COPY "):
            continue
        args = shlex.split(line)[1:]
        if any(a.startswith("--from") for a in args):
            continue  # copies from another stage or image, not from the build context
        parts = [a for a in args if not a.startswith("--")]
        if len(parts) < 2:
            continue
        *sources, dest = parts
        for src in sources:
            out[src] = dest
    return out


def _lands_importable(src: str, dest: str) -> bool:
    """True when ``src`` ends up directly in the working directory under its own name."""
    name = src.rsplit("/", 1)[-1]
    return dest.rstrip("/") in (".", _WORKDIR) or dest in (name, f"{_WORKDIR}/{name}", f"./{name}")


def _imported_top_level_modules(path: Path) -> set[str]:
    """Top-level module names named by every absolute import statement in ``path``."""
    mods: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            mods.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            mods.add(node.module.split(".")[0])
    return mods


def _local_modules_needed(service_dir: str, entries: tuple[str, ...]) -> dict[str, set[str]]:
    """Local ``<module>.py`` files (directly in the service dir) -> entry modules importing them."""
    needed: dict[str, set[str]] = {}
    for entry in entries:
        for mod in _imported_top_level_modules(_ROOT / service_dir / entry):
            if (_ROOT / service_dir / f"{mod}.py").is_file():
                needed.setdefault(f"{mod}.py", set()).add(entry)
    return needed


@pytest.mark.parametrize("image", IMAGES)
def test_entry_modules_and_dockerfile_exist(image):
    dockerfile, service_dir, entries = IMAGES[image]
    assert (_ROOT / dockerfile).is_file(), dockerfile
    for entry in entries:
        assert (_ROOT / service_dir / entry).is_file(), entry


@pytest.mark.parametrize("image", IMAGES)
def test_entry_modules_import_at_least_one_local_module(image):
    """Guard against a vacuous pass: the import scan must actually find local modules."""
    _, service_dir, entries = IMAGES[image]
    needed = _local_modules_needed(service_dir, entries)
    assert "auth_identity.py" in needed, needed


@pytest.mark.parametrize("image", IMAGES)
def test_image_copies_every_local_module_its_entry_points_import(image):
    dockerfile, service_dir, entries = IMAGES[image]
    copied = {
        src.removeprefix(service_dir + "/")
        for src, dest in _copied_files(_ROOT / dockerfile).items()
        if src.startswith(service_dir + "/") and _lands_importable(src, dest)
    }
    needed = _local_modules_needed(service_dir, entries)
    missing = {mod: sorted(who) for mod, who in sorted(needed.items()) if mod not in copied}
    assert not missing, f"{dockerfile} does not COPY: {missing}"


def test_copy_parser_reads_a_plain_copy_line(tmp_path):
    df = tmp_path / "Dockerfile"
    df.write_text(
        "FROM x\n"
        "COPY svc/a.py .\n"
        "COPY svc/b.py /app/\n"
        "COPY svc/c.py /elsewhere/c.py\n"
        "COPY --from=other /uv /bin/\n"
    )
    copied = _copied_files(df)
    assert _lands_importable("svc/a.py", copied["svc/a.py"])
    assert _lands_importable("svc/b.py", copied["svc/b.py"])
    assert not _lands_importable("svc/c.py", copied["svc/c.py"])
    assert "/uv" not in copied
