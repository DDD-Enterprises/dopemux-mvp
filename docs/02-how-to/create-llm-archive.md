---
title: Creating LLM-Friendly Repository Archives
category: how-to
tags:
- llm
- code-review
- auditing
- chatgpt
created: 2026-02-02
updated: 2026-02-02
date: 2026-02-02
author: Dopemux Team
id: create-llm-archive
type: how-to
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
prelude: >
  Create optimized ZIP archives of the dopemux-mvp repository for uploading to
  ChatGPT or other LLM services. Includes intelligent file filtering to produce
  ~40MB archives from 3,000+ source files with automatic manifest generation.
---
# Creating LLM-Friendly Repository Archives

This guide explains how to create optimized ZIP archives of the dopemux-mvp repository for uploading to ChatGPT or other LLM services for code auditing and analysis.

## Quick Start

```bash
# Create archive
./scripts/create_llm_archive.sh

# Result: dopemux-mvp-llm-YYYYMMDD-HHMMSS.zip (~40 MB)
```

## What Gets Included

The archive script intelligently includes:

✅ **Source Code**
- All Python files (`src/`, `services/`, `tests/`)
- Shell scripts
- Configuration files

✅ **Documentation**
- All Markdown files
- `docs/` directory (complete)
- `.claude/` agent configurations

✅ **Configuration**
- `pyproject.toml`, `requirements.txt`
- Docker configurations
- YAML/JSON config files

✅ **Infrastructure**
- Docker Compose files
- Dockerfiles
- MCP server configurations

## What Gets Excluded

The script automatically filters out:

❌ **Build Artifacts**
- `__pycache__/`, `*.pyc`
- `.mypy_cache/`, `.pytest_cache/`
- `htmlcov/`, coverage reports

❌ **Dependencies**
- `.venv/`, `node_modules/`
- Python packages, npm modules

❌ **Version Control**
- `.git/` directory
- Git worktrees

❌ **Large Files**
- Log files > 1MB
- Database files (`.db`, `.sqlite`)
- Pickle/model files

❌ **Secrets**
- `.env` files (except `.env.example`)
- API keys, credentials

❌ **IDE & Temp**
- `.vscode/`, `.idea/`
- Temporary directories
- Archive directories (`TRASH/`, `SYSTEM_ARCHIVE/`)

## Archive Contents

Each archive includes:

1. **ARCHIVE_MANIFEST.txt** - Complete manifest with:
- File listing (all 3,000+ files)
- Directory tree visualization
- Size analysis by category
- Archive metadata (commit hash, branch, timestamp)
- Usage instructions and LLM analysis suggestions

1. **All source and documentation files** - Everything needed for comprehensive code review

## Using with ChatGPT

### Upload Process

1. Open ChatGPT (web or desktop app)
1. Click the attachment/paperclip icon
1. Select your `dopemux-mvp-llm-*.zip` file
1. Wait for upload to complete (~30 seconds for 40MB)

### Example Prompts

**Security Audit**:
```
I've uploaded the dopemux-mvp codebase. Please:
1. Review for common security vulnerabilities
1. Check for exposed secrets or credentials
1. Analyze authentication/authorization patterns
1. Review input validation and sanitization
```

**Architecture Review**:
```
Review the architecture of this ADHD-optimized development platform.
Focus on:
- Three-plane architecture (PM, Cognitive, Coordination)
- Service communication patterns
- DopeconBridge integration
- Suggest improvements for scalability
```

**Code Quality Audit**:
```
Audit the code quality, focusing on:
- Type safety (Python typing, mypy compliance)
- Error handling patterns
- Test coverage
- Code organization and modularity
- Adherence to best practices
```

**Documentation Review**:
```
Review the documentation for:
- Completeness vs actual code
- Consistency across services
- Missing README files
- Outdated or incorrect information
- Suggestions for improvement
```

