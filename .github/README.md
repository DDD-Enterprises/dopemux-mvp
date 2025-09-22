# 🤖 Claude Code + GitHub Actions Setup Guide

## Overview
Your dopemux project now has AI-powered CI/CD with Claude Code! This setup provides ADHD-optimized security reviews and development workflows.

## 🎯 What You Get

### AI-Powered Security Reviews
- **Contextual Analysis**: Claude understands your memory/intelligence system code
- **ADHD-Friendly**: 25-minute focus sessions, gentle notifications
- **Custom Rules**: Tailored for Dopemux security concerns
- **False Positive Filtering**: Reduces noise in development environments

### ADHD-Optimized CI/CD
- **Progressive Disclosure**: See essential results first
- **Chunked Workflows**: Separate jobs prevent overwhelming feedback
- **Encouraging Tone**: Supportive language throughout
- **Quick Feedback**: Fast quality checks with detailed security analysis

## 🚀 Quick Setup (3 Steps)

### 1. Get Your Claude API Key
```bash
# Visit: https://console.anthropic.com/
# Create an API key with Claude and Claude Code permissions
```

### 2. Add to GitHub Secrets
```
Repository Settings → Secrets and variables → Actions
Add: CLAUDE_API_KEY = "your-api-key-here"
```

### 3. Enable Workflows
```bash
# Commit and push the new workflows
git add .github/
git commit -m "feat: Add Claude Code AI-powered CI/CD"
git push
```

## 🔧 Available Workflows

### `ci-complete.yml` (Recommended)
- **Code Quality**: Pre-commit checks, linting
- **Security Review**: AI-powered vulnerability analysis
- **Documentation**: Link checking for docs
- **ADHD Summary**: Gentle, encouraging results overview

### `security-review.yml` (Standalone)
- Dedicated security analysis workflow
- Can be triggered independently
- Detailed PR comments with findings

## ⚙️ Customization Options

### Security Scan Instructions (`.github/security-scan-instructions.txt`)
Edit this file to add custom security checks for:
- Memory system vulnerabilities
- MCP integration security
- ADHD feature protections

### False Positive Filtering (`.github/security-filtering-instructions.txt`)
Customize to reduce noise in your development environment:
- Exclude test files and docs from scans
- Accept patterns common in your codebase
- Filter development-only security warnings

### Timeout Settings
Adjust focus durations in workflow files:
```yaml
claudecode-timeout: "20"  # 20-minute analysis sessions
```

## 🎨 ADHD Optimizations

### Workflow Design
- **Separate Jobs**: Code quality → Security → Docs (prevent overwhelm)
- **Timeouts**: 10min quality, 25min security, 15min docs
- **Cancel Old Runs**: New pushes cancel outdated CI runs
- **Progressive Feedback**: Essential info first, details on request

### Communication Style
- ✅ **Positive reinforcement** for good practices
- 🎯 **Clear next steps** when issues found
- 💡 **Contextual guidance** throughout
- ⏰ **Time awareness** with session-based work

### Gentle Notifications
- Success: "Great work! Your code is secure!"
- Issues: "Some items to review - tackle them one at a time"
- Encouragement: "Remember: Progress over perfection"

## 🔍 Local Development

### /security-review Slash Command
Your Claude Code environment now has ADHD-optimized security reviews:
```bash
/security-review
```
- Analyzes pending changes
- ADHD-friendly output format
- Integrated with your Dopemux workflow

### Customization
Edit `.claude/commands/security-review.md` to:
- Adjust analysis focus areas
- Modify ADHD accommodations
- Add project-specific guidance

## 📊 Understanding Results

### Security Finding Levels
- 🔴 **HIGH**: Address immediately (workflow blocking)
- 🟡 **MEDIUM**: Fix this session if possible
- 🔵 **LOW**: Note for later review
- ✅ **INFO**: Best practices to consider

### CI Summary
The final job provides an ADHD-friendly overview:
- What's working well
- What needs attention (if anything)
- Suggested next steps
- Encouraging context

## 🛠️ Troubleshooting

### Missing API Key
```
Error: CLAUDE_API_KEY not found
```
→ Add the secret in repository settings

### Timeout Issues
```
Security analysis timed out
```
→ Increase `claudecode-timeout` in workflow files

### Too Many False Positives
```
False positives in findings
```
→ Edit `.github/security-filtering-instructions.txt`

## 💡 Best Practices

1. **Start Small**: Enable one workflow, add others gradually
2. **Customize Gradually**: Add custom rules as you learn what works
3. **Team Calibration**: Adjust filtering based on team feedback
4. **Break Integration**: Use with Dopemux's 25-minute sessions

## 🤝 Getting Help

- **Workflow Issues**: Check Actions tab in GitHub
- **Security Questions**: Review PR comments from Claude
- **Customization Help**: Edit the instruction files and test
- **Dopemux Integration**: Use `/dopemux help` for session management

---

**🎉 Happy coding!** Your ADHD-optimized AI development environment is ready.