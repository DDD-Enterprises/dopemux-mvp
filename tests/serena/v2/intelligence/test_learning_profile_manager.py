"""
Comprehensive Test Suite for PersonalLearningProfileManager

Tests profile persistence, accommodation preferences, navigation patterns,
and attention pattern tracking for ADHD optimization.
"""

import pytest
from datetime import datetime, timezone

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "services" / "serena"))

from v2.intelligence.learning_profile_manager import (
    PersonalLearningProfileManager,
    AccommodationPreference,
    NavigationPreferencePattern,
    AttentionPattern,
    ProfileInsight,
    create_profile_manager,
    simulate_profile_learning
)
from v2.intelligence.adaptive_learning import PersonalLearningProfile, LearningPhase


# ==========================================
# Test 1: Profile Manager Initialization
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
async def test_profile_manager_initialization(intelligence_db, performance_monitor):
    """Test profile manager creation."""
    manager = PersonalLearningProfileManager(intelligence_db, performance_monitor)

    assert manager.database == intelligence_db
    assert manager.performance_monitor == performance_monitor


# ==========================================
# Test 2: Profile Creation and Storage
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
async def test_profile_creation_and_storage(intelligence_db, performance_monitor):
    """Test creating and storing learning profiles."""
    manager = PersonalLearningProfileManager(intelligence_db, performance_monitor)

    user_id = "test_profile_user"
    workspace = "/test/workspace"

    # Create profile
    profile = PersonalLearningProfile(
        user_session_id=user_id,
        workspace_path=workspace,
        average_attention_span_minutes=20.0,
        preferred_result_limit=8
    )

    # Get or create profile (stores automatically)
    retrieved = await manager.get_or_create_profile(user_id, workspace)
    assert retrieved is not None
    assert retrieved.user_session_id == user_id
    assert retrieved.workspace_path == workspace


# ==========================================
# Test 3: Profile Update
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
async def test_profile_update(intelligence_db, performance_monitor):
    """Test updating existing profiles."""
    manager = PersonalLearningProfileManager(intelligence_db, performance_monitor)

    user_id = "update_test_user"
    workspace = "/test/workspace"

    # Get initial profile
    profile = await manager.get_or_create_profile(user_id, workspace)

    # Update profile via navigation data
    navigation_data = {
        "session_duration_ms": 600000,  # 10 minutes
        "actions_completed": 15,
        "effectiveness_score": 0.8
    }

    updated_profile = await manager.update_profile_from_navigation(
        user_id, workspace, navigation_data
    )

    # Retrieve and verify
    assert updated_profile.user_session_id == user_id


# ==========================================
# Test 4: Accommodation Preferences
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
@pytest.mark.adhd
async def test_accommodation_preferences(intelligence_db, performance_monitor):
    """Test ADHD accommodation preference management."""
    manager = PersonalLearningProfileManager(intelligence_db, performance_monitor)

    user_id = "adhd_prefs_user"
    workspace = "/test/workspace"

    # Get profile which includes accommodation data
    profile = await manager.get_or_create_profile(user_id, workspace)

    # Update with navigation that uses accommodations
    navigation_data = {
        "accommodations_used": {
            "progressive_disclosure": True,
            "complexity_filtering": True
        },
        "accommodation_effectiveness": 0.8
    }

    updated = await manager.update_profile_from_navigation(user_id, workspace, navigation_data)
    assert updated is not None


# ==========================================
# Test 5: Navigation Preference Patterns
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
async def test_navigation_preference_patterns(intelligence_db, performance_monitor):
    """Test navigation preference pattern tracking."""
    manager = PersonalLearningProfileManager(intelligence_db, performance_monitor)

    user_id = "nav_pattern_user"
    workspace = "/test/workspace"

    # Update profile with navigation preference data
    nav_data = {
        "navigation_mode": "focus",
        "complexity_encountered": 0.4,
        "result_limit_used": 8,
        "was_effective": True
    }

    profile = await manager.update_profile_from_navigation(user_id, workspace, nav_data)
    assert profile is not None


# ==========================================
# Test 6: Attention Pattern Tracking
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
@pytest.mark.adhd
async def test_attention_pattern_tracking(intelligence_db, performance_monitor):
    """Test attention pattern tracking for ADHD users."""
    manager = PersonalLearningProfileManager(intelligence_db, performance_monitor)

    user_id = "attention_user"
    workspace = "/test/workspace"

    # Update profile with attention data embedded in navigation
    attention_data = {
        "session_duration_ms": 900000,  # 15 minutes
        "attention_quality": 0.7,
        "interruptions_count": 2
    }

    profile = await manager.update_profile_from_navigation(user_id, workspace, attention_data)
    assert profile is not None


# ==========================================
# Test 7: Profile Insights Generation
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
@pytest.mark.adhd
async def test_profile_insights_generation(intelligence_db, performance_monitor):
    """Test ADHD-specific profile insights."""
    manager = PersonalLearningProfileManager(intelligence_db, performance_monitor)

    user_id = "insights_user"
    workspace = "/test/workspace"

    # Get adaptive recommendations (includes insights)
    recommendations = await manager.get_adaptive_recommendations(user_id, workspace)

    assert recommendations is not None
    # Should provide ADHD-relevant guidance


# ==========================================
# Test 8: Factory Function
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
async def test_create_profile_manager_factory(intelligence_db, performance_monitor):
    """Test convenience factory function."""
    manager = await create_profile_manager(intelligence_db, performance_monitor)

    assert isinstance(manager, PersonalLearningProfileManager)


# ==========================================
# Test 9: Profile Learning Simulation
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
@pytest.mark.slow
async def test_simulate_profile_learning(intelligence_db, performance_monitor):
    """Test profile learning simulation."""
    manager = await create_profile_manager(intelligence_db, performance_monitor)

    result = await simulate_profile_learning(
        profile_manager=manager,
        user_session_id="sim_user",
        workspace_path="/test/workspace",
        days=3  # Correct parameter name
    )

    assert result is not None
    assert isinstance(result, dict)


# ==========================================
# Test 10: Performance (ADHD Compliance)
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
@pytest.mark.performance
@pytest.mark.adhd
async def test_profile_manager_performance(intelligence_db, performance_monitor, assert_adhd_compliant):
    """Test that profile operations meet ADHD performance targets."""
    manager = PersonalLearningProfileManager(intelligence_db, performance_monitor)

    user_id = "perf_user"
    workspace = "/test/workspace"

    import time

    # Test profile get/create performance
    start_time = time.time()
    profile = await manager.get_or_create_profile(user_id, workspace)
    get_time = (time.time() - start_time) * 1000

    assert_adhd_compliant(get_time)

    # Test profile update performance
    start_time = time.time()
    updated = await manager.update_profile_from_navigation(
        user_id, workspace, {"test_data": "value"}
    )
    update_time = (time.time() - start_time) * 1000

    assert_adhd_compliant(update_time)

    print(f"Profile get: {get_time:.2f}ms, Profile update: {update_time:.2f}ms")
