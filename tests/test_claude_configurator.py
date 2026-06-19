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
        assert "pal" in servers
        assert "claude-context" in servers
        assert "Python documentation" in servers

    def test_mcp_servers_for_template_javascript(self, config_manager):
        """Test MCP server recommendations for JavaScript."""
        configurator = ClaudeConfigurator(config_manager)

        servers = configurator._get_mcp_servers_for_template("javascript")

        assert "React/Vue/Node.js" in servers
        assert "claude-context" in servers
        assert "exa" in servers

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

        assert "pal" in servers
        assert "claude-context" in servers

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
            assert js_found, (
                f"{filename} should contain JavaScript-specific content. Content preview: {content[:200]}..."
            )


class TestPersonaInjection:
    """Tests for role/persona injection during `dopemux start --role X`.

    Persona activation calls ``setup_project_config(project_path, role=role)``.
    It must inject the role's assembled guidelines WITHOUT clobbering existing
    doctrine files (claude.md / session.md / etc.).
    """

    PERSONA_SENTINEL = "DEVELOPER_PERSONA_SENTINEL guidelines body"

    def _write_persona(self, project_dir, role="developer"):
        """Create a resolvable persona file for the given role."""
        personas_dir = project_dir / ".claude" / "personas"
        personas_dir.mkdir(parents=True, exist_ok=True)
        (personas_dir / f"{role}.agent.md").write_text(
            f"# {role} persona\n\n{self.PERSONA_SENTINEL}\n"
        )

    def test_role_injects_persona_into_active_persona_file(
        self, config_manager, temp_project_dir
    ):
        """`--role developer` writes the assembled guidelines to active-persona.md."""
        self._write_persona(temp_project_dir, "developer")
        configurator = ClaudeConfigurator(config_manager)

        configurator.setup_project_config(temp_project_dir, role="developer")

        active = temp_project_dir / ".claude" / "active-persona.md"
        assert active.exists(), "active-persona.md should be created on role activation"
        content = active.read_text()
        assert self.PERSONA_SENTINEL in content
        assert "developer" in content.lower()

    def test_role_does_not_regenerate_doctrine_files(
        self, config_manager, temp_project_dir
    ):
        """Role activation must NOT regenerate doctrine files (early-return contract)."""
        self._write_persona(temp_project_dir, "developer")
        configurator = ClaudeConfigurator(config_manager)

        configurator.setup_project_config(temp_project_dir, role="developer")

        claude_dir = temp_project_dir / ".claude"
        # Doctrine files are only written in the no-role generation path.
        assert not (claude_dir / "session.md").exists()
        assert not (claude_dir / "context.md").exists()
        assert not (claude_dir / "llms.md").exists()

    def test_role_does_not_clobber_existing_claude_md(
        self, config_manager, temp_project_dir
    ):
        """Existing claude.md doctrine content is preserved; a reference is added."""
        claude_dir = temp_project_dir / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        (claude_dir / "claude.md").write_text(
            "# Project Doctrine\n\nEXISTING_DOCTRINE_SENTINEL must survive.\n"
        )
        self._write_persona(temp_project_dir, "developer")
        configurator = ClaudeConfigurator(config_manager)

        configurator.setup_project_config(temp_project_dir, role="developer")

        claude_md = (claude_dir / "claude.md").read_text()
        assert "EXISTING_DOCTRINE_SENTINEL must survive." in claude_md
        assert "active-persona.md" in claude_md

    def test_role_injection_is_idempotent(self, config_manager, temp_project_dir):
        """Re-activating the same role does not duplicate the reference block."""
        claude_dir = temp_project_dir / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        (claude_dir / "claude.md").write_text("# Doctrine\n\nbody\n")
        self._write_persona(temp_project_dir, "developer")
        configurator = ClaudeConfigurator(config_manager)

        configurator.setup_project_config(temp_project_dir, role="developer")
        configurator.setup_project_config(temp_project_dir, role="developer")

        claude_md = (claude_dir / "claude.md").read_text()
        assert claude_md.count("DOPEMUX:ACTIVE-PERSONA:START") == 1
        assert claude_md.count("DOPEMUX:ACTIVE-PERSONA:END") == 1

    def test_unresolvable_role_fails_closed(self, config_manager, temp_project_dir):
        """A role with no guidelines writes no active-persona.md (no false success)."""
        configurator = ClaudeConfigurator(config_manager)

        configurator.setup_project_config(temp_project_dir, role="no-such-role")

        active = temp_project_dir / ".claude" / "active-persona.md"
        assert not active.exists()

    def test_returns_true_on_injection_false_on_failclosed(
        self, config_manager, temp_project_dir
    ):
        """Return value reports injection status for a truthful CLI message."""
        configurator = ClaudeConfigurator(config_manager)

        assert (
            configurator.setup_project_config(temp_project_dir, role="no-such-role")
            is False
        )

        self._write_persona(temp_project_dir, "developer")
        assert (
            configurator.setup_project_config(temp_project_dir, role="developer")
            is True
        )

    def test_unresolvable_role_fails_closed_even_with_global_instructions(
        self, config_manager, temp_project_dir
    ):
        """Global instructions must not mask an unresolvable persona.

        ``assemble_instructions`` appends role-independent global guidelines, so
        fail-closed must gate on the persona resolving — not on combined output.
        """
        instr_dir = temp_project_dir / "config" / "instructions"
        instr_dir.mkdir(parents=True, exist_ok=True)
        (instr_dir / "house.instructions.md").write_text("GLOBAL_RULE always.\n")
        configurator = ClaudeConfigurator(config_manager)

        configurator.setup_project_config(temp_project_dir, role="no-such-role")

        active = temp_project_dir / ".claude" / "active-persona.md"
        assert not active.exists()

    def test_orphaned_end_marker_does_not_duplicate(
        self, config_manager, temp_project_dir
    ):
        """A pre-existing orphaned END marker must not cause unbounded duplication."""
        claude_dir = temp_project_dir / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        # Malformed prior state: an END marker with no matching START.
        (claude_dir / "claude.md").write_text(
            "# Doctrine\n\nKEEP_ME line.\n\n<!-- DOPEMUX:ACTIVE-PERSONA:END -->\n"
        )
        self._write_persona(temp_project_dir, "developer")
        configurator = ClaudeConfigurator(config_manager)

        configurator.setup_project_config(temp_project_dir, role="developer")
        configurator.setup_project_config(temp_project_dir, role="developer")

        claude_md = (claude_dir / "claude.md").read_text()
        assert "KEEP_ME line." in claude_md
        assert claude_md.count("DOPEMUX:ACTIVE-PERSONA:START") == 1
        assert claude_md.count("DOPEMUX:ACTIVE-PERSONA:END") == 1

    def test_switching_roles_replaces_block(self, config_manager, temp_project_dir):
        """Activating role B after role A replaces the block (no stale role A)."""
        claude_dir = temp_project_dir / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        (claude_dir / "claude.md").write_text("# Doctrine\n\nbody\n")
        self._write_persona(temp_project_dir, "developer")
        self._write_persona(temp_project_dir, "reviewer")
        configurator = ClaudeConfigurator(config_manager)

        configurator.setup_project_config(temp_project_dir, role="developer")
        configurator.setup_project_config(temp_project_dir, role="reviewer")

        claude_md = (claude_dir / "claude.md").read_text()
        assert claude_md.count("DOPEMUX:ACTIVE-PERSONA:START") == 1
        assert "Role **reviewer** is active" in claude_md
        assert "Role **developer** is active" not in claude_md


