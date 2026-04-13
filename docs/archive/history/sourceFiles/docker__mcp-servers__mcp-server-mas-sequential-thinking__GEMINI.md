---
id: docker__mcp-servers__mcp-server-mas-sequential-thinking__GEMINI
title: Docker  Mcp Servers  Mcp Server Mas Sequential Thinking  Gemini
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-13'
last_review: '2026-04-13'
next_review: '2026-07-12'
prelude: Docker  Mcp Servers  Mcp Server Mas Sequential Thinking  Gemini (explanation)
  for dopemux documentation and developer workflows.
---
- **Project Overview:** A Multi-Agent System (MAS) for sequential thinking, built with the Agno framework. It uses a team of specialized agents (Planner, Researcher, Analyzer, Critic, Synthesizer) coordinated by a Team agent to process complex problems.
- **Key Technologies:** Python, Agno, FastMCP, Pydantic.
- **Core Logic:** The main logic is in `main.py`. It defines the `sequentialthinking` tool, which takes a `ThoughtData` object as input. The tool call is then processed by the `SequentialThinkingTeam`.
- **Agents:** Agents are defined in `main.py`. The `Team` agent in `coordinate` mode delegates tasks to specialist agents.
- **Configuration:** The project is configured via environment variables (e.g., `LLM_PROVIDER`, API keys) and the `smithery.yaml` file.
- **Dependencies:** Project dependencies are listed in `pyproject.toml`. Key dependencies include `agno`, `mcp`, `groq`, `exa-py`.
- **Entrypoint:** The application is started by running `main.py`, which calls the `run` function. The `mcp-server-mas-sequential-thinking` script is the entrypoint.