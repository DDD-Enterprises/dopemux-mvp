import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/generate_pal_model_manifest.py"


def test_generated_pal_manifests_are_current():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_check_mode_detects_drift_without_writing(tmp_path):
    output_root = tmp_path / "conf"
    output_root.mkdir()
    stale = output_root / "custom_models.direct-ci.json"
    stale.write_text("{}\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--check",
            "--output-dir",
            str(output_root),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert stale.read_text(encoding="utf-8") == "{}\n"


def test_generated_manifests_load_through_pal_custom_registry():
    conf = ROOT / "docker/mcp-servers-source/pal/pal-mcp-server/conf"
    pal_root = conf.parent
    code = """
from providers.registries.custom import CustomEndpointModelRegistry
import sys

direct = CustomEndpointModelRegistry(sys.argv[1])
gateway = CustomEndpointModelRegistry(sys.argv[2])
assert direct.resolve('kimi-k3') is not None
assert direct.resolve('claude-fable-5') is not None
assert gateway.resolve('kimi-k3-ci') is not None
assert gateway.resolve('fable-5-ci') is not None
assert gateway.resolve('kimi-k3-or') is None
"""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            code,
            str(conf / "custom_models.direct-ci.json"),
            str(conf / "custom_models.gateway.json"),
        ],
        cwd=pal_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
