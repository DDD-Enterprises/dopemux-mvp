"""scripts/proof_conport_mcp.py is not an HTTP writer.

It builds an in-process server and calls ``mcp_endpoint`` directly with mock
requests, so it bypasses the auth middleware and no bearer token can apply. W05
only makes its tool-call payload carry the ids a ConPort progress write requires.
"""

from __future__ import annotations

import ast
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "proof_conport_mcp.py"


def _tool_call_arguments() -> dict:
    for node in ast.walk(ast.parse(SCRIPT.read_text())):
        if isinstance(node, ast.Dict):
            keys = [k.value for k in node.keys if isinstance(k, ast.Constant)]
            if "name" in keys and "arguments" in keys:
                arguments = node.values[keys.index("arguments")]
                return ast.literal_eval(arguments)
    raise AssertionError("no tools/call params literal found in the proof script")


def test_should_carry_both_ids_in_the_progress_tool_call():
    arguments = _tool_call_arguments()

    assert arguments["workspace_id"]
    assert arguments["instance_id"]


def test_should_stay_an_in_process_script_without_http_calls():
    source = SCRIPT.read_text()

    assert "aiohttp" not in source and "requests" not in source and "httpx" not in source
