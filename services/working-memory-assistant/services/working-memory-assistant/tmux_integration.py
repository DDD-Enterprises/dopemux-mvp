"""
Tmux Integration for Working Memory Assistant

This module handles tmux session state capture and restoration, enabling seamless terminal context recovery.
"""

import subprocess

import logging

logger = logging.getLogger(__name__)

import json
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

class TmuxSession:
    """Represents a tmux session state for capture and restoration"""

    def __init__(self, session_name: str = None):
        self.session_name = session_name or f"wma-session-{int(datetime.now().timestamp())}"
        self.windows = []
        self.panes = []
        self.active_window = None
        self.active_pane = None
        self.layout = None

def capture_tmux_state() -> Dict[str, Any]:
    """Capture current tmux session state"""
    try:
        # Get current session
        session_info = subprocess.run(['tmux', 'display-message', '-p', '#S'],
                                     capture_output=True, text=True, check=True)
        session_name = session_info.stdout.strip()

        # Get session windows
        windows_output = subprocess.run(['tmux', 'list-windows', '-t', session_name, '-F', '#{window_index} #{window_name} #{window_active}'],
                                        capture_output=True, text=True, check=True)

        windows = []
        for line in windows_output.stdout.strip().split('\n'):
            if line:
                parts = line.split(' ', 2)
                if len(parts) == 3:
                    index, name, active = parts
                    windows.append({
                        'index': index,
                        'name': name,
                        'active': active == '1'
                    })

        # Get detailed pane information for active window
        active_window = None
        panes = []
        if windows:
            active_window_index = next((w['index'] for w in windows if w['active']), '0')
            panes_output = subprocess.run(['tmux', 'list-panes', '-t', f"{session_name}:{active_window_index}", '-F', '#{pane_index} #{pane_title} #{pane_active} #{pane_current_path}'],
                                         capture_output=True, text=True, check=True)

            for line in panes_output.stdout.strip().split('\n'):
                if line:
                    parts = line.split(' ', 3)
                    if len(parts) == 4:
                        index, title, active, path = parts
                        panes.append({
                            'index': index,
                            'title': title,
                            'active': active == '1',
                            'path': path
                        })

        # Get current layout
        layout_output = subprocess.run(['tmux', 'display-message', '-p', '#{window_layout}'],
                                       capture_output=True, text=True, check=True)
        layout = layout_output.stdout.strip()

        return {
            'session_name': session_name,
            'windows': windows,
            'active_window': active_window_index if windows else None,
            'panes': panes,
            'active_pane': next((p['index'] for p in panes if p['active']), None),
            'layout': layout,
            'captured_at': datetime.now().isoformat()
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"Tmux capture failed: {e}")
        return None

def restore_tmux_state(state: Dict[str, Any]) -> bool:
    """Restore tmux session state"""
    try:
        session_name = state['session_name']

        # Create or attach to session
        subprocess.run(['tmux', 'new-session', '-d', '-s', session_name], check=True)

        # Set window layout
        if state.get('layout'):
            subprocess.run(['tmux', 'select-layout', '-t', session_name, state['layout']], check=True)

        # Restore panes and paths
        if state.get('panes'):
            for pane in state['panes']:
                pane_index = pane['index']
                path = pane['path']

                # Switch to pane and set path
                subprocess.run(['tmux', 'select-pane', '-t', f"{session_name}:{pane_index}"], check=True)
                subprocess.run(['tmux', 'send-keys', f'cd "{path}"', 'Enter'], check=True)

        # Switch to active pane
        if state.get('active_pane'):
            subprocess.run(['tmux', 'select-pane', '-t', state['active_pane']], check=True)

        # Attach to session
        subprocess.run(['tmux', 'attach-session', '-t', session_name], check=True)

        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Tmux restore failed: {e}")
        return False

def get_tmux_sessions() -> List[str]:
    """Get list of available tmux sessions"""
    try:
        result = subprocess.run(['tmux', 'list-sessions'],
                                capture_output=True, text=True, check=True)
        return [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
    except subprocess.CalledProcessError:
        return []

def create_new_tmux_session(name: str, path: str = None) -> bool:
    """Create a new tmux session for WMA"""
    try:
        cmd = ['tmux', 'new-session', '-d', '-s', name]
        if path:
            cmd.extend(['-c', path])
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create tmux session: {e}")
        return False

if __name__ == "__main__":
    # Test tmux integration
    logger.info("Testing Tmux Integration...")

    # Capture current state
    state = capture_tmux_state()
    if state:
        logger.info(f"Captured tmux state for session: {state['session_name']}")
        logger.info(f"Active window: {state['active_window']}")
        logger.info(f"Active pane: {state['active_pane']}")
        logger.info(f"Number of panes: {len(state['panes'])}")

        # Save to JSON for snapshot
        with open('tmux_state.json', 'w') as f:
            json.dump(state, f, indent=2)
        logger.info("Tmux state saved to tmux_state.json")
    else:
        logger.error("No tmux session found or capture failed")
