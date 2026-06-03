"""
Interactive Prompts for Dopemux ADHD UX

Provides choice-limited, progressive disclosure prompts using Questionary.
Designed for ADHD workflows with minimal cognitive load and clear next steps.
"""

from typing import List, Dict, Any, Optional, Union

import logging

logger = logging.getLogger(__name__)

from ..console import console
from .questionary_support import require_questionary


def _questionary_parts():
    questionary = require_questionary()
    return questionary, questionary.Choice


class InteractivePrompts:
    """
    ADHD-optimized interactive prompts with progressive disclosure.

    Limits choices to prevent decision paralysis, provides clear defaults,
    and supports context-aware responses.
    """

    def __init__(self):
        self.max_choices = 3  # ADHD-optimized limit
        self.default_timeout = 30  # Seconds before auto-selecting default

    def ask_action_selection(
        self,
        actions: List[Dict[str, Any]],
        context: str = "",
        *,
        show_all: bool = False,
    ) -> Optional[str]:
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

        # Limit to max_choices until the operator explicitly expands the list.
        display_actions = sorted_actions if show_all else sorted_actions[:self.max_choices]

        # Create choices with descriptions
        questionary, Choice = _questionary_parts()
        choices = []
        for action in display_actions:
            choice_text = f"{action['name']}: {action['description'][:50]}"
            if len(action['description']) > 50:
                choice_text += "..."
            choices.append(Choice(choice_text, value=action['name']))

        # Add "Show more options" if limited
        if len(sorted_actions) > len(display_actions):
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
                return self.ask_action_selection(
                    actions,
                    f"{context} (showing all options)",
                    show_all=True,
                )
            else:
                return result

        except KeyboardInterrupt:
            console.log("[warning]Selection cancelled[/warning]")
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
                questionary, _Choice = _questionary_parts()
                return questionary.confirm(question, default=default).ask()
            except KeyboardInterrupt:
                return default
        else:
            # Normal complexity - show options
            questionary, Choice = _questionary_parts()
            options = ["Yes", "No", "Show details"]
            result = questionary.select(
                message,
                choices=[Choice(opt, value=opt.lower()) for opt in options],
                default="yes" if default else "no"
            ).ask()

            if result == "show details":
                console.log(f"[text.dim]{message} - This action will proceed with the recommended settings.[/text.dim]")
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

        questionary, Choice = _questionary_parts()
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
            console.log("[warning]Break skipped[/warning]")
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
        console.log("[bold]Operation Summary:[/bold]")
        for key, value in basic_info.items():
            console.log(f"  {key}: {value}")

        # Offer to show more based on user level
        if user_level in ["intermediate", "expert"]:
            try:
                questionary, _Choice = _questionary_parts()
                show_more = questionary.confirm(
                    "Show detailed information?",
                    default=False
                ).ask()

                if show_more:
                    console.log("\n[bold]Detailed Information:[/bold]")
                    for key, value in full_info.items():
                        if key not in basic_info:
                            console.log(f"  {key}: {value}")
                    return full_info
            except KeyboardInterrupt:
                pass

        return basic_info

    def show_menu(
        self,
        title: str,
        options: List[Dict[str, Any]],
        context: str = "",
        *,
        show_all: bool = False,
    ) -> Optional[str]:
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
            console.log(f"[warning]No {title.lower()} available[/warning]")
            return None

        # Create choices
        questionary, Choice = _questionary_parts()
        choices = []
        display_options = options if show_all else options[:self.max_choices]

        for option in display_options:
            choice_text = f"{option['name']}"
            if 'description' in option:
                choice_text += f" - {option['description'][:30]}"
            choices.append(Choice(choice_text, value=option.get('action', option['name'])))

        if len(options) > len(display_options):
            choices.append(Choice("Show all options...", value="__show_all__"))

        # Add back/cancel option
        choices.append(Choice("Cancel", value="__cancel__"))

        try:
            if context:
                console.log(f"[text.dim]{context}[/text.dim]")

            result = questionary.select(
                title,
                choices=choices,
                default=choices[0] if choices else None
            ).ask()

            if result == "__show_all__":
                return self.show_menu(
                    title,
                    options,
                    f"{context} (showing all)",
                    show_all=True,
                )
            elif result == "__cancel__":
                return None
            else:
                return result

        except KeyboardInterrupt:
            console.log("[warning]Menu cancelled[/warning]")
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
