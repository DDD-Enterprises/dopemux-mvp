ChatX/ChatRipper Repository Prompt
Status: Draft | Owner: <TBD> | Last Updated: 2025‑09‑02
Purpose
This prompt provides Claude Code with essential context about the ChatX/ChatRipper project. It should be loaded at the beginning of each session to orient the model and reduce token consumption. Keep this file concise; link out to detailed documents when necessary.
Project Overview
Goal: Summarise and extract chat conversations into actionable data structures. The project implements pipelines for extraction, transformation, redaction, indexing, enrichment and querying of chat messages.
Languages & Frameworks: [Specify, e.g., Python 3.11, FastAPI, SQLite].
Repository Structure:
src/ — Core application code (extractors, transformers, redactors, enrichers, indexers).
tests/ — Unit and integration tests.
PROJECT_DESIGN_FILES/ — Architecture, ADRs, interfaces and acceptance criteria.
scripts/ — Utility scripts for maintenance and automation.
Build & Test: To install dependencies run pip install -r requirements.txt. To run tests execute pytest. Use make lint to check formatting and type hints if a Makefile is provided.
Documentation: See ARCHITECTURE.md for the C4 narrative, INTERFACES.md for API contracts and ACCEPTANCE_CRITERIA.md for user stories and scenarios.
Development Guidelines
Slice‑Based Development: Define small vertical slices with clear user stories and acceptance criteria. Store them in ACCEPTANCE_CRITERIA.md.
Test First: Write failing tests before implementing. Use TDD loops to guide development and ensure coverage.
Use MCP Tools:
Read and edit files via the Filesystem server
mcpservers.org
.
Manage code and commits via the GitHub server
apidog.com
.
Persist decisions and notes in the Memory Bank and Knowledge Graph Memory servers
mcpmarket.com
.
Fetch up‑to‑date docs via Context7
upstash.com
 and perform research via Exa
apidog.com
 or DuckDuckGo.
Model Use: Default to local models; use Sonnet or Opus only when necessary. Let the PluggedIn router decide if configured.
Document & Commit: Update docs (architecture, interfaces, ADRs) and commit frequently. Use conventional commit messages.
Privacy & Security: Never include secrets or personal data in prompts or code. Follow redaction guidelines when handling sensitive messages.
Open Questions: Log ambiguities, unresolved questions and technical debts in NEXT.md.
Setup & Configuration
Run ./setup_mcp_servers.sh to install required MCP servers. Set environment variables for API keys and paths (see the script header). After installation, restart Claude Desktop and verify that each server appears in your tool list.
Limitations
This prompt is intentionally brief. For detailed instructions on using MCP servers and models, see CLAUDE.md and docs/reference/workflow/taskmaster-integration.md.
Replace placeholder text (e.g., languages, modules) with accurate information for your repository.
Keep this prompt up to date as your project evolves. It is a critical input for high‑quality AI assistance.