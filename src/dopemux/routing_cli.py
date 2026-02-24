"""CLI commands for Dopemux routing and launchd services."""

import click
import logging

from dopemux.launchd_services import LaunchdServiceManager

logger = logging.getLogger(__name__)


@click.group()
def routing():
    """Manage Dopemux routing and launchd services."""
    pass


@routing.command()
@click.option("--force", is_flag=True, help="Force reinstall even if already installed")
def install(force: bool):
    """Install launchd services for LiteLLM and CCR."""
    try:
        manager = LaunchdServiceManager.get_instance()
        
        # Check if already installed
        if not force:
            status = manager.get_service_status()
            if (status.get("litellm", {}).get("status") == "running" or 
                status.get("ccr", {}).get("status") == "running"):
                click.echo("⚠️  Services appear to be already installed. Use --force to reinstall.")
                return
        
        click.echo("🛠️  Installing Dopemux launchd services...")
        manager.install_services()
        click.echo("✅ Services installed successfully!")
        
        # Show status
        status = manager.get_service_status()
        click.echo("\n📊 Service Status:")
        for service, info in status.items():
            click.echo(f"  {service}: {info['status']}")
        
    except Exception as e:
        logger.error(f"Failed to install services: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        raise


@routing.command()
def start():
    """Start all launchd services."""
    try:
        manager = LaunchdServiceManager.get_instance()
        click.echo("🚀 Starting Dopemux launchd services...")
        manager.start_services()
        click.echo("✅ Services started!")
    except Exception as e:
        logger.error(f"Failed to start services: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        raise


@routing.command()
def stop():
    """Stop all launchd services."""
    try:
        manager = LaunchdServiceManager.get_instance()
        click.echo("⏹️  Stopping Dopemux launchd services...")
        manager.stop_services()
        click.echo("✅ Services stopped!")
    except Exception as e:
        logger.error(f"Failed to stop services: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        raise


@routing.command()
def reload():
    """Reload all launchd services."""
    try:
        manager = LaunchdServiceManager.get_instance()
        click.echo("🔄 Reloading Dopemux launchd services...")
        manager.reload_services()
        click.echo("✅ Services reloaded!")
    except Exception as e:
        logger.error(f"Failed to reload services: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        raise


@routing.command()
def uninstall():
    """Uninstall all launchd services."""
    try:
        manager = LaunchdServiceManager.get_instance()
        click.echo("🗑️  Uninstalling Dopemux launchd services...")
        manager.uninstall_services()
        click.echo("✅ Services uninstalled!")
    except Exception as e:
        logger.error(f"Failed to uninstall services: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        raise


@routing.command()
def status():
    """Show status of launchd services."""
    try:
        manager = LaunchdServiceManager.get_instance()
        status = manager.get_service_status()
        
        click.echo("📊 Dopemux Launchd Service Status:")
        click.echo("=" * 50)
        
        for service_name, service_info in status.items():
            click.echo(f"\n{service_name.upper()}:")
            click.echo(f"  Status: {service_info['status']}")
            if service_info.get('details'):
                click.echo(f"  Details: {service_info['details'][:100]}...")
        
        # Check health if services are running
        health = manager.check_health()
        
        # Check for config errors first
        if "config" in health:
            click.echo("\n🏥 Service Health:")
            click.echo("-" * 50)
            click.echo(f"❌ config: {health['config']['status']}")
            click.echo(f"   Error: {health['config']['error']}")
            return
        
        click.echo("\n🏥 Service Health:")
        click.echo("-" * 50)
        
        for service_name, health_info in health.items():
            status_emoji = "✅" if health_info['status'] == 'healthy' else "❌"
            port_info = f" (127.0.0.1:{health_info.get('port', 'unknown')})" if health_info.get('port') else ""
            click.echo(f"{status_emoji} {service_name}: {health_info['status']}{port_info}")
            if health_info.get('error'):
                click.echo(f"   Error: {health_info['error']}")
        
    except Exception as e:
        logger.error(f"Failed to get service status: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        raise


@routing.command()
def health():
    """Check service health and exit with appropriate status code."""
    try:
        manager = LaunchdServiceManager.get_instance()
        health = manager.check_health()
        
        # Check for config errors first
        if "config" in health:
            click.echo(f"❌ {health['config']['error']}", err=True)
            raise SystemExit(2)
        
        # Check if we're in subscription mode
        try:
            mode = manager.routing_config.config.get('mode', 'subscription')
            if mode == 'subscription':
                click.echo("ℹ️  Routing mode is 'subscription' - service health checks not applicable")
                raise SystemExit(0)
        except Exception:
            # If we can't determine mode, assume we need to check services
            pass
        
        # Check service health
        unhealthy_services = []
        for service_name, health_info in health.items():
            if health_info['status'] != 'healthy':
                unhealthy_services.append(service_name)
                click.echo(f"❌ {service_name}: {health_info.get('error', 'unhealthy')}", err=True)
        
        if unhealthy_services:
            raise SystemExit(1)
        else:
            click.echo("✅ All services healthy")
            raise SystemExit(0)
            
    except Exception as e:
        logger.error(f"Failed to check service health: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        raise SystemExit(2)


@routing.command()
def config():
    """Show current routing configuration."""
    try:
        manager = LaunchdServiceManager.get_instance()
        config = manager.routing_config.load()
        
        click.echo("📋 Dopemux Routing Configuration:")
        click.echo("=" * 50)
        click.echo(f"Mode: {config.get('mode', 'N/A')}")
        click.echo(f"LiteLLM Port: {config.get('ports', {}).get('litellm', 'N/A')}")
        click.echo(f"CCR Port: {config.get('ports', {}).get('ccr', 'N/A')}")
        
        providers = config.get('providers', [])
        click.echo(f"\nProviders ({len(providers)}):")
        for provider in providers:
            click.echo(f"  - {provider['name']} ({provider.get('label', 'N/A')})")
        
        models = config.get('models', [])
        click.echo(f"\nModels ({len(models)}):")
        for model in models:
            click.echo(f"  - {model['name']} (via {model['provider']})")
        
    except Exception as e:
        logger.error(f"Failed to load routing config: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        raise


@routing.command()
def docker():
    """Generate Docker Compose snippets for services."""
    try:
        manager = LaunchdServiceManager.get_instance()
        snippets = manager.generate_docker_compose_snippets()
        
        click.echo("🐳 Docker Compose Snippets:")
        click.echo("=" * 50)
        click.echo("\nLiteLLM Service:")
        click.echo(snippets['litellm'])
        click.echo("\nCCR Service:")
        click.echo(snippets['ccr'])
        
    except Exception as e:
        logger.error(f"Failed to generate Docker snippets: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        raise


@routing.command()
def sync_keys():
    """Sync API keys from current environment to routing.env."""
    try:
        manager = LaunchdServiceManager.get_instance()
        click.echo("🔑 Syncing API keys from environment...")
        manager.sync_keys_from_environment()
        click.echo("✅ API keys synced successfully!")
        
        # Show what was synced
        env_path = manager.DOPEMUX_DIR / "routing.env"
        if env_path.exists():
            click.echo("\n📋 Synced keys in:")
            click.echo(f"   {env_path}")
            
    except Exception as e:
        logger.error(f"Failed to sync keys: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        raise


def register_routing_commands(cli_group):
    """Register routing commands with the main CLI."""
    cli_group.add_command(routing, "routing")
