# Custom Data: implementation_plans

### comprehensive_code_doc_review_2025-10-16

*   [2025-10-16 20:33:28]

```json
{
  "plan_name": "Comprehensive Code & Documentation Review - Dopemux MVP",
  "created_date": "2025-10-16",
  "scope": {
    "python_files": 828,
    "lines_of_code": 24134,
    "markdown_docs": 495,
    "services": 12,
    "review_type": "comprehensive_audit"
  },
  "goal": "Systematic review and standardization of all code and documentation across Dopemux MVP",
  "phases": [
    {
      "phase": 1,
      "name": "Critical Systems Review",
      "duration": "Week 1 (10-12 hours)",
      "priority": "HIGH",
      "focus": "Production-critical services with user impact",
      "services": [
        {
          "service": "dope-context",
          "status": "COMPLETED - Just reviewed and committed",
          "files": 69,
          "review_findings": "ConPort Decision #72, #73 - Production-ready",
          "next_action": "None - freshly validated"
        },
        {
          "service": "orchestrator",
          "status": "READY_TO_SHIP marker added",
          "files": "~800 lines HTTP client",
          "review_findings": "ConPort Decision #66 - 100% tests, Zen validated",
          "next_action": "Continue Phase 1 MVP implementation per roadmap"
        },
        {
          "service": "conport",
          "status": "IN_USE - needs review",
          "files": "~2000 lines estimated",
          "review_focus": ["API consistency", "Error handling", "Performance", "AGE graph optimization"],
          "estimated_time": "4 hours"
        },
        {
          "service": "serena (v2)",
          "status": "PHASE_2E_COMPLETE - needs validation",
          "files": "~8000+ lines (31 components)",
          "review_focus": ["Integration points", "ADHD features working", "Performance targets", "LSP stability"],
          "estimated_time": "6 hours"
        }
      ]
    },
    {
      "phase": 2,
      "name": "Supporting Services Review",
      "duration": "Week 2 (8-10 hours)",
      "priority": "MEDIUM",
      "services": [
        {
          "service": "conport_kg_ui",
          "review_focus": ["TUI stability", "Color accessibility", "ADHD features"],
          "estimated_time": "3 hours"
        },
        {
          "service": "task-orchestrator",
          "review_focus": ["37 tools validation", "Error handling", "Integration with orchestrator"],
          "estimated_time": "4 hours"
        },
        {
          "service": "taskmaster",
          "review_focus": ["PRD parsing", "Task decomposition", "AI integration"],
          "estimated_time": "3 hours"
        }
      ]
    },
    {
      "phase": 3,
      "name": "Documentation Standardization",
      "duration": "Week 3 (12-15 hours)",
      "priority": "HIGH",
      "focus": "Standardize all 495 markdown files",
      "tasks": [
        {
          "task": "Audit main documentation",
          "scope": ["docs/", "README.md", "ARCHITECTURE.md"],
          "review_criteria": ["Accuracy", "Completeness", "ADHD-friendly formatting", "Cross-references"],
          "estimated_time": "4 hours"
        },
        {
          "task": "Standardize claudedocs/",
          "scope": "495 markdown files",
          "review_criteria": ["Consolidate duplicates", "Archive old research", "Tag by relevance", "Create index"],
          "estimated_time": "6 hours"
        },
        {
          "task": "Service-level docs",
          "scope": ["Each service README", "API docs", "Setup guides"],
          "review_criteria": ["Complete", "Accurate", "Examples working"],
          "estimated_time": "5 hours"
        }
      ]
    },
    {
      "phase": 4,
      "name": "Code Quality & Standards",
      "duration": "Week 4 (10-12 hours)",
      "priority": "MEDIUM",
      "tasks": [
        {
          "task": "Run comprehensive linting",
          "tools": ["pylint", "mypy", "black", "ruff"],
          "scope": "All 828 Python files",
          "estimated_time": "2 hours"
        },
        {
          "task": "Fix critical issues",
          "criteria": ["Security vulnerabilities", "Type errors", "Breaking bugs"],
          "estimated_time": "6 hours"
        },
        {
          "task": "Standardize code style",
          "focus": ["Consistent imports", "Type hints", "Docstrings", "Error handling patterns"],
          "estimated_time": "4 hours"
        }
      ]
    },
    {
      "phase": 5,
      "name": "Testing & Validation",
      "duration": "Week 5 (8-10 hours)",
      "priority": "HIGH",
      "tasks": [
        {
          "task": "Run all existing tests",
          "command": "pytest --cov --cov-report=html",
          "success_criteria": ">80% pass rate",
          "estimated_time": "2 hours"
        },
        {
          "task": "Fix failing tests",
          "priority": "Critical tests first",
          "estimated_time": "4 hours"
        },
        {
          "task": "Add missing tests",
          "focus": "Core functionality with <50% coverage",
          "estimated_time": "4 hours"
        }
      ]
    },
    {
      "phase": 6,
      "name": "Architecture Validation",
      "duration": "Week 6 (6-8 hours)",
      "priority": "MEDIUM",
      "tasks": [
        {
          "task": "Two-plane architecture compliance",
          "review": "Authority boundaries, cross-plane communication, Integration Bridge usage",
          "use_tool": "Zen thinkdeep for analysis",
          "estimated_time": "3 hours"
        },
        {
          "task": "MCP integration audit",
          "review": "All 8 MCP servers working, global config verified, worktree support",
          "estimated_time": "2 hours"
        },
        {
          "task": "ADHD feature validation",
          "review": "Sub-200ms targets, progressive disclosure, complexity scoring, auto-save",
          "estimated_time": "3 hours"
        }
      ]
    }
  ],
  "total_effort": {
    "total_hours": "54-67 hours",
    "adhd_sessions": "130-160 sessions (25 min each)",
    "calendar_weeks": 6,
    "daily_commitment": "1.5-2 hours per day"
  },
  "review_methodology": {
    "tools": ["Zen codereview", "Dope-Context search", "Serena navigation", "pytest", "mypy", "pylint"],
    "approach": "Service-by-service systematic review",
    "validation": "Multi-model validation for critical findings",
    "documentation": "Log all decisions to ConPort"
  },
  "success_criteria": [
    "All critical issues fixed",
    "Test coverage >80%",
    "Documentation standardized and indexed",
    "ADHD features validated working",
    "Architecture compliance verified",
    "Security vulnerabilities resolved"
  ],
  "status": "Plan ready - start with Phase 1 Critical Systems Review",
  "next_step": "Review ConPort service (4 hours estimated)"
}
```

