#!/usr/bin/env python3
"""
Real-time MetaMCP Status Updater for Tmux

Provides live status updates that integrate with the actual MetaMCP system
and the tmux interface controller.
"""

import json
import subprocess
import time
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class RealtimeStatusUpdater:
    """Real-time status updater with MetaMCP integration."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.controller_path = Path(__file__).parent / "tmux_metamcp_controller.py"
        self.cache_duration = 3  # seconds
        self.last_cache = None
        self.cache_timestamp = None

    def get_live_metamcp_status(self) -> Optional[Dict]:
        """Get status from live MetaMCP system."""
        try:
            # First try to get status from the actual MetaMCP system
            result = subprocess.run([
                'python', str(self.controller_path), 'status'
            ], capture_output=True, text=True, timeout=2)

            if result.returncode == 0:
                # Parse the human-readable output back to structured data
                lines = result.stdout.strip().split('\n')
                status = {'live_system': True}

                for line in lines:
                    if 'Current role:' in line:
                        status['role'] = line.split(':')[1].strip()
                    elif 'Token usage:' in line:
                        usage_part = line.split(':')[1].strip()
                        usage, budget = usage_part.split('/')
                        status['token_usage'] = int(usage.replace(',', ''))
                        status['token_budget'] = int(budget.replace(',', ''))
                    elif 'Session time:' in line:
                        time_part = line.split(':')[1].strip()
                        status['session_duration'] = int(time_part.split()[0])
                    elif 'Tools:' in line:
                        tools_part = line.split(':')[1].strip()
                        status['tools_count'] = int(tools_part.split()[0])

                # Fill in defaults for missing fields
                status.setdefault('health', 'healthy')
                status.setdefault('adhd_features', True)

                return status

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError):
            pass

        return None

    def get_cached_status(self) -> Dict:
        """Get status with caching to prevent overwhelming the system."""
        now = datetime.now()

        # Use cache if available and fresh
        if (self.last_cache and self.cache_timestamp and
            (now - self.cache_timestamp).total_seconds() < self.cache_duration):
            return self.last_cache

        # Try to get live status
        live_status = self.get_live_metamcp_status()

        if live_status:
            self.last_cache = live_status
            self.cache_timestamp = now
            return live_status

        # Fallback to simulated status
        return self._get_fallback_status()

    def _get_fallback_status(self) -> Dict:
        """Fallback status when live system unavailable."""
        return {
            'role': 'researcher',
            'tools_count': 4,
            'token_usage': 300,
            'token_budget': 10000,
            'session_duration': 0,
            'health': 'unknown',
            'adhd_features': True,
            'live_system': False
        }

    def format_role_indicator(self, role: str, live_system: bool = False) -> str:
        """Format role with live system indicator."""
        role_colors = {
            'developer': '#4A90E2',
            'researcher': '#7ED321',
            'planner': '#F5A623',
            'reviewer': '#D0021B',
            'ops': '#9013FE',
            'architect': '#50E3C2',
            'debugger': '#BD10E0'
        }

        role_icons = {
            'developer': '🧑‍💻',
            'researcher': '🔬',
            'planner': '📋',
            'reviewer': '👀',
            'ops': '⚙️',
            'architect': '🏗️',
            'debugger': '🐛'
        }

        icon = role_icons.get(role, '❓')
        color = role_colors.get(role, '#9B9B9B')

        # Add live system indicator
        live_indicator = '●' if live_system else '○'

        return f"#[fg={color},bold]{icon} {role.upper()}{live_indicator}#[default]"

    def format_token_usage(self, usage: int, budget: int) -> str:
        """Format token usage with progress visualization."""
        if budget == 0:
            percentage = 0
        else:
            percentage = usage / budget

        # Choose color and emoji based on usage
        if percentage < 0.6:
            color = '#7ED321'  # Green
            emoji = '💚'
        elif percentage < 0.8:
            color = '#F5A623'  # Yellow
            emoji = '💛'
        elif percentage < 0.9:
            color = '#FF9500'  # Orange
            emoji = '🧡'
        else:
            color = '#D0021B'  # Red
            emoji = '❤️'

        # Create 5-segment progress bar
        filled = int(percentage * 5)
        bar = '█' * filled + '░' * (5 - filled)

        return f"#[fg={color}]{emoji} {usage/1000:.1f}k/{budget/1000:.0f}k #[fg=white]{bar}#[default]"

    def format_session_duration(self, duration_minutes: int) -> str:
        """Format session duration with ADHD break guidance."""
        if duration_minutes < 25:
            color = '#7ED321'  # Green
            icon = '🟢'
        elif duration_minutes < 50:
            color = '#F5A623'  # Yellow
            icon = '🟡'
        else:
            color = '#D0021B'  # Red
            icon = '🔴'

        hours = duration_minutes // 60
        mins = duration_minutes % 60

        if hours > 0:
            time_str = f"{hours}h{mins:02d}m"
        else:
            time_str = f"{mins}m"

        return f"#[fg={color}]{icon} {time_str}#[default]"

    def format_health_status(self, health: str, tools_count: int) -> str:
        """Format health status with tool count."""
        if health == 'healthy':
            color = '#7ED321'
            icon = '✅'
        elif health == 'warning':
            color = '#F5A623'
            icon = '⚠️'
        elif health == 'error':
            color = '#D0021B'
            icon = '❌'
        else:
            color = '#9B9B9B'
            icon = '❓'

        return f"#[fg={color}]{icon} {tools_count} tools#[default]"

    def format_adhd_status(self, adhd_features: bool) -> str:
        """Format ADHD accommodations status."""
        if adhd_features:
            return "#[fg=#7ED321]🧠 ADHD✓#[default]"
        else:
            return "#[fg=#9B9B9B]🧠 OFF#[default]"

    def generate_realtime_status_bar(self) -> str:
        """Generate the complete real-time status bar."""
        status = self.get_cached_status()

        # Extract status information
        role = status.get('role', 'unknown')
        tools_count = status.get('tools_count', 0)
        token_usage = status.get('token_usage', 0)
        token_budget = status.get('token_budget', 10000)
        session_duration = status.get('session_duration', 0)
        health = status.get('health', 'unknown')
        adhd_features = status.get('adhd_features', True)
        live_system = status.get('live_system', False)

        # Build status components
        components = [
            self.format_role_indicator(role, live_system),
            self.format_token_usage(token_usage, token_budget),
            self.format_session_duration(session_duration),
            self.format_health_status(health, tools_count),
            self.format_adhd_status(adhd_features),
            f"#[fg=#9B9B9B]{datetime.now().strftime('%H:%M')}#[default]"
        ]

        # Join with separators
        separator = " #[fg=#9B9B9B]|#[default] "
        return separator.join(components)

    def run_continuous_update(self, interval: int = 5):
        """Run continuous status updates for tmux."""
        while True:
            try:
                status_bar = self.generate_realtime_status_bar()
                print(status_bar, flush=True)
                time.sleep(interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                error_bar = f"#[fg=#D0021B]MetaMCP Error: {str(e)}#[default]"
                print(error_bar, flush=True)
                time.sleep(interval)


def main():
    """Main entry point."""
    updater = RealtimeStatusUpdater()

    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        updater.run_continuous_update()
    else:
        # Single status output
        print(updater.generate_realtime_status_bar())


if __name__ == '__main__':
    main()