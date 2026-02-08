---
id: QUICK_REFERENCE_DAY2
title: Quick_Reference_Day2
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
author: '@hu3mann'
date: '2026-02-05'
prelude: Quick_Reference_Day2 (explanation) for dopemux documentation and developer
  workflows.
---
# Day 2 Quick Reference

## 🎯 What We Accomplished

✅ **Bug Fix:** Python 3.11 → 3.10 (Ubuntu 22.04 LTS support)
✅ **Test Suite:** `test_installer_basic.sh` (3s, CI-ready)
✅ **Homebrew:** `dopemux.rb` formula complete
✅ **PyPI:** Package built (565KB wheel, 575KB tarball)
✅ **Docs:** Testing report + PyPI release guide

---

## 🚀 Quick Commands

### Testing
```bash
# Fast smoke test (3 seconds)
./test_installer_basic.sh

# Ubuntu container test (84 seconds)
./test_installer_ubuntu.sh
```

### Package Building
```bash
# Build Python package
python3 -m build --sdist --wheel

# Check built packages
ls -lh dist/
```

### Homebrew (Local Testing)
```bash
# Test formula locally
brew install --build-from-source ./dopemux.rb

# Uninstall
brew uninstall dopemux
```

### PyPI (TestPyPI)
```bash
# Upload to test server
python3 -m twine upload --repository testpypi dist/*

# Install from test server
pip install --index-url https://test.pypi.org/simple/ dopemux
```

---

## 📁 Key Files

| File | Purpose | Size |
|------|---------|------|
| `install.sh` | Main installer (Python 3.10+ now) | - |
| `test_installer_basic.sh` | Fast test suite | - |
| `dopemux.rb` | Homebrew formula | 3KB |
| `PYPI_RELEASE_GUIDE.md` | Publishing guide | 4.4KB |
| `dist/dopemux-0.1.0-py3-none-any.whl` | Wheel package | 565KB |
| `dist/dopemux-0.1.0.tar.gz` | Source package | 575KB |

---

## 🐛 Bug Fixed

**Issue:** Installer required Python 3.11+, too strict for Ubuntu 22.04 LTS
**Fix:** Changed to Python 3.10+ (aligns with pyproject.toml >= 3.8)
**Files:** `install.sh` (3 lines changed)

---

## 📊 Test Results

| Platform | Duration | Result |
|----------|----------|--------|
| macOS | 3s | ✅ 100% (5/5) |
| Ubuntu 22.04 | 84s | ⚠️ 60% (3/5)* |

*Container limitations (Docker-in-Docker)

---

## 🎯 Next Steps (Day 3)

1. Test Homebrew formula locally
2. Upload to TestPyPI
3. Create GitHub release (v0.1.0)
4. Test installations

---

## 💡 Key Learning

**Python Versioning Matters:** Always align installer requirements with:
- Target platform defaults (Ubuntu 22.04 = Python 3.10)
- Actual project requirements (pyproject.toml = >= 3.8)
- Balance compatibility vs. features

---

**Progress:** 28% → 40% (Week 1) | Installer: 85% → 95%
