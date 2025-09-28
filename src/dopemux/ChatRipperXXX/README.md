# ChatX - Privacy-Focused Chat Analysis

ChatX is a privacy-focused, local-first CLI tool for forensic chat analysis. It extracts, transforms, and analyzes chat data from multiple platforms while maintaining strict privacy controls.

## Features

- **Multi-Platform Support**: iMessage, Instagram DM, WhatsApp, and text files
- **Privacy-First**: Local processing with optional cloud LLM integration only after redaction  
- **Differential Privacy**: (ε,δ)-DP statistical aggregation for safe cloud insights
- **Lossless Extraction**: Preserves original data fidelity via source metadata
- **Schema-Driven**: Well-defined JSON schemas for all data formats
- **Extensible Architecture**: Plugin-based extractors for new platforms

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/hue/Dopemux-ChatRipperXX.git
cd Dopemux-ChatRipperXX

# Install in development mode
pip install -e ".[dev]"
```

### Basic Usage

```bash
# Extract iMessage for a contact
chatx imessage pull --contact "+15551234567" --db ~/Library/Messages/chat.db --out ./out

# Extract iMessage from an iPhone backup (Finder/iTunes MobileSync)
chatx imessage pull --contact "+15551234567" --from-backup "~/Library/Application Support/MobileSync/Backup/<UDID>" --out ./out

# Extract Instagram DMs for a single user (required)
chatx instagram pull --zip ./instagram.zip --user "Your Name" --out ./out

# Audit iMessage DB for missing local attachments (report-only)
chatx imessage audit --db ~/Library/Messages/chat.db --out ./out

# Ingest PDF conversation export (text-first, OCR fallback)
chatx imessage pdf --pdf ./conversation.pdf --me "Your Name" --out ./out

# Run full pipeline with privacy redaction
chatx pipeline ~/Library/Messages/chat.db ./output --provider local

# Get help
chatx --help
```

## Architecture

ChatX follows a pipeline architecture:

1. **Extract**: Platform-specific extractors convert native formats to canonical JSON
2. **Transform**: Data transformation pipeline normalizes and validates messages  
3. **Redact**: Policy Shield removes sensitive information before any cloud processing
4. **Enrich**: Optional LLM processing adds semantic metadata
5. **Analyze**: Generate insights and reports from enriched data

## Privacy Principles

- **Local-First Processing**: All sensitive operations happen locally
- **Explicit Consent**: Cloud LLM integration requires explicit user consent
- **Redaction Transparency**: Detailed reports show what data was removed
- **Source Preservation**: Original data preserved in source_meta fields

## Supported Platforms

| Platform | Status | Data Source |
|----------|--------|-------------|
| iMessage | ✅ Complete | macOS chat.db SQLite database |
| Instagram DM | ✅ Initial extractor | Official data ZIP export |
| WhatsApp | 🚧 Planned | Text export files |
| Generic Text | 🚧 Planned | Plain text conversation files |

## Development

This project follows modern Python packaging standards with:

- **Package Management**: `pyproject.toml` with optional dependencies
- **Code Quality**: `ruff` for linting, `mypy` for type checking
- **Testing**: `pytest` with coverage reporting
- **Documentation**: `mkdocs` with material theme
- **CI/CD**: GitHub Actions for testing and docs deployment

### Project Structure

```
src/chatx/           # Main package
├── cli/            # Command-line interface
├── extractors/     # Platform-specific extractors  
├── schemas/        # Pydantic data models
├── transformers/   # Data transformation pipeline
├── redaction/      # Privacy redaction system
├── enrichment/     # LLM integration
└── utils/          # Common utilities

tests/              # Test suite
├── unit/           # Unit tests
├── integration/    # Integration tests  
└── fixtures/       # Test data

docs/               # Documentation
schemas/            # JSON Schema definitions
config/             # Configuration files
```

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=src/chatx --cov-report=html
```

### Documentation

Documentation is built with MkDocs and deployed automatically:

```bash
# Serve docs locally  
mkdocs serve

# Build docs
mkdocs build
```

## Contributing

1. Read the [Contributing Guide](docs/development/contributing.md)
2. Review the [Code of Conduct](docs/policy/code-of-conduct.md)
3. Check existing [Issues](https://github.com/hue/Dopemux-ChatRipperXX/issues)
4. Follow the development process in [CLAUDE.md](CLAUDE.md)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Security

This tool handles sensitive personal data. Please review the [Security Threat Model](docs/operations/security-threat-model.md), see our [Security & Vulnerability Reporting](docs/policy/security.md) guidance, and follow security best practices.
