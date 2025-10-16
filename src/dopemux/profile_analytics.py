"""
Profile Usage Analytics & Metrics.

Tracks profile switches, accuracy, and usage patterns in ConPort.
Provides insights and optimization suggestions for ADHD workflows.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import aiohttp
import asyncio
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


@dataclass
class ProfileSwitch:
    """Record of a profile switch event."""
    timestamp: datetime
    from_profile: Optional[str]
    to_profile: str
    trigger: str  # 'manual', 'auto', 'suggestion_accepted'
    confidence: Optional[float] = None  # For auto-detection


@dataclass
class ProfileStats:
    """Aggregated statistics for profile usage."""
    total_switches: int
    manual_switches: int
    auto_switches: int
    suggestion_accepted: int
    suggestion_declined: int
    most_used_profile: str
    avg_switches_per_day: float
    switch_accuracy: float  # % of switches that weren't immediately reversed
    usage_by_hour: Dict[int, int]  # Hour -> switch count
    usage_by_profile: Dict[str, int]  # Profile -> switch count


class ProfileAnalytics:
    """Tracks and analyzes profile usage patterns."""

    CATEGORY = "profile_metrics"

    def __init__(self, workspace_id: str, conport_port: int = 3004):
        """
        Initialize analytics tracker.

        Args:
            workspace_id: Workspace root path
            conport_port: ConPort HTTP API port
        """
        self.workspace_id = workspace_id
        self.conport_url = f"http://localhost:{conport_port}"

    async def log_switch(
        self,
        to_profile: str,
        trigger: str,
        from_profile: Optional[str] = None,
        confidence: Optional[float] = None
    ) -> bool:
        """
        Log a profile switch to ConPort.

        Args:
            to_profile: Profile being switched to
            trigger: 'manual', 'auto', 'suggestion_accepted', 'suggestion_declined'
            from_profile: Previous profile (if known)
            confidence: Detection confidence (if auto-triggered)

        Returns:
            True if logged successfully
        """
        try:
            switch_data = {
                'timestamp': datetime.now().isoformat(),
                'to_profile': to_profile,
                'from_profile': from_profile,
                'trigger': trigger,
                'confidence': confidence
            }

            # Generate unique key with timestamp
            key = f"switch_{datetime.now().timestamp()}"

            async with aiohttp.ClientSession() as session:
                data = {
                    "workspace_id": self.workspace_id,
                    "category": self.CATEGORY,
                    "key": key,
                    "value": switch_data
                }

                async with session.post(
                    f"{self.conport_url}/api/custom_data",
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=5.0)
                ) as response:
                    return response.status == 200

        except Exception:
            return False

    async def get_stats(self, days_back: int = 30) -> ProfileStats:
        """
        Get aggregated profile usage statistics.

        Args:
            days_back: Number of days to analyze (default: 30)

        Returns:
            ProfileStats with aggregated metrics
        """
        try:
            # Get all profile metrics from ConPort
            async with aiohttp.ClientSession() as session:
                params = {
                    "workspace_id": self.workspace_id,
                    "category": self.CATEGORY
                }

                async with session.get(
                    f"{self.conport_url}/api/custom_data",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=5.0)
                ) as response:
                    if response.status != 200:
                        return self._empty_stats()

                    result = await response.json()
                    switches = []

                    if isinstance(result, list):
                        for item in result:
                            if 'value' in item:
                                switch_data = item['value']
                                # Parse timestamp
                                ts = datetime.fromisoformat(switch_data['timestamp'])

                                # Filter by date range
                                if datetime.now() - ts <= timedelta(days=days_back):
                                    switches.append(ProfileSwitch(
                                        timestamp=ts,
                                        from_profile=switch_data.get('from_profile'),
                                        to_profile=switch_data['to_profile'],
                                        trigger=switch_data['trigger'],
                                        confidence=switch_data.get('confidence')
                                    ))

                    # Analyze switches
                    return self._analyze_switches(switches, days_back)

        except Exception:
            return self._empty_stats()

    def _analyze_switches(self, switches: List[ProfileSwitch], days_back: int) -> ProfileStats:
        """Analyze switch data to compute statistics."""
        if not switches:
            return self._empty_stats()

        # Count by trigger type
        manual = sum(1 for s in switches if s.trigger == 'manual')
        auto = sum(1 for s in switches if s.trigger == 'auto')
        accepted = sum(1 for s in switches if s.trigger == 'suggestion_accepted')
        declined = sum(1 for s in switches if s.trigger == 'suggestion_declined')

        # Usage by profile
        profile_counter = Counter()
        for switch in switches:
            profile_counter[switch.to_profile] += 1

        most_used = profile_counter.most_common(1)[0][0] if profile_counter else "unknown"

        # Usage by hour
        hour_counter = Counter()
        for switch in switches:
            hour_counter[switch.timestamp.hour] += 1

        # Calculate switch accuracy (switches that lasted >30 min)
        accurate_switches = 0
        for i, switch in enumerate(switches[:-1]):
            next_switch = switches[i + 1]
            time_diff = next_switch.timestamp - switch.timestamp
            if time_diff >= timedelta(minutes=30):
                accurate_switches += 1

        accuracy = (accurate_switches / len(switches)) * 100 if switches else 0.0

        return ProfileStats(
            total_switches=len(switches),
            manual_switches=manual,
            auto_switches=auto,
            suggestion_accepted=accepted,
            suggestion_declined=declined,
            most_used_profile=most_used,
            avg_switches_per_day=len(switches) / days_back if days_back > 0 else 0,
            switch_accuracy=round(accuracy, 1),
            usage_by_hour=dict(hour_counter),
            usage_by_profile=dict(profile_counter)
        )

    def _empty_stats(self) -> ProfileStats:
        """Return empty stats when no data available."""
        return ProfileStats(
            total_switches=0,
            manual_switches=0,
            auto_switches=0,
            suggestion_accepted=0,
            suggestion_declined=0,
            most_used_profile="none",
            avg_switches_per_day=0.0,
            switch_accuracy=0.0,
            usage_by_hour={},
            usage_by_profile={}
        )


def display_stats(stats: ProfileStats, days_back: int = 30) -> None:
    """
    Display profile usage statistics with ADHD-friendly visuals.

    Args:
        stats: ProfileStats to display
        days_back: Time period analyzed
    """
    if stats.total_switches == 0:
        console.print("[yellow]📊 No usage data yet[/yellow]")
        console.print("\n[dim]Start using profiles to see analytics![/dim]")
        return

    console.print(Panel(
        f"[bold cyan]Profile Usage Analytics[/bold cyan]\n"
        f"Last {days_back} days",
        border_style="cyan"
    ))

    # Summary stats
    console.print(f"\n[bold]📈 Summary:[/bold]")
    console.print(f"   Total switches: [cyan]{stats.total_switches}[/cyan]")
    console.print(f"   Per day (avg): [cyan]{stats.avg_switches_per_day:.1f}[/cyan]")
    console.print(f"   Most used: [cyan]{stats.most_used_profile}[/cyan]")
    console.print(f"   Accuracy: [cyan]{stats.switch_accuracy:.0f}%[/cyan] (switches lasting >30 min)")

    # Switch breakdown
    console.print(f"\n[bold]🎯 Switch Types:[/bold]")
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("Manual", f"{stats.manual_switches}", f"({stats.manual_switches / stats.total_switches * 100:.0f}%)")
    table.add_row("Auto", f"{stats.auto_switches}", f"({stats.auto_switches / stats.total_switches * 100:.0f}%)")
    table.add_row("Accepted", f"{stats.suggestion_accepted}", f"({stats.suggestion_accepted / stats.total_switches * 100:.0f}%)")
    table.add_row("Declined", f"{stats.suggestion_declined}", f"({stats.suggestion_declined / stats.total_switches * 100:.0f}%)")
    console.print(table)

    # Profile usage
    if stats.usage_by_profile:
        console.print(f"\n[bold]📊 Profile Usage:[/bold]")
        profile_table = Table(show_header=True, box=None)
        profile_table.add_column("Profile", style="cyan")
        profile_table.add_column("Uses", justify="right")
        profile_table.add_column("Usage", justify="right")

        for profile, count in sorted(stats.usage_by_profile.items(), key=lambda x: x[1], reverse=True):
            pct = (count / stats.total_switches) * 100
            profile_table.add_row(profile, str(count), f"{pct:.0f}%")

        console.print(profile_table)

    # Time-of-day heatmap (ASCII)
    if stats.usage_by_hour:
        console.print(f"\n[bold]⏰ Time-of-Day Heatmap:[/bold]")
        max_switches = max(stats.usage_by_hour.values())

        for hour in range(24):
            count = stats.usage_by_hour.get(hour, 0)
            if count == 0:
                continue

            # Create ASCII bar
            bar_length = int((count / max_switches) * 20)
            bar = "█" * bar_length
            time_str = f"{hour:02d}:00"

            console.print(f"   {time_str}  {bar} {count}")


# Synchronous wrappers for CLI usage

def log_switch_sync(
    workspace_id: str,
    to_profile: str,
    trigger: str,
    from_profile: Optional[str] = None,
    confidence: Optional[float] = None,
    conport_port: int = 3004
) -> bool:
    """Synchronous wrapper for log_switch."""
    analytics = ProfileAnalytics(workspace_id, conport_port)
    return asyncio.run(analytics.log_switch(to_profile, trigger, from_profile, confidence))


def get_stats_sync(
    workspace_id: str,
    days_back: int = 30,
    conport_port: int = 3004
) -> ProfileStats:
    """Synchronous wrapper for get_stats."""
    analytics = ProfileAnalytics(workspace_id, conport_port)
    return asyncio.run(analytics.get_stats(days_back))


if __name__ == "__main__":
    # Test analytics
    print("Testing profile analytics...")

    stats = get_stats_sync("/Users/hue/code/dopemux-mvp", days_back=30)
    display_stats(stats, days_back=30)
