import pytest
from datetime import datetime
import os
import shutil
import json
from services.adhd_engine.attention_calibrator import AttentionCalibrator, CalibrationSample

class TestAttentionCalibrator:
    @pytest.fixture
    def temp_storage(self):
        path = ".test_calibration"
        if os.path.exists(path):
            shutil.rmtree(path)
        os.makedirs(path)
        yield path
        if os.path.exists(path):
            shutil.rmtree(path)

    @pytest.fixture
    def calibrator(self, temp_storage):
        return AttentionCalibrator(
            user_id="test_user",
            storage_path=temp_storage
        )

    def test_record_feedback(self, calibrator):
        """Test recording user feedback."""
        calibrator.record_feedback(
            predicted="focused",
            actual="scattered",
            context={"switches": 5},
            confidence=0.8
        )
        
        assert len(calibrator.samples) == 1
        assert calibrator.samples[0].predicted_state == "focused"
        assert calibrator.samples[0].actual_state == "scattered"
        
        # Verify persistence
        saved_file = f"{calibrator.storage_path}/test_user_calibration.json"
        assert os.path.exists(saved_file)

    def test_calibration_logic(self, calibrator):
        """Test that calibration adjusts thresholds."""
        # Simulate consistent misclassification:
        # Model predicts 'focused' but user is 'scattered'
        # This should cause the 'focused_confidence' threshold to INCREASE (be more conservative)
        
        initial_threshold = calibrator.personal_thresholds.get("focused_confidence", 0.7)
        
        # Add 10 samples of false positives
        for _ in range(10):
            calibrator.samples.append(CalibrationSample(
                predicted_state="focused",
                actual_state="scattered",
                timestamp=datetime.now(),
                context={},
                confidence=0.6
            ))
            
        calibrator.calibrate()
        
        new_threshold = calibrator.personal_thresholds.get("focused_confidence")
        assert new_threshold > initial_threshold

    def test_get_calibrated_prediction(self, calibrator):
        """Test applying calibrated thresholds."""
        # Set a high threshold for "focused"
        calibrator.personal_thresholds["focused_confidence"] = 0.9
        
        # Raw prediction is "focused" with 0.8 confidence
        # Should be downgraded to "unknown" because 0.8 < 0.9
        pred, conf = calibrator.get_calibrated_prediction("focused", 0.8, {})
        assert pred == "unknown"
        
        # Raw prediction "focused" with 0.95 confidence
        # Should pass
        pred, conf = calibrator.get_calibrated_prediction("focused", 0.95, {})
        assert pred == "focused"

    def test_hyperfocus_calibration(self, calibrator):
        """Test calibration of hyperfocus duration."""
        calibrator.samples = [
            CalibrationSample(
                predicted_state="hyperfocus",
                actual_state="hyperfocus",
                timestamp=datetime.now(),
                context={"session_duration": 60}, # 60 min duration
                confidence=0.9
            ) for _ in range(5)
        ]
        
        calibrator.calibrate()
        
        # Threshold should be around 80% of 60 = 48
        threshold = calibrator.personal_thresholds["hyperfocus_duration_min"]
        assert 40 <= threshold <= 55

    def test_get_statistics(self, calibrator):
        """Test stats generation."""
        calibrator.record_feedback("focused", "focused", {}, 0.9)
        stats = calibrator.get_statistics()
        
        assert stats["total_samples"] == 1
        assert stats["accuracy_by_state"]["focused"] == 1.0
