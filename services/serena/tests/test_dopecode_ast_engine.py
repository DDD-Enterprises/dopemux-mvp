from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.serena.dopecode.navigation.ast_engine import ASTEngine


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.mark.asyncio
async def test_ast_engine_navigation_surfaces(tmp_path: Path):
    _write(
        tmp_path / "pkg" / "helpers.py",
        "def helper():\n    return 1\n",
    )
    _write(
        tmp_path / "pkg" / "main.py",
        "from pkg.helpers import helper\n\n"
        "def local_helper():\n"
        "    return 2\n\n"
        "def run():\n"
        "    return helper() + local_helper()\n\n"
        "def caller():\n"
        "    return run()\n",
    )

    engine = ASTEngine(tmp_path, "ws-test")

    symbols = await engine.get_file_symbols("pkg/main.py")
    names = [item["name"] for item in symbols["symbols"]]
    assert names == ["local_helper", "run", "caller"]

    run_symbol_id = next(item["symbol_id"] for item in symbols["symbols"] if item["name"] == "run")

    callers = await engine.find_callers(run_symbol_id)
    assert callers["caller_count"] == 1
    assert callers["callers"][0]["caller"] == "caller"

    callees = await engine.find_callees(run_symbol_id)
    assert callees["callee_count"] == 2
    assert [item["name"] for item in callees["callees"]] == ["helper", "local_helper"]
    assert callees["callees"][0]["kind"] == "from_import"
    assert callees["callees"][0]["resolved_file"] == "pkg/helpers.py"
    assert callees["callees"][1]["kind"] == "local_symbol"
    assert callees["resolution_mode"] == "python_ast"

    imports = await engine.get_import_graph("pkg/main.py")
    assert imports["imports"]["pkg/main.py"][0]["module"] == "pkg.helpers"
    assert imports["imports"]["pkg/main.py"][0]["resolved_path"] == "pkg/helpers.py"

    matches = await engine.search_pattern("helper", max_results=10)
    locations = [(item["file"], item["line"]) for item in matches["results"]]
    assert ("pkg/helpers.py", 1) in locations
    assert ("pkg/main.py", 1) in locations
