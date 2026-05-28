# **Dopemux Architecture: Multi-Agent Ingress and Control Layer Design**

## **Executive Summary**

The architectural evolution of the Dopemux workspace necessitates a highly strategic decision regarding the ingress and control layer for a rapidly expanding, heterogeneous ecosystem of autonomous coding agents. Currently, the Dopemux ecosystem supports a highly fragmented multi-plane topology consisting of over thirty discrete services, adapters, sidecars, and canonical systems.1 With the introduction of advanced and diverse runtimes—such as Claude Code, GitHub Copilot, Gemini CLI workflows, OpenAI Codex, and Google Antigravity—the workspace faces a significant integration challenge. The core architectural decision revolves around whether Dopemux should introduce a unified single-agent gateway that standardizes lifecycle hooks, Model Context Protocol (MCP) integrations, wrappers, prompt injections, and event normalization, while strictly preserving the isolated integrity of the underlying canonical backend authorities.  
Extensive analysis of vendor documentation and runtime capabilities indicates a high degree of variance in extensibility surfaces across different AI providers. While the Model Context Protocol has emerged as the dominant industry standard for external tool integration and capability discovery 2, the mechanisms for intercepting the agentic loop—specifically deterministic lifecycle hooks, middleware execution, and context injection—remain highly heterogeneous.3 Furthermore, a rigorous analysis of the Dopemux operational boundaries dictates that domain authorities governing project management, memory chronicles, and code retrieval must under no circumstances be collapsed into a monolithic routing or application layer.1  
The findings strongly advocate for a decoupled ingress architecture. The recommended topology is the implementation of a centralized Dopemux Agent Gateway dedicated strictly to routing, authentication, rate limiting, and MCP aggregation, complemented by lightweight, runtime-specific shim layers deployed natively at the edge. This approach satisfies the necessity for unified tool management and event normalization without violating the epistemic boundaries of the canonical truth systems, ensuring that Dopemux remains portable, secure, and resilient in the face of rapidly shifting multi-agent paradigms.

## **System Context and Architectural Boundary Discipline**

Designing an effective multi-agent ingress layer requires a foundational understanding of the existing Dopemux architecture. The Dopemux workspace is characterized by a composed, multi-system paradigm that explicitly emphasizes cross-system coupling over monolithic centralization.1 In this environment, authority is explicitly split across specialized operational planes, and maintaining boundary discipline is paramount. Introducing application logic, memory storage, or state management into an ingress gateway would constitute a critical architectural violation.1

### **The Principle of Distributed Authority**

The Dopemux workspace explicitly prohibits multiple writers for a single domain and mandates that adapters, bridges, and proxies must never be treated as the source of truth.1 The existing topology maps authority across five distinct operational planes, each governed by strict isolation rules. The Operator and Control Plane, primarily driven by the dopemux core service, acts as the main operator-facing control surface.1 It owns the command-line interface entrypoints, startup behaviors, MCP server coordination, and local environment shaping.1 Crucially, the control plane acts strictly as a router and configuration manager; it possesses no canonical truth regarding project management, workflow status, or memory persistence.1  
The Project Management (PM) Plane is characterized by a deliberately split authority model.1 The Leantime application manages passive metadata and sprint or project snapshot authority.1 Operating alongside it, the task-orchestrator service coordinates workflow-significant transitions and manages the workflow-serving application programming interfaces (APIs).1 Furthermore, ConPort acts as the authority for structured decisions, project progress, and specific context.1 Finally, the dope-memory service functions as a read-only mirror for historical project management receipts.1 If a unified agent gateway were to attempt to coalesce these distinct PM states into a single database, it would fatally violate the distributed writer constraints of the workspace.1  
The Memory and Retrieval Planes are similarly segmented to separate chronicle history from structured operational context. The dope-memory service serves as the canonical SQLite chronicle ledger, preserving raw event storage and work-log evidence.1 Conversely, the working-memory-assistant manages volatile state, snapshot recovery, and cognitive operational support.1 For retrieval, the dope-context service manages deterministic codebase and documentation indexing, operating completely orthagonally to ConPort, which exclusively manages semantic and graph-based retrieval mechanisms.1  
The Adapter and Bridge Plane, populated by services such as dopecon-bridge, is responsible for mediating communication, performing safe PM routing, and transporting events via Redis Streams.1 The documentation explicitly warns that these surfaces must never establish or claim canonical authority, as operators and agents alike can easily mistake proxy endpoints for the source of truth.1

### **Architectural Drift and Truth Gaps**

A comprehensive audit of the Dopemux service catalog reveals significant architectural drift and unresolved "Truth Gaps" that the new ingress layer must navigate.1 There are currently over thirty services, including active canonical systems, support services, sidecars, adapters, and a substantial accumulation of legacy or drifted applications.1 Naming and branding standardization has deteriorated, evidenced by the divergence between the actual runtime engine (dopetask) and the legacy operator language (TaskX) still prevalent in code and documentation.1  
Systemic contradictions are particularly evident in the orchestration and execution pathways. Within the task-orchestrator service, the runtime authority points in conflicting directions; the Dockerfile targets modules that conflict with the observed canonical authorities, and the task\_orchestrator/app.py path is an actively failing legacy route that explicitly instructs operators against its use.1 Furthermore, port connectivity conflicts plague the workspace, with the task-orchestrator defaulting to port 3014 in the codebase but being exposed on port 8000 via Docker Compose configurations.1 Memory surface overlaps between services/dope-query and ConPort create semantic retrieval ambiguities, while the code-intelligence service Serena suffers from duplicate implementations across the repository without a single declared canonical writer.1  
These truth gaps underscore the danger of a monolithic ingress gateway. If the gateway attempts to absorb application logic, it will invariably inherit and compound these existing ambiguities. Therefore, the ingress layer must remain a strictly network-level entity, delegating all domain logic to the clearly defined Tier 1 canonical systems while actively obfuscating the Tier 4 legacy services from the agents' view.

