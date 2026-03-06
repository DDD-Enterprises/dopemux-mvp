from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys


def _load_collect_module():
    root = Path(__file__).resolve().parents[3]
    service_root = root / "services" / "repo-truth-extractor"
    if str(service_root) not in sys.path:
        sys.path.insert(0, str(service_root))
    return importlib.import_module("s_int.collect_input")


def _make_fixture_repo(tmp_path: Path) -> Path:
    (tmp_path / "services" / "alpha").mkdir(parents=True, exist_ok=True)
    (tmp_path / "services" / "alpha" / "main.py").write_text(
        "API_KEY = os.getenv('API_KEY')\n# hook callback\n",
        encoding="utf-8",
    )
    (tmp_path / "docker" / "mcp-servers-source" / "demo").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docker" / "mcp-servers-source" / "demo" / "server.py").write_text(
        "TRANSPORT='stdio'\n# mcp tools/list\n",
        encoding="utf-8",
    )
    (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".claude" / "settings.json").write_text('{"mcp": true}\n', encoding="utf-8")
    (tmp_path / "compose.yml").write_text(
        "services:\n  alpha:\n    command: python main.py\n    environment:\n      API_KEY: test_secret\n",
        encoding="utf-8",
    )
    return tmp_path


def test_collect_input_bundle_is_deterministic(tmp_path: Path) -> None:
    module = _load_collect_module()
    repo_root = _make_fixture_repo(tmp_path)
    out_root = tmp_path / "out"
    first = module.collect_input_bundle(repo_root, "sint_case", out_root=out_root)
    second = module.collect_input_bundle(repo_root, "sint_case", out_root=out_root)
    assert first == second
    assert first["schema_version"] == "S_INT_INPUT_V1"
    assert any(row["name"] == "claude_code" for row in first["cli_clients"])
    assert any(row["service_id"] == "alpha" for row in first["services"])
    assert any("mcp" in row["path"] for row in first["mcp_servers"])
    payload_path = out_root / "sint_case" / "S_INT_INPUT.json"
    assert payload_path.exists()
    parsed = json.loads(payload_path.read_text(encoding="utf-8"))
    assert parsed == first


def test_collect_input_never_executes_tools(tmp_path: Path) -> None:
    module = _load_collect_module()
    repo_root = _make_fixture_repo(tmp_path)
    payload = module.collect_input_payload(repo_root, "run_static")
    assert all(row["tool_list"] == "UNKNOWN" for row in payload["mcp_servers"])
    assert all(row["health"] == "UNKNOWN" for row in payload["mcp_servers"])
