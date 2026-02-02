"""
Medication Effectiveness Tracker

Tracks ADHD medication effectiveness through objective metrics:
- Focus duration before/after medication
- Task completion rates
- Context switch frequency
- Energy levels throughout day
- Correlates with medication timing
- Generates effectiveness reports for medical appointments

ADHD Benefit: Data-driven medication management, objective feedback for doctors
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta, time
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MedicationType(Enum):
    """Common ADHD medication types."""
    STIMULANT_SHORT = "stimulant_short"  # 4-6 hours (e.g., Ritalin IR)
    STIMULANT_LONG = "stimulant_long"  # 8-12 hours (e.g., Adderall XR)
    NON_STIMULANT = "non_stimulant"  # 24 hours (e.g., Strattera)
    COMBINATION = "combination"  # Multiple medications


@dataclass
class MedicationDose:
    """Single medication dose."""
    medication_name: str
    medication_type: MedicationType
    dosage_mg: float
    taken_at: datetime
    expected_duration_hours: int
    notes: Optional[str] = None
    
    def is_active(self, at_time: datetime) -> bool:
        """Check if medication is still active."""
        elapsed = (at_time - self.taken_at).total_seconds() / 3600  # hours
        return elapsed < self.expected_duration_hours
    
    def effectiveness_window(self) -> Tuple[datetime, datetime]:
        """Get expected effectiveness window."""
        start = self.taken_at + timedelta(minutes=30)  # Typical onset
        end = self.taken_at + timedelta(hours=self.expected_duration_hours)
        return start, end


@dataclass
class CognitiveMetrics:
    """Cognitive performance metrics for a time period."""
    timestamp: datetime
    duration_minutes: int
    
    # Focus metrics
    avg_focus_duration_minutes: float
    max_focus_duration_minutes: int
    total_focused_minutes: int
    
    # Productivity metrics
    tasks_completed: int
    commits_made: int
    lines_written: int
    
    # Distraction metrics
    context_switches: int
    avg_switch_interval_minutes: float
    
    # Subjective metrics (user-reported 1-10 scale)
    self_reported_focus: Optional[int] = None
    self_reported_motivation: Optional[int] = None
    self_reported_anxiety: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for storage."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "duration_minutes": self.duration_minutes,
            "avg_focus_duration_minutes": self.avg_focus_duration_minutes,
            "max_focus_duration_minutes": self.max_focus_duration_minutes,
            "total_focused_minutes": self.total_focused_minutes,
            "tasks_completed": self.tasks_completed,
            "commits_made": self.commits_made,
            "lines_written": self.lines_written,
            "context_switches": self.context_switches,
            "avg_switch_interval_minutes": self.avg_switch_interval_minutes,
            "self_reported_focus": self.self_reported_focus,
            "self_reported_motivation": self.self_reported_motivation,
            "self_reported_anxiety": self.self_reported_anxiety
        }


@dataclass
class MedicationEffectivenessReport:
    """Effectiveness report for medical appointment."""
    user_id: str
    medication_name: str
    report_period_days: int
    generated_at: datetime
    
    # Aggregate metrics
    doses_taken: int
    avg_effectiveness_score: float  # 0-100
    
    # On medication vs baseline
    on_med_avg_focus: float
    baseline_avg_focus: float
    focus_improvement_pct: float
    
    on_med_tasks_per_hour: float
    baseline_tasks_per_hour: float
    productivity_improvement_pct: float
    
    on_med_context_switches: float
    baseline_context_switches: float
    distraction_reduction_pct: float
    
    # Timing insights
    best_dose_times: List[str]
    effectiveness_by_hour: Dict[int, float]
    
    # Subjective reports
    avg_self_reported_focus: Optional[float] = None
    avg_self_reported_motivation: Optional[float] = None
    avg_self_reported_anxiety: Optional[float] = None
    
    # Side effects tracking
    reported_side_effects: List[str] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)


class MedicationEffectivenessTracker:
    """
    Track ADHD medication effectiveness through objective metrics.
    
    Features:
    - Tracks cognitive metrics before/during/after medication
    - Correlates performance with medication timing
    - Generates reports for doctor appointments
    - Identifies optimal dosing times
    - Tracks side effects
    - Provides data-driven recommendations
    """
    
    def __init__(self, conport_client=None):
        """
        Initialize medication tracker.
        
        Args:
            conport_client: Optional ConPort client for data persistence
        """
        self.conport = conport_client
        
        # State tracking
        self.doses: List[MedicationDose] = []
        self.metrics: List[CognitiveMetrics] = []
        self.side_effects: List[Dict[str, Any]] = []
    
    def log_medication_dose(
        self,
        medication_name: str,
        medication_type: MedicationType,
        dosage_mg: float,
        taken_at: Optional[datetime] = None,
        expected_duration_hours: Optional[int] = None,
        notes: Optional[str] = None
    ) -> MedicationDose:
        """
        Log medication dose.
        
        Args:
            medication_name: Name of medication
            medication_type: Type of medication
            dosage_mg: Dosage in mg
            taken_at: When taken (defaults to now)
            expected_duration_hours: Expected duration (defaults based on type)
            notes: Optional notes
        
        Returns:
            MedicationDose object
        """
        if taken_at is None:
            taken_at = datetime.now()
        
        if expected_duration_hours is None:
            # Default durations
            if medication_type == MedicationType.STIMULANT_SHORT:
                expected_duration_hours = 4
            elif medication_type == MedicationType.STIMULANT_LONG:
                expected_duration_hours = 10
            elif medication_type == MedicationType.NON_STIMULANT:
                expected_duration_hours = 24
            else:
                expected_duration_hours = 8
        
        dose = MedicationDose(
            medication_name=medication_name,
            medication_type=medication_type,
            dosage_mg=dosage_mg,
            taken_at=taken_at,
            expected_duration_hours=expected_duration_hours,
            notes=notes
        )
        
        self.doses.append(dose)
        logger.info(f"💊 Logged dose: {medication_name} {dosage_mg}mg at {taken_at.strftime('%H:%M')}")
        
        # Log to ConPort if available
        if self.conport:
            try:
                self.conport.log_decision(
                    summary=f"Medication: {medication_name} {dosage_mg}mg",
                    rationale=f"Tracking effectiveness for {medication_type.value}",
                    implementation_details=notes or "No notes"
                )
            except Exception as e:
                logger.error(f"Failed to log dose to ConPort: {e}")
        
        return dose
    
    def log_cognitive_metrics(
        self,
        avg_focus_duration: float,
        max_focus_duration: int,
        total_focused_minutes: int,
        tasks_completed: int,
        commits_made: int,
        lines_written: int,
        context_switches: int,
        duration_minutes: int = 60,
        self_reported_focus: Optional[int] = None,
        self_reported_motivation: Optional[int] = None,
        self_reported_anxiety: Optional[int] = None
    ) -> CognitiveMetrics:
        """
        Log cognitive performance metrics.
        
        Args:
            avg_focus_duration: Average focus duration in minutes
            max_focus_duration: Maximum focus duration in minutes
            total_focused_minutes: Total minutes spent focused
            tasks_completed: Number of tasks completed
            commits_made: Number of git commits
            lines_written: Lines of code written
            context_switches: Number of context switches
            duration_minutes: Duration of measurement period
            self_reported_focus: User's self-rating (1-10)
            self_reported_motivation: Motivation rating (1-10)
            self_reported_anxiety: Anxiety rating (1-10)
        
        Returns:
            CognitiveMetrics object
        """
        avg_switch_interval = (
            duration_minutes / context_switches if context_switches > 0 else duration_minutes
        )
        
        metrics = CognitiveMetrics(
            timestamp=datetime.now(),
            duration_minutes=duration_minutes,
            avg_focus_duration_minutes=avg_focus_duration,
            max_focus_duration_minutes=max_focus_duration,
            total_focused_minutes=total_focused_minutes,
            tasks_completed=tasks_completed,
            commits_made=commits_made,
            lines_written=lines_written,
            context_switches=context_switches,
            avg_switch_interval_minutes=avg_switch_interval,
            self_reported_focus=self_reported_focus,
            self_reported_motivation=self_reported_motivation,
            self_reported_anxiety=self_reported_anxiety
        )
        
        self.metrics.append(metrics)
        
        return metrics
    
    def log_side_effect(
        self,
        effect_type: str,
        severity: str,  # "mild", "moderate", "severe"
        description: str,
        occurred_at: Optional[datetime] = None
    ):
        """
        Log medication side effect.
        
        Args:
            effect_type: Type of side effect (e.g., "headache", "insomnia")
            severity: Severity level
            description: Description of effect
            occurred_at: When it occurred
        """
        side_effect = {
            "type": effect_type,
            "severity": severity,
            "description": description,
            "occurred_at": occurred_at or datetime.now(),
            "active_medications": [
                dose.medication_name for dose in self.doses
                if dose.is_active(datetime.now())
            ]
        }
        
        self.side_effects.append(side_effect)
        logger.warning(f"⚠️ Side effect logged: {effect_type} ({severity})")
    
    def get_active_medications(self, at_time: Optional[datetime] = None) -> List[MedicationDose]:
        """Get currently active medications."""
        if at_time is None:
            at_time = datetime.now()
        
        return [dose for dose in self.doses if dose.is_active(at_time)]
    
    def is_medicated(self, at_time: Optional[datetime] = None) -> bool:
        """Check if user is currently medicated."""
        return len(self.get_active_medications(at_time)) > 0
    
    def get_baseline_metrics(self, days: int = 7) -> Optional[CognitiveMetrics]:
        """
        Get baseline (unmedicated) metrics.
        
        Args:
            days: Number of days to look back
        
        Returns:
            Aggregate baseline metrics or None if insufficient data
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        # Filter to unmedicated periods
        baseline_metrics = [
            m for m in self.metrics
            if m.timestamp >= cutoff and not self.is_medicated(m.timestamp)
        ]
        
        if not baseline_metrics:
            return None
        
        # Aggregate
        total_duration = sum(m.duration_minutes for m in baseline_metrics)
        
        return CognitiveMetrics(
            timestamp=datetime.now(),
            duration_minutes=total_duration,
            avg_focus_duration_minutes=sum(m.avg_focus_duration_minutes for m in baseline_metrics) / len(baseline_metrics),
            max_focus_duration_minutes=max(m.max_focus_duration_minutes for m in baseline_metrics),
            total_focused_minutes=sum(m.total_focused_minutes for m in baseline_metrics),
            tasks_completed=sum(m.tasks_completed for m in baseline_metrics),
            commits_made=sum(m.commits_made for m in baseline_metrics),
            lines_written=sum(m.lines_written for m in baseline_metrics),
            context_switches=sum(m.context_switches for m in baseline_metrics),
            avg_switch_interval_minutes=sum(m.avg_switch_interval_minutes for m in baseline_metrics) / len(baseline_metrics),
            self_reported_focus=int(sum(m.self_reported_focus or 0 for m in baseline_metrics) / len(baseline_metrics)) if any(m.self_reported_focus for m in baseline_metrics) else None
        )
    
    def get_medicated_metrics(self, days: int = 7) -> Optional[CognitiveMetrics]:
        """Get medicated period metrics."""
        cutoff = datetime.now() - timedelta(days=days)
        
        # Filter to medicated periods
        medicated_metrics = [
            m for m in self.metrics
            if m.timestamp >= cutoff and self.is_medicated(m.timestamp)
        ]
        
        if not medicated_metrics:
            return None
        
        # Aggregate
        total_duration = sum(m.duration_minutes for m in medicated_metrics)
        
        return CognitiveMetrics(
            timestamp=datetime.now(),
            duration_minutes=total_duration,
            avg_focus_duration_minutes=sum(m.avg_focus_duration_minutes for m in medicated_metrics) / len(medicated_metrics),
            max_focus_duration_minutes=max(m.max_focus_duration_minutes for m in medicated_metrics),
            total_focused_minutes=sum(m.total_focused_minutes for m in medicated_metrics),
            tasks_completed=sum(m.tasks_completed for m in medicated_metrics),
            commits_made=sum(m.commits_made for m in medicated_metrics),
            lines_written=sum(m.lines_written for m in medicated_metrics),
            context_switches=sum(m.context_switches for m in medicated_metrics),
            avg_switch_interval_minutes=sum(m.avg_switch_interval_minutes for m in medicated_metrics) / len(medicated_metrics),
            self_reported_focus=int(sum(m.self_reported_focus or 0 for m in medicated_metrics) / len(medicated_metrics)) if any(m.self_reported_focus for m in medicated_metrics) else None
        )
    
    def generate_effectiveness_report(
        self,
        user_id: str,
        medication_name: str,
        days: int = 30
    ) -> MedicationEffectivenessReport:
        """
        Generate effectiveness report for doctor appointment.
        
        Args:
            user_id: User identifier
            medication_name: Medication to report on
            days: Number of days to analyze
        
        Returns:
            Effectiveness report
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        # Filter doses for this medication
        relevant_doses = [
            d for d in self.doses
            if d.medication_name == medication_name and d.taken_at >= cutoff
        ]
        
        # Get baseline and medicated metrics
        baseline = self.get_baseline_metrics(days)
        medicated = self.get_medicated_metrics(days)
        
        if not baseline or not medicated:
            raise ValueError("Insufficient data for report generation")
        
        # Calculate improvements
        focus_improvement = (
            ((medicated.avg_focus_duration_minutes - baseline.avg_focus_duration_minutes) /
             baseline.avg_focus_duration_minutes) * 100
        )
        
        baseline_tasks_per_hour = baseline.tasks_completed / (baseline.total_focused_minutes / 60)
        medicated_tasks_per_hour = medicated.tasks_completed / (medicated.total_focused_minutes / 60)
        productivity_improvement = (
            ((medicated_tasks_per_hour - baseline_tasks_per_hour) /
             baseline_tasks_per_hour) * 100
        )
        
        distraction_reduction = (
            ((baseline.context_switches - medicated.context_switches) /
             baseline.context_switches) * 100
        )
        
        # Analyze best dosing times
        dose_hours = [d.taken_at.hour for d in relevant_doses]
        best_times = list(set(dose_hours))  # Unique hours
        
        # Effectiveness by hour
        effectiveness_by_hour = {}
        for hour in range(24):
            hour_metrics = [
                m for m in self.metrics
                if m.timestamp.hour == hour and self.is_medicated(m.timestamp)
            ]
            if hour_metrics:
                avg_focus = sum(m.avg_focus_duration_minutes for m in hour_metrics) / len(hour_metrics)
                effectiveness_by_hour[hour] = avg_focus
        
        # Calculate overall effectiveness score
        effectiveness_score = min(100, (
            (focus_improvement / 100 * 40) +
            (productivity_improvement / 100 * 40) +
            (distraction_reduction / 100 * 20)
        ))
        
        # Generate recommendations
        recommendations = []
        if focus_improvement < 20:
            recommendations.append("Focus improvement is modest. Consider dosage adjustment or timing change.")
        if productivity_improvement < 15:
            recommendations.append("Productivity gains are limited. Discuss with doctor.")
        if distraction_reduction < 25:
            recommendations.append("Distraction levels still high. May need additional support strategies.")
        if len(self.side_effects) > 5:
            recommendations.append(f"{len(self.side_effects)} side effects reported. Discuss with doctor.")
        
        # Side effects summary
        recent_side_effects = [
            se["type"] for se in self.side_effects
            if se["occurred_at"] >= cutoff
        ]
        
        report = MedicationEffectivenessReport(
            user_id=user_id,
            medication_name=medication_name,
            report_period_days=days,
            generated_at=datetime.now(),
            doses_taken=len(relevant_doses),
            avg_effectiveness_score=effectiveness_score,
            on_med_avg_focus=medicated.avg_focus_duration_minutes,
            baseline_avg_focus=baseline.avg_focus_duration_minutes,
            focus_improvement_pct=focus_improvement,
            on_med_tasks_per_hour=medicated_tasks_per_hour,
            baseline_tasks_per_hour=baseline_tasks_per_hour,
            productivity_improvement_pct=productivity_improvement,
            on_med_context_switches=medicated.context_switches,
            baseline_context_switches=baseline.context_switches,
            distraction_reduction_pct=distraction_reduction,
            best_dose_times=[f"{h:02d}:00" for h in best_times],
            effectiveness_by_hour=effectiveness_by_hour,
            avg_self_reported_focus=medicated.self_reported_focus,
            reported_side_effects=list(set(recent_side_effects)),
            recommendations=recommendations
        )
        
        return report
    
    def format_report_for_doctor(self, report: MedicationEffectivenessReport) -> str:
        """Format report for doctor appointment."""
        lines = [
            f"# Medication Effectiveness Report",
            f"**Patient**: {report.user_id}",
            f"**Medication**: {report.medication_name}",
            f"**Period**: {report.report_period_days} days ({report.generated_at.strftime('%Y-%m-%d')})",
            "",
            "## Summary",
            f"- **Doses Taken**: {report.doses_taken}",
            f"- **Overall Effectiveness**: {report.avg_effectiveness_score:.1f}/100",
            "",
            "## Objective Metrics",
            "",
            "### Focus Duration",
            f"- Baseline: {report.baseline_avg_focus:.1f} min",
            f"- On Medication: {report.on_med_avg_focus:.1f} min",
            f"- **Improvement: {report.focus_improvement_pct:+.1f}%**",
            "",
            "### Productivity",
            f"- Baseline: {report.baseline_tasks_per_hour:.1f} tasks/hour",
            f"- On Medication: {report.on_med_tasks_per_hour:.1f} tasks/hour",
            f"- **Improvement: {report.productivity_improvement_pct:+.1f}%**",
            "",
            "### Distractibility",
            f"- Baseline: {report.baseline_context_switches:.0f} switches/hour",
            f"- On Medication: {report.on_med_context_switches:.0f} switches/hour",
            f"- **Reduction: {report.distraction_reduction_pct:+.1f}%**",
            "",
        ]
        
        if report.avg_self_reported_focus:
            lines.extend([
                "## Subjective Reports",
                f"- Average Self-Reported Focus: {report.avg_self_reported_focus:.1f}/10",
                "",
            ])
        
        if report.reported_side_effects:
            lines.extend([
                "## Side Effects",
                *[f"- {effect}" for effect in report.reported_side_effects],
                "",
            ])
        
        if report.best_dose_times:
            lines.extend([
                "## Dosing Schedule",
                f"- Most Common Times: {', '.join(report.best_dose_times)}",
                "",
            ])
        
        if report.recommendations:
            lines.extend([
                "## Recommendations",
                *[f"- {rec}" for rec in report.recommendations],
                "",
            ])
        
        return "\n".join(lines)
