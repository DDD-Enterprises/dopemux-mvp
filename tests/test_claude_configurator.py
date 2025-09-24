"""
Tests for the Claude configurator module.
"""

import yaml

from dopemux.claude.configurator import ClaudeConfigurator


class TestClaudeConfigurator:
    """Test ClaudeConfigurator class."""

    def test_initialization(self, config_manager):
        """Test ClaudeConfigurator initialization."""
        configurator = ClaudeConfigurator(config_manager)
        assert configurator.config_manager == config_manager

    def test_setup_project_config_python(self, config_manager, temp_project_dir):
        """Test setting up project configuration for Python."""
        configurator = ClaudeConfigurator(config_manager)

        configurator.setup_project_config(temp_project_dir, template="python")

        # Verify directories were created
        claude_dir = temp_project_dir / ".claude"
        dopemux_dir = temp_project_dir / ".dopemux"
        assert claude_dir.exists()
        assert dopemux_dir.exists()

        # Verify configuration files were created
        assert (claude_dir / "claude.md").exists()
        assert (claude_dir / "session.md").exists()
        assert (claude_dir / "context.md").exists()
        assert (claude_dir / "llms.md").exists()
        assert (dopemux_dir / "config.yaml").exists()

    def test_setup_project_config_javascript(self, config_manager, temp_project_dir):
        """Test setting up project configuration for JavaScript."""
        configurator = ClaudeConfigurator(config_manager)

        configurator.setup_project_config(temp_project_dir, template="javascript")

        claude_dir = temp_project_dir / ".claude"

        # Check that JavaScript-specific content is in the files
        claude_md_content = (claude_dir / "claude.md").read_text()
        assert "JavaScript" in claude_md_content
        assert "TypeScript" in claude_md_content

    def test_setup_project_config_rust(self, config_manager, temp_project_dir):
        """Test setting up project configuration for Rust."""
        configurator = ClaudeConfigurator(config_manager)

        configurator.setup_project_config(temp_project_dir, template="rust")

        claude_dir = temp_project_dir / ".claude"

        # Check that Rust-specific content is in the files
        claude_md_content = (claude_dir / "claude.md").read_text()
        assert "Rust" in claude_md_content
        assert "cargo" in claude_md_content

    def test_create_claude_md_content(self, config_manager, temp_project_dir):
        """Test that claude.md contains expected ADHD accommodations."""
        configurator = ClaudeConfigurator(config_manager)

        configurator.setup_project_config(temp_project_dir, template="python")

        claude_md = temp_project_dir / ".claude" / "claude.md"
        content = claude_md.read_text()

        # Verify ADHD-specific content
        assert "ADHD Accommodations Active" in content
        assert "Focus Duration" in content
        assert "Break Intervals" in content
        assert "Context Preservation" in content
        assert "Task Chunking" in content

    def test_create_session_md_content(self, config_manager, temp_project_dir):
        """Test that session.md contains session management content."""
        configurator = ClaudeConfigurator(config_manager)

        configurator.setup_project_config(temp_project_dir)

        session_md = temp_project_dir / ".claude" / "session.md"
        content = session_md.read_text()

        # Verify session-specific content
        assert "Session Components" in content
        assert "Critical State" in content
        assert "ADHD-Optimized Recovery" in content
        assert "Auto-Save Events" in content

    def test_create_context_md_content(self, config_manager, temp_project_dir):
        """Test that context.md contains context management content."""
        configurator = ClaudeConfigurator(config_manager)

        configurator.setup_project_config(temp_project_dir)

        context_md = temp_project_dir / ".claude" / "context.md"
        content = context_md.read_text()

        # Verify context-specific content
        assert "Context Layers" in content
        assert "Immediate Context" in content
        assert "Working Context" in content
        assert "Session Context" in content

    def test_create_llms_md_content(self, config_manager, temp_project_dir):
        """Test that llms.md contains LLM configuration content."""
        configurator = ClaudeConfigurator(config_manager)

        configurator.setup_project_config(temp_project_dir, template="python")

        llms_md = temp_project_dir / ".claude" / "llms.md"
        content = llms_md.read_text()

        # Verify LLM-specific content
        assert "Model Selection" in content
        assert "Attention-Based Routing" in content
        assert "Python" in content
        assert "MCP Server Integration" in content

    def test_create_dopemux_config(self, config_manager, temp_project_dir):
        """Test that dopemux config.yaml is created correctly."""
        configurator = ClaudeConfigurator(config_manager)

        configurator.setup_project_config(temp_project_dir, template="python")

        config_file = temp_project_dir / ".dopemux" / "config.yaml"
        with open(config_file) as f:
            config = yaml.safe_load(f)

        # Verify config structure
        assert config["version"] == "1.0"
        assert config["project_type"] == "python"
        assert "adhd_profile" in config
        assert "active_features" in config
        assert "session_settings" in config

    def test_language_specific_instructions_python(self, config_manager):
        """Test Python-specific development instructions."""
        configurator = ClaudeConfigurator(config_manager)

        instructions = configurator._get_language_specific_instructions("python")

        assert "type hints" in instructions
        assert "PEP 8" in instructions
        assert "pytest" in instructions
        assert "dataclasses" in instructions

    def test_language_specific_instructions_javascript(self, config_manager):
        """Test JavaScript-specific development instructions."""
        configurator = ClaudeConfigurator(config_manager)

        instructions = configurator._get_language_specific_instructions("javascript")

        assert "TypeScript" in instructions
        assert "async/await" in instructions
        assert "Jest" in instructions
        assert "React Testing Library" in instructions

    def test_language_specific_instructions_rust(self, config_manager):
        """Test Rust-specific development instructions."""
        configurator = ClaudeConfigurator(config_manager)

        instructions = configurator._get_language_specific_instructions("rust")

        assert "type system" in instructions
        assert "cargo" in instructions
        assert "Result<T, E>" in instructions
        assert "tests/ directory" in instructions

    def test_project_standards_python(self, config_manager):
        """Test Python project standards."""
        configurator = ClaudeConfigurator(config_manager)

        standards = configurator._get_project_standards("python")

        assert "src/" in standards
        assert "pyproject.toml" in standards
        assert "virtual environments" in standards
        assert "isort" in standards

    def test_project_standards_javascript(self, config_manager):
        """Test JavaScript project standards."""
        configurator = ClaudeConfigurator(config_manager)

        standards = configurator._get_project_standards("javascript")

        assert "package.json" in standards
        assert "components" in standards
        assert "semantic versioning" in standards

    def test_project_standards_rust(self, config_manager):
        """Test Rust project standards."""
        configurator = ClaudeConfigurator(config_manager)

        standards = configurator._get_project_standards("rust")

        assert "Cargo.toml" in standards
        assert "modules" in standards
        assert "workspaces" in standards

    def test_session_specifics_python(self, config_manager):
        """Test Python session-specific state tracking."""
        configurator = ClaudeConfigurator(config_manager)

        specifics = configurator._get_session_specifics("python")

        assert "Virtual environment" in specifics
        assert "Python interpreter" in specifics
        assert "pip list" in specifics
        assert "Database connections" in specifics

    def test_session_specifics_javascript(self, config_manager):
        """Test JavaScript session-specific state tracking."""
        configurator = ClaudeConfigurator(config_manager)

        specifics = configurator._get_session_specifics("javascript")

        assert "Node.js" in specifics
        assert "npm/yarn" in specifics
        assert ".env files" in specifics
        assert "development servers" in specifics

    def test_session_specifics_rust(self, config_manager):
        """Test Rust session-specific state tracking."""
        configurator = ClaudeConfigurator(config_manager)

        specifics = configurator._get_session_specifics("rust")

        assert "Cargo project" in specifics
        assert "compilation settings" in specifics
        assert "Feature flags" in specifics
        assert "Compiler version" in specifics

    def test_attention_patterns_generation(self, config_manager):
        """Test attention pattern generation for different templates."""
        configurator = ClaudeConfigurator(config_manager)

        patterns = configurator._get_attention_patterns("python")

        assert "Focused State" in patterns
        assert "Scattered State" in patterns
        assert "Hyperfocus State" in patterns
        assert "python" in patterns.lower()

    def test_language_model_preferences_python(self, config_manager):
        """Test model preferences for Python development."""
        configurator = ClaudeConfigurator(config_manager)

        preferences = configurator._get_language_model_preferences("python")

        assert "Claude Sonnet" in preferences
        assert "DeepSeek Chat" in preferences
        assert "Code Generation" in preferences
        assert "Architecture" in preferences

    def test_language_model_preferences_javascript(self, config_manager):
        """Test model preferences for JavaScript development."""
        configurator = ClaudeConfigurator(config_manager)

        preferences = configurator._get_language_model_preferences("javascript")

        assert "React/Vue" in preferences
        assert "Node.js" in preferences
        assert "TypeScript" in preferences

    def test_language_model_preferences_rust(self, config_manager):
        """Test model preferences for Rust development."""
        configurator = ClaudeConfigurator(config_manager)

        preferences = configurator._get_language_model_preferences("rust")

        assert "Systems Programming" in preferences
        assert "Memory Safety" in preferences
        assert "Performance" in preferences

    def test_language_model_adaptations_python(self, config_manager):
        """Test model adaptations for Python."""
        configurator = ClaudeConfigurator(config_manager)

        adaptations = configurator._get_language_model_adaptations("python")

        assert "Pythonic" in adaptations
        assert "Type hints" in adaptations
        assert "pytest" in adaptations

    def test_language_model_adaptations_javascript(self, config_manager):
        """Test model adaptations for JavaScript."""
        configurator = ClaudeConfigurator(config_manager)

        adaptations = configurator._get_language_model_adaptations("javascript")

        assert "ES6+" in adaptations
        assert "React/Vue" in adaptations
        assert "Async/await" in adaptations

    def test_language_model_adaptations_rust(self, config_manager):
        """Test model adaptations for Rust."""
        configurator = ClaudeConfigurator(config_manager)

        adaptations = configurator._get_language_model_adaptations("rust")

        assert "Memory safety" in adaptations
        assert "ownership" in adaptations
        assert "Result types" in adaptations

    def test_mcp_servers_for_template_python(self, config_manager):
        """Test MCP server recommendations for Python."""
        configurator = ClaudeConfigurator(config_manager)

        servers = configurator._get_mcp_servers_for_template("python")

        assert "mas-sequential-thinking" in servers
        assert "context7" in servers
        assert "claude-context" in servers
        assert "Python documentation" in servers

    def test_mcp_servers_for_template_javascript(self, config_manager):
        """Test MCP server recommendations for JavaScript."""
        configurator = ClaudeConfigurator(config_manager)

        servers = configurator._get_mcp_servers_for_template("javascript")

        assert "React/Vue/Node.js" in servers
        assert "Framework migrations" in servers

    def test_mcp_servers_for_template_rust(self, config_manager):
        """Test MCP server recommendations for Rust."""
        configurator = ClaudeConfigurator(config_manager)

        servers = configurator._get_mcp_servers_for_template("rust")

        assert "Systems design" in servers
        assert "Rust documentation" in servers
        assert "crates" in servers

    def test_update_project_config(self, config_manager, temp_project_dir):
        """Test updating existing project configuration."""
        configurator = ClaudeConfigurator(config_manager)

        # Setup initial config
        configurator.setup_project_config(temp_project_dir)

        # Update configuration
        updates = {"adhd_profile.focus_duration": 30, "new_setting": "test_value"}

        configurator.update_project_config(temp_project_dir, updates)

        # Verify updates were applied
        config_file = temp_project_dir / ".dopemux" / "config.yaml"
        with open(config_file) as f:
            config = yaml.safe_load(f)

        assert config["adhd_profile"]["focus_duration"] == 30
        assert config["new_setting"] == "test_value"

    def test_update_project_config_nonexistent(self, config_manager, temp_project_dir):
        """Test updating configuration when project is not initialized."""
        configurator = ClaudeConfigurator(config_manager)

        updates = {"test": "value"}

        # Should not crash, but should print error message
        configurator.update_project_config(temp_project_dir, updates)

        # Config file should not exist
        config_file = temp_project_dir / ".dopemux" / "config.yaml"
        assert not config_file.exists()

    def test_get_project_status_initialized(self, config_manager, temp_project_dir):
        """Test getting project status for initialized project."""
        configurator = ClaudeConfigurator(config_manager)

        configurator.setup_project_config(temp_project_dir, template="python")

        status = configurator.get_project_status(temp_project_dir)

        assert status["dopemux_initialized"] is True
        assert status["claude_configured"] is True
        assert status["project_type"] == "python"
        assert status["config_files"]["claude.md"] is True
        assert status["config_files"]["config.yaml"] is True
        assert "adhd_features" in status

    def test_get_project_status_not_initialized(self, config_manager, temp_project_dir):
        """Test getting project status for non-initialized project."""
        configurator = ClaudeConfigurator(config_manager)

        status = configurator.get_project_status(temp_project_dir)

        assert status["dopemux_initialized"] is False
        assert status["claude_configured"] is False
        assert status["config_files"]["claude.md"] is False

    def test_copy_template_files_nonexistent(self, config_manager, temp_project_dir):
        """Test copying template files when template directory doesn't exist."""
        configurator = ClaudeConfigurator(config_manager)

        # Should not crash when template directory doesn't exist
        configurator._copy_template_files(temp_project_dir, "nonexistent_template")

        # No files should be copied
        assert len(list(temp_project_dir.iterdir())) == 0

    def test_language_specific_instructions_unknown_template(self, config_manager):
        """Test language instructions for unknown template."""
        configurator = ClaudeConfigurator(config_manager)

        instructions = configurator._get_language_specific_instructions("unknown")

        assert "Unknown" in instructions
        assert "best practices" in instructions

    def test_project_standards_unknown_template(self, config_manager):
        """Test project standards for unknown template."""
        configurator = ClaudeConfigurator(config_manager)

        standards = configurator._get_project_standards("unknown")

        assert "Unknown" in standards
        assert "best practices" in standards

    def test_session_specifics_unknown_template(self, config_manager):
        """Test session specifics for unknown template."""
        configurator = ClaudeConfigurator(config_manager)

        specifics = configurator._get_session_specifics("unknown")

        assert "Unknown" in specifics
        assert "state tracking" in specifics

    def test_language_model_preferences_unknown_template(self, config_manager):
        """Test model preferences for unknown template."""
        configurator = ClaudeConfigurator(config_manager)

        preferences = configurator._get_language_model_preferences("unknown")

        assert "Claude Sonnet" in preferences
        assert "DeepSeek Chat" in preferences

    def test_language_model_adaptations_unknown_template(self, config_manager):
        """Test model adaptations for unknown template."""
        configurator = ClaudeConfigurator(config_manager)

        adaptations = configurator._get_language_model_adaptations("unknown")

        assert "patterns" in adaptations
        assert "best practices" in adaptations

    def test_mcp_servers_for_unknown_template(self, config_manager):
        """Test MCP servers for unknown template."""
        configurator = ClaudeConfigurator(config_manager)

        servers = configurator._get_mcp_servers_for_template("unknown")

        assert "context7" in servers
        assert "claude-context" in servers
        assert "morphllm-fast-apply" in servers

    def test_setup_project_config_creates_all_template_content(
        self, config_manager, temp_project_dir
    ):
        """Test that setup creates content specific to the template throughout all files."""
        configurator = ClaudeConfigurator(config_manager)

        configurator.setup_project_config(temp_project_dir, template="rust")

        # Check multiple files contain template-specific content
        claude_md = (temp_project_dir / ".claude" / "claude.md").read_text()
        session_md = (temp_project_dir / ".claude" / "session.md").read_text()
        context_md = (temp_project_dir / ".claude" / "context.md").read_text()
        llms_md = (temp_project_dir / ".claude" / "llms.md").read_text()

        # All should reference Rust
        assert "Rust" in claude_md
        assert "Rust" in session_md
        assert "Rust" in context_md
        assert "Rust" in llms_md

    def test_file_content_integration(self, config_manager, temp_project_dir):
        """Test that all generated files have coherent, template-specific content."""
        configurator = ClaudeConfigurator(config_manager)

        configurator.setup_project_config(temp_project_dir, template="javascript")

        # Read all files
        files = {}
        for filename in ["claude.md", "session.md", "context.md", "llms.md"]:
            files[filename] = (temp_project_dir / ".claude" / filename).read_text()

        # Verify JavaScript/TypeScript references throughout
        js_terms = ["JavaScript", "TypeScript", "Node.js", "React", "npm", "javascript"]

        for filename, content in files.items():
            # Each file should contain at least some JS-specific terms
            js_found = any(term in content for term in js_terms)
            assert (
                js_found
            ), f"{filename} should contain JavaScript-specific content. Content preview: {content[:200]}..."
