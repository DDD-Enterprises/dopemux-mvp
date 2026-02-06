"""Trust-building service for ADHD prediction feedback loops."""

from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple


VALID_AUTOMATION_LEVELS = {"minimal", "balanced", "proactive"}


class TrustBuildingService:
    """Stores lightweight trust metrics and user feedback in memory."""

    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self._prediction_records: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._feedback_records: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._automation_levels: Dict[Tuple[str, str], str] = defaultdict(lambda: "balanced")

    async def record_prediction_outcome(
        self,
        user_id: str,
        prediction_type: str,
        predicted_value: Any,
        actual_value: Any = None,
        confidence: float = 0.5,
    ) -> None:
        self._prediction_records[user_id].append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "prediction_type": prediction_type,
                "predicted_value": predicted_value,
                "actual_value": actual_value,
                "confidence": confidence,
            }
        )

    async def collect_user_feedback(
        self,
        user_id: str,
        prediction_type: str,
        prediction_id: str,
        rating: int,
        usefulness: str,
        comments: Optional[str] = None,
    ) -> None:
        self._feedback_records[user_id].append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "prediction_type": prediction_type,
                "prediction_id": prediction_id,
                "rating": rating,
                "usefulness": usefulness,
                "comments": comments,
            }
        )

    async def get_trust_metrics(self, user_id: str) -> Dict[str, Any]:
        feedback = self._feedback_records.get(user_id, [])
        predictions = self._prediction_records.get(user_id, [])

        rating_avg = (
            sum(item["rating"] for item in feedback) / len(feedback)
            if feedback
            else 3.5
        )
        overall_trust_score = max(0.0, min(1.0, rating_avg / 5.0))

        prediction_types: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"count": 0, "avg_confidence": 0.0}
        )
        for item in predictions:
            record = prediction_types[item["prediction_type"]]
            record["count"] += 1
            record["avg_confidence"] += float(item.get("confidence", 0.0))

        for record in prediction_types.values():
            if record["count"]:
                record["avg_confidence"] /= record["count"]

        feedback_summary = {
            "total_feedback_entries": len(feedback),
            "average_rating": round(rating_avg, 2),
            "usefulness_breakdown": dict(
                (label, sum(1 for item in feedback if item["usefulness"] == label))
                for label in {"very_useful", "somewhat_useful", "neutral", "not_useful", "harmful"}
            ),
        }

        automation_levels = {}
        for key, value in self._automation_levels.items():
            uid, prediction_type = key
            if uid == user_id:
                automation_levels[prediction_type] = value

        recommendations = []
        if overall_trust_score < 0.5:
            recommendations.append("Lower automation to reduce friction while confidence rebuilds.")
        if overall_trust_score > 0.8:
            recommendations.append("Current predictions are trusted; proactive automation is suitable.")
        if not recommendations:
            recommendations.append("Maintain balanced automation and continue collecting feedback.")

        return {
            "overall_trust_score": round(overall_trust_score, 3),
            "prediction_types": dict(prediction_types),
            "feedback_summary": feedback_summary,
            "automation_levels": automation_levels,
            "recommendations": recommendations,
        }

    async def get_visualization_data(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=max(days, 1))
        feedback = [
            item
            for item in self._feedback_records.get(user_id, [])
            if datetime.fromisoformat(item["timestamp"]) >= cutoff
        ]
        predictions = [
            item
            for item in self._prediction_records.get(user_id, [])
            if datetime.fromisoformat(item["timestamp"]) >= cutoff
        ]

        feedback_distribution = {
            str(star): sum(1 for item in feedback if item["rating"] == star)
            for star in range(1, 6)
        }

        trust_progression = []
        running_total = 0.0
        for idx, item in enumerate(feedback, start=1):
            running_total += item["rating"] / 5.0
            trust_progression.append(
                {
                    "timestamp": item["timestamp"],
                    "trust_score": round(running_total / idx, 3),
                }
            )

        by_type: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for item in predictions:
            by_type[item["prediction_type"]].append(
                {
                    "timestamp": item["timestamp"],
                    "confidence": float(item.get("confidence", 0.0)),
                    "has_actual_value": item.get("actual_value") is not None,
                }
            )

        level_changes = []
        for (uid, prediction_type), level in self._automation_levels.items():
            if uid == user_id:
                level_changes.append(
                    {
                        "prediction_type": prediction_type,
                        "new_level": level,
                    }
                )

        success_stories = [
            {
                "prediction_type": item["prediction_type"],
                "timestamp": item["timestamp"],
                "confidence": item.get("confidence", 0.0),
            }
            for item in predictions
            if float(item.get("confidence", 0.0)) >= 0.8
        ][:20]

        return {
            "accuracy_over_time": dict(by_type),
            "feedback_distribution": feedback_distribution,
            "trust_score_progression": trust_progression,
            "automation_level_changes": level_changes,
            "prediction_success_stories": success_stories,
        }

    async def adjust_automation_level(
        self,
        prediction_type: str,
        user_id: str,
        new_level: str,
    ) -> bool:
        if new_level not in VALID_AUTOMATION_LEVELS:
            return False
        self._automation_levels[(user_id, prediction_type)] = new_level
        return True


_trust_services: Dict[str, TrustBuildingService] = {}


async def get_trust_building_service(workspace_id: str) -> TrustBuildingService:
    """Get or create trust service for workspace."""
    service = _trust_services.get(workspace_id)
    if service is None:
        service = TrustBuildingService(workspace_id)
        _trust_services[workspace_id] = service
    return service
