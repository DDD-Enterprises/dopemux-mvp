# SYSTEM PROMPT\nMODE: Mechanical extractions unless explicitly marked ARBITRATION (GPT-5.2).
NO INTERPRETATION: No "purpose", "likely", "should", "means".
EVIDENCE REQUIRED: Every extracted item must include path + line_range.
OUTPUT: JSON only for scan phases. Markdown only for arbitration phases.
STABLE ORDER: Sort lists by path, then line_range[0], then id.
CHUNKING: If output would exceed context, emit PART files and a CAP_NOTICES file.

# Phase G2: Governance Merge + QA

Outputs:
- GOVERNANCE_RULES.json
- GOVERNANCE_QA.json
\n\n# USER CONTEXT\n\n--- FILE: /Users/hue/code/dopemux-mvp/.github/copilot-instructions.md ---\nThis repository is governed by .claude/PROJECT_INSTRUCTIONS.md.
Investigations and redesigns must follow .claude/PRIMER.md

# Dopemux Copilot Instructions (Repository Policy)

These instructions apply to all GitHub Copilot contributions in this repository.
Goal: produce deterministic, auditable changes that match Dopemux architecture and operator workflow.

## Quick Reference

### Build, Test, and Lint Commands

```bash
# Install dependencies
pip install -e .              # Production mode
pip install -e .[dev]         # Development mode with dev dependencies

# Testing
pytest tests/                 # All tests
pytest tests/ -m unit         # Unit tests only
pytest tests/ -m integration  # Integration tests only
pytest tests/ -m "not slow"   # Skip slow tests (fast feedback)
pytest tests/specific_test.py # Single test file
pytest tests/specific_test.py::test_name  # Single test

# Test coverage
pytest --cov=src/dopemux --cov-report=term-missing

# Quality checks
make lint                     # Run flake8
make format                   # Format with black + isort
make type-check               # Run mypy
make quality                  # All quality checks

# Docker stacks
docker-compose -f docker-compose.smoke.yml up    # Core services only
docker-compose -f docker-compose.master.yml up   # Full stack
docker compose config         # Validate compose file syntax

# Documentation validation
python scripts/docs_validator.py              # Validate frontmatter
python scripts/docs_frontmatter_guard.py --fix  # Auto-fix frontmatter
python scripts/docs_normalize.py --apply      # Normalize filenames
```

### Service Registry and Ports

All services are registered in `services/registry.yaml` with their ports and health endpoints:

- **postgres** (5432): PostgreSQL with AGE extension
- **redis** (6379): Caching and event streaming
- **qdrant** (6333): Vector database
- **dope-query** (3004): Knowledge g... [truncated for trace]