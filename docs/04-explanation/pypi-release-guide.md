---
id: PYPI_RELEASE_GUIDE
title: Pypi_Release_Guide
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
author: '@hu3mann'
date: '2026-02-05'
prelude: Pypi_Release_Guide (explanation) for dopemux documentation and developer
  workflows.
---
# PyPI Package Release Guide

## Package Information

- **Package Name:** dopemux
- **Version:** 0.1.0
- **Built Artifacts:**
  - `dopemux-0.1.0-py3-none-any.whl` (565 KB)
  - `dopemux-0.1.0.tar.gz` (575 KB)
- **Build Date:** 2025-11-13
- **Python Support:** >= 3.8

## Build Status: ✅ SUCCESS

The package builds cleanly with no errors.

## Installation Methods

### From PyPI (after publishing)
```bash
pip install dopemux
```

### From Wheel (local testing)
```bash
pip install dist/dopemux-0.1.0-py3-none-any.whl
```

### From Source
```bash
pip install -e .
```

## Package Structure

```
dopemux-0.1.0/
├── dopemux/              # Main package
│   ├── cli.py            # CLI entry point
│   ├── adhd/             # ADHD optimizations
│   ├── claude/           # Claude integration
│   ├── claude_tools/     # Claude CLI tools
│   ├── embeddings/       # Vector embeddings
│   ├── mcp/              # MCP server management
│   ├── mobile/           # Mobile workflow support
│   ├── orchestrator/     # Task orchestration
│   └── ...
├── utils/                # Utility modules
├── core/                 # Core functionality
└── integrations/         # External integrations
```

## Entry Points

The package provides the following CLI command:
```bash
dopemux --help              # Show help
dopemux --version           # Show version
dopemux --quick             # Quick installation
dopemux --full              # Full installation
```

## Publishing to PyPI

### Prerequisites
1. Create account on [PyPI](https://pypi.org)
2. Create account on [TestPyPI](https://test.pypi.org) (for testing)
3. Generate API token: Account Settings → API Tokens

### Install Twine
```bash
pip install twine
```

### Test Upload (TestPyPI)
```bash
# Upload to TestPyPI
python3 -m twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ dopemux
```

### Production Upload
```bash
# Upload to PyPI (production)
python3 -m twine upload dist/*

# Verify
pip install dopemux
```

### Using API Token
Create `~/.pypirc`:
```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR-API-TOKEN

[testpypi]
username = __token__
password = pypi-YOUR-TESTPYPI-TOKEN
```

## Pre-Release Checklist

- [x] Package builds successfully
- [x] All dependencies listed in pyproject.toml
- [x] Entry points configured correctly
- [x] README.md exists and is informative
- [ ] Version number updated (currently 0.1.0)
- [ ] CHANGELOG.md updated
- [ ] Tests pass
- [ ] Documentation complete
- [ ] License file included
- [ ] GitHub repository tagged

## Post-Release Tasks

1. **Tag Release on GitHub**
   ```bash
   git tag -a v0.1.0 -m "Release version 0.1.0"
   git push origin v0.1.0
   ```

2. **Create GitHub Release**
   - Upload wheel and tarball as release artifacts
   - Add release notes from CHANGELOG

3. **Update Documentation**
   - Add PyPI badge to README
   - Update installation instructions

4. **Announce**
   - Share on relevant communities
   - Update project homepage

## Testing the Package

### Local Testing
```bash
# Create test virtualenv
python3 -m venv test-env
source test-env/bin/activate

# Install from wheel
pip install dist/dopemux-0.1.0-py3-none-any.whl

# Test CLI
dopemux --help
dopemux --verify

# Deactivate
deactivate
```

### Uninstall
```bash
pip uninstall dopemux
```

## Troubleshooting

### Build Errors
```bash
# Clean previous builds
rm -rf build/ dist/ src/*.egg-info

# Rebuild
python3 -m build --sdist --wheel
```

### Upload Errors
```bash
# Check package
python3 -m twine check dist/*

# Verbose upload
python3 -m twine upload --verbose dist/*
```

## Version Management

Current version: `0.1.0` (Alpha)

To bump version:
1. Update `pyproject.toml` → `version = "0.2.0"`
2. Update `src/dopemux/__version__.py`
3. Update `CHANGELOG.md`
4. Rebuild: `python3 -m build`
5. Tag: `git tag v0.2.0`

## Notes

- Package is currently in **Alpha** status (0.1.0)
- Suitable for testing and feedback
- Not recommended for production use yet
- Breaking changes may occur between versions

## Links

- **PyPI:** https://pypi.org/project/dopemux/ (after publishing)
- **GitHub:** https://github.com/dopemux/dopemux-mvp
- **Documentation:** https://docs.dopemux.dev
- **Issues:** https://github.com/dopemux/dopemux-mvp/issues
