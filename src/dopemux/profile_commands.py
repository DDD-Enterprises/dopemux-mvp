"""
Profile management CLI commands.

Provides user-facing commands for managing Dopemux profiles including
listing, showing details, and validating profiles against Claude config.
"""

from pathlib import Path
from typing import Optional

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

from .profile_parser import ProfileParser, ProfileParseError, parse_profile_file
from .claude_config import ClaudeConfig, ClaudeConfigError
from .profile_models import Profile

console = Console()


def get_profiles_directory() -> Path:
    """Get the default profiles directory.

    Returns:
        Path to profiles directory (~/code/dopemux-mvp/profiles or ./profiles)
    """
    # Try project root first
    project_root = Path.cwd()
    profiles_dir = project_root / "profiles"

    if profiles_dir.exists():
        return profiles_dir

    # Fallback to ~/.dopemux/profiles
    home_profiles = Path.home() / ".dopemux" / "profiles"
    home_profiles.mkdir(parents=True, exist_ok=True)
    return home_profiles


def list_profiles(profiles_dir: Optional[Path] = None) -> None:
    """List all available profiles.

    Args:
        profiles_dir: Directory containing profiles (default: auto-detect)
    """
    if profiles_dir is None:
        profiles_dir = get_profiles_directory()

    if not profiles_dir.exists():
        console.print(f"[yellow]⚠️  No profiles directory found at {profiles_dir}[/yellow]")
        console.print("\nCreate profiles in one of these locations:")
        console.print(f"  • {Path.cwd() / 'profiles'}")
        console.print(f"  • {Path.home() / '.dopemux' / 'profiles'}")
        return

    # Find all YAML profile files
    profile_files = sorted(profiles_dir.glob("*.yaml"))
    profile_files.extend(sorted(profiles_dir.glob("*.yml")))

    if not profile_files:
        console.print(f"[yellow]⚠️  No profile files found in {profiles_dir}[/yellow]")
        console.print("\nCreate a profile file like:")
        console.print("  profiles/developer.yaml")
        return

    # Parse and display profiles
    parser = ProfileParser(validate_mcps=False)

    table = Table(title="📋 Available Profiles", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="green", width=15)
    table.add_column("Display Name", width=20)
    table.add_column("Description", width=40)
    table.add_column("MCPs", justify="right", width=8)

    for file_path in profile_files:
        try:
            collection = parser.parse_file(file_path)
            for profile in collection.profiles:
                table.add_row(
                    profile.name,
                    profile.display_name,
                    profile.description[:40] + ("..." if len(profile.description) > 40 else ""),
                    str(len(profile.mcps))
                )
        except ProfileParseError as e:
            console.print(f"[red]⚠️  Error parsing {file_path.name}: {e.message}[/red]")

    console.print(table)
    console.print(f"\n[dim]Profiles directory: {profiles_dir}[/dim]")


def show_profile(profile_name: str, profiles_dir: Optional[Path] = None) -> None:
    """Show detailed information about a profile.

    Args:
        profile_name: Name of the profile to show
        profiles_dir: Directory containing profiles (default: auto-detect)
    """
    if profiles_dir is None:
        profiles_dir = get_profiles_directory()

    # Try to find profile file
    profile_file = profiles_dir / f"{profile_name}.yaml"
    if not profile_file.exists():
        profile_file = profiles_dir / f"{profile_name}.yml"

    if not profile_file.exists():
        console.print(f"[red]❌ Profile '{profile_name}' not found at {profile_file}[/red]")
        console.print("\nAvailable profiles:")
        list_profiles(profiles_dir)
        return

    try:
        # Parse profile
        parser = ProfileParser(validate_mcps=False)
        collection = parser.parse_file(profile_file)
        profile = collection.get_profile(profile_name)

        if profile is None:
            console.print(f"[red]❌ Profile '{profile_name}' not found in {profile_file}[/red]")
            return

        # Display profile details
        console.print(Panel(
            f"[bold cyan]{profile.display_name}[/bold cyan]\n\n"
            f"{profile.description}",
            title=f"📄 Profile: {profile.name}",
            border_style="cyan"
        ))

        # MCP Servers
        console.print("\n[bold]MCP Servers:[/bold]")
        mcp_table = Table(show_header=False, box=None, padding=(0, 2))
        for mcp in profile.mcps:
            mcp_table.add_row("•", mcp)
        console.print(mcp_table)

        # ADHD Config
        if profile.adhd_config:
            console.print("\n[bold]ADHD Configuration:[/bold]")
            adhd_table = Table(show_header=False, box=None, padding=(0, 2))
            adhd_table.add_row("Energy Preference:", str(profile.adhd_config.energy_preference))
            adhd_table.add_row("Attention Mode:", str(profile.adhd_config.attention_mode))
            adhd_table.add_row("Session Duration:", f"{profile.adhd_config.session_duration} minutes")
            console.print(adhd_table)

        # Auto-detection
        if profile.auto_detection:
            console.print("\n[bold]Auto-Detection Rules:[/bold]")

            if profile.auto_detection.git_branches:
                console.print("\n  [cyan]Git Branches:[/cyan]")
                for branch in profile.auto_detection.git_branches:
                    console.print(f"    • {branch}")

            if profile.auto_detection.directories:
                console.print("\n  [cyan]Directories:[/cyan]")
                for directory in profile.auto_detection.directories:
                    console.print(f"    • {directory}")

            if profile.auto_detection.file_patterns:
                console.print("\n  [cyan]File Patterns:[/cyan]")
                for pattern in profile.auto_detection.file_patterns:
                    console.print(f"    • {pattern}")

            if profile.auto_detection.time_windows:
                console.print("\n  [cyan]Time Windows:[/cyan]")
                for window in profile.auto_detection.time_windows:
                    console.print(f"    • {window}")

        # Show raw YAML
        console.print("\n[bold]Raw YAML:[/bold]")
        with open(profile_file, "r") as f:
            yaml_content = f.read()

        syntax = Syntax(yaml_content, "yaml", theme="monokai", line_numbers=False)
        console.print(syntax)

        console.print(f"\n[dim]File: {profile_file}[/dim]")

    except ProfileParseError as e:
        console.print(f"[red]❌ Error parsing profile: {e}[/red]")
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")