# ---------------------------------------------------------------------------
# New tests for findings F1-F5
# ---------------------------------------------------------------------------


class TestF1CatalogAliases:
    """F1: Catalog role names (developer, architect, reviewer, debugger, ops)
    must resolve to an existing persona via the alias table.
    """

    def _write_persona(self, project_dir, stem):
        personas_dir = project_dir / ".claude" / "personas"
        personas_dir.mkdir(parents=True, exist_ok=True)
        (personas_dir / f"{stem}.agent.md").write_text(
            f"# {stem}\n\nSENTINEL_CONTENT for {stem}.\n"
        )

    def test_developer_alias_resolves_to_principal_software_engineer(
        self, config_manager, temp_project_dir
    ):
        """'developer' (THE default role) must resolve via alias."""
        self._write_persona(temp_project_dir, "principal-software-engineer")
        configurator = ClaudeConfigurator(config_manager)

        result = configurator.setup_project_config(temp_project_dir, role="developer")

        assert result is True
        active = temp_project_dir / ".claude" / "active-persona.md"
        assert active.exists()
        assert (
            "principal-software-engineer" in active.read_text().lower()
            or "SENTINEL_CONTENT" in active.read_text()
        )

    def test_architect_alias_resolves(self, config_manager, temp_project_dir):
        """'architect' must resolve to se-system-architecture-reviewer."""
        self._write_persona(temp_project_dir, "se-system-architecture-reviewer")
        configurator = ClaudeConfigurator(config_manager)

        result = configurator.setup_project_config(temp_project_dir, role="architect")

        assert result is True
        assert (temp_project_dir / ".claude" / "active-persona.md").exists()

    def test_reviewer_alias_resolves(self, config_manager, temp_project_dir):
        """'reviewer' must resolve to wg-code-sentinel (or se-security-reviewer)."""
        self._write_persona(temp_project_dir, "wg-code-sentinel")
        configurator = ClaudeConfigurator(config_manager)

        result = configurator.setup_project_config(temp_project_dir, role="reviewer")

        assert result is True

    def test_debugger_alias_resolves(self, config_manager, temp_project_dir):
        """'debugger' must resolve to principal-software-engineer."""
        self._write_persona(temp_project_dir, "principal-software-engineer")
        configurator = ClaudeConfigurator(config_manager)

        result = configurator.setup_project_config(temp_project_dir, role="debugger")

        assert result is True

    def test_ops_alias_resolves(self, config_manager, temp_project_dir):
        """'ops' must resolve to devops-expert."""
        self._write_persona(temp_project_dir, "devops-expert")
        configurator = ClaudeConfigurator(config_manager)

        result = configurator.setup_project_config(temp_project_dir, role="ops")

        assert result is True

    def test_unresolvable_role_clears_stale_active_persona(
        self, config_manager, temp_project_dir
    ):
        """When a role resolves to no persona, stale active-persona.md is removed (F1)."""
        claude_dir = temp_project_dir / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        # Pre-plant a stale active-persona.md from a prior activation.
        stale = claude_dir / "active-persona.md"
        stale.write_text("# stale content\n")

        configurator = ClaudeConfigurator(config_manager)
        result = configurator.setup_project_config(
            temp_project_dir, role="no-such-role"
        )

        assert result is False
        assert not stale.exists(), (
            "Stale active-persona.md must be cleared on fail-closed"
        )

    def test_unresolvable_role_clears_stale_managed_block(
        self, config_manager, temp_project_dir
    ):
        """When a role resolves to no persona, the managed block in claude.md is removed (F1)."""
        claude_dir = temp_project_dir / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        # Pre-plant a claude.md with a managed block from a prior activation.
        prior_block = (
            "# Doctrine\n\nKEEP_ME.\n\n"
            "<!-- DOPEMUX:ACTIVE-PERSONA:START -->\n"
            "## Active Persona\n\n@active-persona.md\n"
            "<!-- DOPEMUX:ACTIVE-PERSONA:END -->\n"
        )
        (claude_dir / "claude.md").write_text(prior_block)
        configurator = ClaudeConfigurator(config_manager)

        configurator.setup_project_config(temp_project_dir, role="no-such-role")

        content = (claude_dir / "claude.md").read_text()
        assert "KEEP_ME." in content
        assert "DOPEMUX:ACTIVE-PERSONA:START" not in content
        assert "DOPEMUX:ACTIVE-PERSONA:END" not in content


