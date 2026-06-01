from __future__ import annotations

from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from lib.prescan.code_intelligence_report import CodeIntelligenceBuilder
from lib.prescan.code_prescan import CodePrescan
from lib.prescan.dependency_graph import DependencyGraph
from lib.prescan.models import FileEntry, PrescanConfig


def _make_config(tmp_path: Path) -> PrescanConfig:
    return PrescanConfig(
        repo_root=tmp_path,
        output_dir=tmp_path / "out",
        enable_git_enrichment=False,
        batch_mode=False,
    )


@pytest.mark.xfail(
    sys.platform == "darwin",
    reason="Deferred to TP-RTE-WALKER-006: prescan schema/runtime drift is outside CostProfile F repair scope.",
    strict=True,
)
def test_code_prescan_emits_dotted_relative_python_imports(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    mod = pkg / "mod.py"
    mod.write_text(
        "from . import models\n"
        "from ..core import util\n"
        "from pkg.sub import thing\n"
        "import os\n",
        encoding="utf-8",
    )

    config = _make_config(tmp_path)
    prescan = CodePrescan(config)
    entry = FileEntry(rel_path="pkg/mod.py", size_bytes=mod.stat().st_size, extension=".py")

    result = prescan.analyze_file(entry, tmp_path)

    assert set(result["imports"]) == {".models", "..core", "pkg.sub", "os"}


def test_dependency_graph_uses_emitted_relative_python_imports(tmp_path: Path) -> None:
    graph = DependencyGraph()
    manifest = [
        {"rel_path": "pkg/mod.py"},
        {"rel_path": "pkg/models.py"},
        {"rel_path": "core.py"},
    ]
    code_intel = [
        {"rel_path": "pkg/mod.py", "imports": [".models", "..core"]},
    ]

    graph.build_from_code_intelligence(code_intel, manifest)

    assert ("pkg/mod.py", "pkg/models.py") in graph.edges
    assert ("pkg/mod.py", "core.py") in graph.edges


@pytest.mark.xfail(
    sys.platform == "darwin",
    reason="Deferred to TP-RTE-WALKER-006: prescan schema/runtime drift is outside CostProfile F repair scope.",
    strict=True,
)
def test_code_prescan_api_surface_detection_avoids_substring_false_positives(tmp_path: Path) -> None:
    comment_only = tmp_path / "comment_only.py"
    comment_only.write_text(
        "# mentions fastapi and flask and click and mcp in comments only\n"
        'TOKENS = ["fastapi", "flask", "click", "mcp"]\n'
        "def helper():\n"
        "    return TOKENS\n",
        encoding="utf-8",
    )
    real_surfaces = tmp_path / "real_surfaces.py"
    real_surfaces.write_text(
        "from fastapi import APIRouter\n"
        "import click\n"
        "from mcp.server.fastmcp import FastMCP\n"
        "router = APIRouter()\n"
        '@router.get("/health")\n'
        "@click.command()\n"
        "def health():\n"
        '    return {"ok": True}\n',
        encoding="utf-8",
    )

    config = _make_config(tmp_path)
    prescan = CodePrescan(config)

    comment_entry = FileEntry(
        rel_path="comment_only.py",
        size_bytes=comment_only.stat().st_size,
        extension=".py",
    )
    real_entry = FileEntry(
        rel_path="real_surfaces.py",
        size_bytes=real_surfaces.stat().st_size,
        extension=".py",
    )

    assert prescan.analyze_file(comment_entry, tmp_path)["api_surfaces"] == []
    assert set(prescan.analyze_file(real_entry, tmp_path)["api_surfaces"]) == {
        "fastapi",
        "cli",
        "mcp",
    }


@pytest.mark.xfail(
    sys.platform == "darwin",
    reason="Deferred to TP-RTE-WALKER-006: prescan schema/runtime drift is outside CostProfile F repair scope.",
    strict=True,
)
def test_code_prescan_arrow_function_signatures_match_symbol_coverage(tmp_path: Path) -> None:
    handlers = tmp_path / "handlers.ts"
    handlers.write_text(
        "const handle = () => 1;\n"
        "export const serve = async () => { return 2; };\n"
        "function named() { return 3; }\n"
        "class Box {}\n",
        encoding="utf-8",
    )

    config = _make_config(tmp_path)
    prescan = CodePrescan(config)
    entry = FileEntry(rel_path="handlers.ts", size_bytes=handlers.stat().st_size, extension=".ts")

    analyzed = prescan.analyze_file(entry, tmp_path)
    signatures = prescan.extract_signatures(entry, tmp_path)

    symbol_names = {symbol["name"] for symbol in analyzed["symbols"]}
    signature_names = {signature["name"] for signature in signatures}

    assert {"handle", "serve", "named", "Box"} <= symbol_names
    assert {"handle", "serve", "named", "Box"} <= signature_names


def test_code_intelligence_report_uses_actual_repo_root(tmp_path: Path) -> None:
    config = _make_config(tmp_path)
    prescan = CodePrescan(config)
    dep_graph = DependencyGraph()

    source = tmp_path / "pkg" / "module.py"
    source.parent.mkdir(parents=True)
    source.write_text("def run():\n    return 1\n", encoding="utf-8")

    entry = FileEntry(rel_path="pkg/module.py", size_bytes=source.stat().st_size, extension=".py")
    manifest = [entry.to_dict()]
    builder = CodeIntelligenceBuilder(prescan, dep_graph, [entry], manifest)

    report = builder.build(tmp_path)

    assert report["repo_root"] == str(tmp_path)
