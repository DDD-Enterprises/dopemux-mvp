import pathlib, tomllib
def _data():
    root = pathlib.Path(__file__).resolve().parents[2]
    return tomllib.loads((root / "pyproject.toml").read_text())
def test_pcp_packages_declared():
    assert {"dopemux.pcp", "dopemux.pcp.bridge"} <= set(_data()["tool"]["setuptools"]["packages"])
def test_pcp_console_script_declared():
    assert _data()["project"]["scripts"].get("dopemux-pcp") == "dopemux.pcp.cli:pcp"