## **Runtime Capability Analysis**

The extensibility surfaces of modern agentic coding assistants dictate how they can interact with the proposed Dopemux architecture. Designing a robust ingress gateway requires a granular understanding of how each specific runtime handles the Model Context Protocol (MCP), deterministic lifecycle hooks, prompt injection capabilities, and background execution mechanics.

### **Claude Code Extensibility Mechanisms**

Claude Code provides a highly mature, structured, and rigorously documented extensibility model, leveraging both MCP for capability expansion and deterministic lifecycle hooks for execution interception.3 The agentic loop within Claude Code consists of gathering context, taking action, and verifying results, blending these phases iteratively.8 Hooks are designed to run outside this loop entirely as deterministic background scripts, ensuring predictable automation without requiring expensive LLM reasoning tokens.3  
Claude Code supports deterministic hooks executed at precise lifecycle events, primarily SessionStart, PreToolUse, PostToolUse, UserPromptSubmit, and Stop.3 These hooks can be configured globally within the user's home directory, or locally within a project directory, allowing for highly granular scope management.3 The hook infrastructure supports robust filtering via matchers; for instance, a PreToolUse hook can be configured to fire exclusively when the agent attempts to utilize the Bash tool to execute a specific command pattern.3  
Crucially, Claude Code offers versatile execution modes for these hooks. It natively supports synchronous command execution via shell scripts, HTTP POST requests to specified uniform resource locators (URLs), and asynchronous execution enabled by an async: true configuration flag.3 Asynchronous hooks run in the background without blocking the primary interactive session, which is vital for long-running telemetry or test-suite execution.3 Furthermore, context injection is seamlessly supported; standard output generated during SessionStart and UserPromptSubmit hooks is natively ingested directly into the LLM's context window.3  
Regarding external connections, Claude Code provides extensive support for the Model Context Protocol. It accommodates local stdio transports for system-level access and remote http transports for cloud-based services, while explicitly deprecating the older Server-Sent Events (sse) transport.3 Installation scopes are strictly hierarchal (User, Project, Local), and administrators can enforce policy-based controls via allowlists and denylists in a managed configuration file.3 The combination of streamable HTTP hooks and robust remote HTTP MCP servers allows Claude Code to interface cleanly and natively with a centralized Dopemux gateway.

### **GitHub Copilot Agent Mode Extensibility**

Recent updates to the GitHub Copilot Agent Mode (specifically the v1.109 release cycle) have significantly expanded its extensibility profile, advancing its capabilities to near parity with Claude Code.6 Historically, the extensibility of the Copilot CLI was limited, but the introduction of agent hooks allows developers to execute custom shell commands at specific lifecycle points to enforce policies or automate project-specific tasks.6  
The Copilot hook architecture mirrors the Claude Code event model, intentionally utilizing a compatible configuration format to allow developers to reuse existing configurations across different agent ecosystems.6 The supported lifecycle events include onSessionStart, onPreToolUse, onPostToolUse, onUserPromptSubmitted, and onSessionEnd.9 Additionally, Copilot exposes highly specific execution events such as shell\_detached\_completed and agent\_idle, which provide deep visibility into asynchronous background tasks.10  
Execution modes within Copilot include local process execution via standard input/output, remote server communication via streamable HTTP transport, and remote server access via Server-Sent Events.10 Unlike Claude Code, Copilot retains robust support for SSE transports. Context injection is natively supported via the onSessionStart and onUserPromptSubmitted hooks, allowing operators to inject git states, load user preferences, or rewrite prompts dynamically before the model processes them.9 Furthermore, Copilot supports custom instructions, organization-wide rules, and workspace-specific prompt files for static context management.6  
Copilot has also heavily invested in MCP integration, allowing the agent to interact with external tools and services.6 While native, arbitrary extensibility APIs are not currently planned by Microsoft, the combination of deterministic lifecycle hooks and standard MCP support renders the implementation of a universal wrapper shim highly feasible for the Dopemux architecture.11

### **Gemini CLI Workflow Integration**

Google's Gemini CLI employs a distinct middleware approach to its agentic loop, prioritizing pre-execution validation, context shaping, and synchronous control.5 Introduced in version 0.26.0, Gemini CLI hooks operate as middleware scripts that pause the execution environment, forcing the CLI to wait for the custom logic to complete before continuing the LLM's generation cycle.5  
The primary lifecycle events utilized by Gemini are BeforeTool and AfterAgent.5 The BeforeTool hook serves as a synchronous gatekeeper, commonly deployed to validate actions, enforce security policies, or prevent the agent from writing sensitive credentials into the codebase.5 The AfterAgent hook intercepts the agent's completion signal, allowing developers to enforce continuous iterative loops until specific testing requirements are met.5  
Gemini natively supports asynchronous operations through JavaScript async/await patterns within its extension framework, allowing developers to record input/output telemetry and assign custom metadata attributes during execution.13 Context injection is heavily supported; the CLI can recursively ingest files from directories, reference binary images directly in prompts, and dynamically inject relevant information via the BeforeTool hook before the model processes a request.5  
The discovery and execution of external tools are managed by a sophisticated internal discovery layer (mcp-client.ts).15 This layer establishes connections using stdio, sse, or streamable HTTP transports, fetches tool definitions, and sanitizes the tool schemas for compatibility with the Gemini API prior to global registration.15 While integration is highly feasible, the semantic differences in hook naming conventions (e.g., utilizing BeforeTool rather than the industry-standard PreToolUse) dictate that a translation abstraction layer must be implemented within the Dopemux client-side shim to ensure compatibility.3

### **OpenAI Codex Capabilities and Limitations**

