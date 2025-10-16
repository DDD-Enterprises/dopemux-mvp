"""
Interactive Profile Creation Wizard.

ADHD-optimized wizard for creating personalized Dopemux profiles based on
git history analysis and user preferences. Gentle guidance with max 3 questions.
"""

from pathlib import Path
from typing import Dict, List, Optional

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from .profile_analyzer import GitHistoryAnalyzer
from .profile_models import Profile, ADHDConfig, AutoDetection

console = Console()


class ProfileWizard:
    """Interactive wizard for profile creation."""

    # Available MCP servers
    ALL_MCPS = [
        "serena-v2",
        "conport",
        "dope-context",
        "context7",
        "zen",
        "gpt-researcher",
        "exa",
        "desktop-commander",
        "mas-sequential-thinking"
    ]

    def __init__(self, repo_path: Optional[Path] = None):
        """
        Initialize wizard.

        Args:
            repo_path: Path to git repository (default: current directory)
        """
        self.repo_path = repo_path or Path.cwd()
        self.analyzer = GitHistoryAnalyzer(self.repo_path)

    def run(self, profile_name: Optional[str] = None, output_dir: Optional[Path] = None) -> Optional[Path]:
        """
        Run the interactive wizard.

        Args:
            profile_name: Name for the new profile (prompts if not provided)
            output_dir: Directory to save profile (default: ./profiles)

        Returns:
            Path to created profile file, or None if cancelled

        ADHD Optimization: Max 3 questions, auto-suggests from git analysis
        """
        console.print(Panel(
            "[bold cyan]Welcome to the Dopemux Profile Wizard![/bold cyan]\n\n"
            "I'll analyze your git history and help you create a personalized profile.\n"
            "This will only take about 2 minutes. 🚀",
            title="✨ Profile Creation",
            border_style="cyan"
        ))

        # Step 1: Analyze git history
        console.print("\n[cyan]📊 Analyzing your development patterns...[/cyan]")
        analysis = self.analyzer.analyze(days_back=90, max_commits=100)
        self.analyzer.display_analysis(analysis)

        # Step 2: Ask for profile name
        if not profile_name:
            console.print("\n[bold]Question 1 of 3:[/bold] What should we call this profile?")
            profile_name = Prompt.ask(
                "Profile name",
                default="my-workflow",
                show_default=True
            )

        # Step 3: Confirm MCP servers (with smart defaults)
        console.print(f"\n[bold]Question 2 of 3:[/bold] Which MCP servers do you want?")
        console.print(f"[dim]Based on your git history, I recommend: {', '.join(analysis.suggested_mcps)}[/dim]")

        mcp_choice = Prompt.ask(
            "MCP selection",
            choices=["recommended", "minimal", "full", "custom"],
            default="recommended"
        )

        if mcp_choice == "recommended":
            selected_mcps = analysis.suggested_mcps
        elif mcp_choice == "minimal":
            selected_mcps = ["serena-v2", "conport"]
        elif mcp_choice == "full":
            selected_mcps = self.ALL_MCPS
        else:  # custom
            console.print("\n[cyan]Available MCPs:[/cyan]")
            for i, mcp in enumerate(self.ALL_MCPS, 1):
                console.print(f"  {i}. {mcp}")
            console.print("\n[dim]Enter numbers separated by commas (e.g., 1,2,4)[/dim]")
            selection = Prompt.ask("MCP numbers")
            indices = [int(x.strip()) - 1 for x in selection.split(',') if x.strip().isdigit()]
            selected_mcps = [self.ALL_MCPS[i] for i in indices if 0 <= i < len(self.ALL_MCPS)]

        # Step 4: ADHD preferences
        console.print(f"\n[bold]Question 3 of 3:[/bold] ADHD session preferences")
        console.print(f"[dim]Suggested: {analysis.suggested_session_duration} min sessions, {analysis.suggested_energy_level} energy[/dim]")

        use_suggested = Confirm.ask(
            "Use suggested ADHD settings?",
            default=True
        )

        if use_suggested:
            session_duration = analysis.suggested_session_duration
            energy_level = analysis.suggested_energy_level
        else:
            session_duration = int(Prompt.ask(
                "Session duration (minutes)",
                default=str(analysis.suggested_session_duration)
            ))
            energy_level = Prompt.ask(
                "Energy level",
                choices=["low", "medium", "high"],
                default=analysis.suggested_energy_level
            )

        # Build the profile
        profile = self._build_profile(
            name=profile_name,
            mcps=selected_mcps,
            session_duration=session_duration,
            energy_level=energy_level,
            git_analysis=analysis
        )

        # Step 5: Save profile
        if not output_dir:
            output_dir = self.repo_path / "profiles"

        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{profile_name}.yaml"

        # Confirm before writing
        console.print(f"\n[bold]Profile Summary:[/bold]")
        console.print(f"   • Name: [cyan]{profile.name}[/cyan]")
        console.print(f"   • MCPs: [cyan]{len(profile.mcps)} servers[/cyan]")
        console.print(f"   • Session: [cyan]{session_duration} min[/cyan]")
        console.print(f"   • Energy: [cyan]{energy_level}[/cyan]")
        console.print(f"   • File: [dim]{output_file}[/dim]")

        if not Confirm.ask(f"\nSave profile to {output_file}?", default=True):
            console.print("[yellow]❌ Profile creation cancelled[/yellow]")
            return None

        # Write profile YAML
        self._save_profile(profile, output_file)

        console.print(f"\n[green]✅ Profile '{profile_name}' created successfully![/green]")
        console.print(f"\n[dim]💡 Next steps:[/dim]")
        console.print(f"   • Test it: [cyan]dopemux profile show {profile_name}[/cyan]")
        console.print(f"   • Apply it: [cyan]dopemux profile apply {profile_name}[/cyan]")

        return output_file

    def _build_profile(
        self,
        name: str,
        mcps: List[str],
        session_duration: int,
        energy_level: str,
        git_analysis
    ) -> Profile:
        """Build Profile object from wizard inputs."""
        # Create ADHD config
        adhd_config = ADHDConfig(
            energy_preference=energy_level,
            attention_mode="focused",
            session_duration=session_duration
        )

        # Create auto-detection rules from git analysis
        auto_detection = None
        if git_analysis.common_branch_prefixes:
            branch_patterns = [prefix for prefix, _ in git_analysis.common_branch_prefixes[:3]]
            auto_detection = AutoDetection(
                git_branches=[f"{prefix}/*" for prefix in branch_patterns if prefix]
            )

        # Build profile
        profile = Profile(
            name=name,
            display_name=name.replace("-", " ").replace("_", " ").title(),
            description=f"Personalized profile based on your development patterns",
            mcps=mcps,
            adhd_config=adhd_config,
            auto_detection=auto_detection
        )

        return profile

    def _save_profile(self, profile: Profile, output_file: Path) -> None:
        """Save profile to YAML file."""
        # Convert to dict
        profile_dict = profile.model_dump(exclude_none=True, exclude_defaults=True)

        # Write YAML
        with open(output_file, 'w') as f:
            # Add header comment
            f.write(f"# Dopemux Profile: {profile.display_name}\n")
            f.write(f"# Created by Profile Wizard\n")
            f.write(f"# Auto-generated from git history analysis\n\n")

            yaml.dump(profile_dict, f, default_flow_style=False, indent=2, sort_keys=False)

        console.print(f"[dim]   Written {output_file.stat().st_size} bytes to {output_file.name}[/dim]")
