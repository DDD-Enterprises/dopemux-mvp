"""Test Suite for EffectivenessTracker - Navigation effectiveness measurement and A/B testing"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "services" / "serena"))

from v2.intelligence.effectiveness_tracker import (
    EffectivenessTracker,
    create_effectiveness_tracker
)

@pytest.mark.asyncio
@pytest.mark.database
async def test_effectiveness_tracker_initialization(intelligence_db, performance_monitor):
    """Test effectiveness tracker creation."""
    tracker = await create_effectiveness_tracker(intelligence_db, None, None, performance_monitor)
    assert tracker is not None
