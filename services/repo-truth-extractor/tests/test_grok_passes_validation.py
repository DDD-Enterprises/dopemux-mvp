import sys
import json
import hashlib
from pathlib import Path
from typing import Any, Dict

import pytest

ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from lib.prescan.grok_passes import BatchResponseValidator, GrokPassRunner
from lib.prescan.models import PrescanConfig

def test_batch_response_validator_dedup():
    validator = BatchResponseValidator()
    
    valid_response = {
        "duplicate_assessments": [
            {
                "group_id": "hash123",
                "confirmed_duplicate": True,
                "canonical_path": "src/main.py",
                "superseded_paths": ["src/main_copy.py"],
                "confidence": 0.95,
                "reasoning": "Identical hash."
            }
        ]
    }
    
    ok, data, error = validator.validate("dedup", json.dumps(valid_response))
    assert ok is True
    assert data["duplicate_assessments"][0]["confidence"] == 0.95
    assert not error

def test_batch_response_validator_discover():
    validator = BatchResponseValidator()
    
    valid_response = {
        "hidden_features": [
            {
                "path": "src/hidden.py",
                "feature_name": "Ghost API",
                "description": "Undocumented endpoint.",
                "confidence": 0.8,
                "extraction_phase": "C"
            }
        ]
    }
    
    ok, data, error = validator.validate("discover", json.dumps(valid_response))
    assert ok is True
    assert data["hidden_features"][0]["feature_name"] == "Ghost API"

def test_grok_pass_runner_caching(tmp_path: Path):
    config = PrescanConfig(
        repo_root=tmp_path,
        output_dir=tmp_path / "out",
    )
    runner = GrokPassRunner(config)
    
    pass_id = "dedup"
    payload = {"corpus_summary": {"total_files": 10}}
    result = {"duplicate_assessments": []}
    
    # 1. Save to cache
    runner._save_cached_pass(pass_id, payload, result)
    
    # 2. Load from cache
    cached = runner._load_cached_pass(pass_id, payload)
    assert cached == result
    
    # 3. Different payload should not hit cache
    other_payload = {"corpus_summary": {"total_files": 20}}
    not_cached = runner._load_cached_pass(pass_id, other_payload)
    assert not_cached is None

def test_grok_pass_runner_preview_truncation(tmp_path: Path):
    config = PrescanConfig(
        repo_root=tmp_path,
        output_dir=tmp_path / "out",
    )
    runner = GrokPassRunner(config)
    
    large_file = tmp_path / "large.txt"
    # Create a file larger than MAX_PREVIEW_BYTES (6144)
    content = "line\n" * 1000 
    large_file.write_text(content)
    
    from lib.prescan.models import FileEntry
    entry = FileEntry(rel_path="large.txt", size_bytes=len(content), extension=".txt")
    
    preview = runner._get_file_preview(entry)
    
    # Check lines (MAX_PREVIEW_LINES = 150)
    assert len(preview.splitlines()) <= 151 # 150 + [TRUNCATED]
    assert "...[TRUNCATED]" in preview

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