The OpenAI Codex Command Line Interface operates as a terminal-native, Rust-based agent designed for high-speed local execution, but its extensibility framework remains explicitly experimental and somewhat constrained.4 Codex launches a full-screen terminal user interface that supports conversational workflows, subagent parallelization, and local code reviews.4  
The hook architecture in Codex is activated exclusively via an experimental feature flag (codex\_hooks \= true) located in the configuration file.4 The supported events include SessionStart, PreToolUse, PostToolUse, UserPromptSubmit, PermissionRequest, and Stop.4 A critical limitation of the Codex hook implementation is its restrictive matchers; currently, the PreToolUse, PostToolUse, and PermissionRequest events only emit and intercept the Bash tool, ignoring other execution modalities.4 Furthermore, hook support is completely disabled on the Windows operating system.4  
Execution modes rely entirely on standard input/output shell command execution. Unlike Claude Code and Gemini, Codex natively lacks support for asynchronous hooks; any background processes or telemetry tasks must be delegated externally, severely limiting local non-blocking telemetry.4 Context injection is handled via standard output during the SessionStart or UserPromptSubmit events, allowing developers to pass workspace conventions or augment prompts.4  
Codex connects to external tools via the Model Context Protocol, supporting both stdio and HTTP transports configured through the global configuration file.18 It fully respects HTTP, HTTPS, and SOCKS5 proxy environments.17 However, the combination of strictly synchronous shell hooks, the restriction to Bash-only interception, and the experimental nature of the framework presents significant integration challenges. Codex will require heavy reliance on standard MCP tools rather than deep, reliable lifecycle hook integration.4

### **Google Antigravity Extensibility**

Google Antigravity represents an architectural departure from standard command-line interfaces, operating as a comprehensive, multi-window, agent-first Integrated Development Environment (IDE).19 Rather than functioning as a tool that provides suggestions within an editor, Antigravity provides a "Mission Control" interface for managing autonomous agents capable of planning, executing, and validating complex tasks across terminal, browser, and editor subagents simultaneously.19  
Because of its GUI-first approach, Antigravity eschews traditional, deterministic Git-style lifecycle hooks.21 Instead, extensibility is driven by "Agent Skills" and semantic triggers.21 The agent utilizes natural language reasoning to contextualize when to trigger specific logic or rulesets, rather than relying on strict, state-machine-driven lifecycle events.21 Developers influence this behavior through project-scoped markdown files (such as .windsurfrules analogs) and carefully crafted Skill descriptors.21  
Full integration with the Model Context Protocol was introduced to Antigravity in late 2025, enabling robust external tool access.20 However, because strict deterministic hooks are unsupported, integrating Antigravity into the Dopemux architecture requires a fundamentally distinct strategy.22 Integration must bypass the expectation of a local CLI lifecycle shim and rely almost entirely on the centralized MCP Gateway providing access to normalized backend tools.

### **Runtime Capability Matrix**

| Capability Feature | Claude Code | GitHub Copilot | Gemini CLI | OpenAI Codex | Google Antigravity |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Hook Support** | Yes (Mature) | Yes (v1.109+) | Yes (Middleware) | Yes (Experimental) | No (Relies on Skills) |
| **HTTP Hook Support** | Yes | Yes (Streamable) | Yes | No (Shell Execution Only) | N/A |
| **Async Hook Support** | Yes (async: true) | Yes (Detached Shell) | Yes (async/await) | No | N/A (Background Agents) |
| **Prompt / Context Injection** | Yes (via stdout) | Yes (Hooks & Files) | Yes (via BeforeTool) | Yes (via stdout) | Yes (via Skills/Rules) |
| **MCP Support** | Yes | Yes | Yes | Yes | Yes |
| **MCP Transport Scopes** | stdio, http | stdio, http, sse | stdio, http, sse | stdio, http | Undocumented GUI |
| **Wrapper Feasibility** | High | High | High | Moderate (CLI restrictions) | Low (GUI Application) |
| **Session Event Support** | Yes (SessionStart) | Yes (onSessionStart) | Unknown | Yes (SessionStart) | N/A |
| **Tool Event Support** | Yes (PreToolUse) | Yes (onPreToolUse) | Yes (BeforeTool) | Yes (PreToolUse \- Bash only) | N/A |
| **Primary Integration Mode** | MCP \+ HTTP Hooks | MCP \+ Shell Hooks | MCP \+ Middleware Hooks | Wrapper Script \+ MCP | MCP Gateway \+ Skills |
| **Fallback Integration Mode** | Wrapper Script | Wrapper Script | Wrapper Script | Shell Hooks | None |

## **Claude-Mem Architecture and Portability Analysis**

To determine whether Dopemux should attempt to implement a monolithic unified gateway that absorbs all lifecycle logic, or a pattern of distributed local shims interfacing with a backend gateway, an analysis of the widely adopted claude-mem architecture serves as a critical systemic case study.24

### **Architectural Breakdown**

The claude-mem application operates as a specialized plugin designed to mitigate "context compaction"—a degradation phenomenon where AI assistants lose nuanced session history, architectural context, and bug resolutions as their working context windows fill and compress.26 To resolve this, claude-mem captures execution data, summarizes it, and injects it back into future sessions.  
The architecture is composed of five tightly coupled functional components.25 First, a suite of six distinct JavaScript Plugin Hooks capture precise lifecycle events within the Claude Code environment, including context-hook.js for session initialization and save-hook.js for post-tool executions.25 Second, a Smart Install pre-hook script functions as a cached dependency checker, ensuring operational stability before the context hooks execute.25 Third, a Worker Service built on Express.js and managed by the Bun runtime processes raw observations asynchronously.25 Fourth, the Database Layer utilizes a local SQLite 3 database with the bun:sqlite driver, leveraging FTS5 virtual tables for high-speed full-text search and ChromaDB for semantic vector retrieval.25 Finally, a Viewer UI provides real-time visualization of the memory stream via Server-Sent Events (SSE), alongside a specialized mem-search skill that employs progressive disclosure to drastically reduce token consumption during context retrieval.25  
The data pipeline follows a strict chronological flow. Terminal standard input (stdin) triggers the hooks, which write raw observational data synchronously to the local SQLite database. The asynchronous Worker Service subsequently reads these observations, utilizing the Anthropic SDK to extract structured learnings and generate semantic summaries.25 These compressed summaries are written back to the database, standing ready for retrieval by the next session's initialization hook.25

