from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.serena.dopecode.navigation.ast_engine import ASTEngine
from services.serena.dopecode.transform.refactor_layer import RefactorLayer
from services.serena.dopecode.transform.write_layer import WriteLayer


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.mark.asyncio
async def test_rename_symbol_preview_and_apply_are_workspace_bounded(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _write(
        workspace / "pkg" / "mod.py",
        "def run():\n"
        "    return helper()\n\n"
        "def helper():\n"
        "    return 1\n",
    )
    _write(
        workspace / "pkg" / "other.py",
        "from pkg.mod import run\n\n"
        "def outer():\n"
        "    return run()\n",
    )

    engine = ASTEngine(workspace, "ws-test")
    write_layer = WriteLayer(workspace, "ws-test")
    refactor = RefactorLayer(write_layer, engine)

    symbols = await engine.get_file_symbols("pkg/mod.py")
    run_symbol_id = symbols["symbols"][0]["symbol_id"]

    preview = await refactor.rename_symbol(run_symbol_id, "execute", preview=True)
    assert preview["status"] == "preview"
    assert preview["approval_receipt"]["execution_mode"] == "preview_required"
    assert preview["approval_receipt"]["execution_status"] == "preview_only"
    assert preview["execution_receipt"]["event"]["event_type"] == "dopecode.mutation.previewed"
    assert preview["files_affected"] == ["pkg/mod.py", "pkg/other.py"]
    assert preview["refactor_plan"]["confidence"] == "medium"
    assert preview["refactor_plan"]["affected_file_summary"]["count"] == 2
    assert workspace.joinpath("pkg", "mod.py").read_text(encoding="utf-8").startswith("def run():")

    result = await refactor.rename_symbol(run_symbol_id, "execute", preview=False)
    assert result["status"] == "applied"
    assert result["approval_receipt"]["execution_mode"] == "approval_required"
    assert result["execution_receipt"]["event"]["event_type"] == "dopecode.mutation.applied"
    assert workspace.joinpath("pkg", "mod.py").read_text(encoding="utf-8").startswith("def execute():")
    assert "run" not in workspace.joinpath("pkg", "other.py").read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_rename_symbol_resume_is_explicit_and_reuses_prior_successful_steps(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _write(
        workspace / "pkg" / "mod.py",
        "def run():\n"
        "    return helper()\n\n"
        "def helper():\n"
        "    return 1\n",
    )
    _write(
        workspace / "pkg" / "other.py",
        "from pkg.mod import run\n\n"
        "def outer():\n"
        "    return run()\n",
    )

    engine = ASTEngine(workspace, "ws-test")
    write_layer = WriteLayer(workspace, "ws-test")
    refactor = RefactorLayer(write_layer, engine)

    symbols = await engine.get_file_symbols("pkg/mod.py")
    run_symbol_id = symbols["symbols"][0]["symbol_id"]

    real_apply_patch = write_layer.apply_patch
    call_count = {"value": 0}

    def flaky_apply_patch(relative_path: str, diff_text: str, emit_receipt: bool = True):
        result = real_apply_patch(relative_path, diff_text, emit_receipt=emit_receipt)
        call_count["value"] += 1
        if call_count["value"] == 1:
            workspace.joinpath("pkg", "other.py").write_text(
                "from pkg.mod import run\n\n"
                "def outer():\n"
                "    return run() + 1\n",
                encoding="utf-8",
            )
        return result

    write_layer.apply_patch = flaky_apply_patch  # type: ignore[method-assign]
    first = await refactor.rename_symbol(run_symbol_id, "execute", preview=False)

    assert first["status"] == "partial_failure"
    assert first["execution_plan"]["plan_status"] == "blocked"
    assert first["execution_plan"]["next_action"] == "resume"
    assert workspace.joinpath("pkg", "mod.py").read_text(encoding="utf-8").startswith("def execute():")
    assert workspace.joinpath("pkg", "other.py").read_text(encoding="utf-8").endswith("return run() + 1\n")

    write_layer.apply_patch = real_apply_patch  # type: ignore[method-assign]
    no_resume = await refactor.rename_symbol(run_symbol_id, "execute", preview=False)
    assert no_resume["status"] == "partial_failure"
    assert no_resume["message"] == "Resume is required to continue the existing bounded plan."

    workspace.joinpath("pkg", "other.py").write_text(
        "from pkg.mod import run\n\n"
        "def outer():\n"
        "    return run()\n",
        encoding="utf-8",
    )
    resumed = await refactor.rename_symbol(run_symbol_id, "execute", preview=False, resume=True)

    assert resumed["status"] == "applied"
    assert resumed["execution_plan"]["plan_status"] == "verified"
    assert resumed["execution_plan"]["completed_step_count"] == resumed["execution_plan"]["step_count"]
    assert workspace.joinpath("pkg", "mod.py").read_text(encoding="utf-8").startswith("def execute():")
    assert "run" not in workspace.joinpath("pkg", "other.py").read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_replace_symbol_body_preview_and_apply_preserve_signature(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _write(
        workspace / "pkg" / "mod.py",
        "def run():\n"
        "    value = helper()\n"
        "    return value\n\n"
        "def helper():\n"
        "    return 1\n",
    )

    engine = ASTEngine(workspace, "ws-test")
    write_layer = WriteLayer(workspace, "ws-test")
    refactor = RefactorLayer(write_layer, engine)

    symbols = await engine.get_file_symbols("pkg/mod.py")
    run_symbol_id = symbols["symbols"][0]["symbol_id"]

    preview = await refactor.replace_symbol_body(
        run_symbol_id,
        "result = helper()\nreturn result",
        preview=True,
    )
    assert preview["status"] == "preview"
    assert preview["approval_receipt"]["execution_mode"] == "preview_required"
    assert preview["execution_receipt"]["event"]["event_type"] == "dopecode.mutation.previewed"
    assert preview["refactor_plan"]["confidence"] == "high"
    assert preview["refactor_plan"]["target_symbol"] == "run"
    assert preview["line_span"]["body_start_line"] == 2

    result = await refactor.replace_symbol_body(
        run_symbol_id,
        "result = helper()\nreturn result",
        preview=False,
    )
    assert result["status"] == "applied"
    assert result["approval_receipt"]["execution_mode"] == "approval_required"
    assert result["execution_receipt"]["event"]["event_type"] == "dopecode.mutation.applied"
    assert workspace.joinpath("pkg", "mod.py").read_text(encoding="utf-8") == (
        "def run():\n"
        "    result = helper()\n"
        "    return result\n\n"
        "def helper():\n"
        "    return 1\n"
    )


@pytest.mark.asyncio
async def test_replace_symbol_body_preview_and_apply_support_javascript(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _write(
        workspace / "pkg" / "mod.js",
        "import helper from \"./helper\";\n\n"
        "export function run(value) {\n"
        "  const result = helper(value);\n"
        "  return result + localHelper();\n"
        "}\n\n"
        "const localHelper = () => {\n"
        "  return 2;\n"
        "};\n",
    )

    engine = ASTEngine(workspace, "ws-test")
    write_layer = WriteLayer(workspace, "ws-test")
    refactor = RefactorLayer(write_layer, engine)

    symbols = await engine.get_file_symbols("pkg/mod.js")
    run_symbol_id = next(item["symbol_id"] for item in symbols["symbols"] if item["name"] == "run")

    preview = await refactor.replace_symbol_body(
        run_symbol_id,
        "const value = helper(value)\nreturn value",
        preview=True,
    )
    assert preview["status"] == "preview"
    assert preview["approval_receipt"]["execution_mode"] == "preview_required"
    assert preview["approval_receipt"]["reason"] == "Symbol refactors must surface blast radius before apply."
    assert preview["execution_receipt"]["event"]["event_type"] == "dopecode.mutation.previewed"
    assert preview["line_span"]["body_start_line"] == 4

    result = await refactor.replace_symbol_body(
        run_symbol_id,
        "const value = helper(value)\nreturn value",
        preview=False,
    )
    assert result["status"] == "applied"
    assert result["approval_receipt"]["execution_mode"] == "approval_required"
    assert result["execution_receipt"]["event"]["event_type"] == "dopecode.mutation.applied"
    assert workspace.joinpath("pkg", "mod.js").read_text(encoding="utf-8") == (
        "import helper from \"./helper\";\n\n"
        "export function run(value) {\n"
        "  const value = helper(value)\n"
        "  return value\n"
        "}\n\n"
        "const localHelper = () => {\n"
        "  return 2;\n"
        "};\n"
    )


@pytest.mark.asyncio
async def test_replace_symbol_body_preview_and_apply_support_typescript_block_functions(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _write(
        workspace / "pkg" / "mod.ts",
        "import helper from \"./helper\";\n\n"
        "export function run(value: string): number {\n"
        "  const result = helper(value);\n"
        "  return result + localHelper();\n"
        "}\n\n"
        "const localHelper = (): number => {\n"
        "  return 2;\n"
        "};\n"
        "\n"
        "const inlineHelper = (): number => 3;\n"
    )

    engine = ASTEngine(workspace, "ws-test")
    write_layer = WriteLayer(workspace, "ws-test")
    refactor = RefactorLayer(write_layer, engine)

    symbols = await engine.get_file_symbols("pkg/mod.ts")
    run_symbol_id = next(item["symbol_id"] for item in symbols["symbols"] if item["name"] == "run")

    preview = await refactor.replace_symbol_body(
        run_symbol_id,
        "const value = helper(value)\nreturn value",
        preview=True,
    )
    assert preview["status"] == "preview"
    assert preview["approval_receipt"]["execution_mode"] == "preview_required"
    assert preview["execution_receipt"]["event"]["event_type"] == "dopecode.mutation.previewed"
    assert preview["refactor_plan"]["affected_file_summary"]["files"] == ["pkg/mod.ts"]
    assert preview["line_span"]["body_start_line"] == 4

    result = await refactor.replace_symbol_body(
        run_symbol_id,
        "const value = helper(value)\nreturn value",
        preview=False,
    )
    assert result["status"] == "applied"
    assert result["approval_receipt"]["execution_mode"] == "approval_required"
    assert result["execution_receipt"]["event"]["event_type"] == "dopecode.mutation.applied"
    assert workspace.joinpath("pkg", "mod.ts").read_text(encoding="utf-8") == (
        "import helper from \"./helper\";\n\n"
        "export function run(value: string): number {\n"
        "  const value = helper(value)\n"
        "  return value\n"
        "}\n\n"
        "const localHelper = (): number => {\n"
        "  return 2;\n"
        "};\n"
        "\n"
        "const inlineHelper = (): number => 3;\n"
    )

    inline_helper_symbol_id = next(item["symbol_id"] for item in symbols["symbols"] if item["name"] == "inlineHelper")

    with pytest.raises(NotImplementedError):
        await refactor.replace_symbol_body(
            inline_helper_symbol_id,
            "return 3",
            preview=True,
        )

    with pytest.raises(ValueError):
        await refactor.replace_symbol_body(
            run_symbol_id,
            "",
            preview=True,
        )
