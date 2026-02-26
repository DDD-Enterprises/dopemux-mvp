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

### Added
- Memory capture CLI commands (`dopemux memory rollup`)
  - `build` - Build global rollup index from project ledgers
  - `list` - List registered projects in global index
  - `search` - Search promoted work log entries across projects
- Comprehensive memory capture CLI reference documentation
- CLI interface section in Derived Memory Pipeline specification
- Repo Truth Extractor operator documentation
  - user guide and batch quickstart
  - CLI runbook cross-links

### Fixed
- Repo Truth Extractor routing defaults now use `gpt-5.2` / `gpt-5.2-pro` model IDs for OpenAI ladders.
- OpenAI GPT-5 requests omit custom temperature to avoid unsupported parameter errors.
- Webhook poller now uses the shared EventStore ledger interface (instead of removed legacy DB helpers) and writes idempotent normalized poll events.
- Webhook receiver and poller now accept `WEBHOOK_DB_URL` in compose, enabling explicit SQLite or Postgres ledger selection.
- Repo Truth Extractor Phase R async finalize now applies webhook migrations with the resolved DB URL and script fallback.
- Local runner fallback DB path for webhook ledger now avoids container-only `/data` defaults when running outside Docker.

### Planned
- Windows support (chocolatey package)
- GitHub Actions CI/CD pipeline
- Multi-Python version testing (3.8, 3.9, 3.10, 3.11, 3.12)
- Enhanced documentation
- Integration tests
- Performance optimizations

---

[0.1.0]: https://github.com/dopemux/dopemux-mvp/releases/tag/v0.1.0
