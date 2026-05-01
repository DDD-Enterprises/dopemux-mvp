"""CLI commands for Dopemux routing and launchd services."""

import json
import click
import logging
from pathlib import Path

from dopemux.launchd_services import LaunchdServiceManager
from dopemux.routing_config import RoutingConfig, RoutingConfigError
from dopemux.freeflow import (
    FreeflowQuotaLedger,
    FreeflowRouter,
    build_doctor_report,
)

logger = logging.getLogger(__name__)


@click.group()
def routing():
    """Manage Dopemux routing and launchd services."""
    pass


@routing.group()
def freeflow():
    """Inspect strict-free routing policy, quotas, and admissible routes."""
    pass


def _load_freeflow_config() -> dict:
    routing_config = RoutingConfig()
    return routing_config.load()


@freeflow.command("doctor")
@click.option("--offline", is_flag=True, help="Skip live backend probes.")
@click.option("--json", "json_output", is_flag=True, help="Emit machine-readable JSON.")
def freeflow_doctor(offline: bool, json_output: bool):
    """Audit strict-free routing policy and quota metadata."""
    try:
        config = _load_freeflow_config()
        report = build_doctor_report(config, offline=offline)
        if json_output:
            click.echo(json.dumps(report, indent=2, sort_keys=True))
            return

        click.echo("Freeflow Strict-Free Router Doctor")
        click.echo("=" * 50)
        click.echo(f"Enabled: {report['enabled']}")
        click.echo(f"Mode: {report['mode']}")
        click.echo(f"Ledger: {report['ledger_path']}")
        for key, value in report["summary"].items():
            click.echo(f"{key}: {value}")
        if report["issues"]:
            click.echo("\nIssues:")
            for issue in report["issues"]:
                click.echo(f"  - {issue}")
    except RoutingConfigError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(2)


@freeflow.command("quota")
@click.option("--json", "json_output", is_flag=True, help="Emit machine-readable JSON.")
def freeflow_quota(json_output: bool):
    """Show strict-free quota ledger state."""
    ledger = FreeflowQuotaLedger()
    report = ledger.quota_summary()
    if json_output:
        click.echo(json.dumps(report, indent=2, sort_keys=True))
        return
    click.echo(f"Ledger: {report['ledger_path']}")
    click.echo(f"Generated: {report['generated_at']}")
    click.echo(f"Buckets: {len(report['buckets'])}")
    click.echo(f"Cooldowns: {len(report['cooldowns'])}")


