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

def test_provision_vendor_fallback(temp_project):
    # Setup vendor path
    vendor_mcp = temp_project / ".dopemux" / "vendor" / "mcp-servers" / PINNED_VERSION
    vendor_mcp.mkdir(parents=True)
    (vendor_mcp / "start-all-mcp-servers.sh").touch()
    
    provisioner = MCPProvisioner(temp_project)
    # resolve_stack_source should find it
    path = provisioner.resolve_stack_source()
    assert path == vendor_mcp
    assert provisioner.report["source_resolved"] == "project_vendor"

def test_provision_cache_fallback(temp_project):
    home = temp_project / "home"
    cache_mcp = home / ".cache" / "dopemux" / "mcp-servers" / PINNED_VERSION
    cache_mcp.mkdir(parents=True)
    (cache_mcp / "start-all-mcp-servers.sh").touch()
    
    with patch("dopemux.mcp.provision.Path.home", return_value=home):
        provisioner = MCPProvisioner(temp_project)
        path = provisioner.resolve_stack_source()
        assert path == cache_mcp
        assert provisioner.report["source_resolved"] == "user_cache"

def test_provision_invalid_target_cleanup(temp_project):
    target = temp_project / "docker" / "mcp-servers"
    target.mkdir(parents=True)
    # Exists but no script
    
    pkg_mcp = temp_project / "pkg" / "docker" / "mcp-servers"
    pkg_mcp.mkdir(parents=True)
    (pkg_mcp / "start-all-mcp-servers.sh").touch()
    
    provisioner = MCPProvisioner(temp_project)
    with patch.object(provisioner, "resolve_stack_source", return_value=pkg_mcp):
        path = provisioner.ensure_stack_present()
        assert path.exists()
        assert path.is_symlink()
        # Backup should exist
        assert (temp_project / "docker" / "mcp-servers.bak").exists()

def test_provision_fail_raises(temp_project):
    provisioner = MCPProvisioner(temp_project)
    with patch.object(provisioner, "resolve_stack_source", return_value=None):
        with pytest.raises(RuntimeError, match="Could not resolve MCP stack source"):
            provisioner.ensure_stack_present()

def test_provision_project_local(temp_project):
    local_path = temp_project / "docker" / "mcp-servers"
    local_path.mkdir(parents=True)
    (local_path / "start-all-mcp-servers.sh").touch()
    
    provisioner = MCPProvisioner(temp_project)
    path = provisioner.resolve_stack_source()
    assert path == local_path
    assert provisioner.report["source_resolved"] == "project_local"

def test_provision_project_source(temp_project):
    source_path = temp_project / "docker" / "mcp-servers-source"
    source_path.mkdir(parents=True)
    (source_path / "start-all-mcp-servers.sh").touch()
    
    provisioner = MCPProvisioner(temp_project)
    path = provisioner.resolve_stack_source()
    assert path == source_path
    assert provisioner.report["source_resolved"] == "project_source"

def test_provision_copy_fallback(temp_project):
    pkg_mcp = temp_project / "pkg" / "docker" / "mcp-servers"
    pkg_mcp.mkdir(parents=True)
    (pkg_mcp / "start-all-mcp-servers.sh").touch()
    
    provisioner = MCPProvisioner(temp_project)
    with patch.object(provisioner, "resolve_stack_source", return_value=pkg_mcp):
        # Mock os.symlink to fail
        with patch("os.symlink", side_effect=OSError):
            path = provisioner.ensure_stack_present()
            assert path.exists()
            assert not path.is_symlink()
            assert (path / "start-all-mcp-servers.sh").exists()
            assert provisioner.report["method"] == "copy"

def test_provision_already_present(temp_project):
    target = temp_project / "docker" / "mcp-servers"
    target.mkdir(parents=True)
    (target / "start-all-mcp-servers.sh").touch()
    
    provisioner = MCPProvisioner(temp_project)
    path = provisioner.ensure_stack_present()
    assert provisioner.report["method"] == "already_present"

def test_provision_broken_symlink_cleanup(temp_project):
    target = temp_project / "docker" / "mcp-servers"
    target.parent.mkdir(parents=True, exist_ok=True)
    # Use os.symlink directly to allow creating broken links easily
    os.symlink(str(temp_project / "non-existent"), str(target))
    
    pkg_mcp = temp_project / "pkg" / "docker" / "mcp-servers"
    pkg_mcp.mkdir(parents=True)
    (pkg_mcp / "start-all-mcp-servers.sh").touch()
    
    provisioner = MCPProvisioner(temp_project)
    with patch.object(provisioner, "resolve_stack_source", return_value=pkg_mcp):
        path = provisioner.ensure_stack_present()
        assert path.exists()
        assert path.is_symlink()
        assert os.readlink(path) == str(pkg_mcp)

def test_instance_overlay_no_id(temp_project):
    manager = InstanceOverlayManager(temp_project, "")
    assert manager.base_port == 3000
