import json
import os
import httpx
from pathlib import Path
from typing import Dict, Any, List, Optional

class RTEAdapter:
    """Boundary adapter between 2025 Cognitive Plane and 2026 RTE architecture."""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.rte_output_dir = self.workspace_root / "extraction"
        # Connect directly to ConPort for decision logging
        self.conport_url = os.getenv("CONPORT_URL", "http://localhost:3004")
        
    def get_latest_truth(self, artifact_type: str = "doctor/DOCTOR_FULL") -> Dict[str, Any]:
        """Read the latest specified JSON artifact from RTE output."""
        path = self.rte_output_dir / f"{artifact_type}.json"
        if not path.exists():
            raise FileNotFoundError(f"RTE Artifact not found at: {path}")
            
        with open(path, 'r') as f:
            return json.load(f)

    async def write_decision_to_conport(self, decision_data: Dict[str, Any]) -> Dict[str, Any]:
        """Write truth artifacts as 'decisions' into ConPort KG."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.conport_url}/api/decisions",
                json=decision_data,
                timeout=10.0
            )
            response.raise_for_status()
            # httpx .json() is NOT a coroutine
            return response.json()
