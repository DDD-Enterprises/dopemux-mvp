"""
Profile Commands
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from subprocess import CalledProcessError
from typing import Optional, Dict, List, Sequence

import click
import yaml
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..console import console

@click.group()
def profile():
    """📋 Manage MCP profiles for context-aware tool selection."""
    pass


@profile.command("list")
@click.option("--profile-dir", "-d", help="Profile directory path", type=click.Path(exists=True))
@click.pass_context
def profile_list_cmd(ctx, profile_dir: Optional[str]):
    """📋 List all available profiles.

    Shows all profiles with their MCP server counts and descriptions.
    Profiles can be applied with: dopemux profile apply <name>
    """
    try:
        # Get profiles directory
        from ..profile_commands import get_profiles_directory
        profiles_directory = Path(profile_dir) if profile_dir else get_profiles_directory()

        # Parse all profiles in directory
        parser = ProfileParser(validate_mcps=False)
        profile_set = parser.parse_directory(profiles_directory, pattern="*.yaml")

        if not profile_set.profiles:
            console.logger.info("[yellow]⚠️  No valid profiles found[/yellow]")
            console.logger.info(f"\n[dim]Profile directory: {profiles_directory}[/dim]")
            console.logger.info("\n[cyan]💡 Get started:[/cyan]")
            console.logger.info(f"   • Create personalized profile: [white]dopemux profile init[/white]")
            console.logger.info(f"   • See examples: [white]dopemux profile --help[/white]")
            console.logger.info(f"   • Read guide: [white]docs/guides/PROFILE_USER_GUIDE.md[/white]")
            sys.exit(1)

        # Display profiles in a rich table
        table = Table(title="📋 Available Profiles", show_header=True, header_style="bold cyan")
        table.add_column("Name", style="green")
        table.add_column("Display Name", style="cyan")
        table.add_column("MCPs", style="yellow")
        table.add_column("Description", style="white", no_wrap=False)

        for p in profile_set.profiles:
            mcp_count = len(p.mcps)
            table.add_row(
                p.name,
                p.display_name,
                f"{mcp_count} servers",
                p.description
            )

        console.logger.info(table)
        console.logger.info(f"\n[dim]Profile directory: {profiles_directory}[/dim]")
        console.logger.info(f"[dim]Total profiles: {len(profile_set.profiles)}[/dim]")

        # Add helpful tips
        console.logger.info(f"\n[cyan]💡 Quick Tips:[/cyan]")
        console.logger.info(f"   • View details: [white]dopemux profile show <name>[/white]")
        console.logger.info(f"   • Apply profile: [white]dopemux profile apply <name>[/white]")
        console.logger.info(f"   • Create custom: [white]dopemux profile init[/white]")

    except FileNotFoundError as e:
        console.logger.error(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.logger.error(f"[red]Unexpected error: {e}[/red]")
        if ctx.obj.get("verbose"):
            raise
        sys.exit(1)


@profile.command("init")
@click.argument("profile_name", required=False)
@click.option("--output-dir", "-o", help="Output directory for profile", type=click.Path())
@click.pass_context
def profile_init_cmd(ctx, profile_name: Optional[str], output_dir: Optional[str]):
    """✨ Create a personalized profile using git history analysis."""
    try:
        from ..profile_wizard import ProfileWizard

        # Initialize wizard
        wizard = ProfileWizard()

        # Run interactive wizard
        output_path = Path(output_dir) if output_dir else None
        result_file = wizard.run(profile_name=profile_name, output_dir=output_path)

        if result_file:
            sys.exit(0)
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        console.logger.info("\n[yellow]❌ Profile creation cancelled[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.logger.error(f"[red]Unexpected error: {e}[/red]")
        if ctx.obj.get("verbose"):
            raise
        sys.exit(1)


@profile.command("auto-enable")
@click.option("--check-interval", "-i", type=int, help="Check interval in seconds (default: 300)")
@click.option("--threshold", "-t", type=float, help="Confidence threshold (default: 0.85)")
@click.pass_context
def profile_auto_enable_cmd(ctx, check_interval: Optional[int], threshold: Optional[float]):
    """🔍 Enable auto-detection with gentle profile suggestions."""
    try:
        from ..auto_detection_service import AutoDetectionService, create_default_settings

        # Create default config if it doesn't exist
        config_file = Path.cwd() / ".dopemux" / "profile-settings.yaml"
        if not config_file.exists():
            create_default_settings(config_file)

        # Load and update config
        service = AutoDetectionService(config_file=config_file)

        if check_interval:
            service.config.check_interval_seconds = check_interval
        if threshold:
            service.config.confidence_threshold = threshold

        service.config.enabled = True
        service.config.save(config_file)

        console.logger.info("[green]✅ Auto-detection enabled[/green]")
        console.logger.info(f"   Check interval: {service.config.check_interval_seconds}s ({service.config.check_interval_seconds // 60} min)")
        console.logger.info(f"   Confidence threshold: {service.config.confidence_threshold:.0%}")
        console.logger.info(f"   Quiet hours: {service.config.quiet_hours_start}-{service.config.quiet_hours_end}")
        console.logger.info(f"\n[dim]💡 Service will suggest profile switches when confidence >{service.config.confidence_threshold:.0%}[/dim]")
        console.logger.info(f"[dim]💡 Edit settings: {config_file}[/dim]")

    except Exception as e:
        console.logger.error(f"[red]Error: {e}[/red]")
        if ctx.obj.get("verbose"):
            raise
        sys.exit(1)


@profile.command("auto-disable")
@click.pass_context
def profile_auto_disable_cmd(ctx):
    """⏸️  Disable auto-detection suggestions."""
    try:
        config_file = Path.cwd() / ".dopemux" / "profile-settings.yaml"

        if not config_file.exists():
            console.logger.info("[yellow]Auto-detection not configured[/yellow]")
            return

        from ..auto_detection_service import AutoDetectionConfig

        config = AutoDetectionConfig(config_file)
        config.enabled = False
        config.save(config_file)

        console.logger.info("[green]✅ Auto-detection disabled[/green]")

    except Exception as e:
        console.logger.error(f"[red]Error: {e}[/red]")
        sys.exit(1)


@profile.command("auto-status")
@click.pass_context
def profile_auto_status_cmd(ctx):
    """📊 Show auto-detection configuration and status."""
    try:
        config_file = Path.cwd() / ".dopemux" / "profile-settings.yaml"

        if not config_file.exists():
            console.logger.info("[yellow]Auto-detection not configured[/yellow]")
            console.logger.info(f"\n[dim]Run 'dopemux profile auto-enable' to set up[/dim]")
            return

        from ..auto_detection_service import AutoDetectionConfig

        config = AutoDetectionConfig(config_file)

        status = "[green]Enabled[/green]" if config.enabled else "[red]Disabled[/red]"
        console.logger.info(f"\n[bold]Auto-Detection Status:[/bold] {status}")
        console.logger.info(f"\n[cyan]Settings:[/cyan]")
        console.logger.info(f"   Check interval: {config.check_interval_seconds}s ({config.check_interval_seconds // 60} min)")
        console.logger.info(f"   Confidence threshold: {config.confidence_threshold:.0%}")
        console.logger.info(f"   Debounce period: {config.debounce_minutes} min")
        console.logger.info(f"   Quiet hours: {config.quiet_hours_start}-{config.quiet_hours_end}")

        if config.never_suggest:
            console.logger.info(f"\n[yellow]Never Suggest:[/yellow]")
            for profile in sorted(config.never_suggest):
                console.logger.info(f"   • {profile}")

        console.logger.info(f"\n[dim]Config file: {config_file}[/dim]")

    except Exception as e:
        console.logger.error(f"[red]Error: {e}[/red]")
        sys.exit(1)


@profile.command("stats")
@click.option("--days", "-d", type=int, default=30, help="Days of history to analyze (default: 30)")
@click.pass_context
def profile_stats_cmd(ctx, days: int):
    """📊 Show profile usage analytics and trends."""
    try:
        from ..profile_analytics import get_stats_sync, display_stats

        workspace_id = str(Path.cwd())

        # Get stats from ConPort
        console.logger.info(f"[cyan]📊 Analyzing profile usage (last {days} days)...[/cyan]\n")
        stats = get_stats_sync(workspace_id, days_back=days)

        # Display with visual dashboard
        display_stats(stats, days_back=days)

        # Optimization suggestions (if enough data)
        if stats.total_switches >= 10:
            console.logger.info(f"\n[bold]💡 Optimization Suggestions:[/bold]")

            # Suggest based on patterns
            if stats.switch_accuracy < 70:
                console.logger.info(f"   • [yellow]Low accuracy ({stats.switch_accuracy:.0f}%)[/yellow]: Consider refining auto-detection rules")

            if stats.auto_switches == 0 and stats.total_switches > 20:
                console.logger.info(f"   • [cyan]All manual switches[/cyan]: Try 'dopemux profile auto-enable' for suggestions")

            if stats.suggestion_declined > stats.suggestion_accepted * 2:
                console.logger.info(f"   • [yellow]Many declined suggestions[/yellow]: Lower confidence threshold or adjust profile rules")

            # Suggest creating a new profile for common patterns
            if stats.most_used_profile and stats.usage_by_profile.get(stats.most_used_profile, 0) > stats.total_switches * 0.7:
                console.logger.info(f"   • [green]Stable workflow detected[/green]: Your '{stats.most_used_profile}' profile is well-matched!")

    except Exception as e:
        console.logger.error(f"[red]Error: {e}[/red]")
        if ctx.obj.get("verbose"):
            raise
        sys.exit(1)


@profile.command("analyze-usage")
@click.option("--days", "days_back", type=click.IntRange(1), default=90, show_default=True, help="Days of git history to analyze")
@click.option(
    "--max-commits",
    type=click.IntRange(1),
    default=500,
    show_default=True,
    help="Maximum commits to scan",
)
@click.option(
    "--repo-path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Repository path (defaults to current directory)",
)
@click.pass_context
def profile_analyze_usage_cmd(ctx, days_back: int, max_commits: int, repo_path: Optional[Path]):
    """Analyze git usage patterns to suggest profile defaults."""
    try:
        from ..profile_analyzer import GitHistoryAnalyzer

        analyzer = GitHistoryAnalyzer(repo_path=repo_path or Path.cwd())
        analysis = analyzer.analyze(days_back=days_back, max_commits=max_commits)
        analyzer.display_analysis(analysis)
    except Exception as e:
        console.logger.error(f"[red]Error: {e}[/red]")
        if ctx.obj.get("verbose"):
            raise
        sys.exit(1)


@profile.command("show")
@click.argument("profile_name")
@click.option("--profile-dir", "-d", help="Profile directory path", type=click.Path(exists=True))
@click.option("--raw", "-r", is_flag=True, help="Show raw YAML content")
@click.pass_context
def profile_show_cmd(ctx, profile_name: str, profile_dir: Optional[str], raw: bool):
    """📄 Show detailed profile information."""
    try:
        parser = ProfileParser(Path(profile_dir) if profile_dir else None)
        profile_paths = parser.discover_profiles()

        # Find matching profile
        profile_path = None
        for path in profile_paths:
            if path.stem == profile_name:
                profile_path = path
                break

        if not profile_path:
            console.logger.info(f"[red]Profile '{profile_name}' not found[/red]")
            console.logger.info(f"\nAvailable profiles in {parser.profile_dir}:")
            for path in profile_paths:
                console.logger.info(f"  • {path.stem}")
            sys.exit(1)

        # Show raw YAML if requested
        if raw:
            console.logger.info(f"\n[cyan]Profile: {profile_name}[/cyan]")
            console.logger.info(f"[dim]Path: {profile_path}[/dim]\n")
            with open(profile_path, 'r') as f:
                console.logger.info(f.read())
            return

        # Load and validate profile
        p = parser.load_profile(profile_path)

        # Display formatted profile info
        console.logger.info(f"\n[bold cyan]Profile: {p.display_name}[/bold cyan]")
        console.logger.info(f"[dim]Name: {p.name}[/dim]")
        console.logger.info(f"[dim]File: {profile_path}[/dim]\n")

        console.logger.info(f"[bold]Description:[/bold] {p.description}\n")

        # MCP Servers
        console.logger.info("[bold]MCP Servers:[/bold]")
        for mcp in p.mcps:
            console.logger.info(f"  • {mcp}")

        # ADHD Config (if present)
        if p.adhd_config:
            console.logger.info("\n[bold]ADHD Configuration:[/bold]")
            console.logger.info(f"  Energy preference: {p.adhd_config.energy_preference}")
            console.logger.info(f"  Attention mode: {p.adhd_config.attention_mode}")
            console.logger.info(f"  Session duration: {p.adhd_config.session_duration} minutes")

        # Auto-detection rules (if present)
        if p.auto_detection:
            console.logger.info("\n[bold]Auto-Detection Rules:[/bold]")
            if p.auto_detection.git_branches:
                console.logger.info("  Git branches:")
                for branch in p.auto_detection.git_branches:
                    console.logger.info(f"    • {branch}")
            if p.auto_detection.directories:
                console.logger.info("  Directories:")
                for dir in p.auto_detection.directories:
                    console.logger.info(f"    • {dir}")
            if p.auto_detection.file_patterns:
                console.logger.info("  File patterns:")
                for pattern in p.auto_detection.file_patterns:
                    console.logger.info(f"    • {pattern}")
            if p.auto_detection.time_windows:
                console.logger.info("  Time windows:")
                for window in p.auto_detection.time_windows:
                    console.logger.info(f"    • {window}")

        console.logger.info(f"\n[green]✓ Profile is valid[/green]")

    except ProfileValidationError as e:
        console.logger.error(f"[red]Validation Error:[/red] {e.reason}")
        if e.fix_suggestion:
            console.logger.info(f"[yellow]Suggestion:[/yellow] {e.fix_suggestion}")
        sys.exit(1)
    except FileNotFoundError as e:
        console.logger.error(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.logger.error(f"[red]Unexpected error: {e}[/red]")
        if ctx.obj.get("verbose"):
            raise
        sys.exit(1)


@profile.command("validate")
@click.argument("profile_name", required=False)
@click.option("--profile-dir", "-d", help="Profile directory path", type=click.Path(exists=True))
@click.option("--all", "-a", is_flag=True, help="Validate all profiles")
@click.pass_context
def profile_validate_cmd(ctx, profile_name: Optional[str], profile_dir: Optional[str], all: bool):
    """✅ Validate profile YAML and configuration."""
    try:
        parser = ProfileParser(Path(profile_dir) if profile_dir else None)

        if all:
            # Validate all profiles
            console.logger.info("[cyan]Validating all profiles...[/cyan]\n")
            profile_set = parser.load_all_profiles(fail_fast=False)

            # Show results
            table = Table(title="Validation Results", show_header=True, header_style="bold cyan")
            table.add_column("Profile", style="cyan")
            table.add_column("Status", style="white")
            table.add_column("Message", style="white", no_wrap=False)

            for p in profile_set.profiles:
                table.add_row(p.name, "[green]✓ Valid[/green]", f"{len(p.mcps)} MCP servers")

            for path, error in profile_set.errors:
                error_msg = str(error)
                if isinstance(error, ProfileValidationError):
                    error_msg = f"{error.reason}"
                table.add_row(path.stem, "[red]✗ Invalid[/red]", error_msg)

            console.logger.info(table)

            # Summary
            total = len(profile_set.profiles) + len(profile_set.errors)
            valid = len(profile_set.profiles)
            console.logger.info(f"\n[bold]Summary:[/bold] {valid}/{total} profiles valid")

            if profile_set.errors:
                sys.exit(1)

        else:
            # Validate single profile
            if not profile_name:
                console.logger.error("[red]Error: Provide a profile name or use --all[/red]")
                console.logger.info("Usage: dopemux profile validate <profile_name>")
                console.logger.info("   or: dopemux profile validate --all")
                sys.exit(1)

            profile_paths = parser.discover_profiles()
            profile_path = None
            for path in profile_paths:
                if path.stem == profile_name:
                    profile_path = path
                    break

            if not profile_path:
                console.logger.info(f"[red]Profile '{profile_name}' not found[/red]")
                sys.exit(1)

            console.logger.info(f"[cyan]Validating profile: {profile_name}[/cyan]\n")

            # Load and validate
            p = parser.load_profile(profile_path)

            console.logger.info(f"[green]✓ YAML syntax is valid[/green]")
            console.logger.info(f"[green]✓ Profile schema is valid[/green]")
            console.logger.info(f"[green]✓ All {len(p.mcps)} MCP servers are configured[/green]")
            if p.adhd_config:
                console.logger.info(f"[green]✓ ADHD configuration is valid[/green]")
            if p.auto_detection:
                console.logger.info(f"[green]✓ Auto-detection rules are valid[/green]")

            console.logger.info(f"\n[bold green]Profile '{profile_name}' is valid ✓[/bold green]")

    except ProfileValidationError as e:
        console.logger.error(f"[red]✗ Validation failed:[/red] {e.reason}")
        if e.fix_suggestion:
            console.logger.info(f"[yellow]💡 Suggestion:[/yellow] {e.fix_suggestion}")
        sys.exit(1)
    except FileNotFoundError as e:
        console.logger.error(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.logger.error(f"[red]Unexpected error: {e}[/red]")
        if ctx.obj.get("verbose"):
            raise
        sys.exit(1)


@profile.command("copy")
@click.argument("source_name")
@click.argument("target_name")
def profile_copy_cmd(source_name: str, target_name: str):
    """Copy profile command placeholder."""
    raise click.ClickException("profile copy is not implemented yet")


@profile.command("edit")
@click.argument("profile_name")
def profile_edit_cmd(profile_name: str):
    """Edit profile command placeholder."""
    raise click.ClickException("profile edit is not implemented yet")


@profile.command("delete")
@click.argument("profile_name")
def profile_delete_cmd(profile_name: str):
    """Delete profile command placeholder."""
    raise click.ClickException("profile delete is not implemented yet")


@profile.command("current")
def profile_current_cmd():
    """Show current active profile placeholder."""
    raise click.ClickException("profile current is not implemented yet")


# Register additional profile commands from modules
try:
    from ..profile_commands import (
        use_profile,
        create_profile
    )

    # Note: 'list' and 'show' are already defined above as inline commands.
    # We only add unique commands from the module to avoiding conflicts.
    profile.add_command(use_profile, "use")
    profile.add_command(create_profile, "create")
    profile.add_command(use_profile, "apply")

except ImportError:
    pass  # Profile commands not available
