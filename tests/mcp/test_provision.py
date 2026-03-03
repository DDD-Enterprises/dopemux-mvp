import os
import shutil
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from dopemux.mcp.provision import MCPProvisioner, PINNED_VERSION
from dopemux.mcp.instance_overlay import InstanceOverlayManager

@pytest.fixture
def temp_project(tmp_path):
    project_root = tmp_path / "test-project"
    project_root.mkdir()
    return project_root

def test_provision_first_run(temp_project):
    # Setup mock package data
    pkg_mcp = temp_project / "pkg" / "docker" / "mcp-servers"
    pkg_mcp.mkdir(parents=True)
    (pkg_mcp / "start-all-mcp-servers.sh").touch()
    
    with patch("dopemux.mcp.provision.Path.home", return_value=temp_project / "home"):
        # We need to mock the package resolution part
        provisioner = MCPProvisioner(temp_project)
        
        # Manually set source_resolved for test since we can't easily mock dopemux package
        with patch.object(provisioner, "resolve_stack_source", return_value=pkg_mcp):
            target_path = provisioner.ensure_stack_present()
            
            assert target_path.exists()
            assert target_path.is_symlink()
            assert os.readlink(target_path) == str(pkg_mcp)
            assert provisioner.report["method"] == "symlink"

def test_provision_idempotency(temp_project):
    pkg_mcp = temp_project / "pkg" / "docker" / "mcp-servers"
    pkg_mcp.mkdir(parents=True)
    (pkg_mcp / "start-all-mcp-servers.sh").touch()
    
    provisioner = MCPProvisioner(temp_project)
    with patch.object(provisioner, "resolve_stack_source", return_value=pkg_mcp):
        # Run 1
        path1 = provisioner.ensure_stack_present()
        assert provisioner.report["method"] == "symlink"
        
        # Run 2
        path2 = provisioner.ensure_stack_present()
        assert provisioner.report["method"] == "already_present"
        assert path1 == path2

def test_instance_overlay_uniqueness(temp_project):
    # Instance A
    manager_a = InstanceOverlayManager(temp_project, "A")
    overlay_a = manager_a.materialize()
    
    # Instance B
    manager_b = InstanceOverlayManager(temp_project, "B")
    overlay_b = manager_b.materialize()
    
    assert overlay_a["base_port"] == 3000
    assert overlay_b["base_port"] == 3100
    assert overlay_a["port_map"]["ConPort"] == 3004
    assert overlay_b["port_map"]["ConPort"] == 3104
    assert overlay_a["compose_project_name"] != overlay_b["compose_project_name"]
    assert overlay_a["instance_dir"] != overlay_b["instance_dir"]

def test_instance_overlay_idempotency(temp_project):
    manager = InstanceOverlayManager(temp_project, "A")
    
    # Run 1
    overlay1 = manager.materialize()
    env_content1 = Path(overlay1["env_path"]).read_text()
    
    # Run 2
    overlay2 = manager.materialize()
    env_content2 = Path(overlay2["env_path"]).read_text()
    
    assert env_content1 == env_content2
    assert overlay1["port_map"] == overlay2["port_map"]
