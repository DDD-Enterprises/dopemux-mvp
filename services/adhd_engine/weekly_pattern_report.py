"""
Weekly Pattern Report Generator

Friday afternoon wrap-up providing:
- Best focus time windows analysis
- Total hyperfocus hours with patterns
- Break acceptance rate and timing
- Energy patterns throughout week
- Trend analysis (improving/declining)
- Recommendations for next week

ADHD Benefit: Self-awareness, pattern recognition, data-driven improvements
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TrendDirection(Enum):
    """Trend direction."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class FocusWindow:
    """Time window with focus metrics."""
    start_hour: int
    end_hour: int
    total_focus_minutes: int
    average_attention_score: float
    sessions_count: int
    
    def __str__(self) -> str:
        return f"{self.start_hour:02d}:00-{self.end_hour:02d}:00 ({self.total_focus_minutes}min, {self.average_attention_score:.1f} avg attention)"


@dataclass
class WeeklyReport:
    """Weekly pattern report."""
    user_id: str
    week_start: datetime
    week_end: datetime
    
    # Focus patterns
    best_focus_windows: List[FocusWindow] = field(default_factory=list)
    worst_focus_windows: List[FocusWindow] = field(default_factory=list)
    total_focus_minutes: int = 0
    total_hyperfocus_hours: float = 0.0
    
    # Break patterns
    total_breaks_suggested: int = 0
    total_breaks_accepted: int = 0
    break_acceptance_rate: float = 0.0
    best_break_times: List[str] = field(default_factory=list)
    
    # Energy patterns
    high_energy_hours: List[int] = field(default_factory=list)
    low_energy_hours: List[int] = field(default_factory=list)
    average_daily_energy: Dict[str, float] = field(default_factory=dict)
    
    # Trends
    focus_trend: TrendDirection = TrendDirection.INSUFFICIENT_DATA
    energy_trend: TrendDirection = TrendDirection.INSUFFICIENT_DATA
    break_trend: TrendDirection = TrendDirection.INSUFFICIENT_DATA
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for storage."""
        return {
            "user_id": self.user_id,
            "week_start": self.week_start.isoformat(),
            "week_end": self.week_end.isoformat(),
            "best_focus_windows": [str(w) for w in self.best_focus_windows],
            "total_focus_minutes": self.total_focus_minutes,
            "total_hyperfocus_hours": self.total_hyperfocus_hours,
            "break_acceptance_rate": self.break_acceptance_rate,
            "high_energy_hours": self.high_energy_hours,
            "recommendations": self.recommendations,
            "trends": {
                "focus": self.focus_trend.value,
                "energy": self.energy_trend.value,
                "breaks": self.break_trend.value
            }
        }


class WeeklyPatternReporter:
    """
    Generate weekly pattern reports.
    
    Analyzes:
    - Focus time windows and patterns
    - Hyperfocus session frequency and duration
    - Break acceptance and timing
    - Energy patterns by day and hour
    - Week-over-week trends
    """
    
    def __init__(self, redis_client=None, conport_client=None):
        """
        Initialize weekly reporter.
        
        Args:
            redis_client: Redis client for fetching activity data
            conport_client: ConPort client for historical decisions
        """
        self.redis = redis_client
        self.conport = conport_client
        
        # Report history
        self.report_history: List[WeeklyReport] = []
    
    async def generate_weekly_report(
        self,
        user_id: str,
        week_data: Optional[Dict[str, Any]] = None,
        force_friday: bool = False
    ) -> Dict[str, Any]:
        """
        Generate weekly pattern report.
        
        Args:
            user_id: User identifier
            week_data: Optional pre-collected week data (for testing)
            force_friday: Generate report even if not Friday
        
        Returns:
            Comprehensive weekly report
        """
        today = datetime.now()
        
        # Check if Friday
        if not force_friday and today.weekday() != 4:  # 4 = Friday
            return {
                "report_ready": False,
                "reason": f"Today is {today.strftime('%A')}, not Friday",
                "suggestion": "Weekly reports are generated on Fridays. Use force_friday=True to generate anyway."
            }
        
        logger.info(f"📊 Generating weekly report for {user_id}")
        
        # Determine week boundaries (Monday-Friday)
        week_start = today - timedelta(days=today.weekday())  # Monday
        week_end = week_start + timedelta(days=4)  # Friday
        
        # Collect week data (or use provided)
        if week_data is None:
            week_data = await self._collect_week_data(user_id, week_start, week_end)
        
        # Generate report
        report = WeeklyReport(
            user_id=user_id,
            week_start=week_start,
            week_end=week_end
        )
        
        # Analyze focus patterns
        report.best_focus_windows = self._analyze_focus_windows(week_data)
        report.total_focus_minutes = week_data.get('total_focus_minutes', 0)
        report.total_hyperfocus_hours = week_data.get('total_hyperfocus_minutes', 0) / 60
        
        # Analyze break patterns
        breaks_suggested = week_data.get('breaks_suggested', 0)
        breaks_accepted = week_data.get('breaks_accepted', 0)
        report.total_breaks_suggested = breaks_suggested
        report.total_breaks_accepted = breaks_accepted
        report.break_acceptance_rate = (
            breaks_accepted / breaks_suggested if breaks_suggested > 0 else 0
        )
        report.best_break_times = self._find_best_break_times(week_data)
        
        # Analyze energy patterns
        report.high_energy_hours = self._find_high_energy_hours(week_data)
        report.low_energy_hours = self._find_low_energy_hours(week_data)
        report.average_daily_energy = self._calculate_daily_energy(week_data)
        
        # Analyze trends
        if self.report_history:
            report.focus_trend = self._calculate_trend(
                'focus_minutes',
                report.total_focus_minutes
            )
            report.energy_trend = self._calculate_trend(
                'average_energy',
                self._get_week_average_energy(week_data)
            )
            report.break_trend = self._calculate_trend(
                'break_rate',
                report.break_acceptance_rate
            )
        
        # Generate recommendations
        report.recommendations = self._generate_recommendations(report, week_data)
        
        # Store report
        self.report_history.append(report)
        
        # Save to ConPort
        if self.conport:
            try:
                await self._save_report_to_conport(report)
            except Exception as e:
                logger.error(f"Failed to save report to ConPort: {e}")
        
        return {
            "report_ready": True,
            "report": self._format_report(report),
            "visualizations": self._generate_visualizations(report, week_data),
            "action_items": self._extract_action_items(report)
        }
    
    async def _collect_week_data(
        self,
        user_id: str,
        week_start: datetime,
        week_end: datetime
    ) -> Dict[str, Any]:
        """Collect data for the week."""
        # In real implementation, would query from Redis and other services
        # For now, return mock structure
        
        # Mock data structure
        data = {
            "hourly_focus": defaultdict(int),  # hour -> focus minutes
            "hourly_attention": defaultdict(list),  # hour -> attention scores
            "hourly_energy": defaultdict(list),  # hour -> energy levels
            "daily_energy": defaultdict(list),  # day -> energy levels
            "total_focus_minutes": 0,
            "total_hyperfocus_minutes": 0,
            "breaks_suggested": 0,
            "breaks_accepted": 0,
            "break_times": [],  # list of (hour, accepted bool)
            "sessions": []  # list of session dicts
        }
        
        # Would populate from actual data sources
        # data = await self._query_redis_for_week(user_id, week_start, week_end)
        
        return data
    
    def _analyze_focus_windows(self, week_data: Dict[str, Any]) -> List[FocusWindow]:
        """Identify best focus time windows."""
        hourly_focus = week_data.get('hourly_focus', {})
        hourly_attention = week_data.get('hourly_attention', {})
        
        windows = []
        
        # Create 2-hour windows
        for start_hour in range(7, 21):  # 7 AM to 9 PM
            end_hour = start_hour + 2
            
            # Calculate metrics for this window
            total_focus = sum(
                hourly_focus.get(h, 0) for h in range(start_hour, end_hour)
            )
            
            attention_scores = []
            for h in range(start_hour, end_hour):
                attention_scores.extend(hourly_attention.get(h, []))
            
            if total_focus > 0 and attention_scores:
                window = FocusWindow(
                    start_hour=start_hour,
                    end_hour=end_hour,
                    total_focus_minutes=total_focus,
                    average_attention_score=sum(attention_scores) / len(attention_scores),
                    sessions_count=len(attention_scores)
                )
                windows.append(window)
        
        # Sort by focus minutes * attention score
        windows.sort(
            key=lambda w: w.total_focus_minutes * w.average_attention_score,
            reverse=True
        )
        
        return windows[:3]  # Top 3 windows
    
    def _find_best_break_times(self, week_data: Dict[str, Any]) -> List[str]:
        """Find times when breaks are most accepted."""
        break_times = week_data.get('break_times', [])
        
        if not break_times:
            return []
        
        # Group by hour, calculate acceptance rate
        hourly_acceptance = defaultdict(lambda: {"accepted": 0, "total": 0})
        
        for hour, accepted in break_times:
            hourly_acceptance[hour]["total"] += 1
            if accepted:
                hourly_acceptance[hour]["accepted"] += 1
        
        # Calculate rates
        rates = []
        for hour, stats in hourly_acceptance.items():
            rate = stats["accepted"] / stats["total"]
            if stats["total"] >= 2:  # At least 2 break suggestions
                rates.append((hour, rate))
        
        # Sort by acceptance rate
        rates.sort(key=lambda x: x[1], reverse=True)
        
        # Format top 3
        return [
            f"{hour:02d}:00 ({rate:.0%} acceptance)"
            for hour, rate in rates[:3]
        ]
    
    def _find_high_energy_hours(self, week_data: Dict[str, Any]) -> List[int]:
        """Find hours with consistently high energy."""
        hourly_energy = week_data.get('hourly_energy', {})
        
        high_energy_hours = []
        
        for hour in range(24):
            energy_levels = hourly_energy.get(hour, [])
            if not energy_levels:
                continue
            
            # Convert to numeric (high=3, medium=2, low=1)
            numeric = [
                3 if e == 'high' else 2 if e == 'medium' else 1
                for e in energy_levels
            ]
            
            avg = sum(numeric) / len(numeric)
            if avg >= 2.5:  # Average is "high"
                high_energy_hours.append(hour)
        
        return high_energy_hours
    
    def _find_low_energy_hours(self, week_data: Dict[str, Any]) -> List[int]:
        """Find hours with consistently low energy."""
        hourly_energy = week_data.get('hourly_energy', {})
        
        low_energy_hours = []
        
        for hour in range(24):
            energy_levels = hourly_energy.get(hour, [])
            if not energy_levels:
                continue
            
            # Convert to numeric
            numeric = [
                3 if e == 'high' else 2 if e == 'medium' else 1
                for e in energy_levels
            ]
            
            avg = sum(numeric) / len(numeric)
            if avg <= 1.5:  # Average is "low"
                low_energy_hours.append(hour)
        
        return low_energy_hours
    
    def _calculate_daily_energy(self, week_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate average energy by day."""
        daily_energy = week_data.get('daily_energy', {})
        
        averages = {}
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        
        for day in days:
            energy_levels = daily_energy.get(day, [])
            if energy_levels:
                numeric = [
                    3 if e == 'high' else 2 if e == 'medium' else 1
                    for e in energy_levels
                ]
                averages[day] = sum(numeric) / len(numeric)
        
        return averages
    
    def _get_week_average_energy(self, week_data: Dict[str, Any]) -> float:
        """Get average energy for the week."""
        daily_avg = self._calculate_daily_energy(week_data)
        if not daily_avg:
            return 0.0
        return sum(daily_avg.values()) / len(daily_avg)
    
    def _calculate_trend(
        self,
        metric: str,
        current_value: float
    ) -> TrendDirection:
        """Calculate trend direction."""
        if len(self.report_history) < 2:
            return TrendDirection.INSUFFICIENT_DATA
        
        # Get previous week's value
        prev_report = self.report_history[-1]
        
        if metric == 'focus_minutes':
            prev_value = prev_report.total_focus_minutes
        elif metric == 'break_rate':
            prev_value = prev_report.break_acceptance_rate
        elif metric == 'average_energy':
            # Would need to calculate from previous week data
            return TrendDirection.STABLE
        else:
            return TrendDirection.INSUFFICIENT_DATA
        
        # Calculate change
        if prev_value == 0:
            return TrendDirection.STABLE
        
        change_pct = ((current_value - prev_value) / prev_value) * 100
        
        if change_pct > 10:
            return TrendDirection.IMPROVING
        elif change_pct < -10:
            return TrendDirection.DECLINING
        else:
            return TrendDirection.STABLE
    
    def _generate_recommendations(
        self,
        report: WeeklyReport,
        week_data: Dict[str, Any]
    ) -> List[str]:
        """Generate personalized recommendations."""
        recs = []
        
        # Focus window recommendations
        if report.best_focus_windows:
            best = report.best_focus_windows[0]
            recs.append(
                f"📍 Schedule important work during {best.start_hour:02d}:00-{best.end_hour:02d}:00 "
                f"(your best focus window this week)"
            )
        
        # Break recommendations
        if report.break_acceptance_rate < 0.5:
            recs.append(
                f"⚠️ Only accepted {report.break_acceptance_rate:.0%} of break suggestions. "
                f"Try accepting more breaks to sustain energy."
            )
        elif report.break_acceptance_rate > 0.8:
            recs.append(
                f"✅ Great break acceptance rate ({report.break_acceptance_rate:.0%})! Keep it up."
            )
        
        # Energy pattern recommendations
        if report.low_energy_hours:
            recs.append(
                f"🔋 Low energy typically at {report.low_energy_hours[0]:02d}:00. "
                f"Schedule simple tasks or breaks during this time."
            )
        
        # Hyperfocus recommendations
        if report.total_hyperfocus_hours > 10:
            recs.append(
                f"⚡ {report.total_hyperfocus_hours:.1f} hours of hyperfocus this week - "
                f"impressive, but watch for burnout. Ensure adequate recovery."
            )
        
        # Trend-based recommendations
        if report.focus_trend == TrendDirection.DECLINING:
            recs.append(
                "📉 Focus time is declining. Check for: too many meetings, distractions, burnout."
            )
        
        if not recs:
            recs.append("👍 Keep doing what you're doing - your patterns look healthy!")
        
        return recs
    
    def _format_report(self, report: WeeklyReport) -> str:
        """Format report for display."""
        lines = [
            f"📊 **Weekly Pattern Report**",
            f"Week of {report.week_start.strftime('%B %d')} - {report.week_end.strftime('%B %d, %Y')}",
            "",
            "## 🧠 Focus Patterns",
            f"- **Total Focus Time**: {report.total_focus_minutes} minutes ({report.total_focus_minutes / 60:.1f} hours)",
            f"- **Hyperfocus Sessions**: {report.total_hyperfocus_hours:.1f} hours",
            "",
            "### Best Focus Windows:",
        ]
        
        for i, window in enumerate(report.best_focus_windows, 1):
            lines.append(f"  {i}. {window}")
        
        lines.extend([
            "",
            "## ☕ Break Patterns",
            f"- **Suggested**: {report.total_breaks_suggested}",
            f"- **Accepted**: {report.total_breaks_accepted}",
            f"- **Acceptance Rate**: {report.break_acceptance_rate:.0%}",
        ])
        
        if report.best_break_times:
            lines.append("\n### Best Break Times:")
            for time in report.best_break_times:
                lines.append(f"  - {time}")
        
        lines.extend([
            "",
            "## 🔋 Energy Patterns",
            f"- **High Energy Hours**: {', '.join(f'{h:02d}:00' for h in report.high_energy_hours) if report.high_energy_hours else 'None identified'}",
            f"- **Low Energy Hours**: {', '.join(f'{h:02d}:00' for h in report.low_energy_hours) if report.low_energy_hours else 'None identified'}",
        ])
        
        lines.extend([
            "",
            "## 📈 Trends",
            f"- **Focus**: {report.focus_trend.value.title()}",
            f"- **Energy**: {report.energy_trend.value.title()}",
            f"- **Breaks**: {report.break_trend.value.title()}",
        ])
        
        lines.extend([
            "",
            "## 💡 Recommendations for Next Week",
        ])
        for rec in report.recommendations:
            lines.append(f"- {rec}")
        
        return "\n".join(lines)
    
    def _generate_visualizations(
        self,
        report: WeeklyReport,
        week_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate visualization data."""
        # Return data structures that could be visualized
        return {
            "focus_by_hour": week_data.get('hourly_focus', {}),
            "energy_by_day": report.average_daily_energy,
            "break_acceptance": {
                "accepted": report.total_breaks_accepted,
                "rejected": report.total_breaks_suggested - report.total_breaks_accepted
            }
        }
    
    def _extract_action_items(self, report: WeeklyReport) -> List[str]:
        """Extract actionable items from recommendations."""
        actions = []
        
        for rec in report.recommendations:
            if "Schedule" in rec or "Try" in rec or "Check for" in rec:
                # Extract the action part
                actions.append(rec)
        
        return actions[:3]  # Top 3 actions
    
    async def _save_report_to_conport(self, report: WeeklyReport):
        """Save weekly report to ConPort."""
        if not self.conport:
            return
        
        await self.conport.log_decision(
            summary=f"Weekly Pattern Report: {report.week_start.strftime('%b %d')}",
            rationale="ADHD pattern analysis and recommendations",
            implementation_details=self._format_report(report)
        )
