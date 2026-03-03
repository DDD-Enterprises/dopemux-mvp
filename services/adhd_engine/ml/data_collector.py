"""
Data Collector for ML Training Pipeline.

Responsible for aggregating and logging runtime state to building historical datasets.
Feeds into: services/adhd_engine/ml/energy_predictor.py
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DataCollector:
    """
    Collects and persists user activity data for ML model training.
    
    Format: JSONL (one valid JSON object per line)
    Location: data/adhd_training_data.jsonl
    """
    
    def __init__(self, data_dir: str = "data", filename: str = "adhd_training_data.jsonl"):
        self.data_dir = data_dir
        self.filename = filename
        self.file_path = os.path.join(data_dir, filename)
        
        # Ensure directory exists
        os.makedirs(data_dir, exist_ok=True)
        
    async def log_state(self, user_id: str, state_vector: Dict[str, Any]) -> bool:
        """
        Log a snapshot of the user's current state.
        
        Args:
            user_id: User identifier
            state_vector: Dictionary containing features and labels
                          (energy_level, attention_state, session_duration, etc.)
        """
        try:
            entry = {
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                **state_vector
            }
            
            def _write_sync():
                with open(self.file_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry) + "\n")

            await asyncio.to_thread(_write_sync)
            return True
            
        except Exception as e:
            logger.error(f"Failed to log training data: {e}")
            return False

    async def get_recent_history(self, user_id: str, limit: int = 100) -> list:
        """
        Retrieve recent history for a user (useful for immediate context).
        Warning: Not efficient for large datasets. Use with caution.
        """
        history = []
        try:
            def _read_sync():
                if not os.path.exists(self.file_path):
                    return []

                # Read last N lines (inefficient but simple for MVP)
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return f.readlines()

            lines = await asyncio.to_thread(_read_sync)

            if not lines:
                return []

            for line in reversed(lines):
                if len(history) >= limit:
                    break
                try:
                    data = json.loads(line)
                    if data.get("user_id") == user_id:
                        history.append(data)
                except json.JSONDecodeError:
                    continue
                    
            return history
            
        except Exception as e:
            logger.error(f"Failed to read history: {e}")
            return []

    async def load_all_data(self) -> list:
        """
        Load all collected data for training (Phase 10.4).
        Returns a list of dictionaries, one per line of JSONL.
        """
        try:
            def _load_sync():
                data = []
                if not os.path.exists(self.file_path):
                    return []

                with open(self.file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            data.append(entry)
                        except json.JSONDecodeError:
                            continue
                return data
            
            data = await asyncio.to_thread(_load_sync)
            logger.info(f"Loaded {len(data)} records for training")
            return data
            
        except Exception as e:
            logger.error(f"Failed to load training data: {e}")
            return []