class TestF2CreateMinimalClaudeMd:
    """F2: When claude.md does not exist, _inject_persona must create a minimal
    one that imports the persona via @active-persona.md.
    """

    def _write_persona(self, project_dir, role="developer"):
        personas_dir = project_dir / ".claude" / "personas"
        personas_dir.mkdir(parents=True, exist_ok=True)
        (personas_dir / f"{role}.agent.md").write_text(f"# {role} persona\n\nBODY.\n")

    def test_creates_minimal_claude_md_when_absent(
        self, config_manager, temp_project_dir
    ):
        """Injecting a persona must create a minimal claude.md if none exists (F2)."""
        self._write_persona(temp_project_dir, "developer")
        configurator = ClaudeConfigurator(config_manager)

        result = configurator.setup_project_config(temp_project_dir, role="developer")

        assert result is True
        claude_md = temp_project_dir / ".claude" / "claude.md"
        assert claude_md.exists(), "claude.md must be created when absent"
        content = claude_md.read_text()
        # Must contain the @import so the harness loads the persona.
        assert "@active-persona.md" in content
        # Must contain the managed markers.
        assert "DOPEMUX:ACTIVE-PERSONA:START" in content

    def test_minimal_claude_md_not_clobbered_when_exists(
        self, config_manager, temp_project_dir
    ):
        """Existing claude.md is never overwritten by F2 creation logic."""
        claude_dir = temp_project_dir / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        original = "# Pre-existing Doctrine\n\nIMPORTANT_CONTENT_MUST_SURVIVE.\n"
        (claude_dir / "claude.md").write_text(original)
        self._write_persona(temp_project_dir, "developer")
        configurator = ClaudeConfigurator(config_manager)

        configurator.setup_project_config(temp_project_dir, role="developer")

        content = (claude_dir / "claude.md").read_text()
        assert "IMPORTANT_CONTENT_MUST_SURVIVE." in content

    def test_minimal_claude_md_is_loadable_on_re_activation(
        self, config_manager, temp_project_dir
    ):
        """Re-activating a role after the minimal claude.md was auto-created is
        idempotent — no duplicate markers."""
        self._write_persona(temp_project_dir, "developer")
        configurator = ClaudeConfigurator(config_manager)

        configurator.setup_project_config(temp_project_dir, role="developer")
        configurator.setup_project_config(temp_project_dir, role="developer")

        content = (temp_project_dir / ".claude" / "claude.md").read_text()
        assert content.count("DOPEMUX:ACTIVE-PERSONA:START") == 1
        assert content.count("DOPEMUX:ACTIVE-PERSONA:END") == 1


