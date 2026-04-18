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


@pytest.mark.asyncio
async def test_ast_engine_javascript_navigation_surfaces(tmp_path: Path):
    _write(
        tmp_path / "pkg" / "helper.js",
        "export function helper(value) {\n"
        "  return value + 1;\n"
        "}\n",
    )
    _write(
        tmp_path / "pkg" / "main.js",
        "import helper from \"./helper\";\n\n"
        "export function run(value) {\n"
        "  return helper(value) + localHelper();\n"
        "}\n\n"
        "const localHelper = () => {\n"
        "  return 2;\n"
        "};\n\n"
        "class Demo {\n"
        "  method() {\n"
        "    return helper(value);\n"
        "  }\n"
        "}\n",
    )

    engine = ASTEngine(tmp_path, "ws-test")

    symbols = await engine.get_file_symbols("pkg/main.js")
    names = [item["name"] for item in symbols["symbols"]]
    assert names == ["run", "localHelper", "Demo"]

    run_symbol_id = next(item["symbol_id"] for item in symbols["symbols"] if item["name"] == "run")

    callees = await engine.find_callees(run_symbol_id)
    assert callees["callee_count"] == 2
    assert [item["name"] for item in callees["callees"]] == ["helper", "localHelper"]
    assert callees["callees"][0]["kind"] == "import"
    assert callees["callees"][0]["resolved_file"] == "pkg/helper.js"
    assert callees["callees"][1]["kind"] == "local_symbol"
    assert callees["resolution_mode"] == "javascript_ast"

    imports = await engine.get_import_graph("pkg/main.js")
    assert imports["imports"]["pkg/main.js"][0]["module"] == "./helper"
    assert imports["imports"]["pkg/main.js"][0]["resolved_path"] == "pkg/helper.js"

    matches = await engine.search_pattern("helper", relative_path="pkg/main.js", max_results=10)
    locations = [(item["file"], item["line"]) for item in matches["results"]]
    assert ("pkg/main.js", 1) in locations


@pytest.mark.asyncio
async def test_ast_engine_typescript_navigation_surfaces(tmp_path: Path):
    _write(
        tmp_path / "pkg" / "helper.ts",
        "export function helper(value: string): number {\n"
        "  return value.length;\n"
        "}\n",
    )
    _write(
        tmp_path / "pkg" / "types.ts",
        "export interface Thing {\n"
        "  x: number;\n"
        "}\n",
    )
    _write(
        tmp_path / "pkg" / "main.tsx",
        "import helper from \"./helper\";\n\n"
        "import type { Thing } from \"./types\";\n\n"
        "export function run(value: string): number {\n"
        "  return helper(value) + localHelper();\n"
        "}\n\n"
        "const localHelper = (): number => {\n"
        "  return 2;\n"
        "}\n",
    )

    engine = ASTEngine(tmp_path, "ws-test")

    symbols = await engine.get_file_symbols("pkg/main.tsx")
    names = [item["name"] for item in symbols["symbols"]]
    assert names == ["run", "localHelper"]

    run_symbol_id = next(item["symbol_id"] for item in symbols["symbols"] if item["name"] == "run")

    callees = await engine.find_callees(run_symbol_id)
    assert callees["callee_count"] == 2
    assert [item["name"] for item in callees["callees"]] == ["helper", "localHelper"]
    assert callees["callees"][0]["kind"] == "import"
    assert callees["callees"][0]["resolved_file"] == "pkg/helper.ts"
    assert callees["resolution_mode"] == "typescript_ast"

    imports = await engine.get_import_graph("pkg/main.tsx")
    assert len(imports["imports"]["pkg/main.tsx"]) == 1
    assert imports["imports"]["pkg/main.tsx"][0]["module"] == "./helper"
    assert imports["imports"]["pkg/main.tsx"][0]["resolved_path"] == "pkg/helper.ts"

    matches = await engine.search_pattern("helper", relative_path="pkg/main.tsx", max_results=10)
    locations = [(item["file"], item["line"]) for item in matches["results"]]
    assert ("pkg/main.tsx", 1) in locations
