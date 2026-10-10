# Runbooks - Operational Procedures

This directory contains operational runbooks for maintaining, troubleshooting, and operating Dopemux systems. These are **action-oriented** procedures for operational tasks.

## 📋 What are runbooks?
Runbooks are **operational procedures** that provide step-by-step instructions for system administration, maintenance, and incident response. They ensure consistent operational practices.

## 🧠 ADHD-Friendly Runbook Format
Our runbooks use clear, actionable formats optimized for stress situations:

```markdown
# [System/Service] - [Operation] Runbook

**Difficulty**: [Beginner | Intermediate | Advanced]
**Time Required**: [Estimated duration]
**Prerequisites**: [Required access/tools]
**Tags**: #category #urgency

## 🚨 When to Use This Runbook
Clear description of when this procedure applies.

## 🎯 Quick Summary
One-sentence description of what this accomplishes.

## ✅ Prerequisites
- [ ] Required tool/access 1
- [ ] Required tool/access 2
- [ ] Backup completed (if applicable)

## 🛠️ Step-by-Step Procedure

### Step 1: [Action Name]
**Purpose**: Why this step matters
**Command**: `specific command here`
**Expected Output**: What you should see
**Troubleshooting**: What to do if this fails

### Step 2: [Action Name]
[Continue pattern...]

## ✅ Verification
How to confirm the operation succeeded:
- [ ] Check 1
- [ ] Check 2
- [ ] Check 3

## 🔄 Rollback (if applicable)
Steps to undo changes if something goes wrong.

## 📞 Escalation
When to escalate and who to contact.

## 🔗 Related Runbooks
- Link to related procedures
```

## 📂 Runbook Categories

### System Administration (001-099)
- [RB-001: Dopemux Installation](001-dopemux-installation.md) - Fresh system setup
- [RB-002: System Health Check](002-system-health-check.md) - Regular maintenance
- [RB-003: Database Backup](003-database-backup.md) - Context data protection
- [RB-004: Log Analysis](004-log-analysis.md) - Troubleshooting guide
- [RB-005: Performance Tuning](005-performance-tuning.md) - Optimization procedures

### MCP Server Management (100-199)
- [RB-101: MCP Server Deployment](101-mcp-deployment.md) - Deploy new servers
- [RB-102: MCP Health Monitoring](102-mcp-health.md) - Server status checks
- [RB-103: MCP Server Updates](103-mcp-updates.md) - Version management
- [RB-104: MCP Troubleshooting](104-mcp-troubleshooting.md) - Common issues
- [RB-105: MCP Configuration Reset](105-mcp-config-reset.md) - Recovery procedures

### Context Management (200-299)
- [RB-201: Context Database Maintenance](201-context-maintenance.md) - DB optimization
- [RB-202: Session Recovery](202-session-recovery.md) - Restore lost sessions
- [RB-203: Context Data Migration](203-context-migration.md) - Move between systems
- [RB-204: Corruption Recovery](204-corruption-recovery.md) - Fix corrupted data
- [RB-205: Performance Optimization](205-context-performance.md) - Speed improvements

### Integration Management (300-399)
- [RB-301: Leantime Integration Setup](301-leantime-setup.md) - Project management sync
- [RB-302: Claude Code Configuration](302-claude-config.md) - AI integration setup
- [RB-303: Task-Master AI Deployment](303-task-master-deploy.md) - AI service setup
- [RB-304: API Key Rotation](304-api-key-rotation.md) - Security maintenance
- [RB-305: Health Monitoring Setup](305-health-setup.md) - System monitoring

### Incident Response (400-499)
- [RB-401: Service Outage Response](401-outage-response.md) - Emergency procedures
- [RB-402: Data Loss Recovery](402-data-recovery.md) - Backup restoration
- [RB-403: Security Incident Response](403-security-incident.md) - Breach procedures
- [RB-404: Performance Degradation](404-performance-issues.md) - Speed problems
- [RB-405: Configuration Rollback](405-config-rollback.md) - Undo changes

### User Support (500-599)
- [RB-501: User Account Recovery](501-account-recovery.md) - Help users regain access
- [RB-502: Context Restoration Help](502-context-help.md) - Session recovery support
- [RB-503: ADHD Feature Troubleshooting](503-adhd-troubleshooting.md) - Optimization issues
- [RB-504: Migration Assistance](504-migration-help.md) - Help users move systems
- [RB-505: Training & Onboarding](505-training.md) - New user support

