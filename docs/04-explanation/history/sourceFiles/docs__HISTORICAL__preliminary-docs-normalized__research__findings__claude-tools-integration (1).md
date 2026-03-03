# Integrating Claude tools into dopemux CLI

## Critical licensing constraint blocks direct integration

The most significant finding from this research is that **Claude Code cannot be directly integrated into dopemux** due to its Business Source License (BUSL-1.1), which explicitly prohibits redistribution for competitive products and integration into commercial applications without a commercial license. The source code, while partially observable through transpiled versions, cannot be legally used for production purposes. This fundamental constraint shapes the entire integration strategy.

Instead of direct embedding, dopemux must use Claude Code through subprocess calls or the Anthropic API directly. The recommended approach is to implement similar UI patterns and functionality while respecting the licensing restrictions, potentially transitioning to full integration if the license changes to open source after its typical 4-year transition period.

## SuperClaude and claude-flow offer complementary but conflicting approaches

### Performance and architecture comparison reveals clear winner

Claude-flow emerges as the superior choice for production multi-agent systems with its **84.8% SWE-Bench solve rate** and native support for up to 64 specialized agents running in parallel. Its enterprise-grade architecture includes SQLite memory persistence, 87 MCP tools for swarm orchestration, and WASM SIMD acceleration delivering 2.8-4.4x speed improvements. SuperClaude, with 15.2k GitHub stars, focuses on behavioral enhancement through 9 cognitive personas and template-driven commands, achieving 70% token reduction but lacking true multi-agent parallelism.

The frameworks are **mutually exclusive** due to architectural conflicts - both modify Claude Code's behavior through different mechanisms (SuperClaude uses configuration files in ~/.claude/ while claude-flow uses MCP protocol integration). However, they can be used sequentially: SuperClaude for initial prototyping due to its simpler setup, then migrating to claude-flow for production deployment requiring parallel agent coordination.

### Integration compatibility requires careful orchestration

While the three tools cannot run simultaneously, they can work together with proper configuration management. The recommended installation sequence is crucial: SuperClaude first to establish base configuration, then claude-flow with the `--force` flag to handle existing setups, followed by comprehensive integration testing. Key technical requirements include Node.js 18+, proper namespace management to prevent command conflicts, and unified permission strategies using `--dangerously-skip-permissions` flags.

MCP server conflicts present the primary challenge, as multiple servers with identical tool names cause unpredictable behavior in Claude Code. The solution involves prefixing tools (e.g., `cf_` for claude-flow, `sc_` for SuperClaude) and implementing scoped MCP server configurations. Combined token optimization can achieve up to 60% reduction when both systems' optimization strategies work together.

## Technical implementation demands modular architecture

### Modular monolithic design with plugin system proves optimal

The recommended architecture follows a **modular monolithic approach with plugin-based extensibility**, avoiding microservices complexity while maintaining flexibility. This design implements the Command Pattern for CLI operations, utilizing event-driven hooks for tool coordination. The single deployable binary ensures fast startup times essential for CLI responsiveness, while the plugin interface allows each tool to operate in isolation with clear boundaries.

The architecture employs multiple design patterns: Facade pattern for unified interfaces, Observer pattern for event handling, and Strategy pattern for swappable implementations. A sophisticated hook system manages extensibility with pre-defined events (startup, shutdown, before/after-command) and priority-based execution. Conflict resolution uses namespace management with prefixed commands (claude-code:edit, flow:run) and priority-based command resolution when conflicts occur.

### Comprehensive technical stack leverages Go ecosystem

The implementation uses Go as the primary language, following industry leaders like Docker and Kubernetes for CLI development. Key components include Cobra for command hierarchies, Viper for configuration management, and GoReleaser for multi-platform builds. The system implements lazy loading for tool integrations, connection pooling for network efficiency, and parallel tool execution for concurrent operations.

Process isolation prevents conflicts through containerization or systemd sandboxing, with resource limits on CPU, memory, and network access. The configuration hierarchy supports multiple sources (default, system, user, project, environment, CLI args) with proper precedence rules. Authentication unifies across all three tools using secure OS keyring storage for API keys.

