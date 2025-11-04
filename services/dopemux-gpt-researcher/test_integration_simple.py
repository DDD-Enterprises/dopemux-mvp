"""
Simple integration test for SearchOrchestrator integration

This test validates that the integration is syntactically correct and
that basic initialization works.
"""

import sys
import os

# Add the research_api directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'research_api'))

try:
    print("Testing imports...")

    # Test model imports
    from research_api.models.research_task import ResearchType, ADHDConfiguration, ProjectContext
    print("✅ Research task models imported successfully")

    # Test orchestrator import
    from research_api.services.orchestrator import ResearchTaskOrchestrator
    print("✅ ResearchTaskOrchestrator imported successfully")

    # Test search engine imports
    from research_api.engines.search.search_orchestrator import SearchOrchestrator, SearchStrategy
    print("✅ SearchOrchestrator imported successfully")

    # Test adapter imports
    from research_api.engines.search.base_adapter import BaseSearchAdapter, SearchResult
    print("✅ Search adapters imported successfully")

    print("\n🎉 All imports successful! Integration is syntactically correct.")

    # Test basic initialization
    print("\nTesting basic initialization...")

    project_context = ProjectContext(
        workspace_path="/Users/hue/code/dopemux-mvp",
        tech_stack=["Python", "FastAPI"],
        architecture_patterns=["microservices"]
    )

    # Initialize without API keys (will use mock adapter)
    orchestrator = ResearchTaskOrchestrator(
        project_context=project_context,
        search_api_keys={}
    )

    print("✅ ResearchTaskOrchestrator initialized successfully")
    print(f"✅ SearchOrchestrator has {len(orchestrator.search_orchestrator.engines)} engines")
    print(f"✅ Available engines: {list(orchestrator.search_orchestrator.engines.keys())}")

    print("\n🚀 Basic integration test PASSED!")
    print("The SearchOrchestrator integration is working correctly.")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Integration has import issues that need to be resolved.")
    sys.exit(1)

except Exception as e:
    print(f"❌ Initialization error: {e}")
    print("Integration has initialization issues.")
    sys.exit(1)