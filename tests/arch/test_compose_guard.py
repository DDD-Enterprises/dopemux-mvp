"""Focused tests for compose guard drift checks."""

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent.parent
COMPOSE_GUARD_PATH = REPO_ROOT / "scripts" / "compose_guard.py"

spec = importlib.util.spec_from_file_location("compose_guard", COMPOSE_GUARD_PATH)
compose_guard = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(compose_guard)


def test_extra_root_compose_file_fails(tmp_path):
    compose_file = tmp_path / "compose.yml"
    compose_file.write_text("services: {}\n")
    (tmp_path / "docker-compose.unified.yml").write_text("services: {}\n")

    assert not compose_guard.check_for_extra_root_compose_files(tmp_path, compose_file)


def test_legacy_compose_directory_is_allowed(tmp_path):
    compose_file = tmp_path / "compose.yml"
    compose_file.write_text("services: {}\n")
    legacy_dir = tmp_path / "compose" / "legacy"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "old-docker-compose.yml").write_text("services: {}\n")

    assert compose_guard.check_for_extra_root_compose_files(tmp_path, compose_file)


def test_only_canonical_compose_passes(tmp_path):
    compose_file = tmp_path / "compose.yml"
    compose_file.write_text("services: {}\n")

    assert compose_guard.check_for_extra_root_compose_files(tmp_path, compose_file)
