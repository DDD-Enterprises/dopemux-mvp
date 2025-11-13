# Changelog

All notable changes to Dopemux will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-13

### Added
- Initial public alpha release
- Universal installer script with platform detection
- Support for macOS (Apple Silicon & Intel), Ubuntu 22.04+, Arch Linux, Fedora
- Fast test suite for CI/CD (`test_installer_basic.sh`)
- Homebrew formula for macOS installation
- PyPI package distribution (wheel + source)
- ADHD-optimized CLI with 40+ commands
- Multi-instance workspace support
- Claude Code integration
- MCP server management
- Document processing pipeline
- Profile management system
- Mobile workflow support
- Docker service orchestration

### Fixed
- Python version requirement (3.11 → 3.10) for Ubuntu 22.04 LTS compatibility
- IndentationError in cli.py (misplaced imports)
- Missing litellm dependency in package dependencies

### Changed
- Installer now requires Python 3.10+ (down from 3.11+)
- Updated help text to reflect Python 3.10+ requirement

### Documentation
- Comprehensive installer testing report
- PyPI release guide
- Platform-specific testing documentation
- Quick reference guides
- Session summaries (Days 1-3)

### Testing
- Validated on macOS (100% pass rate)
- Partial Ubuntu 22.04 container testing (60% pass rate)
- Clean virtualenv installation verified
- Twine PyPI compliance validation passed
- CLI functionality verified

### Package Details
- Package Size: 565 KB (wheel), 575 KB (source)
- Dependencies: 86 packages
- Python Support: >= 3.8 (tested on 3.10, 3.13)
- Entry Point: `dopemux` CLI command

### Known Limitations
- Docker-in-Docker testing not supported in containers
- Full functionality requires Docker daemon running
- Some features require system-level dependencies

## [Unreleased]

### Planned
- Windows support (chocolatey package)
- GitHub Actions CI/CD pipeline
- Multi-Python version testing (3.8, 3.9, 3.10, 3.11, 3.12)
- Enhanced documentation
- Integration tests
- Performance optimizations

---

[0.1.0]: https://github.com/dopemux/dopemux-mvp/releases/tag/v0.1.0
