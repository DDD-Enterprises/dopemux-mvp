---
id: docs__LEANTIME_MCP_OFFICIAL_ANALYSIS
title: Docs  Leantime Mcp Official Analysis
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-13'
last_review: '2026-04-13'
next_review: '2026-07-12'
prelude: Docs  Leantime Mcp Official Analysis (explanation) for dopemux documentation
  and developer workflows.
---
# Leantime MCP Official Integration Analysis

**Date**: September 22, 2025
**Status**: Research Complete - Implementation Strategy Updated

## 🎯 Key Findings from Official Leantime MCP Documentation

### Official MCP Server vs Our Implementation

**Official Leantime MCP Server** (Beta)
- Commercial plugin available through Leantime Marketplace
- Requires license purchase and activation
- Built-in `/mcp` HTTP endpoint at `https://YOURLEANTIMEURL/mcp`
- Supports both STDIO and HTTP transport protocols
- Production-ready with security features

**Our Current Implementation**
- Custom Python bridge in `/src/integrations/leantime_bridge.py`
- Direct API integration using aiohttp
- Custom MCP server in `/src/integrations/leantime_mcp_server.js`
- ADHD-specific optimizations built-in

`★ Insight ─────────────────────────────────────`
The official MCP server provides a standardized approach, but our custom implementation offers unique ADHD optimizations that aren't available in the commercial version. We can leverage both approaches for maximum effectiveness.
`─────────────────────────────────────────────────`

## 🔧 Official MCP Tools Available

### Core Project Management Tools
1. **create_milestone** - Creates project milestones
2. **create_timesheet** - Time tracking functionality
3. **create_todo** - Task creation
4. **update_todo** - Task modification

### Event Triggers (Webhooks)
- new_todo, new_comment, new_goal, new_idea
- new_milestone, new_project, new_timesheet
- updated_* versions of all above

### Authentication Methods
1. **Personal Access Tokens** (Recommended)
   - More secure, user-specific permissions
   - Generated via Profile → Personal Access Tokens
2. **Standard API Keys**
   - Format: `lt_{username}_{hash}`
   - Legacy support, limited functionality

## 🧠 ADHD-Specific Integration Strategy

### What We Keep from Our Implementation
1. **Cognitive Load Tracking** - Not available in official MCP
2. **Attention State Management** - Custom ADHD feature
3. **Context Preservation** - Enhanced beyond standard features
4. **Break Frequency Management** - ADHD-specific timing
5. **Task Filtering by Mental State** - Unique to our implementation

### What We Adopt from Official Implementation
1. **Standardized MCP Protocol** - Better interoperability
2. **Security Best Practices** - Rate limiting, IP whitelisting
3. **Transport Protocol Support** - Both STDIO and HTTP
4. **Role-Based Access Control** - Enterprise security features

## 🎯 Enhanced Hybrid Integration Plan

### Phase 1: Dual Implementation Approach
```
Dopemux Leantime Integration
├── Official MCP Server (Commercial)
│   ├── Standard project management tools
│   ├── Real-time webhooks for updates
│   └── Enterprise security features
└── Custom ADHD Bridge (Our Implementation)
    ├── Cognitive load tracking
    ├── Attention state management
    ├── Context preservation
    └── ADHD workflow optimizations
```

### Phase 2: Configuration Strategy

#### Option A: Official MCP Only
- Purchase Leantime MCP Server license
- Use standard MCP tools with ADHD workflow layers
- Implement ADHD features as client-side logic

#### Option B: Custom Implementation Only
- Continue with our Python bridge
- Add standardized MCP protocol support
- Implement security features from official docs

#### Option C: Hybrid Approach (Recommended)
- Use official MCP for standard operations
- Custom bridge for ADHD-specific features
- Unified interface through Dopemux orchestration

## 🚀 Implementation Recommendations

### Immediate Actions
1. **Test Official MCP Server**
   - Try the commercial version for comparison
   - Evaluate performance and feature gaps

2. **Enhance Our Custom Implementation**
   - Add MCP protocol compliance
   - Implement security best practices
   - Add missing standard tools

3. **ADHD Feature Development**
   - Focus on cognitive load algorithms
   - Attention state detection
   - Context switching optimization

### Long-term Strategy

#### For Dopemux Users
```yaml
integration_options:
  basic:
    - Custom ADHD bridge only
    - Free and open source
    - Full ADHD optimizations

  professional:
    - Official MCP + ADHD bridge
    - Enterprise security
    - Real-time synchronization

  enterprise:
    - Full hybrid implementation
    - Advanced analytics
    - Team coordination features
```

## 🔐 Security Implementation

### From Official Documentation
```env
# Production Configuration
MCP_SERVER_ENABLED=true
MCP_SERVER_HOST=127.0.0.1  # Localhost only for security
MCP_SERVER_PORT=3001
MCP_TRANSPORT=http
MCP_LOG_REQUESTS=true  # For debugging
```

### Enhanced Security for ADHD Features
- Encrypted context storage
- Privacy-focused attention tracking
- Local-only cognitive data processing
- Secure session persistence

## 📊 Feature Comparison Matrix

| Feature | Official MCP | Our Implementation | Hybrid Approach |
|---------|-------------|-------------------|-----------------|
| Standard PM Tools | ✅ | ✅ | ✅ |
| Real-time Updates | ✅ | ❌ | ✅ |
| Enterprise Security | ✅ | ⚠️ | ✅ |
| ADHD Optimizations | ❌ | ✅ | ✅ |
| Cognitive Load Tracking | ❌ | ✅ | ✅ |
| Attention Management | ❌ | ✅ | ✅ |
| Context Preservation | ❌ | ✅ | ✅ |
| Cost | 💰 | Free | 💰 |
| Maintenance | Low | High | Medium |

## 🎯 Next Steps for Current Setup

### While You're Setting Up the Token

1. **Complete Basic Setup**
   - Generate Personal Access Token
   - Test our custom Python bridge
   - Verify ADHD features work

2. **Evaluate Official MCP**
   - Consider trial of commercial plugin
   - Compare feature sets
   - Assess integration complexity

3. **Enhanced Integration Planning**
   - Design hybrid architecture
   - Plan ADHD feature enhancement
   - Create deployment strategies

### Immediate Development Priorities

1. **MCP Protocol Compliance**
   - Update our server to match official standards
   - Add transport protocol support
   - Implement proper error handling

2. **Security Hardening**
   - Add rate limiting
   - Implement IP whitelisting
   - Enhance authentication

3. **ADHD Feature Enhancement**
   - Cognitive load algorithms
   - Attention state detection
   - Advanced context management

## 🧠 ADHD-Optimized Workflow Integration

### Human-AI Coordination Protocol
Based on official documentation, implement:

```markdown
## Task Management Rules
1. **AI agents ONLY claim unassigned "todo" tasks**
2. **Immediately label with "AI-Agent" to prevent conflicts**
3. **Update status to "in_progress" when starting**
4. **Document all changes in task comments**
5. **Mark "done" only when complete and tested**
```

### Enhanced for ADHD
```markdown
## ADHD-Specific Extensions
1. **Check cognitive load before task assignment**
2. **Verify attention state compatibility**
3. **Set appropriate break reminders**
4. **Preserve context for task switching**
5. **Update attention metrics on completion**
```

---

**Conclusion**: The official Leantime MCP server provides excellent standardization and enterprise features, but our custom ADHD implementations offer unique value. A hybrid approach leveraging both will provide the best outcome for Dopemux users.

**Recommendation**: Continue with our current setup while planning a hybrid integration that combines official MCP standards with our ADHD optimizations.