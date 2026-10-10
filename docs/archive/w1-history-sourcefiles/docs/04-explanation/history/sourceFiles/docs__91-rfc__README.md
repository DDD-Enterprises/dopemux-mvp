# Request for Comments (RFCs)

This directory contains Request for Comments (RFCs) for proposed features, changes, and improvements to Dopemux. RFCs enable community discussion before implementation.

## 📋 What are RFCs?
RFCs are **proposal documents** that describe new features or significant changes before implementation. They enable community feedback and help ensure thoughtful design decisions.

## 🧠 ADHD-Friendly RFC Format
Our RFCs use a clear, scannable format optimized for neurodivergent developers:

```markdown
# RFC-XXX: [Title]

**Status**: [Draft | Under Review | Accepted | Rejected | Implemented]
**Author**: @username
**Date**: YYYY-MM-DD
**Stakeholders**: @username, @username
**Tags**: #category #impact-level

## 🎯 Summary
One-sentence description of the proposal.

## 🎭 Motivation
Why is this needed? What problems does it solve?

## 🎪 Detailed Design
How will this work? Include:
- API changes
- User interface changes
- Implementation approach
- Examples

## 🔄 Alternatives Considered
What other approaches were considered and why were they rejected?

## 📊 Impact Assessment
### Users
- How will this affect end users?

### Developers
- How will this affect contributors?

### ADHD Accommodations
- How does this support neurodivergent users?

## 🛣️ Implementation Plan
1. Phase 1: ...
2. Phase 2: ...
3. Phase 3: ...

## ❓ Unresolved Questions
- Question 1?
- Question 2?

## 🔗 References
- Related ADRs
- External research
```

## 📂 Active RFCs

### Core Platform (001-099)
- [RFC-001: MCP Server Auto-Discovery](001-mcp-auto-discovery.md) - Automatic service detection
- [RFC-002: Plugin Architecture v2](002-plugin-architecture-v2.md) - Enhanced extension system
- [RFC-003: Multi-Project Workspace](003-multi-project-workspace.md) - Handle multiple projects

### ADHD Enhancements (100-199)
- [RFC-101: Biometric Attention Monitoring](101-biometric-monitoring.md) - Heart rate/eye tracking
- [RFC-102: Personalized Focus Patterns](102-personalized-patterns.md) - Learning individual rhythms
- [RFC-103: Collaborative Session Sharing](103-collaborative-sessions.md) - Pair programming support
- [RFC-104: Smart Break Scheduling](104-smart-breaks.md) - AI-driven break timing

### Integration Features (200-299)
- [RFC-201: VSCode Extension](201-vscode-extension.md) - Native editor integration
- [RFC-202: tmux Session Management](202-tmux-integration.md) - Terminal multiplexer support
- [RFC-203: GitHub Actions Integration](203-github-actions.md) - CI/CD workflow integration
- [RFC-204: Slack/Discord Notifications](204-chat-notifications.md) - Team communication

### Developer Experience (300-399)
- [RFC-301: Hot Reload Configuration](301-hot-reload-config.md) - Live config updates
- [RFC-302: Advanced Debugging Tools](302-debugging-tools.md) - Enhanced troubleshooting
- [RFC-303: Performance Profiling](303-performance-profiling.md) - Built-in profiling
- [RFC-304: Custom Theme System](304-custom-themes.md) - Visual customization

### Enterprise Features (400-499)
- [RFC-401: Team ADHD Profiles](401-team-profiles.md) - Organization-wide accommodations
- [RFC-402: Advanced Analytics](402-advanced-analytics.md) - Productivity insights
- [RFC-403: SSO Integration](403-sso-integration.md) - Enterprise authentication
- [RFC-404: Compliance Framework](404-compliance-framework.md) - Security standards

## 🔄 RFC Lifecycle

### Status Flow
```
Draft → Under Review → [Accepted|Rejected] → Implemented
  ↓                         ↓
Withdrawn              → Superseded
```

### Process Steps
1. **💡 Idea**: Discuss in issues or discussions first
2. **📝 Draft**: Create RFC with "Draft" status
3. **👥 Review**: Community feedback period (2 weeks minimum)
4. **🎯 Decision**: Maintainers accept, reject, or request changes
5. **🏗️ Implementation**: Update status when complete

## 🎯 RFC Quality Guidelines

### ADHD-Friendly Writing
- ✅ **Clear structure** - Use headings and lists
- ✅ **Concrete examples** - Show don't just tell
- ✅ **Visual breaks** - Avoid walls of text
- ✅ **Key takeaways** - Summarize main points

### Technical Depth
- 🔍 **Motivation clarity** - Why is this needed?
- 🏗️ **Implementation detail** - How will it work?
- ⚖️ **Tradeoff analysis** - What are the costs?
- 🎭 **User impact** - How does this affect users?

### ADHD Impact Assessment
Every RFC must address:
- How does this support neurodivergent users?
- Does it increase or decrease cognitive load?
- Will it preserve or disrupt context?
- How does it align with gentle UX principles?

## 🏷️ RFC Tags

### Impact Level
- `#critical` - Core platform changes
- `#major` - Significant new features
- `#minor` - Small improvements

### Category Tags
- `#adhd` - ADHD optimization features
- `#integration` - External service integration
- `#performance` - Speed and efficiency
- `#ux` - User experience improvements
- `#development` - Developer tools

### Implementation Tags
- `#breaking` - Breaking changes
- `#backwards-compatible` - Non-breaking changes
- `#experimental` - Experimental features

## 🔍 Finding RFCs

### By Status
```bash
# Find RFCs under review
grep -r "Status.*Under Review" docs/91-rfc/

# Find accepted but not implemented
grep -r "Status.*Accepted" docs/91-rfc/
```

### By Category
- **ADHD Features**: RFC-100 series
- **Integrations**: RFC-200 series
- **Developer Experience**: RFC-300 series
- **Enterprise**: RFC-400 series

## 💬 Participating in RFC Process

### Providing Feedback
- Comment on specific sections
- Suggest alternatives
- Share ADHD perspective
- Ask clarifying questions

### ADHD-Friendly Participation
- **No judgment**: All questions welcome
- **Flexible timing**: Respond when attention allows
- **Any format**: Bullet points, voice notes, rough ideas
- **Clear guidelines**: Specific feedback format provided

## 📚 Related Documentation
- **[ADRs](../90-adr/)** - Decided architectural choices
- **[Explanations](../04-explanation/)** - Understanding existing design
- **[Architecture](../94-architecture/)** - System design docs
- **[Runbooks](../92-runbooks/)** - Implementation procedures

## 📝 Contributing RFCs
1. **Check existing**: Search for similar proposals first
2. **Discuss first**: Use GitHub discussions for initial feedback
3. **Use template**: Follow the ADHD-friendly format above
4. **Start simple**: Focus on motivation and high-level design
5. **Iterate**: Expect multiple rounds of feedback

---
*RFCs help ensure thoughtful design decisions that support the ADHD developer community's needs.*