# Glossary

**Version**: 1.0
**Status**: Complete
**Last Updated**: 2025-09-18

## Overview

This glossary provides definitions for technical terms, ADHD-related concepts, and system-specific terminology used throughout the Dopemux architecture documentation. Terms are organized alphabetically within categories for easy reference.

---

## Technical Architecture Terms

### A

**ADR (Architecture Decision Record)**
: A structured document capturing an important architectural decision, its context, rationale, and consequences. Dopemux uses ADRs to document all significant system design choices.

**Agent Orchestration**
: The systematic coordination and management of multiple AI agents working together to accomplish complex tasks. In Dopemux, this includes the Claude-flow 64-agent system and MCP server coordination.

**Async Communication**
: Communication pattern where the sender doesn't wait for an immediate response from the receiver. Critical for maintaining ADHD-accommodated sub-50ms response times in Dopemux.

### B

**Byzantine Fault Tolerance (BFT)**
: A property of distributed systems that can continue operating correctly even when some components fail or behave maliciously. Used in Dopemux agent coordination.

### C

**Circuit Breaker Pattern**
: A design pattern that prevents cascading failures by temporarily disabling calls to a failing service. Dopemux uses circuit breakers for MCP server resilience.

**Context7**
: Primary MCP server for official documentation and API references. Critical component that must be queried first for all code-related work in Dopemux.

**ConPort**
: MCP server for project-specific memory storage, including decisions, notes, and implementation history.

### D

**Dopemux**
: The world's first comprehensively ADHD-accommodated development platform, combining software development tools with personal life automation through multi-agent AI orchestration.

### E

**EXA**
: Web research MCP server used as fallback when Context7 lacks required information. Provides community solutions and current best practices.

### F

**Fallback Chain**
: Sequence of alternative services or methods used when primary systems fail. Example: Context7 → EXA → Local Documentation → Manual Research.

### H

**Hub-and-Spoke Architecture**
: Dopemux's core architectural pattern with a central orchestration hub coordinating specialized spoke services. Provides centralized control while enabling independent scaling.

**Hyperfocus**
: ADHD-related state of intense concentration that can lead to losing track of time and neglecting other needs. Dopemux provides hyperfocus management features.

### L

**Letta Framework**
: Primary memory management system providing hierarchical memory blocks with unlimited context within fixed token limits. Achieves 74% accuracy on LoCoMo benchmarks.

**LoCoMo (Long Context Memory)**
: Benchmark for measuring memory system accuracy in preserving and retrieving context across long conversations and extended time periods.

### M

**MCP (Model Context Protocol)**
: Standardized protocol for AI model integration with external tools and services. Dopemux orchestrates 12+ MCP servers for different capabilities.

**Multi-Model Orchestration**
: Coordination of multiple AI models (Claude, GPT, Gemini, etc.) to leverage their different strengths for complex problem-solving.

### O

**OpenMemory**
: Cross-session personal knowledge base for user preferences, patterns, and long-term facts. Complements ConPort's project-specific memory.

**Orchestration Hub**
: Central coordination component in Dopemux's hub-and-spoke architecture. Manages message routing, component lifecycle, and system state.

### P

**PBFT (Practical Byzantine Fault Tolerance)**
: Consensus algorithm used in Dopemux for agent coordination, ensuring system reliability even when some agents fail or provide conflicting information.

### Q

**Quality Gate**
: Automated checkpoint that validates code quality, security, and compliance requirements before allowing progression to next development phase.

### R

**RSD (Rejection Sensitive Dysphoria)**
: ADHD-related condition involving extreme emotional sensitivity to perceived rejection or criticism. Dopemux feedback systems are designed to accommodate RSD.

### S

**Sequential-Thinking**
: MCP server providing multi-step reasoning and systematic problem analysis. Used for complex debugging and architectural decisions.

**Serena**
: MCP server providing LSP (Language Server Protocol) functionality, symbol operations, and project memory for code navigation and refactoring.

**Slice-Based Development**
: Systematic 8-command workflow for feature development: bootstrap → research → story → plan → implement → debug → ship → switch.

**Spoke Service**
: Specialized microservice in Dopemux's hub-and-spoke architecture. Each spoke handles specific domain functionality (memory, AI, security, etc.).

### T

**Token Optimization**
: Strategies for reducing AI model token consumption while maintaining functionality. Dopemux achieves 15-25% token reduction through smart query patterns.

**tmux**
: Terminal multiplexer providing session persistence and window management. Foundation for Dopemux's terminal-based ADHD-accommodated interface.

### Z

**Zen**
: Multi-model AI orchestration MCP server that coordinates conversations across different AI models (Gemini, GPT, Claude, etc.) for complex analysis and consensus.

---

## ADHD and Neurodiversity Terms

### A

**ADHD (Attention Deficit Hyperactivity Disorder)**
: Neurodevelopmental condition affecting attention, impulse control, and executive function. Primary target demographic for Dopemux accommodations.

**Accommodation**
: Modification or adjustment to environment, task, or approach that enables individuals with disabilities to participate fully. Dopemux provides comprehensive ADHD accommodations.

**Attention Management**
: Systematic approach to directing and sustaining attention effectively. Includes strategies for minimizing distractions and preserving focus.

### C

**Cognitive Load**
: Amount of mental effort being used in working memory. Dopemux aims to reduce cognitive load through intuitive interfaces and automated processes.

**Context Switching**
: Mental process of shifting attention from one task to another. Particularly challenging for ADHD individuals; Dopemux minimizes switching overhead.

### E

**Executive Function**
: Set of mental skills including working memory, cognitive flexibility, and inhibitory control. Often impaired in ADHD; Dopemux provides executive function support.

