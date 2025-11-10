#!/usr/bin/env python3
"""
ML Predictive Engine for ADHD Accommodation

Implements machine learning models for forecasting cognitive load,
energy levels, and attention states to enable proactive ADHD accommodations.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import asyncio
from dataclasses import dataclass
from enum import Enum

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("PyTorch not available, using fallback predictions")

logger = logging.getLogger(__name__)


class PredictionModel(Enum):
    """Available prediction model types."""
    LSTM = "lstm"
    LINEAR = "linear"
    SIMPLE_AVERAGE = "simple_average"
    FALLBACK = "fallback"


@dataclass
class PredictionResult:
    """Container for prediction results."""
    predicted_value: float
    confidence: float
    horizon_hours: int
    model_used: str
    feature_importance: Dict[str, float]
    timestamp: datetime


@dataclass
class TrainingData:
    """Container for training data."""
    features: np.ndarray
    targets: np.ndarray
    timestamps: List[datetime]


class LSTMPredictor(nn.Module):
    """LSTM-based predictor for time series forecasting."""

    def __init__(self, input_size: int, hidden_size: int = 64, num_layers: int = 2):
        super(LSTMPredictor, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.2)
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)

        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out


class TimeSeriesDataset(Dataset):
    """Dataset for time series prediction."""

    def __init__(self, data: np.ndarray, targets: np.ndarray, sequence_length: int = 24):
        self.data = data
        self.targets = targets
        self.sequence_length = sequence_length

    def __len__(self):
        return len(self.data) - self.sequence_length

    def __getitem__(self, idx):
        x = self.data[idx:idx + self.sequence_length]
        y = self.targets[idx + self.sequence_length]
        return torch.tensor(x, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)


class CognitiveLoadPredictor:
    """
    Machine learning predictor for cognitive load forecasting.

    Uses historical data to predict future cognitive load levels,
    enabling proactive ADHD accommodations like break suggestions
    and task adjustments.
    """

    def __init__(self, model_type: PredictionModel = PredictionModel.LINEAR):
        self.model_type = model_type
        self.model = None
        self.is_trained = False
        self.training_history = []
        self.feature_cache = {}  # Cache for feature extraction
        self.cache_timestamp = {}  # Cache timestamps for invalidation

        # Model parameters
        self.sequence_length = 24  # 24 hours of historical data
        self.prediction_horizon = 1  # Predict 1 hour ahead
        self.confidence_threshold = 0.7
        self.max_cache_size = 1000  # Prevent unbounded memory growth

        logger.info(f"Initialized CognitiveLoadPredictor with {model_type.value} model")

    def _manage_cache_size(self):
        """Keep cache size under control to prevent memory leaks."""
        if len(self.feature_cache) > self.max_cache_size:
            # Remove oldest 20% of entries
            items_to_remove = int(self.max_cache_size * 0.2)
            sorted_items = sorted(self.cache_timestamp.items(),
                                key=lambda x: x[1])[:items_to_remove]
            for key, _ in sorted_items:
                del self.feature_cache[key]
                del self.cache_timestamp[key]

    def _extract_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Extract numerical features from input data with validation."""
        try:
            # Validate inputs
            energy = max(0.0, min(1.0, float(data.get('energy_level', 0.5))))
            attention = max(0.0, min(1.0, float(data.get('attention_state', 0.5))))
            complexity = max(0.0, min(1.0, float(data.get('task_complexity', 0.5))))
            time_of_day = max(0.0, min(1.0, float(data.get('time_of_day', 0.5))))
            day_of_week = max(0.0, min(1.0, float(data.get('day_of_week', 0.5))))

            # Handle optional features safely
            recent_breaks = min(10, max(0, int(data.get('recent_breaks', 0)))) / 10.0
            task_switches = min(10, max(0, int(data.get('task_switches', 0)))) / 5.0

            features = [
                energy, attention, complexity,
                time_of_day, day_of_week,
                recent_breaks, task_switches
            ]

            return np.array(features).reshape(1, -1)

        except (ValueError, TypeError) as e:
            logger.warning(f"Feature extraction failed, using defaults: {e}")
            # Return safe default features
            return np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.0, 0.0]).reshape(1, -1)

    async def train(self, training_data: TrainingData) -> bool:
        """
        Train the prediction model on historical cognitive load data.

        Args:
            training_data: Historical features, targets, and timestamps

        Returns:
            bool: True if training successful
        """
        try:
            if self.model_type == PredictionModel.LSTM and TORCH_AVAILABLE:
                await self._train_lstm(training_data)
            elif self.model_type == PredictionModel.LINEAR:
                await self._train_linear(training_data)
            else:
                await self._train_simple_average(training_data)

            self.is_trained = True
            logger.info(f"Successfully trained {self.model_type.value} model")
            return True

        except Exception as e:
            logger.error(f"Training failed: {e}")
            # Fallback to simple model
            await self._train_simple_average(training_data)
            return False

    async def _train_lstm(self, data: TrainingData):
        """Train LSTM model."""
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch not available")

        # Create dataset
        dataset = TimeSeriesDataset(data.features, data.targets, self.sequence_length)
        dataloader = DataLoader(dataset, batch_size=32, shuffle=True)

        # Initialize model
        input_size = data.features.shape[1]
        self.model = LSTMPredictor(input_size=input_size)

        # Training setup
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)

        # Train for a few epochs
        for epoch in range(10):
            total_loss = 0
            for inputs, targets in dataloader:
                optimizer.zero_grad()
                outputs = self.model(inputs)
                loss = criterion(outputs.squeeze(), targets)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()

            avg_loss = total_loss / len(dataloader)
            self.training_history.append(avg_loss)
            logger.debug(f"Epoch {epoch+1}, Loss: {avg_loss:.4f}")

    async def _train_linear(self, data: TrainingData):
        """Train simple linear regression model."""
        from sklearn.linear_model import LinearRegression

        # Use recent data for training
        recent_features = data.features[-self.sequence_length:]
        recent_targets = data.targets[-self.sequence_length:]

        self.model = LinearRegression()
        self.model.fit(recent_features, recent_targets)

    async def _train_simple_average(self, data: TrainingData):
        """Fallback: Simple moving average model."""
        # Calculate simple moving average
        recent_targets = data.targets[-self.sequence_length:]
        self.model = {
            'moving_average': np.mean(recent_targets),
            'recent_trend': recent_targets[-1] - recent_targets[0] if len(recent_targets) > 1 else 0
        }

    async def predict(self, current_data: Dict[str, Any], horizon_hours: int = 1) -> PredictionResult:
        """
        Predict future cognitive load.

        Args:
            current_data: Current features (energy, attention, task complexity, etc.)
            horizon_hours: How many hours ahead to predict

        Returns:
            PredictionResult with prediction and confidence
        """
        if not self.is_trained:
            return self._fallback_prediction(current_data, horizon_hours)

        try:
            features = self._extract_features(current_data)

            if self.model_type == PredictionModel.LSTM and TORCH_AVAILABLE:
                prediction = await self._predict_lstm(features, horizon_hours)
            elif self.model_type == PredictionModel.LINEAR:
                prediction = await self._predict_linear(features, horizon_hours)
            else:
                prediction = await self._predict_simple(features, horizon_hours)

            confidence = self._calculate_confidence(prediction, features)
            feature_importance = self._calculate_feature_importance(features)

            # Manage cache size to prevent memory leaks
            self._manage_cache_size()

            return PredictionResult(
                predicted_value=max(0.0, min(1.0, prediction)),  # Clamp to 0-1 range
                confidence=confidence,
                horizon_hours=horizon_hours,
                model_used=self.model_type.value,
                feature_importance=feature_importance,
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return self._fallback_prediction(current_data, horizon_hours)

    async def _predict_lstm(self, features: np.ndarray, horizon: int) -> float:
        """Make prediction using LSTM model."""
        if not TORCH_AVAILABLE or self.model is None:
            return np.mean(features)

        # Convert to tensor
        input_tensor = torch.tensor(features[-self.sequence_length:], dtype=torch.float32).unsqueeze(0)

        # Make prediction
        with torch.no_grad():
            output = self.model(input_tensor)
            return output.item()

    async def _predict_linear(self, features: np.ndarray, horizon: int) -> float:
        """Make prediction using linear regression."""
        if self.model is None:
            return np.mean(features)

        # Use current features for prediction
        return self.model.predict(features)[0]

    async def _predict_simple(self, features: np.ndarray, horizon: int) -> float:
        """Make prediction using simple average."""
        if self.model is None:
            return np.mean(features)

        base_value = self.model.get('moving_average', 0.5)
        trend = self.model.get('recent_trend', 0)

        # Apply trend adjustment
        adjustment = (trend * horizon) / 24.0  # Scale trend by horizon
        return max(0.0, min(1.0, base_value + adjustment))

    def _fallback_prediction(self, current_data: Dict[str, Any], horizon: int) -> PredictionResult:
        """Fallback prediction when model fails."""
        # Use current energy as baseline prediction
        current_energy = current_data.get('energy_level', 0.5)
        prediction = max(0.0, min(1.0, current_energy))

        return PredictionResult(
            predicted_value=prediction,
            confidence=0.3,  # Low confidence for fallback
            horizon_hours=horizon,
            model_used="fallback",
            feature_importance={"current_energy": 1.0},
            timestamp=datetime.now()
        )

    def _extract_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Extract numerical features from input data."""
        features = [
            data.get('energy_level', 0.5),
            data.get('attention_state', 0.5),
            data.get('task_complexity', 0.5),
            data.get('time_of_day', datetime.now().hour / 24.0),
            data.get('day_of_week', datetime.now().weekday() / 7.0),
            data.get('recent_breaks', 0) / 10.0,  # Normalize
            data.get('task_switches', 0) / 5.0,   # Normalize
        ]
        return np.array(features).reshape(1, -1)

    def _calculate_confidence(self, prediction: float, features: np.ndarray) -> float:
        """Calculate prediction confidence."""
        # Base confidence on model training history
        if hasattr(self, 'training_history') and self.training_history:
            recent_loss = self.training_history[-1]
            # Convert loss to confidence (lower loss = higher confidence)
            confidence = max(0.1, min(1.0, 1.0 - recent_loss))
        else:
            confidence = 0.5  # Default confidence

        # Adjust based on data quality
        data_variance = np.var(features)
        if data_variance < 0.1:  # Low variance = more predictable
            confidence += 0.2

        return min(1.0, confidence)

    def _calculate_feature_importance(self, features: np.ndarray) -> Dict[str, float]:
        """Calculate feature importance for interpretability."""
        feature_names = ['energy_level', 'attention_state', 'task_complexity',
                        'time_of_day', 'day_of_week', 'recent_breaks', 'task_switches']

        # Simple importance based on feature values (higher values = more important)
        total = np.sum(np.abs(features))
        if total == 0:
            return {name: 1.0/len(feature_names) for name in feature_names}

        importance = {}
        for i, name in enumerate(feature_names):
            importance[name] = abs(features[0][i]) / total

        return importance

    async def update_with_feedback(self, actual_value: float, predicted_value: float):
        """
        Update model with actual vs predicted feedback for continuous learning.

        Args:
            actual_value: Actual cognitive load measured
            predicted_value: Model prediction
        """
        error = abs(actual_value - predicted_value)
        logger.info(f"Prediction error: {error:.3f}")

        # In a real implementation, this would trigger model retraining
        # For now, just log the feedback
        self.training_history.append(error)