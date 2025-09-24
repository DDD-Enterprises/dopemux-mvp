"""
Unit tests for ADHD Workflow Optimizations.

Comprehensive test coverage for ADHD-specific task optimization and workflow management.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.config import Config
from utils.adhd_optimizations import (
    ADHDProfile,
    ADHDTaskOptimizer,
    AttentionState,
    CognitiveLoad,
    TaskComplexity,
    TaskOptimization,
    create_adhd_optimizer,
)


class TestAttentionState:
    """Test AttentionState enum."""

    def test_attention_state_values(self):
        """Test attention state enum values."""
        assert AttentionState.HYPERFOCUS.value == "hyperfocus"
        assert AttentionState.FOCUSED.value == "focused"
        assert AttentionState.SCATTERED.value == "scattered"
        assert AttentionState.OVERWHELMED.value == "overwhelmed"
        assert AttentionState.TRANSITIONING.value == "transitioning"


class TestCognitiveLoad:
    """Test CognitiveLoad enum."""

    def test_cognitive_load_values(self):
        """Test cognitive load enum values."""
        assert CognitiveLoad.MINIMAL.value == 1
        assert CognitiveLoad.LOW.value == 2
        assert CognitiveLoad.MODERATE.value == 3
        assert CognitiveLoad.HIGH.value == 4
        assert CognitiveLoad.MAXIMUM.value == 5


class TestTaskComplexity:
    """Test TaskComplexity enum."""

    def test_task_complexity_values(self):
        """Test task complexity enum values."""
        assert TaskComplexity.QUICK_WIN.value == "quick_win"
        assert TaskComplexity.FOCUSED_WORK.value == "focused_work"
        assert TaskComplexity.DEEP_WORK.value == "deep_work"
        assert TaskComplexity.COLLABORATIVE.value == "collaborative"
        assert TaskComplexity.CREATIVE.value == "creative"


class TestADHDProfile:
    """Test ADHDProfile dataclass."""

    def test_profile_creation_with_defaults(self):
        """Test creating profile with default values."""
        profile = ADHDProfile(user_id="test_user")

        assert profile.user_id == "test_user"
        assert profile.primary_attention_pattern == AttentionState.FOCUSED
        assert profile.optimal_focus_duration == 25
        assert profile.break_duration == 5
        assert profile.long_break_duration == 15
        assert profile.context_switch_buffer == 10
        assert profile.max_cognitive_load == CognitiveLoad.MODERATE
        assert profile.preferred_task_size == TaskComplexity.FOCUSED_WORK
        assert profile.notification_threshold == 3
        assert profile.distraction_sensitivity == 0.7
        assert profile.context_preservation_priority == 0.9

    def test_profile_creation_with_values(self):
        """Test creating profile with specific values."""
        time_preferences = {"9": 0.9, "10": 0.8, "11": 0.7}
        triggers = ["coding", "design"]
        drains = ["meetings", "noise"]
        patterns = ["morning_work", "deep_focus"]

        profile = ADHDProfile(
            user_id="custom_user",
            primary_attention_pattern=AttentionState.HYPERFOCUS,
            optimal_focus_duration=45,
            break_duration=10,
            max_cognitive_load=CognitiveLoad.HIGH,
            time_of_day_preference=time_preferences,
            hyperfocus_triggers=triggers,
            attention_drain_factors=drains,
            successful_patterns=patterns,
        )

        assert profile.user_id == "custom_user"
        assert profile.primary_attention_pattern == AttentionState.HYPERFOCUS
        assert profile.optimal_focus_duration == 45
        assert profile.break_duration == 10
        assert profile.max_cognitive_load == CognitiveLoad.HIGH
        assert profile.time_of_day_preference == time_preferences
        assert profile.hyperfocus_triggers == triggers
        assert profile.attention_drain_factors == drains
        assert profile.successful_patterns == patterns

    def test_profile_post_init_defaults(self):
        """Test profile post-init creates default values."""
        profile = ADHDProfile(user_id="test_user")

        # Check default time preferences were created
        assert isinstance(profile.time_of_day_preference, dict)
        assert len(profile.time_of_day_preference) == 24

        # Check default lists were created
        assert isinstance(profile.hyperfocus_triggers, list)
        assert len(profile.hyperfocus_triggers) > 0
        assert isinstance(profile.attention_drain_factors, list)
        assert len(profile.attention_drain_factors) > 0
        assert isinstance(profile.successful_patterns, list)
        assert len(profile.successful_patterns) > 0


class TestTaskOptimization:
    """Test TaskOptimization dataclass."""

    def test_optimization_creation_with_defaults(self):
        """Test creating optimization with default values."""
        optimization = TaskOptimization()

        assert optimization.cognitive_load_score == 3.0
        assert optimization.estimated_attention_duration == 25
        assert optimization.context_complexity == 0.5
        assert optimization.dependency_weight == 0.3
        assert isinstance(optimization.break_recommendations, list)
        assert isinstance(optimization.attention_anchors, list)
        assert isinstance(optimization.context_cues, list)
        assert isinstance(optimization.completion_rewards, list)
        assert isinstance(optimization.optimal_time_slots, list)
        assert isinstance(optimization.avoid_time_slots, list)

    def test_optimization_creation_with_values(self):
        """Test creating optimization with specific values."""
        break_recs = [{"type": "short", "duration": 5}]
        anchors = ["focus_point_1", "focus_point_2"]
        cues = ["context_cue_1"]
        rewards = ["celebration"]
        time_slots = [(9, 11), (14, 16)]
        avoid_slots = [(12, 13)]

        optimization = TaskOptimization(
            cognitive_load_score=4.5,
            estimated_attention_duration=60,
            context_complexity=0.8,
            dependency_weight=0.6,
            break_recommendations=break_recs,
            attention_anchors=anchors,
            context_cues=cues,
            completion_rewards=rewards,
            optimal_time_slots=time_slots,
            avoid_time_slots=avoid_slots,
        )

        assert optimization.cognitive_load_score == 4.5
        assert optimization.estimated_attention_duration == 60
        assert optimization.context_complexity == 0.8
        assert optimization.dependency_weight == 0.6
        assert optimization.break_recommendations == break_recs
        assert optimization.attention_anchors == anchors
        assert optimization.context_cues == cues
        assert optimization.completion_rewards == rewards
        assert optimization.optimal_time_slots == time_slots
        assert optimization.avoid_time_slots == avoid_slots

    def test_generate_break_recommendations(self):
        """Test break recommendation generation."""
        # Low cognitive load
        low_load = TaskOptimization(cognitive_load_score=2.0)
        assert len(low_load.break_recommendations) == 1
        assert low_load.break_recommendations[0]["type"] == "micro"

        # Medium cognitive load
        med_load = TaskOptimization(cognitive_load_score=3.0)
        assert len(med_load.break_recommendations) == 2
        assert any(rec["type"] == "short" for rec in med_load.break_recommendations)

        # High cognitive load
        high_load = TaskOptimization(cognitive_load_score=4.5)
        assert len(high_load.break_recommendations) == 3
        assert any(rec["type"] == "standard" for rec in high_load.break_recommendations)


class TestADHDTaskOptimizer:
    """Test ADHDTaskOptimizer functionality."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config(
            {
                "adhd": {
                    "cognitive_load_threshold": 0.8,
                    "attention_decay_rate": 0.05,
                    "context_switch_penalty": 0.2,
                }
            }
        )

    @pytest.fixture
    def optimizer(self, config):
        """Create test optimizer."""
        return ADHDTaskOptimizer(config)

    def test_optimizer_initialization(self, optimizer, config):
        """Test optimizer initialization."""
        assert optimizer.config == config
        assert optimizer.cognitive_load_threshold == 0.8
        assert optimizer.attention_decay_rate == 0.05
        assert optimizer.context_switch_penalty == 0.2
        assert isinstance(optimizer.adhd_profiles, dict)

    @pytest.mark.asyncio
    async def test_optimize_task_basic(self, optimizer):
        """Test basic task optimization."""
        # Mock task object
        task = MagicMock()
        task.headline = "Test Task"
        task.description = "Test description"
        task.complexity_score = None
        task.estimated_hours = None
        task.dependencies = []

        with patch.object(optimizer, "_get_adhd_profile") as mock_get_profile:
            with patch.object(optimizer, "_analyze_task_complexity") as mock_analyze:
                with patch.object(
                    optimizer, "_generate_task_optimization"
                ) as mock_generate:
                    with patch.object(optimizer, "_apply_optimizations") as mock_apply:
                        with patch.object(optimizer, "_log_optimization") as mock_log:
                            # Setup mocks
                            mock_profile = ADHDProfile("test_user")
                            mock_get_profile.return_value = mock_profile

                            mock_analysis = {
                                "cognitive_load": 3.0,
                                "attention_requirement": 25,
                            }
                            mock_analyze.return_value = mock_analysis

                            mock_optimization = TaskOptimization()
                            mock_generate.return_value = mock_optimization

                            mock_apply.return_value = task

                            # Run optimization
                            result = await optimizer.optimize_task(task, "test_user")

                            assert result == task
                            mock_get_profile.assert_called_once_with("test_user")
                            mock_analyze.assert_called_once_with(task)
                            mock_generate.assert_called_once()
                            mock_apply.assert_called_once()
                            mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_optimize_task_without_user(self, optimizer):
        """Test task optimization without user ID."""
        task = MagicMock()
        task.headline = "Test Task"

        with patch.object(
            optimizer, "_analyze_task_complexity", AsyncMock(return_value={})
        ):
            with patch.object(
                optimizer,
                "_generate_task_optimization",
                AsyncMock(return_value=TaskOptimization()),
            ):
                with patch.object(
                    optimizer, "_apply_optimizations", AsyncMock(return_value=task)
                ):
                    with patch.object(optimizer, "_log_optimization", AsyncMock()):
                        result = await optimizer.optimize_task(task)

                        assert result == task

    @pytest.mark.asyncio
    async def test_optimize_task_error_handling(self, optimizer):
        """Test task optimization error handling."""
        task = MagicMock()

        with patch.object(
            optimizer,
            "_analyze_task_complexity",
            AsyncMock(side_effect=Exception("Analysis error")),
        ):
            result = await optimizer.optimize_task(task)

            # Should return original task on error
            assert result == task

    @pytest.mark.asyncio
    async def test_optimize_taskmaster_task(self, optimizer):
        """Test TaskMaster task optimization."""
        # Mock TaskMaster task
        tm_task = MagicMock()
        tm_task.complexity_score = 4.5
        tm_task.estimated_hours = 3.0
        tm_task.priority = 1
        tm_task.tags = []
        tm_task.ai_analysis = {}

        result = await optimizer.optimize_taskmaster_task(tm_task)

        assert result == tm_task
        assert "deep_work" in tm_task.tags
        assert "hyperfocus_required" in tm_task.tags
        assert "adhd_optimization" in tm_task.ai_analysis

    @pytest.mark.asyncio
    async def test_optimize_taskmaster_task_low_complexity(self, optimizer):
        """Test TaskMaster task optimization for low complexity."""
        tm_task = MagicMock()
        tm_task.complexity_score = 1.5
        tm_task.estimated_hours = 0.5
        tm_task.priority = 3
        tm_task.tags = []
        tm_task.ai_analysis = {}

        await optimizer.optimize_taskmaster_task(tm_task)

        assert "quick_win" in tm_task.tags
        assert "adhd_optimization" in tm_task.ai_analysis

    @pytest.mark.asyncio
    async def test_optimize_taskmaster_task_error_handling(self, optimizer):
        """Test TaskMaster task optimization error handling."""
        tm_task = MagicMock()

        # Simulate error during optimization
        with patch.object(
            optimizer, "_calculate_break_frequency", side_effect=Exception("Error")
        ):
            result = await optimizer.optimize_taskmaster_task(tm_task)

            # Should return original task on error
            assert result == tm_task

    @pytest.mark.asyncio
    async def test_schedule_optimal_sequence(self, optimizer):
        """Test optimal task sequence scheduling."""
        tasks = [
            MagicMock(id=1, headline="Task 1"),
            MagicMock(id=2, headline="Task 2"),
            MagicMock(id=3, headline="Task 3"),
        ]

        with patch.object(optimizer, "_get_adhd_profile") as mock_get_profile:
            with patch.object(optimizer, "_analyze_task_complexity") as mock_analyze:
                with patch.object(optimizer, "_sort_tasks_for_adhd") as mock_sort:
                    with patch.object(
                        optimizer, "_create_adhd_schedule"
                    ) as mock_create:
                        # Setup mocks
                        mock_profile = ADHDProfile("test_user")
                        mock_get_profile.return_value = mock_profile

                        mock_analyze.return_value = {
                            "cognitive_load": 3.0,
                            "estimated_duration": 30,
                        }

                        task_analyses = [
                            (task, {"cognitive_load": 3.0}) for task in tasks
                        ]
                        mock_sort.return_value = task_analyses

                        expected_schedule = [
                            {
                                "type": "task",
                                "task": tasks[0],
                                "start_time": 0,
                                "duration": 30,
                            }
                        ]
                        mock_create.return_value = expected_schedule

                        # Run scheduling
                        result = await optimizer.schedule_optimal_sequence(
                            tasks, "test_user", 480
                        )

                        assert result == expected_schedule
                        mock_get_profile.assert_called_once_with("test_user")
                        assert mock_analyze.call_count == len(tasks)
                        mock_sort.assert_called_once()
                        mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_schedule_optimal_sequence_error_handling(self, optimizer):
        """Test task scheduling error handling."""
        tasks = [MagicMock()]

        with patch.object(
            optimizer,
            "_analyze_task_complexity",
            AsyncMock(side_effect=Exception("Error")),
        ):
            result = await optimizer.schedule_optimal_sequence(tasks)

            # Should return simple fallback schedule
            assert len(result) == 1
            assert result[0]["task"] == tasks[0]

    @pytest.mark.asyncio
    async def test_detect_attention_state_default(self, optimizer):
        """Test attention state detection with default pattern."""
        with patch.object(optimizer, "_get_adhd_profile") as mock_get_profile:
            mock_profile = ADHDProfile("test_user")
            mock_profile.primary_attention_pattern = AttentionState.FOCUSED
            mock_get_profile.return_value = mock_profile

            state = await optimizer.detect_attention_state("test_user")

            assert state == AttentionState.FOCUSED

    @pytest.mark.asyncio
    async def test_detect_attention_state_with_activity(self, optimizer):
        """Test attention state detection with activity data."""
        activity = [
            {"type": "task_switch", "timestamp": datetime.now()},
            {"type": "focus_session", "duration": 60},
        ]

        with patch.object(optimizer, "_get_adhd_profile") as mock_get_profile:
            with patch.object(
                optimizer, "_analyze_attention_indicators"
            ) as mock_analyze:
                with patch.object(
                    optimizer, "_classify_attention_state"
                ) as mock_classify:
                    with patch.object(
                        optimizer, "_update_attention_pattern"
                    ) as mock_update:
                        mock_profile = ADHDProfile("test_user")
                        mock_get_profile.return_value = mock_profile

                        mock_indicators = {"focus_duration": 60, "task_switches": 1}
                        mock_analyze.return_value = mock_indicators

                        mock_classify.return_value = AttentionState.HYPERFOCUS
                        mock_update.return_value = None

                        state = await optimizer.detect_attention_state(
                            "test_user", activity
                        )

                        assert state == AttentionState.HYPERFOCUS
                        mock_analyze.assert_called_once_with(activity)
                        mock_classify.assert_called_once_with(
                            mock_indicators, mock_profile
                        )
                        mock_update.assert_called_once_with(
                            "test_user", AttentionState.HYPERFOCUS
                        )

    @pytest.mark.asyncio
    async def test_detect_attention_state_error_handling(self, optimizer):
        """Test attention state detection error handling."""
        with patch.object(
            optimizer, "_get_adhd_profile", AsyncMock(side_effect=Exception("Error"))
        ):
            state = await optimizer.detect_attention_state("test_user")

            # Should return safe default
            assert state == AttentionState.FOCUSED

    @pytest.mark.asyncio
    async def test_generate_context_preservation(self, optimizer):
        """Test context preservation generation."""
        context = {
            "task_name": "Test Task",
            "project": "Test Project",
            "current_state": "working",
        }

        with patch.object(optimizer, "_get_adhd_profile") as mock_get_profile:
            with patch.object(optimizer, "_generate_context_summary") as mock_summary:
                with patch.object(optimizer, "_capture_mental_model") as mock_mental:
                    with patch.object(
                        optimizer, "_extract_decision_trail"
                    ) as mock_decisions:
                        with patch.object(
                            optimizer, "_identify_attention_anchors"
                        ) as mock_anchors:
                            with patch.object(
                                optimizer, "_generate_continuation_cues"
                            ) as mock_cues:
                                with patch.object(
                                    optimizer, "_create_restoration_steps"
                                ) as mock_steps:
                                    with patch.object(
                                        optimizer, "_store_context_preservation"
                                    ) as mock_store:
                                        # Setup mocks
                                        mock_profile = ADHDProfile("test_user")
                                        mock_get_profile.return_value = mock_profile
                                        mock_summary.return_value = "Context summary"
                                        mock_mental.return_value = {
                                            "concepts": ["concept1"]
                                        }
                                        mock_decisions.return_value = [
                                            {"decision": "choice1"}
                                        ]
                                        mock_anchors.return_value = ["anchor1"]
                                        mock_cues.return_value = ["cue1"]
                                        mock_steps.return_value = ["step1"]

                                        result = await optimizer.generate_context_preservation(
                                            "test_user", context
                                        )

                                        assert result["user_id"] == "test_user"
                                        assert (
                                            result["context_summary"]
                                            == "Context summary"
                                        )
                                        assert result["mental_model"] == {
                                            "concepts": ["concept1"]
                                        }
                                        assert result["attention_anchors"] == [
                                            "anchor1"
                                        ]
                                        mock_store.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_context_preservation_error_handling(self, optimizer):
        """Test context preservation error handling."""
        with patch.object(
            optimizer, "_get_adhd_profile", AsyncMock(side_effect=Exception("Error"))
        ):
            result = await optimizer.generate_context_preservation("test_user", {})

            assert "error" in result
            assert "Error" in result["error"]

    @pytest.mark.asyncio
    async def test_restore_context_with_data(self, optimizer):
        """Test context restoration with preservation data."""
        preservation_data = {
            "timestamp": datetime.now().isoformat(),
            "context_summary": "Previous work summary",
            "restoration_steps": ["Step 1", "Step 2"],
            "attention_anchors": ["Anchor 1"],
            "continuation_cues": ["Cue 1"],
        }

        with patch.object(optimizer, "_get_adhd_profile") as mock_get_profile:
            with patch.object(optimizer, "_calculate_context_age") as mock_age:
                with patch.object(
                    optimizer, "_generate_restoration_recommendations"
                ) as mock_recs:
                    mock_profile = ADHDProfile("test_user")
                    mock_get_profile.return_value = mock_profile
                    mock_age.return_value = "30 minutes ago"
                    mock_recs.return_value = ["Recommendation 1"]

                    result = await optimizer.restore_context(
                        "test_user", preservation_data
                    )

                    assert result["status"] == "ready"
                    assert result["context_age"] == "30 minutes ago"
                    assert result["summary"] == "Previous work summary"
                    assert result["orientation_steps"] == ["Step 1", "Step 2"]

    @pytest.mark.asyncio
    async def test_restore_context_no_data(self, optimizer):
        """Test context restoration with no data."""
        with patch.object(
            optimizer, "_retrieve_latest_context", AsyncMock(return_value=None)
        ):
            result = await optimizer.restore_context("test_user")

            assert result["status"] == "no_context"
            assert "No preserved context found" in result["message"]

    @pytest.mark.asyncio
    async def test_restore_context_error_handling(self, optimizer):
        """Test context restoration error handling."""
        with patch.object(
            optimizer,
            "_retrieve_latest_context",
            AsyncMock(side_effect=Exception("Error")),
        ):
            result = await optimizer.restore_context("test_user")

            assert result["status"] == "error"
            assert "Error" in result["error"]

    @pytest.mark.asyncio
    async def test_get_adhd_profile_existing(self, optimizer):
        """Test getting existing ADHD profile."""
        profile = ADHDProfile("test_user")
        optimizer.adhd_profiles["test_user"] = profile

        result = await optimizer._get_adhd_profile("test_user")

        assert result == profile

    @pytest.mark.asyncio
    async def test_get_adhd_profile_new(self, optimizer):
        """Test getting new ADHD profile."""
        with patch.object(
            optimizer, "_load_profile_data", AsyncMock(return_value=None)
        ):
            with patch.object(optimizer, "_save_profile_data", AsyncMock()):
                result = await optimizer._get_adhd_profile("new_user")

                assert result.user_id == "new_user"
                assert "new_user" in optimizer.adhd_profiles

    @pytest.mark.asyncio
    async def test_get_adhd_profile_from_storage(self, optimizer):
        """Test getting ADHD profile from storage."""
        profile_data = {
            "user_id": "stored_user",
            "optimal_focus_duration": 45,
            "break_duration": 10,
        }

        with patch.object(
            optimizer, "_load_profile_data", AsyncMock(return_value=profile_data)
        ):
            result = await optimizer._get_adhd_profile("stored_user")

            assert result.user_id == "stored_user"
            assert result.optimal_focus_duration == 45
            assert result.break_duration == 10

    @pytest.mark.asyncio
    async def test_analyze_task_complexity_basic(self, optimizer):
        """Test basic task complexity analysis."""
        task = MagicMock()
        task.complexity_score = 3.5
        task.estimated_hours = 2.0
        task.dependencies = ["dep1", "dep2"]
        task.description = "Simple task description"

        analysis = await optimizer._analyze_task_complexity(task)

        assert analysis["cognitive_load"] == 3.5
        assert analysis["estimated_duration"] == 120  # 2 hours in minutes
        assert analysis["attention_requirement"] == 120
        assert analysis["dependency_count"] == 2
        assert analysis["context_complexity"] == 0.4  # 2 * 0.2

    @pytest.mark.asyncio
    async def test_analyze_task_complexity_with_description_indicators(self, optimizer):
        """Test task complexity analysis with description indicators."""
        # Complex task
        complex_task = MagicMock()
        complex_task.complexity_score = 3.0
        complex_task.estimated_hours = None
        complex_task.dependencies = []
        complex_task.description = (
            "Integrate complex algorithm and refactor architecture"
        )

        analysis = await optimizer._analyze_task_complexity(complex_task)
        assert (
            analysis["cognitive_load"] >= 3.5
        )  # Should increase due to complex indicators

        # Simple task
        simple_task = MagicMock()
        simple_task.complexity_score = 3.0
        simple_task.estimated_hours = None
        simple_task.dependencies = []
        simple_task.description = "Fix small bug and update documentation"

        analysis = await optimizer._analyze_task_complexity(simple_task)
        assert (
            analysis["cognitive_load"] <= 2.5
        )  # Should decrease due to simple indicators

    @pytest.mark.asyncio
    async def test_analyze_task_complexity_error_handling(self, optimizer):
        """Test task complexity analysis error handling."""
        task = MagicMock()
        task.complexity_score = None
        task.estimated_hours = None
        task.dependencies = []

        # Mock an error in attribute access
        with patch.object(
            task, "description", side_effect=Exception("Attribute error")
        ):
            analysis = await optimizer._analyze_task_complexity(task)

            # Should return default values despite error
            assert analysis["cognitive_load"] == 3.0
            assert analysis["estimated_duration"] == 30

    def test_calculate_break_frequency(self, optimizer):
        """Test break frequency calculation."""
        assert (
            optimizer._calculate_break_frequency(10) == 0
        )  # No breaks for short tasks
        assert optimizer._calculate_break_frequency(25) == 25  # Standard Pomodoro
        assert (
            optimizer._calculate_break_frequency(45) == 20
        )  # More frequent for medium tasks
        assert (
            optimizer._calculate_break_frequency(90) == 15
        )  # Very frequent for long tasks

    def test_get_optimal_scheduling(self, optimizer):
        """Test optimal scheduling recommendations."""
        assert optimizer._get_optimal_scheduling(4.5) == "morning_deep_work"
        assert optimizer._get_optimal_scheduling(3.5) == "high_energy_periods"
        assert optimizer._get_optimal_scheduling(2.0) == "flexible_scheduling"

    def test_get_context_tips(self, optimizer):
        """Test context preservation tips generation."""
        # Task without dependencies
        simple_task = MagicMock()
        simple_task.dependencies = []
        simple_task.complexity_score = 2.0

        tips = optimizer._get_context_tips(simple_task)
        assert len(tips) >= 2
        assert any("Write down your current approach" in tip for tip in tips)

        # Task with dependencies
        complex_task = MagicMock()
        complex_task.dependencies = ["dep1", "dep2"]
        complex_task.complexity_score = 4.5

        tips = optimizer._get_context_tips(complex_task)
        assert any("relationships between this task" in tip for tip in tips)
        assert any("Break this complex task" in tip for tip in tips)

    @pytest.mark.asyncio
    async def test_generate_attention_anchors(self, optimizer):
        """Test attention anchors generation."""
        task = MagicMock()
        task.description = "Implement authentication system with JWT tokens"
        task.headline = None

        analysis = {"cognitive_load": 4.0, "dependency_count": 1}

        anchors = await optimizer._generate_attention_anchors(task, analysis)

        assert "complex_problem_solving" in anchors  # Due to high cognitive load
        assert "dependency_management" in anchors  # Due to dependencies
        assert len(anchors) <= 5  # Limited to 5 anchors

    @pytest.mark.asyncio
    async def test_generate_context_cues(self, optimizer):
        """Test context cues generation."""
        task = MagicMock()
        task.project_id = 123

        analysis = {"cognitive_load": 4.0}
        profile = ADHDProfile("test_user")

        cues = await optimizer._generate_context_cues(task, analysis, profile)

        assert any("Started at" in cue for cue in cues)
        assert any("Deep work mode" in cue for cue in cues)  # High cognitive load
        assert any("Part of project 123" in cue for cue in cues)

    @pytest.mark.asyncio
    async def test_generate_completion_rewards(self, optimizer):
        """Test completion rewards generation."""
        task = MagicMock()
        profile = ADHDProfile("test_user")
        profile.successful_patterns = ["celebration"]

        rewards = await optimizer._generate_completion_rewards(task, profile)

        assert "Check off the completed task" in rewards
        assert "Take a victory break" in rewards
        assert "Celebrate the achievement" in rewards  # Due to successful pattern

    @pytest.mark.asyncio
    async def test_calculate_optimal_timing(self, optimizer):
        """Test optimal timing calculation."""
        profile = ADHDProfile("test_user")
        profile.time_of_day_preference = {
            "9": 0.9,
            "10": 0.8,
            "11": 0.7,  # High productivity hours
            "14": 0.6,
            "15": 0.5,  # Lower productivity hours
        }

        # High cognitive load - needs peak times
        high_load_slots = await optimizer._calculate_optimal_timing(4.5, profile)
        assert (9, 11) in high_load_slots  # Should include peak hours

        # Low cognitive load - flexible
        low_load_slots = await optimizer._calculate_optimal_timing(1.5, profile)
        assert len(low_load_slots) == 0  # No specific timing needed

    @pytest.mark.asyncio
    async def test_sort_tasks_for_adhd(self, optimizer):
        """Test ADHD-optimal task sorting."""
        task1 = MagicMock()
        task2 = MagicMock()
        task3 = MagicMock()

        task_analyses = [
            (
                task1,
                {
                    "estimated_duration": 60,
                    "cognitive_load": 4.0,
                    "context_complexity": 0.8,
                    "dependency_count": 3,
                },
            ),
            (
                task2,
                {
                    "estimated_duration": 10,
                    "cognitive_load": 1.0,
                    "context_complexity": 0.1,
                    "dependency_count": 0,
                },
            ),
            (
                task3,
                {
                    "estimated_duration": 30,
                    "cognitive_load": 3.0,
                    "context_complexity": 0.3,
                    "dependency_count": 1,
                },
            ),
        ]

        profile = ADHDProfile("test_user")

        sorted_tasks = await optimizer._sort_tasks_for_adhd(task_analyses, profile)

        # Quick wins (task2) should be first
        assert sorted_tasks[0][0] == task2
        # Moderate complexity (task3) should be second
        assert sorted_tasks[1][0] == task3
        # Complex tasks (task1) should be last
        assert sorted_tasks[2][0] == task1

    @pytest.mark.asyncio
    async def test_create_adhd_schedule(self, optimizer):
        """Test ADHD-accommodated schedule creation."""
        task1 = MagicMock()
        task2 = MagicMock()

        sorted_tasks = [
            (task1, {"estimated_duration": 20, "cognitive_load": 2.0}),
            (task2, {"estimated_duration": 45, "cognitive_load": 4.0}),
        ]

        profile = ADHDProfile("test_user")
        profile.optimal_focus_duration = 25
        profile.break_duration = 5
        profile.context_switch_buffer = 10

        schedule = await optimizer._create_adhd_schedule(sorted_tasks, profile, 480)

        assert len(schedule) > 0

        # First task should be at time 0
        first_task_entry = next(
            entry
            for entry in schedule
            if entry["type"] == "task" and entry["task"] == task1
        )
        assert first_task_entry["start_time"] == 0

        # Should have breaks and buffers
        assert any(entry["type"] == "break" for entry in schedule)

    @pytest.mark.asyncio
    async def test_classify_attention_state(self, optimizer):
        """Test attention state classification."""
        profile = ADHDProfile("test_user")

        # Hyperfocus indicators
        hyperfocus_indicators = {"focus_duration": 90, "task_switches": 1}
        state = await optimizer._classify_attention_state(
            hyperfocus_indicators, profile
        )
        assert state == AttentionState.HYPERFOCUS

        # Scattered indicators
        scattered_indicators = {"focus_duration": 15, "task_switches": 8}
        state = await optimizer._classify_attention_state(scattered_indicators, profile)
        assert state == AttentionState.SCATTERED

        # Focused indicators
        focused_indicators = {"focus_duration": 30, "task_switches": 2}
        state = await optimizer._classify_attention_state(focused_indicators, profile)
        assert state == AttentionState.FOCUSED

    def test_calculate_context_age(self, optimizer):
        """Test context age calculation."""
        now = datetime.now()

        # Recent context (minutes)
        recent_data = {"timestamp": (now - timedelta(minutes=30)).isoformat()}
        age = optimizer._calculate_context_age(recent_data)
        assert "minutes ago" in age

        # Older context (hours)
        older_data = {"timestamp": (now - timedelta(hours=3)).isoformat()}
        age = optimizer._calculate_context_age(older_data)
        assert "hours ago" in age

        # Very old context (days)
        old_data = {"timestamp": (now - timedelta(days=2)).isoformat()}
        age = optimizer._calculate_context_age(old_data)
        assert "days ago" in age

    @pytest.mark.asyncio
    async def test_generate_restoration_recommendations(self, optimizer):
        """Test restoration recommendations generation."""
        profile = ADHDProfile("test_user")

        # Recent context
        recent_data = {
            "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat()
        }
        recs = await optimizer._generate_restoration_recommendations(
            recent_data, profile
        )
        assert len(recs) >= 3
        assert all(isinstance(rec, str) for rec in recs)

        # Old context
        old_data = {"timestamp": (datetime.now() - timedelta(hours=5)).isoformat()}
        recs = await optimizer._generate_restoration_recommendations(old_data, profile)
        assert any("extra time to re-familiarize" in rec for rec in recs)


class TestFactoryFunction:
    """Test factory function."""

    def test_create_adhd_optimizer(self):
        """Test factory function."""
        config = Config({"adhd": {"cognitive_load_threshold": 0.9}})

        optimizer = create_adhd_optimizer(config)

        assert isinstance(optimizer, ADHDTaskOptimizer)
        assert optimizer.config == config
        assert optimizer.cognitive_load_threshold == 0.9


if __name__ == "__main__":
    pytest.main(
        [__file__, "-v", "--cov=utils.adhd_optimizations", "--cov-report=term-missing"]
    )
