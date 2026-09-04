"""P1 generic atomic materialization: temp generation + fsync + atomic
replacement, shared/global config rejection, and PROVENANCE_ONLY receipts.

Covers Task 6 of TP-DMX-MCP-MULTIPROJECT-P1-FLEET-CONTROL-PLANE-001.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from dopemux.mcp import materialization as m

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schemas/mcp/runner-materialization-receipt.schema.json"


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def _plan(output_root: Path, **overrides) -> m.MaterializationPlan:
    base = dict(
        output_root=output_root,
        files={".mcp.json": b'{"mcpServers": {}}', "notes.md": b"hello"},
        project_id="prj_a",
        workspace_id="ws_a",
        instance_id="inst_a",
        registry_generation=1,
        runner_family="claude",
        profile="core-code",
        catalog_digest="a" * 64,
        lease_refs=("lease-1",),
        strict_mode=False,
        inherited_surface_status="UNKNOWN",
    )
    base.update(overrides)
    return m.MaterializationPlan(**base)


def test_materialize_produces_schema_valid_receipt(tmp_path: Path):
    receipt = m.materialize_atomic(_plan(tmp_path / "session"))
    jsonschema.validate(receipt.to_schema_dict(), _schema())
    assert receipt.to_schema_dict()["shared_global_config_mutated"] is False
    assert receipt.to_schema_dict()["authority"] == "PROVENANCE_ONLY"


def test_materialize_writes_files_under_current(tmp_path: Path):
    root = tmp_path / "session"
    m.materialize_atomic(_plan(root))
    current = root / m.CURRENT_LINK_NAME
    assert current.is_symlink()
    assert (current / ".mcp.json").read_bytes() == b'{"mcpServers": {}}'
    assert (current / "notes.md").read_bytes() == b"hello"
    assert (current / "receipt.json").exists()


def test_second_materialization_keeps_prior_generation_on_disk(tmp_path: Path):
    root = tmp_path / "session"
    first = m.materialize_atomic(_plan(root))
    second = m.materialize_atomic(_plan(root, files={".mcp.json": b'{"mcpServers": {"x": 1}}'}))

    assert first.generation_dir.exists()
    assert second.generation_dir.exists()
    assert first.generation_dir != second.generation_dir

    current = root / m.CURRENT_LINK_NAME
    assert current.resolve() == second.generation_dir.resolve()
    assert (current / ".mcp.json").read_bytes() == b'{"mcpServers": {"x": 1}}'


def test_rendered_config_digest_changes_with_content(tmp_path: Path):
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    receipt_a = m.materialize_atomic(_plan(root_a, files={"x.txt": b"one"}))
    receipt_b = m.materialize_atomic(_plan(root_b, files={"x.txt": b"two"}))
    assert receipt_a.rendered_config_digest != receipt_b.rendered_config_digest


def test_rendered_config_digest_stable_for_identical_content(tmp_path: Path):
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    receipt_a = m.materialize_atomic(_plan(root_a, files={"x.txt": b"same"}))
    receipt_b = m.materialize_atomic(_plan(root_b, files={"x.txt": b"same"}))
    assert receipt_a.rendered_config_digest == receipt_b.rendered_config_digest


# ---- shared/global config rejection ----------------------------------------


@pytest.mark.parametrize(
    "relative_root",
    [".claude", ".claude.json", ".codex", ".config/opencode", ".gemini", ".config/github-copilot"],
)
def test_rejects_known_shared_global_roots(tmp_path: Path, relative_root: str):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    forbidden_root = fake_home / relative_root
    with pytest.raises(m.MaterializationError):
        m.materialize_atomic(_plan(forbidden_root), home=fake_home)


def test_rejects_output_root_nested_inside_shared_global(tmp_path: Path):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    nested = fake_home / ".claude" / "sessions" / "deep"
    with pytest.raises(m.MaterializationError):
        m.materialize_atomic(_plan(nested), home=fake_home)


def test_rejects_output_root_that_is_home_itself(tmp_path: Path):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    with pytest.raises(m.MaterializationError):
        m.materialize_atomic(_plan(fake_home), home=fake_home)


def test_allows_ordinary_session_dir_outside_known_roots(tmp_path: Path):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    ok_root = fake_home / ".dopemux" / "sessions" / "abc"
    receipt = m.materialize_atomic(_plan(ok_root), home=fake_home)
    assert receipt is not None


# ---- strict mode / plan validation -----------------------------------------


def test_strict_mode_requires_known_inherited_surface(tmp_path: Path):
    with pytest.raises(m.MaterializationError):
        m.materialize_atomic(_plan(tmp_path / "s", strict_mode=True, inherited_surface_status="UNKNOWN"))


def test_strict_mode_with_known_surface_succeeds(tmp_path: Path):
    receipt = m.materialize_atomic(
        _plan(tmp_path / "s", strict_mode=True, inherited_surface_status="KNOWN")
    )
    jsonschema.validate(receipt.to_schema_dict(), _schema())


def test_rejects_unsafe_relative_paths(tmp_path: Path):
    with pytest.raises(m.MaterializationError):
        m.materialize_atomic(_plan(tmp_path / "s", files={"../escape.txt": b"x"}))


def test_rejects_empty_file_set(tmp_path: Path):
    with pytest.raises(m.MaterializationError):
        m.materialize_atomic(_plan(tmp_path / "s", files={}))


def test_rejects_unknown_runner_family(tmp_path: Path):
    with pytest.raises(m.MaterializationError):
        m.materialize_atomic(_plan(tmp_path / "s", runner_family="notarunner"))


# ---- failure injection: no mixed generations --------------------------------


def test_injected_failure_never_leaves_mixed_generations(tmp_path: Path, monkeypatch):
    root = tmp_path / "session"
    first = m.materialize_atomic(_plan(root))
    current_before = (root / m.CURRENT_LINK_NAME).resolve()

    real_fsync_file = m._fsync_file

    def poisoned_fsync_file(path: Path) -> None:
        if path.name == "poison.txt":
            raise OSError("simulated disk failure mid-generation")
        return real_fsync_file(path)

    monkeypatch.setattr(m, "_fsync_file", poisoned_fsync_file)

    with pytest.raises(m.MaterializationError):
        m.materialize_atomic(_plan(root, files={"poison.txt": b"boom", "ok.txt": b"fine"}))

    # current still points at the first, complete generation.
    assert (root / m.CURRENT_LINK_NAME).resolve() == current_before
    assert (root / m.CURRENT_LINK_NAME / ".mcp.json").exists()

    # no orphaned partial generation directories left behind.
    generations = list((root / m.GENERATIONS_DIRNAME).iterdir())
    assert len(generations) == 1
    assert generations[0].resolve() == first.generation_dir.resolve()

    # no leftover staging directories.
    staging_dirs = [p for p in root.iterdir() if p.name.startswith(".staging-")]
    assert staging_dirs == []


def test_injected_failure_after_rename_before_flip_orphans_cleanly(tmp_path: Path, monkeypatch):
    root = tmp_path / "session"
    first = m.materialize_atomic(_plan(root))
    current_before = (root / m.CURRENT_LINK_NAME).resolve()

    def poisoned_flip(output_root: Path, gen_dir: Path) -> None:
        raise OSError("simulated symlink flip failure")

    monkeypatch.setattr(m, "_flip_current_symlink", poisoned_flip)

    with pytest.raises(m.MaterializationError):
        m.materialize_atomic(_plan(root, files={"x.txt": b"new"}))

    assert (root / m.CURRENT_LINK_NAME).resolve() == current_before
    generations = list((root / m.GENERATIONS_DIRNAME).iterdir())
    assert len(generations) == 1
    assert generations[0].resolve() == first.generation_dir.resolve()


# ---- read_current_receipt ----------------------------------------------------


def test_read_current_receipt_round_trip(tmp_path: Path):
    root = tmp_path / "session"
    assert m.read_current_receipt(root) is None
    receipt = m.materialize_atomic(_plan(root))
    read_back = m.read_current_receipt(root)
    assert read_back["materialization_id"] == receipt.materialization_id
    jsonschema.validate(read_back, _schema())