**ADHD Features Audit**:
```
This is an ADHD-optimized development platform. Review:
- Cognitive load management features
- Break suggestion algorithms
- Consent-first interaction patterns
- Energy/attention state tracking
- Suggest additional ADHD accommodations
```

## Verification

Before uploading, you can verify the archive contents:

```bash
# List all files
unzip -l dopemux-mvp-llm-*.zip

# Extract to temporary directory
unzip dopemux-mvp-llm-*.zip -d /tmp/verify

# View manifest
unzip -p dopemux-mvp-llm-*.zip ARCHIVE_MANIFEST.txt | less
```

## Archive Statistics

Typical archive metrics:
- **Files included**: ~3,077 files
- **Total scanned**: ~3,187 files
- **Inclusion rate**: 96.5%
- **Archive size**: ~40 MB
- **Compression ratio**: Excellent (64MB uncompressed → 40MB zipped)

## Limitations

### ChatGPT Limits
- File size limit: ~512 MB (archive is well under)
- Processing time: 30-60 seconds for initial load
- Context window: Archive is optimized to fit in modern LLM contexts

### What LLMs Can't Do
- **Run the code**: LLMs can analyze but not execute
- **Access external services**: Can't test API integrations
- **Real-time analysis**: Static code review only
- **Binary analysis**: No compiled code included

## Advanced Usage

### Custom Filters

Edit `scripts/create_llm_archive.sh` to customize:
- Include/exclude patterns
- File size limits
- Archive naming

### Multiple Archives

Create specialized archives for different purposes:

```bash
# Full archive (default)
./scripts/create_llm_archive.sh

# Could add flags in future:
# ./scripts/create_llm_archive.sh --minimal    # Docs only
# ./scripts/create_llm_archive.sh --services   # Services only
# ./scripts/create_llm_archive.sh --core       # Core library only
```

## Troubleshooting

### Archive Too Large

If the archive exceeds 100 MB:
1. Check for large log files that weren't excluded
1. Verify no large binaries are included
1. Review the exclude patterns in the script

### Missing Files

If expected files are missing:
1. Check if files are in `.gitignore` (script uses `git ls-files`)
1. Review exclude patterns in script
1. Verify files are committed to git

### Upload Fails

If ChatGPT rejects the upload:
1. Verify file size is under 512 MB
1. Try uploading via web interface instead of desktop app
1. Extract and re-zip if corruption suspected

## Best Practices

1. **Create fresh archives** before each major review session
1. **Include commit hash** in prompts for traceability
1. **Be specific** in your review requests
1. **Ask follow-up questions** to drill into findings
1. **Document findings** from LLM reviews in ConPort or issues

## Automation

### Scheduled Archives

Create archives before major releases:

```bash
# In CI/CD or pre-release workflow
./scripts/create_llm_archive.sh
# Upload to artifact storage or Google Drive
```

### Pre-commit Hook

Add to `.git/hooks/pre-push` for automatic archival:

```bash
#!/bin/bash
echo "Creating LLM archive for code review..."
./scripts/create_llm_archive.sh
```

## Related Documentation

- [Reference Overview](../03-reference/overview.md)
- [Security Guidelines](../03-reference/security.md)
- [Architecture Overview](../04-explanation/architecture/DOPEMUX_ARCHITECTURE_OVERVIEW.md)
- [ADHD Features API](../03-reference/adhd-engine-api.md)

## Script Reference

**Location**: `scripts/create_llm_archive.sh`

**Features**:
- Intelligent file filtering
- Automatic manifest generation
- Size optimization
- Timestamped archives
- Git-aware (uses `git ls-files`)

**Output**:
- Archive: `dopemux-mvp-llm-YYYYMMDD-HHMMSS.zip`
- Manifest: Included in archive as `ARCHIVE_MANIFEST.txt`
- Temp files: Auto-cleaned up

---

**Last Updated**: 2026-02-02
**Script Version**: 1.0
