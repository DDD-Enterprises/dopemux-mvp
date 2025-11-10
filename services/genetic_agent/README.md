# Vanilla Agent: AI-Powered Code Repair and Bluesky Development

The Vanilla Agent is now a full AI development partner integrated into Dopemux. It handles bug repairs and complete bluesky development workflows (ideation to documentation) using MCP tools (Zen for reasoning, GPT-Researcher for research, Serena for code analysis, Dope-Context for patterns, ConPort for knowledge).

## Quick Start

### Installation
```bash
cd services/genetic-agent
pip install -e .
dopemux mcp start-all  # Start MCP services
```

### Basic Usage
```bash
# Bug repair
dopemux code repair "undefined variable" --file script.py

# Bluesky development
dopemux code ideation "user authentication system"
dopemux code design "REST API for user management"
dopemux code implement "add JWT authentication middleware"
dopemux code develop "full feature" --full-workflow
```

## Architecture

The agent uses a phased pipeline with mode detection:

- **Mode Detection**: Keyword matching + LLM classification (repair vs. bluesky).
- **Iterative Loop**: Analyze ’ Generate (Zen LLM) ’ Validate (Serena) ’ Learn (ConPort).
- **Phases**: Ideation (brainstorming), Design (planning), Implementation (code gen), Integration (merging), Testing (validation), Documentation (handoff).

**Data Flow**:
```
User Task ’ Mode Detection ’ Phase Pipeline ’ MCP Tools ’ Output (Code/Docs/Plans)
```

## CLI Commands

### Core Commands
- `dopemux code repair "bug" --file file.py`: Iterative bug fix.
- `dopemux code status`: Agent status and MCP health.
- `dopemux code develop "feature" --full-workflow`: End-to-end development.

### Bluesky Modes
- `dopemux code ideation "new feature"`: Generate 3 ideas with feasibility/complexity ratings.
- `dopemux code design "REST API for users" --planning-steps 3`: Create roadmap and components.
- `dopemux code implement "add JWT middleware" --style modern`: Generate code.
- `dopemux code integrate "add new API to existing app" --strategy merge`: Resolve dependencies.
- `dopemux code test "user registration flow" --coverage 0.8`: Generate/run tests.
- `dopemux code docs "user authentication feature" --format markdown`: Auto-generate guides.

**Common Options**:
- `--verbose`: Detailed output.
- `--dry-run`: Preview without execution.
- `--config [file]`: Custom config (e.g., mode thresholds).

## MCP Integration

- **Zen**: Planning, failure analysis, LLM routing (GPT-5-Codex for code, GPT-5 for planning).
- **GPT-Researcher**: Market trends, similar features.
- **Serena**: Code analysis, dependency mapping.
- **Dope-Context**: Semantic search for patterns.
- **ConPort**: Knowledge logging, historical patterns.

## Libraries

- **tree-sitter**: Code parsing for analysis.
- **pytest-asyncio**: Async testing for validation.
- **mkdocs**: Builds docs in documentation mode.
- **tenacity**: Retries for MCP calls.
- **httpx**: Async HTTP for MCP tool calls.
- **black/mypy**: Formats and type-checks generated code.

**Install**: `pip install -r requirements.txt`.

## LLM Models (Via Zen MCP)

- **GPT-5 (OpenAI)**: Ideation and planning (creative brainstorming).
- **GPT-5-Codex (OpenAI)**: Implementation and code generation (precise coding).
- **Gemini 2.5 Pro (Google)**: Research and trend analysis in ideation.
- **Grok-4 (xAI)**: Testing and validation (technical accuracy).

**Selection Logic**: Zen routes based on phase (e.g., GPT-5-Codex for code).

## Configuration

Edit `.env` for custom thresholds:
```
GENETIC_AGENT_ZEN_URL=http://zen:3003
GENETIC_AGENT_GPTR_URL=http://gptr-mcp:3009
GENETIC_AGENT_CONFIDENCE_THRESHOLD=0.7
GENETIC_AGENT_RESEARCH_DEPTH=5
```

## Testing

### Unit Tests
- Run: `pytest services/genetic-agent/tests/`.
- Coverage: 80% target (pytest-cov).

### Integration Tests
- Mock MCP services to test end-to-end flows.

## Deployment

```bash
docker-compose -f docker-compose.master.yml up genetic-agent
```

Monitor: `docker logs dopemux-genetic-agent`.

## Workflow Example

**Command**: `dopemux code develop "build user dashboard" --full-workflow`

**Output**:
- **Ideation**: 3 ideas with scores.
- **Design**: Architecture roadmap.
- **Implementation**: Generated code.
- **Integration**: Merge plan.
- **Testing**: Test suite (pytest).
- **Documentation**: Markdown guide.

This agent transforms Dopemux into a complete AI development platform! =€