### **Portability and Claude-Specific Constraints**

The portability of the claude-mem architecture presents a dichotomy. The underlying technology stack—Node.js, Bun, Express, and SQLite—is highly portable across major operating systems (Windows, macOS, Linux).25 The database logic is self-contained within a single local file, and the user interface is bundled cleanly via esbuild.25  
However, the ingress mechanisms and control flow are deeply proprietary and Claude-specific. The application is fundamentally reliant on the precise firing sequences of Claude Code's internal state machine.25 It depends entirely on the @anthropic-ai/claude-agent-sdk for processing and cannot function without the exact UserPromptSubmit and PostToolUse event payloads generated by the Claude CLI.25

### **Systemic Implications for Gateway Design**

The architectural paradigm demonstrated by claude-mem provides definitive evidence against attempting to unify agent lifecycle events within a remote network gateway. Lifecycle events—such as the initiation of a user prompt, the localized spawning of a background subagent, or the generation of a specific file edit—occur entirely on the client-side, deep within the local CLI runtime.24 A remote network gateway can only observe externalized API traffic, such as outbound MCP tool execution requests.25  
If Dopemux were to consolidate all tracking and lifecycle logic into a single monolithic ingress gateway, the system would immediately lose visibility into internal agent states, pre-tool security validations, and local context compactions occurring on the operator's machine. Therefore, the claude-mem architecture strongly argues for a bifurcated approach: **robust local shims** are required to capture the client-side state machine transitions, while a **unified MCP gateway** is required to provide backend access to the workspace services and canonical data stores.

## **Multi-Agent Architecture Patterns**

Designing a centralized control layer capable of managing over thirty microservices while simultaneously interfacing with diverse, autonomous AI runtimes requires the application of highly resilient distributed system patterns. The architecture must actively balance network latency, state isolation, authentication governance, and fault tolerance.27

### **The MCP Gateway versus MCP Proxy Pattern**

In an expansive ecosystem comprising multiple discrete tools (e.g., dope-context, ConPort, task-orchestrator), allowing every autonomous agent to maintain individual point-to-point connections with every tool creates an unmanageable mesh.28 This mesh leads to combinatorial configuration explosions and fragmented security policies.  
The distinction between an MCP Proxy and an MCP Gateway is critical.29 An MCP Proxy represents a lightweight transport bridge; it merely converts protocols (e.g., translating standard input/output stdio streams into Server-Sent Events or HTTP requests) without inspecting, mediating, or securing the underlying payload.30 Conversely, an MCP Gateway actively enables, controls, secures, and logs the interactions between the agents and the servers.29 As observed in enterprise implementations such as Kong, Azure APIM, and MintMCP Gateway, the gateway pattern introduces token-based quotas, Identity Provider (IdP) authentication, dynamic tool filtering, and request logging vital for incident response.32  
Given the strict domain boundaries enforced within the Dopemux ecosystem 1, the implementation of a full MCP Gateway is imperative. It centralizes tool discovery—functioning similarly to Gemini's internal mcp-client.ts layer—while shielding the highly sensitive canonical backend systems from abusive retry loops or hallucinated API calls generated by autonomous agents.15

### **Event-Driven Hook Ingestion with Async Workers**

Agentic execution loops are exquisitely sensitive to latency. Synchronous lifecycle hooks that block the agent from taking its subsequent action severely degrade the user experience and increase the likelihood of LLM timeout errors.5 The architectural pattern derived from both the claude-mem implementation and the Gemini CLI extensions dictates that hooks should execute synchronously only when performing deterministic security gating (e.g., intercepting and blocking a destructive rm \-rf shell command).3  
All other non-critical tasks—such as memory indexing, telemetry logging, and context summarization—must utilize an event-driven ingestion queue.34 In this pattern, the local client-side shim drops a lightweight JSON payload to a fast ledger (such as Redis Streams or a local SQLite instance) and immediately returns control to the agent.25 An asynchronous background worker process subsequently consumes the event queue, interacting with the LLM or the Dopemux backend to perform the heavy analytical processing offline.25 This pattern ensures maximum system responsiveness while maintaining comprehensive data capture.

### **Capability-Adaptive Adapter Layers**

Different AI runtimes require different payload structures and exhibit varying reasoning capacities. A capability-adaptive adapter layer dynamically reshapes data based on the identity of the calling agent.1 Within the current Dopemux architecture, the dopecon-bridge already functions as a rudimentary adapter layer, mediating project management operations.1 In a refined multi-agent architecture, the gateway itself must assume this capability-adaptive role. When the gateway receives a request, it will interrogate the incoming agent identifier (differentiating between a Codex request and a Copilot request) and dynamically adapt the tool schema formatting to match the vendor's specific MCP dialect or context window limitations.

### **Service-Tier-Aware Consolidation**

Large, multi-service systems inevitably drift toward complexity and redundancy. Service-tier-aware consolidation involves categorizing microservices based on their epistemic authority and selectively merging or isolating them to reduce network hops.1 By decoupling the control plane (routing, ingress, API aggregation) from the data plane (canonical truth, storage, state), system architects can merge intermediate proxies and bridges into the ingress gateway without corrupting the underlying domain authorities.

## **Architectural Options Analysis**

To establish the optimal ingress and control layer for the Dopemux workspace, three primary architectural configurations were rigorously evaluated against the system's operational requirements and boundary constraints.1

### **Option A: Status Quo Plus Better Local Hooks**

In this model, the architecture remains highly decentralized. The dopemux core service continues to generate local wrapper scripts and environment configuration files, and each individual agent (Claude, Copilot, Codex) connects directly to the backend domain services via locally configured stdio MCP processes.1