class TestF3PackagedPersonaFallback:
    """F3: get_persona_content must fall back to packaged personas when the
    project .claude/personas directory is absent or does not contain the file.
    """

    def test_packaged_fallback_resolves_developer(self, temp_project_dir):
        """'developer' resolves even when project has no .claude/personas dir."""
        from dopemux.claude.instruction_manager import InstructionManager

        # Ensure no local personas directory exists.
        assert not (temp_project_dir / ".claude" / "personas").exists()

        manager = InstructionManager(temp_project_dir)
        content = manager.get_persona_content("developer")

        assert content is not None, (
            "'developer' should resolve via packaged fallback when no local personas dir"
        )
        assert len(content.strip()) > 0

    def test_packaged_fallback_resolves_architect(self, temp_project_dir):
        """'architect' resolves via packaged fallback."""
        from dopemux.claude.instruction_manager import InstructionManager

        manager = InstructionManager(temp_project_dir)
        content = manager.get_persona_content("architect")

        assert content is not None

    def test_packaged_fallback_resolves_ops(self, temp_project_dir):
        """'ops' resolves via packaged fallback to devops-expert."""
        from dopemux.claude.instruction_manager import InstructionManager

        manager = InstructionManager(temp_project_dir)
        content = manager.get_persona_content("ops")

        assert content is not None

    def test_project_local_persona_takes_precedence_over_packaged(
        self, temp_project_dir
    ):
        """A project-local persona overrides the packaged version."""
        from dopemux.claude.instruction_manager import InstructionManager

        personas_dir = temp_project_dir / ".claude" / "personas"
        personas_dir.mkdir(parents=True, exist_ok=True)
        # Write a local override for the alias target.
        (personas_dir / "principal-software-engineer.agent.md").write_text(
            "# LOCAL_OVERRIDE\n\nLOCAL_SENTINEL.\n"
        )

        manager = InstructionManager(temp_project_dir)
        content = manager.get_persona_content("developer")

        assert content is not None
        assert "LOCAL_SENTINEL" in content, (
            "Project-local persona must take precedence over packaged fallback"
        )

    def test_full_injection_works_with_no_local_personas(
        self, config_manager, temp_project_dir
    ):
        """setup_project_config resolves and injects a persona via packaged fallback (F3)."""
        # No .claude/personas directory — simulates a `dopemux init` project.
        configurator = ClaudeConfigurator(config_manager)

        result = configurator.setup_project_config(temp_project_dir, role="developer")

        assert result is True
        active = temp_project_dir / ".claude" / "active-persona.md"
        assert active.exists()


