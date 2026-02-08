---
id: DEPENDABOT_SETUP
title: Dependabot_Setup
type: how-to
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Dependabot_Setup (how-to) for dopemux documentation and developer workflows.
---
# Dependabot Automated Dependency Updates

**Status**: Configured and ready to activate
**File**: `.github/dependabot.yml`
**ADHD-Optimized**: Prevents PR overwhelm with smart scheduling

---

## What This Does

Dependabot automatically:
1. Checks for dependency updates weekly
2. Creates PRs with changelogs and compatibility notes
3. Groups minor/patch updates to reduce noise
4. Prioritizes security updates

---

## Schedule (ADHD-Friendly)

**Monday 9am PT**: Python dependencies
- Root project (`requirements.txt`)
- dope-context, serena, activity-capture services

**Tuesday**: Python MCP servers
- zen-mcp, desktop-commander, exa-mcp

**Wednesday**: JavaScript/TypeScript
- frontend, backend apps

**Thursday**: GitHub Actions
- CI/CD workflow dependencies

**Why staggered?**: Prevents 20+ PRs on Monday morning causing analysis paralysis

---

## Configuration Highlights

### PR Limits (Prevents Overwhelm)
- Root Python: Max 5 concurrent PRs
- Services: Max 3 concurrent PRs each
- JavaScript: Max 5 concurrent PRs
- Actions: Max 3 concurrent PRs

**Total max**: ~30 PRs across entire week (not all at once)

### Update Grouping
**Python Minor/Patch Group**:
- Single PR for all minor/patch updates
- Example: `deps(python): Bump minor and patch dependencies`
- Contains: pytest 7.0.1→7.0.2, black 23.1→23.2, etc.

**JavaScript Minor/Patch Group**:
- Same strategy for npm packages
- Reduces 10 individual PRs → 1 grouped PR

### Security Updates
- **Always separate PRs** (never grouped)
- **Immediate notification** via GitHub
- **High priority labels** for easy filtering

---

## What to Expect

### Week 1 (Initial Run)
- **Many PRs**: Dependabot catches up on outdated dependencies
- **Action**: Review security updates first, merge in batches
- **Time**: 1-2 hours for initial cleanup

### Ongoing (Weekly)
- **Few PRs**: 3-8 PRs per week (most grouped)
- **Action**: Quick review on Monday/Wednesday
- **Time**: 15-30 minutes per week

---

## PR Review Workflow

### Security Updates (High Priority)
1. Check CVE details in PR description
2. Review changelog for breaking changes
3. Verify tests pass
4. **Merge immediately** if critical

### Grouped Updates (Normal Priority)
1. Scan PR for breaking changes
2. Check test results
3. Merge if all green
4. Rollback if issues found

### Major Updates (Low Priority)
1. Review migration guide
2. Test locally if needed
3. Schedule for dedicated time
4. Consider holding for batch upgrades

---

## ADHD-Friendly Features

### Visual Labels
- 🐍 `python` - Python packages
- 📦 `javascript` - npm packages
- 🔒 `security` - Security patches
- 🤖 `automated` - Auto-generated PR
- 🎯 `dependencies` - Dependency update

### Easy Filtering
GitHub search: `is:pr label:security label:dependencies`

### Batch Merging
Use GitHub CLI for bulk operations:
```bash
# Merge all passing dependency PRs
gh pr list --label dependencies --json number,title,statusCheckRollup | \
  jq -r '.[] | select(.statusCheckRollup[].conclusion == "SUCCESS") | .number' | \
  xargs -I {} gh pr merge {} --squash --auto
```

### Auto-Merge (Optional)
Enable in `.github/dependabot.yml` per package:
```yaml
# Auto-merge patch updates if tests pass
- package-ecosystem: "pip"
  directory: "/"
  # ... other config ...
  pull-request-branch-name:
    separator: "-"
```

Then: `gh pr merge --auto --squash` for trusted updates

---

## Activation

Once this PR is merged, Dependabot automatically activates. You'll see:

1. **First run**: Within 24 hours
2. **PRs created**: According to schedule
3. **Notifications**: Via GitHub notifications

No additional setup required! ✅

---

## Customization

Edit `.github/dependabot.yml` to adjust:
- **Schedule**: Change `day` or `time`
- **PR limits**: Adjust `open-pull-requests-limit`
- **Grouping**: Modify `groups` patterns
- **Reviewers**: Update `reviewers` list

Changes take effect on next scheduled run.

---

## Disabling (If Needed)

**Temporarily**:
- Pause in GitHub Settings → Code Security → Dependabot

**Permanently**:
- Delete `.github/dependabot.yml`

---

## Benefits

✅ **Security**: Automatic vulnerability patches
✅ **ADHD-Safe**: Controlled PR flow prevents overwhelm
✅ **Time-Saving**: Automated changelog and compatibility checks
✅ **Consistency**: Conventional commit messages
✅ **Visibility**: Clear labels and assignments

---

## Next Steps

After merge:
1. ✅ Configuration active automatically
2. 📅 Wait for Monday 9am PT (first Python run)
3. 📬 Review PRs as they arrive
4. 🔄 Establish weekly review routine (15-30 min)

---

**Estimated time savings**: 2-3 hours/month on manual dependency updates