* **Advantages**: This approach requires minimal infrastructure engineering and introduces zero new network hops, ensuring the lowest possible latency for local agent execution.  
* **Disadvantages**: Security, authentication, and telemetry remain hopelessly fractured across the workspace. Managing connections for over thirty services across five distinct agent environments results in a combinatorial configuration nightmare. It fundamentally fails to provide a unified control surface, allowing agents to bypass security gateways and interact directly with vulnerable backend systems.

### **Option B: Single Dopemux Agent Gateway with Separate Domain Authorities**

This configuration deliberately decouples the ingress routing plane from the canonical data planes. A centralized Dopemux Agent Gateway is deployed as the sole network entry point for all agentic traffic. This gateway exposes a unified MCP HTTP endpoint, manages Identity Provider authentication, enforces rate limiting, aggregates tool discovery, and routes validated requests to the appropriate backend canonical systems (e.g., Leantime, ConPort, dope-memory).1 Concurrently, extremely lightweight local shims are deployed natively to the developer's machine to capture client-side lifecycle events and forward telemetry asynchronously to the gateway.

* **Advantages**: This architecture strictly preserves the split-authority boundary discipline governing the PM and Memory planes.1 It consolidates security, authentication, and logging into a single highly observable layer. It normalizes vendor-specific payload quirks into a standard internal protocol, rendering the backend architecture highly portable and entirely agnostic to the choice of front-end LLM.  
* **Disadvantages**: The introduction of a centralized gateway establishes a single point of failure and introduces an additional network hop, which could marginally impact request latency.

### **Option C: Monolithic Dopemux Service Merging Ingress and Canonical Systems**

This approach seeks maximum consolidation by merging the ingress gateway, the project management orchestrator (task-orchestrator), the chronicle ledger (dope-memory), and the codebase indexer (dope-context) into a single, massive monolithic application that holds all canonical truth and handles all routing internally.

* **Advantages**: This eliminates nearly all internal network hops, simplifying container deployment and reducing the operational footprint.  
* **Disadvantages**: This option catastrophically violates every established boundary constraint within the Dopemux ecosystem.1 It directly contradicts the explicit mandate that Project Management authority must remain split across systems 1, and it fatally conflates the durable, immutable ledger (dope-memory) with operational, volatile context (working-memory-assistant).1 From an architectural standpoint, this option is invalid and highly toxic to system integrity.

### **Architecture Options Comparison Table**

| Analytical Metric | Option A: Status Quo \+ Hooks | Option B: Gateway \+ Separate Authorities | Option C: Monolithic Service |
| :---- | :---- | :---- | :---- |
| **Boundary Adherence** | High (Maintains separation) | High (Enforces separation via network) | Critical Failure (Violates isolation) |
| **Cross-Agent Portability** | Low (Requires high local config) | High (Abstracted behind gateway) | High (Abstracted API) |
| **State Governance** | Fractured | Unified at Edge, Isolated at Core | Fatally Conflated |
| **Security & Auditing** | Poor (No centralized logging) | Excellent (Centralized choke point) | Excellent |
| **Implementation Risk** | Low | Moderate | High (Requires complete rewrite) |
| **Final Verdict** | **Reject** | **Recommended Strategy** | **Reject** |

## **Service-Tier Consolidation Policy**

The Dopemux workspace currently sustains an unsustainable sprawl of over thirty microservices. Many of these services suffer from overlapping operational scopes, naming ambiguities, and wholly unresolved authority.1 To implement the Option B Agent Gateway effectively and securely, the ecosystem must undergo aggressive, disciplined consolidation. Services must be categorized into distinct tiers, and subsequently merged, hidden, or explicitly isolated based upon their epistemic domain.

### **Tier 1: Canonical Domain Authorities**

* **Policy**: **Keep Separate**. These systems constitute the absolute bedrock of truth within the workspace. They must never be merged into the ingress gateway, as doing so violates the core boundary directives.1  
* **Target Services**: Leantime (canonical PM metadata), task-orchestrator (canonical workflow transitions), ConPort (canonical decisions and semantic retrieval), dope-memory (canonical SQLite chronicle ledger), dope-context (deterministic codebase retrieval), and repo-truth-extractor (the isolated audit runtime).1

### **Tier 1/2: Ingress and Control Layer**

* **Policy**: **Merge into Gateway**. Routing, proxying, model-selection, and operator CLI orchestration functions provide zero durable truth. They should be completely centralized to form the computational core of the new Agent Gateway.  
* **Target Services**: dopemux core (the operator CLI and config generation logic) and LiteLLM (the model routing proxy).1

### **Tier 2: Active Support Services**

* **Policy**: **Expose only via generated config/registry**. These services provide critical operational assistance and cognitive support but do not hold durable, canonical truth.1 Agents should interact with them solely via the gateway's unified MCP tool registry.  
* **Target Services**: working-memory-assistant (volatile snapshots and recovery) and the ADHD Engine (cognitive-state logic and workload management).1

### **Tier 2/3: Asynchronous Sidecars**

* **Policy**: **Keep Separate**. Sidecars handle highly specific background tasks. Merging them into the gateway would risk blocking the main asynchronous ingress event loop. However, their egress telemetry must be routed through the gateway.  
* **Target Services**: webhook-receiver and webhook-poller (services managing async job completion events from external providers).1

### **Tier 3: Adapters, Proxies, and Bridges**

* **Policy**: **Merge into Gateway**. Intermediate network layers add unnecessary latency and systemic confusion when deployed as standalone microservices. The translation and routing logic contained within these services must be absorbed directly into the Agent Gateway's internal middleware.  
* **Target Services**: dopecon-bridge (mediates safe PM operations), leantime-bridge, mcp-client utility, and the PAL reasoning proxy.1

### **Tier 3/4: Wrappers and Local Shims**

* **Policy**: **Keep Separate**. These must remain as ultra-lightweight bash or TypeScript scripts deployed directly to the operator's host machine. Their sole purpose is to interface with specific agent CLIs (e.g., executing within the .claude/settings.json lifecycle) and forward events to the gateway.3

### **Tier 4: Duplicate, Legacy, and Drifted Services**

