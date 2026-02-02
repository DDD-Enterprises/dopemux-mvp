---
id: terminal-setup
title: ADHD-Optimized Terminal Setup
type: how-to
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
---
# ADHD-Optimized Terminal Setup

Dopemux includes a comprehensive terminal environment installer that sets up modern, fast, and ADHD-friendly tools.

## 🎯 What Gets Installed

### Core Tools

1. **Kitty Terminal**
   - GPU-accelerated
   - Low latency
   - Reduced visual noise
   - Custom ADHD-optimized config

2. **zsh + Oh My Zsh**
   - Fast, modern shell
   - Smart auto-suggestions
   - Syntax highlighting
   - History search

3. **Starship Prompt**
   - Minimal, fast prompt
   - Reduced cognitive load
   - Git status at a glance
   - Battery indicator (laptop reminder)

### Productivity CLI Tools

- **fzf** - Fuzzy finder for files and commands
- **ripgrep (rg)** - Fast grep alternative
- **bat** - Better cat with syntax highlighting
- **eza** - Better ls with icons
- **fd** - Better find
- **zoxide** - Smart directory jumping
- **tldr** - Simplified man pages

## 🚀 Quick Install

```bash
# From dopemux-mvp directory
./install.sh --terminal

# Or directly
./scripts/setup-terminal-env.sh
```

## ✨ Features

### ADHD-Friendly Design

- **Reduced Visual Noise**: Calm color scheme, minimal prompt
- **Fast Response**: Sub-500ms command execution feedback
- **Smart History**: Easy to search and recall commands
- **Visual Feedback**: Emoji and icons for quick recognition
- **Auto-suggestions**: Reduce typing, increase speed

### Keyboard Shortcuts (Kitty)

```bash
# Tabs
Ctrl+Shift+T        New tab
Ctrl+Shift+W        Close tab
Ctrl+Shift+→        Next tab
Ctrl+Shift+←        Previous tab

# Splits
Ctrl+Shift+-        Horizontal split
Ctrl+Shift+\        Vertical split
Ctrl+Shift+→/←/↑/↓  Navigate splits

# Clipboard
Ctrl+Shift+C        Copy
Ctrl+Shift+V        Paste
```

### Shell Aliases

```bash
# Navigation
ll                  # Better ls with details
la                  # Show hidden files
lt                  # Tree view
..                  # Up one directory
...                 # Up two directories

# Git shortcuts
gs                  # git status
ga                  # git add
gc "message"        # git commit -m
gp                  # git push
gl                  # git log (last 10)
gd                  # git diff

# Dopemux shortcuts
dm                  # dopemux
dms                 # dopemux start
dmi                 # dopemux init
dmd                 # dopemux doctor

# Tools
cat                 # Uses bat with syntax highlighting
cd                  # Uses zoxide (smart jumping)
```

### FZF Integration

```bash
Ctrl+R              # Search command history
Ctrl+T              # Search files in current dir
Alt+C               # Change to directory (fuzzy)
```

## 📋 Configuration Files

After installation, you'll have:

```
~/.config/kitty/kitty.conf       # Kitty terminal config
~/.config/starship.toml          # Starship prompt config
~/.zshrc                         # zsh configuration
```

### Customization

All configs are designed to be easily customizable:

**Change Kitty colors:**
```bash
# Edit ~/.config/kitty/kitty.conf
# Search for "color scheme" section
```

**Modify Starship prompt:**
```bash
# Edit ~/.config/starship.toml
# See: https://starship.rs/config/
```

**Add zsh aliases:**
```bash
# Edit ~/.zshrc
# Add your aliases at the bottom
```

## 🎨 Color Scheme

The default theme is **ADHD-optimized** with:
- Low contrast backgrounds (reduce eye strain)
- High contrast text (improve readability)
- Distinct syntax colors (quick visual parsing)
- Calm accent colors (reduce overstimulation)

### Color Philosophy