**Effect Size**
: Statistical measure of the magnitude of a difference or relationship. Dopemux accommodations show effect sizes of d=0.56-2.03 for various ADHD symptoms.

### H

**Hyperfocus**
: ADHD state of intense concentration on preferred activities, often leading to time blindness and neglect of other needs. Can be both advantage and challenge.

### N

**Neurodivergent**
: Having a brain that functions differently from typical expectations. Includes ADHD, autism, dyslexia, and other neurological variations.

**Neurotypical**
: Having neurological development and functioning considered typical or standard.

### R

**Rejection Sensitive Dysphoria (RSD)**
: Extreme emotional sensitivity to perceived rejection, criticism, or failure. Common in ADHD; affects 98% of individuals with ADHD.

### T

**Time Blindness**
: Difficulty accurately perceiving the passage of time. Common ADHD symptom that Dopemux addresses through time awareness features.

### W

**Working Memory**
: Cognitive system responsible for temporarily holding and processing information. Often impaired in ADHD (g=0.56 effect size improvement possible with tools).

---

## System-Specific Terms

### A

**Adaptive Security Learning**
: Dopemux security system that learns project-specific safe patterns to reduce security friction over time while maintaining protection.

### B

**Bootstrap Command**
: First step in slice-based development workflow. Gathers initial context, identifies relevant files, and proposes implementation plan.

### C

**Claude-flow**
: 64-agent hive-mind system achieving 84.8% SWE-Bench solve rates through specialized agent coordination and consensus algorithms.

### D

**Documentation-Driven Development**
: Dopemux development philosophy requiring Context7 documentation queries before any code implementation to ensure accuracy and best practices.

### G

**Graceful Degradation**
: System behavior that maintains partial functionality when components fail. Dopemux gracefully degrades to local-only mode when external services unavailable.

### M

**Memory Block**
: Hierarchical data structure in Letta framework for organizing and retrieving contextual information across different time scales and scopes.

### P

**Privacy Validation**
: Automated scanning and protection system that prevents exposure of personal identifiable information (PII) and sensitive data in AI responses and storage.

### Q

**Quality Gate Hook**
: Automated validation system that runs comprehensive checks (testing, linting, security, privacy) after code changes to ensure quality standards.

### R

**Ratatui**
: Rust library for building terminal user interfaces. Used in Dopemux for creating ADHD-accommodated terminal layouts and visualizations.

### S

**Security Audit Log**
: Comprehensive record of all security decisions, pattern learning, and policy enforcement actions for compliance and debugging purposes.

**Session Persistence**
: Capability to save and restore complete development session state, including context, decisions, and mental models across interruptions.

### T

**Terminal IDE**
: Integrated development environment built for terminal/command-line use. Dopemux implements a terminal IDE optimized for ADHD accommodation.

**Three-Tier Memory**
: Dopemux memory architecture with short-term (current session), working (recent context), and long-term (archived decisions) storage levels.

### V

**Visual Workflow UI**
: ASCII art-based pipeline visualization in terminal showing development workflow progression and current status.

---

## Acronyms and Abbreviations

**ADR** - Architecture Decision Record
**ADHD** - Attention Deficit Hyperactivity Disorder
**API** - Application Programming Interface
**ASCII** - American Standard Code for Information Interchange
**BFT** - Byzantine Fault Tolerance
**CLI** - Command Line Interface
**GDPR** - General Data Protection Regulation
**HIPAA** - Health Insurance Portability and Accountability Act
**IDE** - Integrated Development Environment
**JSON** - JavaScript Object Notation
**JSONL** - JSON Lines
**LSP** - Language Server Protocol
**MCP** - Model Context Protocol
**MVP** - Minimum Viable Product
**PBFT** - Practical Byzantine Fault Tolerance
**PII** - Personally Identifiable Information
**PRD** - Product Requirements Document
**QoS** - Quality of Service
**REST** - Representational State Transfer
**RSD** - Rejection Sensitive Dysphoria
**SLA** - Service Level Agreement
**SQLite** - SQL Database Engine
**TDD** - Test-Driven Development
**TUI** - Terminal User Interface
**UX** - User Experience
**WebRTC** - Web Real-Time Communication
**YAML** - YAML Ain't Markup Language

---

## Units and Measurements

**Latency Targets**
- ADHD-critical operations: <50ms
- AI responses: <2s
- Memory retrieval: <100ms
- Session restoration: <2s

**Performance Metrics**
- SWE-Bench solve rate: 84.8%
- LoCoMo accuracy: 74%
- Token reduction: 15-25%
- Context switching reduction: 89%
- Test coverage requirement: ≥90%

**Effect Sizes (Cohen's d)**
- Working memory improvement: d=0.56
- Attention deficits: d=1.62-2.03
- Executive function support: d=0.8-1.2
- Overall ADHD accommodation effectiveness: d=1.2-1.8

---

## References and Standards

**Architecture Frameworks**
- arc42: Architecture documentation template
- C4 Model: Software architecture visualization
- Diátaxis: Documentation system framework

**Development Standards**
- Model Context Protocol (MCP)
- Language Server Protocol (LSP)
- OAuth 2.0 with PKCE
- OpenTelemetry observability
- JSON-RPC communication protocol

**Compliance Frameworks**
- GDPR (General Data Protection Regulation)
- HIPAA (Health Insurance Portability and Accountability Act)
- SOC 2 (Service Organization Control 2)
- WCAG (Web Content Accessibility Guidelines)

---

**Glossary Status**: Complete and ready for reference during implementation. Terms will be updated as system evolves and new concepts are introduced.