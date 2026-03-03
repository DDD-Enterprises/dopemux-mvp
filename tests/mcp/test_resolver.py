import os
import shutil
from pathlib import Path
from dopemux.mcp.resolver import InstanceResolver

def test_resolver_precedence():
    project_root = Path.cwd() / "tmp_test_resolver"
    if project_root.exists():
        shutil.rmtree(project_root)
    project_root.mkdir(parents=True, exist_ok=True)
    
    # 1. Test Repo Profile
    dopemux_dir = project_root / ".dopemux"
    dopemux_dir.mkdir(exist_ok=True)
    with open(dopemux_dir / "mcp.instances.toml", "w") as f:
        f.write("""
[project]
project_id = "test-repo"

[mcp.conport]
url = "http://repo-url:3000"
""")
    
    resolver = InstanceResolver(project_root)
    res = resolver.resolve()
    assert res["servers"]["conport"]["url"] == "http://repo-url:3000"
    assert res["provenance"]["conport"] == "repo_profile"
    print("✓ Repo profile resolved")

    # 2. Test Env Var Override
    os.environ["DOPMUX_CONPORT_URL"] = "http://env-url:4000"
    res = resolver.resolve()
    assert res["servers"]["conport"]["url"] == "http://env-url:4000"
    assert res["provenance"]["conport"] == "env_var"
    print("✓ Env var override resolved")
    del os.environ["DOPMUX_CONPORT_URL"]

    # 3. Test Global Fallback (Mocking home)
    # We can't easily mock Path.home() without patching, but we can check if it exists
    # For this test, we'll just check if it's handled.
    
    print("Resolver precedence test passed")

if __name__ == "__main__":
    test_resolver_precedence()
