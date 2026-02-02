"""
ADHD Notification Styles

Theming and styling for ADHD findings across all output channels.
Supports multiple color themes and emoji sets.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class Theme(str, Enum):
    """Available color themes."""
    NEON = "neon"       # Vibrant cyberpunk colors
    CALM = "calm"       # Muted, low-stimulation
    DARK = "dark"       # High contrast dark mode
    LIGHT = "light"     # Light mode
    ADHD = "adhd"       # Fun, dopamine-boosting


class EmojiSet(str, Enum):
    """Emoji style options."""
    FUN = "fun"           # Playful emojis
    MINIMAL = "minimal"   # Unicode symbols only
    PROFESSIONAL = "professional"  # Subdued icons
    NONE = "none"         # No emojis


@dataclass
class SeverityStyle:
    """Style configuration for a severity level."""
    ansi_fg: str          # ANSI foreground color code
    ansi_bg: str          # ANSI background color code (optional)
    emoji: str            # Default emoji
    sound_name: str       # macOS sound name (optional)
    border_style: str     # Rich border style


@dataclass
class NotificationTheme:
    """Complete theme configuration."""
    name: str
    severities: Dict[str, SeverityStyle]
    accent_color: str
    border_color: str
    
    def get_style(self, severity: str) -> SeverityStyle:
        """Get style for severity, with fallback."""
        return self.severities.get(severity, self.severities.get("medium"))


# ───────────────────────────────────────────────────────────────
# ANSI Color Codes
# ───────────────────────────────────────────────────────────────
class ANSI:
    """ANSI escape codes."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    
    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright foreground
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    
    # Background colors
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"


# ───────────────────────────────────────────────────────────────
# Emoji Sets
# ───────────────────────────────────────────────────────────────
EMOJI_SETS: Dict[EmojiSet, Dict[str, str]] = {
    EmojiSet.FUN: {
        "low": "💚",
        "medium": "💛",
        "high": "🧡",
        "critical": "❤️‍🔥",
        "hyperfocus": "🔥",
        "overwhelm": "😰",
        "break": "☕",
        "energy_high": "⚡",
        "energy_medium": "🔋",
        "energy_low": "🪫",
        "focus": "🎯",
        "distracted": "🌊",
        "success": "🚀",
        "warning": "⚠️",
        "info": "💡",
    },
    EmojiSet.MINIMAL: {
        "low": "○",
        "medium": "◐",
        "high": "●",
        "critical": "◉",
        "hyperfocus": "★",
        "overwhelm": "✕",
        "break": "□",
        "energy_high": "▲",
        "energy_medium": "■",
        "energy_low": "▼",
        "focus": "◆",
        "distracted": "~",
        "success": "✓",
        "warning": "!",
        "info": "i",
    },
    EmojiSet.PROFESSIONAL: {
        "low": "ℹ️",
        "medium": "⚡",
        "high": "⚠️",
        "critical": "🔴",
        "hyperfocus": "🔒",
        "overwhelm": "🚫",
        "break": "⏸️",
        "energy_high": "🟢",
        "energy_medium": "🟡",
        "energy_low": "🔴",
        "focus": "🎯",
        "distracted": "📡",
        "success": "✅",
        "warning": "⚠️",
        "info": "ℹ️",
    },
    EmojiSet.NONE: {
        key: "" for key in ["low", "medium", "high", "critical", "hyperfocus",
                           "overwhelm", "break", "energy_high", "energy_medium",
                           "energy_low", "focus", "distracted", "success",
                           "warning", "info"]
    },
}


# ───────────────────────────────────────────────────────────────
# Pre-configured Themes
# ───────────────────────────────────────────────────────────────
THEMES: Dict[Theme, NotificationTheme] = {
    Theme.NEON: NotificationTheme(
        name="Neon",
        severities={
            "low": SeverityStyle(ANSI.BRIGHT_CYAN, "", "💡", "", "cyan"),
            "medium": SeverityStyle(ANSI.BRIGHT_YELLOW, "", "💛", "Pop", "yellow"),
            "high": SeverityStyle(ANSI.BRIGHT_MAGENTA, "", "🧡", "Sosumi", "magenta"),
            "critical": SeverityStyle(ANSI.BRIGHT_RED + ANSI.BOLD, "", "❤️‍🔥", "Basso", "red"),
        },
        accent_color="#7dfbf6",
        border_color="bright_magenta",
    ),
    Theme.CALM: NotificationTheme(
        name="Calm",
        severities={
            "low": SeverityStyle(ANSI.DIM + ANSI.WHITE, "", "○", "", "dim"),
            "medium": SeverityStyle(ANSI.WHITE, "", "◐", "", "white"),
            "high": SeverityStyle(ANSI.YELLOW, "", "●", "", "yellow"),
            "critical": SeverityStyle(ANSI.RED, "", "◉", "Submarine", "red"),
        },
        accent_color="#8899aa",
        border_color="dim",
    ),
    Theme.ADHD: NotificationTheme(
        name="ADHD Friendly",
        severities={
            "low": SeverityStyle(ANSI.BRIGHT_GREEN, "", "🌱", "", "green"),
            "medium": SeverityStyle(ANSI.BRIGHT_CYAN, "", "🌊", "Pop", "cyan"),
            "high": SeverityStyle(ANSI.BRIGHT_YELLOW + ANSI.BOLD, "", "⚡", "Ping", "yellow"),
            "critical": SeverityStyle(ANSI.BRIGHT_MAGENTA + ANSI.BOLD + ANSI.BLINK, "", "🔥", "Hero", "magenta"),
        },
        accent_color="#ff69b4",
        border_color="bright_cyan",
    ),
}


# ───────────────────────────────────────────────────────────────
# Sound Alerts
# ───────────────────────────────────────────────────────────────
SOUND_ALERTS: Dict[str, str] = {
    # macOS system sounds
    "gentle": "Pop",
    "attention": "Ping",
    "warning": "Sosumi",
    "urgent": "Basso",
    "success": "Glass",
    "error": "Funk",
}


@dataclass
class StyleConfig:
    """User's style configuration."""
    theme: Theme = Theme.NEON
    emoji_set: EmojiSet = EmojiSet.FUN
    enable_sound: bool = True
    enable_blink: bool = False  # Can be distracting for ADHD
    
    def get_theme(self) -> NotificationTheme:
        """Get current theme."""
        return THEMES.get(self.theme, THEMES[Theme.NEON])
    
    def get_emoji(self, key: str) -> str:
        """Get emoji for key."""
        return EMOJI_SETS.get(self.emoji_set, EMOJI_SETS[EmojiSet.FUN]).get(key, "")
    
    def format_message(self, message: str, severity: str) -> str:
        """Format message with theme colors."""
        theme = self.get_theme()
        style = theme.get_style(severity)
        emoji = self.get_emoji(severity)
        
        # Remove blink if disabled
        ansi = style.ansi_fg
        if not self.enable_blink and ANSI.BLINK in ansi:
            ansi = ansi.replace(ANSI.BLINK, "")
        
        return f"{ansi}{emoji} {message}{ANSI.RESET}"


# Default configuration
DEFAULT_STYLE = StyleConfig()


def get_style_config() -> StyleConfig:
    """Get current style configuration (could be user-specific)."""
    return DEFAULT_STYLE


def format_finding(finding_type: str, severity: str, message: str) -> str:
    """Format a finding with current style."""
    config = get_style_config()
    return config.format_message(f"[{finding_type}] {message}", severity)
