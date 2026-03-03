Based on the analysis of `DOPEMUX_IMPLEMENTATION_GUIDE_v2.md`, here is the extracted technical blueprint.

### 1. Core Project Objective & Key Performance Indicators (KPIs)

*   **Primary Technical Goal:** Deliver a multi-agent, AI-augmented terminal development environment designed to accelerate complex software engineering tasks.
*   **Key Performance Indicators:**
    *   **Software Engineering Task Resolution:** 84.8% pass rate on the SWE-Bench benchmark.
    *   **Agent Orchestration Throughput:** 626 QPS on the Master Control Plane (MCP) servers.
    *   **Interactive Latency:** <100ms P99 latency for user-facing terminal interactions.
    *   **Code Completion Accuracy:** >70% line completion accuracy on the HumanEval-X benchmark.
    *   **Client Resource Footprint:** <250MB idle RAM consumption for the client-side PTY process.

### 2. Core Architecture & System Components

*   **Overall Architecture:** A client-server, multi-agent swarm architecture. The system is composed of 64 discrete agents operating on a hierarchical, multi-layered memory system. A central Master Control Plane manages agent lifecycle and task distribution.
*   **Primary Components:**
    *   **Claude-flow:** The primary agentic workflow engine responsible for state machine orchestration, task decomposition, and agent scheduling.
    *   **Letta Memory:** A hierarchical memory system comprised of three layers:
        *   **L1 (Working Context):** In-memory Redis cache for ephemeral data and active agent state. TTL of 5 minutes.
        *   **L2 (Episodic):** PostgreSQL database storing conversational history and short-term project context.
        *   **L3 (Long-Term):** A knowledge graph (Neo4j) and a vector database (Qdrant/pgvector) for embedding-based retrieval of documentation, codebase semantics, and historical solutions.
    *   **MCP (Master Control Plane) Servers:** A set of gRPC servers responsible for agent lifecycle management, resource allocation, and routing tasks to available agents based on skill and load.
    *   **CCFlare Proxy:** A secure ingress proxy routing user requests from the client to the appropriate MCP instance, handling authentication and rate limiting.
    *   **DTerm Client:** A custom pseudo-terminal (PTY) client built with Rust and WebAssembly, responsible for rendering the UI and managing local state.

### 3. Technology Stack

*   **Backend & Orchestration:** Rust (MCP Servers), Python (Agents), DSPy (Agent development framework).
*   **Databases & Storage:**
    *   **PostgreSQL + pgvector:** Primary relational store and L3 vector storage.
    *   **Redis:** L1 working memory cache and message bus for inter-agent communication.
    *   **Qdrant:** Dedicated high-performance vector store for semantic search.
    *   **Neo4j:** Knowledge graph for representing codebase relationships and dependencies.
*   **Frontend / Client:** TypeScript, React Ink (Terminal UI rendering), Rust, WebAssembly (Core terminal logic).
*   **Infrastructure & Communication:**
    *   **Containerization:** Docker.
    *   **Orchestration:** Kubernetes (K8s).
    *   **Protocols:** gRPC with Protocol Buffers (Internal service-to-service), JSON-RPC 2.0 over WebSockets (Client-to-server).

### 4. Key Algorithms & Protocols

*   **Memory Retrieval:** A hybrid search algorithm for the L3 Letta Memory layer. It combines keyword-based sparse vector search (BM25) with dense vector semantic search (HNSW). The final relevance score is a weighted combination: `Score = α * (BM25_Score) + (1-α) * (Cosine_Similarity)`, where α is dynamically adjusted based on query type.
*   **Agent Task Planning:** Hierarchical Task Network (HTN) planning is used by Claude-flow to decompose high-level user goals into a graph of executable sub-tasks for individual agents.
*   **Inter-Service Communication:** gRPC with Protocol Buffers is mandated for all internal backend communication to ensure low latency and strong typing.
*   **Client-Server Communication:** JSON-RPC 2.0 over a persistent WebSocket connection is used for real-time, bidirectional communication between the DTerm Client and the CCFlare Proxy.

### 5. Unique User-Facing Features & Implementations

*   **Progressive Information Disclosure:** The UI renders complex agent outputs in stages. By default, only the final command or code block is shown. The underlying reasoning, tool usage, and file diffs are collapsed within expandable toggles to reduce initial cognitive load.
*   **RSD-aware Feedback Loop:** System-generated feedback and error messages are programmatically rephrased to be constructive and solution-oriented, avoiding negative framing. (e.g., "Error: Command failed" becomes "That didn't work. Let's try this alternative approach..."). The implementation guide cites research (`Fischer et al., 2023`) indicating this approach has a +0.4 Cohen's d effect size on user task persistence.
*   **ADHD-optimized `tmux` Environment:** A built-in, pre-configured `tmux` session manager featuring a high-contrast, minimalist theme. It utilizes `tmux-resurrect` for automatic session persistence and provides single-keystroke bindings for core workflows to minimize context switching.

### 6. Implementation Plan Summary

*   **Timeline:** A 16-week, 4-phase implementation is outlined.
*   **Initial Deliverables:**
    *   **Phase 1 (Weeks 1-4): Core Infrastructure & Memory.**
        *   Deliverable: A provisioned Kubernetes cluster running PostgreSQL/pgvector, Redis, and Qdrant.
        *   Deliverable: A functional Letta Memory L2/L3 API with the core hybrid search algorithm implemented.
    *   **Phase 2 (Weeks 5-8): Agent & Orchestration MVP.**
        *   Deliverable: A single-node MCP server capable of managing the lifecycle of a single agent.
        *   Deliverable: A baseline Python agent built with DSPy capable of performing a "hello world" task via gRPC.

### 7. Critical Risks & Mitigation Strategies

*   **Risk:** Cascading LLM inference latency in multi-agent chains will violate the <100ms P99 interactive latency KPI.
    *   **Mitigation:** Implement aggressive, multi-layer caching in Letta Memory (L1/L2). Utilize speculative execution for parallelizable agent sub-tasks. Develop and fine-tune smaller, distilled models for routine, low-level tasks (e.g., code classification, intent recognition).
*   **Risk:** State synchronization and consistency across a 64-agent distributed system is prone to race conditions and data corruption.
    *   **Mitigation:** Enforce an immutable state transition model within the Claude-flow orchestrator. Utilize Redis as a centralized, authoritative state store with optimistic locking mechanisms for concurrent writes.
*   **Risk:** The system is vulnerable to prompt injection and other adversarial inputs that could compromise agent behavior or data security.
    *   **Mitigation:** Implement a dual-LLM security architecture. A "sanitizer" LLM validates and rewrites user input against predefined security policies before passing it to the primary "execution" LLM. Employ strict input/output schemas and context fencing to limit the operational scope of each agent.