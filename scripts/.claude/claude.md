# Scripts Context

> **TL;DR**: Automation scripts with clear output and error handling. Organized by purpose. Use argparse, emit progress with emojis.

**Inherits**: Root context (MCP tools, Do/Don't rules)

---

## Script Organization

```
scripts/
├── deployment/        # Stack management
├── indexing/          # Code/doc indexing
├── testing/           # Validation scripts
├── monitoring/        # Health checks
├── docs_audit/        # Documentation auditing
├── maintenance/       # Cleanup, migrations
└── README.md          # Full organization guide
```

---

## Key Scripts

| Script | Purpose |
|--------|---------|
| `docs_validator.py` | Validate doc frontmatter |
| `docs_frontmatter_guard.py` | Fix frontmatter issues |
| `docs_normalize.py` | Normalize filenames |
| `deployment/start_stack.sh` | Launch Docker stack |

---

## Script Standards

### Python
```python
#!/usr/bin/env python3
import argparse, logging, sys

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="...")
    args = parser.parse_args()
    
    logger.info("🚀 Starting...")
    # logic
    logger.info("✅ Complete")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Bash
```bash
#!/bin/bash
set -euo pipefail

log_info() { echo "[INFO] $1"; }
log_success() { echo "✅ $1"; }
log_error() { echo "❌ $1" >&2; }
```

---

## ADHD Patterns

- **Progress bars** - Show `[████████░░] 80%`
- **Clear errors** - `❌ Error: [details] 💡 Suggestion`
- **Execution summary** - `✅ 5 passed, ❌ 1 failed, ⏱️ 12s`
- **Emoji status** - 🚀 🛑 ✅ ❌ ⚠️ 📊