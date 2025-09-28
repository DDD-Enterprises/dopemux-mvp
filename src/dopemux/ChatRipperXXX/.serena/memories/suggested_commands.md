# ChatX - Suggested Commands

## Installation Commands
```bash
# Install in development mode with all dependencies
pip install -e ".[dev]"

# Install with specific optional dependencies
pip install -e ".[llm]"        # LLM integration
pip install -e ".[local-llm]"   # Local LLM only
pip install -e ".[wave3]"       # Enhanced ML features
```

## Development Commands

### Code Quality
```bash
# Lint code (fast)
ruff check .
ruff format .

# Type checking
mypy src

# Run all quality checks
ruff check . && mypy src
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage reporting
pytest --cov=src/chatx --cov-report=term-missing

# Run with HTML coverage report
pytest --cov=src/chatx --cov-report=html

# Run specific test file
pytest tests/unit/test_specific.py

# Run performance tests (opt-in)
pytest -m perf
```

### Documentation
```bash
# Serve documentation locally
mkdocs serve

# Build documentation
mkdocs build
```

### Application Commands
```bash
# Main CLI entry point
chatx --help

# Extract iMessage data
chatx imessage pull --contact "+15551234567" --db ~/Library/Messages/chat.db --out ./out

# Extract Instagram DMs
chatx instagram pull --zip ./instagram.zip --user "Your Name" --out ./out

# Run full pipeline
chatx pipeline ~/Library/Messages/chat.db ./output --provider local
```

## Development Workflow
1. Make changes to code
2. Run `ruff check . && mypy src` for quality checks
3. Run `pytest` to ensure tests pass
4. Check coverage with `pytest --cov=src/chatx --cov-fail-under=60`