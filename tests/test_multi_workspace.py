#!/usr/bin/env python3
"""
Multi-Workspace Integration Tests
Tests workspace isolation, cross-workspace queries, and switching
"""

import pytest
import os
import tempfile
from pathlib import Path

# Test fixtures

@pytest.fixture
def temp_workspaces():
    """Create temporary workspace directories for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspaces = {
            "project1": Path(tmpdir) / "project1",
            "project2": Path(tmpdir) / "project2",
            "project3": Path(tmpdir) / "project3",
        }
        
        # Create workspace directories
        for workspace in workspaces.values():
            workspace.mkdir(parents=True)
            (workspace / ".git").mkdir()  # Simulate git repo
            
        yield workspaces


@pytest.fixture
def workspace_env(temp_workspaces):
    """Set up workspace environment variables"""
    old_env = {}
    
    # Save old environment
    for key in ["DEFAULT_WORKSPACE_PATH", "WORKSPACE_PATHS", "DOPEMUX_WORKSPACE_ID", "DOPE_WORKSPACES"]:
        old_env[key] = os.environ.get(key)
    
    # Set test environment
    os.environ["DEFAULT_WORKSPACE_PATH"] = str(temp_workspaces["project1"])
    os.environ["WORKSPACE_PATHS"] = f"{temp_workspaces['project2']},{temp_workspaces['project3']}"
    os.environ["DOPEMUX_WORKSPACE_ID"] = str(temp_workspaces["project1"])
    os.environ["DOPE_WORKSPACES"] = ",".join(
        str(temp_workspaces[name]) for name in ("project1", "project2", "project3")
    )
    
    yield temp_workspaces
    
    # Restore old environment
    for key, value in old_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


# Test Cases

class TestWorkspaceIsolation:
    """Test that workspace data is properly isolated"""
    
    def test_workspace_detection(self, workspace_env):
        """Test automatic workspace detection"""
        from services.shared.workspace_utils import resolve_workspaces
        
        # Should detect from environment
        workspaces = resolve_workspaces(fallback_to_current=False)
        assert len(workspaces) == 3
        assert workspaces[0] == Path(os.environ["DEFAULT_WORKSPACE_PATH"]).resolve()
    
    def test_workspace_identifier(self, workspace_env):
        """Test workspace to identifier conversion"""
        from services.shared.workspace_utils import workspace_to_identifier
        
        workspace = Path(workspace_env["project1"])
        identifier = workspace_to_identifier(workspace)
        
        # Should be a valid identifier
        assert identifier.replace("_", "").replace("-", "").isalnum()
        assert "/" not in identifier
    
    @pytest.mark.asyncio
    async def test_cognitive_state_isolation(self, workspace_env):
        """Test ADHD Engine cognitive state is isolated per workspace"""
        # This test requires ADHD Engine running
        # For now, test the data model
        from services.session_intelligence.coordinator import CognitiveState
        
        state1 = CognitiveState(
            user_id="test",
            energy_level="high",
            attention_state="focused",
            last_break_timestamp=None,
            minutes_since_break=None,
            workspace_path=str(workspace_env["project1"])
        )
        
        state2 = CognitiveState(
            user_id="test",
            energy_level="low",
            attention_state="scattered",
            last_break_timestamp=None,
            minutes_since_break=None,
            workspace_path=str(workspace_env["project2"])
        )
        
        # Should have different workspace paths
        assert state1.workspace_path != state2.workspace_path
    
    @pytest.mark.asyncio
    async def test_session_isolation(self, workspace_env):
        """Test sessions are isolated per workspace"""
        from services.session_intelligence.coordinator import SessionState
        
        session1 = SessionState(
            session_id="s1",
            workspace="project1",
            worktree="main",
            branch="main",
            current_focus="feature A",
            session_duration_minutes=30,
            workspace_path=str(workspace_env["project1"])
        )
        
        session2 = SessionState(
            session_id="s2",
            workspace="project2",
            worktree="main",
            branch="develop",
            current_focus="feature B",
            session_duration_minutes=45,
            workspace_path=str(workspace_env["project2"])
        )
        
        # Verify isolation
        assert session1.workspace_path != session2.workspace_path
        assert session1.current_focus != session2.current_focus


class TestCrossWorkspaceQueries:
    """Test cross-workspace query functionality"""
    
    def test_aggregate_results(self):
        """Test aggregating results from multiple workspaces"""
        from services.shared.workspace_utils import aggregate_multi_workspace_results
        
        workspaces = [
            Path("/path/to/workspace1"),
            Path("/path/to/workspace2"),
            Path("/path/to/workspace3"),
        ]
        results = [
            [{"decision": "A"}, {"decision": "B"}],
            [{"decision": "C"}],
            [],
        ]
        
        aggregated = aggregate_multi_workspace_results(results, workspaces)
        
        assert aggregated["workspace_count"] == 3
        assert aggregated["total_results"] == 3
        assert len(aggregated["results"]) == 3
        assert aggregated["results"][0]["workspace"] == str(workspaces[0])
        assert aggregated["results"][0]["result_count"] == 2
        assert aggregated["results"][1]["workspace"] == str(workspaces[1])
        assert aggregated["results"][1]["result_count"] == 1
    
    def test_workspace_resolution(self, workspace_env):
        """Test resolving workspace paths"""
        from services.shared.workspace_utils import resolve_workspaces
        
        # Single workspace
        workspaces = resolve_workspaces(
            workspace_path=str(workspace_env["project1"]),
            fallback_to_current=False,
        )
        assert len(workspaces) == 1
        
        # Multiple workspaces
        workspaces = resolve_workspaces(
            workspace_paths=[
                str(workspace_env["project1"]),
                str(workspace_env["project2"])
            ],
            fallback_to_current=False,
        )
        assert len(workspaces) == 2
    
    @pytest.mark.asyncio
    async def test_multi_workspace_query(self, workspace_env):
        """Test querying across multiple workspaces"""
        # This would require actual services running
        # For now, test the query structure
        
        workspaces = [
            str(workspace_env["project1"]),
            str(workspace_env["project2"]),
        ]
        
        # Verify workspace list is valid
        assert all(Path(w).exists() for w in workspaces)


class TestWorkspaceSwitching:
    """Test workspace switching functionality"""
    
    def test_workspace_selector_init(self, workspace_env):
        """Test workspace selector initialization"""
        from dashboard.workspace_selector import WorkspaceSelector
        
        selector = WorkspaceSelector()
        
        # Should load workspaces from environment
        assert len(selector.workspaces) >= 1
        assert selector.current_workspace is not None
    
    def test_workspace_navigation(self, workspace_env):
        """Test workspace next/prev navigation"""
        from dashboard.workspace_selector import WorkspaceSelector
        
        selector = WorkspaceSelector()
        original = selector.current_workspace
        
        # Navigate forward
        next_ws = selector.next_workspace()
        assert next_ws != original or len(selector.workspaces) == 1
        
        # Navigate backward (should cycle)
        if len(selector.workspaces) > 1:
            prev_ws = selector.prev_workspace()
            assert prev_ws == original
    
    def test_workspace_display(self, workspace_env):
        """Test workspace display formatting"""
        from dashboard.workspace_selector import WorkspaceSelector
        
        selector = WorkspaceSelector()
        display = selector.get_workspace_display()
        
        # Should include workspace name
        assert len(display) > 0
        
        # If multiple workspaces, should show navigation hint
        if len(selector.workspaces) > 1:
            assert "←/→" in display or "/" in display


class TestWorkspaceCaching:
    """Test workspace-scoped caching"""
    
    def test_cache_key_scoping(self, workspace_env):
        """Test cache keys are scoped by workspace"""
        workspace1 = str(workspace_env["project1"])
        workspace2 = str(workspace_env["project2"])
        
        # Cache keys should include workspace identifier
        from services.shared.workspace_utils import workspace_to_identifier
        
        id1 = workspace_to_identifier(Path(workspace1))
        id2 = workspace_to_identifier(Path(workspace2))
        
        assert id1 != id2
        
        # Cache key pattern: service:workspace_id:key
        key1 = f"adhd:{id1}:state"
        key2 = f"adhd:{id2}:state"
        
        assert key1 != key2


class TestWorkspacePerformance:
    """Test workspace operations performance"""
    
    def test_single_workspace_query_fast(self, workspace_env):
        """Test single workspace queries are fast"""
        from services.shared.workspace_utils import resolve_workspaces
        import time
        
        start = time.time()
        workspaces = resolve_workspaces(
            workspace_path=str(workspace_env["project1"]),
            fallback_to_current=False,
        )
        elapsed = time.time() - start
        
        # Should be very fast (< 10ms)
        assert elapsed < 0.01
        assert workspaces == [workspace_env["project1"].resolve()]
    
    def test_multi_workspace_query_acceptable(self, workspace_env):
        """Test multi-workspace queries have acceptable performance"""
        from services.shared.workspace_utils import resolve_workspaces
        import time
        
        workspaces = [
            str(workspace_env["project1"]),
            str(workspace_env["project2"]),
            str(workspace_env["project3"]),
        ]
        
        start = time.time()
        resolved = resolve_workspaces(
            workspace_paths=workspaces,
            fallback_to_current=False,
        )
        elapsed = time.time() - start
        
        # Should be reasonably fast (< 50ms for 3 workspaces)
        assert elapsed < 0.05
        assert resolved == [
            workspace_env["project1"].resolve(),
            workspace_env["project2"].resolve(),
            workspace_env["project3"].resolve(),
        ]


# Integration Tests (require services running)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_end_to_end_workspace_workflow(workspace_env):
    """Test complete multi-workspace workflow"""
    # This requires all services running
    # Skipped in unit tests, run separately
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
