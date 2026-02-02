# Tools Context

> **TL;DR**: Development and operational tools. Well-documented, standalone, with clear CLI interfaces.

**Inherits**: Root context (MCP tools, Do/Don't rules)

---

## Purpose

Standalone tools for development and operations:
- Port auditing
- Health checking
- Code analysis
- Development utilities

---

## Key Tools

| Tool | Purpose |
|------|---------|
| `ports_health_audit.py` | Check service port health |

---

## Tool Standards

- **Standalone** - No complex dependencies
- **CLI interface** - argparse or click
- **Documentation** - Clear --help output
- **Exit codes** - 0 success, non-zero error

```python
#!/usr/bin/env python3
"""Tool description.

Usage:
    python tool.py --option value
"""
```
