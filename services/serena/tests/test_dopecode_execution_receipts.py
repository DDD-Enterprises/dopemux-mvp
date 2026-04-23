import json
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = REPO_ROOT / "src"
for candidate in (REPO_ROOT, SRC_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from dopemux.execution.dopecode_receipts import (
    DopeCodeReceiptReadError,
    build_dopecode_execution_history_view,
    load_dopecode_execution_receipts,
    replay_dopecode_execution_receipts,
)
from services.serena.dopecode.execution_receipts import (
    DOPECODE_EXECUTION_RECEIPT_RELATIVE_PATH,
    DopeCodeExecutionReceiptStore,
    ReceiptReplayMismatchError,
)
from services.serena.dopecode.navigation.ast_engine import ASTEngine
from services.serena.dopecode.transform.refactor_layer import RefactorLayer
from services.serena.dopecode.transform.write_layer import WriteLayer


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_apply_patch_emits_durable_execution_receipt_and_deduplicates_replay(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "pkg" / "module.py"
    _write(target, "alpha = 1\nbeta = 2\ngamma = 3\n")

    layer = WriteLayer(workspace, "ws-test")
    diff_text = """--- a/pkg/module.py\n+++ b/pkg/module.py\n@@ -1,3 +1,3 @@\n alpha = 1\n-beta = 2\n+beta = 20\n gamma = 3\n"""

    result = layer.apply_patch("pkg/module.py", diff_text)

    execution_receipt = result["execution_receipt"]
    assert execution_receipt["persistence"]["status"] == "recorded"
    assert execution_receipt["event"]["event_type"] == "dopecode.mutation.applied"
    assert execution_receipt["event"]["operation"] == "apply_patch"
    assert execution_receipt["event"]["payload"]["files"] == ["pkg/module.py"]

    recorded = load_dopecode_execution_receipts(workspace)
    assert len(recorded) == 1
    assert recorded[0]["event_id"] == execution_receipt["event"]["event_id"]

    store = DopeCodeExecutionReceiptStore(workspace, "ws-test")
    replayed_event, replay_status = store.append_event(execution_receipt["event"])
    assert replay_status == "replayed"
    assert replayed_event["event_id"] == execution_receipt["event"]["event_id"]
    assert len(load_dopecode_execution_receipts(workspace)) == 1


def test_execution_receipt_store_fails_closed_on_idempotency_mismatch(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    store = DopeCodeExecutionReceiptStore(workspace, "ws-test")

    event = store.build_event(
        event_type="dopecode.mutation.applied",
        lifecycle_stage="apply",
        operation="apply_patch",
        operation_class="single_file_patch",
        execution_mode="direct",
        execution_status="ready",
        mutation_context={"path": "pkg/module.py", "diff_sha256": "abc"},
        payload={"status": "applied", "summary": "ok", "files": ["pkg/module.py"]},
        ts_utc="2026-04-18T12:00:00Z",
    )
    store.append_event(event)

    conflicting = dict(event)
    conflicting["payload"] = {"status": "failed", "summary": "different", "files": ["pkg/module.py"]}

    with pytest.raises(ReceiptReplayMismatchError):
        store.append_event(conflicting)


def test_dopemux_reader_rejects_unsupported_event_type(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    store = DopeCodeExecutionReceiptStore(workspace, "ws-test")
    event = store.build_event(
        event_type="dopecode.mutation.applied",
        lifecycle_stage="apply",
        operation="apply_patch",
        operation_class="single_file_patch",
        execution_mode="direct",
        execution_status="ready",
        mutation_context={"path": "pkg/module.py", "diff_sha256": "abc"},
        payload={"status": "applied", "summary": "ok", "files": ["pkg/module.py"]},
        ts_utc="2026-04-18T12:00:00Z",
    )
    event["event_type"] = "dopecode.mutation.unknown"
    ledger_path = workspace / DOPECODE_EXECUTION_RECEIPT_RELATIVE_PATH
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(f"{json.dumps(event)}\n", encoding="utf-8")

    with pytest.raises(DopeCodeReceiptReadError, match="Unsupported execution receipt event type"):
        load_dopecode_execution_receipts(workspace)


def test_dopemux_reader_rejects_workspace_id_mismatch(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    store = DopeCodeExecutionReceiptStore(workspace, "ws-test")
    event = store.build_event(
        event_type="dopecode.mutation.applied",
        lifecycle_stage="apply",
        operation="apply_patch",
        operation_class="single_file_patch",
        execution_mode="direct",
        execution_status="ready",
        mutation_context={"path": "pkg/module.py", "diff_sha256": "abc"},
        payload={"status": "applied", "summary": "ok", "files": ["pkg/module.py"]},
        ts_utc="2026-04-18T12:00:00Z",
    )
    store.append_event(event)

    with pytest.raises(DopeCodeReceiptReadError, match="Execution receipt workspace_id mismatch"):
        load_dopecode_execution_receipts(workspace, expected_workspace_id="ws-other")


@pytest.mark.asyncio
async def test_dopemux_history_view_consumes_preview_and_apply_receipts_without_duplicates(tmp_path: Path):
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
    applied = await refactor.rename_symbol(run_symbol_id, "execute", preview=False)

    ledger_events = load_dopecode_execution_receipts(workspace)
    assert [event["event_type"] for event in ledger_events] == [
        "dopecode.mutation.previewed",
        "dopecode.mutation.applied",
    ]

    replayed = replay_dopecode_execution_receipts(
        [*ledger_events, preview["execution_receipt"]["event"], applied["execution_receipt"]["event"]]
    )
    view = build_dopecode_execution_history_view(replayed)

    assert view["event_count"] == 2
    assert view["timeline"][0]["display"].endswith(
        "Preview mode. Pass preview=False to apply the refactor."
    )
    assert "Renamed run to execute." in view["timeline"][1]["display"]
    assert view["timeline"][1]["orchestration"]["plan_status"] == "verified"
    assert view["active_plans"]["plan_count"] == 1
    assert view["active_plans"]["plans"][0]["next_action"] == "none"


@pytest.mark.asyncio
async def test_dopemux_orchestration_view_reports_blocked_current_step(tmp_path: Path):
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
    await refactor.rename_symbol(run_symbol_id, "execute", preview=False)

    ledger_events = load_dopecode_execution_receipts(workspace)
    view = build_dopecode_execution_history_view(ledger_events)

    assert view["active_plans"]["plan_count"] == 1
    active = view["active_plans"]["plans"][0]
    assert active["plan_status"] == "blocked"
    assert active["next_action"] == "resume"
    assert active["current_step_title"] == "Rename references in pkg/other.py"
