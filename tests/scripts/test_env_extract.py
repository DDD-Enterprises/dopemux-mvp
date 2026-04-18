from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "env_extract.py"
SPEC = importlib.util.spec_from_file_location("env_extract", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_extract_outputs_are_deduplicated_and_stable(tmp_path: Path) -> None:
    root = tmp_path
    (root / "pyproject.toml").write_text(
        """
[project]
dependencies = ["click>=8.0.0", "requests>=2.28.0"]

[project.optional-dependencies]
test = ["pytest>=9.0.3"]
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (root / "requirements.txt").write_text("requests>=2.28.0\nblack>=23.0.0\n", encoding="utf-8")
    (root / "package.json").write_text(
        json.dumps({"dependencies": {"next": "15.5.15"}, "devDependencies": {"typescript": "5.6.2"}}),
        encoding="utf-8",
    )
    (root / ".env.example").write_text(
        "OPENAI_API_KEY=your_openai_api_key_here\nFRONTEND_API_URL=http://localhost:8000\n",
        encoding="utf-8",
    )
    docs_dir = root / "docs"
    docs_dir.mkdir()
    (docs_dir / "setup.md").write_text(
        "Required: VOYAGE_API_KEY\nexport LEANTIME_TOKEN=\n",
        encoding="utf-8",
    )

    outputs = MODULE.write_outputs(root, include_packages=True, include_env=True, include_template=True)

    packages = (root / "scripts" / "env_outputs" / "packages.txt").read_text(encoding="utf-8").splitlines()
    assert packages == [
        "node\tnext@15.5.15\tpackage.json",
        "node\ttypescript@5.6.2\tpackage.json",
        "python\tblack>=23.0.0\trequirements.txt",
        "python\tclick>=8.0.0\tpyproject.toml",
        "python\tpytest>=9.0.3\tpyproject.toml",
        "python\trequests>=2.28.0\tpyproject.toml;requirements.txt",
    ]

    env_vars = (root / "scripts" / "env_outputs" / "env_vars.txt").read_text(encoding="utf-8").splitlines()
    assert "OPENAI_API_KEY=" in env_vars
    assert "FRONTEND_API_URL=" in env_vars
    assert "VOYAGE_API_KEY=" in env_vars

    template = (root / "scripts" / "env_outputs" / ".env.codex").read_text(encoding="utf-8").splitlines()
    assert "OPENAI_API_KEY=your_openai_api_key_here" in template
    assert "FRONTEND_API_URL=http://localhost:8000" in template

    assert outputs["manifests"].name == "manifests.txt"
