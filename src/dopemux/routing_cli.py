"""CLI commands for Dopemux routing and launchd services."""

import json
import click
import logging
from pathlib import Path

import yaml

from dopemux.console import console
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

        console.print("Freeflow Strict-Free Router Doctor")
        console.print("=" * 50)
        console.print(f"Enabled: {report['enabled']}", markup=False)
        console.print(f"Mode: {report['mode']}", markup=False)
        console.print(f"Ledger: {report['ledger_path']}", markup=False)
        for key, value in report["summary"].items():
            console.print(f"{key}: {value}", markup=False)
        if report["issues"]:
            console.print("\nIssues:")
            for issue in report["issues"]:
                console.print(f"  - {issue}", markup=False)
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
    console.print(f"Ledger: {report['ledger_path']}", markup=False)
    console.print(f"Generated: {report['generated_at']}", markup=False)
    console.print(f"Buckets: {len(report['buckets'])}")
    console.print(f"Cooldowns: {len(report['cooldowns'])}")


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
            console.print(f"{route['name']} -> {route['effective_provider']} ({status})", markup=False)
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
                console.print("⚠️  Services appear to be already installed. Use --force to reinstall.")
                return

        console.print("🛠️  Installing Dopemux launchd services...")
        manager.install_services()
        console.print("✅ Services installed successfully!")

        # Show status
        status = manager.get_service_status()
        console.print("\n📊 Service Status:")
        for service, info in status.items():
            console.print(f"  {service}: {info['status']}", markup=False)

    except Exception as e:
        logger.error(f"Failed to install services: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        raise


@routing.command()
def start():
    """Start all launchd services."""
    try:
        manager = LaunchdServiceManager.get_instance()
        console.print("🚀 Starting Dopemux launchd services...")
        manager.start_services()
        console.print("✅ Services started!")
    except Exception as e:
        logger.error(f"Failed to start services: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        raise


@routing.command()
def stop():
    """Stop all launchd services."""
    try:
        manager = LaunchdServiceManager.get_instance()
        console.print("⏹️  Stopping Dopemux launchd services...")
        manager.stop_services()
        console.print("✅ Services stopped!")
    except Exception as e:
        logger.error(f"Failed to stop services: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        raise


@routing.command()
def reload():
    """Reload all launchd services."""
    try:
        manager = LaunchdServiceManager.get_instance()
        console.print("🔄 Reloading Dopemux launchd services...")
        manager.reload_services()
        console.print("✅ Services reloaded!")
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
            console.print("ℹ️  Already in API mode")
            return

        _set_routing_mode(manager.routing_config.config_path, "api")
        console.print("✅ Switched to API mode (external models via LiteLLM)")

        _set_claude_base_url("http://127.0.0.1:4010")
        console.print("✅ Updated Claude Code baseUrl → http://127.0.0.1:4010")

        if restart:
            console.print("🔄 Restarting services...")
            manager.routing_config._loaded = False
            manager.routing_config.load()
            manager._regenerate_configs()
            manager.reload_services()
            console.print("✅ Services restarted!")

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
            console.print("ℹ️  Already in subscription (direct) mode")
            return

        _set_routing_mode(manager.routing_config.config_path, "subscription")
        console.print("✅ Switched to subscription mode (direct to Anthropic)")

        _set_claude_base_url("https://api.anthropic.com")
        console.print("✅ Updated Claude Code baseUrl → https://api.anthropic.com")

    except Exception as e:
        logger.error(f"Failed to switch to direct mode: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        raise


@routing.command()
def uninstall():
    """Uninstall all launchd services."""
    try:
        manager = LaunchdServiceManager.get_instance()
        console.print("🗑️  Uninstalling Dopemux launchd services...")
        manager.uninstall_services()
        console.print("✅ Services uninstalled!")
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

        console.print("📊 Dopemux Launchd Service Status:")
        console.print("=" * 50)

        for service_name, service_info in status.items():
            console.print(f"\n{service_name.upper()}:", markup=False)
            console.print(f"  Status: {service_info['status']}", markup=False)
            if service_info.get('details'):
                console.print(f"  Details: {service_info['details'][:100]}...", markup=False)

        # Check health if services are running
        health = manager.check_health()

        # Check for config errors first
        if "config" in health:
            console.print("\n🏥 Service Health:")
            console.print("-" * 50)
            console.print(f"❌ config: {health['config']['status']}", markup=False)
            console.print(f"   Error: {health['config']['error']}", markup=False)
            return

        console.print("\n🏥 Service Health:")
        console.print("-" * 50)

        for service_name, health_info in health.items():
            status_emoji = "✅" if health_info['status'] == 'healthy' else "❌"
            port_info = f" (127.0.0.1:{health_info.get('port', 'unknown')})" if health_info.get('port') else ""
            console.print(f"{status_emoji} {service_name}: {health_info['status']}{port_info}", markup=False)
            if health_info.get('error'):
                console.print(f"   Error: {health_info['error']}", markup=False)

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
                console.print("ℹ️  Routing mode is 'subscription' - service health checks not applicable")
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
            console.print("✅ All services healthy")
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

        console.print("📋 Dopemux Routing Configuration:")
        console.print("=" * 50)
        console.print(f"Mode: {config.get('mode', 'N/A')}", markup=False)
        console.print(f"LiteLLM Port: {config.get('ports', {}).get('litellm', 'N/A')}", markup=False)
        console.print(f"CCR Port: {config.get('ports', {}).get('ccr', 'N/A')}", markup=False)

        providers = config.get('providers', [])
        console.print(f"\nProviders ({len(providers)}):")
        for provider in providers:
            console.print(f"  - {provider['name']} ({provider.get('label', 'N/A')})", markup=False)

        models = config.get('models', [])
        console.print(f"\nModels ({len(models)}):")
        for model in models:
            console.print(f"  - {model['name']} (via {model['provider']})", markup=False)

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

        console.print("🩺 Routing Alias Contract Doctor")
        console.print("=" * 50)
        console.print(f"Config:   {audit['config_path']}", markup=False)
        console.print(f"Template: {audit['template_path']}", markup=False)

        if not audit["stale"]:
            console.print("\n✅ Alias contract matches the repo-owned template.")
            return

        console.print("\n❌ Stale routing alias contract detected.")

        missing = audit["missing_aliases"]
        if missing:
            console.print("\nMissing aliases:")
            for alias, target in missing.items():
                console.print(f"  - {alias}: expected {target}", markup=False)

        mismatched = audit["mismatched_aliases"]
        if mismatched:
            console.print("\nMismatched aliases:")
            for alias, values in mismatched.items():
                console.print(
                    f"  - {alias}: expected {values['expected']}, found {values['actual']}", markup=False
                )

        console.print("\nNext steps:")
        console.print("  • Preview repair: dopemux routing repair-aliases")
        console.print("  • Apply repair: dopemux routing repair-aliases --apply")
        console.print("  • Inspect config: dopemux routing config")
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

        console.print("🔧 Routing Alias Contract Repair")
        console.print("=" * 50)

        if not audit["stale"]:
            console.print("✅ No alias repair needed.")
            return

        console.print("Planned alias updates:")
        for alias, target in audit["missing_aliases"].items():
            console.print(f"  - add {alias}: {target}", markup=False)
        for alias, values in audit["mismatched_aliases"].items():
            console.print(
                f"  - set {alias}: {values['actual']} -> {values['expected']}", markup=False
            )

        if not apply:
            console.print("\nDry run only. No files changed.")
            console.print("Run `dopemux routing repair-aliases --apply` to write the repair.")
            return

        result = manager.routing_config.repair_alias_contract()
        console.print("\n✅ Alias contract repaired.")
        console.print(f"Backup: {result['backup_path']}", markup=False)
        console.print(f"Updated: {manager.routing_config.config_path}", markup=False)
    except RoutingConfigError as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise SystemExit(2)
    except Exception as e:
        logger.error(f"Failed to repair routing alias contract: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        raise


@routing.command("audit-catalog")
@click.option("--json", "json_output", is_flag=True, help="Emit machine-readable JSON.")
def audit_catalog(json_output: bool):
    """Audit full repo-owned routing catalog drift without writing."""
    try:
        manager = LaunchdServiceManager.get_instance()
        audit = manager.routing_config.audit_catalog_contract()
        if json_output:
            payload = {key: value for key, value in audit.items() if key != "merged_config"}
            click.echo(json.dumps(payload, indent=2, sort_keys=True))
            if audit["stale"]:
                raise SystemExit(1)
            return

        console.print("Routing Catalog Audit")
        console.print("=" * 50)
        if not audit["stale"]:
            console.print("Catalog matches repo-owned template.")
            return
        console.print("Stale repo-owned catalog sections:")
        for section in audit["changed_sections"]:
            console.print(f"  - {section}", markup=False)
        raise SystemExit(1)
    except RoutingConfigError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(2)


@routing.command("sync-catalog")
@click.option(
    "--apply",
    is_flag=True,
    help="Back up and atomically upsert repo-owned catalog sections.",
)
def sync_catalog(apply: bool):
    """Preview or apply additive routing catalog synchronization."""
    try:
        manager = LaunchdServiceManager.get_instance()
        result = manager.routing_config.sync_catalog_contract(apply=apply)
        audit = result["audit"]

        console.print("Routing Catalog Sync")
        console.print("=" * 50)
        if not audit["stale"] and not result["changed"]:
            console.print("No catalog sync needed.")
            return

        console.print("Repo-owned sections to upsert:")
        for section in audit["changed_sections"]:
            console.print(f"  - {section}", markup=False)

        if not apply:
            console.print("\nDry run only. No files changed.")
            console.print("Run `dopemux routing sync-catalog --apply` to write.")
            return

        console.print("\nCatalog synchronized.")
        console.print(f"Backup: {result['backup_path']}", markup=False)
        console.print(f"Updated: {manager.routing_config.config_path}", markup=False)
    except RoutingConfigError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(2)


@routing.command()
def docker():
    """Generate Docker Compose snippets for services."""
    try:
        manager = LaunchdServiceManager.get_instance()
        snippets = manager.generate_docker_compose_snippets()

        console.print("🐳 Docker Compose Snippets:")
        console.print("=" * 50)
        console.print("\nLiteLLM Service:")
        click.echo(snippets['litellm'])
        console.print("\nCCR Service:")
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
        console.print("🔑 Syncing API keys from environment...")
        manager.sync_keys_from_environment()
        console.print("✅ API keys synced successfully!")

        # Show what was synced
        env_path = manager.DOPEMUX_DIR / "routing.env"
        if env_path.exists():
            console.print("\n📋 Synced keys in:")
            console.print(f"   {env_path}", markup=False)

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
        console.print("🔧 Attempting to repair routing services...")

        # Run repair
        repair_result = manager.repair(
            max_passes=max_passes,
            allow_sync_keys=allow_sync_keys
        )

        # Show results
        if repair_result.get("healthy", False):
            console.print("✅ Routing services repaired successfully!")

            # Show final health
            health = repair_result["health"]
            console.print("\n🏥 Final Health Status:")
            for service, info in health.items():
                if service == "mode":
                    continue
                status_emoji = "✅" if info.get("status") == "healthy" else "❌"
                console.print(f"  {status_emoji} {service}: {info.get('status')}", markup=False)
        else:
            console.print("❌ Failed to repair routing services")

            # Show repair attempts
            console.print("\n📋 Repair Attempts:")
            for attempt in repair_result.get("attempts", []):
                status = "✅" if attempt.get("result", {}).get("ok") else "❌"
                console.print(f"  {status} Pass {attempt['pass']}: {attempt['action']}", markup=False)

            # Show diagnostics
            console.print("\n🔍 Diagnostics:")
            log_paths = manager._get_log_paths()
            console.print(f"  LiteLLM launchd log: {log_paths['litellm_launchd']}", markup=False)
            console.print(f"  CCR launchd log: {log_paths['ccr_launchd']}", markup=False)
            console.print(f"  Latest LiteLLM log: {log_paths['litellm_latest']}", markup=False)

            console.print("\n💡 Next steps:")
            console.print("  • Check logs with: tail -f ~/.dopemux/logs/litellm_launchd.log")
            console.print("  • Run health check: dopemux routing health")
            console.print("  • Check service status: dopemux routing status")

            raise SystemExit(1)

    except Exception as e:
        logger.error(f"Failed to repair services: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        raise


def _set_routing_mode(config_path: Path, mode: str) -> None:
    if mode not in {"api", "subscription"}:
        raise RoutingConfigError(f"Unsupported routing mode: {mode}")

    try:
        if config_path.exists():
            loaded = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        else:
            loaded = {}
    except yaml.YAMLError as exc:
        raise RoutingConfigError(f"Invalid routing config {config_path}: {exc}") from exc

    if not isinstance(loaded, dict):
        raise RoutingConfigError(f"Invalid routing config {config_path}: expected a mapping")

    loaded["mode"] = mode
    rendered = yaml.safe_dump(loaded, sort_keys=False)

    config_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = config_path.with_name(f".{config_path.name}.tmp")
    tmp_path.write_text(rendered, encoding="utf-8")
    tmp_path.replace(config_path)


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
