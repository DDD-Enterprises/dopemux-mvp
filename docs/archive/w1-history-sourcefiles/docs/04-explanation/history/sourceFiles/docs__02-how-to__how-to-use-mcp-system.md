# How To: Use the MCP System for ADHD-Optimized Development
**Category**: `problem-oriented solution guides`
**Target Audience**: `practitioners`
**Cognitive Load**: `medium`
**ADHD Optimized**: ✅

**Last Updated**: 2025-09-24
**Estimated Reading Time**: 15 minutes
**Prerequisites**: MCP system operational (see status check)

---

## 🎯 What This Guide Covers

Learn how to effectively use the integrated MCP (Model Context Protocol) system for ADHD-optimized development workflows. This guide provides practical examples and cognitive load management strategies.

### Quick Navigation
- **5 minutes**: [Status Check](#quick-status-check) + [Essential Tools](#essential-tools-overview)
- **15 minutes**: Complete workflow examples
- **25 minutes**: Advanced patterns and optimization

---

## ⚡ Quick Status Check

Before starting, verify your MCP system is operational:

```bash
claude mcp list
```

**Expected Result**: ✅ Connected status for:
- `context7` - Documentation access
- `zen` - Multi-model reasoning
- `exa` - Development tools

**If any show ❌**: See [troubleshooting runbook](../92-runbooks/runbook-mcp-system-integration.md)

---

## 🛠️ Essential Tools Overview

### 📚 Context7 - Your Documentation Assistant
**When to Use**: Before writing any code, when learning new libraries
**Cognitive Benefit**: Reduces documentation hunting, focused results
**Token Savings**: ~80% vs manual search

```python
# Find the right library
mcp__context7__resolve_library_id(libraryName="fastapi")

# Get focused documentation
mcp__context7__get_library_docs(
    context7CompatibleLibraryID="/tiangolo/fastapi",
    topic="authentication"
)
```

### 🧠 Zen-MCP - Your Reasoning Partner
**When to Use**: Complex problems, architectural decisions, debugging
**Cognitive Benefit**: Breaks down overwhelming problems
**Models Available**: 46 (Gemini, OpenAI, OpenRouter)

```python
# Get system status
mcp__zen__version()

# Deep problem analysis
mcp__zen__thinkdeep(
    step="Analyze why my FastAPI auth isn't working",
    model="gemini-2.5-pro",
    confidence="medium"
)
```

### 🔧 EXA - Your Testing & Utility Toolkit
**When to Use**: Testing connections, quick calculations, demonstrations
**Cognitive Benefit**: Single interface for multiple needs
**Response Time**: < 1 second

```python
# Test MCP connectivity
mcp__exa__echo(message="MCP system working!")

# Quick calculations
mcp__exa__add(a=25, b=17)

# Monitor long operations
mcp__exa__longRunningOperation(duration=10, steps=5)
```

---

## 🎯 ADHD-Optimized Workflows

### 💡 Developer Workflow (Focus Mode)
**Best For**: Implementation, bug fixes, daily coding
**Time Box**: 25 minutes maximum
**Token Budget**: Conservative (< 1000 tokens per session)

#### Step 1: Start with Context7 (2 minutes)
```python
# Always start with documentation
mcp__context7__resolve_library_id(libraryName="your_library")
```
**Why**: Prevents going down rabbit holes, establishes context

#### Step 2: Use EXA for Testing (1 minute)
```python
# Verify your environment
mcp__exa__echo(message="Ready to code!")
```
**Why**: Quick confidence boost, confirms tools are working

#### Step 3: Code Implementation (20 minutes)
- Use Context7 docs as reference
- Stay within your 25-minute time box
- Take notes on decisions made

#### Step 4: Quick Validation (2 minutes)
```python
# Test your changes
mcp__exa__add(a=your_test_value, b=expected_result)
```

### 🔍 Research Workflow (Learning Mode)
**Best For**: New technology exploration, requirements gathering
**Time Box**: 50 minutes (2 × 25-minute sessions)
**Token Budget**: Moderate (< 2000 tokens per session)

#### Session 1: Discovery (25 minutes)
```python
# Find relevant libraries
mcp__context7__resolve_library_id(libraryName="machine_learning")

# Get overview documentation
mcp__context7__get_library_docs(
    context7CompatibleLibraryID="/tensorflow/tensorflow",
    topic="getting_started"
)
```

**🎯 ADHD Tip**: Set a timer! Stop at 25 minutes even if not "done"

#### Break (5 minutes)
Stand up, hydrate, brief walk

#### Session 2: Deep Dive (25 minutes)
```python
# Analyze specific concepts
mcp__zen__thinkdeep(
    step="Compare TensorFlow vs PyTorch for my use case",
    model="gemini-2.5-flash",
    confidence="medium"
)
```

### 🏗️ Architecture Workflow (Design Mode)
**Best For**: System design, major refactoring, technical decisions
**Time Box**: Extended sessions with breaks
**Token Budget**: Higher (< 5000 tokens per session)

#### Pattern: Problem → Research → Analysis → Decision

```python
# Step 1: Define the problem clearly
problem = "Need to choose between microservices vs monolith"

# Step 2: Research current best practices
mcp__context7__resolve_library_id(libraryName="microservices")

# Step 3: Deep architectural analysis
mcp__zen__thinkdeep(
    step=f"Architectural analysis: {problem}",
    model="o3-mini",  # Use reasoning model for architecture
    confidence="high"
)

# Step 4: Validate understanding
mcp__zen__version()  # Confirm model capabilities
```

---

## 💊 Token Optimization Strategies

### 🎯 Smart Tool Selection

#### Use Context7 First (Always)
```python
# ❌ Don't start with expensive reasoning
mcp__zen__thinkdeep(step="How do I use FastAPI?")

# ✅ Start with focused documentation
mcp__context7__resolve_library_id(libraryName="fastapi")
# THEN use reasoning if needed
```
**Savings**: ~1500 tokens per query

#### Choose Right Model for Task
```python
# ✅ For quick questions
mcp__zen__version()  # Free status check

# ✅ For deep analysis
mcp__zen__thinkdeep(model="gemini-2.5-flash")  # Fast model

# ✅ For complex reasoning
mcp__zen__thinkdeep(model="o3-mini")  # Reasoning model

# ❌ Don't use expensive models for simple tasks
mcp__zen__thinkdeep(model="o3-pro", step="What is 2+2?")
```

#### Batch Related Queries
```python
# ❌ Don't make separate calls
result1 = mcp__context7__get_library_docs(lib1)
result2 = mcp__context7__get_library_docs(lib2)
result3 = mcp__context7__get_library_docs(lib3)

# ✅ Use focused queries and build on results
libs = mcp__context7__resolve_library_id(libraryName="web_frameworks")
# Then pick the most relevant one
```

### 🧠 Cognitive Load Management

#### The 3-2-1 Rule
- **3 options maximum**: Never present more than 3 choices
- **2 minute rule**: If stuck for 2 minutes, use MCP tools
- **1 focus**: One problem at a time, use time boxing

#### Progressive Disclosure Pattern
```python
# ✅ Start broad
overview = mcp__context7__resolve_library_id(libraryName="react")

# ✅ Then narrow down
details = mcp__context7__get_library_docs(
    context7CompatibleLibraryID="/facebook/react",
    topic="hooks"
)

# ✅ Finally analyze if needed
analysis = mcp__zen__thinkdeep(
    step="Best practices for React hooks in my specific use case"
)
```

---

## 🔧 Common Use Cases

### 🐛 Debugging Session
```python
# 1. Describe the problem clearly
problem = "Authentication failing with 401 error"

# 2. Get relevant documentation
auth_docs = mcp__context7__resolve_library_id(libraryName="authentication")

# 3. Deep debug analysis
debug_help = mcp__zen__debug(
    step=f"Debug: {problem}",
    model="gemini-2.5-pro",
    files_checked=["auth.py", "config.py"]
)

# 4. Test potential solutions
test_result = mcp__exa__echo(message="Testing auth fix...")
```

### 📖 Learning New Technology
```python
# 1. Overview first
tech_options = mcp__context7__resolve_library_id(libraryName="web_scraping")

# 2. Pick the best option based on trust score
best_lib = mcp__context7__get_library_docs(
    context7CompatibleLibraryID="/scrapy/scrapy",  # Highest rated
    topic="tutorial"
)

# 3. Understand concepts deeply
understanding = mcp__zen__thinkdeep(
    step="Explain web scraping best practices for beginners",
    model="gemini-2.5-flash"
)
```

### 🚀 API Integration
```python
# 1. Find the official library
api_lib = mcp__context7__resolve_library_id(libraryName="stripe_api")

# 2. Get integration documentation
integration_guide = mcp__context7__get_library_docs(
    context7CompatibleLibraryID="/stripe/stripe-python",
    topic="payments"
)

# 3. Test connection
connection_test = mcp__exa__echo(message="Stripe API integration ready")
```

---

## ⚠️ When Things Go Wrong

### Tool Not Responding
```python
# Quick diagnostic
system_status = mcp__zen__version()
connectivity_test = mcp__exa__echo(message="health check")
```

**If both fail**: Check [runbook](../92-runbooks/runbook-mcp-system-integration.md)

### Unexpected Results
```python
# Verify your query format
test_query = mcp__context7__resolve_library_id(libraryName="test")

# If working, your original query may need adjustment
# Check documentation for proper parameter names
```

### Rate Limiting / Token Issues
```python
# Use free status check
status = mcp__zen__version()

# Switch to lighter operations
quick_test = mcp__exa__add(a=1, b=1)

# Wait before using expensive reasoning tools
```

---

## 🎯 ADHD Success Tips

### ⏰ Time Management
- **Set timers**: Use 25-minute Pomodoro sessions
- **Break at timer**: Even if you're in flow state
- **Record decisions**: Write down what you learned
- **Use bookmarks**: Save Context7 library IDs for reuse

### 🧠 Working Memory Support
```python
# Save important library IDs
useful_libs = {
    "web_framework": "/flask/flask",
    "database": "/sqlalchemy/sqlalchemy",
    "testing": "/pytest-dev/pytest"
}

# Use consistent patterns
status = mcp__zen__version()  # Always start sessions this way
test = mcp__exa__echo(message="session ready")  # Confirm tools working
```

### 🎨 Visual Organization
- Use emoji in your messages for quick scanning: 🔍📊🐛✅
- Keep successful queries in a "patterns" file
- Use Context7 trust scores to prioritize options

### 💡 Executive Function Support
- **One goal per session**: Don't try to solve multiple problems
- **Clear exit criteria**: Define "done" before starting
- **Celebrate completions**: Use EXA echo to mark success!

```python
# Mark session completion
mcp__exa__echo(message="🎉 Authentication debugging complete!")
```

---

## 📚 Next Steps

### If This Worked Well
- Read: [Token optimization strategies](../03-reference/TOKEN_OPTIMIZATION_STRATEGIES.md)
- Try: [Advanced MCP patterns](../04-explanation/mcp-ecosystem.md)
- Configure: [ADHD-specific settings](../02-how-to/adhd-configuration.md)

### If You Had Issues
- Check: [MCP troubleshooting runbook](../92-runbooks/runbook-mcp-system-integration.md)
- Review: [System integration status](../03-reference/MCP_SYSTEM_INTEGRATION_STATUS.md)
- Ask: Contact support with specific error messages

### For Advanced Usage
- Explore: [Role-based tool access](../04-explanation/features/mcp-role-system.md)
- Configure: [MetaMCP broker setup](../03-reference/METAMCP_INTEGRATION_GUIDE.md)
- Optimize: [Performance tuning guide](../02-how-to/performance-issues.md)

---

## 📋 Quick Reference Card

### Essential Commands
```python
# Status check
mcp__zen__version()

# Documentation search
mcp__context7__resolve_library_id(libraryName="your_topic")

# Get specific docs
mcp__context7__get_library_docs(context7CompatibleLibraryID="/org/project")

# Deep analysis
mcp__zen__thinkdeep(step="your_question", model="gemini-2.5-flash")

# Testing & validation
mcp__exa__echo(message="test_message")
```

### Troubleshooting
```bash
# Check MCP system
claude mcp list

# Test individual server
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize"}' | python3 server.py
```

---

## 🏷️ Document Metadata

**Document Type**: How-To Guide
**Diátaxis Category**: How-to (problem-oriented)
**ADHD Compliance**: ✅ Time-boxed, visual indicators, clear actions
**Maintenance**: Updated with new MCP features
**Review Cycle**: Bi-weekly
**Owner**: Developer Experience Team

**Tags**: `mcp-usage`, `adhd-workflow`, `developer-guide`, `how-to`