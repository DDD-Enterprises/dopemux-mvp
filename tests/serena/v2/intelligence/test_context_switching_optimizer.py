"""Test Suite for ContextSwitchingOptimizer - Context switch detection and optimization"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "services" / "serena"))

from v2.intelligence.context_switching_optimizer import (
    ContextSwitchingOptimizer,
    create_context_switching_optimizer
)

@pytest.mark.asyncio
@pytest.mark.database
async def test_context_switching_optimizer_initialization(intelligence_db, performance_monitor):
    """Test context switching optimizer creation."""
    optimizer = await create_context_switching_optimizer(intelligence_db, None, None, performance_monitor)
    assert optimizer is not None