* **Policy**: **Deprecate and Hide**. Unresolved authorities, duplicated implementations, and active-but-failing legacy paths must be aggressively excised from the workspace to prevent agents from hallucinating capabilities or corrupting internal state.1  
* **Target Services**: services/dope-query (legacy surface), the legacy task-orchestrator app.py path, the duplicate services/adhd-engine residue, services/serena (due to an unresolved canonical authority conflict with the docker/mcp-servers-source implementation), taskmaster, conport\_kg, activity-capture, and workspace-watcher.1

### **Service Consolidation Implementation Table**

| Service Tier & Category | Action Directive | Specific Target Services | Architectural Rationale |
| :---- | :---- | :---- | :---- |
| **Tier 1: Canonical Authority** | Keep Separate | Leantime, ConPort, task-orchestrator, dope-memory, dope-context | Must retain strict isolation to prevent domain corruption and multiple writer conflicts.1 |
| **Tier 1/2: Ingress / Control** | Merge into Gateway | dopemux core, LiteLLM | Unifies the control plane, simplifies API routing, and centralizes model management.1 |
| **Tier 2: Support Services** | Expose via Registry | working-memory-assistant, ADHD engine | Valid tools providing cognitive capabilities, but lacking canonical truth.1 |
| **Tier 2/3: Sidecars** | Keep Separate | webhook-receiver, webhook-poller | Background polling architectures should not block the main ingress thread.1 |
| **Tier 3: Adapters / Bridges** | Merge into Gateway | dopecon-bridge, leantime-bridge, mcp-client | Absorbing intermediate proxies into the gateway drastically reduces network hops.1 |
| **Tier 3/4: Wrappers / Shims** | Keep Separate | Vendor-specific host scripts | Required for client-side state machine interception.25 |
| **Tier 4: Legacy / Duplicates** | Deprecate & Hide | dope-query, serena (duplicate), taskmaster, legacy app.py | Eliminates highly dangerous "Truth Gaps" and ambiguous authority targets.1 |

## **Strategic Final Recommendation**

Based on the exhaustive analysis of runtime capabilities across five distinct vendors, established distributed architectural patterns, and the rigid systemic constraints governing the workspace, the following answers form the definitive strategic recommendation for the Dopemux multi-agent architecture.  
**What should be unified?** The ingress and control plane must be completely unified. Dopemux must architect and deploy a centralized **Agent Gateway** that consolidates Model Context Protocol (MCP) tool discovery, HTTP request routing, identity and authentication verification, token rate-limiting, and event normalization.32 This gateway absorbs all intermediate bridge and proxy services—such as dopecon-bridge and LiteLLM—standardizing all payload formatting before any traffic is permitted to traverse the network toward the backend systems.  
**What must remain separate?** Canonical backend authorities must remain strictly and fiercely isolated. Under no circumstances should the domain truth governing project metadata (Leantime), workflow transition states (task-orchestrator), durable historical ledgers (dope-memory), structured decision and semantic context (ConPort), or deterministic codebase retrieval (dope-context) be merged into a shared database or application layer.1 Furthermore, the local lifecycle shims—the lightweight scripts executing natively on the host operating system capturing PreToolUse or SessionStart events—must remain separate, edge-deployed utilities explicitly tailored to the proprietary state machines of Claude, Copilot, or Gemini.3  
**What should be hidden from agent-facing complexity?** All internal routing logic, backend fallback behaviors, and intermediate adapter translations must be completely abstracted. An autonomous AI agent querying the Dopemux workspace should observe a single, cohesive, highly robust MCP server exposed by the gateway. The agent should remain completely unaware that a leantime-bridge is secretly translating its payload into a GraphQL mutation, or that PM metadata and PM workflow state actually reside in physically disparate databases.1 Additionally, all fourteen Tier 4 legacy, duplicated, and drifted services must be completely hidden from the MCP registry and actively deprecated to close existing "Truth Gaps" and prevent agent hallucination.1  
**What architecture is most portable across vendors?** The most portable and future-proof architecture is the **Decoupled Gateway-Shim Model**. By pushing all complex system logic, authorization schemas, tool definitions, and retrieval operations behind a standardized HTTP MCP Gateway 3, the Dopemux backend becomes entirely agnostic to the choice of front-end LLM vendor. To handle highly specific, vendor-proprietary lifecycle events—which a remote network gateway fundamentally cannot observe—Dopemux will deploy vendor-specific, "dumb" lightweight shims (e.g., a .claude/settings.json hook script). The sole responsibility of these shims is to translate local CLI lifecycle events into standard HTTP REST payloads and push them asynchronously to the gateway's event ingestion queue.3

## **Source Appendix with Confidence Levels**

To satisfy the requirements for data provenance without utilizing a standard academic reference section, the following analysis categorizes the sources utilized throughout this architectural report, assigning confidence levels based on their origin and relevance to the established claims.

| Source Classification | Description of Artifacts | Confidence Level | Architectural Impact |
| :---- | :---- | :---- | :---- |
| **Primary System Definitions** | ARCHITECTURE.md, SERVICE\_CATALOG.md, SYSTEM\_Dopemux.md, system-boundaries.md.1 | **Absolute (High)** | Dictates the inviolable laws of the workspace. Defines the PM Plane split, the memory domains, and the absolute prohibition on conflating proxies with canonical truth. |
| **Vendor Technical Documentation** | Documentation for Claude Code, GitHub Copilot v1.109, Gemini CLI, and OpenAI Codex.3 | **High** | Provides the precise specifications for lifecycle hooks, MCP transports (stdio, HTTP, SSE), and event payload structures utilized to construct the Runtime Capability Matrix. |
| **Observational Architecture Case Studies** | claude-mem implementation details, API Gateway research (Kong, Gravitee), Async worker patterns.25 | **Moderate** | Synthesized from community consensus and emerging standards in multi-agent routing. Highly reliable in practice, but represents architectural interpretation rather than explicit vendor mandate. |
| **Experimental & Undocumented Tool Interfaces** | Google Antigravity Agent Skills formatting, OpenAI Codex Windows capabilities.17 | **Low** | Extrapolated from secondary community discussions, Reddit forums, and limited tutorial artifacts due to a lack of explicit, low-level API documentation. Findings should be treated as provisional. |
| **Dopemux Internal Audits** | TRUTH\_INTERFACES.md, TRUTH\_GAPS.md, PM\_PLANE.md.1 | **Absolute (High)** | Highlights internal contradictions, port conflicts, and legacy paths that strictly inform the Service-Tier Consolidation Policy. |

