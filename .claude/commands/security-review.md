# /security-review: ADHD-Optimized Security Analysis

> Analyzes your code changes for security vulnerabilities with ADHD-friendly reporting and focus duration awareness.

## Context
When you run `/security-review`, Claude analyzes all uncommitted changes and staged files for security issues. The analysis is optimized for ADHD developers with:
- 25-minute focus session timeouts
- Gentle, encouraging notifications
- Prioritized findings (high-impact first)
- Clear remediation guidance

## How it works
1. Identifies security vulnerabilities in your pending changes
2. Filters out false positives common in development environments
3. Prioritizes findings by impact on ADHD workflows
4. Provides actionable remediation steps
5. Suggests task chunking for security fixes

## Custom filtering for Dopemux
This command is tuned for memory/intelligence system security:
- Focuses on memory poisoning and context tampering
- Checks MCP integration security
- Validates ADHD feature implementations
- Filters development-environment noise

## Example usage
```
/security-review
```
*Runs full security analysis on your working directory changes*

## Output format
- 🔴 **HIGH**: Fix immediately (blocks workflow)
- 🟡 **MEDIUM**: Fix this session if possible
- 🔵 **LOW**: Note for later (won't disrupt flow)
- ✅ **INFO**: Good practices to consider

## ADHD accommodations
- **Break reminders**: Suggests breaks during complex analyses
- **Chunked results**: Groups findings by type and priority
- **Context preservation**: Maintains analysis state across sessions
- **Gentle guidance**: Encouraging language for security learning

## When to use
- Before committing memory system changes
- After adding new MCP integrations
- When implementing security features
- During code review preparation