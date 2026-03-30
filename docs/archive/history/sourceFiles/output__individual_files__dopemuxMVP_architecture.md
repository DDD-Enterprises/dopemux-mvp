Of course. Based on the technical implementation document `dopemuxMVP.md`, here is the extracted engineering and architectural blueprint.

***

### 1. Core Project Objective & Key Performance Indicators (KPIs)

*   **Primary Technical Goal:** Deliver an AI-native pair programming development environment, operating within a terminal-based user interface, designed for high-performance code generation and problem-solving.
*   **Success Metrics & Targets:**
    *   **SWE-Bench Score:** 84.8% (pass@1) on the SWE-Bench benchmark.
    *   **Query Throughput:** 626 QPS (Queries Per Second) system load target for the initial deployment.
    *   **Interactive Latency:** <150ms for P99 interactive responses (user input to first token).
    *   **Assist Frequency:** Mean Time Between Assists (MTBA) of < 45 seconds for an active user.
    *   **Context Efficiency:** >90% context window utilization efficiency via compression and RAG.

### 2. Core Architecture & System Components

*   **Overall Architecture:** A multi-agent system composed of 64 specialized agents orchestrated by a central control plane. The architecture utilizes a hierarchical, multi-tiered memory system (L1, L2, L3) to manage state, context, and long-term knowledge. Communication is routed through a central dispatch core.
*   **Primary Components:**
    *   **Claude-flow:** The primary orchestration engine responsible for task decomposition, agent selection, and workflow execution. It translates user intent into a directed acyclic graph (DAG) of agent tasks.
    *   **Letta Memory:** The hierarchical memory subsystem.
        *   **L1 (Working Memory):** Redis-backed, low-latency cache for session state, active context, and agent scratchpads.
        *   **L2 (Episodic Memory):** Qdrant vector database for high-performance semantic search over recent conversations and project files.
        *   **L3 (Long-Term Memory):** PostgreSQL with `pgvector` extension for persistent storage of summarized insights, user preferences, and project-level knowledge graphs.
    *   **MCP (Mimir Control Plane) Servers:** The core backend application servers running the Claude-flow engine and agent logic.
    *   **CCFlare Proxy:** A Cloudflare Worker-based proxy responsible for API authentication, rate limiting, request validation, and A/B testing of different underlying LLM providers.
    *   **Term-UI:** The client-side terminal interface built with React Ink. It manages the user session, renders output, and communicates with the MCP servers via a WebSocket connection.
    *   **Dispatch Core:** A routing component within the MCP that directs tasks from Claude-flow to the appropriate specialized agent pools.

### 3. Technology Stack

*   **Databases:**
    *   **PostgreSQL 16** with `pgvector` extension (L3 Memory)
    *   **Neo4j** (Knowledge graph for code dependency analysis)
*   **Caching & In-Memory:**
    *   **Redis** (L1 Memory, session state)
    *   **Qdrant** (L2 vector search)
*   **Containerization & Orchestration:**
    *   **Docker** & Docker Compose
*   **Languages & Runtimes:**
    *   **Python 3.11+** (Backend services, MCP, agents)
    *   **TypeScript** (Term-UI client)
    *   **Node.js**
*   **Libraries & Frameworks:**
    *   **React Ink** (Terminal UI)
    *   **DSPy** (LLM program compilation and prompt optimization)
    *   **FastAPI** (Backend API framework)
*   **Infrastructure & Cloud:**
    *   **Cloudflare Workers** (CCFlare Proxy)

### 4. Key Algorithms & Protocols

*   **Hybrid Search Algorithm:** A weighted combination of BM25 (sparse, keyword-based) and cosine similarity (dense, semantic) search is used across Letta Memory tiers L2 and L3 to improve retrieval accuracy. The weights are dynamically adjusted based on query type.
*   **RAG (Retrieval-Augmented Generation):** The core mechanism for grounding LLM responses. Context is retrieved from the project codebase and Letta Memory before being passed to the generative model.
*   **Thought Coalescence Protocol (TCP):** A proprietary JSON-based protocol used by agents to broadcast, weigh, and merge partial solutions. This allows for parallelized problem-solving before a final answer is synthesized by a master agent.
*   **Progressive Context Compression:** An algorithm that summarizes and compresses the oldest parts of the conversation and code history into a condensed format to maintain session context while staying within the LLM's context window limits.

### 5. Unique User-Facing Features & Implementations

*   **ADHD-optimized tmux configuration:** A pre-configured `tmux` session is provided with minimal visual clutter, focus-oriented layouts (e.g., single-pane focus mode), and color-blind-friendly themes to reduce cognitive load.
*   **RSD-aware Feedback Mechanism:** (Rejection Sensitive Dysphoria) - The system's agents are prompted to provide constructive feedback using a non-confrontational, Socratic questioning method rather than direct criticism. Error messages are rephrased to be solution-focused.
*   **Progressive Information Disclosure:** Complex outputs (e.g., large code blocks, stack traces) are initially presented in a collapsed, summarized view. The user can explicitly request to expand sections for more detail, preventing information overload.
*   **Gamified Onboarding (`/dopemux quest`):** An interactive tutorial system implemented as a series of quests to teach users the core functionalities of the system in a structured, engaging manner.

### 6. Implementation Plan Summary

*   **Timeline:** A 16-week, 3-phase plan is specified for the MVP.
*   **Initial Phase Deliverables:**
    *   **Phase 1 (Weeks 1-6): Core Infrastructure & Memory.**
        *   Deliverable: A functional Letta Memory subsystem (L1 Redis, L2 Qdrant, L3 PostgreSQL).
        *   Deliverable: A prototype MCP server capable of basic task reception.
        *   Deliverable: A functional Claude-flow orchestration engine for simple, single-agent tasks.
    *   **Phase 2 (Weeks 7-12): Agent Integration & CLI.**
        *   Deliverable: An 8-agent system integrated with the Dispatch Core.
        *   Deliverable: A functional Term-UI client with basic command handling and output rendering.
        *   Deliverable: End-to-end integration for a single core use case (e.g., "explain this code block").

### 7. Critical Risks & Mitigation Strategies

*   **Risk:** Model Drift/Degradation from upstream provider API changes.
    *   **Mitigation:** Implement a continuous evaluation pipeline using the SWE-Bench benchmark. The CCFlare Proxy will be used to A/B test and canary-roll new model versions. A "prompt-as-code" repository with versioning will be maintained.
*   **Risk:** Scalability bottleneck in Letta Memory's vector search component under high load.
    *   **Mitigation:** Qdrant was chosen for its horizontal scaling capabilities. The system will be load-tested early in Phase 2 to identify performance cliffs. Read/write operations will be benchmarked to determine appropriate sharding strategies.
*   **Risk:** Exceeding LLM context window limits during long, complex sessions.
    *   **Mitigation:** Prioritize the implementation of the Progressive Context Compression algorithm. Aggressively use RAG to offload static file context to the vector database instead of stuffing it directly into the prompt.
*   **Risk:** State management complexity across the distributed agent system.
    *   **Mitigation:** Enforce a strict separation of concerns for state: Redis (L1) for ephemeral session/task state and PostgreSQL (L3) for persistent, transactional state. All inter-agent communication and state-modifying API calls must use idempotency keys.