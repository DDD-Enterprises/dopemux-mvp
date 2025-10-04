"""
Tests for F5: Pattern Learning Foundation

Tests pattern_learner.py functionality:
- Pattern extraction from git detections
- Pattern caching with TTL and LRU eviction
- Probability calculation with time decay
- Confidence boosting based on patterns
- Top patterns retrieval
"""

import pytest
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Add Serena v2 to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "services" / "serena" / "v2"))

from pattern_learner import PatternLearner, PatternCache


class TestPatternCache:
    """Test suite for PatternCache class"""

    @pytest.fixture
    def cache(self):
        """Create PatternCache instance"""
        return PatternCache(max_size=5, ttl_minutes=60)

    def test_cache_initialization(self, cache):
        """Test cache initializes with correct parameters"""
        assert cache.max_size == 5
        assert cache.ttl == timedelta(minutes=60)
        assert len(cache.cache) == 0

    def test_cache_put_and_get(self, cache):
        """Test basic put/get operations"""
        pattern_data = {"type": "file_extension", "value": ".py", "probability": 0.75}
        cache.put("ext_py", pattern_data)

        retrieved = cache.get("ext_py")
        assert retrieved == pattern_data
        assert cache.access_counts["ext_py"] == 1

    def test_cache_miss_returns_none(self, cache):
        """Test cache miss returns None"""
        result = cache.get("nonexistent")
        assert result is None

    def test_cache_access_count_increments(self, cache):
        """Test access count increments on get"""
        cache.put("key1", {"data": "value"})

        cache.get("key1")
        cache.get("key1")
        cache.get("key1")

        assert cache.access_counts["key1"] == 3

    def test_cache_lru_eviction(self, cache):
        """Test LRU eviction when cache is full"""
        # Fill cache to capacity (max_size=5)
        for i in range(5):
            cache.put(f"key{i}", {"data": f"value{i}"})

        # Access key1 multiple times to make it "most used"
        for _ in range(10):
            cache.get("key1")

        # Add new entry - should evict least-used key (key0, key2, key3, or key4)
        cache.put("key_new", {"data": "new_value"})

        # key1 should still be in cache (most accessed)
        assert cache.get("key1") is not None

        # key_new should be in cache
        assert cache.get("key_new") is not None

        # Cache should still be at max size
        assert len(cache.cache) == 5

    def test_cache_ttl_expiration(self, cache):
        """Test cache entries expire after TTL"""
        cache.put("key1", {"data": "value"})

        # Manually set timestamp to past TTL
        cache.timestamps["key1"] = datetime.now() - timedelta(minutes=61)

        # Should return None (expired)
        result = cache.get("key1")
        assert result is None

        # Key should be evicted
        assert "key1" not in cache.cache

    def test_cache_invalidate(self, cache):
        """Test manual cache invalidation"""
        cache.put("key1", {"data": "value"})
        assert cache.get("key1") is not None

        cache.invalidate("key1")
        assert cache.get("key1") is None

    def test_cache_clear(self, cache):
        """Test clearing entire cache"""
        cache.put("key1", {"data": "value1"})
        cache.put("key2", {"data": "value2"})

        cache.clear()

        assert len(cache.cache) == 0
        assert len(cache.access_counts) == 0
        assert len(cache.timestamps) == 0

    def test_cache_stats(self, cache):
        """Test cache statistics"""
        cache.put("key1", {"data": "value1"})
        cache.put("key2", {"data": "value2"})

        cache.get("key1")
        cache.get("key1")
        cache.get("key2")

        stats = cache.stats()

        assert stats["size"] == 2
        assert stats["max_size"] == 5
        assert stats["utilization"] == 0.4  # 2/5
        assert stats["total_accesses"] == 3
        assert stats["avg_accesses_per_pattern"] == 1.5  # 3/2


