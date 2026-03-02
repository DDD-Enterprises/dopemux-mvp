# Deep technical integration architecture for Leantime MCP and Claude-Task-Master on dopemux

This comprehensive technical analysis explores the integration architecture between Leantime MCP Server and Claude-Task-Master for creating a sophisticated two-tier task management system on the dopemux platform. The research reveals both tools implement Model Context Protocol (MCP) with complementary capabilities - Leantime handling strategic project management while Claude-Task-Master manages granular code implementation tasks.

## Leantime MCP Server architecture and capabilities

The Leantime MCP Server consists of dual components: a PHP server plugin integrated directly into Leantime's core and a TypeScript client bridge for MCP connectivity. The server exposes comprehensive project management functionality through JSON-RPC APIs accessible via MCP tools.

**Core MCP tools available through Leantime** include ticket management (`leantime.rpc.tickets.getTicket`, `addTicket`, `getAllTickets`), project operations (`leantime.rpc.projects.getAllProjects`, `getProject`), milestone tracking, and timesheet management. The server implements MCP Protocol 2025-03-26 with backward compatibility, supporting both STDIO and HTTP transports with Server-Sent Events for real-time updates.

**Authentication utilizes multiple mechanisms**: Personal Access Tokens (recommended for user-specific queries), standard API keys with format `lt_{username}_{hash}`, Bearer token headers, and X-API-Key alternatives. The MCP endpoint is accessible at `https://YOURLEANTIMEURL/mcp` for HTTP transport or via command line using `php /path-to-leantime/bin/leantime lt-mcp:start --transport=stdio --token=YOUR_TOKEN`.

**Data schemas follow structured formats** with tasks containing id, headline, type, description, projectId, userId, status (numeric), priority, storypoints, sprint reference, and milestone associations. The TypeScript bridge implements retry logic with exponential backoff, smart caching for tool/resource lists with 5-minute TTL, and automatic session management for stateful interactions.

## Claude-Task-Master implementation deep dive

Claude-Task-Master, built on FastMCP v1.20.5, provides sophisticated AI-driven task management specifically designed for development workflows. The server architecture centers around a `TaskMasterMCPServer` class that exposes comprehensive task management tools.

**The MCP tool suite includes** `get_tasks` for retrieving task lists, `next_task` for finding actionable items, `parse_prd` for automatic PRD document analysis, `expand_task` for subtask decomposition, `set_status` and `update_task` for state management, `research` for AI-powered information gathering, and `analyze_complexity` for task estimation. All tools follow RESTful patterns with lean JSON outputs optimized for context efficiency.

**Task structure employs a hierarchical JSON schema** with metadata containing project name, version, PRD source, and timestamps. Individual tasks include id, title, description, status (pending/in_progress/done/deferred/cancelled), dependencies array, priority levels, and nested subtasks. Version 0.16.2+ introduces tagged task systems supporting branch-specific contexts like master and feature branches.

**State management uses a multi-file approach** with `.taskmaster/config.json` for configuration, `.taskmaster/tasks/tasks.json` for task persistence, individual task files in `.taskmaster/tasks/`, and `.cursor/mcp.json` for MCP-specific settings. The system supports multiple AI providers (Anthropic, OpenAI, Perplexity) with configurable models for different operations.

## Two-tier integration architecture patterns

The integration between Leantime's strategic planning and Claude-Task-Master's tactical execution requires sophisticated synchronization patterns addressing different data models and operational contexts.

**Hierarchical task decomposition** maps Leantime projects and milestones to Claude-Task-Master epics and implementation tasks. A `TaskMappingService` converts Leantime milestones into Task-Master epics, translating priority levels, extracting acceptance criteria from goals, and maintaining dependency relationships. Reverse mapping aggregates Task-Master completion status back to Leantime progress percentages.

**Event-driven synchronization** employs an `MCPEventBroker` that publishes events to local queues and notifies subscribed servers. Status changes in Task-Master trigger corresponding Leantime milestone updates, while Leantime modifications cascade to Task-Master tasks. The system implements conflict detection for milestone status mismatches, priority divergences, and dependency cycles.

**Structured handoff protocols** define the transition from planning to implementation. A `TaskHandoffManager` validates handoff readiness, creates implementation contexts in Task-Master from Leantime milestones, updates Leantime with implementation references, and establishes bidirectional progress monitoring. The handoff state machine manages transitions through ready, in_progress, completed, blocked, and failed states.

## Dopemux workflow orchestration implementation

