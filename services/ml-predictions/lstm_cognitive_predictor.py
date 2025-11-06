#!/usr/bin/env python3
"""
LSTM Cognitive Load Predictor - Phase 3.2 ML-Powered Predictions
Simplified version for API integration with enhanced confidence calculation
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

try:
    import pandas as pd
except ImportError:
    # Fallback if pandas not available
    pd = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LSTMCognitivePredictor:
    """
    Simplified LSTM-based cognitive load predictor for API integration.
    Includes multi-factor confidence calculation for reliability assessment.
    """

    def __init__(self):
        self.model_loaded = False
        logger.info("LSTM Cognitive Predictor initialized (simplified for API)")

    async def predict_next_load_async(
        self,
        historical_data: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
        prediction_minutes: int = 15
    ) -> Dict[str, Any]:
        """
        Simplified prediction method for API usage.
        Returns enhanced predictions with multi-factor confidence assessment.
        """
        # For now, return mock predictions based on recent data
        if not historical_data:
            return {
                'prediction': 0.5,
                'confidence': 0.3,
                'recommended_actions': ['Monitor your cognitive state closely']
            }

        # Simple mock prediction based on recent average
        recent_loads = [d['cognitive_load'] for d in historical_data[-10:]]
        avg_load = sum(recent_loads) / len(recent_loads)

        # Mock prediction: slightly trend toward mean
        prediction = avg_load + (0.5 - avg_load) * 0.1
        prediction = max(0.0, min(1.0, prediction))

        # Enhanced confidence calculation using multi-factor analysis
        confidence = self._calculate_prediction_confidence(historical_data, prediction)

        # Generate recommended actions based on prediction and confidence
        actions = self._generate_recommended_actions(prediction, confidence, context)

        return {
            'prediction': prediction,
            'confidence': confidence,
            'recommended_actions': actions[:3],
            'timestamp': datetime.utcnow(),
            'prediction_minutes': prediction_minutes
        }

    async def predict_next_load(self, historical_data, prediction_minutes=15):
        """Legacy method for compatibility."""
        # Convert to list format and call async method
        if hasattr(historical_data, 'to_dict'):  # pandas DataFrame
            data_list = []
            for _, row in historical_data.iterrows():
                data_list.append({
                    'timestamp': row.get('timestamp', datetime.utcnow()),
                    'energy_level': row.get('energy_level', 0.5),
                    'attention_focus': row.get('attention_focus', 0.5),
                    'cognitive_load': row.get('cognitive_load', 0.5),
                    'task_complexity': row.get('task_complexity', 0.5),
                    'context_switches': row.get('context_switches', 0),
                    'break_frequency': row.get('break_frequency', 0),
                    'session_duration': row.get('session_duration', 60),
                    'interruptions': row.get('interruptions', 0)
                })
            return await self.predict_next_load_async(data_list, None, prediction_minutes)

        return await self.predict_next_load_async(historical_data, None, prediction_minutes)

    def _calculate_prediction_confidence(
        self,
        historical_data: List[Dict[str, Any]],
        prediction: float
    ) -> float:
        """
        Calculate prediction confidence using multi-factor analysis:
        - Data quality and consistency (30%)
        - Pattern stability (25%)
        - Prediction characteristics (25%)
        - Model calibration (20%)
        """
        if not historical_data:
            return 0.3  # Low confidence for insufficient data

        # Convert to DataFrame for analysis
        df = pd.DataFrame(historical_data)

        # Factor 1: Data Quality (30% weight)
        data_quality_score = self._assess_data_quality(df)

        # Factor 2: Pattern Stability (25% weight)
        pattern_stability = self._assess_pattern_stability(df)

        # Factor 3: Prediction Characteristics (25% weight)
        prediction_characteristics = self._assess_prediction_characteristics(prediction, df)

        # Factor 4: Model Calibration (20% weight)
        model_calibration = self._assess_model_calibration()

        # Weighted confidence calculation
        confidence = (
            data_quality_score * 0.30 +
            pattern_stability * 0.25 +
            prediction_characteristics * 0.25 +
            model_calibration * 0.20
        )

        return max(0.0, min(1.0, confidence))

    def _assess_data_quality(self, df) -> float:
        """Assess data quality based on completeness, recency, and consistency."""
        score = 1.0

        # Recency penalty (more recent data = higher confidence)
        if not df.empty and 'timestamp' in df.columns:
            # Convert timestamp if needed
            if isinstance(df['timestamp'].iloc[0], str):
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            hours_since_last = (datetime.now() - df['timestamp'].max()).total_seconds() / 3600
            recency_penalty = min(hours_since_last / 24, 0.3)  # Max 30% penalty
            score -= recency_penalty

        # Completeness check (missing data reduces confidence)
        total_points = len(df)
        if total_points < 10:
            completeness_penalty = (10 - total_points) / 10 * 0.2  # Max 20% penalty
            score -= completeness_penalty

        # Data variance check (too much noise = lower confidence)
        if 'cognitive_load' in df.columns and len(df) > 5:
            variance = df['cognitive_load'].var()
            if variance > 0.1:  # High variance indicates noisy data
                variance_penalty = min(variance * 2, 0.15)  # Max 15% penalty
                score -= variance_penalty

        return max(0.0, score)

    def _assess_pattern_stability(self, df) -> float:
        """Assess stability of cognitive patterns over time."""
        if len(df) < 20:  # Need sufficient data for pattern analysis
            return 0.5

        # Calculate trend stability (how consistent are the patterns)
        if 'cognitive_load' in df.columns:
            # Rolling standard deviation (lower = more stable)
            rolling_std = df['cognitive_load'].rolling(window=min(10, len(df))).std()
            avg_stability = 1.0 - min(rolling_std.mean(), 0.5)  # Convert to 0-1 scale
            return avg_stability

        return 0.6  # Default moderate stability

    def _assess_prediction_characteristics(self, prediction: float, df) -> float:
        """Assess prediction characteristics (extremity, plausibility)."""
        score = 1.0

        # Extremity penalty (extreme predictions less confident)
        if prediction < 0.2 or prediction > 0.8:
            extremity_penalty = 0.2  # 20% penalty for extreme predictions
            score -= extremity_penalty

        # Plausibility check against recent data
        if 'cognitive_load' in df.columns and len(df) > 5:
            recent_avg = df['cognitive_load'].tail(10).mean()
            deviation = abs(prediction - recent_avg)

            if deviation > 0.3:  # Prediction significantly different from recent average
                plausibility_penalty = min(deviation, 0.25)  # Max 25% penalty
                score -= plausibility_penalty

        return max(0.0, score)

    def _assess_model_calibration(self) -> float:
        """Assess model calibration and training status."""
        # For now, return moderate confidence
        # In production, this would check:
        # - Training data quality and recency
        # - Cross-validation performance
        # - Model drift detection
        # - Recent accuracy metrics
        return 0.75

    def _generate_recommended_actions(
        self,
        prediction: float,
        confidence: float,
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Generate recommended actions based on prediction and context."""
        actions = []

        # Base recommendations based on prediction level
        if prediction > 0.8:
            actions.extend([
                "Take a 10-15 minute break to reset cognitive load",
                "Consider task switching to lower-complexity work",
                "Review and simplify current task requirements"
            ])
        elif prediction > 0.6:
            actions.extend([
                "Schedule a short break within the next 10 minutes",
                "Consider breaking current task into smaller steps",
                "Monitor energy levels and take proactive breaks"
            ])
        elif prediction < 0.3:
            actions.extend([
                "Good time for complex problem-solving tasks",
                "Consider tackling high-priority items requiring focus",
                "Optimal time for deep work sessions"
            ])

        # Confidence-based adjustments
        if confidence < 0.7:
            actions.append("Prediction confidence is moderate - monitor your state closely")
        elif confidence < 0.5:
            actions.append("Prediction confidence is low - rely more on self-assessment")

        # Context-based recommendations
        if context:
            current_task = context.get('current_task', '').lower()
            if 'debugging' in current_task and prediction > 0.7:
                actions.append("Consider stepping away from debugging and returning later")
            elif 'design' in current_task and prediction < 0.4:
                actions.append("Excellent time for design and creative work")

        return actions[:3]  # Limit to top 3 actions