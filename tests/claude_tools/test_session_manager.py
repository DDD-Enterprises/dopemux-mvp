"""
Unit tests for Claude-Code-Tools session manager.

Tests unified session search and resume functionality.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

from dopemux.claude_tools.session_manager import SessionManager
from dopemux.adhd.context_manager import ContextManager


class TestSessionManager:
    """Test SessionManager functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_context_manager = Mock()
        self.session_manager = SessionManager(self.mock_context_manager)

    def test_find_sessions_dopemux(self):
        """Test finding Dopemux sessions."""
        # Mock context manager to return sessions
        mock_sessions = [
            {
                'session_id': 'test_session_1',
                'timestamp': datetime.now().isoformat(),
                'current_goal': 'Implement feature',
                'message': 'Working on authentication',
                'git_branch': 'main',
                'open_files': [{'path': 'auth.py'}]
            }
        ]
        self.mock_context_manager.list_sessions.return_value = mock_sessions

        # Mock other session sources to return empty
        self.session_manager._find_claude_sessions = Mock(return_value=[])
        self.session_manager._find_codex_sessions = Mock(return_value=[])

        sessions = self.session_manager.find_sessions()

        assert len(sessions) == 1
        assert sessions[0]['agent'] == 'dopemux'
        assert sessions[0]['id'] == 'test_session_1'

    def test_find_sessions_with_filter(self):
        """Test finding sessions with agent filter."""
        # Mock Dopemux sessions
        mock_sessions = [
            {
                'session_id': 'dopemux_session',
                'timestamp': datetime.now().isoformat(),
                'current_goal': 'Test',
                'message': 'Dopemux work',
                'git_branch': 'main',
                'open_files': []
            }
        ]
        self.mock_context_manager.list_sessions.return_value = mock_sessions

        # Mock Claude sessions
        self.session_manager._find_claude_sessions = Mock(return_value=[
            {
                'id': 'claude_session',
                'agent': 'claude',
                'timestamp': datetime.now(),
                'project': 'claude',
                'message': 'Claude work'
            }
        ])
        self.session_manager._find_codex_sessions = Mock(return_value=[])

        # Filter for Claude only
        sessions = self.session_manager.find_sessions(agent_filter='claude')

        assert len(sessions) == 1
        assert sessions[0]['agent'] == 'claude'

    def test_find_sessions_with_keywords(self):
        """Test finding sessions with keyword search."""
        # Mock Dopemux sessions with different messages
        mock_sessions = [
            {
                'session_id': 'session1',
                'timestamp': datetime.now().isoformat(),
                'message': 'Working on authentication system',
                'current_goal': 'Auth implementation'
            },
            {
                'session_id': 'session2',
                'timestamp': datetime.now().isoformat(),
                'message': 'Database optimization work',
                'current_goal': 'DB tuning'
            }
        ]
        self.mock_context_manager.list_sessions.return_value = mock_sessions

        # Mock other sources empty
        self.session_manager._find_claude_sessions = Mock(return_value=[])
        self.session_manager._find_codex_sessions = Mock(return_value=[])

        # Search for 'authentication'
        sessions = self.session_manager.find_sessions(keywords='authentication')

        assert len(sessions) == 1
        assert 'authentication' in sessions[0]['message']

    def test_session_matches(self):
        """Test session matching logic."""
        session_data = {'message': 'Working on authentication', 'agent': 'dopemux'}

        # Test keyword matching
        assert self.session_manager._session_matches(session_data, 'authentication', None)

        # Test agent filtering
        assert self.session_manager._session_matches(session_data, None, 'dopemux')

        # Test no match
        assert not self.session_manager._session_matches(session_data, 'database', None)
        assert not self.session_manager._session_matches(session_data, None, 'claude')

    def test_group_sessions_by_time(self):
        """Test time-based session grouping."""
        now = datetime.now()
        sessions = [
            {'timestamp': now},  # Today
            {'timestamp': now - timedelta(days=1)},  # Yesterday
            {'timestamp': now - timedelta(days=5)},  # This week
            {'timestamp': now - timedelta(days=20)}  # Older
        ]

        grouped = self.session_manager._group_sessions_by_time(sessions)

        assert len(grouped['Today']) == 1
        assert len(grouped['Yesterday']) == 1
        assert len(grouped['This Week']) == 1
        assert len(grouped['Older']) == 1

    def test_format_relative_time(self):
        """Test relative time formatting."""
        now = datetime.now()
        past = now - timedelta(hours=3)

        formatted = self.session_manager._format_relative_time(past.isoformat())
        assert 'h ago' in formatted

    def test_resume_dopemux_session(self):
        """Test resuming a Dopemux session."""
        session = {
            'id': 'test_session',
            'agent': 'dopemux'
        }

        success = self.session_manager.resume_session(session)

        # Should call context manager restore
        self.mock_context_manager.restore_session.assert_called_once_with('test_session')
        assert success  # Mock returns True by default

    def test_resume_claude_session(self):
        """Test resuming a Claude session."""
        session = {
            'id': 'claude_session',
            'agent': 'claude',
            'path': '/fake/path/session.json'
        }

        # Mock subprocess to avoid actual system calls
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = '/current/dir'

            success = self.session_manager.resume_session(session)

            assert success
            # Should call subprocess.run for cd and claude resume
            assert mock_subprocess.call_count >= 2

    def test_conport_integration(self):
        """Test ConPort availability and operations."""
        # Mock ConPort as unavailable
        self.session_manager.conport_available = False

        # Should return empty lists
        assert self.session_manager._retrieve_sessions_from_conport() == []

        # Should not store
        assert not self.session_manager._store_session_in_conport({'test': 'data'})