class TestF4WizardEnvPathInjects:
    """F4: Persona injection must be driven by requested_role (the resolved
    value), not the raw Click `role` option, so wizard/env/default paths
    also inject a persona.
    """

    def test_cli_injection_uses_requested_role_variable(self, temp_project_dir):
        """The injection block in cli.py now reads `requested_role`, not `role`.
        Verify this at the source-text level — the authoritative unit test for
        the wire-up when no full CLI invocation is practical.
        """
        import pathlib

        cli_source = pathlib.Path(__file__).parent.parent / "src" / "dopemux" / "cli.py"
        source = cli_source.read_text()

        # The configure role-based instructions block must reference
        # `requested_role` as the condition, not bare `role`.
        assert "if requested_role:" in source, (
            "cli.py must gate persona injection on `requested_role`, not raw `role`"
        )
        # And must pass requested_role to setup_project_config.
        assert "role=requested_role" in source, (
            "cli.py must pass requested_role to setup_project_config"
        )
        # Find the INJECTION-SITE ClaudeConfigurator call (second occurrence —
        # the first is in the `dopemux init` path).
        first_idx = source.find("ClaudeConfigurator(config_manager)")
        second_idx = source.find("ClaudeConfigurator(config_manager)", first_idx + 1)
        assert second_idx != -1, "Expected a second ClaudeConfigurator instantiation"
        # The `if requested_role:` block should precede the second call.
        relevant_slice = source[max(0, second_idx - 400) : second_idx]
        assert "requested_role" in relevant_slice, (
            "The `if requested_role:` guard must immediately precede the "
            "ClaudeConfigurator instantiation at the injection site"
        )

    def test_dry_run_does_not_write_persona(self, config_manager, temp_project_dir):
        """The dry_run path exits before persona injection — active-persona.md must
        not be written during a dry run."""
        # The dry_run gate in cli.py calls ctx.exit(0) before the injection block.
        # Test directly: calling setup_project_config only happens when not dry_run.
        # We verify here that setup_project_config with a valid role DOES write the
        # file (so the absence in dry-run is meaningful), and separately confirm the
        # CLI source has the correct guard.
        # If developer resolves (packaged fallback), calling setup does inject.
        configurator = ClaudeConfigurator(config_manager)
        result = configurator.setup_project_config(temp_project_dir, role="developer")
        assert result is True
        active = temp_project_dir / ".claude" / "active-persona.md"
        assert active.exists()

        # Confirm cli.py dry_run exit is BEFORE the injection block in source order.
        import pathlib

        cli_source = pathlib.Path(__file__).parent.parent / "src" / "dopemux" / "cli.py"
        source = cli_source.read_text()
        dry_run_exit_idx = source.find("ctx.exit(0)")
        injection_idx = source.find("role=requested_role")
        assert dry_run_exit_idx < injection_idx, (
            "ctx.exit(0) for dry_run must appear before the persona injection call"
        )


class TestF5AtImportSyntax:
    """F5: The managed block must use @active-persona.md (harness import syntax),
    not a Markdown link.
    """

    def _write_persona(self, project_dir, role="developer"):
        personas_dir = project_dir / ".claude" / "personas"
        personas_dir.mkdir(parents=True, exist_ok=True)
        (personas_dir / f"{role}.agent.md").write_text(f"# {role}\n\nBODY.\n")

    def test_managed_block_uses_at_import_not_markdown_link(
        self, config_manager, temp_project_dir
    ):
        """The managed block must contain @active-persona.md, not a [link](...) (F5)."""
        claude_dir = temp_project_dir / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        (claude_dir / "claude.md").write_text("# Doctrine\n\nbody\n")
        self._write_persona(temp_project_dir, "developer")
        configurator = ClaudeConfigurator(config_manager)

        configurator.setup_project_config(temp_project_dir, role="developer")

        content = (claude_dir / "claude.md").read_text()
        # Must have the @import syntax.
        assert "@active-persona.md" in content, (
            "The managed block must use @active-persona.md import syntax"
        )
        # Must NOT have the old Markdown link syntax.
        assert "[active-persona.md](active-persona.md)" not in content, (
            "The old Markdown link syntax must not be emitted"
        )

    def test_minimal_created_claude_md_uses_at_import(
        self, config_manager, temp_project_dir
    ):
        """The auto-created minimal claude.md (F2) must also use @import syntax (F5)."""
        self._write_persona(temp_project_dir, "developer")
        configurator = ClaudeConfigurator(config_manager)

        configurator.setup_project_config(temp_project_dir, role="developer")

        content = (temp_project_dir / ".claude" / "claude.md").read_text()
        assert "@active-persona.md" in content
        assert "[active-persona.md](active-persona.md)" not in content

    def test_at_import_survives_re_activation(self, config_manager, temp_project_dir):
        """Re-activating a role preserves @import syntax — no regression to link form."""
        claude_dir = temp_project_dir / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        (claude_dir / "claude.md").write_text("# Doctrine\n\nbody\n")
        self._write_persona(temp_project_dir, "developer")
        configurator = ClaudeConfigurator(config_manager)

        configurator.setup_project_config(temp_project_dir, role="developer")
        configurator.setup_project_config(temp_project_dir, role="developer")

        content = (claude_dir / "claude.md").read_text()
        assert "@active-persona.md" in content
        assert "[active-persona.md](active-persona.md)" not in content
