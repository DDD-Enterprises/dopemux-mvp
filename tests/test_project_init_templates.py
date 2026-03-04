"""
Tests for project template installation.
"""

from pathlib import Path
import pytest

from dopemux.project_init import ProjectInitializer


class TestTemplateInstallation:
    """Test template file installation during project initialization."""

    def test_install_templates_creates_all_files(self, tmp_path):
        """Verify all template files are created."""
        initializer = ProjectInitializer(tmp_path)
        initializer.install_templates()

        # Check .claude templates
        assert (tmp_path / ".claude" / "README.md").exists()
        assert (tmp_path / ".claude" / "PRIMER.md").exists()
        assert (tmp_path / ".claude" / "PROJECT_INSTRUCTIONS.MD").exists()
        assert (tmp_path / ".claude" / "claude.md").exists()

        # Check repo-root task-packets templates
        assert (tmp_path / "task-packets" / "README.md").exists()
        assert (tmp_path / "task-packets" / "STATUS.md").exists()
        assert (tmp_path / "task-packets" / "INDEX.md").exists()
        assert (tmp_path / "task-packets" / "CHECKLIST.md").exists()
        assert (tmp_path / "task-packets" / "TEMPLATE_TASK_PACKET.md").exists()

        # Check docs/90-adr templates
        assert (tmp_path / "docs" / "90-adr" / "TEMPLATE_ADR.md").exists()
        assert (tmp_path / "docs" / "90-adr" / "TEMPLATE_ADR_LIGHT.md").exists()
        assert (tmp_path / "docs" / "90-adr" / "TEMPLATE_ADR_RECORD.md").exists()

    def test_install_templates_skips_existing_files(self, tmp_path):
        """Verify existing files are not overwritten."""
        # Create a file with specific content
        claude_readme = tmp_path / ".claude" / "README.md"
        claude_readme.parent.mkdir(parents=True)
        test_content = "# My Custom README\n\nDo not overwrite this!"
        claude_readme.write_text(test_content)

        # Install templates
        initializer = ProjectInitializer(tmp_path)
        initializer.install_templates()

        # Verify content was not overwritten
        assert claude_readme.read_text() == test_content

        # Verify other files were still created
        assert (tmp_path / ".claude" / "PRIMER.md").exists()

    def test_install_templates_creates_directory_structure(self, tmp_path):
        """Verify directory structure is created correctly."""
        initializer = ProjectInitializer(tmp_path)
        initializer.install_templates()

        # Verify all directories exist
        assert (tmp_path / ".claude").is_dir()
        assert (tmp_path / "task-packets").is_dir()
        assert (tmp_path / "docs" / "90-adr").is_dir()

    def test_install_templates_with_missing_template_dir(self, tmp_path, monkeypatch):
        """Verify graceful handling when template directory is missing."""
        # Mock templates directory to not exist
        def mock_exists(self):
            if "templates/init" in str(self):
                return False
            return Path.exists(self)

        monkeypatch.setattr(Path, "exists", mock_exists)

        initializer = ProjectInitializer(tmp_path)
        # Should not raise an exception
        initializer.install_templates()

    def test_status_md_is_virgin(self, tmp_path):
        """Verify STATUS.md has project-agnostic content."""
        initializer = ProjectInitializer(tmp_path)
        initializer.install_templates()

        status = (tmp_path / "task-packets" / "STATUS.md").read_text()

        # Should not contain project-specific subsystems
        assert "PACKET_031" not in status
        assert "PACKET_032" not in status
        assert "Memory Stack" not in status

        # Should contain virgin template markers
        assert "[Add your subsystems here]" in status

    def test_index_md_is_virgin(self, tmp_path):
        """Verify INDEX.md has project-agnostic content."""
        initializer = ProjectInitializer(tmp_path)
        initializer.install_templates()

        index = (tmp_path / "task-packets" / "INDEX.md").read_text()

        # Should be empty catalog
        assert "## Active" in index
        assert "- None" in index
