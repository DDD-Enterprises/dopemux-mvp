---
id: DEVELOPING_ZEN
title: Developing Zen MCP
type: how-to
owner: '@hu3mann'
date: '2026-02-02'
tags:
- zen
- mcp
- development
- contributing
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
prelude: Developing Zen MCP (how-to) for dopemux documentation and developer workflows.
---
# Developing Zen MCP - Contributor Guide

**Goal**: Improve Zen MCP tools (thinkdeep, planner, consensus, debug, codereview)
**Audience**: MCP contributors, AI reasoning enthusiasts
**Time**: 5-10 minutes to first contribution

---

## 🎯 What is Zen MCP?

Zen is Dopemux's multi-model reasoning MCP server. It provides:

- **zen/thinkdeep** - Multi-step investigation with hypothesis testing
- **zen/planner** - Interactive planning with revision support
- **zen/consensus** - Multi-model decision making (2-5 models)
- **zen/debug** - Systematic debugging with root cause analysis
- **zen/codereview** - Multi-domain code review
- **zen/challenge** - Critical thinking validation

**Model Support**: 70+ models via OpenAI, Gemini, Grok, Claude, OpenRouter

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Git
- API keys: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GROQ_API_KEY` (optional)

### Setup (5 minutes)

```bash
# 1. Fork dopemux-mvp on GitHub (Zen is currently embedded)

# 2. Clone to standard location
git clone https://github.com/YOUR_USER/dopemux-mvp.git ~/code/dopemux-mvp
cd ~/code/dopemux-mvp

# 3. Install in editable mode
pip install -e ".[dev]"

# 4. Install Zen dependencies
pip install anthropic openai groq

# 5. Verify dev mode detects Zen
dopemux dev status
# Should show: "zen: ~/code/dopemux-mvp ✅"
```

### First Contribution (Example: Improve thinkdeep)

```bash
# 1. Navigate to Zen tools
cd ~/code/dopemux-mvp/docker/mcp-servers/zen/zen-mcp-server/tools

# 2. Edit thinkdeep.py
nano thinkdeep.py
# Make your improvement (e.g., better confidence scoring)

# 3. Test immediately
cd ~/code/dopemux-mvp
dopemux restart

# 4. Test in Claude Code
# Use /zen:thinkdeep to verify your changes work

# 5. Commit and push
git checkout -b feature/improve-thinkdeep-confidence
git add docker/mcp-servers/zen/zen-mcp-server/tools/thinkdeep.py
git commit -m "feat(zen): improve confidence tracking in thinkdeep"
git push origin feature/improve-thinkdeep-confidence

# 6. Create Pull Request on GitHub
```

---

## 📂 Zen Architecture

### Directory Structure

```
docker/mcp-servers/zen/zen-mcp-server/
├── server.py              # MCP server entry point
├── tools/                 # Tool implementations
│   ├── thinkdeep.py      # Multi-step investigation
│   ├── planner.py        # Interactive planning
│   ├── consensus.py      # Multi-model decisions
│   ├── debug.py          # Systematic debugging
│   ├── codereview.py     # Code quality review
│   └── challenge.py      # Critical thinking
├── models/                # Model abstraction layer
│   ├── openai_client.py  # OpenAI integration
│   ├── anthropic_client.py # Claude integration
│   └── groq_client.py    # Groq integration
└── utils/                 # Shared utilities
    ├── confidence.py     # Confidence scoring
    └── formatting.py     # Output formatting
```

### Key Concepts

#### Tool Structure

Each Zen tool follows this pattern:

```python
# tools/example.py

from typing import Dict, Any

