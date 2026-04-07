from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from lib.prescan.engine import PrescanEngine
from lib.prescan.models import FileEntry, PrescanConfig


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class FakeWalker:
    def __init__(self, repo_root: Path, files: dict[str, str]):
        self.repo_root = repo_root
        self.files = files

    def sync(self) -> None:
        existing = [p for p in self.repo_root.rglob("*") if p.is_file()]
        for path in existing:
            path.unlink()
        for rel_path, content in self.files.items():
            path = self.repo_root / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    def walk(self) -> list[FileEntry]:
        self.sync()
        entries: list[FileEntry] = []
        for rel_path, content in sorted(self.files.items()):
            path = self.repo_root / rel_path
            entries.append(
                FileEntry(
                    rel_path=rel_path,
                    size_bytes=path.stat().st_size,
                    extension=path.suffix,
                    authority_class="canonical",
                    content_hash=_sha256_text(content),
                )
            )
        return entries


class FakeNoop:
    def classify_all(self, entries: list[FileEntry]) -> None:
        return None

    def enrich(self, entries: list[FileEntry]) -> None:
        return None

    def recover_ghost_files(self, existing_paths: set[str]) -> list[FileEntry]:
        return []

    def detect_duplicates(self, entries: list[FileEntry]) -> None:
        return None

    def detect_version_chains(self, entries: list[FileEntry]) -> None:
        return None


class FakeCostEstimator:
    def estimate(self, entries: list[FileEntry]) -> dict[str, Any]:
        return {"estimated_tokens": len(entries)}


class FakeCodePrescan:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def analyze_file(self, entry: FileEntry, repo_root: Path) -> dict[str, Any]:
        self.calls.append(entry.rel_path)
        content = (repo_root / entry.rel_path).read_text(encoding="utf-8")
        imports = []
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("IMPORT "):
                imports.append(line.split(" ", 1)[1])
        entry.function_count = content.count("def ")
        entry.class_count = content.count("class ")
        entry.import_count = len(imports)
        entry.complexity_score = round(len(content) / 100, 2)
        entry.docstring_coverage = 1.0 if '"""' in content else 0.0
        return {
            "rel_path": entry.rel_path,
            "language": entry.extension.lstrip("."),
            "symbols": [
                {
                    "name": entry.rel_path.replace("/", "_"),
                    "type": "function",
                    "complexity": entry.complexity_score,
                    "has_docstring": bool(entry.docstring_coverage),
                }
            ],
            "imports": imports,
            "api_surfaces": ["cli"] if "@click.command" in content else [],
        }


class FakeCodeIntelligenceBuilder:
    def __init__(self, code_prescan: FakeCodePrescan, dep_graph, entries: list[FileEntry], manifest: list[dict[str, Any]]):
        self.entries = entries
        self.manifest = manifest
        self.dep_graph = dep_graph

    def build(self, repo_root: Path) -> dict[str, Any]:
        ordered = [
            {"rel_path": entry.rel_path, "score": index + 1}
            for index, entry in enumerate(sorted(self.entries, key=lambda e: e.rel_path))
        ]
        return {
            "generated_at": "normalized",
            "repo_root": str(repo_root),
            "summary": {"total_code_files": len(self.entries)},
            "processing_order": ordered,
            "hotspots": [],
            "orphans": [],
            "test_mappings": [],
            "pagerank_scores": {},
        }


def _make_config(tmp_path: Path, *, output_name: str = "out", **overrides: Any) -> PrescanConfig:
    config = PrescanConfig(
        repo_root=tmp_path / "repo",
        output_dir=tmp_path / output_name,
        enable_code_prescan=True,
        enable_git_enrichment=False,
        batch_mode=False,
        cost_estimate=False,
    )
    for key, value in overrides.items():
        setattr(config, key, value)
    return config


def _make_engine(tmp_path: Path, files: dict[str, str], *, output_name: str = "out", **config_overrides: Any) -> tuple[PrescanEngine, FakeWalker, FakeCodePrescan]:
    config = _make_config(tmp_path, output_name=output_name, **config_overrides)
    config.repo_root.mkdir(parents=True, exist_ok=True)
    engine = PrescanEngine(config)
    walker = FakeWalker(config.repo_root, files)
    code_prescan = FakeCodePrescan()
    engine.walker = walker
    engine.classifier = FakeNoop()
    engine.git_enricher = FakeNoop()
    engine.duplicate_detector = FakeNoop()
    engine.cost_estimator = FakeCostEstimator()
    engine.code_prescan = code_prescan
    return engine, walker, code_prescan