---
### orchestrator_phase1_roadmap

*   [2025-10-16 20:27:26]

```json
{
  "plan_name": "Dopemux Multi-AI Orchestrator - Phase 1 MVP",
  "goal": "Production-ready tmux-based multi-AI orchestrator with core functionality",
  "timeline": "Weeks 1-2 (33 focus blocks, ~825 minutes)",
  "success_criteria": [
    "Launch 2-4 AI instances in tmux panes",
    "Route commands to appropriate agents",
    "Auto-save context every 30 seconds",
    "Resume sessions after interruption",
    "ADHD-optimized energy-based layouts"
  ],
  "steps": [
    {
      "step": 1,
      "name": "Create tmux 4-pane layout manager",
      "files": [
        "services/orchestrator/src/tmux_manager.py",
        "services/orchestrator/src/layouts/adaptive_layout.py",
        "services/orchestrator/tests/test_tmux_manager.py",
        "services/orchestrator/config/layouts.yaml"
      ],
      "focus_blocks": 4,
      "minutes": 100,
      "complexity": 0.35,
      "energy_required": "medium",
      "dependencies": [],
      "validation": "Can create tmux session with 2-4 panes, layout adapts to energy level, pane IDs tracked"
    },
    {
      "step": 2,
      "name": "Implement chat command parser (slash commands)",
      "files": [
        "services/orchestrator/src/command_parser.py",
        "services/orchestrator/src/commands/__init__.py",
        "services/orchestrator/src/commands/research_commands.py",
        "services/orchestrator/src/commands/plan_commands.py",
        "services/orchestrator/src/commands/implement_commands.py",
        "services/orchestrator/src/commands/delegate_commands.py",
        "services/orchestrator/tests/test_command_parser.py"
      ],
      "focus_blocks": 5,
      "minutes": 125,
      "complexity": 0.45,
      "energy_required": "medium-high",
      "dependencies": ["step_1"],
      "validation": "Parse all 5 command types, route to correct agents, handle parallel flag"
    },
    {
      "step": 3,
      "name": "Build agent spawner (launch Claude/Gemini/Grok in panes)",
      "files": [
        "services/orchestrator/src/agent_spawner.py",
        "services/orchestrator/src/agents/__init__.py",
        "services/orchestrator/src/agents/base_agent.py",
        "services/orchestrator/src/agents/claude_agent.py",
        "services/orchestrator/src/agents/gemini_agent.py",
        "services/orchestrator/src/agents/grok_agent.py",
        "services/orchestrator/config/agent_configs.yaml",
        "services/orchestrator/tests/test_agent_spawner.py"
      ],
      "focus_blocks": 6,
      "minutes": 150,
      "complexity": 0.65,
      "energy_required": "high",
      "dependencies": ["step_1", "step_2"],
      "validation": "All 3 agents launch, health checks pass, respond to test commands",
      "adhd_note": "Implement one agent per day to reduce context switching"
    },
    {
      "step": 4,
      "name": "Implement TmuxCapture message abstraction",
      "files": [
        "services/orchestrator/src/message_bus.py",
        "services/orchestrator/src/capture/tmux_capture.py",
        "services/orchestrator/src/capture/message_extractor.py",
        "services/orchestrator/tests/test_message_bus.py",
        "services/orchestrator/config/message_patterns.yaml"
      ],
      "focus_blocks": 5,
      "minutes": 125,
      "complexity": 0.55,
      "energy_required": "medium-high",
      "dependencies": ["step_1", "step_3"],
      "validation": "Capture incremental output, parse responses, route correctly, maintain history"
    },
    {
      "step": 5,
      "name": "Integrate ConPort for auto-save checkpoints",
      "files": [
        "services/orchestrator/src/checkpoint_manager.py",
        "services/orchestrator/src/integrations/conport_client.py",
        "services/orchestrator/tests/test_checkpoint_manager.py"
      ],
      "focus_blocks": 4,
      "minutes": 100,
      "complexity": 0.40,
      "energy_required": "medium",
      "dependencies": ["step_3", "step_4"],
      "validation": "Checkpoint every 30s, ConPort updated, restore works, no data loss",
      "adhd_benefit": "HIGH - enables interruption recovery (23-min context switching cost avoided)"
    },
    {
      "step": 6,
      "name": "Build basic command routing (research/plan/implement modes)",
      "files": [
        "services/orchestrator/src/router.py",
        "services/orchestrator/src/modes/__init__.py",
        "services/orchestrator/src/modes/research_mode.py",
        "services/orchestrator/src/modes/plan_mode.py",
        "services/orchestrator/src/modes/implement_mode.py",
        "services/orchestrator/src/modes/delegate_mode.py",
        "services/orchestrator/config/routing_rules.yaml",
        "services/orchestrator/tests/test_router.py"
      ],
      "focus_blocks": 5,
      "minutes": 125,
      "complexity": 0.50,
      "energy_required": "medium-high",
      "dependencies": ["step_2", "step_3", "step_4"],
      "validation": "Commands routed correctly by mode, parallel delegation works, mode switching smooth"
    },
    {
      "step": 7,
      "name": "Create resume flow for session restoration",
      "files": [
        "services/orchestrator/src/session_manager.py",
        "services/orchestrator/src/restore/checkpoint_restore.py",
        "services/orchestrator/tests/test_session_manager.py"
      ],
      "focus_blocks": 4,
      "minutes": 100,
      "complexity": 0.35,
      "energy_required": "medium",
      "dependencies": ["step_5"],
      "validation": "Resume from checkpoint, restore pane layout, reload message history, clear 'where you left off' summary"
    }
  ],
  "total_effort": {
    "focus_blocks": 33,
    "total_minutes": 825,
    "total_hours": 13.75,
    "adhd_sessions": "28 sessions (25 min each + 5 min breaks)"
  },
  "research_foundation": {
    "total_words": 120000,
    "research_streams": 6,
    "design_documents": 5,
    "zen_validations": 3,
    "confidence": 0.87
  },
  "status": "Phase 1 MVP partially complete - orchestrator HTTP client (806 lines) already built",
  "next_step": "Step 1: tmux layout manager"
}
```
