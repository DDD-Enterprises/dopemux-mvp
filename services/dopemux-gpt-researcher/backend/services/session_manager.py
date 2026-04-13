"""
Session Manager for GPT-Researcher
Provides persistence and recovery for research sessions with ADHD support
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import uuid4

import aiofiles


class SessionManager:
    """
    Manages research sessions with persistence for ADHD-friendly interruption recovery

    Features:
    - Auto-save every 30 seconds
    - Session restoration after interruptions
    - Context reminders for task switching
    - Break history tracking
    - Attention state monitoring
    """

    def __init__(self, storage_path: str = None):
        """Initialize session manager with storage location"""
        self.storage_path = Path(storage_path or os.getenv(
            'SESSION_STORAGE_PATH',
            '/Users/hue/code/dopemux-mvp/.sessions'
        ))
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.auto_save_task = None
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initialize session manager and restore active sessions"""
        # Create storage directory if it doesn't exist
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Restore active sessions from disk
        await self._restore_active_sessions()

        # Start auto-save task
        self.auto_save_task = asyncio.create_task(self._auto_save_loop())

        print(f"✅ Session manager initialized with {len(self.sessions)} active sessions")

    async def get_or_create_session(self, session_id: str = None) -> Dict[str, Any]:
        """Get existing session or create new one"""
        async with self._lock:
            if not session_id:
                session_id = str(uuid4())

            if session_id not in self.sessions:
                self.sessions[session_id] = {
                    'session_id': session_id,
                    'created_at': datetime.utcnow().isoformat(),
                    'last_activity': datetime.utcnow().isoformat(),
                    'task_ids': [],
                    'completed_tasks': [],
                    'attention_state': 'fresh',
                    'break_history': [],
                    'total_focus_minutes': 0,
                    'interruptions': 0,
                    'context_switches': 0,
                    'preferences': {
                        'break_interval': 25,
                        'notification_style': 'gentle',
                        'hyperfocus_protection': True
                    }
                }

                # Save new session
                await self._save_session(session_id)

            else:
                # Update last activity
                self.sessions[session_id]['last_activity'] = datetime.utcnow().isoformat()

            return self.sessions[session_id]

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        async with self._lock:
            return self.sessions.get(session_id)

    async def save_task_results(self, session_id: str, task_id: str, results: Dict[str, Any]):
        """Save task results to session"""
        async with self._lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]

                # Add task to history
                if task_id not in session['task_ids']:
                    session['task_ids'].append(task_id)

                # Mark as completed
                session['completed_tasks'].append({
                    'task_id': task_id,
                    'completed_at': datetime.utcnow().isoformat(),
                    'summary': results.get('summary', ''),
                    'key_findings': results.get('key_findings', [])
                })

                # Update focus time
                session['total_focus_minutes'] += results.get('execution_time_minutes', 0)

                # Save session
                await self._save_session(session_id)

    async def pause_session(self, session_id: str):
        """Pause session for break or interruption"""
        async with self._lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]

                # Record pause
                session['last_pause'] = datetime.utcnow().isoformat()
                session['attention_state'] = 'paused'
                session['interruptions'] += 1

                # Calculate focus duration
                if 'last_resume' in session:
                    last_resume = datetime.fromisoformat(session['last_resume'])
                    focus_duration = (datetime.utcnow() - last_resume).total_seconds() / 60
                    session['total_focus_minutes'] += focus_duration

                # Add to break history
                session['break_history'].append({
                    'type': 'pause',
                    'timestamp': datetime.utcnow().isoformat(),
                    'reason': 'user_initiated'
                })

                await self._save_session(session_id)

    async def resume_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Resume paused session"""
        async with self._lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]

                # Record resume
                session['last_resume'] = datetime.utcnow().isoformat()
                session['attention_state'] = 'resuming'
                session['context_switches'] += 1

                # Add to break history
                if 'last_pause' in session:
                    pause_time = datetime.fromisoformat(session['last_pause'])
                    break_duration = (datetime.utcnow() - pause_time).total_seconds() / 60

                    session['break_history'].append({
                        'type': 'resume',
                        'timestamp': datetime.utcnow().isoformat(),
                        'break_duration_minutes': break_duration
                    })

                await self._save_session(session_id)
                return session

            return None

    async def get_context_reminder(self, session_id: str) -> str:
        """Get context reminder for session resumption"""
        session = await self.get_session(session_id)

        if not session:
            return "No previous context found. Starting fresh!"

        # Build context reminder
        reminder_parts = []

        # Last activity time
        last_activity = datetime.fromisoformat(session['last_activity'])
        time_away = (datetime.utcnow() - last_activity).total_seconds() / 60

        if time_away < 5:
            reminder_parts.append("You just stepped away briefly.")
        elif time_away < 30:
            reminder_parts.append(f"You were away for {int(time_away)} minutes.")
        else:
            reminder_parts.append(f"Welcome back! You were away for {int(time_away)} minutes.")

        # Recent tasks
        if session['completed_tasks']:
            last_task = session['completed_tasks'][-1]
            reminder_parts.append(f"Last completed: {last_task['summary'][:100]}")

        # Current focus time
        reminder_parts.append(f"Total focus time today: {session['total_focus_minutes']} minutes")

        # Break recommendation
        if session['total_focus_minutes'] > 0 and session['total_focus_minutes'] % 25 == 0:
            reminder_parts.append("💡 Consider taking a 5-minute break soon!")

        return " ".join(reminder_parts)

    async def save_all_sessions(self):
        """Save all active sessions to disk"""
        async with self._lock:
            for session_id in self.sessions:
                await self._save_session(session_id)

    async def _save_session(self, session_id: str):
        """Save individual session to disk"""
        if session_id not in self.sessions:
            return

        session_file = self.storage_path / f"{session_id}.json"

        try:
            async with aiofiles.open(session_file, 'w') as f:
                await f.write(json.dumps(self.sessions[session_id], indent=2))
        except Exception as e:
            print(f"⚠️ Failed to save session {session_id}: {e}")

    async def _restore_active_sessions(self):
        """Restore active sessions from disk"""
        session_files = list(self.storage_path.glob("*.json"))

        for session_file in session_files:
            try:
                async with aiofiles.open(session_file, 'r') as f:
                    content = await f.read()
                    session = json.loads(content)

                    # Only restore recent sessions (last 24 hours)
                    last_activity = datetime.fromisoformat(session['last_activity'])
                    if (datetime.utcnow() - last_activity) < timedelta(days=1):
                        session_id = session['session_id']
                        self.sessions[session_id] = session
                        print(f"📂 Restored session: {session_id}")

            except Exception as e:
                print(f"⚠️ Failed to restore session from {session_file}: {e}")

    async def _auto_save_loop(self):
        """Auto-save sessions periodically"""
        while True:
            try:
                await asyncio.sleep(30)  # Save every 30 seconds
                await self.save_all_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️ Auto-save error: {e}")

    async def cleanup_old_sessions(self, days: int = 7):
        """Clean up sessions older than specified days"""
        async with self._lock:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            sessions_to_remove = []

            for session_id, session in self.sessions.items():
                last_activity = datetime.fromisoformat(session['last_activity'])
                if last_activity < cutoff_date:
                    sessions_to_remove.append(session_id)

            for session_id in sessions_to_remove:
                del self.sessions[session_id]

                # Remove file
                session_file = self.storage_path / f"{session_id}.json"
                if session_file.exists():
                    session_file.unlink()

            if sessions_to_remove:
                print(f"🧹 Cleaned up {len(sessions_to_remove)} old sessions")

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session"""
        session = self.sessions.get(session_id)

        if not session:
            return {}

        return {
            'session_id': session_id,
            'total_tasks': len(session['task_ids']),
            'completed_tasks': len(session['completed_tasks']),
            'total_focus_minutes': session['total_focus_minutes'],
            'interruptions': session['interruptions'],
            'context_switches': session['context_switches'],
            'break_count': len([b for b in session['break_history'] if b['type'] == 'pause']),
            'average_focus_period': (
                session['total_focus_minutes'] / max(1, session['context_switches'])
                if session['context_switches'] > 0 else 0
            ),
            'productivity_score': self._calculate_productivity_score(session)
        }

    def _calculate_productivity_score(self, session: Dict[str, Any]) -> int:
        """Calculate ADHD-friendly productivity score"""
        score = 0

        # Points for completed tasks
        score += len(session['completed_tasks']) * 10

        # Points for maintaining focus
        if session['total_focus_minutes'] > 0:
            score += min(50, session['total_focus_minutes'] // 5)

        # Points for taking breaks (ADHD-friendly!)
        break_count = len([b for b in session['break_history'] if b['type'] == 'pause'])
        ideal_breaks = session['total_focus_minutes'] // 25
        if break_count >= ideal_breaks:
            score += 20  # Reward for taking breaks!

        # Penalty for too many interruptions
        if session['interruptions'] > 5:
            score -= (session['interruptions'] - 5) * 2

        return max(0, min(100, score))  # Cap between 0-100