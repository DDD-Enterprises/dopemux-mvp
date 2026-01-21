"""
Debug imports to identify the specific issue
"""

import sys

import logging

logger = logging.getLogger(__name__)

import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    logger.info("Step 1: Testing research task models...")
    from models.research_task import ResearchType, ADHDConfiguration, ProjectContext
    logger.info("✅ Research task models imported successfully")

    logger.info("\nStep 2: Testing query classifier...")
    from engines.query_classifier import QueryClassificationEngine
    logger.info("✅ Query classifier imported successfully")

    logger.info("\nStep 3: Testing base search adapter...")
    from engines.search.base_adapter import BaseSearchAdapter, SearchResult
    logger.info("✅ Base search adapter imported successfully")

    logger.info("\nStep 4: Testing search adapters individually...")
    try:
        from engines.search.exa_adapter import ExaSearchAdapter
        logger.info("✅ Exa adapter imported successfully")
    except Exception as e:
        logger.info(f"⚠️ Exa adapter import issue: {e}")

    try:
        from engines.search.tavily_adapter import TavilySearchAdapter
        logger.info("✅ Tavily adapter imported successfully")
    except Exception as e:
        logger.info(f"⚠️ Tavily adapter import issue: {e}")

    try:
        from engines.search.perplexity_adapter import PerplexitySearchAdapter
        logger.info("✅ Perplexity adapter imported successfully")
    except Exception as e:
        logger.info(f"⚠️ Perplexity adapter import issue: {e}")

    try:
        from engines.search.context7_adapter import Context7SearchAdapter
        logger.info("✅ Context7 adapter imported successfully")
    except Exception as e:
        logger.info(f"⚠️ Context7 adapter import issue: {e}")

    logger.info("\nStep 5: Testing search orchestrator...")
    from engines.search.search_orchestrator import SearchOrchestrator, SearchStrategy
    logger.info("✅ Search orchestrator imported successfully")

    logger.info("\nStep 6: Testing final orchestrator...")
    from services.orchestrator import ResearchTaskOrchestrator
    logger.info("✅ ResearchTaskOrchestrator imported successfully")

    logger.info("\n🎉 All imports successful!")

except Exception as e:
    logger.error(f"❌ Error at step: {e}")
    import traceback
    traceback.print_exc()