"""
Unit Tests for Feature Flags System

Tests the gradual rollout system for ADHD Engine integration.
"""

import pytest
import pytest_asyncio
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from adhd_engine.feature_flags import (
    ADHDFeatureFlags,
    FEATURE_ADHD_ENGINE_SERENA,
    FEATURE_ADHD_ENGINE_CONPORT,
    FEATURE_ADHD_ENGINE_DOPE_CONTEXT
)


@pytest_asyncio.fixture
async def feature_flags(redis_client):
    """Create ADHDFeatureFlags instance for testing."""
    return ADHDFeatureFlags(redis_client)


class TestPriorityHierarchy:
    """Test feature flag priority: user > service > global > default."""

    @pytest.mark.asyncio
    async def test_user_override_beats_service_flag(self, feature_flags, redis_client):
        """User-level override should take priority over service flag."""
        # Setup: Service enabled, user disabled
        await redis_client.set(
            "adhd:feature_flags:test_feature:service:serena",
            "true"
        )
        await redis_client.set(
            "adhd:feature_flags:test_feature:user:user1",
            "false"
        )

        # User override should win
        enabled = await feature_flags.is_enabled("test_feature", "serena", "user1")

        assert enabled is False, "User override should beat service flag"

    @pytest.mark.asyncio
    async def test_service_flag_beats_global(self, feature_flags, redis_client):
        """Service flag should take priority over global flag."""
        # Setup: Global enabled, service disabled
        await redis_client.set(
            "adhd:feature_flags:test_feature:global",
            "true"
        )
        await redis_client.set(
            "adhd:feature_flags:test_feature:service:serena",
            "false"
        )

        # Service flag should win
        enabled = await feature_flags.is_enabled("test_feature", "serena")

        assert enabled is False, "Service flag should beat global"

    @pytest.mark.asyncio
    async def test_global_flag_beats_default(self, feature_flags, redis_client):
        """Global flag should take priority over default (disabled)."""
        # Setup: Only global flag set
        await redis_client.set(
            "adhd:feature_flags:test_feature:global",
            "true"
        )

        enabled = await feature_flags.is_enabled("test_feature", "serena")

        assert enabled is True, "Global flag should enable feature"

    @pytest.mark.asyncio
    async def test_default_is_disabled(self, feature_flags, redis_client):
        """Default should be disabled (safe during migration)."""
        # No flags set
        enabled = await feature_flags.is_enabled("test_feature", "serena")

        assert enabled is False, "Default should be disabled"


class TestEnableDisable:
    """Test enable/disable methods."""

    @pytest.mark.asyncio
    async def test_enable_for_service(self, feature_flags, redis_client):
        """Should enable feature for specific service."""
        await feature_flags.enable_for_service("test_feature", "serena")

        # Verify enabled
        enabled = await feature_flags.is_enabled("test_feature", "serena")
        assert enabled is True

        # Verify Redis key set
        key = "adhd:feature_flags:test_feature:service:serena"
        value = await redis_client.get(key)
        assert value == "true"

    @pytest.mark.asyncio
    async def test_disable_for_service(self, feature_flags, redis_client):
        """Should disable feature for specific service."""
        # Enable first
        await feature_flags.enable_for_service("test_feature", "serena")

        # Then disable
        await feature_flags.disable_for_service("test_feature", "serena")

        # Verify disabled
        enabled = await feature_flags.is_enabled("test_feature", "serena")
        assert enabled is False

    @pytest.mark.asyncio
    async def test_enable_for_user(self, feature_flags, redis_client):
        """Should enable feature for specific user (beta testing)."""
        await feature_flags.enable_for_user("test_feature", "developer1")

        enabled = await feature_flags.is_enabled("test_feature", "serena", "developer1")
        assert enabled is True

    @pytest.mark.asyncio
    async def test_enable_globally(self, feature_flags, redis_client):
        """Should enable feature globally (full rollout)."""
        await feature_flags.enable_globally("test_feature")

        # All services should see it enabled
        enabled_serena = await feature_flags.is_enabled("test_feature", "serena")
        enabled_conport = await feature_flags.is_enabled("test_feature", "conport")

        assert enabled_serena is True
        assert enabled_conport is True

    @pytest.mark.asyncio
    async def test_disable_globally_rollback(self, feature_flags, redis_client):
        """Should disable globally for emergency rollback."""
        # Enable first
        await feature_flags.enable_globally("test_feature")
        assert await feature_flags.is_enabled("test_feature", "serena") is True

        # Emergency rollback
        await feature_flags.disable_globally("test_feature")

        # Verify disabled everywhere
        enabled = await feature_flags.is_enabled("test_feature", "serena")
        assert enabled is False


