# Dopemux Profile System - User Guide

**Get personalized MCP configurations in 2 minutes** ⚡

## What Are Profiles?

Profiles let you switch between different sets of MCP servers instantly based on what you're working on:

```
📝 Writing docs?    → minimal profile  (fast, focused)
💻 Coding?          → developer profile (LSP, search, docs)
🔬 Researching?     → researcher profile (+ reasoning, web search)
🏗️  Designing?       → architect profile (+ consensus, planning)
```

**ADHD Benefit**: Pre-configured sets = no decision fatigue, instant context switching

## Quick Start

### 1. Create Your Profile (2 minutes)

```bash
dopemux profile init
```

The wizard will:
1. Analyze your git history (branches, directories, work patterns)
2. Ask 3 simple questions (name, MCPs, ADHD settings)
3. Generate a personalized `profiles/your-name.yaml`

**Example Output:**
```
📊 Your Development Pattern Analysis
📈 Activity: 50 commits (1.67 per day)
🌿 Branch Patterns: feature/ (20), fix/ (15)
📁 Common Directories: services (1604), docker (488)
⚡ Suggested: high energy, 30 min sessions
🔧 Recommended MCPs: serena-v2, conport, dope-context, context7

✅ Profile 'my-workflow' created!
```

### 2. View Your Profiles

```bash
dopemux profile list
```

Shows all available profiles with descriptions and MCP counts.

### 3. Apply a Profile

```bash
dopemux profile apply developer
```

This updates your Claude Code configuration to use only the MCPs in that profile.

### 4. Enable Auto-Suggestions (Optional)

```bash
dopemux profile auto-enable
```

The system will gently suggest profile switches when confidence >85%:
- ✅ Non-intrusive (default: No)
- ✅ Respects quiet hours (22:00-08:00)
- ✅ No nagging (30-min debounce)
- ✅ User control ("never" option)

## Available Commands

### Profile Management

| Command | Description | Example |
|---------|-------------|---------|
| `profile list` | Show all profiles | `dopemux profile list` |
| `profile show <name>` | View profile details | `dopemux profile show developer` |
| `profile init [name]` | Create new profile | `dopemux profile init` |
| `profile apply <name>` | Switch to profile | `dopemux profile apply minimal` |
| `profile validate <name>` | Check profile validity | `dopemux profile validate custom` |

### Auto-Detection

| Command | Description | Example |
|---------|-------------|---------|
| `profile auto-enable` | Enable auto-suggestions | `dopemux profile auto-enable` |
| `profile auto-disable` | Disable suggestions | `dopemux profile auto-disable` |
| `profile auto-status` | Show config | `dopemux profile auto-status` |

### Analytics

| Command | Description | Example |
|---------|-------------|---------|
| `profile stats` | Show usage analytics | `dopemux profile stats --days 30` |

## Pre-Made Profiles

Dopemux includes 5 ready-to-use profiles:

### minimal (1 server)
**Best for**: Quick tasks, low energy, documentation
```
MCPs: serena-v2 (file navigation only)
Energy: low
Use when: Writing docs, quick edits, low cognitive load
```

### developer (4 servers)
**Best for**: Implementation, debugging, code work
```
MCPs: serena-v2, conport, dope-context, context7
Energy: medium
Use when: Daily coding, implementing features, debugging
```

### researcher (5 servers)
**Best for**: Investigation, analysis, learning
```
MCPs: serena-v2, conport, dope-context, zen, gpt-researcher
Energy: medium-high
Use when: Deep analysis, research, understanding complex systems
```

### architect (5 servers)
**Best for**: System design, planning, architecture decisions
```
MCPs: serena-v2, conport, dope-context, context7, zen
Energy: high
Use when: Architecture planning, design decisions, system thinking
```

### full (9 servers)
**Best for**: Complex multi-domain work, maximum capability
```
MCPs: All 9 available servers
Energy: high
Use when: Complex tasks requiring multiple capabilities
```

## Auto-Detection How It Works

The detection system scores profiles based on 5 signals (100 points total):

1. **Git Branch** (30 points) - Matches branch patterns (e.g., `feature/*`)
2. **Directory** (25 points) - Working in specific directories (e.g., `src/`)
3. **ADHD State** (20 points) - Current energy/attention level
4. **Time Window** (15 points) - Time-of-day preferences
5. **File Patterns** (10 points) - Recently edited file types

**Confidence Levels:**
- **>85%**: Auto-suggest (high confidence)
- **65-85%**: Prompt with explanation (moderate)
- **<65%**: No suggestion (low confidence, manual choice)

