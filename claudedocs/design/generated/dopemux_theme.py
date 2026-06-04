"""Auto-generated Rich theme — Direction B Electric Refresh. DO NOT EDIT."""
from rich.theme import Theme

# ANSI-16 fallback map (NO_COLOR / 16-color terminals)
_ANSI16 = {
    "success":   "bold green",
    "error":     "bold red",
    "warning":   "bold yellow",
    "info":      "bold cyan",
    "aftercare": "bold blue",
}

def build_theme(truecolor: bool = True) -> Theme:
    """Return Rich Theme. Pass truecolor=False for 16-color terminal."""
    if not truecolor:
        return Theme({
            "success":  _ANSI16["success"],
            "error":    _ANSI16["error"],
            "warning":  _ANSI16["warning"],
            "info":     _ANSI16["info"],
            "aftercare":_ANSI16["aftercare"],
            "text":     "default",
            "text.dim": "dim",
            "heading":  "bold",
        })
    return Theme({
        "brand":          "bold #2FFFF0",
        "brand.dim":      "#00C9B8",
        "success":        "bold #00FF85",
        "error":          "bold #FF2255",
        "warning":        "bold #FFE600",
        "info":           "#00E5FF",
        "aftercare":      "#C07BFF",
        "accent":         "#FF00CC",
        "text":           "#E2E8F0",
        "text.dim":       "#94A3B8",
        "text.muted":     "#808DA0",
        "text.disabled":  "#475569",
        "heading":        "bold #2FFFF0",
        "subheading":     "bold #00C9B8",
        "chip.live":      "bold #00E5FF",
        "chip.done":      "bold #00FF85",
        "chip.blocked":   "bold #FF2255",
        "chip.warn":      "bold #FFE600",
        "chip.aftercare": "#C07BFF",
        "table.header":   "bold #2FFFF0",
        "table.border":   "#2E3F54",
        "panel.border":   "#2E3F54",
        "panel.title":    "bold #2FFFF0",
        "bar.complete":   "#2FFFF0",
        "bar.pulse":      "#FF00CC",
    })

# Convenience singleton (truecolor)
THEME = build_theme()