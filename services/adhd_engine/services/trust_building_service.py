"""
Trust Building Service - Phase 3.6

Builds user trust in ML predictions through accuracy tracking, feedback integration,
and gradual automation adoption. Provides visualization of prediction performance
and adjusts system behavior based on user confidence levels.

Features:
- Prediction accuracy tracking (predictions vs actual outcomes)
- User feedback collection and analysis
- Trust score calculation per prediction type
- Gradual automation adoption based on trust levels
- Visualization endpoints for accuracy metrics
- Confidence threshold adjustment based on user behavior
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict

import redis.asyncio as redis

from ..models import EnergyLevel, AttentionState
from ..config import settings

logger = logging.getLogger(__name__)

class TrustBuildingService:
    """
    Service for building and maintaining user trust in AI predictions.

    Tracks prediction accuracy, collects user feedback, and adjusts automation
    levels to ensure users feel in control while benefiting from AI assistance.
    """

    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.redis_client: Optional[redis.Redis] = None

        # Trust tracking
        self.prediction_accuracy: Dict[str, List[Dict]] = defaultdict(list)  # prediction_type -> accuracy records
        self.user_feedback: Dict[str, List[Dict]] = defaultdict(list)  # user_id -> feedback records
        self.trust_scores: Dict[str, float] = {}  # prediction_type -> trust score (0-1)
        self.automation_levels: Dict[str, str] = {}  # prediction_type -> automation level

        # Configuration
        self.accuracy_window_days = 30  # Track accuracy over last 30 days
        self.min_feedback_samples = 10  # Minimum feedback samples for trust calculation
        self.feedback_decay_factor = 0.8  # How much older feedback matters

    async def initialize(self) -> None:
        """Initialize trust building service."""
        logger.info("🤝 Initializing Trust Building Service (Phase 3.6)")

        # Connect to Redis
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)

        # Load existing trust data
        await self._load_trust_data()

        logger.info("✅ Trust Building Service ready")

    async def record_prediction_outcome(
        self,
        user_id: str,
        prediction_type: str,
        predicted_value: Any,
        actual_value: Any,
        confidence: float,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Record the outcome of a prediction for accuracy tracking."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # Determine if prediction was accurate
        accuracy = self._calculate_prediction_accuracy(predicted_value, actual_value)

        # Create accuracy record
        record = {
            "user_id": user_id,
            "prediction_type": prediction_type,
            "predicted_value": predicted_value,
            "actual_value": actual_value,
            "confidence": confidence,
            "accuracy": accuracy,
            "timestamp": timestamp.isoformat()
        }

        # Store in Redis
        key = f"adhd:prediction_accuracy:{prediction_type}:{user_id}"
        await self.redis_client.lpush(key, json.dumps(record))

        # Keep only recent records (last 30 days)
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.accuracy_window_days)
        cutoff_iso = cutoff.isoformat()

        # Remove old records (this is simplified - in production, use a more efficient approach)
        all_records = await self.redis_client.lrange(key, 0, -1)
        recent_records = [
            rec for rec in all_records
            if json.loads(rec)["timestamp"] > cutoff_iso
        ]

        # Clear and repopulate (not ideal for production, but works for demo)
        await self.redis_client.delete(key)
        if recent_records:
            await self.redis_client.rpush(key, *recent_records)

        # Update trust scores
        await self._update_trust_score(prediction_type)

        logger.debug(f"📊 Recorded prediction outcome: {prediction_type} accuracy={accuracy:.2f}")

    async def collect_user_feedback(
        self,
        user_id: str,
        prediction_type: str,
        prediction_id: str,
        rating: int,  # 1-5 stars
        usefulness: str,  # "very_useful", "somewhat_useful", "neutral", "not_useful", "harmful"
        comments: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Collect user feedback on prediction usefulness."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # Create feedback record
        feedback = {
            "user_id": user_id,
            "prediction_type": prediction_type,
            "prediction_id": prediction_id,
            "rating": rating,
            "usefulness": usefulness,
            "comments": comments,
            "timestamp": timestamp.isoformat()
        }

        # Store in Redis
        key = f"adhd:user_feedback:{user_id}"
        await self.redis_client.lpush(key, json.dumps(feedback))

        # Keep only recent feedback (last 90 days for trend analysis)
        cutoff = datetime.now(timezone.utc) - timedelta(days=90)
        cutoff_iso = cutoff.isoformat()

        all_feedback = await self.redis_client.lrange(key, 0, -1)
        recent_feedback = [
            fb for fb in all_feedback
            if json.loads(fb)["timestamp"] > cutoff_iso
        ]

        await self.redis_client.delete(key)
        if recent_feedback:
            await self.redis_client.rpush(key, *recent_feedback)

        # Update trust scores based on feedback
        await self._update_trust_score_from_feedback(prediction_type, user_id)

        logger.info(f"💬 Collected feedback for {user_id}: {prediction_type} rating={rating}")

    async def get_trust_metrics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get trust metrics for visualization."""
        metrics = {
            "overall_trust_score": sum(self.trust_scores.values()) / len(self.trust_scores) if self.trust_scores else 0.5,
            "prediction_types": {},
            "feedback_summary": await self._get_feedback_summary(user_id),
            "accuracy_trends": {},
            "automation_levels": self.automation_levels.copy(),
            "recommendations": self._generate_trust_recommendations()
        }

        # Add per-prediction-type metrics
        for pred_type in ["energy", "attention", "break"]:
            metrics["prediction_types"][pred_type] = {
                "trust_score": self.trust_scores.get(pred_type, 0.5),
                "accuracy_rate": await self._get_accuracy_rate(pred_type, user_id),
                "feedback_count": await self._get_feedback_count(pred_type, user_id),
                "automation_level": self.automation_levels.get(pred_type, "minimal")
            }

            # Accuracy trends (simplified - last 7 days vs previous 7 days)
            metrics["accuracy_trends"][pred_type] = await self._get_accuracy_trend(pred_type, user_id)

        return metrics

    async def get_visualization_data(self, user_id: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
        """Get data for trust visualization dashboards."""
        data = {
            "accuracy_over_time": {},
            "feedback_distribution": {},
            "trust_score_progression": {},
            "automation_level_changes": [],
            "prediction_success_stories": []
        }

        # Get accuracy data over time
        for pred_type in ["energy", "attention", "break"]:
            data["accuracy_over_time"][pred_type] = await self._get_accuracy_over_time(pred_type, user_id, days)

        # Get feedback distribution
        data["feedback_distribution"] = await self._get_feedback_distribution(user_id)

        # Get trust score progression
        data["trust_score_progression"] = await self._get_trust_score_progression(user_id, days)

        # Get automation level changes
        data["automation_level_changes"] = await self._get_automation_changes(user_id, days)

        # Get success stories
        data["prediction_success_stories"] = await self._get_success_stories(user_id)

        return data

    async def adjust_automation_level(
        self,
        prediction_type: str,
        user_id: str,
        new_level: str
    ) -> bool:
        """Manually adjust automation level for a prediction type."""
        valid_levels = ["minimal", "balanced", "proactive"]
        if new_level not in valid_levels:
            return False

        self.automation_levels[prediction_type] = new_level

        # Store in Redis
        key = f"adhd:automation_levels:{user_id}"
        levels_data = {k: v for k, v in self.automation_levels.items()}
        await self.redis_client.setex(key, 86400, json.dumps(levels_data))  # 24 hours

        logger.info(f"🔧 Adjusted automation level for {prediction_type} to {new_level}")
        return True

    # Internal methods

    def _calculate_prediction_accuracy(self, predicted: Any, actual: Any) -> float:
        """Calculate accuracy score for a prediction (0.0-1.0)."""
        try:
            # For categorical predictions (energy, attention states)
            if isinstance(predicted, str) and isinstance(actual, str):
                return 1.0 if predicted.lower() == actual.lower() else 0.0

            # For numerical predictions (break timing)
            if isinstance(predicted, (int, float)) and isinstance(actual, (int, float)):
                diff = abs(predicted - actual)
                max_diff = max(abs(predicted), abs(actual), 1)  # Avoid division by zero
                return max(0.0, 1.0 - (diff / max_diff))

            # Default: assume correct if values are equal
            return 1.0 if predicted == actual else 0.0

        except Exception as e:
            return 0.0  # Error in calculation

            logger.error(f"Error: {e}")
    async def _update_trust_score(self, prediction_type: str) -> None:
        """Update trust score based on recent accuracy data."""
        accuracy_records = await self._get_accuracy_records(prediction_type, limit=50)

        if len(accuracy_records) < self.min_feedback_samples:
            self.trust_scores[prediction_type] = 0.5  # Default neutral trust
            return

        # Calculate weighted accuracy (recent predictions matter more)
        total_weight = 0
        weighted_accuracy = 0

        for i, record in enumerate(accuracy_records):
            weight = self.feedback_decay_factor ** i  # Exponential decay
            weighted_accuracy += record["accuracy"] * weight
            total_weight += weight

        trust_score = weighted_accuracy / total_weight if total_weight > 0 else 0.5
        self.trust_scores[prediction_type] = min(1.0, max(0.0, trust_score))

        # Adjust automation level based on trust score
        await self._adjust_automation_based_on_trust(prediction_type, trust_score)

    async def _update_trust_score_from_feedback(self, prediction_type: str, user_id: str) -> None:
        """Update trust score based on user feedback."""
        feedback_records = await self._get_feedback_records(prediction_type, user_id, limit=20)

        if not feedback_records:
            return

        # Calculate average rating (1-5 scale converted to 0-1)
        ratings = [record["rating"] for record in feedback_records]
        avg_rating = sum(ratings) / len(ratings)
        feedback_trust = (avg_rating - 1) / 4  # Convert 1-5 to 0-1

        # Combine with accuracy-based trust
        accuracy_trust = self.trust_scores.get(prediction_type, 0.5)
        combined_trust = (accuracy_trust * 0.7) + (feedback_trust * 0.3)

        self.trust_scores[prediction_type] = combined_trust

    async def _adjust_automation_based_on_trust(self, prediction_type: str, trust_score: float) -> None:
        """Adjust automation level based on trust score."""
        if trust_score >= 0.8:
            level = "proactive"
        elif trust_score >= 0.6:
            level = "balanced"
        else:
            level = "minimal"

        self.automation_levels[prediction_type] = level

    async def _get_accuracy_records(self, prediction_type: str, limit: int = 100) -> List[Dict]:
        """Get recent accuracy records for a prediction type."""
        pattern = f"adhd:prediction_accuracy:{prediction_type}:*"
        keys = await self.redis_client.keys(pattern)

        all_records = []
        for key in keys:
            records = await self.redis_client.lrange(key, 0, limit - 1)
            for record_json in records:
                try:
                    record = json.loads(record_json)
                    all_records.append(record)
                except json.JSONDecodeError:
                    continue

        # Sort by timestamp, most recent first
        all_records.sort(key=lambda x: x["timestamp"], reverse=True)
        return all_records[:limit]

    async def _get_feedback_records(self, prediction_type: str, user_id: str, limit: int = 50) -> List[Dict]:
        """Get feedback records for a prediction type and user."""
        key = f"adhd:user_feedback:{user_id}"
        records = await self.redis_client.lrange(key, 0, limit - 1)

        feedback_records = []
        for record_json in records:
            try:
                record = json.loads(record_json)
                if record.get("prediction_type") == prediction_type:
                    feedback_records.append(record)
            except json.JSONDecodeError:
                continue

        return feedback_records

    async def _get_accuracy_rate(self, prediction_type: str, user_id: Optional[str] = None) -> float:
        """Get overall accuracy rate for a prediction type."""
        records = await self._get_accuracy_records(prediction_type, limit=100)

        if user_id:
            records = [r for r in records if r["user_id"] == user_id]

        if not records:
            return 0.0

        accuracies = [r["accuracy"] for r in records]
        return sum(accuracies) / len(accuracies)

    async def _get_feedback_count(self, prediction_type: str, user_id: Optional[str] = None) -> int:
        """Get count of feedback records."""
        records = await self._get_feedback_records(prediction_type, user_id or "*", limit=1000)
        return len(records)

    async def _get_accuracy_trend(self, prediction_type: str, user_id: Optional[str] = None) -> Dict[str, float]:
        """Get accuracy trend (recent vs older)."""
        records = await self._get_accuracy_records(prediction_type, limit=200)

        if user_id:
            records = [r for r in records if r["user_id"] == user_id]

        if len(records) < 20:
            return {"trend": 0.0, "recent_accuracy": 0.0, "older_accuracy": 0.0}

        # Split into recent (first half) and older (second half)
        midpoint = len(records) // 2
        recent_records = records[:midpoint]
        older_records = records[midpoint:]

        recent_accuracy = sum(r["accuracy"] for r in recent_records) / len(recent_records)
        older_accuracy = sum(r["accuracy"] for r in older_records) / len(older_records)

        trend = recent_accuracy - older_accuracy

        return {
            "trend": trend,
            "recent_accuracy": recent_accuracy,
            "older_accuracy": older_accuracy
        }

    async def _get_accuracy_over_time(self, prediction_type: str, user_id: Optional[str] = None, days: int = 30) -> List[Dict]:
        """Get accuracy data over time for visualization."""
        # Simplified: return daily accuracy averages
        records = await self._get_accuracy_records(prediction_type, limit=1000)

        if user_id:
            records = [r for r in records if r["user_id"] == user_id]

        # Group by day
        daily_accuracy = defaultdict(list)

        for record in records:
            date = record["timestamp"][:10]  # YYYY-MM-DD
            daily_accuracy[date].append(record["accuracy"])

        # Calculate daily averages
        result = []
        for date in sorted(daily_accuracy.keys())[-days:]:  # Last N days
            accuracies = daily_accuracy[date]
            avg_accuracy = sum(accuracies) / len(accuracies)
            result.append({
                "date": date,
                "accuracy": avg_accuracy,
                "sample_count": len(accuracies)
            })

        return result

    async def _get_feedback_summary(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of user feedback."""
        if user_id:
            key = f"adhd:user_feedback:{user_id}"
            records = await self.redis_client.lrange(key, 0, -1)
        else:
            # Get all feedback (simplified - in production, aggregate across users)
            pattern = "adhd:user_feedback:*"
            keys = await self.redis_client.keys(pattern)
            records = []
            for key in keys[:10]:  # Limit to avoid excessive computation
                user_records = await self.redis_client.lrange(key, 0, 100)
                records.extend(user_records)

        if not records:
            return {"total_feedback": 0, "average_rating": 0.0, "distribution": {}}

        ratings = []
        usefulness_counts = defaultdict(int)

        for record_json in records:
            try:
                record = json.loads(record_json)
                ratings.append(record["rating"])
                usefulness_counts[record["usefulness"]] += 1
            except (json.JSONDecodeError, KeyError):
                continue

        return {
            "total_feedback": len(ratings),
            "average_rating": sum(ratings) / len(ratings) if ratings else 0.0,
            "distribution": dict(usefulness_counts)
        }

    async def _get_feedback_distribution(self, user_id: Optional[str] = None) -> Dict[str, int]:
        """Get feedback usefulness distribution."""
        summary = await self._get_feedback_summary(user_id)
        return summary.get("distribution", {})

    async def _get_trust_score_progression(self, user_id: Optional[str] = None, days: int = 30) -> List[Dict]:
        """Get trust score progression over time."""
        # Simplified: return current trust scores with timestamps
        # In production, store historical trust scores
        current_scores = []
        for pred_type, score in self.trust_scores.items():
            current_scores.append({
                "prediction_type": pred_type,
                "trust_score": score,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        return current_scores

    async def _get_automation_changes(self, user_id: Optional[str] = None, days: int = 30) -> List[Dict]:
        """Get automation level change history."""
        # Simplified: return current automation levels
        changes = []
        for pred_type, level in self.automation_levels.items():
            changes.append({
                "prediction_type": pred_type,
                "automation_level": level,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "reason": "trust_score_adjustment"
            })

        return changes

    async def _get_success_stories(self, user_id: Optional[str] = None) -> List[Dict]:
        """Get examples of successful predictions."""
        # Find high-accuracy predictions with positive feedback
        success_stories = []

        for pred_type in ["energy", "attention", "break"]:
            records = await self._get_accuracy_records(pred_type, limit=50)

            if user_id:
                records = [r for r in records if r["user_id"] == user_id]

            for record in records:
                if record["accuracy"] >= 0.9 and record["confidence"] >= 0.8:
                    success_stories.append({
                        "prediction_type": pred_type,
                        "predicted_value": record["predicted_value"],
                        "actual_value": record["actual_value"],
                        "confidence": record["confidence"],
                        "accuracy": record["accuracy"],
                        "user_id": record["user_id"],
                        "timestamp": record["timestamp"]
                    })

                    if len(success_stories) >= 5:  # Limit to 5 stories
                        break

            if len(success_stories) >= 5:
                break

        return success_stories

    def _generate_trust_recommendations(self) -> List[str]:
        """Generate recommendations for improving trust."""
        recommendations = []

        # Check trust scores
        low_trust_types = [pt for pt, score in self.trust_scores.items() if score < 0.6]
        if low_trust_types:
            recommendations.append(f"Consider providing more training data for: {', '.join(low_trust_types)}")

        # Check feedback counts
        low_feedback_types = []
        for pred_type in ["energy", "attention", "break"]:
            feedback_count = len(self.user_feedback.get(pred_type, []))
            if feedback_count < self.min_feedback_samples:
                low_feedback_types.append(pred_type)

        if low_feedback_types:
            recommendations.append(f"Collect more user feedback for: {', '.join(low_feedback_types)}")

        # General recommendations
        if not recommendations:
            recommendations.append("System trust levels are healthy - continue monitoring")

        return recommendations

    async def _load_trust_data(self) -> None:
        """Load existing trust data from Redis."""
        try:
            # Load automation levels
            pattern = "adhd:automation_levels:*"
            keys = await self.redis_client.keys(pattern)

            for key in keys:
                levels_data = await self.redis_client.get(key)
                if levels_data:
                    self.automation_levels.update(json.loads(levels_data))

        except Exception as e:
            logger.warning(f"Failed to load trust data: {e}")

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.redis_client:
            await self.redis_client.close()


# Global service instance
_trust_service: Optional[TrustBuildingService] = None


async def get_trust_building_service(workspace_id: str = settings.workspace_id) -> TrustBuildingService:
    """Get or create global trust building service instance."""
    global _trust_service

    if _trust_service is None:
        _trust_service = TrustBuildingService(workspace_id)
        await _trust_service.initialize()

    return _trust_service