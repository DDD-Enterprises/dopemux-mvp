#!/usr/bin/env python3
"""
Simple installation script for Dopemux standalone CLI.

This script sets up Dopemux as a standalone document analysis tool
that can be invoked with 'dopemux analyze <directory>'.
"""

import os

import logging

logger = logging.getLogger(__name__)

import sys
import subprocess
import shutil
from pathlib import Path


def check_python_version():
    """Ensure Python 3.8+ is available."""
    if sys.version_info < (3, 8):
        logger.info("❌ Python 3.8+ required. Current version:", sys.version)
        sys.exit(1)
    logger.info(f"✅ Python {sys.version.split()[0]} detected")


def check_dependencies():
    """Check if pip and venv are available."""
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"],
                      check=True, capture_output=True)
        logger.info("✅ pip is available")
    except subprocess.CalledProcessError:
        logger.info("❌ pip is not available. Please install pip.")
        sys.exit(1)

    try:
        subprocess.run([sys.executable, "-m", "venv", "--help"],
                      check=True, capture_output=True)
        logger.info("✅ venv is available")
    except subprocess.CalledProcessError:
        logger.info("❌ venv is not available. Please install python3-venv.")
        sys.exit(1)


def create_virtual_environment():
    """Create a virtual environment for Dopemux."""
    venv_path = Path.home() / ".dopemux" / "venv"

    if venv_path.exists():
        logger.info(f"⚠️ Virtual environment already exists at {venv_path}")
        return venv_path

    logger.info(f"📦 Creating virtual environment at {venv_path}")
    venv_path.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
    logger.info("✅ Virtual environment created")

    return venv_path


def install_package(venv_path):
    """Install Dopemux package in virtual environment."""
    if os.name == 'nt':  # Windows
        pip_path = venv_path / "Scripts" / "pip"
        python_path = venv_path / "Scripts" / "python"
    else:  # Unix/Linux/macOS
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"

    logger.info("📥 Installing Dopemux package...")

    # Install in development mode from current directory
    current_dir = Path(__file__).parent
    subprocess.run([
        str(pip_path), "install", "-e", str(current_dir)
    ], check=True)

    logger.info("✅ Package installed")

    return python_path


def create_launcher_script(python_path):
    """Create a launcher script for easy CLI access."""
    # Determine the appropriate bin directory
    if os.name == 'nt':  # Windows
        bin_dir = Path.home() / "AppData" / "Local" / "Microsoft" / "WindowsApps"
        script_name = "dopemux.bat"
        script_content = f"""@echo off
"{python_path}" -m dopemux.cli %*
"""
    else:  # Unix/Linux/macOS
        bin_dir = Path.home() / ".local" / "bin"
        script_name = "dopemux"
        script_content = f"""#!/bin/bash
"{python_path}" -m dopemux.cli "$@"
"""

    bin_dir.mkdir(parents=True, exist_ok=True)
    script_path = bin_dir / script_name

    with open(script_path, 'w') as f:
        f.write(script_content)

    if os.name != 'nt':  # Make executable on Unix systems
        os.chmod(script_path, 0o755)

    logger.info(f"✅ Launcher script created at {script_path}")

    return script_path, bin_dir


def update_path_instructions(bin_dir):
    """Provide instructions for updating PATH."""
    if os.name == 'nt':  # Windows
        print(f"""
🎯 Installation Complete!

To use Dopemux from anywhere, add this to your PATH:
{bin_dir}

You can do this by:
1. Open System Properties → Advanced → Environment Variables
2. Edit the PATH variable for your user
3. Add: {bin_dir}
4. Restart your terminal

Then run: dopemux analyze <directory>
""")
    else:  # Unix/Linux/macOS
        shell_rc = Path.home() / ".bashrc"
        if (Path.home() / ".zshrc").exists():
            shell_rc = Path.home() / ".zshrc"

        print(f"""
🎯 Installation Complete!

To use Dopemux from anywhere, add this to your {shell_rc.name}:
export PATH="$PATH:{bin_dir}"

Or run this command:
echo 'export PATH="$PATH:{bin_dir}"' >> {shell_rc}

Then restart your terminal or run:
source {shell_rc}

Usage: dopemux analyze <directory>
""")


def test_installation(script_path):
    """Test that the installation works."""
    try:
        if os.name == 'nt':
            result = subprocess.run([str(script_path), "--version"],
                                  capture_output=True, text=True)
        else:
            result = subprocess.run([str(script_path), "--version"],
                                  capture_output=True, text=True)

        if result.returncode == 0:
            logger.info("✅ Installation test passed")
            return True
        else:
            logger.error("❌ Installation test failed")
            logger.error("Error:", result.stderr)
            return False

    except Exception as e:
        logger.error(f"❌ Installation test error: {e}")
        return False


def main():
    """Main installation process."""
    logger.info("🧠 Dopemux Standalone CLI Installer")
    logger.info("=" * 40)

    # Pre-checks
    check_python_version()
    check_dependencies()

    # Installation steps
    venv_path = create_virtual_environment()
    python_path = install_package(venv_path)
    script_path, bin_dir = create_launcher_script(python_path)

    # Test installation
    if test_installation(script_path):
        logger.info("\n🎉 Installation successful!")
        update_path_instructions(bin_dir)

        print("""
🔍 Example usage:
  dopemux analyze .                    # Analyze current directory
  dopemux analyze /path/to/project     # Analyze specific project
  dopemux analyze --help               # Show all options

🧠 ADHD-optimized features:
  • Gentle progress feedback
  • 25-minute processing chunks
  • Visual completion summaries
  • Structured knowledge extraction
""")
    else:
        logger.error("\n❌ Installation failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()