def validate_profile(
    profile_name: str,
    profiles_dir: Optional[Path] = None,
    dry_run: bool = True
) -> bool:
    """Validate a profile against Claude configuration.

    Args:
        profile_name: Name of the profile to validate
        profiles_dir: Directory containing profiles (default: auto-detect)
        dry_run: Whether to test config generation without writing

    Returns:
        True if validation passed, False otherwise
    """
    if profiles_dir is None:
        profiles_dir = get_profiles_directory()

    # Find profile file
    profile_file = profiles_dir / f"{profile_name}.yaml"
    if not profile_file.exists():
        profile_file = profiles_dir / f"{profile_name}.yml"

    if not profile_file.exists():
        console.print(f"[red]❌ Profile '{profile_name}' not found[/red]")
        return False

    try:
        # Parse profile
        parser = ProfileParser(validate_mcps=False)
        collection = parser.parse_file(profile_file)
        profile = collection.get_profile(profile_name)

        if profile is None:
            console.print(f"[red]❌ Profile '{profile_name}' not found in file[/red]")
            return False

        console.print(f"[green]✅ Profile YAML is valid[/green]")
        console.print(f"   • Name: {profile.name}")
        console.print(f"   • MCPs: {len(profile.mcps)} servers")

        # Validate against Claude config
        console.print("\n[bold]Validating against Claude configuration...[/bold]")

        try:
            config = ClaudeConfig()
            result = config.validate_profile_against_config(profile)

            if result["available"]:
                console.print(f"\n[green]✅ Available MCP servers ({len(result['available'])}):[/green]")
                for mcp in result["available"]:
                    console.print(f"   • {mcp}")

            if result["missing"]:
                console.print(f"\n[red]❌ Missing MCP servers ({len(result['missing'])}):[/red]")
                for mcp in result["missing"]:
                    console.print(f"   • {mcp}")
                console.print("\n[yellow]⚠️  These servers must be configured in Claude before using this profile[/yellow]")
                return False

            # Test config generation (dry run)
            if dry_run:
                console.print("\n[bold]Testing config generation (dry run)...[/bold]")
                new_config = config.apply_profile(profile, dry_run=True)

                console.print(f"[green]✅ Config generation successful[/green]")
                console.print(f"   • Would enable {len(new_config['mcpServers'])} MCP servers")
                console.print(f"   • Would preserve env, statusLine, and other settings")

                # Show what would be enabled
                console.print("\n[bold]MCP servers that would be enabled:[/bold]")
                for server_name in sorted(new_config['mcpServers'].keys()):
                    console.print(f"   • {server_name}")

            console.print("\n[green]✅ Profile validation passed![/green]")
            return True

        except ClaudeConfigError as e:
            console.print(f"\n[red]❌ Claude config error: {e}[/red]")
            return False

    except ProfileParseError as e:
        console.print(f"[red]❌ Profile parse error: {e}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        return False


def apply_profile(
    profile_name: str,
    profiles_dir: Optional[Path] = None,
    create_backup: bool = True
) -> bool:
    """Apply a profile to Claude configuration.

    Args:
        profile_name: Name of the profile to apply
        profiles_dir: Directory containing profiles (default: auto-detect)
        create_backup: Whether to create a backup first

    Returns:
        True if successful, False otherwise
    """
    if profiles_dir is None:
        profiles_dir = get_profiles_directory()

    # Find and parse profile
    profile_file = profiles_dir / f"{profile_name}.yaml"
    if not profile_file.exists():
        profile_file = profiles_dir / f"{profile_name}.yml"

    if not profile_file.exists():
        console.print(f"[red]❌ Profile '{profile_name}' not found[/red]")
        return False

    try:
        # Parse profile
        collection = parse_profile_file(profile_file, validate_mcps=False)
        profile = collection.get_profile(profile_name)

        if profile is None:
            console.print(f"[red]❌ Profile '{profile_name}' not found in file[/red]")
            return False

        # Apply to Claude config
        console.print(f"[bold]Applying profile '{profile.display_name}'...[/bold]")

        config = ClaudeConfig()

        # Validate first
        result = config.validate_profile_against_config(profile)
        if result["missing"]:
            console.print(f"\n[red]❌ Cannot apply profile: missing MCP servers[/red]")
            for mcp in result["missing"]:
                console.print(f"   • {mcp}")
            return False

        # Create backup
        if create_backup:
            console.print("\n[cyan]📦 Creating backup...[/cyan]")
            backup_path = config.backup_config()
            console.print(f"[green]✅ Backup created: {backup_path.name}[/green]")

        # Apply profile
        console.print(f"\n[cyan]⚙️  Applying profile...[/cyan]")
        new_config = config.apply_profile(profile, create_backup=False)  # Already backed up

        console.print(f"[green]✅ Profile '{profile_name}' applied successfully![/green]")
        console.print(f"   • Enabled {len(new_config['mcpServers'])} MCP servers")
        console.print(f"   • Preserved all other settings")

        if create_backup:
            console.print(f"\n[dim]💡 To rollback: dopemux profile rollback[/dim]")

        return True

    except (ProfileParseError, ClaudeConfigError) as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        return False
