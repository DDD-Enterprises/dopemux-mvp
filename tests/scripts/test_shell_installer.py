#!/usr/bin/env python3
"""
Test shell hook installer functionality.
"""

import tempfile
import os
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dopemux.hooks.shell_hook_installer import ShellHookInstaller

def test_installer():
    """Test shell hook installer with temporary files."""
    installer = ShellHookInstaller()

    # Test shell detection
    shell = installer.detect_shell()
    print(f"🧪 Detected shell: {shell}")

    # Test with temporary config file
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create fake shell config
        config_path = tmpdir / '.bashrc'
        config_path.write_text('# Test bash config\n')

        # Override config paths for testing
        installer.shell_configs['bash'] = [str(config_path)]

        # Test hook checking
        has_hooks = installer.check_existing_hooks(config_path)
        assert not has_hooks, "Should not have hooks initially"
        print("✅ Hook detection test passed")

        # Test installation
        success, message = installer.install_hooks('bash')
        assert success, f"Installation failed: {message}"
        print("✅ Hook installation test passed")

        # Verify hooks were added
        content = config_path.read_text()
        assert 'dopemux_trigger' in content, "Hooks not found in config"
        print("✅ Hook content verification passed")

        # Test existing hook detection
        has_hooks_after = installer.check_existing_hooks(config_path)
        assert has_hooks_after, "Should detect hooks after installation"
        print("✅ Existing hook detection test passed")

        # Test uninstallation
        success, message = installer.uninstall_hooks('bash')
        assert success, f"Uninstallation failed: {message}"
        print("✅ Hook uninstallation test passed")

    print("🎉 Shell hook installer tests completed successfully!")

if __name__ == "__main__":
    test_installer()