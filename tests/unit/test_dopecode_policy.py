from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.serena.dopecode.runtime import DopeCodeRuntime


def test_dopecode_runtime_bundles_policy_and_layers(tmp_path: Path):
    runtime = DopeCodeRuntime(tmp_path, "ws-test")

    assert runtime.write_layer.policy is runtime.policy
    assert runtime.refactor_layer.policy is runtime.policy

    single_patch = runtime.policy.single_file_patch("pkg/module.py", preview=False)
    assert single_patch.operation_class == "single_file_patch"
    assert single_patch.preview_required is False
    assert single_patch.blast_radius == 1

    batch_patch = runtime.policy.batch_patch(
        [{"path": "b.py", "diff": "x"}, {"path": "a.py", "diff": "y"}],
        preview=True,
    )
    assert batch_patch.operation_class == "multi_file_patch"
    assert batch_patch.preview_required is True
    assert batch_patch.affected_files == ["a.py", "b.py"]

    refactor = runtime.policy.refactor(
        "rename_symbol",
        "ws-test::pkg/module.py::run::1",
        ["pkg/a.py", "pkg/b.py"],
        preview=True,
    )
    assert refactor.operation_class == "symbol_refactor"
    assert refactor.approval_level == "multi_file"
    assert refactor.blast_radius == 2
