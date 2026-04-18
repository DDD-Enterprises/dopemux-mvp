from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.serena.dopecode.runtime import DopeCodeRuntime


def test_dopecode_runtime_bundles_policy_and_layers(tmp_path: Path):
    runtime = DopeCodeRuntime(tmp_path, "ws-test")

    assert runtime.write_layer.policy is runtime.policy
    assert runtime.refactor_layer.policy is runtime.policy
    assert runtime.write_layer.receipt_store is runtime.execution_receipts

    single_patch = runtime.policy.single_file_patch("pkg/module.py", preview=False)
    assert single_patch.operation_class == "single_file_patch"
    assert single_patch.preview_required is False
    assert single_patch.execution_mode == "direct"
    assert single_patch.requires_approval is False
    assert single_patch.blast_radius == 1
    assert single_patch.approval_receipt()["execution_mode"] == "direct"
    assert single_patch.approval_receipt()["execution_status"] == "ready"
    assert single_patch.approval_receipt()["risk_tier"] == "low"

    batch_patch = runtime.policy.batch_patch(
        [{"path": "b.py", "diff": "x"}, {"path": "a.py", "diff": "y"}],
        preview=True,
    )
    assert batch_patch.operation_class == "multi_file_patch"
    assert batch_patch.preview_required is True
    assert batch_patch.execution_mode == "preview_required"
    assert batch_patch.requires_approval is False
    assert batch_patch.affected_files == ["a.py", "b.py"]
    assert batch_patch.approval_receipt()["execution_mode"] == "preview_required"
    assert batch_patch.approval_receipt()["execution_status"] == "preview_only"
    assert batch_patch.approval_receipt()["affected_file_summary"]["count"] == 2

    batch_apply = runtime.policy.batch_patch(
        [{"path": "b.py", "diff": "x"}, {"path": "a.py", "diff": "y"}],
        preview=False,
    )
    assert batch_apply.execution_mode == "approval_required"
    assert batch_apply.requires_approval is True
    assert batch_apply.approval_receipt()["execution_mode"] == "approval_required"
    assert batch_apply.approval_receipt()["execution_status"] == "approval_required"

    refactor = runtime.policy.refactor(
        "rename_symbol",
        "ws-test::pkg/module.py::run::1",
        ["pkg/a.py", "pkg/b.py"],
        preview=True,
    )
    assert refactor.operation_class == "symbol_refactor"
    assert refactor.approval_level == "multi_file"
    assert refactor.execution_mode == "preview_required"
    assert refactor.requires_approval is False
    assert refactor.blast_radius == 2
    assert refactor.approval_receipt()["execution_mode"] == "preview_required"
    assert refactor.approval_receipt()["risk_tier"] == "high"
    assert "blast radius" in refactor.approval_receipt()["reason"]

    refactor_apply = runtime.policy.refactor(
        "rename_symbol",
        "ws-test::pkg/module.py::run::1",
        ["pkg/a.py", "pkg/b.py"],
        preview=False,
    )
    assert refactor_apply.execution_mode == "approval_required"
    assert refactor_apply.requires_approval is True
    assert refactor_apply.approval_receipt()["execution_mode"] == "approval_required"
    assert refactor_apply.approval_receipt()["execution_status"] == "approval_required"