class TestPatternExtraction:
    """Test suite for pattern extraction functionality"""

    @pytest.fixture
    def learner(self):
        """Create PatternLearner instance"""
        return PatternLearner(workspace_id="/tmp/test_workspace")

    @pytest.fixture
    def git_detection_python(self):
        """Sample git detection with Python files"""
        return {
            "has_uncommitted": True,
            "branch": "feature/auth",
            "files": [
                "services/auth/jwt.py",
                "services/auth/session.py",
                "services/auth/middleware.py",
                "tests/test_auth.py"
            ]
        }

    @pytest.fixture
    def git_detection_mixed(self):
        """Sample git detection with mixed file types"""
        return {
            "has_uncommitted": True,
            "branch": "docs/update",
            "files": [
                "docs/api.md",
                "docs/guide.md",
                "README.md",
                "services/api/routes.py",
                "services/api/handlers.py"
            ]
        }

    @pytest.mark.asyncio
    async def test_extract_file_extension_patterns(self, learner, git_detection_python):
        """Test extracting file extension patterns"""
        patterns = await learner.extract_patterns(git_detection_python)

        # Find .py extension patterns
        py_patterns = [p for p in patterns if p["type"] == "file_extension" and p["value"] == ".py"]

        assert len(py_patterns) == 1
        assert py_patterns[0]["frequency"] == 4  # 4 .py files
        assert py_patterns[0]["context"]["branch"] == "feature/auth"

    @pytest.mark.asyncio
    async def test_extract_directory_patterns(self, learner, git_detection_python):
        """Test extracting directory patterns"""
        patterns = await learner.extract_patterns(git_detection_python)

        # Find directory patterns
        dir_patterns = [p for p in patterns if p["type"] == "directory"]

        # Should have services/auth and tests
        dirs = {p["value"] for p in dir_patterns}
        assert "services/auth" in dirs
        assert "tests" in dirs

    @pytest.mark.asyncio
    async def test_extract_branch_prefix_pattern(self, learner, git_detection_python):
        """Test extracting branch prefix pattern"""
        patterns = await learner.extract_patterns(git_detection_python)

        # Find branch prefix patterns
        branch_patterns = [p for p in patterns if p["type"] == "branch_prefix"]

        assert len(branch_patterns) == 1
        assert branch_patterns[0]["value"] == "feature"
        assert branch_patterns[0]["context"]["full_branch"] == "feature/auth"

    @pytest.mark.asyncio
    async def test_extract_patterns_mixed_types(self, learner, git_detection_mixed):
        """Test pattern extraction with mixed file types"""
        patterns = await learner.extract_patterns(git_detection_mixed)

        # Should have .md and .py extensions
        ext_patterns = [p for p in patterns if p["type"] == "file_extension"]
        extensions = {p["value"] for p in ext_patterns}
        assert ".md" in extensions
        assert ".py" in extensions

        # Should have docs and services/api directories
        dir_patterns = [p for p in patterns if p["type"] == "directory"]
        directories = {p["value"] for p in dir_patterns}
        assert "docs" in directories
        assert "services/api" in directories

        # Should have "docs" branch prefix
        branch_patterns = [p for p in patterns if p["type"] == "branch_prefix"]
        assert branch_patterns[0]["value"] == "docs"

    @pytest.mark.asyncio
    async def test_extract_patterns_no_files(self, learner):
        """Test pattern extraction with no files"""
        git_detection = {
            "has_uncommitted": False,
            "branch": "main",
            "files": []
        }

        patterns = await learner.extract_patterns(git_detection)

        # Should have no file/directory patterns, but may have branch prefix
        # (depends on branch name format)
        assert isinstance(patterns, list)

    @pytest.mark.asyncio
    async def test_extract_patterns_no_branch_prefix(self, learner):
        """Test pattern extraction with branch without prefix"""
        git_detection = {
            "has_uncommitted": True,
            "branch": "main",  # No "/" in branch name
            "files": ["test.py"]
        }

        patterns = await learner.extract_patterns(git_detection)

        # Should have no branch_prefix pattern
        branch_patterns = [p for p in patterns if p["type"] == "branch_prefix"]
        assert len(branch_patterns) == 0


class TestPatternProbability:
    """Test suite for pattern probability calculation"""

    @pytest.fixture
    def learner(self):
        """Create PatternLearner instance"""
        return PatternLearner(workspace_id="/tmp/test_workspace")

    @pytest.mark.asyncio
    async def test_probability_caches_results(self, learner):
        """Test probability results are cached"""
        # First call
        prob1 = await learner.calculate_pattern_probability(
            "file_extension", ".py", lookback_days=90
        )

        # Second call should hit cache
        prob2 = await learner.calculate_pattern_probability(
            "file_extension", ".py", lookback_days=90
        )

        assert prob1 == prob2

        # Verify cache hit
        cache_key = "file_extension:.py:90"
        cached_data = learner.cache.get(cache_key)
        assert cached_data is not None
        assert "probability" in cached_data

    @pytest.mark.asyncio
    async def test_probability_different_lookback_periods(self, learner):
        """Test different lookback periods create separate cache entries"""
        prob_90 = await learner.calculate_pattern_probability(
            "file_extension", ".py", lookback_days=90
        )

        prob_30 = await learner.calculate_pattern_probability(
            "file_extension", ".py", lookback_days=30
        )

        # Should have separate cache entries
        assert learner.cache.get("file_extension:.py:90") is not None
        assert learner.cache.get("file_extension:.py:30") is not None


