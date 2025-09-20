"""
Claude Code Configurator Module.

Handles generation and management of project-specific Claude Code configurations
with ADHD-optimized settings and templates.
"""

import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

from rich.console import Console
from ..config import ConfigManager

console = Console()

class ClaudeConfigurator:
    """
    Generates and manages Claude Code project configurations.

    Handles:
    - Project-specific .claude/ directory setup
    - Template-based configuration generation
    - ADHD-optimized instruction sets
    - MCP server configuration files
    """

    def __init__(self, config_manager: ConfigManager):
        """Initialize configurator with configuration manager."""
        self.config_manager = config_manager

    def setup_project_config(
        self,
        project_path: Path,
        template: str = 'python',
        force: bool = False
    ) -> None:
        """
        Setup complete project configuration for Dopemux.

        Args:
            project_path: Target project directory
            template: Project template type
            force: Overwrite existing configuration
        """
        claude_dir = project_path / '.claude'
        dopemux_dir = project_path / '.dopemux'

        # Create directories
        claude_dir.mkdir(exist_ok=True)
        dopemux_dir.mkdir(exist_ok=True)

        # Generate Claude configuration files
        self._create_claude_md(claude_dir, template)
        self._create_session_md(claude_dir, template)
        self._create_context_md(claude_dir, template)
        self._create_llms_md(claude_dir, template)

        # Generate Dopemux configuration
        self._create_dopemux_config(dopemux_dir, template)

        # Copy template files if they exist
        self._copy_template_files(project_path, template)

        console.print(f"[green]✓ Claude configuration setup complete for {template} project[/green]")

    def _create_claude_md(self, claude_dir: Path, template: str) -> None:
        """Create project-specific claude.md file."""
        config = self.config_manager.load_config()
        template_config = config.project_templates.get(template, {})

        content = f"""# {template.title()} Project - Dopemux Configuration

Project-specific Claude Code instructions for {template} development with ADHD accommodations.

## Project Context

You are working on a **{template} project** with Dopemux ADHD optimizations enabled.

### ADHD Accommodations Active
- **Focus Duration**: {config.adhd_profile.focus_duration_avg} minutes average
- **Break Intervals**: {config.adhd_profile.break_interval} minutes
- **Notification Style**: {config.adhd_profile.notification_style}
- **Visual Complexity**: {config.adhd_profile.visual_complexity}
- **Attention Adaptation**: {'Enabled' if config.attention.adaptation_enabled else 'Disabled'}

### Development Principles
- **Context Preservation**: Auto-save every {config.context.auto_save_interval} seconds
- **Gentle Guidance**: Use encouraging, supportive language
- **Progressive Disclosure**: Show essential info first, details on request
- **Task Chunking**: Break work into {config.adhd_profile.focus_duration_avg}-minute segments

{self._get_language_specific_instructions(template)}

## ADHD-Optimized Response Patterns

### When User is Focused
- Provide comprehensive technical details
- Include multiple implementation approaches
- Show complete code examples with explanations

### When User is Scattered
- Use bullet points and concise explanations
- Highlight only critical information
- Provide ONE clear next action
- Keep responses under 500 words

### During Context Switches
- Provide brief orientation: "You were working on X, now Y"
- Bridge between tasks with summaries
- Maintain awareness of previous context

## Project Standards

{self._get_project_standards(template)}

## Integration with Dopemux

### Available Commands
- `dopemux save` - Manual context preservation
- `dopemux restore` - Restore previous session
- `dopemux status` - Check attention metrics
- `dopemux task` - ADHD-friendly task management

### Context Sharing
- Session state automatically preserved
- Mental model tracked across interruptions
- Decision history maintained
- Progress visualization available

---

**Focus**: {template} development with ADHD accommodations
**Goal**: Maintain productivity while respecting neurodivergent needs
**Style**: Supportive, clear, action-oriented
"""

        (claude_dir / 'claude.md').write_text(content)

    def _create_session_md(self, claude_dir: Path, template: str) -> None:
        """Create session.md for project session management."""
        content = f"""# Session Management - {template.title()} Project

Session persistence patterns optimized for {template} development with ADHD considerations.

## Session Components

### Critical State (Always Preserved)
- Working directory and active files
- Cursor positions and scroll state
- Current task and mental model
- Unsaved changes tracking

### Context-Specific State
{self._get_session_specifics(template)}

### ADHD-Optimized Recovery
- Gentle re-entry prompts
- Visual progress indicators
- Time-since-last-work tracking
- Attention state restoration

## Session Triggers

### Auto-Save Events
- Every 30 seconds during active work
- Before context switches (file/directory changes)
- Before potentially disruptive operations
- On attention state changes

### Manual Save Points
- End of focused work sessions
- Before breaks or interruptions
- After completing significant milestones
- When switching between major tasks

## Recovery Patterns

### Session Restoration
```
1. Load previous session state
2. Display: "Welcome back! You were working on [task]"
3. Show: "[N] files open, last edit [time] ago"
4. Restore: File positions and cursor locations
5. Prompt: "Continue where you left off? [Y/n]"
```

### Interruption Recovery
```
1. Emergency context save on unexpected exit
2. On restart: "Session recovered from interruption"
3. Show: "Away for [duration], [changes] since you left"
4. Bridge: "You were [context], ready to continue?"
```

---

**Performance Target**: <500ms restoration time
**Storage**: Local SQLite database
**Privacy**: No sensitive data, local-only storage
"""

        (claude_dir / 'session.md').write_text(content)

    def _create_context_md(self, claude_dir: Path, template: str) -> None:
        """Create context.md for context management."""
        content = f"""# Context Management - {template.title()} Project

ADHD-optimized context preservation and restoration for {template} development.

## Context Layers

### Immediate Context
- Current file and function
- Active variables and state
- Current line and selection
- Recent edits and changes

### Working Context
- Open files and tabs
- Recent file history
- Active errors and warnings
- Pending tasks and TODOs

### Session Context
- Project goals and objectives
- Completed tasks and progress
- Key decisions and rationale
- Learning notes and insights

## Context Adaptation

### Attention State Based
{self._get_attention_patterns(template)}

### Visual Complexity Control
- **Minimal**: Essential information only
- **Standard**: Balanced detail and simplicity
- **Comprehensive**: Full technical details

## Memory Augmentation

### Decision Journal
- Automatic capture of significant choices
- Rationale and alternatives considered
- Context at time of decision
- Outcome tracking

### Pattern Recognition
- Common workflow sequences
- Repeated debugging patterns
- Successful solution strategies
- Personal productivity patterns

---

**Goal**: Seamless context transitions with minimal cognitive load
**Method**: Layered preservation with attention-aware adaptation
**Storage**: Local with optional cloud backup
"""

        (claude_dir / 'context.md').write_text(content)

    def _create_llms_md(self, claude_dir: Path, template: str) -> None:
        """Create llms.md with project-specific model preferences."""
        config = self.config_manager.load_config()

        content = f"""# LLM Configuration - {template.title()} Project

Multi-model AI configuration optimized for {template} development with ADHD accommodations.

## Model Selection for {template.title()}

### Primary Models
{self._get_language_model_preferences(template)}

### Attention-Based Routing
- **Focused**: Use comprehensive models (Opus 4.1, O3-Pro)
- **Scattered**: Use fast models (Gemini 2.5 Flash, GPT-5 Mini)
- **Hyperfocus**: Use code-focused models (Sonnet 4, Grok Code Fast)

## Project-Specific Adaptations

### {template.title()} Optimizations
{self._get_language_model_adaptations(template)}

### Response Formatting
- Code examples in {template} syntax
- Framework-specific patterns
- Best practices for {template} ecosystem
- ADHD-friendly explanations

## MCP Server Integration

### Active Servers
{self._get_mcp_servers_for_template(template)}

### Cost Optimization
- Prefer faster models for simple queries
- Use premium models for complex architecture decisions
- Cache responses for repeated patterns
- Smart fallback chains

---

**Focus**: {template} development efficiency with ADHD support
**Strategy**: Context-aware model routing
**Goal**: Optimal AI assistance without cognitive overload
"""

        (claude_dir / 'llms.md').write_text(content)

    def _create_dopemux_config(self, dopemux_dir: Path, template: str) -> None:
        """Create Dopemux-specific configuration."""
        config = self.config_manager.load_config()
        template_config = config.project_templates.get(template, {})

        dopemux_config = {
            "version": "1.0",
            "project_type": template,
            "initialized_at": "2024-01-15T10:30:00Z",
            "adhd_profile": {
                **config.adhd_profile.model_dump(),
                **template_config.get('adhd_adaptations', {})
            },
            "active_features": {
                "context_preservation": True,
                "attention_monitoring": True,
                "task_decomposition": True,
                "gentle_notifications": True
            },
            # Don't include mcp_servers in project config - let config manager handle it
            "session_settings": {
                "auto_save_interval": config.context.auto_save_interval,
                "max_sessions": config.context.max_sessions,
                "compression": config.context.compression
            }
        }

        config_file = dopemux_dir / 'config.yaml'
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(dopemux_config, f, default_flow_style=False, indent=2)

    def _copy_template_files(self, project_path: Path, template: str) -> None:
        """Copy template-specific files if they exist."""
        template_dir = Path(__file__).parent.parent / 'templates' / template

        if not template_dir.exists():
            return

        for file_path in template_dir.rglob('*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(template_dir)
                target_path = project_path / relative_path

                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, target_path)

    def _get_language_specific_instructions(self, template: str) -> str:
        """Get language-specific development instructions."""
        instructions = {
            'python': """
### Python Development Guidelines
- Use type hints for better ADHD developer experience
- Follow PEP 8 with Black formatting
- Prefer explicit over implicit (Zen of Python)
- Use dataclasses and Pydantic for clear data structures
- Write docstrings for all public functions

### Testing Strategy
- Use pytest for all testing
- Write tests first for complex logic
- Use descriptive test names
- Mock external dependencies
""",
            'javascript': """
### JavaScript Development Guidelines
- Use TypeScript for type safety and better IDE support
- Follow consistent naming conventions (camelCase)
- Use async/await over Promise chains
- Prefer const/let over var
- Use meaningful variable names

### Testing Strategy
- Jest for unit testing
- React Testing Library for component tests
- Clear test descriptions
- Mock external APIs
""",
            'rust': """
### Rust Development Guidelines
- Leverage the type system for correctness
- Use cargo fmt and cargo clippy
- Write comprehensive documentation
- Handle errors explicitly with Result<T, E>
- Use meaningful error types

### Testing Strategy
- Use built-in testing framework
- Write integration tests in tests/ directory
- Use descriptive test names
- Test both success and error cases
"""
        }

        return instructions.get(template, f"### {template.title()} Development\nUse best practices for {template} development.")

    def _get_project_standards(self, template: str) -> str:
        """Get project-specific coding standards."""
        standards = {
            'python': """
### Code Organization
- Use src/ layout for packages
- Group related functionality in modules
- Clear separation of concerns
- Consistent import ordering (isort)

### Dependencies
- Use pyproject.toml for project configuration
- Pin versions for reproducible builds
- Use virtual environments
- Document all dependencies
""",
            'javascript': """
### Code Organization
- Use consistent folder structure
- Separate components, utilities, and services
- Use index files for clean imports
- Follow component naming conventions

### Dependencies
- Use package.json and lock files
- Keep dependencies up to date
- Use semantic versioning
- Document breaking changes
""",
            'rust': """
### Code Organization
- Use Cargo.toml for project management
- Organize code into logical modules
- Use pub/private visibility appropriately
- Follow Rust naming conventions

### Dependencies
- Use semantic versioning
- Prefer stable crate versions
- Document feature flags
- Use workspaces for multi-crate projects
"""
        }

        return standards.get(template, f"### {template.title()} Standards\nFollow established {template} best practices.")

    def _get_session_specifics(self, template: str) -> str:
        """Get template-specific session state."""
        specifics = {
            'python': """
- Virtual environment state
- Python interpreter version
- Installed packages (pip list)
- Environment variables
- Database connections
- Test runner state
""",
            'javascript': """
- Node.js version and npm/yarn state
- Package.json and lock file status
- Environment variables (.env files)
- Running development servers
- Browser dev tools state
- Testing framework state
""",
            'rust': """
- Cargo project state
- Target compilation settings
- Feature flags enabled
- Dependency versions
- Cargo registry state
- Compiler version
"""
        }

        return specifics.get(template, f"### {template.title()} Session State\n- Project-specific state tracking")

    def _get_attention_patterns(self, template: str) -> str:
        """Get template-specific attention adaptation patterns."""
        return f"""
**Focused State ({template})**:
- Show comprehensive {template} documentation
- Include multiple implementation approaches
- Provide detailed code explanations
- Show related patterns and best practices

**Scattered State ({template})**:
- Quick {template} syntax reminders
- Single, clear implementation
- Bullet-point explanations
- Focus on immediate problem only

**Hyperfocus State ({template})**:
- Streamlined {template} code generation
- Minimal explanations
- Direct implementation focus
- Anticipate next development steps
"""

    def _get_language_model_preferences(self, template: str) -> str:
        """Get model preferences for specific language."""
        preferences = {
            'python': """
- **Code Generation**: Claude Sonnet 4, DeepSeek Chat
- **Architecture**: Claude Opus 4.1, O3-Pro
- **Quick Fixes**: Gemini 2.5 Flash, GPT-5 Mini
- **Documentation**: Claude Opus 4.1, GPT-4.1
""",
            'javascript': """
- **Code Generation**: Grok Code Fast, Claude Sonnet 4
- **React/Vue**: Claude Sonnet 4, DeepSeek Chat
- **Node.js**: Claude Sonnet 4, GPT-4.1
- **TypeScript**: Claude Opus 4.1, O3-Pro
""",
            'rust': """
- **Systems Programming**: Claude Opus 4.1, O3-Pro
- **Code Generation**: Claude Sonnet 4, DeepSeek Chat
- **Performance**: O3-Deep-Research, Claude Opus 4.1
- **Memory Safety**: Claude Opus 4.1, DeepSeek Reasoner
"""
        }

        return preferences.get(template, f"- **{template.title()} Development**: Claude Sonnet 4, DeepSeek Chat")

    def _get_language_model_adaptations(self, template: str) -> str:
        """Get language-specific model adaptations."""
        adaptations = {
            'python': """
- Pythonic code patterns and idioms
- Type hints and mypy compatibility
- PEP compliance and best practices
- pytest testing patterns
""",
            'javascript': """
- Modern ES6+ syntax and features
- React/Vue component patterns
- Async/await best practices
- Node.js and browser compatibility
""",
            'rust': """
- Memory safety and ownership patterns
- Error handling with Result types
- Performance optimization techniques
- Concurrent programming patterns
"""
        }

        return adaptations.get(template, f"- {template.title()}-specific patterns and best practices")

    def _get_mcp_servers_for_template(self, template: str) -> str:
        """Get recommended MCP servers for template."""
        servers = {
            'python': """
- **mas-sequential-thinking**: Complex reasoning for architecture
- **context7**: Python documentation and patterns
- **claude-context**: Semantic code search
- **morphllm-fast-apply**: Code transformations
""",
            'javascript': """
- **context7**: React/Vue/Node.js documentation
- **claude-context**: Codebase semantic search
- **morphllm-fast-apply**: Framework migrations
- **exa**: Web research for best practices
""",
            'rust': """
- **mas-sequential-thinking**: Systems design reasoning
- **context7**: Rust documentation and crates
- **claude-context**: Large codebase navigation
- **morphllm-fast-apply**: Code modernization
"""
        }

        return servers.get(template, """
- **context7**: Language documentation
- **claude-context**: Code search
- **morphllm-fast-apply**: Transformations
""")

    def update_project_config(self, project_path: Path, updates: Dict[str, Any]) -> None:
        """Update existing project configuration."""
        config_file = project_path / '.dopemux' / 'config.yaml'

        if not config_file.exists():
            console.print("[red]No Dopemux configuration found in project[/red]")
            return

        import yaml
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)

        # Apply updates
        for key, value in updates.items():
            if '.' in key:
                # Nested key (e.g., 'adhd_profile.focus_duration_avg')
                keys = key.split('.')
                current = config
                for k in keys[:-1]:
                    current = current.setdefault(k, {})
                current[keys[-1]] = value
            else:
                config[key] = value

        # Save updated config
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)

        console.print(f"[green]✓ Updated project configuration[/green]")

    def get_project_status(self, project_path: Path) -> Dict[str, Any]:
        """Get project configuration status."""
        claude_dir = project_path / '.claude'
        dopemux_dir = project_path / '.dopemux'

        status = {
            "dopemux_initialized": dopemux_dir.exists(),
            "claude_configured": claude_dir.exists(),
            "config_files": {
                "claude.md": (claude_dir / 'claude.md').exists(),
                "session.md": (claude_dir / 'session.md').exists(),
                "context.md": (claude_dir / 'context.md').exists(),
                "llms.md": (claude_dir / 'llms.md').exists(),
                "config.yaml": (dopemux_dir / 'config.yaml').exists()
            }
        }

        # Load project config if available
        config_file = dopemux_dir / 'config.yaml'
        if config_file.exists():
            import yaml
            with open(config_file, 'r') as f:
                project_config = yaml.safe_load(f)
                status["project_type"] = project_config.get('project_type', 'unknown')
                status["adhd_features"] = project_config.get('active_features', {})

        return status