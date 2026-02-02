"""
ML-Based Energy Pattern Learning

Predicts energy levels based on historical data using sklearn RandomForest.
Learns user-specific patterns:
- Time of day patterns
- Activity patterns  
- Day of week trends
- Time since last break
- Recent complexity patterns

ADHD Benefit: Proactive energy management, optimize scheduling
"""
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import pickle
import os

logger = logging.getLogger(__name__)


@dataclass
class EnergyPrediction:
    """Energy prediction result with confidence and contributing factors."""
    predicted_level: str  # "high", "medium", "low", "very_low"
    confidence: float  # 0.0-1.0
    contributing_factors: List[str]  # Top factors influencing prediction
    recommendation: str  # Actionable recommendation
    timestamp: datetime = field(default_factory=datetime.now)


class EnergyPatternPredictor:
    """
    Learn and predict energy patterns from historical data.
    
    Uses RandomForest for multi-class classification of energy levels.
    Features engineered from temporal patterns and cognitive load.
    """
    
    def __init__(self, user_id: str, model_path: Optional[str] = None):
        """
        Initialize energy pattern predictor.
        
        Args:
            user_id: User identifier for personalized model
            model_path: Optional path to saved model (default: .models/<user_id>_energy_model.pkl)
        """
        self.user_id = user_id
        self.model: Optional[RandomForestClassifier] = None
        self.scaler: Optional[StandardScaler] = None
        
        # Feature engineering configuration
        self.feature_names = [
            "hour_of_day",          # 0-23
            "day_of_week",          # 0-6 (Monday=0)
            "minutes_since_break",  # Continuous
            "session_duration",     # Minutes in current session
            "complexity_avg_30min", # Average complexity last 30min
            "is_morning",           # Boolean (before 12pm)
            "is_afternoon",         # Boolean (12pm-5pm)
            "is_evening",           # Boolean (after 5pm)
            "recent_break_count",   # Number of breaks in last 2 hours
        ]
        
        # Model persistence
        if model_path is None:
            os.makedirs(".models", exist_ok=True)
            model_path = f".models/{user_id}_energy_model.pkl"
        self.model_path = model_path
        
        # Try loading existing model
        self._load_model()
    
    def _load_model(self) -> bool:
        """Load saved model if exists."""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data['model']
                    self.scaler = data['scaler']
                logger.info(f"✅ Loaded energy model for {self.user_id}")
                return True
        except Exception as e:
            logger.warning(f"Failed to load model: {e}")
        return False
    
    def _save_model(self) -> bool:
        """Save trained model."""
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'scaler': self.scaler,
                    'user_id': self.user_id,
                    'trained_at': datetime.now().isoformat()
                }, f)
            logger.info(f"✅ Saved energy model for {self.user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return False
    
    def _extract_features(self, observation: Dict[str, Any]) -> np.ndarray:
        """
        Extract features from observation.
        
        Args:
            observation: Dict with keys matching feature requirements
        
        Returns:
            Feature vector as numpy array
        """
        timestamp = observation.get('timestamp', datetime.now())
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        hour = timestamp.hour
        day_of_week = timestamp.weekday()
        
        features = [
            hour,
            day_of_week,
            observation.get('minutes_since_break', 30),
            observation.get('session_duration', 15),
            observation.get('complexity_avg_30min', 0.5),
            1 if hour < 12 else 0,  # is_morning
            1 if 12 <= hour < 17 else 0,  # is_afternoon
            1 if hour >= 17 else 0,  # is_evening
            observation.get('recent_break_count', 0),
        ]
        
        return np.array(features).reshape(1, -1)
    
    def train(self, historical_data: List[Dict[str, Any]]) -> float:
        """
        Train model on historical energy observations.
        
        Args:
            historical_data: List of observations with features + 'energy_level' label
        
        Returns:
            Training accuracy (0.0-1.0)
        """
        if len(historical_data) < 10:
            logger.warning(f"Insufficient data for training: {len(historical_data)} samples")
            return 0.0
        
        try:
            # Extract features and labels
            X = []
            y = []
            for obs in historical_data:
                X.append(self._extract_features(obs).flatten())
                y.append(obs['energy_level'])
            
            X = np.array(X)
            y = np.array(y)
            
            # Normalize features
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            # Train RandomForest
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            )
            self.model.fit(X_scaled, y)
            
            # Calculate accuracy
            accuracy = self.model.score(X_scaled, y)
            
            # Save model
            self._save_model()
            
            logger.info(f"✅ Trained energy model: {len(historical_data)} samples, {accuracy:.2%} accuracy")
            return accuracy
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return 0.0
    
    def predict(self, current_state: Dict[str, Any]) -> EnergyPrediction:
        """
        Predict energy level for current context.
        
        Args:
            current_state: Dict with feature values for current moment
        
        Returns:
            EnergyPrediction with level, confidence, and recommendations
        """
        # Fallback if model not trained
        if self.model is None or self.scaler is None:
            return EnergyPrediction(
                predicted_level="medium",
                confidence=0.3,
                contributing_factors=["Model not trained - using default"],
                recommendation="Gather more historical data to enable predictions"
            )
        
        try:
            # Extract and scale features
            X = self._extract_features(current_state)
            X_scaled = self.scaler.transform(X)
            
            # Predict
            predicted_level = self.model.predict(X_scaled)[0]
            probabilities = self.model.predict_proba(X_scaled)[0]
            confidence = float(max(probabilities))
            
            # Get feature importance
            feature_importance = self.model.feature_importances_
            top_factors = sorted(
                zip(self.feature_names, feature_importance),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            contributing_factors = [f"{name} ({importance:.2f})" for name, importance in top_factors]
            
            # Generate recommendation
            recommendation = self._generate_recommendation(predicted_level, confidence, current_state)
            
            return EnergyPrediction(
                predicted_level=predicted_level,
                confidence=confidence,
                contributing_factors=contributing_factors,
                recommendation=recommendation
            )
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return EnergyPrediction(
                predicted_level="medium",
                confidence=0.1,
                contributing_factors=[f"Prediction error: {e}"],
                recommendation="Using fallback energy level"
            )
    
    def _generate_recommendation(
        self,
        predicted_level: str,
        confidence: float,
        current_state: Dict[str, Any]
    ) -> str:
        """Generate actionable recommendation based on prediction."""
        timestamp = current_state.get('timestamp', datetime.now())
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        hour = timestamp.hour
        
        if predicted_level == "high":
            return "Great time for complex tasks like architecture design or difficult debugging"
        elif predicted_level == "medium":
            return "Good for moderate tasks: feature implementation, code review, refactoring"
        elif predicted_level == "low":
            if hour < 14:
                return "Energy dip detected - consider coffee break and lighter tasks (testing, docs)"
            else:
                return "Afternoon slump - switch to simple tasks or take a longer break"
        else:  # very_low
            return "⚠️ Very low energy - strongly recommend break or end session"
    
    def get_peak_hours(self, historical_data: List[Dict[str, Any]]) -> List[int]:
        """
        Identify user's peak energy hours from historical data.
        
        Args:
            historical_data: List of historical observations
        
        Returns:
            List of hours (0-23) ranked by average energy
        """
        hour_energy = {}
        for obs in historical_data:
            timestamp = obs.get('timestamp', datetime.now())
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            
            hour = timestamp.hour
            energy = obs.get('energy_level', 'medium')
            
            # Convert to numeric score
            energy_score = {
                'very_low': 1,
                'low': 2,
                'medium': 3,
                'high': 4
            }.get(energy, 2)
            
            if hour not in hour_energy:
                hour_energy[hour] = []
            hour_energy[hour].append(energy_score)
        
        # Calculate average energy per hour
        hour_avg = {h: np.mean(scores) for h, scores in hour_energy.items()}
        
        # Sort by average energy (descending)
        peak_hours = sorted(hour_avg.keys(), key=lambda h: hour_avg[h], reverse=True)
        
        return peak_hours