The dopemux platform orchestrates complex workflows between Leantime's backlog and Claude-Task-Master's execution engine through sophisticated patterns, though no existing "dopemux" implementation was found in current sources.

**Agent-based task selection** implements pull-based orchestration where agents periodically query Leantime for tasks in "Ready" state. The system uses webhook notifications for status changes and priority-based selection algorithms considering dependencies and resource availability. Tasks flow from Leantime's Kanban boards through orchestrator logic into Claude-Task-Master's execution queue.

**Task decomposition follows the orchestrator-workers pattern** where an orchestrator LLM analyzes complex requests and generates subtasks, worker agents receive focused assignments, and a synthesizer combines outputs. Claude-Task-Master's PRD parsing automatically generates structured tasks with complexity analysis and intelligent dependency sequencing.

**Routing logic** classifies tasks as code-related (implementation, API development, testing, deployment) or non-code (planning, communications, documentation review). An AI-powered classifier uses content analysis, keyword matching, and dependency grouping to determine optimal routing. Code tasks route to Claude-Task-Master while business tasks remain in Leantime.

**Error handling implements hierarchical recovery** with automatic retry using exponential backoff for transient failures, fallback models for resilience, human escalation for complex issues, and compensation actions for rollback scenarios. The saga pattern manages multi-step operations with choreography-based coordination for distributed transactions.

## Technical implementation specifications

The integration requires sophisticated connection management, caching strategies, and performance optimizations to handle enterprise workloads effectively.

**MCP server connection management** utilizes session-based architecture with in-memory storage for single instances or Redis for distributed deployments. The implementation supports dual protocols (Streamable HTTP and legacy HTTP+SSE) with automatic session cleanup and health check mechanisms. Connection pooling limits concurrent connections while maintaining session persistence across reconnections.

**Multi-level caching architecture** implements L1 memory cache for fastest access, L2 disk cache for persistence, and L3 semantic cache for similarity matching. Token-aware caching tracks hit rates and calculates cost savings, with configurable TTL and automatic cleanup. The system caches tool definitions, response data, and semantic embeddings for performance optimization.

**Transaction patterns** employ distributed transaction coordinators for multi-server operations. Two-phase commit ensures consistency with prepare and commit phases. The saga pattern handles long-running operations with compensating transactions for rollback. Each step includes explicit compensation logic maintaining atomicity across distributed systems.

**Context passing mechanisms** aggregate data from multiple MCP servers through federated resource queries. A `MultiServerContext` class merges resources, tools, and prompts from different servers while maintaining metadata relationships. Cross-server resource sharing uses namespaced URIs preventing conflicts.

## UX design patterns and developer experience

The integration emphasizes developer productivity through intuitive interfaces and comprehensive feedback mechanisms.

**Visual progress tracking** provides real-time execution timelines showing step-by-step progress with active state highlighting. Multi-system dashboards aggregate progress across Leantime and Task-Master, displaying overall completion percentages, system dependencies, blockers, and critical path analysis. WebSocket connections stream live updates to connected clients.

**Task selection interfaces** implement auto-completion with history-based, context-aware, and semantic suggestions. Interactive selectors provide searchable, grouped options with keyboard shortcuts. Tool discovery features dynamic documentation generation with usage examples and interactive demos for testing.

**Notification systems** use event-driven architectures with priority-based routing to multiple channels. Subscribers configure channel preferences, urgency thresholds, and content filters. The system formats notifications with titles, messages, action buttons, and contextual information based on event types.

**Manual intervention points** incorporate approval workflows for high-risk operations. Human-in-the-loop patterns pause execution awaiting manual decisions. Override mechanisms allow authorized users to modify automated decisions with justification requirements and audit logging. Emergency override systems provide break-glass functionality for critical situations.

**Performance optimizations** include async processing for non-blocking operations, HTTP/2 support with connection reuse, prepared SQL statements with query result caching, and background job queues for heavy computations. The architecture scales horizontally through microservices with independent scaling, container orchestration for dynamic resources, and message queue clustering for high availability.

## Conclusion

The deep technical integration between Leantime MCP Server and Claude-Task-Master creates a powerful two-tier system bridging strategic project management with AI-driven development execution. The architecture leverages MCP's standardized protocol while addressing the unique requirements of each system through sophisticated mapping, synchronization, and orchestration patterns. Implementation success depends on robust error handling, comprehensive state management, and thoughtful UX design that maintains developer productivity while automating complex workflows. The dopemux platform can leverage these patterns to create a seamless flow from high-level planning through granular implementation, enabling organizations to maintain strategic oversight while accelerating development velocity through AI-powered automation.
