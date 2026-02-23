import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import os
import shutil
import json
from services.adhd_engine.domains.attention.context_preserver import ContextPreserver, PreservedContext

class TestContextPreserver:
    @pytest.fixture
    def storage_path(self):
        """Create temp storage path."""
        path = ".test_context_snapshots"
        if os.path.exists(path):
            shutil.rmtree(path)
        os.makedirs(path)
        yield path
        if os.path.exists(path):
            shutil.rmtree(path)

    @pytest.fixture
    def mock_conport(self):
        client = AsyncMock()
        client.recent_decisions.return_value = [
            {"summary": "Refactored auth module", "timestamp": "2023-10-27T10:00:00"}
        ]
        return client

    @pytest.fixture
    def mock_serena(self):
        client = AsyncMock()
        # We need to mock the internal methods of ContextPreserver that use serena
        # or mock the serena client if the ContextPreserver called methods on it.
        # Looking at the code, ContextPreserver._get_active_files calls internal implementation
        # that currently returns empty list.
        # But logically, if we passed a client, we'd expect it to use it.
        # The current implementation of ContextPreserver has placeholder methods.
        # We will test the flow assuming these placeholders work or are mocked.
        return client

    @pytest.fixture
    def preserver(self, mock_conport, mock_serena, storage_path):
        return ContextPreserver(
            conport_client=mock_conport,
            serena_client=mock_serena,
            storage_path=storage_path
        )

    @pytest.mark.asyncio
    async def test_capture_context(self, preserver, mock_conport):
        """Test capturing context successfully."""
        # Mock internal helper methods to simulate data retrieval
        with patch.object(preserver, '_get_active_files', return_value=["main.py", "utils.py"]), \
             patch.object(preserver, '_get_cursor_positions', return_value={"main.py": 10}), \
             patch.object(preserver, '_get_recent_symbols', return_value=["UserClass"]), \
             patch.object(preserver, '_get_git_branch', return_value="feature/adhd-mode"):
            
            context = await preserver.capture_current_context("user123", "/tmp/workspace")
            
            assert isinstance(context, PreservedContext)
            assert context.active_files == ["main.py", "utils.py"]
            assert context.cursor_positions == {"main.py": 10}
            assert context.git_branch == "feature/adhd-mode"
            assert "Refactored auth module" in context.task_description
            
            # Verify file was saved
            saved_file = f"{preserver.storage_path}/user123_latest.json"
            assert os.path.exists(saved_file)
            
            with open(saved_file, 'r') as f:
                data = json.load(f)
                assert data['active_files'] == ["main.py", "utils.py"]

    @pytest.mark.asyncio
    async def test_restore_context(self, preserver):
        """Test restoring context from disk."""
        # 1. Create a dummy saved snapshot
        context = PreservedContext(
            active_files=["test.py"],
            task_description="Fixing bugs",
            timestamp=datetime.now()
        )
        await preserver._save_snapshot("user123", context)
        
        # 2. Restore
        result = await preserver.restore_context("user123")
        
        assert result is not None
        assert result['task'] == "Fixing bugs"
        assert result['active_files'] == ["test.py"]
        assert "restoration_tips" in result

    @pytest.mark.asyncio
    async def test_restore_no_context(self, preserver):
        """Test restoring when no file exists."""
        result = await preserver.restore_context("new_user")
        assert "error" in result
        assert result["error"] == "No saved context found"

    @pytest.mark.asyncio
    async def test_generate_mental_model(self, preserver):
        """Test mental model summary generation."""
        context = PreservedContext(
            task_description="Implementing generic tree",
            active_files=["tree.py", "node.py"],
            git_branch="feature/tree"
        )
        
        summary = await preserver._generate_mental_model(context)
        
        assert "Implementing generic tree" in summary
        assert "tree.py" in summary
        assert "feature/tree" in summary
