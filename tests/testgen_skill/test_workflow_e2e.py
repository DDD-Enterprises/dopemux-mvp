from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _workflow_cli() -> Path:
    return Path(__file__).resolve().parents[2] / "templates" / "skills" / "testgen" / "scripts" / "testgen_cli.py"


def _write_coverage_xml(path: Path, filename: str, hits: list[int]) -> None:
    lines_xml = "\n".join(
        f'<line number="{idx + 1}" hits="{hit}"/>' for idx, hit in enumerate(hits)
    )
    path.write_text(
        (
            "<coverage><packages><package name=\"pkg\"><classes>"
            f"<class name=\"x\" filename=\"{filename}\"><lines>{lines_xml}</lines></class>"
            "</classes></package></packages></coverage>"
        ),
        encoding="utf-8",
    )


def test_python_fixture_tdd_driver(tmp_path: Path):
    coverage_xml = tmp_path / "coverage.xml"
    _write_coverage_xml(coverage_xml, "src/auth.py", [1] * 9 + [0])

    command = [
        sys.executable,
        str(_workflow_cli()),
        "--mode",
        "tdd-driver",
        "--source",
        "feature-list",
        "--payload",
        "- Validate login success\n- Validate login failure",
        "--repo-root",
        str(tmp_path),
        "--coverage-xml",
        str(coverage_xml),
        "--touched-file",
        "src/auth.py",
    ]

    result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr

    report = json.loads(result.stdout)
    assert report["request"]["mode"] == "tdd-driver"
    assert report["coverage_gate"]["status"] == "pass"
    assert report["coverage_gate"]["percent"] >= 90


def test_js_fixture_post_impl_generator(tmp_path: Path):
    packet = tmp_path / "packet.md"
    packet.write_text(
        """
        ## Objective

        Prevent checkout regression for invalid discount codes.

        ## Scope

        IN:

        - Validate API workflow for discount validation

        OUT:

        - Payment redesign

        ## Acceptance Criteria

        - Invalid codes return deterministic error payload
        """.strip(),
        encoding="utf-8",
    )

    coverage_xml = tmp_path / "coverage.xml"
    _write_coverage_xml(coverage_xml, "src/checkout.ts", [1] * 10)

    command = [
        sys.executable,
        str(_workflow_cli()),
        "--mode",
        "post-impl-generator",
        "--source",
        "task-packet",
        "--payload-file",
        str(packet),
        "--repo-root",
        str(tmp_path),
        "--coverage-xml",
        str(coverage_xml),
        "--touched-file",
        "src/checkout.ts",
        "--preferred-cli",
        "copilot",
    ]

    result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr

    report = json.loads(result.stdout)
    assert report["request"]["mode"] == "post-impl-generator"
    assert report["coverage_gate"]["status"] == "pass"
    layers = {entry["layer"]: entry["applicable"] for entry in report["layer_plan"]}
    assert layers["regression"] is True