## **Risks, Unknowns, and Validation Needs**

While the Decoupled Gateway-Shim Model presents a structurally sound and highly scalable solution, several critical risk vectors and systemic unknowns require immediate experimental validation prior to full production deployment.

1. **Antigravity Extensibility Semantics**: The available documentation indicates that Google Antigravity relies heavily on non-deterministic "Agent Skills" guided by natural language reasoning, rather than executing strict, deterministic lifecycle hooks.21 Extensive empirical validation is required to determine if the Dopemux Agent Gateway can reliably inject pre-execution safety validations or context formatting into Antigravity's semantic loop without the presence of a dedicated, programmable hook API.  
2. **OpenAI Codex Asynchronous Limitations**: The OpenAI Codex Command Line Interface natively lacks support for asynchronous lifecycle hooks.17 If Codex is maintained as a critical-path runtime within the workspace, any telemetry gathering or event normalization passed to the gateway must inherently block the primary agent loop. Rigorous benchmarking is required to measure the latency degradation caused by forcing synchronous HTTP calls to the gateway, and to determine if this degradation unacceptably increases the rate of LLM execution timeouts.  
3. **Task-Orchestrator Path Contradictions**: The existing task-orchestrator service contains deeply contradictory runtime paths and unresolved port allocations, explicitly alternating between port 3014 and port 8000 depending on the deployment mechanism.1 Furthermore, the app.py legacy path remains an active threat to routing stability. These internal contradictions must be systematically remediated to ensure the newly proposed Agent Gateway possesses a stable, unambiguous backend target for all workflow state transitions.  
4. **Shim Lifecycle Maintenance**: Because the client-side shims are highly coupled to the proprietary state machines of vendors like Anthropic and Microsoft, any upstream changes to the lifecycle event names (e.g., modifying PreToolUse to BeforeToolUse) will instantly break the telemetry pipeline. The organization must establish an active monitoring protocol to validate shim functionality against new release candidates of the supported command-line interfaces.

#### **Works cited**

