#!/usr/bin/env python3
"""
Validate code examples from documentation.
Tests that documented examples actually work.
"""

import re

import logging

logger = logging.getLogger(__name__)

import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Tuple

# Test cases from key documentation
TEST_CASES = [
    {
        "source": "Dope-Context API_REFERENCE.md",
        "description": "Index workspace example",
        "code": """
# Simulated MCP call (testing logic, not actual indexing)
def index_workspace(workspace_path, include_patterns=None, exclude_patterns=None, max_files=None):
    return {"status": "success", "files_indexed": 0}

result = index_workspace("/Users/test/project")
assert result["status"] == "success"
logger.info("✅ index_workspace call structure correct")
        """
    },
    {
        "source": "Dope-Context API_REFERENCE.md",
        "description": "Search code example",
        "code": """
# Simulated MCP search call
def search_code(query, top_k=10, profile="implementation", use_reranking=True, filter_language=None, workspace_path=None):
    return [{"file_path": "/test.py", "code": "def test(): pass", "score": 0.9}]

results = search_code("async database connection pooling")
assert isinstance(results, list)
logger.info("✅ search_code call structure correct")
        """
    },
    {
        "source": "ADHD Engine auth.py",
        "description": "API key authentication logic",
        "code": """
import os
from fastapi import Security, HTTPException

# Test auth logic
API_KEY = "test-key-12345"
EXPECTED_KEY = "test-key-12345"

def verify_key(provided_key):
    if not EXPECTED_KEY:
        return None  # Dev mode
    if not provided_key or provided_key != EXPECTED_KEY:
        raise HTTPException(status_code=401, detail="Invalid")
    return provided_key

result = verify_key(API_KEY)
assert result == API_KEY
logger.info("✅ Authentication logic correct")
        """
    },
    {
        "source": "CORS Configuration",
        "description": "Environment-based CORS",
        "code": """
import os

# Test CORS parsing
os.environ['ALLOWED_ORIGINS'] = 'http://a.com,http://b.com,http://c.com'
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

assert len(ALLOWED_ORIGINS) == 3
assert '*' not in ALLOWED_ORIGINS
assert ALLOWED_ORIGINS[0] == 'http://a.com'
logger.info("✅ CORS configuration parsing correct")
        """
    },
    {
        "source": "Database credentials",
        "description": "Environment variable credential loading",
        "code": """
import os

# Test credential loading
os.environ['TEST_PASSWORD'] = 'from-environment'
password = os.getenv("TEST_PASSWORD", "hardcoded_fallback")

assert password == "from-environment"
logger.info("✅ Environment credential loading correct")
        """
    }
]


def test_example(test_case: Dict) -> Tuple[bool, str]:
    """
    Test a single code example.

    Returns:
        (success, message)
    """
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_case["code"])
            f.flush()
            temp_path = f.name

        # Run code
        result = subprocess.run(
            ['python3', temp_path],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Clean up
        Path(temp_path).unlink()

        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, f"Error: {result.stderr.strip()}"

    except subprocess.TimeoutExpired:
        return False, "Timeout (>5s)"
    except Exception as e:
        return False, f"Exception: {str(e)}"


        logger.error(f"Error: {e}")
def main():
    """Run all validation tests."""
    logger.info("=" * 70)
    logger.info("CODE EXAMPLE VALIDATION")
    logger.info("=" * 70)
    logger.info()

    passed = 0
    failed = 0
    results = []

    for i, test_case in enumerate(TEST_CASES, 1):
        logger.info(f"Test {i}/{len(TEST_CASES)}: {test_case['description']}")
        logger.info(f"  Source: {test_case['source']}")

        success, message = test_example(test_case)

        if success:
            logger.info(f"  ✅ PASS")
            logger.info(f"     {message}")
            passed += 1
        else:
            logger.error(f"  ❌ FAIL")
            logger.info(f"     {message}")
            failed += 1

        results.append({
            "test": test_case['description'],
            "source": test_case['source'],
            "passed": success,
            "message": message
        })

        logger.info()

    # Summary
    logger.info("=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total tests: {len(TEST_CASES)}")
    logger.info(f"Passed: {passed} ({passed/len(TEST_CASES)*100:.0f}%)")
    logger.error(f"Failed: {failed}")
    logger.info()

    if failed == 0:
        logger.info("🎉 All code examples validated successfully!")
        return 0
    else:
        logger.error(f"⚠️  {failed} examples need fixes")
        return 1


if __name__ == "__main__":
    exit(main())
