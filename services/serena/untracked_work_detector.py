# Minimal stub for UntrackedWorkDetector to unblock tests
# Full impl in F1 phase; this satisfies import for v2 testing

class UntrackedWorkDetector:
    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id

    def detect(self, results: list) -> list:
        """Stub: Return mock abandonment data for tests."""
        mock_abandonments = [
            {
                "is_abandoned": False,
                "days_idle": 0,
                "severity": "none",
                "files": [],
                "confidence": 0.0
            }
        ] * len(results)
        return mock_abandonments

    def suggest_action(self, abandonment_data: dict) -> str:
        """Stub: Return safe action."""
        return "monitor"  # No real action in stub