1. TRUTH\_GAPS.md  
2. Gemini CLI and MCP Integration for Data Engineering Workflows | by Dinesh Shankar, accessed April 22, 2026, [https://dishanka.medium.com/gemini-cli-and-mcp-integration-for-data-engineering-workflows-2ad021bb8819](https://dishanka.medium.com/gemini-cli-and-mcp-integration-for-data-engineering-workflows-2ad021bb8819)  
3. Extend Claude Code \- Claude Code Docs, accessed April 22, 2026, [https://code.claude.com/docs/en/features-overview](https://code.claude.com/docs/en/features-overview)  
4. Hooks – Codex | OpenAI Developers, accessed April 22, 2026, [https://developers.openai.com/codex/hooks](https://developers.openai.com/codex/hooks)  
5. Tailor Gemini CLI to your workflow with hooks \- Google Developers ..., accessed April 22, 2026, [https://developers.googleblog.com/tailor-gemini-cli-to-your-workflow-with-hooks/](https://developers.googleblog.com/tailor-gemini-cli-to-your-workflow-with-hooks/)  
6. January 2026 (version 1.109) \- Visual Studio Code, accessed April 22, 2026, [https://code.visualstudio.com/updates/v1\_109](https://code.visualstudio.com/updates/v1_109)  
7. Claude Code SDK Skill \- Extensibility & Configuration \- MCP Market, accessed April 22, 2026, [https://mcpmarket.com/tools/skills/claude-code-sdk-reference](https://mcpmarket.com/tools/skills/claude-code-sdk-reference)  
8. How Claude Code works \- Claude Code Docs, accessed April 22, 2026, [https://code.claude.com/docs/en/how-claude-code-works](https://code.claude.com/docs/en/how-claude-code-works)  
9. Working with hooks \- Use Copilot SDK \- GitHub Docs, accessed April 22, 2026, [https://docs.github.com/en/copilot/how-tos/copilot-sdk/use-copilot-sdk/working-with-hooks](https://docs.github.com/en/copilot/how-tos/copilot-sdk/use-copilot-sdk/working-with-hooks)  
10. GitHub Copilot CLI command reference, accessed April 22, 2026, [https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference)  
11. Visual Studio SDK APIs for Copilot Agent Lifecycle Monitoring, accessed April 22, 2026, [https://developercommunity.microsoft.com/t/Visual-Studio-SDK-APIs-for-Copilot-Agent/10941488](https://developercommunity.microsoft.com/t/Visual-Studio-SDK-APIs-for-Copilot-Agent/10941488)  
12. Google Adds Hooks to Gemini CLI for Customized AI Workflows \- DevOps.com, accessed April 22, 2026, [https://devops.com/google-adds-hooks-to-gemini-cli-for-customized-ai-workflows/](https://devops.com/google-adds-hooks-to-gemini-cli-for-customized-ai-workflows/)  
13. Local development guide | Gemini CLI, accessed April 22, 2026, [https://geminicli.com/docs/local-development/](https://geminicli.com/docs/local-development/)  
14. addyosmani/gemini-cli-tips \- GitHub, accessed April 22, 2026, [https://github.com/addyosmani/gemini-cli-tips](https://github.com/addyosmani/gemini-cli-tips)  
15. MCP servers with Gemini CLI, accessed April 22, 2026, [https://geminicli.com/docs/tools/mcp-server/](https://geminicli.com/docs/tools/mcp-server/)  
16. Codex CLI \- OpenAI Developers, accessed April 22, 2026, [https://developers.openai.com/codex/cli](https://developers.openai.com/codex/cli)  
17. Codex CLI: The Definitive Technical Reference \- Blake Crosley, accessed April 22, 2026, [https://blakecrosley.com/guides/codex](https://blakecrosley.com/guides/codex)  
18. OpenAI Codex CLI: Complete Getting Started Guide \- DeployHQ, accessed April 22, 2026, [https://www.deployhq.com/blog/getting-started-with-openai-codex-cli-ai-powered-code-generation-from-your-terminal](https://www.deployhq.com/blog/getting-started-with-openai-codex-cli-ai-powered-code-generation-from-your-terminal)  
19. Google Antigravity Documentation, accessed April 22, 2026, [https://antigravity.google/docs/home](https://antigravity.google/docs/home)  
20. Tutorial : Getting Started with Google Antigravity | by Romin Irani \- Medium, accessed April 22, 2026, [https://medium.com/google-cloud/tutorial-getting-started-with-google-antigravity-b5cc74c103c2](https://medium.com/google-cloud/tutorial-getting-started-with-google-antigravity-b5cc74c103c2)  
21. Share your best Google Antigravity Skills, Rules & Workflows. : r/google\_antigravity \- Reddit, accessed April 22, 2026, [https://www.reddit.com/r/google\_antigravity/comments/1r3hlis/share\_your\_best\_google\_antigravity\_skills\_rules/](https://www.reddit.com/r/google_antigravity/comments/1r3hlis/share_your_best_google_antigravity_skills_rules/)  
22. Antigravity sub agents \- Google AI Developers Forum, accessed April 22, 2026, [https://discuss.ai.google.dev/t/antigravity-sub-agents/114381](https://discuss.ai.google.dev/t/antigravity-sub-agents/114381)  
23. Antigravity vs Windsurf: Google Agent-First or Cognition Cascade? | Augment Code, accessed April 22, 2026, [https://www.augmentcode.com/tools/antigravity-vs-windsurf-comparison](https://www.augmentcode.com/tools/antigravity-vs-windsurf-comparison)  
24. Claude-Mem Guide: Persistent Memory for Claude Code \- DataCamp, accessed April 22, 2026, [https://www.datacamp.com/tutorial/claude-mem-guide](https://www.datacamp.com/tutorial/claude-mem-guide)  
25. Architecture Overview \- Claude-Mem, accessed April 22, 2026, [https://docs.claude-mem.ai/architecture/overview](https://docs.claude-mem.ai/architecture/overview)  
26. Introducing MCP Backpack: Persistent, Portable Memory for AI Coding Agents \- Medium, accessed April 22, 2026, [https://medium.com/codex/introducing-mcp-backpack-persistent-portable-memory-for-ai-coding-agents-87eea16eaa54](https://medium.com/codex/introducing-mcp-backpack-persistent-portable-memory-for-ai-coding-agents-87eea16eaa54)  
27. Multi-Agent System Patterns: Architectures, Roles & Design Guide \- Medium, accessed April 22, 2026, [https://medium.com/@mjgmario/multi-agent-system-patterns-a-unified-guide-to-designing-agentic-architectures-04bb31ab9c41](https://medium.com/@mjgmario/multi-agent-system-patterns-a-unified-guide-to-designing-agentic-architectures-04bb31ab9c41)  
28. Model Context Protocol (MCP) and the MCP Gateway: Concepts, Architecture, and Case Studies | by ByteBridge, accessed April 22, 2026, [https://bytebridge.medium.com/model-context-protocol-mcp-and-the-mcp-gateway-concepts-architecture-and-case-studies-3470b6d549a1](https://bytebridge.medium.com/model-context-protocol-mcp-and-the-mcp-gateway-concepts-architecture-and-case-studies-3470b6d549a1)  
29. MCP Gateways Explained, accessed April 22, 2026, [https://mcpmanager.ai/blog/mcp-gateway/](https://mcpmanager.ai/blog/mcp-gateway/)  
30. MCP Aggregation, Gateway, and Proxy Tools: State of the Ecosystem (Q1 2026), accessed April 22, 2026, [https://www.heyitworks.tech/blog/mcp-aggregation-gateway-proxy-tools-q1-2026](https://www.heyitworks.tech/blog/mcp-aggregation-gateway-proxy-tools-q1-2026)  
31. Bifrost Alternatives: Top Tools You Can Consider in 2026, accessed April 22, 2026, [https://www.truefoundry.com/blog/bifrost-alternative-mcp-gateway](https://www.truefoundry.com/blog/bifrost-alternative-mcp-gateway)  
32. MCP Architecture Patterns for Production-Grade Agents \- FlowZap, accessed April 22, 2026, [https://flowzap.xyz/blog/mcp-architecture-patterns-for-production-grade-agents](https://flowzap.xyz/blog/mcp-architecture-patterns-for-production-grade-agents)  
33. Kong AI/MCP Gateway and Kong MCP Server Technical Breakdown, accessed April 22, 2026, [https://konghq.com/blog/engineering/ai-gateway-mcp-gateway-mcp-server-breakdown](https://konghq.com/blog/engineering/ai-gateway-mcp-gateway-mcp-server-breakdown)  
34. Four Design Patterns for Event-Driven, Multi-Agent Systems \- Confluent, accessed April 22, 2026, [https://www.confluent.io/blog/event-driven-multi-agent-systems/](https://www.confluent.io/blog/event-driven-multi-agent-systems/)  
35. Supercharge Cortex Code CLI \- A Practical Guide to Skills, SubAgents, Hooks and MCP, accessed April 22, 2026, [https://dev.to/tsubasa\_tech/supercharge-cortex-code-cli-a-practical-guide-to-skills-subagents-hooks-and-mcp-lc8](https://dev.to/tsubasa_tech/supercharge-cortex-code-cli-a-practical-guide-to-skills-subagents-hooks-and-mcp-lc8)