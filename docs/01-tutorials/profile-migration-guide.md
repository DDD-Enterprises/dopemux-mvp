---
id: PROFILE_MIGRATION_GUIDE
title: Profile_Migration_Guide
type: explanation
owner: '@hu3mann'
last_review: '2025-10-17'
next_review: '2026-01-15'
---
# Profile Migration Guide

**Welcome to Dopemux Profiles!** This guide will help you get started with personalized MCP configurations in just 2 minutes.

## Quick Start (2 minutes)

### Option A: Automated Profile Creation ⭐ Recommended

Let the wizard analyze your git history and create a personalized profile:

```bash
dopemux profile init
```

**What it does:**
1. 📊 Analyzes your last 90 days of commits
2. 🔍 Identifies your workflow patterns (branches, directories, work hours)
3. 💡 Suggests optimal MCP servers and ADHD settings
4. ✨ Creates a custom profile in `profiles/your-name.yaml`

**ADHD-Friendly:** Only 3 questions, smart defaults, takes < 2 minutes

### Option B: Use Existing Profiles

Choose from 5 pre-made profiles:

```bash
# See what's available
dopemux profile list

# View details
dopemux profile show developer

# Apply immediately
dopemux profile apply developer
```

**Available Profiles:**
- `minimal` - Lightweight (1 server: serena-v2)
- `developer` - Code focus (4 servers: serena, conport, dope-context, pal)
- `researcher` - Analysis (5 servers: + zen, gpt-researcher)
- `architect` - Design (5 servers: + zen, exa)
- `full` - Everything (9 servers: all MCP capabilities)

## Understanding Profiles

### What Are Profiles?

Profiles let you switch between different MCP server combinations instantly:

```
Working on docs?  → Apply 'minimal' (fast, focused)
Implementing code? → Apply 'developer' (LSP + search)
Deep analysis?    → Apply 'researcher' (+ reasoning)
System design?    → Apply 'architect' (+ consensus)
```

### ADHD Benefits

**Context Preservation:**
- Profiles matched to mental modes (focused vs exploring)
- Reduce decision fatigue (pre-configured sets)
- Quick switching without mental overhead

**Energy Matching:**
- Low energy → Minimal profile (fewer tools, less cognitive load)
- Medium energy → Developer profile (balanced capability)
- High energy → Researcher/Full profile (maximum power)

## Profile Wizard Workflow

### Step 1: Git History Analysis

The wizard analyzes your commits to understand:

```
📊 Analysis Results:
   • 50 commits in last 30 days
   • Top branches: feature/ (20), fix/ (15)
   • Common dirs: services (1604 changes), docker (488)
   • Peak hours: Morning (05:00-08:00)
   • Energy: High (avg 30 files/commit)

💡 Recommendations:
   • Session: 30 minutes (matches your intensity)
   • Energy: high (you work in large bursts)
   • MCPs: serena-v2, conport, dope-context, pal
```

### Step 2: Interactive Questions (3 only!)

**Question 1:** Profile name
```
Profile name: my-workflow
```

**Question 2:** MCP servers
```
MCP selection:
  [recommended] ← Based on your git history
  [minimal]     ← Lightweight
  [full]        ← Everything
  [custom]      ← Pick specific servers

Choice: recommended
```

**Question 3:** ADHD settings
```
Use suggested ADHD settings? (30 min, high energy) [Y/n]: y
```

### Step 3: Profile Created!

```
✅ Profile 'my-workflow' created successfully!

💡 Next steps:
   • Test it: dopemux profile show my-workflow
   • Apply it: dopemux profile apply my-workflow
```

## Manual Profile Creation

If you prefer to write YAML directly:

```yaml
# profiles/my-custom.yaml
name: my-custom
display_name: My Custom Profile
description: Tailored for my specific workflow

mcps:
  - serena-v2
  - conport
  - dope-context
  - pal

adhd_config:
  energy_preference: medium
  attention_mode: focused
  session_duration: 25

auto_detection:
  git_branches:
    - "feature/*"
    - "fix/*"
  directories:
    - "src/"
    - "services/"
```

**Validate before using:**
```bash
dopemux profile show my-custom  # Check it loads correctly
```

## Profile Management Commands

### List Profiles
```bash
dopemux profile list
dopemux profile list --profile-dir ~/.dopemux/profiles
```

### Show Profile Details
```bash
dopemux profile show developer
dopemux profile show researcher --raw  # Show raw YAML
```

### Apply Profile
```bash
dopemux profile apply developer
dopemux profile apply minimal --no-backup  # Skip backup
```

### Create New Profile
```bash
dopemux profile init               # Interactive wizard
dopemux profile init my-profile    # With name pre-filled
```

## Troubleshooting

### "No profiles found"
```bash
# Check profiles directory
dopemux profile list

# Create profiles/ directory
mkdir -p profiles

# Copy example profiles
cp ~/.dopemux/examples/*.yaml profiles/
```

### "Profile validation failed"
```bash
# Check YAML syntax
dopemux profile show my-profile --raw

# Validate against Claude config
dopemux profile show my-profile
```

### "Missing MCP servers"
The profile requires MCP servers not configured in Claude. Either:

**Option A:** Remove from profile
```yaml
# Edit profiles/my-profile.yaml
mcps:
  - serena-v2  # Keep only what you have
  - conport
```

**Option B:** Install missing MCPs
```bash
# Check what's configured
claude config list --verbose

# Add missing server (example)
claude mcp add zen npx -y zen-mcp
```

## Advanced: Auto-Detection

Profiles can auto-switch based on context:

```yaml
auto_detection:
  git_branches:
    - "feature/*"     # Auto-enable when on feature branches
    - "docs/*"

  directories:
    - "src/frontend"  # Auto-enable when in frontend dir

  file_patterns:
    - "*.test.ts"     # Auto-enable when editing tests

  time_windows:
    - "09:00-12:00"   # Auto-enable during focused morning hours
```

**Enable auto-detection:**
```bash
# Coming soon in Task 4.2
dopemux profile auto-enable
```

## Migration Checklist

- [ ] Run `dopemux profile init` to create personalized profile
- [ ] Test profile: `dopemux profile show my-profile`
- [ ] Apply profile: `dopemux profile apply my-profile`
- [ ] Verify MCPs loaded: Check Claude Code shows expected tools
- [ ] Create additional profiles for different modes (focused, research, etc.)
- [ ] (Optional) Set up auto-detection rules in profile YAML

## Next Steps

After creating your first profile:

1. **Try It Out:** Use Claude Code with the new profile
2. **Iterate:** Adjust MCP list if needed
3. **Create More:** Different profiles for different work modes
4. **Auto-Detection:** Set up auto-switching (coming in Task 4.2)

## Support

- 📖 Profile YAML Schema: `docs/PROFILE-YAML-SCHEMA.md`
- 🔧 Command Reference: `dopemux profile --help`
- 🐛 Issues: Report at GitHub

---

**ADHD-Friendly:** Clear steps, visual guides, gentle encouragement. You've got this! 🚀
