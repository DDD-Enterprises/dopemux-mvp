"""
Git History Usage Pattern Analyzer.

Analyzes git history to infer user workflow patterns for personalized
profile generation. ADHD-optimized with gentle guidance and clear insights.
"""

import subprocess

import logging

logger = logging.getLogger(__name__)

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rich.console import Console
from rich.table import Table

console = Console()


@dataclass
class GitAnalysis:
    """Results from git history analysis."""

    # Branch patterns
    common_branch_prefixes: List[Tuple[str, int]]  # (prefix, count)
    total_branches: int

    # Directory patterns
    common_directories: List[Tuple[str, int]]  # (directory, commit_count)
    total_files_changed: int

    # Temporal patterns
    common_work_hours: List[int]  # Hours of day (0-23)
    peak_work_time: Optional[str]  # "morning", "afternoon", "evening", "night"

    # Commit patterns
    total_commits: int
    avg_commits_per_day: float

    # Energy inferences
    suggested_energy_level: str  # "low", "medium", "high"
    suggested_session_duration: int  # minutes

    # MCP suggestions based on directory patterns
    suggested_mcps: List[str]


class GitHistoryAnalyzer:
    """Analyzes git history to infer workflow patterns."""

    def __init__(self, repo_path: Optional[Path] = None):
        """
        Initialize analyzer.

        Args:
            repo_path: Path to git repository (default: current directory)
        """
        self.repo_path = repo_path or Path.cwd()

    def analyze(self, days_back: int = 90, max_commits: int = 500) -> GitAnalysis:
        """
        Analyze git history for workflow patterns.

        Args:
            days_back: How many days of history to analyze (default: 90)
            max_commits: Maximum commits to analyze (default: 500, ADHD limit)

        Returns:
            GitAnalysis with inferred patterns

        ADHD Optimization: Limits to 500 commits to prevent analysis paralysis
        """
        # Get commits from last N days
        commits = self._get_recent_commits(days_back, max_commits)

        if not commits:
            return self._empty_analysis()

        # Analyze branch patterns
        branch_prefixes = self._analyze_branch_patterns(commits)

        # Analyze directory patterns
        dir_patterns = self._analyze_directory_patterns(commits)

        # Analyze temporal patterns
        work_hours, peak_time = self._analyze_temporal_patterns(commits)

        # Infer energy and session preferences
        energy_level, session_duration = self._infer_energy_patterns(commits, work_hours)

        # Suggest MCPs based on directory patterns
        suggested_mcps = self._suggest_mcps_from_patterns(dir_patterns)

        avg_commits = len(commits) / days_back if days_back > 0 else 0

        return GitAnalysis(
            common_branch_prefixes=branch_prefixes[:5],  # Top 5
            total_branches=len(set(c['branch'] for c in commits if c['branch'])),
            common_directories=dir_patterns[:10],  # Top 10
            total_files_changed=sum(c['files_changed'] for c in commits),
            common_work_hours=work_hours,
            peak_work_time=peak_time,
            total_commits=len(commits),
            avg_commits_per_day=round(avg_commits, 2),
            suggested_energy_level=energy_level,
            suggested_session_duration=session_duration,
            suggested_mcps=suggested_mcps
        )

    def _get_recent_commits(self, days_back: int, max_commits: int) -> List[Dict]:
        """Get recent commits with metadata."""
        try:
            # Get commit log with details
            result = subprocess.run(
                [
                    "git", "log",
                    f"--since={days_back} days ago",
                    f"-{max_commits}",
                    "--pretty=format:%H|%ai|%s",
                    "--name-only"
                ],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return []

            commits = []
            current_commit = None

            for line in result.stdout.split('\n'):
                if '|' in line:
                    # Commit header: hash|date|subject
                    parts = line.split('|')
                    if len(parts) >= 3:
                        commit_hash = parts[0]
                        commit_date = parts[1]
                        subject = parts[2]

                        # Parse datetime (format: "2025-10-16 05:26:01 -0700")
                        try:
                            # Split date and timezone
                            date_part = commit_date.rsplit(' ', 1)[0]  # "2025-10-16 05:26:01"
                            dt = datetime.strptime(date_part, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            # Fallback to current time if parsing fails
                            dt = datetime.now()

                        # Infer branch from subject (rough heuristic)
                        branch = self._infer_branch_from_subject(subject)

                        current_commit = {
                            'hash': commit_hash,
                            'date': dt,
                            'subject': subject,
                            'branch': branch,
                            'hour': dt.hour,
                            'files': []
                        }
                        commits.append(current_commit)
                elif line.strip() and current_commit:
                    # File path
                    current_commit['files'].append(line.strip())

            # Add files_changed count
            for commit in commits:
                commit['files_changed'] = len(commit['files'])

            return commits

        except Exception as e:
            return []

            logger.error(f"Error: {e}")
    def _infer_branch_from_subject(self, subject: str) -> Optional[str]:
        """Infer branch type from commit subject."""
        subject_lower = subject.lower()

        if any(word in subject_lower for word in ['feat', 'feature']):
            return 'feature'
        elif any(word in subject_lower for word in ['fix', 'bug']):
            return 'fix'
        elif any(word in subject_lower for word in ['doc', 'docs']):
            return 'docs'
        elif any(word in subject_lower for word in ['test']):
            return 'test'
        elif any(word in subject_lower for word in ['refactor']):
            return 'refactor'

        return None

    def _analyze_branch_patterns(self, commits: List[Dict]) -> List[Tuple[str, int]]:
        """Analyze branch naming patterns."""
        branch_types = Counter()

        for commit in commits:
            if commit['branch']:
                branch_types[commit['branch']] += 1

        return branch_types.most_common()

    def _analyze_directory_patterns(self, commits: List[Dict]) -> List[Tuple[str, int]]:
        """Analyze which directories are modified most."""
        dir_counter = Counter()

        for commit in commits:
            for file_path in commit['files']:
                # Get top-level directory
                parts = Path(file_path).parts
                if parts:
                    top_dir = parts[0]
                    dir_counter[top_dir] += 1

        return dir_counter.most_common()

    def _analyze_temporal_patterns(self, commits: List[Dict]) -> Tuple[List[int], Optional[str]]:
        """Analyze when user typically works."""
        hour_counter = Counter()

        for commit in commits:
            hour_counter[commit['hour']] += 1

        # Get most common hours
        common_hours = [hour for hour, _ in hour_counter.most_common(6)]

        # Determine peak time
        if not common_hours:
            return [], None

        avg_hour = sum(common_hours) / len(common_hours)

        if 5 <= avg_hour < 12:
            peak = "morning"
        elif 12 <= avg_hour < 17:
            peak = "afternoon"
        elif 17 <= avg_hour < 21:
            peak = "evening"
        else:
            peak = "night"

        return sorted(common_hours), peak

    def _infer_energy_patterns(
        self,
        commits: List[Dict],
        work_hours: List[int]
    ) -> Tuple[str, int]:
        """Infer energy level and session duration from commit patterns."""
        if not commits:
            return "medium", 25

        # Calculate commits per session (rough proxy for intensity)
        avg_files_per_commit = sum(c['files_changed'] for c in commits) / len(commits)

        # Energy level based on commit intensity
        if avg_files_per_commit < 2:
            energy = "low"
            session = 20
        elif avg_files_per_commit < 5:
            energy = "medium"
            session = 25
        else:
            energy = "high"
            session = 30

        return energy, session

    def _suggest_mcps_from_patterns(self, dir_patterns: List[Tuple[str, int]]) -> List[str]:
        """Suggest MCP servers based on directory patterns."""
        mcps = set()

        # Always include core MCPs
        mcps.add("serena-v2")
        mcps.add("conport")

        for directory, _count in dir_patterns[:5]:  # Top 5 directories
            dir_lower = directory.lower()

            # Code-heavy work
            if any(word in dir_lower for word in ['src', 'lib', 'app', 'components']):
                mcps.add("dope-context")
                mcps.add("pal")

            # Documentation work
            if any(word in dir_lower for word in ['docs', 'documentation']):
                mcps.add("pal")

            # Testing work
            if any(word in dir_lower for word in ['test', 'tests', '__tests__']):
                mcps.add("dope-context")

            # Research/analysis
            if any(word in dir_lower for word in ['research', 'analysis', 'experiments']):
                mcps.add("zen")
                mcps.add("gpt-researcher")

        return sorted(list(mcps))

    def _empty_analysis(self) -> GitAnalysis:
        """Return empty analysis when no commits found."""
        return GitAnalysis(
            common_branch_prefixes=[],
            total_branches=0,
            common_directories=[],
            total_files_changed=0,
            common_work_hours=[],
            peak_work_time=None,
            total_commits=0,
            avg_commits_per_day=0.0,
            suggested_energy_level="medium",
            suggested_session_duration=25,
            suggested_mcps=["serena-v2", "conport", "dope-context"]
        )

    def display_analysis(self, analysis: GitAnalysis) -> None:
        """
        Display analysis results in ADHD-friendly format.

        Args:
            analysis: GitAnalysis results to display
        """
        if analysis.total_commits == 0:
            console.logger.info("[yellow]⚠️  No git history found - using defaults[/yellow]")
            return

        console.logger.info("\n[bold cyan]📊 Your Development Pattern Analysis[/bold cyan]\n")

        # Commit activity
        console.logger.info(f"[green]📈 Activity:[/green] {analysis.total_commits} commits ({analysis.avg_commits_per_day} per day avg)")

        # Branch patterns
        if analysis.common_branch_prefixes:
            console.logger.info(f"\n[green]🌿 Branch Patterns:[/green]")
            for prefix, count in analysis.common_branch_prefixes[:3]:
                console.logger.info(f"   • {prefix}: {count} commits")

        # Directory patterns
        if analysis.common_directories:
            console.logger.info(f"\n[green]📁 Common Directories:[/green]")
            table = Table(show_header=False, box=None, padding=(0, 2))
            for directory, count in analysis.common_directories[:5]:
                table.add_row(f"• {directory}", f"{count} changes")
            console.logger.info(table)

        # Temporal patterns
        if analysis.common_work_hours:
            hours_str = ", ".join(f"{h:02d}:00" for h in analysis.common_work_hours[:4])
            console.logger.info(f"\n[green]⏰ Peak Work Hours:[/green] {hours_str}")
            if analysis.peak_work_time:
                console.logger.info(f"   → Typically works in the [cyan]{analysis.peak_work_time}[/cyan]")

        # Energy/Session inference
        console.logger.info(f"\n[green]⚡ Suggested Settings:[/green]")
        console.logger.info(f"   • Energy Level: [cyan]{analysis.suggested_energy_level}[/cyan]")
        console.logger.info(f"   • Session Duration: [cyan]{analysis.suggested_session_duration} minutes[/cyan]")

        # MCP suggestions
        console.logger.info(f"\n[green]🔧 Recommended MCP Servers:[/green]")
        for mcp in analysis.suggested_mcps:
            console.logger.info(f"   • {mcp}")
