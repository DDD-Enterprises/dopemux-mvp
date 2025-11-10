"""
Interactive Prompts for Dopemux ADHD UX

Provides choice-limited, progressive disclosure prompts using Questionary.
Designed for ADHD workflows with minimal cognitive load and clear next steps.
"""

from typing import List, Dict, Any, Optional, Union
import questionary
from questionary import Choice
from rich.console import Console

console = Console()


class InteractivePrompts:
    """
    ADHD-optimized interactive prompts with progressive disclosure.

    Limits choices to prevent decision paralysis, provides clear defaults,
    and supports context-aware responses.
    """

    def __init__(self):
        self.max_choices = 3  # ADHD-optimized limit
        self.default_timeout = 30  # Seconds before auto-selecting default

    def ask_action_selection(self, actions: List[Dict[str, Any]], context: str = "") -> Optional[str]:
        """
        Ask user to select from available actions with limited choices.

        Args:
            actions: List of action dicts with 'name', 'description', 'complexity'
            context: Optional context about the current state

        Returns:
            Selected action name or None if cancelled
        """
        if not actions:
            return None

        # Sort by complexity (show simpler options first)
        sorted_actions = sorted(actions, key=lambda x: x.get('complexity', 0.5))

        # Limit to max_choices
        display_actions = sorted_actions[:self.max_choices]

        # Create choices with descriptions
        choices = []
        for action in display_actions:
            choice_text = f"{action['name']}: {action['description'][:50]}"
            if len(action['description']) > 50:
                choice_text += "..."
            choices.append(Choice(choice_text, value=action['name']))

        # Add "Show more options" if limited
        if len(actions) > self.max_choices:
            choices.append(Choice("Show more options...", value="__show_more__"))

        # Ask the question
        question_text = "What would you like to do?"
        if context:
            question_text = f"{context}\n{question_text}"

        try:
            result = questionary.select(
                question_text,
                choices=choices,
                default=choices[0] if choices else None,
                use_indicator=True,
                style=questionary.Style([
                    ('selected', 'fg:ansiblue bold'),
                    ('pointer', 'fg:ansicyan'),
                ])
            ).ask()

            if result == "__show_more__":
                # Show all options
                return self.ask_action_selection(actions, f"{context} (showing all options)")
            else:
                return result

        except KeyboardInterrupt:
            console.print("[yellow]Selection cancelled[/yellow]")
            return None

    def ask_confirmation(self, message: str, default: bool = True, complexity: float = 0.5) -> bool:
        """
        Ask for confirmation with appropriate detail level.

        Args:
            message: Confirmation message
            default: Default answer
            complexity: Current cognitive load (affects detail level)

        Returns:
            User confirmation
        """
        if complexity > 0.7:
            # High complexity - simple yes/no
            question = f"{message} (y/n)"
            try:
                return questionary.confirm(question, default=default).ask()
            except KeyboardInterrupt:
                return default
        else:
            # Normal complexity - show options
            options = ["Yes", "No", "Show details"]
            result = questionary.select(
                message,
                choices=[Choice(opt, value=opt.lower()) for opt in options],
                default="yes" if default else "no"
            ).ask()

            if result == "show details":
                console.print(f"[dim]{message} - This action will proceed with the recommended settings.[/dim]")
                return self.ask_confirmation(message, default, complexity)

            return result == "yes"

    def ask_break_suggestion(self, break_info: Dict[str, Any]) -> Optional[str]:
        """
        Present break suggestions in ADHD-friendly format.

        Args:
            break_info: Break suggestion data

        Returns:
            Selected break activity or None
        """
        if not break_info.get('suggested', False):
            return None

        activities = break_info.get('activities', [])
        if not activities:
            return None

        # Limit activities to prevent overwhelm
        display_activities = activities[:self.max_choices]

        choices = [Choice(activity, value=activity) for activity in display_activities]
        choices.append(Choice("Skip break", value="__skip__"))

        try:
            result = questionary.select(
                f"Break recommended ({break_info.get('reason', 'Time for a break')})",
                choices=choices,
                default=choices[0] if choices else None
            ).ask()

            return None if result == "__skip__" else result

        except KeyboardInterrupt:
            console.print("[yellow]Break skipped[/yellow]")
            return None

    def ask_progressive_details(self, basic_info: Dict[str, Any], full_info: Dict[str, Any], user_level: str = "intermediate") -> Dict[str, Any]:
        """
        Present information with progressive disclosure options.

        Args:
            basic_info: Essential information to show first
            full_info: Complete information available on request
            user_level: User expertise level

        Returns:
            Information appropriate for user level
        """
        # Show basic info first
        console.print("[bold]Operation Summary:[/bold]")
        for key, value in basic_info.items():
            console.print(f"  {key}: {value}")

        # Offer to show more based on user level
        if user_level in ["intermediate", "expert"]:
            try:
                show_more = questionary.confirm(
                    "Show detailed information?",
                    default=False
                ).ask()

                if show_more:
                    console.print("\n[bold]Detailed Information:[/bold]")
                    for key, value in full_info.items():
                        if key not in basic_info:
                            console.print(f"  {key}: {value}")
                    return full_info
            except KeyboardInterrupt:
                pass

        return basic_info

    def show_menu(self, title: str, options: List[Dict[str, Any]], context: str = "") -> Optional[str]:
        """
        Show a menu of options with descriptions.

        Args:
            title: Menu title
            options: List of option dicts with 'name', 'description', 'action'
            context: Optional context information

        Returns:
            Selected option name or None
        """
        if not options:
            console.print(f"[yellow]No {title.lower()} available[/yellow]")
            return None

        # Create choices
        choices = []
        for option in options[:self.max_choices]:  # Limit choices
            choice_text = f"{option['name']}"
            if 'description' in option:
                choice_text += f" - {option['description'][:30]}"
            choices.append(Choice(choice_text, value=option.get('action', option['name'])))

        if len(options) > self.max_choices:
            choices.append(Choice("Show all options...", value="__show_all__"))

        # Add back/cancel option
        choices.append(Choice("Cancel", value="__cancel__"))

        try:
            if context:
                console.print(f"[dim]{context}[/dim]")

            result = questionary.select(
                title,
                choices=choices,
                default=choices[0] if choices else None
            ).ask()

            if result == "__show_all__":
                return self.show_menu(title, options, f"{context} (showing all)")
            elif result == "__cancel__":
                return None
            else:
                return result

        except KeyboardInterrupt:
            console.print("[yellow]Menu cancelled[/yellow]")
            return None


# Convenience functions for common Dopemux interactions
def prompt_action_selection(actions: List[Dict[str, Any]], context: str = "") -> Optional[str]:
    """Convenience function for action selection."""
    prompts = InteractivePrompts()
    return prompts.ask_action_selection(actions, context)


def prompt_confirmation(message: str, default: bool = True) -> bool:
    """Convenience function for confirmations."""
    prompts = InteractivePrompts()
    return prompts.ask_confirmation(message, default)


def prompt_break_activity(break_info: Dict[str, Any]) -> Optional[str]:
    """Convenience function for break suggestions."""
    prompts = InteractivePrompts()
    return prompts.ask_break_suggestion(break_info)