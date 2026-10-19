"""serena wrapper must not start mcp-proxy with a wildcard CORS origin."""
import ast
from pathlib import Path

WRAPPER = (
    Path(__file__).resolve().parents[2]
    / "docker/mcp-servers-source/serena/wrapper.py"
)


def _cmd_literals():
    tree = ast.parse(WRAPPER.read_text())
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "cmd" for t in node.targets)
            and isinstance(node.value, ast.List)
        ):
            return [
                e.value for e in node.value.elts
                if isinstance(e, ast.Constant) and isinstance(e.value, str)
            ]
    raise AssertionError("cmd list not found in wrapper.py")


def test_cmd_found_and_runs_mcp_proxy():
    assert _cmd_literals()[0] == "mcp-proxy"


def test_no_wildcard_origin():
    cmd = _cmd_literals()
    assert "*" not in cmd, f"wildcard in mcp-proxy command: {cmd}"
    for i, a in enumerate(cmd):
        if a == "--allow-origin":
            assert cmd[i + 1] in {"http://localhost", "http://127.0.0.1"} or cmd[i + 1].startswith(
                ("http://localhost:", "http://127.0.0.1:")
            ), f"non-loopback origin: {cmd[i + 1]}"