class TestRolloutScenarios:
    """Test realistic gradual rollout scenarios."""

    @pytest.mark.asyncio
    async def test_beta_test_one_user(self, feature_flags, redis_client):
        """
        Phase 1: Beta test with one user.

        Feature should be enabled ONLY for beta user, not others.
        """
        # Enable for beta user
        await feature_flags.enable_for_user(FEATURE_ADHD_ENGINE_SERENA, "developer1")

        # Beta user sees feature
        beta_enabled = await feature_flags.is_enabled(
            FEATURE_ADHD_ENGINE_SERENA,
            "serena",
            "developer1"
        )
        assert beta_enabled is True

        # Other users don't see feature
        other_enabled = await feature_flags.is_enabled(
            FEATURE_ADHD_ENGINE_SERENA,
            "serena",
            "developer2"
        )
        assert other_enabled is False

    @pytest.mark.asyncio
    async def test_service_rollout(self, feature_flags, redis_client):
        """
        Phase 2: Enable for Serena service (all Serena users).

        Serena users see feature, ConPort users don't.
        """
        await feature_flags.enable_for_service(FEATURE_ADHD_ENGINE_SERENA, "serena")

        # Serena users see feature
        serena_enabled = await feature_flags.is_enabled(
            FEATURE_ADHD_ENGINE_SERENA,
            "serena",
            "any_user"
        )
        assert serena_enabled is True

        # ConPort users don't
        conport_enabled = await feature_flags.is_enabled(
            FEATURE_ADHD_ENGINE_CONPORT,
            "conport",
            "any_user"
        )
        assert conport_enabled is False

    @pytest.mark.asyncio
    async def test_full_rollout(self, feature_flags, redis_client):
        """
        Phase 4: Full rollout - all services, all users.
        """
        # Enable all ADHD Engine integration flags globally
        await feature_flags.enable_globally(FEATURE_ADHD_ENGINE_SERENA)
        await feature_flags.enable_globally(FEATURE_ADHD_ENGINE_CONPORT)
        await feature_flags.enable_globally(FEATURE_ADHD_ENGINE_DOPE_CONTEXT)

        # Verify all services see features
        assert await feature_flags.is_enabled(FEATURE_ADHD_ENGINE_SERENA, "serena")
        assert await feature_flags.is_enabled(FEATURE_ADHD_ENGINE_CONPORT, "conport")
        assert await feature_flags.is_enabled(FEATURE_ADHD_ENGINE_DOPE_CONTEXT, "dope-context")


class TestFlagStatus:
    """Test get_flag_status() method."""

    @pytest.mark.asyncio
    async def test_flag_status_shows_all_levels(self, feature_flags, redis_client):
        """Should show status at global, service, and user levels."""
        # Setup mixed flags
        await feature_flags.enable_globally("test_feature")
        await feature_flags.enable_for_service("test_feature", "serena")
        await feature_flags.enable_for_user("test_feature", "user1")

        # Get status
        status = await feature_flags.get_flag_status("test_feature")

        # Verify all levels present
        assert status["global"] is True
        assert "serena" in status["services"]
        assert status["services"]["serena"] is True
        assert "user1" in status["users"]
        assert status["users"]["user1"] is True

    @pytest.mark.asyncio
    async def test_flag_status_empty_when_disabled(self, feature_flags, redis_client):
        """Should show empty status when feature not enabled anywhere."""
        status = await feature_flags.get_flag_status("disabled_feature")

        assert status["global"] is False
        assert len(status["services"]) == 0
        assert len(status["users"]) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
