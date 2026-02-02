"""
Cross-Service Data Correlation Engine

Correlates data across ADHD services for deeper insights:
- Energy + Complexity → Optimal task matching
- Attention + Switches → Distraction pattern detection
- Break Acceptance + Productivity → Break timing optimization

ADHD Benefit: Holistic view of cognitive patterns, smarter recommendations
"""
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from statistics import mean, correlation

logger = logging.getLogger(__name__)


@dataclass
class CorrelationInsight:
    """Insight from cross-service data correlation."""
    insight_type: str  # "task_matching", "distraction_pattern", "break_optimization"
    confidence: float  # 0.0-1.0
    description: str  # Human-readable insight
    recommendation: str  # Actionable recommendation
    source_services: List[str]  # Services that contributed data
    supporting_data: Dict[str, Any] = None  # Raw data supporting the insight
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class CrossServiceCorrelator:
    """
    Correlate data across ADHD services for deeper insights.
    
    Integrates with:
    - ADHD Engine (energy, attention)
    - Complexity Coordinator (code complexity)
    - Context Switch Tracker (distraction patterns)
    - Break Suggester (break timing, acceptance)
    - Activity Capture (productivity metrics)
    """
    
    def __init__(self, redis_client):
        """
        Initialize correlator.
        
        Args:
            redis_client: Redis client for fetching service data
        """
        self.redis = redis_client
        self.insight_cache: Dict[str, CorrelationInsight] = {}
        self.cache_ttl = 300  # 5 minutes
    
    async def correlate_energy_complexity(
        self,
        user_id: str,
        lookback_hours: int = 24
    ) -> CorrelationInsight:
        """
        Optimal task matching based on energy and complexity patterns.
        
        Analyzes:
        - When user has high energy + tackles high complexity successfully
        - When user struggles with complexity at certain energy levels
        - Optimal energy-complexity pairings
        
        Args:
            user_id: User identifier
            lookback_hours: Hours of history to analyze
        
        Returns:
            CorrelationInsight with task matching recommendations
        """
        cache_key = f"energy_complexity_{user_id}"
        if cache_key in self.insight_cache:
            cached = self.insight_cache[cache_key]
            if (datetime.now() - cached.timestamp).total_seconds() < self.cache_ttl:
                return cached
        
        try:
            # Fetch energy levels from last N hours
            energy_data = await self._fetch_energy_history(user_id, lookback_hours)
            
            # Fetch complexity assessments
            complexity_data = await self._fetch_complexity_history(user_id, lookback_hours)
            
            # Correlate energy with successful complexity handling
            correlation_score = self._correlate_energy_complexity_success(
                energy_data, complexity_data
            )
            
            # Generate insight
            insight = self._generate_task_matching_insight(
                correlation_score, energy_data, complexity_data
            )
            
            # Cache
            self.insight_cache[cache_key] = insight
            
            return insight
            
        except Exception as e:
            logger.error(f"Energy-complexity correlation failed: {e}")
            return CorrelationInsight(
                insight_type="task_matching",
                confidence=0.1,
                description="Insufficient data for correlation",
                recommendation="Continue working to gather more data",
                source_services=["adhd-engine", "complexity-coordinator"]
            )
    
    async def correlate_attention_switches(
        self,
        user_id: str,
        lookback_hours: int = 24
    ) -> CorrelationInsight:
        """
        Distraction pattern detection based on attention state and context switches.
        
        Identifies:
        - Times of day when switches spike
        - Types of switches that break focus
        - Early warning signs of distraction spirals
        
        Args:
            user_id: User identifier
            lookback_hours: Hours of history to analyze
        
        Returns:
            CorrelationInsight with distraction mitigation recommendations
        """
        try:
            # Fetch attention states
            attention_data = await self._fetch_attention_history(user_id, lookback_hours)
            
            # Fetch context switches
            switch_data = await self._fetch_switch_history(user_id, lookback_hours)
            
            # Correlate scattered states with switch patterns
            pattern = self._identify_distraction_pattern(attention_data, switch_data)
            
            # Generate insight
            insight = self._generate_distraction_insight(pattern, attention_data, switch_data)
            
            return insight
            
        except Exception as e:
            logger.error(f"Attention-switches correlation failed: {e}")
            return CorrelationInsight(
                insight_type="distraction_pattern",
                confidence=0.1,
                description="Insufficient data for pattern detection",
                recommendation="Continue monitoring to establish baseline",
                source_services=["adhd-engine", "context-switch-tracker"]
            )
    
    async def correlate_break_productivity(
        self,
        user_id: str,
        lookback_days: int = 7
    ) -> CorrelationInsight:
        """
        Break timing optimization based on break acceptance and productivity.
        
        Analyzes:
        - When breaks are accepted vs. dismissed
        - Productivity before/after breaks
        - Optimal break timing for this user
        
        Args:
            user_id: User identifier
            lookback_days: Days of history to analyze
        
        Returns:
            CorrelationInsight with break timing recommendations
        """
        try:
            # Fetch break suggestions and responses
            break_data = await self._fetch_break_history(user_id, lookback_days)
            
            # Fetch productivity metrics
            productivity_data = await self._fetch_productivity_history(user_id, lookback_days)
            
            # Correlate break timing with productivity
            optimal_timing = self._identify_optimal_break_timing(
                break_data, productivity_data
            )
            
            # Generate insight
            insight = self._generate_break_optimization_insight(
                optimal_timing, break_data, productivity_data
            )
            
            return insight
            
        except Exception as e:
            logger.error(f"Break-productivity correlation failed: {e}")
            return CorrelationInsight(
                insight_type="break_optimization",
                confidence=0.1,
                description="Insufficient data for break optimization",
                recommendation="Accept more break suggestions to learn patterns",
                source_services=["break-suggester", "activity-capture"]
            )
    
    def _correlate_energy_complexity_success(
        self,
        energy_data: List[Dict],
        complexity_data: List[Dict]
    ) -> float:
        """Calculate correlation between energy and complexity handling."""
        # Simplified correlation - in production, use scipy.stats
        if len(energy_data) < 5 or len(complexity_data) < 5:
            return 0.5
        
        # Mock correlation score
        return 0.7
    
    def _identify_distraction_pattern(
        self,
        attention_data: List[Dict],
        switch_data: List[Dict]
    ) -> Dict[str, Any]:
        """Identify distraction patterns from attention and switch data."""
        # Analyze switch frequency during scattered states
        scattered_periods = [
            a for a in attention_data if a.get('state') == 'scattered'
        ]
        
        if not scattered_periods:
            return {'pattern': 'none', 'confidence': 0.3}
        
        # Count switches during scattered periods
        switch_count = len([
            s for s in switch_data
            if any(
                abs((s.get('timestamp', datetime.now()) - 
                     a.get('timestamp', datetime.now())).total_seconds()) < 300
                for a in scattered_periods
            )
        ])
        
        return {
            'pattern': 'high_switch_scatter' if switch_count > 5 else 'moderate',
            'switch_count': switch_count,
            'confidence': 0.7
        }
    
    def _identify_optimal_break_timing(
        self,
        break_data: List[Dict],
        productivity_data: List[Dict]
    ) -> Dict[str, Any]:
        """Identify optimal break timing from historical data."""
        # Analyze productivity delta after breaks
        accepted_breaks = [b for b in break_data if b.get('accepted', False)]
        
        if not accepted_breaks:
            return {'optimal_minutes': 45, 'confidence': 0.3}
        
        # Calculate average time worked before accepting break
        work_durations = [b.get('minutes_since_last_break', 45) for b in accepted_breaks]
        
        if work_durations:
            optimal = int(mean(work_durations))
            return {'optimal_minutes': optimal, 'confidence': 0.8}
        
        return {'optimal_minutes': 45, 'confidence': 0.5}
    
    def _generate_task_matching_insight(
        self,
        correlation_score: float,
        energy_data: List[Dict],
        complexity_data: List[Dict]
    ) -> CorrelationInsight:
        """Generate task matching insight."""
        if correlation_score > 0.7:
            return CorrelationInsight(
                insight_type="task_matching",
                confidence=correlation_score,
                description="Strong correlation found between high energy and successful complex task completion",
                recommendation="Schedule complex architecture/design work during high energy periods (mornings typically)",
                source_services=["adhd-engine", "complexity-coordinator"],
                supporting_data={'correlation': correlation_score}
            )
        else:
            return CorrelationInsight(
                insight_type="task_matching",
                confidence=correlation_score,
                description="Moderate energy-complexity correlation detected",
                recommendation="Continue monitoring to identify optimal task-energy pairings",
                source_services=["adhd-engine", "complexity-coordinator"],
                supporting_data={'correlation': correlation_score}
            )
    
    def _generate_distraction_insight(
        self,
        pattern: Dict[str, Any],
        attention_data: List[Dict],
        switch_data: List[Dict]
    ) -> CorrelationInsight:
        """Generate distraction pattern insight."""
        if pattern['pattern'] == 'high_switch_scatter':
            return CorrelationInsight(
                insight_type="distraction_pattern",
                confidence=pattern['confidence'],
                description=f"High context switching detected during scattered attention ({pattern['switch_count']} switches)",
                recommendation="⚠️ Distraction spiral detected - close extra windows, use focus mode, or take break",
                source_services=["adhd-engine", "context-switch-tracker"],
                supporting_data=pattern
            )
        else:
            return CorrelationInsight(
                insight_type="distraction_pattern",
                confidence=pattern['confidence'],
                description="Moderate context switching observed",
                recommendation="Attention holding well - continue current work pattern",
                source_services=["adhd-engine", "context-switch-tracker"],
                supporting_data=pattern
            )
    
    def _generate_break_optimization_insight(
        self,
        optimal_timing: Dict[str, Any],
        break_data: List[Dict],
        productivity_data: List[Dict]
    ) -> CorrelationInsight:
        """Generate break timing optimization insight."""
        optimal_min = optimal_timing['optimal_minutes']
        confidence = optimal_timing['confidence']
        
        return CorrelationInsight(
            insight_type="break_optimization",
            confidence=confidence,
            description=f"Your optimal break timing: every {optimal_min} minutes based on historical acceptance patterns",
            recommendation=f"🎯 Configure break suggester to {optimal_min}-minute intervals for best results",
            source_services=["break-suggester", "activity-capture"],
            supporting_data=optimal_timing
        )
    
    # Data fetching methods (mock implementations - replace with actual service calls)
    
    async def _fetch_energy_history(self, user_id: str, hours: int) -> List[Dict]:
        """Fetch energy level history from ADHD Engine."""
        # Mock - replace with actual Redis/API call
        return []
    
    async def _fetch_complexity_history(self, user_id: str, hours: int) -> List[Dict]:
        """Fetch complexity assessments from Complexity Coordinator."""
        # Mock - replace with actual service call
        return []
    
    async def _fetch_attention_history(self, user_id: str, hours: int) -> List[Dict]:
        """Fetch attention states from ADHD Engine."""
        # Mock - replace with actual Redis/API call
        return []
    
    async def _fetch_switch_history(self, user_id: str, hours: int) -> List[Dict]:
        """Fetch context switches from Context Switch Tracker."""
        # Mock - replace with actual service call
        return []
    
    async def _fetch_break_history(self, user_id: str, days: int) -> List[Dict]:
        """Fetch break suggestions and responses from Break Suggester."""
        # Mock - replace with actual service call
        return []
    
    async def _fetch_productivity_history(self, user_id: str, days: int) -> List[Dict]:
        """Fetch productivity metrics from Activity Capture."""
        # Mock - replace with actual service call
        return []
