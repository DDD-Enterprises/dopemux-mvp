import pytest
from datetime import datetime, timedelta
import numpy as np
import os
import shutil
from services.adhd_engine.ml.energy_predictor import EnergyPatternPredictor, EnergyPrediction

class TestEnergyPatternPredictor:
    @pytest.fixture
    def temp_model_dir(self):
        """Create a temporary directory for model storage."""
        path = ".test_models"
        os.makedirs(path, exist_ok=True)
        yield path
        if os.path.exists(path):
            shutil.rmtree(path)

    @pytest.fixture
    def predictor(self, temp_model_dir):
        """Create a predictor instance."""
        return EnergyPatternPredictor(
            user_id="test_user",
            model_path=f"{temp_model_dir}/test_model.pkl"
        )

    def test_initialization(self, predictor):
        """Test that predictor initializes correctly."""
        assert predictor.user_id == "test_user"
        assert predictor.model is None
        assert predictor.scaler is None

    def test_feature_extraction(self, predictor):
        """Test feature extraction logic."""
        now = datetime.now()
        obs = {
            "timestamp": now.isoformat(),
            "minutes_since_break": 45,
            "session_duration": 60,
            "complexity_avg_30min": 0.8,
            "recent_break_count": 1
        }
        features = predictor._extract_features(obs)
        assert features.shape == (1, 9)  # 9 features defined in class

    def test_training_insufficient_data(self, predictor):
        """Test training with not enough data."""
        data = [{"energy_level": "high"}] * 5
        accuracy = predictor.train(data)
        assert accuracy == 0.0
        assert predictor.model is None

    def test_training_and_prediction_flow(self, predictor):
        """Test full flow: train -> predict."""
        # Generate mock training data
        processed_data = []
        base_time = datetime.now()
        
        # Create patterns: 
        # Morning + fresh = high energy
        # Evening + long session = low energy
        
        # 10 Morning samples (high energy)
        for i in range(10):
            processed_data.append({
                "timestamp": (base_time.replace(hour=9) + timedelta(minutes=i*10)).isoformat(),
                "minutes_since_break": 10,
                "session_duration": 20,
                "complexity_avg_30min": 0.5,
                "recent_break_count": 0,
                "energy_level": "high"
            })
            
        # 10 Evening samples (low energy)
        for i in range(10):
            processed_data.append({
                "timestamp": (base_time.replace(hour=19) + timedelta(minutes=i*10)).isoformat(),
                "minutes_since_break": 120,
                "session_duration": 180,
                "complexity_avg_30min": 0.2,
                "recent_break_count": 0,
                "energy_level": "low"
            })

        # Train
        accuracy = predictor.train(processed_data)
        assert accuracy > 0.0
        assert predictor.model is not None
        assert predictor.scaler is not None

        # Predict - Morning case
        morning_state = {
            "timestamp": base_time.replace(hour=9, minute=30).isoformat(),
            "minutes_since_break": 15,
            "session_duration": 25,
            "complexity_avg_30min": 0.5,
            "recent_break_count": 0
        }
        prediction = predictor.predict(morning_state)
        assert isinstance(prediction, EnergyPrediction)
        assert prediction.predicted_level == "high"
        assert prediction.confidence > 0.5

        # Predict - Evening case
        evening_state = {
            "timestamp": base_time.replace(hour=19, minute=30).isoformat(),
            "minutes_since_break": 130,
            "session_duration": 190,
            "complexity_avg_30min": 0.2,
            "recent_break_count": 0
        }
        prediction_ev = predictor.predict(evening_state)
        assert prediction_ev.predicted_level == "low"

    def test_predict_without_model(self, predictor):
        """Test prediction behavior when model isn't trained."""
        prediction = predictor.predict({})
        assert prediction.predicted_level == "medium"  # Fallback
        assert "Model not trained" in prediction.contributing_factors[0]

    def test_model_persistence(self, temp_model_dir):
        """Test saving and loading the model."""
        # 1. Train and save
        predictor1 = EnergyPatternPredictor("user1", f"{temp_model_dir}/persist.pkl")
        data = []
        for i in range(15):
            data.append({
                "timestamp": datetime.now().isoformat(),
                "energy_level": "high"
            })
        predictor1.train(data)
        
        # 2. Load in new instance
        predictor2 = EnergyPatternPredictor("user1", f"{temp_model_dir}/persist.pkl")
        assert predictor2.model is not None
        assert predictor2.scaler is not None