class TestConfidenceBoosting:
    """Test suite for confidence boosting based on patterns"""

    @pytest.fixture
    def learner(self):
        """Create PatternLearner instance"""
        return PatternLearner(workspace_id="/tmp/test_workspace")

    @pytest.fixture
    def git_detection(self):
        """Sample git detection"""
        return {
            "has_uncommitted": True,
            "branch": "feature/api",
            "files": [
                "services/api/routes.py",
                "services/api/handlers.py"
            ]
        }

    @pytest.mark.asyncio
    async def test_boost_returns_structure(self, learner, git_detection):
        """Test boost function returns correct structure"""
        result = await learner.suggest_based_on_patterns(git_detection)

        assert "boosted_confidence" in result
        assert "boost_applied" in result
        assert "matching_patterns" in result
        assert "explanation" in result

    @pytest.mark.asyncio
    async def test_boost_confidence_bounded(self, learner, git_detection):
        """Test boost confidence is capped at max"""
        result = await learner.suggest_based_on_patterns(
            git_detection,
            confidence_boost=0.15
        )

        # Boost should never exceed confidence_boost parameter
        assert result["boost_applied"] <= 0.15
        assert result["boosted_confidence"] <= 0.15


class TestTopPatterns:
    """Test suite for retrieving top patterns"""

    @pytest.fixture
    def learner(self):
        """Create PatternLearner instance"""
        return PatternLearner(workspace_id="/tmp/test_workspace")

    @pytest.mark.asyncio
    async def test_top_patterns_limit_enforced(self, learner):
        """Test ADHD limit of max 10 patterns"""
        # Request 20 patterns
        patterns = await learner.get_top_patterns("file_extension", limit=20)

        # Should return max 10 (ADHD limit)
        assert len(patterns) <= 10

    @pytest.mark.asyncio
    async def test_top_patterns_respects_limit(self, learner):
        """Test limit parameter is respected"""
        patterns_5 = await learner.get_top_patterns("file_extension", limit=5)
        assert len(patterns_5) <= 5

        patterns_3 = await learner.get_top_patterns("file_extension", limit=3)
        assert len(patterns_3) <= 3


class TestCacheStats:
    """Test suite for cache statistics"""

    @pytest.fixture
    def learner(self):
        """Create PatternLearner instance"""
        return PatternLearner(workspace_id="/tmp/test_workspace")

    def test_cache_stats_structure(self, learner):
        """Test cache stats return correct structure"""
        stats = learner.get_cache_stats()

        assert "size" in stats
        assert "max_size" in stats
        assert "utilization" in stats
        assert "total_accesses" in stats
        assert "avg_accesses_per_pattern" in stats

    def test_cache_stats_after_operations(self, learner):
        """Test cache stats reflect operations"""
        # Add some items to cache
        learner.cache.put("key1", {"data": "value1"})
        learner.cache.put("key2", {"data": "value2"})

        # Access items
        learner.cache.get("key1")
        learner.cache.get("key2")

        stats = learner.get_cache_stats()

        assert stats["size"] == 2
        assert stats["total_accesses"] == 2
        assert stats["utilization"] > 0


# === Integration Tests ===

@pytest.mark.integration
class TestPatternLearnerIntegration:
    """Integration tests for full pattern learning workflow"""

    @pytest.mark.asyncio
    async def test_full_pattern_learning_workflow(self):
        """Test complete pattern learning cycle"""
        learner = PatternLearner(workspace_id="/tmp/test_workspace")

        # Step 1: Extract patterns from detection
        git_detection = {
            "has_uncommitted": True,
            "branch": "feature/authentication",
            "files": [
                "services/auth/jwt.py",
                "services/auth/session.py",
                "services/auth/middleware.py",
                "tests/test_auth.py"
            ]
        }

        patterns = await learner.extract_patterns(git_detection)

        # Verify patterns extracted
        assert len(patterns) > 0

        # Step 2: Calculate pattern probabilities
        for pattern in patterns:
            if pattern["type"] == "file_extension":
                prob = await learner.calculate_pattern_probability(
                    pattern["type"],
                    pattern["value"]
                )
                assert 0.0 <= prob <= 1.0

        # Step 3: Get confidence boost
        boost_result = await learner.suggest_based_on_patterns(git_detection)
        assert boost_result["boost_applied"] >= 0.0

        # Step 4: Verify cache stats
        stats = learner.get_cache_stats()
        assert stats["size"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
