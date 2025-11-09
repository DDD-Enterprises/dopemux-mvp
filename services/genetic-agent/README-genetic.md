# Genetic Agent: Advanced AI Code Repair with Genetic Programming

The Genetic Agent is the advanced version of the AI code repair system, using hybrid LLM + Genetic Programming (GP) for complex bugs and optimization challenges. It builds on the vanilla agent by adding evolutionary algorithms for exploring multiple solution variants and selecting the best fit.

## Overview

The Genetic Agent uses:
- **LLM (via Zen MCP)**: Initial repair generation and strategy planning.
- **Genetic Programming**: Evolves multiple repair variants, crossing over successful patterns and mutating for diversity.
- **MCP Tools**: Serena (code analysis), Dope-Context (patterns), ConPort (knowledge).

**Best For**: Complex bugs, performance optimization, legacy code refactoring where simple fixes aren't sufficient.

## Usage

### CLI Commands
```bash
# Basic repair with GP
dopemux genetic repair "performance bottleneck" --file slow_function.py

# Advanced optimization
dopemux genetic optimize "reduce memory usage" --file memory_hog.py --population 20

# Mode-specific
dopemux genetic repair "complex algorithm error" --strategy gp --generations 10
```

### Configuration
Edit `.env`:
```
GENETIC_AGENT_POPULATION_SIZE=15
GENETIC_AGENT_MAX_GENERATIONS=8
GENETIC_AGENT_CROSSOVER_RATE=0.8
GENETIC_AGENT_MUTATION_RATE=0.2
```

## Features

### Hybrid LLM + GP Approach
1. **Population Generation**: Zen LLM generates initial repair variants.
2. **Evolutionary Loop**: Crossover successful variants, mutate for diversity.
3. **Fitness Evaluation**: Serena analyzes code quality, performance impact.
4. **Selection**: Keep top 3 variants for final output.

### Optimization Capabilities
- **Performance Tuning**: Evolve multiple optimization strategies.
- **Memory Management**: GP variants for memory-efficient code.
- **Code Refactoring**: Generate alternative implementations.

### Integration
- **EventBus**: Real-time feedback to Dopemux orchestrator.
- **ConPort**: Logs GP patterns for future learning.
- **Docker**: Service in `docker-compose.master.yml`.

## Architecture

- **Generation**: Zen LLM creates initial population.
- **Evolution**: GP operators (crossover, mutation).
- **Evaluation**: Multi-objective fitness (correctness, performance).
- **Convergence**: Stop when best fitness ≥ threshold.

## Testing & Deployment

- **Test**: `pytest services/genetic-agent/tests/test_gp.py`.
- **Deploy**: `docker-compose -f docker-compose.master.yml up genetic-agent`.

For troubleshooting, check `docker logs dopemux-genetic-agent`.

---

# Vanilla Agent: Iterative LLM Code Assistant

The Vanilla Agent is the lightweight, fast version for quick fixes and bluesky development. It uses iterative LLM calls with MCP tools for analysis and learning, without the computational overhead of GP.

## Overview

The Vanilla Agent uses:
- **LLM (via Zen MCP)**: Iterative repair generation with confidence scoring.
- **MCP Tools**: Serena (analysis), Dope-Context (patterns), ConPort (logging).
- **Modes**: Repair, ideation, design, implementation, integration, testing, documentation.

**Best For**: Straightforward bugs, rapid prototyping, quick feature ideation.

## Usage

### CLI Commands
```bash
# Quick repair
dopemux code repair "undefined variable" --file script.py

# Bluesky development
dopemux code ideation "user dashboard"
dopemux code design "REST API"
dopemux code implement "JWT middleware"
dopemux code develop "full feature" --full-workflow
```

### Configuration
Edit `.env`:
```
VANILLA_AGENT_MAX_ITERATIONS=5
VANILLA_AGENT_CONFIDENCE_THRESHOLD=0.7
VANILLA_AGENT_DEVELOPMENT_MODE=repair
```

## Features

### Iterative Repair Loop
1. **Analysis**: Serena complexity + Dope-Context patterns.
2. **Generation**: Zen LLM (GPT-5-Codex) creates repair.
3. **Validation**: Confidence scoring and early exit.
4. **Learning**: Zen analyzes failures for next iteration.

### Bluesky Development Modes
- **Ideation**: Generate 3 ideas with feasibility scores.
- **Design**: Architecture roadmap and components.
- **Implementation**: Code gen with style preferences.
- **Integration**: Dependency resolution and merge plan.
- **Testing**: Pytest suite generation (80% coverage).
- **Documentation**: Mkdocs/Sphinx auto-generation.

### ADHD Optimization
- Progress bars for visual feedback.
- Early termination on high confidence.
- Short iterations to avoid waiting.

## Architecture

- **Mode Detection**: Keywords + Zen LLM for task classification.
- **Pipeline**: Linked phases with shared context (WorkflowContext).
- **Tool Calls**: Async MCP integration for research/planning.
- **Convergence**: Iterative refinement with learning.

## Testing & Deployment

- **Test**: `pytest services/genetic-agent/tests/test_vanilla.py`.
- **Deploy**: `docker-compose -f docker-compose.master.yml up genetic-agent`.

For troubleshooting, check `docker logs dopemux-genetic-agent`.

---

This documentation provides separate, clear guides for both agents, highlighting their strengths and usage in Dopemux. If you'd like HTML versions or additions, let me know! 🚀