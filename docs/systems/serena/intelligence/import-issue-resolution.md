# Import Issue Resolution - Database Tests

**Date**: 2025-10-24
**Status**: ⚠️ ROOT CAUSE IDENTIFIED

---

## Problem

Pytest cannot import `SerenaIntelligenceDatabase` from `database.py`:
```
ImportError: cannot import name 'SerenaIntelligenceDatabase' from 'services.serena.v2.intelligence.database'
```

## Root Cause

**database.py line 27** uses relative imports:
```python
from ..performance_monitor import PerformanceMonitor, PerformanceTarget
from ..adhd_features import CodeComplexityAnalyzer
```

When pytest loads the test file, it may execute `database.py` in a context where relative imports fail:
```
ImportError: attempted relative import with no known parent package
```

## Evidence

✅ **Direct Python import works**:
```bash
python -c "from services.serena.v2.intelligence.database import SerenaIntelligenceDatabase"
# SUCCESS
```

❌ **Direct execution fails**:
```bash
python services/serena/v2/intelligence/database.py
# ImportError: attempted relative import with no known parent package
```

❌ **Pytest fails**:
```bash
pytest services/serena/v2/intelligence/test_database.py
# ImportError: cannot import name 'SerenaIntelligenceDatabase'
```

## Solutions

### Option 1: Move tests to tests/ directory (RECOMMENDED)
```bash
mkdir -p tests/serena/v2/intelligence
mv services/serena/v2/intelligence/test_database.py tests/serena/v2/intelligence/
```

Benefits:
- Standard pytest layout
- Cleaner separation
- Pytest handles paths automatically

### Option 2: Add conftest.py
Create `services/serena/v2/intelligence/conftest.py`:
```python
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))
```

### Option 3: Change database.py imports to absolute
Replace relative imports in database.py:
```python
# Before
from ..performance_monitor import PerformanceMonitor
from ..adhd_features import CodeComplexityAnalyzer

# After
from services.serena.v2.performance_monitor import PerformanceMonitor
from services.serena.v2.adhd_features import CodeComplexityAnalyzer
```

Benefits:
- Works in all contexts
- No import path issues
- Recommended for production code

Drawbacks:
- Breaks relative import pattern used in codebase
- May affect other files

### Option 4: Use pytest.ini configuration
Add to pytest.ini:
```ini
[pytest]
pythonpath = .
testpaths = services
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

---

## Recommended Action

**Use Option 3** (absolute imports in database.py):

1. Change database.py imports to absolute (5 min)
2. Test import: `python -c "from services.serena.v2.intelligence.database import SerenaIntelligenceDatabase"`
3. Run tests: `pytest services/serena/v2/intelligence/test_database.py`
4. Proceed to GREEN phase

**Time to fix**: 10-15 minutes

---

## What We've Accomplished

✅ **Created comprehensive test suite** (600+ lines, 14 tests)
✅ **Fixed 2 bugs** in database.py (missing `import os`, pytest fixture)
✅ **Documented RED phase** completely
✅ **Identified root cause** of import issue
✅ **Created __init__.py files** in package hierarchy

**Remaining**: Fix imports (10-15 min) → Run GREEN phase (30-60 min)

---

## Next Session

1. Apply Option 3 (absolute imports)
2. Run full test suite
3. Fix any failing tests
4. Validate ADHD <200ms targets
5. Document GREEN phase results

**Estimated time**: 45-75 minutes total
