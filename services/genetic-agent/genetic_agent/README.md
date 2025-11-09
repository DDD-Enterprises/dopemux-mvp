# Genetic Coding Agent

A dual-agent system for automated code repair using both vanilla iterative approaches and genetic programming techniques.

## Overview

This project implements two complementary approaches to automated code repair:

1. **Vanilla Agent**: Traditional LLM-based iterative repair with MCP ecosystem integration
2. **Genetic Agent**: Advanced genetic programming approach for systematic code improvement

## Architecture

```
genetic_agent/
├── core/          # Shared agent infrastructure
├── vanilla/       # Vanilla agent implementation
├── genetic/       # Genetic agent implementation
├── shared/        # Common utilities and MCP integrations
└── tests/         # Comprehensive test suite
```

## Features

- **Dual Implementation**: Compare vanilla vs genetic approaches
- **MCP Integration**: Full Dopemux ecosystem support (ConPort, Serena, Dope-Context)
- **ADHD Optimization**: Progressive disclosure and session management
- **Safety Mechanisms**: Circuit breakers and human oversight
- **Performance Tracking**: Token usage and success rate metrics

## Quick Start

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run basic health check
python -m genetic_agent.core.agent
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy genetic_agent/

# Code formatting
black genetic_agent/
isort genetic_agent/
```

## Configuration

Copy `.env.example` to `.env` and configure:

- MCP service URLs
- Token limits and thresholds
- Genetic algorithm parameters

## License

Proprietary - Dopemux MVP