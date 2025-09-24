#!/usr/bin/env python3
"""
Dopemux Leantime & Task-Master Installation Manager

Automated installer for Leantime project management with Task-Master AI integration,
optimized for ADHD-accommodated development workflows.
"""

import asyncio
import os
import sys
import json
import subprocess
import shutil
import logging
import secrets
import string
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import click
import yaml
import docker
from docker.errors import DockerException

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.config import Config
from src.core.monitoring import MetricsCollector
from src.integrations.leantime_bridge import create_leantime_bridge
from src.integrations.taskmaster_bridge import create_taskmaster_bridge


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class InstallationConfig:
    """Installation configuration settings."""
    install_mode: str = "docker"  # docker, manual
    leantime_port: int = 8080
    mysql_port: int = 3306
    redis_port: int = 6379

    # Database settings
    mysql_root_password: str = ""
    mysql_database: str = "leantime_db"
    mysql_user: str = "leantime_user"
    mysql_password: str = ""

    # Application settings
    lean_sitename: str = "Dopemux Leantime"
    lean_session_password: str = ""
    lean_app_url: str = ""

    # Security settings
    redis_password: str = ""

    # Task-Master AI settings
    taskmaster_enabled: bool = True
    ai_providers: Dict[str, str] = None

    # ADHD optimizations
    adhd_mode_enabled: bool = True
    context_preservation: bool = True
    notification_batching: bool = True

    def __post_init__(self):
        if self.ai_providers is None:
            self.ai_providers = {}


