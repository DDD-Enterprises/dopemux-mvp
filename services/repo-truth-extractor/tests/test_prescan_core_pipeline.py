"""Tests for core prescan pipeline modules: corpus_walker, classifier, batch_planner."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from lib.prescan.classifier import Classifier
from lib.prescan.corpus_walker import CorpusWalker
from lib.prescan.engine import _entry_matches_code_language
from lib.prescan.models import FileEntry, PrescanConfig


def test_corpus_walker_finds_files(tmp_path: Path) -> None:
    """Verify CorpusWalker traverses directory and finds files."""
    # Create test structure
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    (tmp_path / "src" / "util.py").write_text("def helper(): pass")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "README.md").write_text("# Doc")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/main")

    config = PrescanConfig(
        repo_root=tmp_path,
        output_dir=tmp_path / "out",
        enable_code_prescan=False,
        enable_git_enrichment=False,
    )
    walker = CorpusWalker(config)
    entries = walker.walk()

    # Should find the 3 files but not .git
    assert len(entries) == 3
    paths = {e.rel_path for e in entries}
    assert "src/main.py" in paths
    assert "src/util.py" in paths
    assert "docs/README.md" in paths
    assert not any(".git" in p for p in paths)


def test_corpus_walker_respects_exclusions(tmp_path: Path) -> None:
    """Verify CorpusWalker excludes based on patterns."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("code")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "lib.js").write_text("lib")
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "bin").mkdir()
    (tmp_path / ".venv" / "bin" / "activate").write_text("activate")

    config = PrescanConfig(
        repo_root=tmp_path,
        output_dir=tmp_path / "out",
        enable_code_prescan=False,
        enable_git_enrichment=False,
    )
    walker = CorpusWalker(config)
    entries = walker.walk()

    # Should exclude node_modules and .venv
    paths = {e.rel_path for e in entries}
    assert "src/main.py" in paths
    assert not any("node_modules" in p for p in paths)
    assert not any(".venv" in p for p in paths)


def test_classifier_categorizes_files(tmp_path: Path) -> None:
    """Verify Classifier correctly categorizes files."""
    config = PrescanConfig(
        repo_root=tmp_path,
        output_dir=tmp_path / "out",
        enable_code_prescan=False,
        enable_git_enrichment=False,
    )
    classifier = Classifier(config)

    entries = [
        FileEntry(rel_path="docs/README.md", size_bytes=50, extension=".md"),
        FileEntry(rel_path="app.py", size_bytes=120, extension=".py"),
        FileEntry(rel_path="image.png", size_bytes=50000, extension=".png"),
    ]

    classifier.classify_all(entries)

    # Verify binary files are classified as noise
    png_entry = next(e for e in entries if e.rel_path == "image.png")
    assert png_entry.authority_class == "noise"

    # Verify code files are classified properly
    py_entry = next(e for e in entries if e.rel_path == "app.py")
    assert py_entry.authority_class != "noise"


def test_classifier_detects_draft_and_adr(tmp_path: Path) -> None:
    """Verify Classifier correctly assigns authority classes."""
    config = PrescanConfig(
        repo_root=tmp_path,
        output_dir=tmp_path / "out",
        enable_code_prescan=False,
        enable_git_enrichment=False,
    )
    classifier = Classifier(config)

    entries = [
        FileEntry(rel_path="docs/90-adr/ADR-001.md", size_bytes=100, extension=".md"),
        FileEntry(rel_path="docs/draft-feature.md", size_bytes=100, extension=".md"),
        FileEntry(rel_path="archive/old-spec.md", size_bytes=100, extension=".md"),
    ]

    classifier.classify_all(entries)

    adr_entry = next(e for e in entries if "ADR" in e.rel_path)
    assert adr_entry.authority_class == "canonical"

    archive_entry = next(e for e in entries if "archive" in e.rel_path)
    assert archive_entry.authority_class == "historical"


def test_code_language_alias_matching() -> None:
    py_entry = FileEntry(rel_path="src/main.py", size_bytes=20, extension=".py")
    tsx_entry = FileEntry(rel_path="ui/app.tsx", size_bytes=20, extension=".tsx")
    txt_entry = FileEntry(rel_path="docs/readme.txt", size_bytes=20, extension=".txt")

    assert _entry_matches_code_language(py_entry, ["python"]) is True
    assert _entry_matches_code_language(tsx_entry, ["typescript"]) is True
    assert _entry_matches_code_language(txt_entry, ["python", "typescript"]) is False




if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
