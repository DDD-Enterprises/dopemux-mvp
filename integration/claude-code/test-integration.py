#!/usr/bin/env python3
"""
Dopemux-Claude Code Integration Test Suite

This script validates the complete integration between Claude Code and
the enhanced Dopemux MCP server stack.
"""

import asyncio
import json
import subprocess
import sys
import time
import requests
from pathlib import Path
from typing import Dict, List, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

class IntegrationTestSuite:
    """Test suite for Dopemux-Claude Code integration"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.integration_path = self.project_root / "integration" / "claude-code"
        self.test_results = {}

    def run_test(self, test_name: str, test_func):
        """Run a single test and record results"""
        print(f"🧪 Testing {test_name}...")
        try:
            result = test_func()
            self.test_results[test_name] = {"status": "PASS", "result": result}
            print(f"✅ {test_name} - PASSED")
            return True
        except Exception as e:
            self.test_results[test_name] = {"status": "FAIL", "error": str(e)}
            print(f"❌ {test_name} - FAILED: {e}")
            return False

    def test_config_validation(self) -> Dict[str, Any]:
        """Test enhanced configuration file validity"""
        config_path = self.integration_path / "enhanced-config.json"

        # Check file exists
        if not config_path.exists():
            raise FileNotFoundError("Enhanced config file not found")

        # Validate JSON format
        with open(config_path) as f:
            config = json.load(f)

        # Validate required sections
        required_sections = ["mcpServers", "dopemuxIntegration"]
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required section: {section}")

        # Validate MetaMCP server configuration
        metamcp_config = config["mcpServers"].get("metamcp-production")
        if not metamcp_config:
            raise ValueError("MetaMCP server not configured")

        return {
            "config_sections": list(config.keys()),
            "mcp_servers": list(config["mcpServers"].keys()),
            "adhd_optimizations": config["dopemuxIntegration"]["features"]["adhdOptimizations"]["enabled"]
        }

    def test_mcp_server_health(self) -> Dict[str, str]:
        """Test health of all required MCP servers"""
        required_servers = {
            "zen": "http://localhost:3003/health",
            "task-master-ai": "http://localhost:3005/health",
            "claude-context": "http://localhost:3007/health",
            "exa": "http://localhost:3008/health",
            "conport-memory": "http://localhost:3010/health",
            "morphllm-fast-apply": "http://localhost:3011/health",
            "desktop-commander": "http://localhost:3012/health"
        }

        health_status = {}
        for server, url in required_servers.items():
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    health_status[server] = "healthy"
                else:
                    health_status[server] = f"unhealthy (status: {response.status_code})"
            except requests.RequestException as e:
                health_status[server] = f"unavailable ({str(e)})"

        # Check if critical servers are healthy
        critical_servers = ["zen", "task-master-ai", "claude-context"]
        unhealthy_critical = [s for s in critical_servers if health_status.get(s) != "healthy"]

        if unhealthy_critical:
            raise RuntimeError(f"Critical servers unhealthy: {unhealthy_critical}")

        return health_status

    def test_docker_containers(self) -> Dict[str, str]:
        """Test Docker container status"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=mcp-", "--format", "{{.Names}}:{{.Status}}"],
                capture_output=True,
                text=True,
                check=True
            )

            container_status = {}
            for line in result.stdout.strip().split('\n'):
                if ':' in line:
                    name, status = line.split(':', 1)
                    container_status[name] = status.strip()

            # Check for required containers
            required_containers = [
                "mcp-zen", "mcp-task-master-ai", "mcp-claude-context",
                "mcp-mas-sequential-thinking"
            ]

            missing_containers = [c for c in required_containers if c not in container_status]
            if missing_containers:
                raise RuntimeError(f"Missing containers: {missing_containers}")

            return container_status

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Docker command failed: {e}")

    def test_python_imports(self) -> Dict[str, bool]:
        """Test Python module imports"""
        import_tests = {}

        try:
            from dopemux.mcp.broker import MetaMCPBroker, BrokerConfig, ToolCallRequest
            import_tests["MetaMCPBroker"] = True
        except ImportError:
            import_tests["MetaMCPBroker"] = False

        try:
            from dopemux.mcp.roles import RoleManager
            import_tests["RoleManager"] = True
        except ImportError:
            import_tests["RoleManager"] = False

        # Check if critical imports failed
        failed_imports = [name for name, success in import_tests.items() if not success]
        if failed_imports:
            raise ImportError(f"Failed to import: {failed_imports}")

        return import_tests

    def test_enhanced_server_syntax(self) -> Dict[str, Any]:
        """Test enhanced MetaMCP server Python syntax"""
        server_path = self.integration_path / "enhanced_metamcp_server.py"

        # Check file exists
        if not server_path.exists():
            raise FileNotFoundError("Enhanced MetaMCP server not found")

        # Test Python syntax
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(server_path)],
                capture_output=True,
                text=True,
                check=True
            )
            syntax_valid = True
        except subprocess.CalledProcessError as e:
            syntax_valid = False
            raise SyntaxError(f"Syntax error in enhanced server: {e.stderr}")

        return {
            "syntax_valid": syntax_valid,
            "file_size": server_path.stat().st_size,
            "line_count": len(server_path.read_text().splitlines())
        }

    def test_installer_script(self) -> Dict[str, Any]:
        """Test installer script validity"""
        installer_path = self.integration_path / "install-dopemux-claude.sh"

        # Check file exists and is executable
        if not installer_path.exists():
            raise FileNotFoundError("Installer script not found")

        if not installer_path.stat().st_mode & 0o111:
            raise PermissionError("Installer script not executable")

        # Test bash syntax (basic check)
        try:
            result = subprocess.run(
                ["bash", "-n", str(installer_path)],
                capture_output=True,
                text=True,
                check=True
            )
            syntax_valid = True
        except subprocess.CalledProcessError as e:
            syntax_valid = False
            raise SyntaxError(f"Bash syntax error: {e.stderr}")

        return {
            "syntax_valid": syntax_valid,
            "executable": True,
            "file_size": installer_path.stat().st_size
        }

    def test_claude_config_backup(self) -> Dict[str, Any]:
        """Test Claude configuration backup functionality"""
        import tempfile
        import shutil

        # Create temporary Claude config directory
        with tempfile.TemporaryDirectory() as temp_dir:
            claude_config_dir = Path(temp_dir) / ".claude"
            claude_config_dir.mkdir()

            # Create fake existing config
            fake_config = {"mcpServers": {"test": {"command": "test"}}}
            config_file = claude_config_dir / "config.json"
            config_file.write_text(json.dumps(fake_config))

            # Test backup logic (simulate installer behavior)
            backup_dir = claude_config_dir / f"backup-test"
            backup_dir.mkdir()

            shutil.copy2(config_file, backup_dir / "config.json.backup")

            # Verify backup
            backup_file = backup_dir / "config.json.backup"
            if not backup_file.exists():
                raise FileNotFoundError("Backup not created")

            backup_content = json.loads(backup_file.read_text())
            if backup_content != fake_config:
                raise ValueError("Backup content mismatch")

            return {
                "backup_created": True,
                "content_preserved": True,
                "backup_size": backup_file.stat().st_size
            }

    def test_environment_variables(self) -> Dict[str, str]:
        """Test environment variable detection"""
        env_vars = {
            "DOPEMUX_INTEGRATION": "Integration flag",
            "ADHD_OPTIMIZATIONS": "ADHD optimizations flag",
            "METAMCP_CONFIG_PATH": "MetaMCP config path",
            "PYTHONPATH": "Python path for imports"
        }

        env_status = {}
        for var, description in env_vars.items():
            value = subprocess.run(
                ["printenv", var],
                capture_output=True,
                text=True
            ).stdout.strip()

            env_status[var] = value if value else "not_set"

        return env_status

    def run_all_tests(self) -> Dict[str, Any]:
        """Run complete test suite"""
        print("🚀 Starting Dopemux-Claude Code Integration Test Suite")
        print("=" * 60)

        test_suite = [
            ("Configuration Validation", self.test_config_validation),
            ("MCP Server Health", self.test_mcp_server_health),
            ("Docker Containers", self.test_docker_containers),
            ("Python Imports", self.test_python_imports),
            ("Enhanced Server Syntax", self.test_enhanced_server_syntax),
            ("Installer Script", self.test_installer_script),
            ("Config Backup Logic", self.test_claude_config_backup),
            ("Environment Variables", self.test_environment_variables)
        ]

        passed = 0
        total = len(test_suite)

        for test_name, test_func in test_suite:
            if self.run_test(test_name, test_func):
                passed += 1
            print()

        # Summary
        print("=" * 60)
        print(f"🎯 Test Results: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 All tests passed! Integration is ready.")
            status = "ALL_PASS"
        elif passed >= total * 0.8:
            print("⚠️  Most tests passed. Minor issues detected.")
            status = "MOSTLY_PASS"
        else:
            print("❌ Significant issues detected. Review failed tests.")
            status = "FAIL"

        return {
            "overall_status": status,
            "passed": passed,
            "total": total,
            "pass_rate": passed / total,
            "test_results": self.test_results
        }


def main():
    """Main test execution"""
    test_suite = IntegrationTestSuite()
    results = test_suite.run_all_tests()

    # Save results to file
    results_file = Path(__file__).parent / "test-results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n📊 Detailed results saved to: {results_file}")

    # Exit with appropriate code
    if results["overall_status"] == "ALL_PASS":
        sys.exit(0)
    elif results["overall_status"] == "MOSTLY_PASS":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()