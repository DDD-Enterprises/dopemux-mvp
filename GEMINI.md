# Gemini CLI - Workspace Configuration & MCP Usage

This workspace integrates custom MCP servers inherited from the `dopemux-mvp` project. These tools power a **Two-Plane Architecture** combining Project Management (PM Plane) with Cognitive accommodations (Cognitive Plane). Below are detailed instructions on how to use them implicitly during tasks:

## Core Components & Architecture

### 1. Task Orchestrator (`task-orchestrator`)
**Purpose:** The central coordination hub linking human project management (Leantime) with AI agents and knowledge graphs. It manages ADHD-optimized workflows.
**Architecture:** 
- Acts as the "PlaneCoordinator".
- Handles task assessment: assigns complexity scores (0.0-1.0), energy requirements (low/medium/high), and calculates cognitive load.
- Enforces user state tracking and 25-minute focus session boundaries.
- Routes tasks based on complexity: High complexity (>0.8) goes to Zen, implementation to Serena, research to Taskmaster.
**Implicit Usage:** 
- Use the orchestrator to break down work. If a task feels overwhelming or complex, delegate the breakdown to the task-orchestrator.
- Obey cognitive load constraints. Keep focus windows strict and summarize progress often.

### 2. ConPort & Dope Memory (`conport`)
**Purpose:** The absolute Single Source of Truth (SSoT) and Authority for the workspace's Knowledge Graph and decision provenance.
**Architecture:**
- **Authority Invariant (INV-MEM-002):** If a decision or progress is not in ConPort, it didn't formally happen.
- **Append-Only Ledger (INV-MEM-003):** All events, decisions, and tool outputs are written to an append-only Chronicle Ledger (via Dope Memory).
- **Promotion (INV-MEM-004):** Raw logs aren't truth; the Supervisor "promotes" summaries to truth. Promoted content must cite source event IDs.
- Tracks project progress, architectural decisions (ADRs), and relationships across files.
**Implicit Usage:** 
- **Read:** Use ConPort (`semantic_search`, `get_decisions`) before making architectural changes to ensure you don't violate past decisions.
- **Write:** After completing a milestone or making a major structural decision, use ConPort (`log_progress`, `update_progress`) to store the outcome permanently. Provide metadata like `tags=["energy-medium", "complexity-3"]`.

### 3. Serena (`serena`)
**Purpose:** Task execution and cognitive (ADHD) accommodation engine.
**Implicit Usage:** Your primary agent for implementation-heavy tasks. Use Serena to get highly structured, step-by-step guidance that prevents losing track of the main goal when deep in debugging.

### 4. Dope Context (`dope-context`)
**Purpose:** Semantic search, deep research, and global indexing.
**Implicit Usage:** Use this to query large codebases, retrieve related documentation, or find specific code patterns quickly.

### 5. PAL MCP (`pal`)
**Purpose:** Provider-Agnostic LLM Server. 
**Implicit Usage:** Offload specific sub-tasks to other LLMs (like Devstral, Claude, etc.) when you need parallel reasoning or specialized models without consuming your own main context thread.

## Operational Invariants
- **Worktree Isolation (INV-MEM-001):** Never cross-contaminate state between different project roots.
- **Stale Read Prevention (INV-MEM-007):** Always operate on the latest state. If a file changes out from under you, refresh your context.
- **Redaction (INV-MEM-005):** Never persist API keys, secrets, or PII into ConPort, Dope Memory, or task logs.

*Note: The servers rely on the `dopemux-mvp` Docker/Tmux stack running locally. Ensure they are active before invoking their tools.*