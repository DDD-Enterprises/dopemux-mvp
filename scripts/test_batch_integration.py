#!/usr/bin/env python3
"""
Test script to verify the OpenAI batch retrieval integration.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the services directory to the path
sys.path.insert(0, str(Path(__file__).parent / "services"))

def test_batch_retriever_import():
    """Test that the batch retriever can be imported."""
    try:
        # Import directly from the file path
        sys.path.insert(0, str(Path(__file__).parent / "services" / "repo-truth-extractor"))
        from lib.batch_retriever import retrieve_openai_batch, retrieve_openai_batches
        print("✓ Batch retriever imports successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import batch retriever: {e}")
        return False

def test_batch_clients_import():
    """Test that the batch clients can be imported."""
    try:
        sys.path.insert(0, str(Path(__file__).parent / "services" / "repo-truth-extractor"))
        from lib.batch_clients import OpenAIBatchClient
        print("✓ Batch clients import successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import batch clients: {e}")
        return False

def test_batch_retriever_functionality():
    """Test the batch retriever with mock data."""
    try:
        sys.path.insert(0, str(Path(__file__).parent / "services" / "repo-truth-extractor"))
        from lib.batch_retriever import retrieve_openai_batch
        
        # Test with a fake batch ID (should fail gracefully)
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
            if not success and "error" in result:
                print("✓ Batch retriever handles errors gracefully")
                return True
            else:
                print("✗ Batch retriever should have failed with fake credentials")
                return False
                
    except Exception as e:
        print(f"✗ Batch retriever test failed: {e}")
        return False

def test_main_script_arguments():
    """Test that the main script accepts the new arguments."""
    try:
        # Test that help works
        import subprocess
        result = subprocess.run([
            sys.executable, "services/repo-truth-extractor/run_extraction_v3.py",
            "--help"
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if "--batch-retrieve" in result.stdout:
            print("✓ Main script accepts --batch-retrieve argument")
            return True
        else:
            print("✗ Main script doesn't show --batch-retrieve in help")
            return False
            
    except Exception as e:
        print(f"✗ Failed to test main script arguments: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing OpenAI Batch Retrieval Integration...")
    print("=" * 50)
    
    tests = [
        test_batch_retriever_import,
        test_batch_clients_import,
        test_batch_retriever_functionality,
        test_main_script_arguments,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