## RAG implementation achieves 49-67% retrieval improvement

### Vector database strategy optimizes for code search

Qdrant emerges as the recommended production vector database due to its Rust-based performance and cost-effectiveness, with Pinecone as an enterprise backup option. The system implements Anthropic's Contextual Retrieval innovation, combining contextual embeddings with contextual BM25 for optimal accuracy. This dual-method approach reduces retrieval failures by 49-67% while prompt caching reduces latency by over 2x and costs by up to 90%.

The embedding strategy uses specialized models: Microsoft UniXcoder-base and Voyage Code-2 for code semantics, with Voyage AI text-embedding-3 and Gemini Text-Embedding-004 for general text. Late chunking processes entire documents before token-level chunking, preserving context better than traditional methods. Contextual prefixes of 50-100 tokens reduce failures by 35%, while batch processing in groups of 100-500 items optimizes cost efficiency.

### Code indexing leverages AST analysis

Tree-sitter provides multi-language AST parsing across 40+ languages, with LSP integrations for accurate symbol resolution. The system implements Git-aware change detection for incremental updates, minimizing reindexing overhead. Adaptive chunking maintains semantic boundaries: 200-800 tokens for code functions, 400-1200 for documentation, with 20% overlap for code and 10% for documentation.

A multi-level caching hierarchy optimizes performance: L1 in-memory cache (Redis) with 1-hour TTL for query embeddings, L2 SSD cache for document embeddings with 24-hour TTL, and L3 cold storage for historical data. Memory management includes lazy loading of embeddings, 4-bit quantization for storage efficiency, and automatic garbage collection of unused cached embeddings. The system targets <500ms query latency for 95th percentile and <30 minutes indexing time for 100k files.

## Implementation roadmap spans 16 weeks with phased delivery

### Phase structure ensures iterative development

The roadmap divides into five distinct phases, each building on previous work. **Phase 1 (Weeks 1-3)** establishes the foundation with core CLI architecture using Go, Cobra framework, and configuration management. **Phase 2 (Weeks 4-7)** integrates individual tools through SDK generation and subprocess communication. **Phase 3 (Weeks 8-10)** implements inter-tool communication via event-driven architecture and shared context management.

**Phase 4 (Weeks 11-13)** develops the unified interface with command harmonization and TUI features. **Phase 5 (Weeks 14-16)** focuses on comprehensive testing, security implementation, and CI/CD pipeline setup. Each phase includes specific technical deliverables, risk assessments, and mitigation strategies.

### Security and testing drive quality assurance

The security implementation employs systemd features for process isolation, with configurable network policies and comprehensive audit logging. Sandboxing configuration allows fine-grained control over file system access, memory limits, and CPU quotas. API key management uses secure OS keyring storage, preventing credential exposure in configuration files.

Testing strategy targets 90%+ unit test coverage with comprehensive integration and end-to-end testing. The CI/CD pipeline uses GitHub Actions for multi-platform testing (Ubuntu, Windows, macOS) with automated security scanning using tools like Trivy and SAST-scan. Performance benchmarking ensures CLI startup under 500ms and average command execution under 2 seconds.

## Architecture patterns enable future extensibility

The plugin system allows third-party tool integrations beyond the initial three Claude tools, with a microkernel architecture supporting dynamic plugin loading. The command router implements slash command support with autocomplete functionality, while the middleware stack enables request preprocessing and modification. The hook system provides extension points throughout the execution lifecycle, allowing custom behaviors without core modifications.

Configuration management supports XDG compliance with hierarchical settings (global, tool-specific, project-level). The system implements graceful degradation when tools are unavailable, with circuit breaker patterns for external API calls and retry mechanisms with exponential backoff. Transaction-like semantics ensure consistency for multi-tool operations, with checkpoint-based recovery for long-running workflows.

This comprehensive feasibility analysis confirms that building the dopemux CLI platform is **technically achievable but legally constrained**. The recommended approach uses subprocess integration for Claude Code while fully integrating claude-flow for production multi-agent capabilities. The 16-week implementation timeline provides a realistic path to a functional, secure, and extensible CLI platform that respects licensing requirements while delivering powerful unified functionality.