def run_tool(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool implementation.

    Args:
        params: Tool parameters from MCP call

    Returns:
        Tool response (success, data, or error)
    """
    # 1. Validate parameters
    # 2. Execute reasoning logic
    # 3. Format response
    # 4. Return with confidence score

    return {
        "success": True,
        "data": {...},
        "confidence": 0.85
    }
```

#### Model Abstraction

Zen uses a model abstraction layer:

```python
# Example model call
from models.openai_client import call_model

response = await call_model(
    model="gpt-5",
    messages=[...],
    temperature=0.7
)
```

#### Confidence Scoring

All tools should return confidence scores (0.0-1.0):

```python
confidence_levels = {
    "exploring": 0.0-0.2,    # Initial investigation
    "low": 0.2-0.4,          # Some evidence
    "medium": 0.4-0.6,       # Moderate confidence
    "high": 0.6-0.8,         # Strong evidence
    "very_high": 0.8-0.9,    # Very confident
    "almost_certain": 0.9-0.95,  # Near certainty
    "certain": 0.95-1.0      # Definitive
}
```

---

## 🛠️ Development Workflows

### Improving an Existing Tool

**Example: Enhance thinkdeep hypothesis tracking**

```bash
# 1. Read the tool code
cat docker/mcp-servers/zen/zen-mcp-server/tools/thinkdeep.py

# 2. Identify improvement area
# e.g., Better hypothesis validation logic

# 3. Make changes
nano docker/mcp-servers/zen/zen-mcp-server/tools/thinkdeep.py

# 4. Test locally
dopemux restart
# Test in Claude Code with /zen:thinkdeep

# 5. Add unit tests (if applicable)
nano tests/test_thinkdeep.py
pytest tests/test_thinkdeep.py -v

# 6. Commit with clear message
git commit -m "feat(zen): improve hypothesis validation in thinkdeep

- Add evidence strength scoring
- Track hypothesis genealogy
- Improve confidence updates

Closes #123"
```

### Adding a New Tool

**Example: Create a new "zen/analyze" tool**

```bash
# 1. Create tool file
nano docker/mcp-servers/zen/zen-mcp-server/tools/analyze.py

# 2. Implement tool (use existing tools as template)
# Follow the standard tool structure

# 3. Register tool in server.py
nano docker/mcp-servers/zen/zen-mcp-server/server.py
# Add tool to AVAILABLE_TOOLS dict

# 4. Test new tool
dopemux restart
# Test in Claude Code

# 5. Add documentation
nano docker/mcp-servers/zen/zen-mcp-server/README.md
# Document the new tool

# 6. Commit
git commit -m "feat(zen): add analyze tool for comprehensive analysis"
```

### Fixing a Bug

```bash
# 1. Reproduce bug
# Document steps in issue or commit message

# 2. Add failing test
nano tests/test_thinkdeep.py
# Write test that fails due to bug

# 3. Fix bug
nano docker/mcp-servers/zen/zen-mcp-server/tools/thinkdeep.py

# 4. Verify test passes
pytest tests/test_thinkdeep.py -v

# 5. Commit with issue reference
git commit -m "fix(zen): handle empty findings in thinkdeep

Previously thinkdeep crashed with empty findings list.
Now returns graceful error message.

Fixes #456"
```

---

## 🧪 Testing Your Changes

### Manual Testing in Claude Code

```bash
# 1. Start Dopemux with your changes
dopemux restart

# 2. Test tool in Claude Code
# Example thinkdeep test:
"""
Use zen/thinkdeep to investigate why authentication fails.

Step 1: Analyze authentication flow
Step 2: Check session management
Step 3: Verify token validation
"""

# 3. Verify:
# - Tool executes without errors
# - Results are accurate and helpful
# - Confidence scores make sense
# - Output is well-formatted
```

### Unit Testing

```bash
# Run all Zen tests
pytest tests/zen/ -v

# Run specific tool tests
pytest tests/zen/test_thinkdeep.py -v

# Run with coverage
pytest tests/zen/ --cov=docker/mcp-servers/zen --cov-report=html
```

### Integration Testing

```bash
# Test with multiple models
export OPENAI_API_KEY=your_key
export ANTHROPIC_API_KEY=your_key
export GROQ_API_KEY=your_key

# Run full integration test
pytest tests/integration/test_zen_integration.py -v
```

---

## 💡 Common Improvements

### 1. Improve Confidence Scoring

**Current**: Basic confidence levels
**Enhancement**: More granular, evidence-based scoring

```python
# Example improvement
def calculate_confidence(findings, contradictions):
    """Calculate confidence based on evidence quality."""
    base_confidence = len(findings) / 10  # More findings = higher confidence

    # Reduce for contradictions
    if contradictions:
        base_confidence *= (1 - (len(contradictions) / len(findings)))

    # Cap at 0.95 (never 100% certain)
    return min(base_confidence, 0.95)
```

### 2. Better Output Formatting

**Current**: Plain text responses
**Enhancement**: Rich markdown with structure

```python
def format_response(data):
    """Format tool response with markdown."""
    output = f"## {data['title']}\n\n"
    output += f"**Confidence**: {data['confidence']*100:.0f}%\n\n"

    for finding in data['findings']:
        output += f"- {finding}\n"

    return output
```

### 3. Enhanced Model Selection

**Current**: Single model per call
**Enhancement**: Automatic model fallback

```python
async def call_with_fallback(prompt, models=["gpt-5", "claude-sonnet-4.5"]):
    """Try models in order until one succeeds."""
    for model in models:
        try:
            return await call_model(model, prompt)
        except Exception as e:
            logger.warning(f"{model} failed: {e}")
            continue
    raise Exception("All models failed")
```

### 4. Add Caching

**Current**: No caching
**Enhancement**: Cache expensive model calls

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_analysis(query_hash):
    """Cache analysis results for duplicate queries."""
    return analyze(query)
```

---

## 📋 Code Style Guidelines

### Python Style

```python
# Use type hints
def process_findings(findings: List[str], confidence: float) -> Dict[str, Any]:
    """Process findings with confidence scoring."""
    pass

# Clear docstrings
"""
Tool for multi-step investigation.

Args:
    query: Investigation query
    max_steps: Maximum investigation steps (default: 5)

Returns:
    Dict with findings, confidence, and recommendations
"""

# Descriptive variable names
hypothesis_confidence = 0.8  # Not: conf = 0.8
evidence_list = []           # Not: ev = []
```

### Error Handling

```python
# Explicit error handling
try:
    result = await model_call(query)
except APIError as e:
    return {
        "success": False,
        "error": f"Model API error: {str(e)}",
        "recoverable": True
    }
except Exception as e:
    return {
        "success": False,
        "error": f"Unexpected error: {str(e)}",
        "recoverable": False
    }
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate log levels
logger.debug(f"Processing step {step_num}")     # Verbose details
logger.info(f"Completed analysis: {summary}")   # Important events
logger.warning(f"Low confidence: {confidence}") # Warnings
logger.error(f"Tool failed: {error}")           # Errors
```

---

## 🐛 Debugging Tips

### Enable Verbose Logging

```bash
# Set log level
export LOG_LEVEL=DEBUG
dopemux restart

# View logs
tail -f ~/.dopemux/logs/zen.log
```

### Test Individual Tools

```python
# Test tool directly (without MCP server)
cd docker/mcp-servers/zen/zen-mcp-server

python -c "
from tools.thinkdeep import run_tool

result = run_tool({
    'step': 'Initial investigation',
    'step_number': 1,
    'total_steps': 3
})

print(result)
"
```

### Use Model Playground

```python
# Test model calls directly
from models.openai_client import call_model
import asyncio

async def test():
    response = await call_model(
        model="gpt-5",
        messages=[{"role": "user", "content": "Test query"}]
    )
    print(response)

asyncio.run(test())
```

---

## 📚 Resources

### Documentation

- **[Zen/PAL Architecture Notes](../04-explanation/design-decisions/tier3-zen-enhanced-design.md)** - Historical Zen design and current migration context
- **[MCP Protocol Spec](https://spec.modelcontextprotocol.io/)** - MCP standard
- **[Development Setup](./DEVELOPMENT_SETUP.md)** - General dev mode guide

### Code References

- **[thinkdeep.py](../../docker/mcp-servers/pal/pal-mcp-server/tools/thinkdeep.py)** - Example tool implementation
- **[Model configs](../../docker/mcp-servers/pal/pal-mcp-server/conf/)** - PAL model configuration examples

### External Resources

- **[Anthropic Claude Docs](https://docs.anthropic.com/)** - Claude API reference
- **[OpenAI API Docs](https://platform.openai.com/docs/)** - OpenAI API reference
- **[Groq API Docs](https://console.groq.com/docs/)** - Groq API reference

---

## 🎯 Contribution Checklist

Before submitting a PR:

- [ ] Code follows style guidelines
- [ ] Tool returns proper confidence scores
- [ ] Error handling is explicit
- [ ] Logging is appropriate
- [ ] Manual testing completed
- [ ] Unit tests added/updated (if applicable)
- [ ] Documentation updated
- [ ] Commit message is clear and descriptive
- [ ] No API keys hardcoded
- [ ] Code works with dev mode

---

## 🚀 Roadmap & Future Work

### Planned Improvements

- **Hot Reload**: Auto-reload tools on file changes
- **Model Routing**: Intelligent model selection based on query
- **Caching Layer**: Cache expensive model calls
- **Parallel Execution**: Run multiple models simultaneously
- **Tool Chaining**: Connect tools for complex workflows

### Ideas for Contributors

- Improve confidence scoring algorithms
- Add new reasoning tools
- Enhance multi-model consensus
- Optimize model selection
- Add tool chaining support
- Improve output formatting
- Add visualization support

---

## 💬 Getting Help

- **Questions**: Open GitHub Issue with `question` label
- **Bugs**: Check [Troubleshooting](./development-troubleshooting.md) first
- **Feature Ideas**: Open GitHub Discussion
- **Stuck**: Review existing tool implementations as examples

---

**Happy Contributing!** 🎉

Every improvement to Zen helps developers think more deeply and solve problems more effectively. Your contributions make a real difference.
