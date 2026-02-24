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
        click.echo("\n🏥 Service Health:")
        click.echo("-" * 50)
        
        for service_name, health_info in health.items():
            status_emoji = "✅" if health_info['status'] == 'healthy' else "❌"
            click.echo(f"{status_emoji} {service_name}: {health_info['status']}")
            if health_info.get('error'):
                click.echo(f"   Error: {health_info['error']}")
        
    except Exception as e:
        logger.error(f"Failed to get service status: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        raise


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


@routing.command()
@click.option("--max-passes", type=int, default=3, help="Maximum repair attempts (default: 3)")
@click.option("--allow-sync-keys", is_flag=True, help="Allow API key syncing during repair")
def repair(max_passes: int, allow_sync_keys: bool):
    """Attempt to repair routing services."""
    try:
        manager = LaunchdServiceManager.get_instance()
        click.echo("🔧 Attempting to repair routing services...")
        
        # Run repair
        repair_result = manager.repair(
            max_passes=max_passes,
            allow_sync_keys=allow_sync_keys
        )
        
        # Show results
        if repair_result.get("healthy", False):
            click.echo("✅ Routing services repaired successfully!")
            
            # Show final health
            health = repair_result["health"]
            click.echo("\n🏥 Final Health Status:")
            for service, info in health.items():
                if service == "mode":
                    continue
                status_emoji = "✅" if info.get("status") == "healthy" else "❌"
                click.echo(f"  {status_emoji} {service}: {info.get('status')}")
        else:
            click.echo("❌ Failed to repair routing services")
            
            # Show repair attempts
            click.echo("\n📋 Repair Attempts:")
            for attempt in repair_result.get("attempts", []):
                status = "✅" if attempt.get("result", {}).get("ok") else "❌"
                click.echo(f"  {status} Pass {attempt['pass']}: {attempt['action']}")
            
            # Show diagnostics
            click.echo("\n🔍 Diagnostics:")
            log_paths = manager._get_log_paths()
            click.echo(f"  LiteLLM launchd log: {log_paths['litellm_launchd']}")
            click.echo(f"  CCR launchd log: {log_paths['ccr_launchd']}")
            click.echo(f"  Latest LiteLLM log: {log_paths['litellm_latest']}")
            
            click.echo("\n💡 Next steps:")
            click.echo("  • Check logs with: tail -f ~/.dopemux/logs/litellm_launchd.log")
            click.echo("  • Run health check: dopemux routing health")
            click.echo("  • Check service status: dopemux routing status")
            
            raise SystemExit(1)
            
    except Exception as e:
        logger.error(f"Failed to repair services: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        raise
