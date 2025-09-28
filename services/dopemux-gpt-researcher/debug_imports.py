"""
Debug imports to identify the specific issue
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    print("Step 1: Testing research task models...")
    from models.research_task import ResearchType, ADHDConfiguration, ProjectContext
    print("✅ Research task models imported successfully")

    print("\nStep 2: Testing query classifier...")
    from engines.query_classifier import QueryClassificationEngine
    print("✅ Query classifier imported successfully")

    print("\nStep 3: Testing base search adapter...")
    from engines.search.base_adapter import BaseSearchAdapter, SearchResult
    print("✅ Base search adapter imported successfully")

    print("\nStep 4: Testing search adapters individually...")
    try:
        from engines.search.exa_adapter import ExaSearchAdapter
        print("✅ Exa adapter imported successfully")
    except Exception as e:
        print(f"⚠️ Exa adapter import issue: {e}")

    try:
        from engines.search.tavily_adapter import TavilySearchAdapter
        print("✅ Tavily adapter imported successfully")
    except Exception as e:
        print(f"⚠️ Tavily adapter import issue: {e}")

    try:
        from engines.search.perplexity_adapter import PerplexitySearchAdapter
        print("✅ Perplexity adapter imported successfully")
    except Exception as e:
        print(f"⚠️ Perplexity adapter import issue: {e}")

    try:
        from engines.search.context7_adapter import Context7SearchAdapter
        print("✅ Context7 adapter imported successfully")
    except Exception as e:
        print(f"⚠️ Context7 adapter import issue: {e}")

    print("\nStep 5: Testing search orchestrator...")
    from engines.search.search_orchestrator import SearchOrchestrator, SearchStrategy
    print("✅ Search orchestrator imported successfully")

    print("\nStep 6: Testing final orchestrator...")
    from services.orchestrator import ResearchTaskOrchestrator
    print("✅ ResearchTaskOrchestrator imported successfully")

    print("\n🎉 All imports successful!")

except Exception as e:
    print(f"❌ Error at step: {e}")
    import traceback
    traceback.print_exc()