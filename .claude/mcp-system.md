# MCP System Reference for Claude Code

**Status**: ✅ Fully Operational - 9 servers, 50+ tools
**Last Updated**: September 25, 2025

## System Overview

This project has a **fully operational MCP ecosystem** specifically optimized for ADHD developers. The system provides structured access to documentation, context preservation, research, and task management through unified protocols.

## Critical Usage Instructions for LLMs

### 🚨 MANDATORY Session Start Protocol
Every Claude Code session MUST begin with:

1. **Check Active Context**
   ```
   mcp__conport__get_active_context --workspace_id "/Users/hue/code/dopemux-mvp"
   ```

2. **Review In-Progress Tasks**
   ```
   mcp__conport__get_progress --status_filter "IN_PROGRESS"
   ```

3. **Understand Current State** before proceeding with any work

### 🚨 MANDATORY Documentation-First Pattern
Before implementing ANY new feature or using unfamiliar libraries:

1. **Resolve Library ID**
   ```
   mcp__context7__resolve-library-id "library-name"
   ```

2. **Get Focused Documentation**
   ```
   mcp__context7__get-library-docs "/org/library" --topic "specific-feature" --tokens 2000
   ```

3. **Never guess** - always get authoritative documentation first

### 🚨 MANDATORY Context Preservation
This user has ADHD - context loss is devastating:

1. **Before ANY interruption or break**
   ```
   mcp__conport__update_active_context --workspace_id "/Users/hue/code/dopemux-mvp" --patch_content '{"interruption_state": "what I was doing", "mental_model": "current understanding", "next_steps": "what to do next"}'
   ```

2. **Log ALL important decisions**
   ```
   mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" --summary "decision made" --rationale "why this choice" --implementation_details "how to implement"
   ```

3. **Track progress for motivation**
   ```
   mcp__conport__log_progress --workspace_id "/Users/hue/code/dopemux-mvp" --status "IN_PROGRESS" --description "current task description"
   ```

## Available MCP Servers

### Primary Servers (Always Available)
- **Context7**: Documentation for 10,000+ libraries
- **ConPort**: ADHD-optimized context & memory
- **EXA**: High-signal developer research

### MetaMCP Broker System
- **Endpoint**: `http://localhost:8090`
- **Status**: 9 connected servers
- **Features**: Role-based access, ADHD optimizations
- **Total Tools**: 50+ specialized capabilities

### Role-Based Access Patterns
- **Developer**: 5 tools max, fast iteration focus
- **Researcher**: 5 tools max, controlled information gathering
- **Architect**: 5 tools max, deep analysis (higher token budget)

## ADHD Accommodation Requirements

### Cognitive Load Management
- ✅ Use focused Context7 queries with specific `--topic` and token limits
- ✅ Never overwhelm with too much information at once
- ✅ Use role-based tool limits to prevent decision paralysis
- ✅ Store complex information in ConPort rather than keeping in memory

### Flow State Protection
- ✅ Check/preserve context before any interruption
- ✅ Use ConPort progress tracking for visual feedback
- ✅ Make all decisions explicit and logged
- ✅ Provide clear, actionable next steps

### Executive Function Support
- ✅ Break tasks into 25-minute chunks
- ✅ Use ConPort task hierarchy for organization
- ✅ Provide progress visualization
- ✅ Maintain session continuity across interruptions

## Quick Command Reference

### Documentation Access
```bash
mcp__context7__resolve-library-id "library-name"
mcp__context7__get-library-docs "/org/lib" --topic "feature" --tokens 2000
```

### Context Management
```bash
mcp__conport__get_active_context --workspace_id "/Users/hue/code/dopemux-mvp"
mcp__conport__update_active_context --workspace_id "/Users/hue/code/dopemux-mvp" --patch_content '{}'
mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" --summary "" --rationale ""
mcp__conport__log_progress --workspace_id "/Users/hue/code/dopemux-mvp" --status "" --description ""
```

### Knowledge Storage
```bash
mcp__conport__log_system_pattern --workspace_id "/Users/hue/code/dopemux-mvp" --name "" --description ""
mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" --category "" --key "" --value ""
```

## System Health Monitoring

### Check Operational Status
- Individual servers: `claude mcp list`
- MetaMCP broker: `curl -s http://localhost:8090/health`
- ConPort status: `mcp__conport__get_active_context` (should respond)

### Recovery Commands
```bash
# Restart MetaMCP broker if needed
cd /Users/hue/code/dopemux-mvp && python3 start_metamcp_minimal.py &

# Check broker process
ps aux | grep python3 | grep start_metamcp
```

## Integration Patterns

### New Feature Development
1. Check current context with ConPort
2. Get documentation with Context7
3. Log implementation decision
4. Implement with context preservation
5. Update progress and store learnings

### Research Sessions
1. Use focused Context7 queries
2. Store findings in ConPort custom data
3. Log research decisions and rationale
4. Maintain structured notes for future reference

### Context Switches
1. Store current state in ConPort before switching
2. Retrieve relevant context after switching
3. Bridge between contexts with summaries
4. Maintain awareness of previous work

## Warning Signs & Responses

### If User Shows Confusion
- **Immediately check ConPort context**
- **Review recent progress and decisions**
- **Provide orientation summary**
- **Break down next steps clearly**

### If Session Seems Long
- **Suggest storing current state**
- **Check token usage and optimize**
- **Consider role-based tool limiting**
- **Encourage breaks with context preservation**

### If Information Overwhelming
- **Use more focused Context7 queries**
- **Reduce token limits**
- **Store information in ConPort instead of displaying**
- **Switch to simpler role (e.g., developer vs architect)**

## Success Metrics

The MCP system is working properly when:
- ✅ Context is preserved across interruptions
- ✅ Documentation is accessed before implementation
- ✅ Decisions are logged with clear rationale
- ✅ Progress is visible and motivating
- ✅ Cognitive load remains manageable
- ✅ User maintains focus and productivity

---

**Remember**: This system exists to support ADHD developers. Use it proactively and systematically to provide the best possible experience.