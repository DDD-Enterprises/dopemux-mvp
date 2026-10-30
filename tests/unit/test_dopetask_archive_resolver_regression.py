"""Recovered MP023 regression tests."""

from pathlib import Path

import pytest

from dopemux_pr_merge_specialist.dopetask_archive_resolver import (
    ArchiveResolution,
    DopetaskArchiveResolver,
)


def _make_bundle(tmp_path: Path) -> tuple[Path, Path]:
    """Create <tmp>/root/bundle_dir/bundle.json and return (bundle_path, expected_zip)."""
    root = tmp_path / "root"
    bundle_dir = root / "bundle_dir"
    bundle_dir.mkdir(parents=True)
    bundle_path = bundle_dir / "bundle.json"
    bundle_path.write_text("{}")
    expected_zip = root / "bundle_dir.zip"
    return bundle_path, expected_zip


def test_directory_named_like_zip_is_not_archive_present(tmp_path):
    # Failing on baseline: Path.exists() is True for a directory.
    bundle_path, expected_zip = _make_bundle(tmp_path)
    expected_zip.mkdir()
    assert expected_zip.is_dir()

    result = DopetaskArchiveResolver().resolve(bundle_path, ["artifact_a.txt"])

    assert result.archive_expected is True
    assert result.archive_present is False
    assert result.archive_path == str(expected_zip)
    assert result.note == f"Archive not found: {expected_zip}"


def test_non_empty_directory_named_like_zip_is_not_archive_present(tmp_path):
    # Failing on baseline: a populated directory with the .zip name is still not a file.
    bundle_path, expected_zip = _make_bundle(tmp_path)
    expected_zip.mkdir()
    (expected_zip / "inner.txt").write_text("decoy")
    (expected_zip / "nested").mkdir()

    result = DopetaskArchiveResolver().resolve(
        bundle_path, ["artifact_a.txt", "artifact_b.txt"]
    )

    assert result.archive_expected is True
    assert result.archive_present is False
    assert result.archive_path == str(expected_zip)
    assert result.note.startswith("Archive not found:")


def test_missing_archive_remains_not_present(tmp_path):
    # Negative regression: nothing at the candidate path -> False.
    bundle_path, expected_zip = _make_bundle(tmp_path)
    assert not expected_zip.exists()

    result = DopetaskArchiveResolver().resolve(bundle_path, ["artifact_a.txt"])

    assert result.archive_expected is True
    assert result.archive_present is False
    assert result.archive_path == str(expected_zip)
    assert result.note == f"Archive not found: {expected_zip}"


def test_no_supporting_artifacts_means_archive_not_expected(tmp_path):
    # Negative regression: no artifacts -> not expected, path None, even if a
    # directory with the zip name exists.
    bundle_path, expected_zip = _make_bundle(tmp_path)
    expected_zip.mkdir()

    result = DopetaskArchiveResolver().resolve(bundle_path, [])

    assert result == ArchiveResolution(
        archive_path=None,
        archive_present=False,
        archive_expected=False,
        note="No supporting artifacts; archive not expected.",
    )


def test_regular_file_archive_is_detected(tmp_path):
    # Valid control: a regular file at the candidate path -> True. Contents are
    # never opened, so an arbitrary byte payload is sufficient.
    bundle_path, expected_zip = _make_bundle(tmp_path)
    expected_zip.write_bytes(b"PK\x05\x06" + b"\x00" * 18)
    assert expected_zip.is_file()

    result = DopetaskArchiveResolver().resolve(bundle_path, ["artifact_a.txt"])

    assert result.archive_expected is True
    assert result.archive_present is True
    assert result.archive_path == str(expected_zip)
    assert result.note == f"Archive found: {expected_zip}"
