# Fonts

This design system declares the following font stack:

```
"JetBrainsMono Nerd Font", "JetBrains Mono", "Fira Code",
"SFMono-Regular", "Menlo", "Consolas", ui-monospace, monospace
```

**Brand mono:** `IosevkaHueTerm-Regular.ttf` ships in this folder and is
loaded via `@font-face` in `colors_and_type.css`. Single weight; bold is
synthesized.

**Nerd Font:** No Nerd Font binary ships here. The cockpit needs a monospace font with
Powerline / Nerd Font glyph coverage to render the icon set in
`src/dopemux/ui/theme.py::Glyphs`. The fallback chain degrades to plain
mono — every glyph has an ASCII fallback in `Glyphs._FALLBACK`, so the
TUI remains legible without the font.

If pixel-perfect Nerd Font glyphs matter to you, drop a build of
**JetBrains Mono Nerd Font** into this folder and add a `@font-face`
rule in your output.

> Get JetBrains Mono Nerd Font:
> https://www.nerdfonts.com/font-downloads (look for "JetBrainsMono")