class DopemuxLeantimeInstaller:
    """Main installer class for Leantime and Task-Master integration."""

    def __init__(self):
        self.config = Config()
        self.metrics = MetricsCollector()
        self.docker_client = None
        self.installation_dir = Path.cwd()
        self.docker_dir = self.installation_dir / "docker" / "leantime"

        # Installation state
        self.install_config = InstallationConfig()
        self.preflight_results = {}
        self.installation_log = []

    async def run_installation(self, config_file: Optional[str] = None) -> bool:
        """
        Run the complete installation process.

        Args:
            config_file: Optional configuration file path

        Returns:
            True if installation successful
        """
        try:
            logger.info("🚀 Starting Dopemux Leantime & Task-Master installation...")

            # Load configuration
            if config_file:
                await self._load_config_file(config_file)
            else:
                await self._interactive_config()

            # Pre-flight checks
            self.log_step("Running pre-flight checks...")
            if not await self._run_preflight_checks():
                logger.error("❌ Pre-flight checks failed")
                return False

            # Generate secure passwords if not provided
            await self._generate_secure_credentials()

            # Install components
            self.log_step("Installing Docker environment...")
            if not await self._install_docker_environment():
                logger.error("❌ Docker environment installation failed")
                return False

            self.log_step("Setting up Task-Master AI...")
            if not await self._install_taskmaster():
                logger.error("❌ Task-Master AI installation failed")
                return False

            self.log_step("Configuring integrations...")
            if not await self._configure_integrations():
                logger.error("❌ Integration configuration failed")
                return False

            # Start services
            self.log_step("Starting services...")
            if not await self._start_services():
                logger.error("❌ Service startup failed")
                return False

            # Verify installation
            self.log_step("Verifying installation...")
            if not await self._verify_installation():
                logger.error("❌ Installation verification failed")
                return False

            # Post-installation setup
            await self._post_installation_setup()

            logger.info("✅ Installation completed successfully!")
            await self._display_installation_summary()

            return True

        except Exception as e:
            logger.error(f"❌ Installation failed: {e}")
            await self._cleanup_failed_installation()
            return False

    def log_step(self, message: str):
        """Log installation step with formatting."""
        logger.info(f"📋 {message}")
        self.installation_log.append(f"{message} - {datetime.now().isoformat()}")

    async def _load_config_file(self, config_file: str):
        """Load configuration from file."""
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        with open(config_path, 'r') as f:
            if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
                config_data = yaml.safe_load(f)
            else:
                config_data = json.load(f)

        # Update install config
        for key, value in config_data.items():
            if hasattr(self.install_config, key):
                setattr(self.install_config, key, value)

    async def _interactive_config(self):
        """Interactive configuration setup."""
        click.echo("🎯 Dopemux Leantime & Task-Master Installation Setup")
        click.echo("=" * 50)

        # Basic settings
        self.install_config.lean_sitename = click.prompt(
            "Site name", default=self.install_config.lean_sitename
        )

        self.install_config.leantime_port = click.prompt(
            "Leantime port", default=self.install_config.leantime_port, type=int
        )

        self.install_config.lean_app_url = click.prompt(
            "Application URL",
            default=f"http://localhost:{self.install_config.leantime_port}"
        )

        # ADHD optimizations
        click.echo("\n🧠 ADHD Optimization Settings")
        self.install_config.adhd_mode_enabled = click.confirm(
            "Enable ADHD optimizations?", default=True
        )

        if self.install_config.adhd_mode_enabled:
            self.install_config.context_preservation = click.confirm(
                "Enable context preservation?", default=True
            )
            self.install_config.notification_batching = click.confirm(
                "Enable notification batching?", default=True
            )

        # Task-Master AI
        click.echo("\n🤖 Task-Master AI Configuration")
        self.install_config.taskmaster_enabled = click.confirm(
            "Enable Task-Master AI integration?", default=True
        )

        if self.install_config.taskmaster_enabled:
            await self._configure_ai_providers()

        # Database settings
        click.echo("\n🗄️ Database Configuration")
        self.install_config.mysql_database = click.prompt(
            "MySQL database name", default=self.install_config.mysql_database
        )
        self.install_config.mysql_user = click.prompt(
            "MySQL username", default=self.install_config.mysql_user
        )

    async def _configure_ai_providers(self):
        """Configure AI provider API keys."""
        providers = [
            ("anthropic", "Anthropic (Claude)"),
            ("openai", "OpenAI (GPT)"),
            ("google", "Google (Gemini)"),
            ("perplexity", "Perplexity"),
            ("mistral", "Mistral"),
            ("groq", "Groq"),
            ("ollama", "Ollama (Local)")
        ]

        click.echo("📡 AI Provider Configuration (optional - you can add these later)")
        click.echo("Tip: You need at least one API key for Task-Master AI to work")

        for provider_key, provider_name in providers:
            if click.confirm(f"Configure {provider_name}?", default=False):
                api_key = click.prompt(f"{provider_name} API key", hide_input=True)
                if api_key.strip():
                    self.install_config.ai_providers[provider_key] = api_key.strip()

    async def _run_preflight_checks(self) -> bool:
        """Run comprehensive pre-flight system checks."""
        checks_passed = True

        # Check Docker
        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()
            self.preflight_results["docker"] = {"status": "ok", "version": self.docker_client.version()}
            logger.info("✅ Docker is available and running")
        except DockerException as e:
            self.preflight_results["docker"] = {"status": "error", "error": str(e)}
            logger.error("❌ Docker is not available or not running")
            checks_passed = False

        # Check Docker Compose
        try:
            result = subprocess.run(
                ["docker-compose", "--version"],
                capture_output=True, text=True, check=True
            )
            self.preflight_results["docker_compose"] = {"status": "ok", "version": result.stdout.strip()}
            logger.info("✅ Docker Compose is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.preflight_results["docker_compose"] = {"status": "error", "error": "Not found"}
            logger.error("❌ Docker Compose is not available")
            checks_passed = False

        # Check Node.js and npm for Task-Master
        try:
            node_result = subprocess.run(
                ["node", "--version"],
                capture_output=True, text=True, check=True
            )
            npm_result = subprocess.run(
                ["npm", "--version"],
                capture_output=True, text=True, check=True
            )
            self.preflight_results["nodejs"] = {
                "status": "ok",
                "node_version": node_result.stdout.strip(),
                "npm_version": npm_result.stdout.strip()
            }
            logger.info("✅ Node.js and npm are available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.preflight_results["nodejs"] = {"status": "error", "error": "Node.js or npm not found"}
            logger.error("❌ Node.js or npm is not available")
            if self.install_config.taskmaster_enabled:
                checks_passed = False

        # Check available ports
        ports_to_check = [
            self.install_config.leantime_port,
            self.install_config.mysql_port,
            self.install_config.redis_port
        ]

        available_ports = []
        for port in ports_to_check:
            if await self._check_port_available(port):
                available_ports.append(port)
                logger.info(f"✅ Port {port} is available")
            else:
                logger.warning(f"⚠️ Port {port} is in use")

        self.preflight_results["ports"] = {
            "requested": ports_to_check,
            "available": available_ports
        }

        # Check disk space (require at least 2GB)
        try:
            disk_usage = shutil.disk_usage(self.installation_dir)
            free_gb = disk_usage.free / (1024**3)
            self.preflight_results["disk_space"] = {"free_gb": free_gb, "status": "ok" if free_gb >= 2 else "warning"}

            if free_gb < 2:
                logger.warning(f"⚠️ Only {free_gb:.1f}GB free disk space (recommended: 2GB+)")
            else:
                logger.info(f"✅ Sufficient disk space: {free_gb:.1f}GB available")
        except Exception as e:
            self.preflight_results["disk_space"] = {"status": "error", "error": str(e)}

        # Check Python dependencies
        try:
            import yaml, click
            self.preflight_results["python_deps"] = {"status": "ok"}
            logger.info("✅ Required Python dependencies are available")
        except ImportError as e:
            self.preflight_results["python_deps"] = {"status": "error", "error": str(e)}
            logger.error(f"❌ Missing Python dependencies: {e}")
            checks_passed = False

        return checks_passed

    async def _check_port_available(self, port: int) -> bool:
        """Check if a port is available."""
        import socket

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('localhost', port))
                return True
        except OSError:
            return False

    async def _generate_secure_credentials(self):
        """Generate secure passwords and tokens if not provided."""
        def generate_password(length: int = 32) -> str:
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
            return ''.join(secrets.choice(alphabet) for _ in range(length))

        if not self.install_config.mysql_root_password:
            self.install_config.mysql_root_password = generate_password()

        if not self.install_config.mysql_password:
            self.install_config.mysql_password = generate_password()

        if not self.install_config.lean_session_password:
            self.install_config.lean_session_password = generate_password(64)

        if not self.install_config.redis_password:
            self.install_config.redis_password = generate_password()

        logger.info("🔐 Generated secure credentials")

    async def _install_docker_environment(self) -> bool:
        """Install and configure Docker environment."""
        try:
            # Ensure Docker directory structure exists
            self.docker_dir.mkdir(parents=True, exist_ok=True)

            # Create .env file
            env_content = self._generate_env_file()
            env_file = self.docker_dir / ".env"

            with open(env_file, 'w') as f:
                f.write(env_content)

            logger.info("✅ Created Docker environment configuration")

            # Copy docker-compose.yml if it doesn't exist
            compose_file = self.docker_dir / "docker-compose.yml"
            if not compose_file.exists():
                # Use the existing docker-compose.yml we created earlier
                source_compose = Path(__file__).parent.parent.parent / "docker" / "leantime" / "docker-compose.yml"
                if source_compose.exists():
                    shutil.copy2(source_compose, compose_file)
                    logger.info("✅ Docker Compose configuration ready")
                else:
                    logger.error("❌ Docker Compose template not found")
                    return False

            return True

        except Exception as e:
            logger.error(f"❌ Docker environment setup failed: {e}")
            return False

    def _generate_env_file(self) -> str:
        """Generate .env file content."""
        def esc(v: str) -> str:
            try:
                return v.replace("$", "$$")
            except Exception:
                return v

        return f"""# Dopemux Leantime Environment Configuration
# Generated on {datetime.now().isoformat()}

# Database Configuration
MYSQL_ROOT_PASSWORD={esc(self.install_config.mysql_root_password)}
MYSQL_DATABASE={self.install_config.mysql_database}
MYSQL_USER={self.install_config.mysql_user}
MYSQL_PASSWORD={esc(self.install_config.mysql_password)}

# Leantime Application Settings
LEAN_SITENAME={self.install_config.lean_sitename}
LEAN_SESSION_PASSWORD={esc(self.install_config.lean_session_password)}
LEAN_APP_URL={self.install_config.lean_app_url}
LEAN_SESSION_EXPIRATION=28800
LEAN_DEBUG=0

# ADHD Optimization Settings
LEAN_ADHD_MODE={str(self.install_config.adhd_mode_enabled).lower()}
LEAN_NOTIFICATION_BATCH={str(self.install_config.notification_batching).lower()}
LEAN_CONTEXT_PRESERVATION={str(self.install_config.context_preservation).lower()}

# MCP Integration Settings
LEAN_MCP_ENABLED=true
LEAN_MCP_TOKEN={secrets.token_urlsafe(32)}
LEAN_API_ENABLED=true

# Redis Configuration
REDIS_PASSWORD={esc(self.install_config.redis_password)}

# File Storage
LEAN_S3_USE_S3=false

# System Permissions
PUID=1000
PGID=1000

# Dopemux Integration
DOPEMUX_INTEGRATION_ENABLED=true
DOPEMUX_SYNC_INTERVAL=300
DOPEMUX_CONTEXT_BRIDGE_ENABLED=true
"""

    async def _install_taskmaster(self) -> bool:
        """Install and configure Task-Master AI."""
        if not self.install_config.taskmaster_enabled:
            logger.info("⏭️ Skipping Task-Master AI installation (disabled)")
            return True

        try:
            # Install task-master-ai globally
            logger.info("📦 Installing task-master-ai package...")

            result = await asyncio.create_subprocess_exec(
                "npm", "install", "-g", "task-master-ai",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                logger.error(f"❌ npm install failed: {stderr.decode()}")
                return False

            logger.info("✅ Task-Master AI installed successfully")

            # Create Task-Master configuration
            await self._create_taskmaster_config()

            return True

        except Exception as e:
            logger.error(f"❌ Task-Master installation failed: {e}")
            return False

    async def _create_taskmaster_config(self):
        """Create Task-Master AI configuration."""
        taskmaster_dir = self.installation_dir / ".taskmaster"
        taskmaster_dir.mkdir(exist_ok=True)

        # Create config.json
        config_data = {
            "providers": {},
            "defaultProvider": "anthropic",
            "researchProvider": "perplexity",
            "fallbackProvider": "openai"
        }

        # Add configured AI providers
        provider_models = {
            "anthropic": "claude-3-sonnet-20240229",
            "openai": "gpt-4",
            "google": "gemini-pro",
            "perplexity": "llama-3.1-sonar-small-128k-online",
            "mistral": "mistral-large-latest",
            "groq": "mixtral-8x7b-32768",
            "ollama": "llama2"
        }

        for provider, api_key in self.install_config.ai_providers.items():
            if api_key:
                config_data["providers"][provider] = {
                    "model": provider_models.get(provider, "default"),
                    "apiKey": api_key
                }

        # Set default provider to first available
        if config_data["providers"]:
            config_data["defaultProvider"] = list(config_data["providers"].keys())[0]

        config_file = taskmaster_dir / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)

        # Create tasks directory and empty tasks.json
        tasks_dir = taskmaster_dir / "tasks"
        tasks_dir.mkdir(exist_ok=True)

        tasks_file = tasks_dir / "tasks.json"
        with open(tasks_file, 'w') as f:
            json.dump({"tasks": [], "metadata": {}}, f, indent=2)

        logger.info("✅ Task-Master AI configuration created")

    async def _configure_integrations(self) -> bool:
        """Configure MCP integrations between systems."""
        try:
            # Create Claude MCP configuration
            claude_config = {
                "mcpServers": {
                    "task-master-ai": {
                        "command": "npx",
                        "args": ["-y", "--package=task-master-ai", "task-master-ai"],
                        "env": {},
                        "type": "stdio"
                    }
                }
            }

            # Add AI provider environment variables
            for provider, api_key in self.install_config.ai_providers.items():
                if api_key:
                    env_key = f"{provider.upper()}_API_KEY"
                    claude_config["mcpServers"]["task-master-ai"]["env"][env_key] = api_key

            # Create .claude directory and config
            claude_dir = self.installation_dir / ".claude"
            claude_dir.mkdir(exist_ok=True)

            claude_config_file = claude_dir / "claude_config.json"
            with open(claude_config_file, 'w') as f:
                json.dump(claude_config, f, indent=2)

            logger.info("✅ MCP integrations configured")
            return True

        except Exception as e:
            logger.error(f"❌ Integration configuration failed: {e}")
            return False

    async def _start_services(self) -> bool:
        """Start Docker services."""
        try:
            # Change to Docker directory
            original_cwd = os.getcwd()
            os.chdir(self.docker_dir)

            try:
                # Pull images first
                logger.info("📥 Pulling Docker images...")
                result = await asyncio.create_subprocess_exec(
                    "docker-compose", "pull",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await result.communicate()

                # Start services
                logger.info("🚀 Starting Docker services...")
                result = await asyncio.create_subprocess_exec(
                    "docker-compose", "up", "-d",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await result.communicate()

                if result.returncode != 0:
                    logger.error(f"❌ Docker Compose failed: {stderr.decode()}")
                    return False

                logger.info("✅ Docker services started successfully")

                # Wait for services to be ready
                await self._wait_for_services()

                return True

            finally:
                os.chdir(original_cwd)

        except Exception as e:
            logger.error(f"❌ Service startup failed: {e}")
            return False

    async def _wait_for_services(self):
        """Wait for services to be ready."""
        import aiohttp

        max_attempts = 30
        wait_interval = 10

        logger.info("⏳ Waiting for services to be ready...")

        for attempt in range(max_attempts):
            try:
                # Check Leantime health
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"http://localhost:{self.install_config.leantime_port}/install",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status in [200, 302]:  # 302 for redirect to installation
                            logger.info("✅ Leantime is ready")
                            return

            except Exception:
                pass

            if attempt < max_attempts - 1:
                logger.info(f"⏳ Services not ready yet, waiting {wait_interval}s... (attempt {attempt + 1}/{max_attempts})")
                await asyncio.sleep(wait_interval)

        logger.warning("⚠️ Services may not be fully ready, but continuing...")

    async def _verify_installation(self) -> bool:
        """Verify the installation is working correctly."""
        try:
            # Check Docker containers
            containers = self.docker_client.containers.list()
            required_containers = ["leantime", "mysql_leantime", "redis_leantime"]

            running_containers = [c.name for c in containers if c.status == "running"]

            for required in required_containers:
                if required not in running_containers:
                    logger.error(f"❌ Container {required} is not running")
                    return False

            logger.info("✅ All Docker containers are running")

            # Test Leantime connectivity
            import aiohttp
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"http://localhost:{self.install_config.leantime_port}",
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status in [200, 302]:
                            logger.info("✅ Leantime is accessible")
                        else:
                            logger.warning(f"⚠️ Leantime returned status {response.status}")
            except Exception as e:
                logger.error(f"❌ Cannot connect to Leantime: {e}")
                return False

            # Test Task-Master if enabled
            if self.install_config.taskmaster_enabled:
                try:
                    result = await asyncio.create_subprocess_exec(
                        "npx", "task-master-ai", "--help",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await result.communicate()

                    if result.returncode == 0:
                        logger.info("✅ Task-Master AI is accessible")
                    else:
                        logger.warning("⚠️ Task-Master AI may not be properly configured")

                except Exception as e:
                    logger.warning(f"⚠️ Task-Master AI check failed: {e}")

            return True

        except Exception as e:
            logger.error(f"❌ Installation verification failed: {e}")
            return False

    async def _post_installation_setup(self):
        """Perform post-installation setup tasks."""
        # Create installation info file
        install_info = {
            "installation_date": datetime.now().isoformat(),
            "version": "1.0.0",
            "components": {
                "leantime": {
                    "enabled": True,
                    "url": self.install_config.lean_app_url,
                    "port": self.install_config.leantime_port
                },
                "taskmaster": {
                    "enabled": self.install_config.taskmaster_enabled,
                    "providers": list(self.install_config.ai_providers.keys())
                },
                "adhd_optimizations": {
                    "enabled": self.install_config.adhd_mode_enabled,
                    "context_preservation": self.install_config.context_preservation,
                    "notification_batching": self.install_config.notification_batching
                }
            },
            "database": {
                "name": self.install_config.mysql_database,
                "user": self.install_config.mysql_user
            },
            "preflight_results": self.preflight_results,
            "installation_log": self.installation_log
        }

        install_info_file = self.installation_dir / "dopemux_leantime_install.json"
        with open(install_info_file, 'w') as f:
            json.dump(install_info, f, indent=2, default=str)

        logger.info("✅ Installation information saved")

    async def _display_installation_summary(self):
        """Display installation summary and next steps."""
        click.echo("\n" + "=" * 60)
        click.echo("🎉 DOPEMUX LEANTIME INSTALLATION COMPLETE!")
        click.echo("=" * 60)

        click.echo(f"\n📊 LEANTIME PROJECT MANAGEMENT")
        click.echo(f"   URL: {self.install_config.lean_app_url}")
        click.echo(f"   Port: {self.install_config.leantime_port}")
        click.echo(f"   ADHD Mode: {'Enabled' if self.install_config.adhd_mode_enabled else 'Disabled'}")

        if self.install_config.taskmaster_enabled:
            click.echo(f"\n🤖 TASK-MASTER AI")
            click.echo(f"   Status: Enabled")
            click.echo(f"   Providers: {', '.join(self.install_config.ai_providers.keys()) or 'None configured'}")

        click.echo(f"\n🗄️ DATABASE")
        click.echo(f"   Name: {self.install_config.mysql_database}")
        click.echo(f"   User: {self.install_config.mysql_user}")

        click.echo(f"\n🔑 CREDENTIALS")
        click.echo(f"   MySQL Root Password: {self.install_config.mysql_root_password}")
        click.echo(f"   MySQL User Password: {self.install_config.mysql_password}")

        click.echo(f"\n📋 NEXT STEPS:")
        click.echo(f"   1. Visit {self.install_config.lean_app_url}/install to complete Leantime setup")
        click.echo(f"   2. Configure your Claude Code with the MCP settings in .claude/")
        click.echo(f"   3. Test Task-Master AI integration")
        click.echo(f"   4. Import your first PRD for AI-powered task breakdown")

        click.echo(f"\n🛠️ MANAGEMENT COMMANDS:")
        click.echo(f"   Start: cd {self.docker_dir} && docker-compose up -d")
        click.echo(f"   Stop:  cd {self.docker_dir} && docker-compose down")
        click.echo(f"   Logs:  cd {self.docker_dir} && docker-compose logs -f")

        click.echo("\n" + "=" * 60)

    async def _cleanup_failed_installation(self):
        """Clean up after failed installation."""
        logger.info("🧹 Cleaning up failed installation...")

        try:
            # Stop and remove containers
            if self.docker_client:
                original_cwd = os.getcwd()
                os.chdir(self.docker_dir)

                try:
                    result = await asyncio.create_subprocess_exec(
                        "docker-compose", "down", "-v",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await result.communicate()
                finally:
                    os.chdir(original_cwd)

            logger.info("✅ Cleanup completed")

        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")


# CLI interface
@click.command()
@click.option('--config', '-c', help='Configuration file path')
@click.option('--unattended', '-u', is_flag=True, help='Run in unattended mode')
@click.option('--docker-port', default=8080, help='Leantime Docker port')
@click.option('--enable-taskmaster/--disable-taskmaster', default=True, help='Enable Task-Master AI')
@click.option('--enable-adhd/--disable-adhd', default=True, help='Enable ADHD optimizations')
def main(config, unattended, docker_port, enable_taskmaster, enable_adhd):
    """Dopemux Leantime & Task-Master Installation Manager."""

    async def run_install():
        installer = DopemuxLeantimeInstaller()

        # Set CLI options
        installer.install_config.leantime_port = docker_port
        installer.install_config.taskmaster_enabled = enable_taskmaster
        installer.install_config.adhd_mode_enabled = enable_adhd

        if unattended and not config:
            click.echo("❌ Unattended mode requires a configuration file")
            sys.exit(1)

        success = await installer.run_installation(config)
        sys.exit(0 if success else 1)

    # Add missing import
    from datetime import datetime

    try:
        asyncio.run(run_install())
    except KeyboardInterrupt:
        click.echo("\n❌ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Installation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
