import ast
from pathlib import Path

COCKPIT_ROOT = Path("src/dopemux/ui/cockpit")
COMMAND_FILE = Path("src/dopemux/commands/cockpit_commands.py")
FORBIDDEN_IMPORTS = {
    "dopemux.ui.pm_writes",
    "dopemux.ui.service_endpoints",
    "httpx",
    "requests",
    "urllib",
    "watchfiles",
    "subprocess",
}


def _import_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def test_cockpit_package_has_no_forbidden_imports() -> None:
    seen: set[str] = set()
    for path in COCKPIT_ROOT.glob("*.py"):
        seen.update(_import_names(path))
    seen.update(_import_names(COMMAND_FILE))
    for imported in seen:
        assert imported not in FORBIDDEN_IMPORTS
        assert imported.split(".", 1)[0] not in FORBIDDEN_IMPORTS


def test_cockpit_code_has_no_shellout_tokens() -> None:
    text = "\n".join(path.read_text() for path in COCKPIT_ROOT.glob("*.py"))
    text += "\n" + COMMAND_FILE.read_text()
    assert "subprocess" not in text
    assert "shell=True" not in text