@freeflow.command("routes")
@click.option("--json", "json_output", is_flag=True, help="Emit machine-readable JSON.")
def freeflow_routes(json_output: bool):
    """List strict-free route decisions from routing config."""
    try:
        config = _load_freeflow_config()
        routes = FreeflowRouter(config).routes()
        if json_output:
            click.echo(json.dumps({"routes": routes}, indent=2, sort_keys=True))
            return
        for route in routes:
            if route["strict_free_allowed"]:
                status = "allowed"
            elif route["paid_cap_allowed"]:
                status = "paid_cap_allowed"
            else:
                reason = route["blocked_reason"] or route["paid_cap_blocked_reason"]
                status = f"blocked:{reason}"
            click.echo(f"{route['name']} -> {route['effective_provider']} ({status})")
    except RoutingConfigError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(2)


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
@click.option("--restart/--no-restart", default=True, help="Restart services after switching (default: True)")
def api(restart: bool):
    """Switch to API mode (route through LiteLLM + external models)."""
    try:
        manager = LaunchdServiceManager.get_instance()
        config = manager.routing_config.load()

        if config.get("mode") == "api":
            click.echo("ℹ️  Already in API mode")
            return

        _set_routing_mode(manager.routing_config.config_path, "api")
        click.echo("✅ Switched to API mode (external models via LiteLLM)")

        _set_claude_base_url("http://127.0.0.1:4010")
        click.echo("✅ Updated Claude Code baseUrl → http://127.0.0.1:4010")

        if restart:
            click.echo("🔄 Restarting services...")
            manager.routing_config._loaded = False
            manager.routing_config.load()
            manager._regenerate_configs()
            manager.reload_services()
            click.echo("✅ Services restarted!")

    except Exception as e:
        logger.error(f"Failed to switch to API mode: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        raise


@routing.command()
def direct():
    """Switch to direct/subscription mode (route straight to Anthropic API)."""
    try:
        manager = LaunchdServiceManager.get_instance()
        config = manager.routing_config.load()

        if config.get("mode") == "subscription":
            click.echo("ℹ️  Already in subscription (direct) mode")
            return

        _set_routing_mode(manager.routing_config.config_path, "subscription")
        click.echo("✅ Switched to subscription mode (direct to Anthropic)")

        _set_claude_base_url("https://api.anthropic.com")
        click.echo("✅ Updated Claude Code baseUrl → https://api.anthropic.com")

    except Exception as e:
        logger.error(f"Failed to switch to direct mode: {e}")
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
def doctor():
    """Audit repo-owned routing alias contract drift in routing.yaml."""
    try:
        manager = LaunchdServiceManager.get_instance()
        audit = manager.routing_config.audit_alias_contract()

        click.echo("🩺 Routing Alias Contract Doctor")
        click.echo("=" * 50)
        click.echo(f"Config:   {audit['config_path']}")
        click.echo(f"Template: {audit['template_path']}")

        if not audit["stale"]:
            click.echo("\n✅ Alias contract matches the repo-owned template.")
            return

        click.echo("\n❌ Stale routing alias contract detected.")

        missing = audit["missing_aliases"]
        if missing:
            click.echo("\nMissing aliases:")
            for alias, target in missing.items():
                click.echo(f"  - {alias}: expected {target}")

        mismatched = audit["mismatched_aliases"]
        if mismatched:
            click.echo("\nMismatched aliases:")
            for alias, values in mismatched.items():
                click.echo(
                    f"  - {alias}: expected {values['expected']}, found {values['actual']}"
                )

        click.echo("\nNext steps:")
        click.echo("  • Preview repair: dopemux routing repair-aliases")
        click.echo("  • Apply repair: dopemux routing repair-aliases --apply")
        click.echo("  • Inspect config: dopemux routing config")
        raise SystemExit(1)
    except RoutingConfigError as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise SystemExit(2)
    except Exception as e:
        logger.error(f"Failed to audit routing alias contract: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        raise


@routing.command("repair-aliases")
@click.option(
    "--apply",
    is_flag=True,
    help="Write the repo-owned alias contract into ~/.dopemux/routing.yaml.",
)
def repair_aliases(apply: bool):
    """Preview or repair stale repo-owned alias mappings explicitly."""
    try:
        manager = LaunchdServiceManager.get_instance()
        audit = manager.routing_config.audit_alias_contract()

        click.echo("🔧 Routing Alias Contract Repair")
        click.echo("=" * 50)

        if not audit["stale"]:
            click.echo("✅ No alias repair needed.")
            return

        click.echo("Planned alias updates:")
        for alias, target in audit["missing_aliases"].items():
            click.echo(f"  - add {alias}: {target}")
        for alias, values in audit["mismatched_aliases"].items():
            click.echo(
                f"  - set {alias}: {values['actual']} -> {values['expected']}"
            )

        if not apply:
            click.echo("\nDry run only. No files changed.")
            click.echo("Run `dopemux routing repair-aliases --apply` to write the repair.")
            return

        result = manager.routing_config.repair_alias_contract()
        click.echo("\n✅ Alias contract repaired.")
        click.echo(f"Backup: {result['backup_path']}")
        click.echo(f"Updated: {manager.routing_config.config_path}")
    except RoutingConfigError as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise SystemExit(2)
    except Exception as e:
        logger.error(f"Failed to repair routing alias contract: {e}")
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


def _set_routing_mode(config_path: Path, mode: str) -> None:
    config_path.write_text(content)


def _set_claude_base_url(url: str) -> None:
    """Update apiConfiguration.baseUrl in ~/.claude/settings.json."""
    import json
    settings_path = Path.home() / ".claude" / "settings.json"
    if not settings_path.exists():
        return
    settings = json.loads(settings_path.read_text())
    if "apiConfiguration" not in settings:
        settings["apiConfiguration"] = {}
    settings["apiConfiguration"]["baseUrl"] = url
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")


def register_routing_commands(cli_group):
    """Register routing commands with the main CLI."""
    cli_group.add_command(routing, "routing")