**Example Suggestion:**
```
💡 Profile Suggestion
✅ Profile Match: developer (86% confidence)

Score Breakdown (86/100 points):
  git_branch      ██████░░░░░░░░░░░░░░  30.0
  directory       █████░░░░░░░░░░░░░░░  25.0
  adhd_state      ████░░░░░░░░░░░░░░░░  20.0
  file_patterns   ███░░░░░░░░░░░░░░░░░  11.0

Switch to 'developer' profile? [y/N/never]:
```

## Usage Analytics

Track your profile usage patterns:

```bash
dopemux profile stats --days 30
```

**Shows:**
- Total switches and daily average
- Most used profile
- Accuracy (% of switches lasting >30 min)
- Switch types (manual vs auto)
- Time-of-day heatmap
- Optimization suggestions

**Example:**
```
📊 Profile Usage Analytics (Last 30 days)

📈 Summary:
   Total switches: 45
   Per day (avg): 1.5
   Most used: developer
   Accuracy: 82%

⏰ Time-of-Day Heatmap:
   09:00  ████████████ 12
   14:00  ████████ 8

💡 Optimization Suggestions:
   • Stable workflow: Your 'developer' profile is well-matched!
```

## Configuration

### Auto-Detection Settings

Edit `.dopemux/profile-settings.yaml`:

```yaml
# ADHD-friendly auto-detection settings
enabled: true
check_interval_seconds: 300  # 5 minutes
confidence_threshold: 0.85   # 85% confidence required
debounce_minutes: 30         # Don't suggest same profile within 30 min
quiet_hours_start: '22:00'   # No suggestions 10pm-8am
quiet_hours_end: '08:00'
never_suggest: []            # Profiles to never suggest
```

**Adjust for your needs:**
- More suggestions? Lower `confidence_threshold` to 0.70
- Less frequent? Increase `check_interval_seconds` to 600 (10 min)
- Different quiet hours? Adjust start/end times

### Profile YAML Structure

Simple structure for custom profiles:

```yaml
name: my-custom
display_name: My Custom Workflow
description: Tailored for my specific needs

mcps:
  - serena-v2
  - conport
  - dope-context

adhd_config:
  energy_preference: medium    # low, medium, high
  attention_mode: focused      # focused, scattered
  session_duration: 25         # minutes

auto_detection:
  git_branches:
    - "feature/*"
  directories:
    - "src/"
  time_windows:
    - "09:00-12:00"  # Morning focus time
```

## Workflows

### Daily Development Flow

```bash
# Morning: Start with analysis
dopemux profile apply researcher

# Mid-day: Switch to implementation
dopemux profile apply developer

# Afternoon: Quick docs update
dopemux profile apply minimal
```

### Context-Aware Workflow

```bash
# Enable auto-detection
dopemux profile auto-enable

# Work normally - system suggests switches automatically
# Accept/decline/never as needed

# Check how you're using profiles
dopemux profile stats
```

## Troubleshooting

### Profile suggestions too frequent?

Increase debounce period:
```yaml
# .dopemux/profile-settings.yaml
debounce_minutes: 60  # Suggest max once per hour
```

### Wrong profile suggestions?

Check detection rules in your profile YAML:
```bash
dopemux profile show developer --raw
```

Adjust `auto_detection` rules to better match your patterns.

### Never want suggestions for a profile?

When prompted, choose "never":
```
Switch to 'full' profile? [y/N/never]: never
```

Or edit config directly:
```yaml
# .dopemux/profile-settings.yaml
never_suggest:
  - full
  - minimal
```

## Best Practices

**Create Profiles for Modes:**
- `focused` - Deep work, single task
- `exploring` - Learning, research, broad search
- `quick` - Fast edits, minimal tools

**Use Analytics:**
- Run `dopemux profile stats` weekly
- Adjust profiles based on actual usage
- Celebrate stable workflows!

**Energy Matching:**
- Low energy morning? Use `minimal`
- High energy afternoon? Use `full`
- Auto-detection can learn these patterns

## Tips

💡 **Start Simple**: Begin with `minimal` or `developer`, expand as needed

💡 **Iterate**: Profiles are easy to modify - adjust MCPs as you learn

💡 **Trust Analytics**: Usage stats reveal your actual patterns (not assumptions)

💡 **Use Auto-Detection**: Let the system help - it learns from your git history

---

**Need Help?** Run `dopemux profile --help` for command reference
