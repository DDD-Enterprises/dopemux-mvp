#!/usr/bin/env python3
"""
Integration test to verify the OpenAI batch retrieval integration.
"""

import sys
import tempfile
from pathlib import Path
import subprocess
import pytest

# Dynamic path resolution
REPO_ROOT = Path(__file__).resolve().parents[2]
SERVICE_DIR = REPO_ROOT / "services" / "repo-truth-extractor"

@pytest.fixture(autouse=True)
def setup_path():
    """Ensure service directory is in sys.path."""
    if str(SERVICE_DIR) not in sys.path:
        sys.path.insert(0, str(SERVICE_DIR))
    yield

def test_batch_retriever_import():
    """Test that the batch retriever can be imported."""
    from lib.batch_retriever import retrieve_openai_batch, retrieve_openai_batches
    assert retrieve_openai_batch is not None
    assert retrieve_openai_batches is not None

def test_batch_clients_import():
    """Test that the batch clients can be imported."""
    from lib.batch_clients import OpenAIBatchClient
    assert OpenAIBatchClient is not None

def test_batch_retriever_functionality():
    """Test the batch retriever with mock data (graceful failure)."""
    from lib.batch_retriever import retrieve_openai_batch
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        # This should fail because we don't have a real API key or batch ID
        # but it should fail gracefully
        success, result = retrieve_openai_batch(
            api_key="fake_key",
            batch_id="fake_batch_id",
            output_dir=output_dir
        )
        
        # Should return False (not successful) but should not crash
        assert not success
        assert "error" in result or result["status"] == "error"

def test_main_script_arguments():
    """Test that the main script accepts the new arguments."""
    # Test that help works
    result = subprocess.run([
        sys.executable, str(SERVICE_DIR / "run_extraction_v3.py"),
        "--help"
    ], capture_output=True, text=True, cwd=REPO_ROOT)
    
    assert result.returncode == 0
    assert "--batch-retrieve" in result.stdout
    assert "--retrieve-provider" in result.stdout