### Development Operations (600-699)
- [RB-601: Release Deployment](601-release-deployment.md) - Version releases
- [RB-602: Environment Setup](602-environment-setup.md) - Development environments
- [RB-603: Testing Infrastructure](603-testing-infrastructure.md) - CI/CD maintenance
- [RB-604: Documentation Updates](604-docs-updates.md) - Keep docs current
- [RB-605: Code Quality Checks](605-quality-checks.md) - Standards enforcement

## 🚨 Emergency Runbooks

### Critical Issues (High Priority)
- [🔥 Service Down](emergency/service-down.md) - Complete outage
- [🔥 Data Corruption](emergency/data-corruption.md) - Context data issues
- [🔥 Security Breach](emergency/security-breach.md) - Unauthorized access
- [🔥 Resource Exhaustion](emergency/resource-exhaustion.md) - System overload

### Urgent Issues (Medium Priority)
- [⚡ Performance Degradation](urgent/performance-issues.md) - Slow response times
- [⚡ Integration Failures](urgent/integration-failures.md) - External service issues
- [⚡ Configuration Errors](urgent/config-errors.md) - Settings problems
- [⚡ MCP Server Issues](urgent/mcp-issues.md) - AI service problems

## 🎯 Runbook Quality Standards

### ADHD-Friendly Design
- ✅ **Clear steps** - One action per step
- ✅ **Expected outcomes** - What success looks like
- ✅ **Error handling** - What to do when things go wrong
- ✅ **Visual indicators** - Use symbols and formatting

### Operational Excellence
- 🔍 **Prerequisites clear** - What you need before starting
- ⏱️ **Time estimates** - How long each step takes
- ✅ **Verification steps** - Confirm success
- 🔄 **Rollback procedures** - How to undo if needed

### Stress-Friendly Format
- 🎯 **Quick summary** - Get oriented fast
- 🚨 **Emergency shortcuts** - Critical actions first
- 📞 **Escalation paths** - When to get help
- 🔗 **Related procedures** - Connect to other runbooks

## 🏷️ Runbook Tags

### Urgency Level
- `#critical` - Service-affecting issues
- `#urgent` - Performance/functionality issues
- `#routine` - Regular maintenance
- `#preventive` - Proactive procedures

### Difficulty Level
- `#beginner` - Basic operational tasks
- `#intermediate` - Requires some experience
- `#advanced` - Expert-level procedures

### System Categories
- `#dopemux` - Core platform operations
- `#mcp` - MCP server management
- `#context` - Context/session management
- `#integration` - External service operations
- `#security` - Security-related procedures

## 🔍 Finding Runbooks

### By Urgency
```bash
# Find emergency procedures
grep -r "#critical" docs/92-runbooks/

# Find routine maintenance
grep -r "#routine" docs/92-runbooks/
```

### By System
- **Core Platform**: RB-001 series
- **MCP Servers**: RB-100 series
- **Context Management**: RB-200 series
- **Integrations**: RB-300 series

### Quick Reference
- **[Emergency Index](quick-ref/emergency.md)** - Critical procedures
- **[Daily Tasks](quick-ref/daily.md)** - Routine operations
- **[Weekly Tasks](quick-ref/weekly.md)** - Regular maintenance
- **[Monthly Tasks](quick-ref/monthly.md)** - Periodic procedures

## 📚 Related Documentation
- **[How-To Guides](../02-how-to/)** - Problem-solving procedures
- **[Reference](../03-reference/)** - Technical specifications
- **[ADRs](../90-adr/)** - Why systems work this way
- **[Architecture](../94-architecture/)** - System design context

## 📝 Contributing Runbooks
1. **Real experience**: Base on actual operational needs
2. **Test thoroughly**: Verify each step works
3. **ADHD-friendly**: Follow stress-friendly format
4. **Keep updated**: Reflect current system state
5. **Link related**: Connect to other procedures

## 🧠 Using Runbooks Effectively
- **Read completely first** - Understand the full procedure
- **Check prerequisites** - Ensure you have everything needed
- **Follow exactly** - Don't skip or modify steps
- **Verify results** - Confirm each step succeeded
- **Document issues** - Note problems for improvement

---
*Runbooks ensure reliable operations and help maintain system health through consistent, ADHD-friendly procedures.*