def _patch_code_report_builder(monkeypatch) -> None:
    import lib.prescan.code_intelligence_report as code_report_module

    monkeypatch.setattr(code_report_module, "CodeIntelligenceBuilder", FakeCodeIntelligenceBuilder)


def _cache_path(output_dir: Path) -> Path:
    return output_dir / ".cache" / "prescan_incremental_cache.json"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalized_outputs(output_dir: Path) -> dict[str, Any]:
    intelligence = _load_json(output_dir / "prescan_intelligence.json")
    report = _load_json(output_dir / "code_intelligence_report.json")
    manifest = _load_json(output_dir / "corpus_manifest.json")
    graph = _load_json(output_dir / "code_graph.json")

    intelligence["generated_at"] = "normalized"
    report["generated_at"] = "normalized"

    return {
        "intelligence": intelligence,
        "report": report,
        "manifest": manifest,
        "graph": graph,
    }


def test_incremental_no_change_reuses_warm_cache(tmp_path: Path, monkeypatch) -> None:
    _patch_code_report_builder(monkeypatch)
    files = {
        "src/a.py": "def alpha():\n    return 1\n",
        "src/b.py": "IMPORT src.a\n\ndef beta():\n    return 2\n",
    }
    engine, _walker, code_prescan = _make_engine(tmp_path, files)
    monkeypatch.setattr(engine, "_get_changed_files", set)

    first = engine.run()
    assert first.success
    assert code_prescan.calls == ["src/a.py", "src/b.py"]
    assert _cache_path(engine.config.output_dir).exists()

    code_prescan.calls.clear()
    second = engine.run(incremental=True)

    assert second.success
    assert code_prescan.calls == []
    assert second.warnings == []


def test_incremental_changed_file_recomputes_only_changed_entry(tmp_path: Path, monkeypatch) -> None:
    _patch_code_report_builder(monkeypatch)
    files = {
        "src/a.py": "def alpha():\n    return 1\n",
        "src/b.py": "IMPORT src.a\n\ndef beta():\n    return 2\n",
    }
    engine, walker, code_prescan = _make_engine(tmp_path, files)
    monkeypatch.setattr(engine, "_get_changed_files", lambda: {"src/b.py"})

    assert engine.run().success
    walker.files["src/b.py"] = "IMPORT src.a\n\ndef beta():\n    return 3\n"
    code_prescan.calls.clear()

    result = engine.run(incremental=True)

    assert result.success
    assert code_prescan.calls == ["src/b.py"]


def test_incremental_added_file_only_analyzes_new_entry(tmp_path: Path, monkeypatch) -> None:
    _patch_code_report_builder(monkeypatch)
    files = {"src/a.py": "def alpha():\n    return 1\n"}
    engine, walker, code_prescan = _make_engine(tmp_path, files)
    monkeypatch.setattr(engine, "_get_changed_files", lambda: {"src/new.py"})

    assert engine.run().success
    walker.files["src/new.py"] = "def added():\n    return 2\n"
    code_prescan.calls.clear()

    result = engine.run(incremental=True)

    assert result.success
    assert code_prescan.calls == ["src/new.py"]


def test_incremental_deleted_file_removes_cache_and_outputs(tmp_path: Path, monkeypatch) -> None:
    _patch_code_report_builder(monkeypatch)
    files = {
        "src/a.py": "def alpha():\n    return 1\n",
        "src/deleted.py": "def doomed():\n    return 0\n",
    }
    engine, walker, code_prescan = _make_engine(tmp_path, files)
    monkeypatch.setattr(engine, "_get_changed_files", lambda: {"src/deleted.py"})

    assert engine.run().success
    del walker.files["src/deleted.py"]
    code_prescan.calls.clear()

    result = engine.run(incremental=True)
    cache_payload = _load_json(_cache_path(engine.config.output_dir))
    manifest = _load_json(engine.config.output_dir / "corpus_manifest.json")

    assert result.success
    assert code_prescan.calls == []
    assert "src/deleted.py" not in cache_payload["files"]
    assert {entry["rel_path"] for entry in manifest} == {"src/a.py"}


def test_incremental_rename_treated_as_delete_plus_add(tmp_path: Path, monkeypatch) -> None:
    _patch_code_report_builder(monkeypatch)
    files = {"src/old.py": "def same_body():\n    return 1\n"}
    engine, walker, code_prescan = _make_engine(tmp_path, files)
    monkeypatch.setattr(engine, "_get_changed_files", lambda: {"src/old.py", "src/new.py"})

    assert engine.run().success
    walker.files["src/new.py"] = walker.files.pop("src/old.py")
    code_prescan.calls.clear()

    result = engine.run(incremental=True)
    cache_payload = _load_json(_cache_path(engine.config.output_dir))
    manifest = _load_json(engine.config.output_dir / "corpus_manifest.json")

    assert result.success
    assert code_prescan.calls == ["src/new.py"]
    assert "src/old.py" not in cache_payload["files"]
    assert "src/new.py" in cache_payload["files"]
    assert {entry["rel_path"] for entry in manifest} == {"src/new.py"}