- **Background**: Dark gray (#1e1e1e) - not pure black
- **Text**: Light gray (#d8d8d8) - not pure white
- **Accent**: Purple/cyan - calming, not aggressive
- **Warnings**: Yellow - noticeable but not alarming
- **Errors**: Red - clear signal without panic

## 🔧 Platform Support

### macOS
✅ Fully supported
- Homebrew packages
- Native Kitty support
- All tools available

### Ubuntu/Debian
✅ Fully supported
- APT packages
- Manual Kitty install
- Cargo for some tools

### Arch Linux
✅ Fully supported
- Pacman packages
- AUR helpers supported

### Fedora
✅ Fully supported
- DNF packages
- All tools available

### WSL2
⚠️  Experimental
- Terminal works
- GUI terminal needs X server

## 🐛 Troubleshooting

### Kitty won't start
```bash
# Check if installed
which kitty

# macOS: Reinstall
brew reinstall kitty

# Linux: Check desktop file
~/.local/kitty.app/bin/kitty
```

### Starship not showing
```bash
# Check if installed
which starship

# Verify .zshrc has init line
grep "starship init" ~/.zshrc

# Restart shell
exec zsh
```

### Fonts not rendering icons
```bash
# Install Nerd Font
brew tap homebrew/cask-fonts
brew install --cask font-jetbrains-mono-nerd-font

# Update Kitty config
# font_family JetBrains Mono Nerd Font
```

### zsh plugins not loading
```bash
# Check Oh My Zsh
ls ~/.oh-my-zsh

# Reinstall plugins
cd ~/.oh-my-zsh/custom/plugins
rm -rf zsh-autosuggestions zsh-syntax-highlighting

# Run setup again
./scripts/setup-terminal-env.sh
```

### Slow shell startup
```bash
# Profile zsh startup
zsh -xv

# Disable heavy plugins in ~/.zshrc
# Comment out: plugins=(...)
```

## 📊 Performance

### Startup Times
- **zsh with Oh My Zsh**: ~200ms
- **Starship prompt**: <50ms per command
- **Kitty terminal**: <100ms launch

### Memory Usage
- **Kitty**: ~50MB baseline
- **zsh**: ~20MB
- **Total**: <100MB (very light)

## 🎓 Learning Resources

### Quick Tips
```bash
# Search command history
Ctrl+R then type keyword

# Jump to frequent directory
z downloads    # Jumps to ~/Downloads

# Quick command help
tldr git       # Simpler than man git

# Find files fast
fd pattern     # Instead of find -name

# Search in files
rg "TODO"      # Instead of grep -r

# Preview file
bat filename   # Syntax highlighted
```

### Advanced Usage

**Custom Starship modules:**
```bash
# Edit ~/.config/starship.toml
[custom.dopemux]
command = "dopemux status --short"
when = "test -f .dopemux"
format = "[$output]($style) "
```

**Kitty layouts:**
```bash
# Create custom layout
kitty @ launch --type=tab
kitty @ launch --type=window --location=hsplit
```

**zsh functions:**
```bash
# Add to ~/.zshrc
work() {
    cd ~/projects/$1
    dopemux start
}
```

## 🔄 Updates

### Update terminal tools
```bash
# macOS
brew upgrade kitty starship fzf ripgrep bat eza

# Ubuntu/Debian
sudo apt update && sudo apt upgrade

# Update Starship
starship update
```

### Update Oh My Zsh
```bash
omz update
```

### Update plugins
```bash
cd ~/.oh-my-zsh/custom/plugins
git pull --all
```

## 🗑️  Uninstall

To remove the terminal setup:

```bash
# Backup first
cp ~/.zshrc ~/.zshrc.backup
cp ~/.config/kitty/kitty.conf ~/.config/kitty/kitty.conf.backup

# Remove configs
rm -rf ~/.config/kitty
rm -rf ~/.config/starship.toml
rm ~/.zshrc

# Restore default shell
chsh -s /bin/bash

# Remove Oh My Zsh
uninstall_oh_my_zsh

# Uninstall tools (macOS)
brew uninstall kitty starship fzf ripgrep bat eza fd zoxide
```

## 🤝 Contributing

Found a bug or have a suggestion?
- Open an issue on GitHub
- Submit a pull request
- Share your custom configs

## 📝 License

Part of Dopemux, licensed under MIT.

---

*Terminal setup designed with ❤️ for developers with ADHD*
