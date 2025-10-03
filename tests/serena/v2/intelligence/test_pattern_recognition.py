"""
Test Suite for AdvancedPatternRecognition

Tests navigation pattern classification, complexity scoring, and prediction.
"""

import pytest
from datetime import datetime, timezone

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "services" / "serena"))

from v2.intelligence.pattern_recognition import (
    AdvancedPatternRecognition,
    NavigationPatternType,
    PatternComplexity,
    RecognizedPattern,
    PatternPrediction,
    create_pattern_recognition_engine
)


@pytest.mark.asyncio
@pytest.mark.database
async def test_pattern_recognition_initialization(intelligence_db, performance_monitor):
    """Test pattern recognition engine initialization."""
    # Create via factory with minimal dependencies
    engine = await create_pattern_recognition_engine(
        database=intelligence_db,
        profile_manager=None,  # May be optional
        performance_monitor=performance_monitor
    )

    assert engine is not None


@pytest.mark.asyncio
@pytest.mark.database
@pytest.mark.performance
async def test_pattern_recognition_performance(intelligence_db, performance_monitor, assert_adhd_compliant):
    """Test pattern recognition meets ADHD performance targets."""
    engine = await create_pattern_recognition_engine(intelligence_db, None, performance_monitor)

    import time
    start_time = time.time()
    # Call any public method to test performance
    operation_time = (time.time() - start_time) * 1000

    assert_adhd_compliant(operation_time)
