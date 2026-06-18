# Dopemux CLI Surfaces

Dopemux help output captured in commands/dopemux_help.txt.

Usage: python -m dopemux.cli [OPTIONS] COMMAND [ARGS]...
  DØPEMÜX is a flight-deck for neurodivergent developers, engineered to
  automate context preservation, orchestrate attention monitoring, and
  decompose complex objectives into ritualistic tasks. This command-line
  interface acts as your  primary ritual circle, synchronizing daemon states
  across your workspace, tmux sessions, and mobile devices to ensure zero
  context decay.
  Invoking this daemon establishes a cockpit environment where focus is a
  service and distraction is mitigated by architectural design.
  --version
  -c, --config TEXT               🔬 Path to the ritual configuration file
  -v, --verbose                   📊 Increase verbosity of the ritual logs.
  --debug-log FILE                📜 Specify a direct telemetry line to a file
  --render-mode [rich|plain|compact|audit]
  --compact                       ⚡ Toggle compact HUD rendering. Minimize the
  --plain                         🧪 Disable ritual styling. Renders output as
  --json                          📊 Emit ritual state as JSON. Ideal for
  --no-hints                      💧 Silence the flight-deck startup tips. For
  --help                          Show this message and exit.
Commands:
  agent          🧠 Cognitive Uplink: Agent-to-agent communication
  agent-loop     🤖 Grand Orchestrator: Agentic workflow execution loop...
  analyze        🔬 Deep Inspection: Run high-fidelity codebase analysis...
  audit          🔬 Documentation Audit: Corpus analysis and guided...
  autoresponder  🤖 Auto-Response Ritual: Manage Claude Auto Responder...
  backup         💾 Save Current Context
  capture        📥 Telemetry Ingestion: Capture ritual tool signals...
  cockpit        Dopemux Cockpit -- guarded operator and runtime-render...
  dashboard      📊 Cockpit HUD: Launch the high-fidelity TUI dashboard
  debug          🩺 Ritual Apothecary: Interactive debugging support
  decisions      📊 Decision Governance: Track and analyze cockpit...
  dev            🔧 Contributor Flight-Deck: Development & hot reload
  doctor         🏥 System Apothecary: Run diagnostics and health checks
  dope           🔥 Engage DOPE Ritual: Launch full high-fidelity cockpit...
  env            🔒 Environment Guard: Safe environment variable inspection
  extract        📄 Ritual Daemon: Document extraction with ADHD-optimized...
  health         🏥 Diagnostic HUD: Comprehensive health check for the...
  hooks          🔗 Event Synchronization: Manage Claude Code integration...
  init           🚀 Synchronize Flight-Deck: Initialize DØPEMÜX Rituals
  instances      🧪 Instance Orchestration: Manage parallel Ritual-Daemons
  kernel         🔬 TaskX Kernel Lifecycle: Orchestrate Ritual Steps
  launch         🚀 Ignite Cockpit: Quick launch with opinionated presets
  layouts        📐 Catalog Cockpit Architectures: Show available layouts...
  mcp            🔬 Neural Architecture: Command the MCP infrastructure
  memory         🧠 Cognitive Core: Memory capture and global DAEMON...
  mobile         📱 Satellite HUD: Manage Dopemux mobile (Happy) integration
  mobile-env     📱 dopemux-mobile: ADHD-optimized mobile tmux environment.
  native-hooks   🔗 Protocol Synchronization: Manage Claude Code internal...
  orchestrator   Read-only Task Orchestrator status and daily planning...
  personas       🎭 Cognitive Personas: Management and discovery of AI...
  pr-merge       Delegate PR merge specialist commands to the...
  pr-steward     🧾 Check-Only Governance: PR Steward
  profile        📋 Contextual Attunement: Manage MCP profiles for tool...
  quick          ⚡ Streamlined Ignition: Fastest cockpit launch (Shortcut)
  restore        🔄 Temporal Restoration: Reconstruct past development...
  routing        Manage Dopemux routing and launchd services.
  rte            Canonical operator entrypoint for Repo Truth Extractor.
  run-build      🏗️ Materialization Ritual: Run a build command and send...
  run-tests      🧪 Validation Ritual: Run automated tests and send...
  safe           🛡️ Safety Interlocks: Ritual safety hook management
  save           💾 Save Current Context
  servers        🔬 Cockpit Alias: Alternative entry point for MCP operations
  session        ⏳ Temporal Registry: Session search and management
  shell-setup    🐚 Engage Shell Uplink: Output integration code for...
  start          ⚡ Ignition: Launch the DØPEMÜX Cockpit
  status         📊 Diagnostic HUD: Show current session status and metrics
  switch         ✅ Set active profile
  system-data    Mac system-data diagnosis, cleanup planning, TUI, and...
  task           📋 Legacy Ritual: Manage tasks (DEPRECATED - Use...
  theme          🎭 Aesthetic Synchronizer: Manage UI themes and ritual...
  tmux           🧭 Cockpit Navigation: Orchestrate tmux sessions and panes
  trigger        ⚡ Sensor Triggers: Internal hook telemetry signals
  truth          Deprecated Repo Truth Extractor entrypoint.
  update         🔄 System Regeneration: Update and Upgrade DØPEMÜX
  upgrades       Legacy compatibility alias for `dopemux rte`.
  wire-conport   ⚡ Synchronize Uplink: Wire ConPort MCP Terminal
  wizard         🧙 Ritual Guide: Guided extraction flight-deck walkthrough
  workflow       📜 Mission Planning: Orchestrate ritual workflows and ideas
Usage: python -m dopemux.cli kernel [OPTIONS] COMMAND [ARGS]...
  Manages the primary execution kernel of the TaskX subsystem. These commands
  delegate to the TaskX ritual wrapper (scripts/taskx), synchronizing the
  core state and lifecycle of the active daemon.
  Capabilities: - Diagnostic Scans: Run the doctor ritual to verify kernel
  health. - Lifecycle Stages: Compile, Run, Collect, Gate, Promote, Feedback,
  and Loop.
  --help  Show this message and exit.
Commands:
  collect   📊 Harvest ritual artifacts and state updates from the active...
  compile   🧪 Synchronize and compile the TaskX ritual logic.
  doctor    🔬 Run diagnostic scan on the active kernel (TaskX doctor).
  feedback  🧠 Process mission feedback and update ritual heuristics.
  gate      💧 Verify ritual exit conditions and quality gates.
  loop      ⚡ Initiate a persistent ritual loop.
  promote   ⚡ Advance the ritual state to the next temporal coordinate.
  run       ⚡ Execute the current TaskX ritual cycle.
Usage: python -m dopemux.cli mcp [OPTIONS] COMMAND [ARGS]...
  Manages the Docker-based Model Context Protocol servers. These daemons
  the cockpit's tool capabilities and semantic context management.
  --help  Show this message and exit.
Commands:
  add           ➕ Append Server: Add a per-worktree MCP from the catalog...
  doctor        🩺 Health Sweep: Verify env vars, port reachability,...
  down          💧 Cool Down Cores: Terminate MCP containers and volumes
  init          🌱 Bootstrap Worktree: Scaffold .mcp.json + per-worktree...
  list          📋 Survey Fleet: Show globals, locals, catalog availability
  logs          🧠 Tap Telemetry: Stream real-time log data from MCP services
  remove        ➖ Drop Server: Remove a per-worktree MCP from .mcp.json
  start-all     🧙 Summon Ecosystem: Ignite the complete DØPEMÜX stack
  status        📊 Diagnostic HUD: Interrogate MCP service health
  sync-globals  🌐 Promote Singletons: Reconcile ~/.claude.json mcpServers...
  up            ⚡ Ignite Engine: Deploy MCP servers via Docker Compose
Usage: python -m dopemux.cli routing [OPTIONS] COMMAND [ARGS]...
  Manage Dopemux routing and launchd services.
  --help  Show this message and exit.
Commands:
  api             Switch to API mode (route through LiteLLM + external...
  config          Show current routing configuration.
  direct          Switch to direct/subscription mode (route straight to...
  docker          Generate Docker Compose snippets for services.
  doctor          Audit repo-owned routing alias contract drift in...