def test_incremental_config_fingerprint_mismatch_forces_explicit_full_recompute(tmp_path: Path, monkeypatch) -> None:
    _patch_code_report_builder(monkeypatch)
    files = {"src/a.py": "def alpha():\n    return 1\n"}
    engine, _walker, code_prescan = _make_engine(tmp_path, files, code_languages=["python"])
    monkeypatch.setattr(engine, "_get_changed_files", set)

    assert engine.run().success

    second_engine, _second_walker, second_prescan = _make_engine(
        tmp_path,
        files,
        code_languages=["python", "typescript"],
    )
    monkeypatch.setattr(second_engine, "_get_changed_files", set)

    result = second_engine.run(incremental=True)

    assert result.success
    assert second_prescan.calls == ["src/a.py"]
    assert any("full recompute" in warning.lower() for warning in result.warnings)


def test_incremental_analyzer_fingerprint_mismatch_forces_explicit_full_recompute(tmp_path: Path, monkeypatch) -> None:
    _patch_code_report_builder(monkeypatch)
    files = {"src/a.py": "def alpha():\n    return 1\n"}
    engine, _walker, code_prescan = _make_engine(tmp_path, files)
    monkeypatch.setattr(engine, "_get_changed_files", set)

    assert engine.run().success
    cache_file = _cache_path(engine.config.output_dir)
    cache_payload = _load_json(cache_file)
    cache_payload["analyzer_fingerprint"] = "stale-analyzer"
    cache_file.write_text(json.dumps(cache_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    code_prescan.calls.clear()

    result = engine.run(incremental=True)

    assert result.success
    assert code_prescan.calls == ["src/a.py"]
    assert any("full recompute" in warning.lower() for warning in result.warnings)


def test_incremental_missing_cache_warns_and_recomputes_fully(tmp_path: Path, monkeypatch) -> None:
    _patch_code_report_builder(monkeypatch)
    files = {"src/a.py": "def alpha():\n    return 1\n"}
    engine, _walker, code_prescan = _make_engine(tmp_path, files)
    monkeypatch.setattr(engine, "_get_changed_files", set)

    result = engine.run(incremental=True)

    assert result.success
    assert code_prescan.calls == ["src/a.py"]
    assert any("full recompute" in warning.lower() for warning in result.warnings)
    assert _cache_path(engine.config.output_dir).exists()


def test_incremental_corrupted_cache_warns_and_recomputes_fully(tmp_path: Path, monkeypatch) -> None:
    _patch_code_report_builder(monkeypatch)
    files = {"src/a.py": "def alpha():\n    return 1\n"}
    engine, _walker, code_prescan = _make_engine(tmp_path, files)
    monkeypatch.setattr(engine, "_get_changed_files", set)

    cache_file = _cache_path(engine.config.output_dir)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text("{ not valid json }\n", encoding="utf-8")

    result = engine.run(incremental=True)

    assert result.success
    assert code_prescan.calls == ["src/a.py"]
    assert any("full recompute" in warning.lower() for warning in result.warnings)


def test_incremental_outputs_match_full_run_semantically(tmp_path: Path, monkeypatch) -> None:
    _patch_code_report_builder(monkeypatch)
    files = {
        "src/a.py": '"""doc"""\ndef alpha():\n    return 1\n',
        "src/b.py": "IMPORT src.a\n@click.command\ndef beta():\n    return 2\n",
    }
    engine, walker, _code_prescan = _make_engine(tmp_path, files, output_name="incremental_out")
    monkeypatch.setattr(engine, "_get_changed_files", lambda: {"src/b.py"})

    assert engine.run().success
    walker.files["src/b.py"] = "IMPORT src.a\n@click.command\ndef beta():\n    return 3\n"
    incremental = engine.run(incremental=True)
    assert incremental.success

    full_engine, full_walker, _full_prescan = _make_engine(
        tmp_path,
        dict(walker.files),
        output_name="full_out",
    )
    full_result = full_engine.run()
    assert full_result.success

    assert _normalized_outputs(engine.config.output_dir) == _normalized_outputs(full_engine.config.output_dir)
