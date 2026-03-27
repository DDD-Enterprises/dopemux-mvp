#!/usr/bin/env python3
"""Zero-network integration checks for batch retrieval surfaces."""

from __future__ import annotations

import sys
from pathlib import Path
import subprocess

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVICE_DIR = REPO_ROOT / "services" / "repo-truth-extractor"


@pytest.fixture(autouse=True)
def setup_path():
    if str(SERVICE_DIR) not in sys.path:
        sys.path.insert(0, str(SERVICE_DIR))
    yield


def test_batch_retriever_imports_provider_aware_surface():
    from lib.batch_retriever import retrieve_batch, retrieve_batches, retrieve_gemini_batches, retrieve_openai_batches, retrieve_xai_batches

    assert retrieve_batch is not None
    assert retrieve_batches is not None
    assert retrieve_openai_batches is not None
    assert retrieve_gemini_batches is not None
    assert retrieve_xai_batches is not None


def test_batch_clients_imports_include_provider_guard():
    from lib.batch_clients import OpenAIBatchClient, UnsupportedBatchProvider

    assert OpenAIBatchClient is not None
    assert UnsupportedBatchProvider is not None


def test_main_script_arguments():
    result = subprocess.run(
        [sys.executable, str(SERVICE_DIR / "run_extraction_v3.py"), "--help"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0
    assert "--batch-retrieve" in result.stdout
    assert "--retrieve-provider" in result.stdout
    assert "xai" in result.stdout
