"""
Personalized Attention State Calibration

Learns user-specific thresholds for attention detection through feedback.
Improves accuracy of attention state predictions over time.

ADHD Benefit: Personalized to individual patterns, not one-size-fits-all
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json
import os
from statistics import mean, stdev

logger = logging.getLogger(__name__)


@dataclass
class CalibrationSample:
    """Single calibration data point from user feedback."""
    predicted_state: str  # "focused", "scattered", "hyperfocus", etc.
    actual_state: str  # User's correction
    timestamp: datetime
    context: Dict[str, Any]  # Contributing signals (energy, complexity, switches, etc.)
    confidence: float = 0.5  # Model's confidence in original prediction
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            'predicted_state': self.predicted_state,
            'actual_state': self.actual_state,
            'timestamp': self.timestamp.isoformat(),
            'context': self.context,
            'confidence': self.confidence
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CalibrationSample':
        """Deserialize from dict."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class AttentionCalibrator:
    """
    Calibrate attention detection to individual user patterns.
    
    Learns from feedback to adjust:
    - Confidence thresholds for each state
    - Feature weights (energy vs. switches vs. complexity)
    - Hyperfocus detection duration
    - Scattered state sensitivity
    """
    
    def __init__(
        self,
        user_id: str,
        storage_path: str = ".calibration_data"
    ):
        """
        Initialize attention calibrator.
        
        Args:
            user_id: User identifier
            storage_path: Directory for calibration data
        """
        self.user_id = user_id
        self.storage_path = storage_path
        self.samples: List[CalibrationSample] = []
        
        # Default thresholds (will be personalized)
        self.personal_thresholds = {
            "focused_confidence": 0.7,
            "scattered_confidence": 0.6,
            "hyperfocus_duration_min": 45,  # Minutes
            "scattered_switch_threshold": 5,  # Switches per 30min
            "energy_weight": 0.4,  # How much to weight energy vs. other signals
            "complexity_weight": 0.3,
            "switches_weight": 0.3
        }
        
        # Create storage
        os.makedirs(storage_path, exist_ok=True)
        
        # Load existing calibration
        self._load_calibration()
    
    def _load_calibration(self) -> bool:
        """Load saved calibration data."""
        try:
            filename = f"{self.storage_path}/{self.user_id}_calibration.json"
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    data = json.load(f)
                
                self.personal_thresholds = data['thresholds']
                self.samples = [
                    CalibrationSample.from_dict(s) for s in data['samples']
                ]
                
                logger.info(f"✅ Loaded calibration: {len(self.samples)} samples")
                return True
        except Exception as e:
            logger.warning(f"Failed to load calibration: {e}")
        return False
    
    def _save_calibration(self) -> bool:
        """Save calibration data."""
        try:
            filename = f"{self.storage_path}/{self.user_id}_calibration.json"
            with open(filename, 'w') as f:
                json.dump({
                    'user_id': self.user_id,
                    'thresholds': self.personal_thresholds,
                    'samples': [s.to_dict() for s in self.samples],
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save calibration: {e}")
            return False
    
    def record_feedback(
        self,
        predicted: str,
        actual: str,
        context: Dict[str, Any],
        confidence: float = 0.5
    ) -> None:
        """
        Record user feedback on attention prediction.
        
        Args:
            predicted: What the model predicted
            actual: What the user reports as actual state
            context: Context signals at time of prediction
            confidence: Model's confidence in prediction
        """
        sample = CalibrationSample(
            predicted_state=predicted,
            actual_state=actual,
            timestamp=datetime.now(),
            context=context,
            confidence=confidence
        )
        
        self.samples.append(sample)
        
        # Auto-calibrate after collecting enough samples
        if len(self.samples) >= 10 and len(self.samples) % 5 == 0:
            self.calibrate()
        
        # Save after each feedback
        self._save_calibration()
        
        logger.info(f"📝 Feedback recorded: {predicted} → {actual} (total: {len(self.samples)})")
    
    def calibrate(self) -> Dict[str, float]:
        """
        Recalibrate thresholds based on accumulated feedback.
        
        Analyzes patterns in mispredictions to adjust thresholds.
        
        Returns:
            Updated thresholds
        """
        if len(self.samples) < 10:
            logger.warning(f"Insufficient samples for calibration: {len(self.samples)}")
            return self.personal_thresholds
        
        logger.info(f"🔧 Calibrating with {len(self.samples)} samples")
        
        try:
            # Analyze accuracy by state
            accuracy_by_state = self._calculate_accuracy_by_state()
            
            # Adjust confidence thresholds based on accuracy
            self._adjust_confidence_thresholds(accuracy_by_state)
            
            # Analyze hyperfocus duration patterns
            self._calibrate_hyperfocus_duration()
            
            # Analyze scattered state patterns
            self._calibrate_scattered_sensitivity()
            
            # Recalibrate feature weights
            self._calibrate_feature_weights()
            
            # Save updated thresholds
            self._save_calibration()
            
            logger.info(f"✅ Calibration complete: {self.personal_thresholds}")
            return self.personal_thresholds
            
        except Exception as e:
            logger.error(f"Calibration failed: {e}")
            return self.personal_thresholds
    
    def _calculate_accuracy_by_state(self) -> Dict[str, float]:
        """Calculate prediction accuracy for each attention state."""
        state_stats = {}
        
        for sample in self.samples:
            state = sample.predicted_state
            correct = (sample.predicted_state == sample.actual_state)
            
            if state not in state_stats:
                state_stats[state] = {'correct': 0, 'total': 0}
            
            state_stats[state]['total'] += 1
            if correct:
                state_stats[state]['correct'] += 1
        
        accuracy = {
            state: stats['correct'] / stats['total']
            for state, stats in state_stats.items()
            if stats['total'] > 0
        }
        
        return accuracy
    
    def _adjust_confidence_thresholds(self, accuracy: Dict[str, float]) -> None:
        """
        Adjust confidence thresholds based on accuracy.
        
        If we're over-predicting (low accuracy), raise threshold.
        If we're under-predicting, lower threshold.
        """
        for state in ['focused', 'scattered']:
            if state in accuracy:
                current_threshold = self.personal_thresholds.get(f"{state}_confidence", 0.7)
                acc = accuracy[state]
                
                if acc < 0.6:
                    # Low accuracy - make more conservative (raise threshold)
                    new_threshold = min(0.9, current_threshold + 0.05)
                elif acc > 0.8:
                    # High accuracy - can be more aggressive (lower threshold)
                    new_threshold = max(0.5, current_threshold - 0.05)
                else:
                    # Acceptable accuracy - small adjustment
                    new_threshold = current_threshold
                
                self.personal_thresholds[f"{state}_confidence"] = new_threshold
    
    def _calibrate_hyperfocus_duration(self) -> None:
        """
        Calibrate hyperfocus detection duration based on user patterns.
        
        Analyzes when user reports being in hyperfocus vs. regular focus.
        """
        hyperfocus_durations = []
        
        for sample in self.samples:
            if sample.actual_state == "hyperfocus":
                duration = sample.context.get('session_duration', 0)
                if duration > 0:
                    hyperfocus_durations.append(duration)
        
        if len(hyperfocus_durations) >= 3:
            # Use minimum observed hyperfocus duration
            min_duration = min(hyperfocus_durations)
            avg_duration = mean(hyperfocus_durations)
            
            # Set threshold at 80% of average, but not less than 30 min
            new_threshold = max(30, int(avg_duration * 0.8))
            
            self.personal_thresholds['hyperfocus_duration_min'] = new_threshold
            logger.info(f"🎯 Hyperfocus duration calibrated to {new_threshold} min")
    
    def _calibrate_scattered_sensitivity(self) -> None:
        """
        Calibrate sensitivity to scattered state based on context switch patterns.
        """
        scattered_switch_counts = []
        
        for sample in self.samples:
            if sample.actual_state == "scattered":
                switches = sample.context.get('recent_switches', 0)
                if switches > 0:
                    scattered_switch_counts.append(switches)
        
        if len(scattered_switch_counts) >= 3:
            # Use average switch count when user reports scattered
            avg_switches = mean(scattered_switch_counts)
            std_switches = stdev(scattered_switch_counts) if len(scattered_switch_counts) > 1 else 1
            
            # Set threshold at 1 std below average
            new_threshold = max(3, int(avg_switches - std_switches))
            
            self.personal_thresholds['scattered_switch_threshold'] = new_threshold
            logger.info(f"🎯 Scattered switch threshold calibrated to {new_threshold}")
    
    def _calibrate_feature_weights(self) -> None:
        """
        Calibrate feature weights based on which signals correlate with accurate predictions.
        
        Analyzes which context features (energy, complexity, switches) best predict
        user's actual attention state.
        """
        # Simple heuristic: analyze correlation between features and correct predictions
        # TODO: Could use more sophisticated feature importance analysis
        
        # For now, keep default weights
        # In production, could use logistic regression or similar
        pass
    
    def get_calibrated_prediction(
        self,
        raw_prediction: str,
        raw_confidence: float,
        context: Dict[str, Any]
    ) -> tuple[str, float]:
        """
        Apply calibrated thresholds to raw prediction.
        
        Args:
            raw_prediction: Initial prediction from model
            raw_confidence: Model's confidence
            context: Current context signals
        
        Returns:
            (calibrated_prediction, calibrated_confidence)
        """
        # Apply personalized confidence threshold
        threshold_key = f"{raw_prediction}_confidence"
        required_confidence = self.personal_thresholds.get(threshold_key, 0.7)
        
        if raw_confidence < required_confidence:
            # Not confident enough - default to "unknown"
            return ("unknown", raw_confidence)
        
        # Check hyperfocus duration threshold
        if raw_prediction == "hyperfocus":
            duration = context.get('session_duration', 0)
            min_duration = self.personal_thresholds['hyperfocus_duration_min']
            
            if duration < min_duration:
                # Too short for hyperfocus
                return ("focused", raw_confidence * 0.8)
        
        # Check scattered switch threshold
        if raw_prediction == "scattered":
            switches = context.get('recent_switches', 0)
            min_switches = self.personal_thresholds['scattered_switch_threshold']
            
            if switches < min_switches:
                # Not enough switches for scattered
                return ("focused", raw_confidence * 0.8)
        
        return (raw_prediction, raw_confidence)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get calibration statistics."""
        if not self.samples:
            return {"error": "No calibration data"}
        
        accuracy = self._calculate_accuracy_by_state()
        
        return {
            "total_samples": len(self.samples),
            "accuracy_by_state": accuracy,
            "overall_accuracy": sum(accuracy.values()) / len(accuracy) if accuracy else 0,
            "thresholds": self.personal_thresholds,
            "calibration_status": "good" if len(self.samples) >= 20 else "learning"
        }
