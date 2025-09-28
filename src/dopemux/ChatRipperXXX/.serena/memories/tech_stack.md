# ChatX - Technology Stack

## Core Language & Runtime
- **Python 3.11+** (primary language)

## Core Python Dependencies
- **Pydantic >= 2.5.0** - Data validation and serialization
- **Click >= 8.1.0** - Command-line interface framework  
- **Rich >= 13.0.0** - Rich text and beautiful formatting
- **Typer >= 0.9.0** - Modern CLI framework built on Click
- **SQLAlchemy >= 2.0.0** - Database ORM and toolkit
- **python-dateutil >= 2.8.0** - Date/time parsing utilities
- **pathvalidate >= 3.0.0** - Path validation utilities
- **jsonschema >= 4.0.0** - JSON schema validation
- **Pillow >= 10.0.0** - Image processing

## Optional LLM Dependencies
- **OpenAI >= 1.0.0** - OpenAI API client
- **Anthropic >= 0.8.0** - Anthropic Claude API client  
- **ChromaDB >= 0.4.0** - Vector database for embeddings
- **Ollama >= 0.1.0** - Local LLM inference

## Wave3 Enhanced Dependencies  
- **sentence-transformers >= 2.2.2** - Sentence embeddings
- **torch >= 2.0.0** - PyTorch for ML
- **numpy >= 1.24.0** - Numerical computing
- **scikit-learn >= 1.3.0** - Machine learning library
- **httpx >= 0.25.0** - HTTP client
- **tenacity >= 8.2.0** - Retry utilities
- **neo4j >= 5.0.0** - Graph database

## Development Tools
- **pytest >= 7.0.0** - Testing framework
- **pytest-cov >= 4.0.0** - Coverage reporting
- **pytest-asyncio >= 0.21.0** - Async testing support
- **mypy >= 1.7.0** - Static type checker
- **ruff >= 0.1.6** - Fast Python linter and formatter
- **pre-commit >= 3.5.0** - Git hooks management
- **mkdocs-material >= 9.0.0** - Documentation generator
- **types-jsonschema >= 4.0.0** - Type stubs
- **pillow-heif >= 0.14.0** - HEIF image format support



## Build System
- **Hatchling** - Modern Python build backend
- **pyproject.toml** - Modern Python packaging standard