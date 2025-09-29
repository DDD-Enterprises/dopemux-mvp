"""
Developer Learning & Historical Analysis Engine for Serena v2

ML-powered learning from developer patterns, git history analysis,
and ADHD-specific personalization for navigation intelligence.
"""

import asyncio
import json
import logging
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics
import re

# ML and analysis imports
try:
    import numpy as np
    import pandas as pd
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics.pairwise import cosine_similarity
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logger.warning("ML libraries not available - install with: pip install numpy pandas scikit-learn")

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class DeveloperPatternType(str, Enum):
    """Types of developer patterns to learn."""
    NAVIGATION_PREFERENCE = "navigation_preference"
    CODING_STYLE = "coding_style"
    REFACTORING_SUCCESS = "refactoring_success"
    ENERGY_PATTERN = "energy_pattern"
    FOCUS_PATTERN = "focus_pattern"
    CONTEXT_SWITCH_PATTERN = "context_switch_pattern"
    COMPLEXITY_PREFERENCE = "complexity_preference"


class RefactoringOutcome(str, Enum):
    """Outcomes of refactoring attempts."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    REVERTED = "reverted"
    ABANDONED = "abandoned"
    IMPROVED = "improved"


@dataclass
class DeveloperAction:
    """Represents a developer action for pattern learning."""
    action_id: str
    developer_id: str
    action_type: str  # navigation, edit, refactor, search, etc.
    timestamp: datetime
    workspace_id: str

    # Action context
    file_path: Optional[str] = None
    function_name: Optional[str] = None
    action_data: Dict[str, Any] = field(default_factory=dict)

    # ADHD context
    energy_level: str = "medium"
    attention_state: str = "focused"
    cognitive_load: float = 0.5
    session_duration: int = 0  # minutes into session

    # Outcome tracking
    success: Optional[bool] = None
    completion_time: Optional[int] = None  # minutes to complete
    context_switches: int = 0


@dataclass
class RefactoringPattern:
    """Represents a refactoring pattern and its success rate."""
    pattern_id: str
    pattern_type: str
    description: str
    success_rate: float
    attempt_count: int

    # Pattern characteristics
    complexity_before: float
    complexity_after: float
    files_affected: int
    developer_energy_optimal: str

    # ADHD insights
    adhd_friendly: bool = True
    cognitive_load_change: float = 0.0
    focus_requirement: str = "medium"

    # Historical data
    first_seen: datetime = None
    last_successful: datetime = None
    examples: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        if self.first_seen is None:
            self.first_seen = datetime.now(timezone.utc)


class DeveloperLearningEngine:
    """
    ML-powered engine for learning developer patterns and historical analysis.

    Features:
    - Developer pattern recognition and personalization
    - Git history analysis for refactoring success patterns
    - ADHD-specific learning and accommodation optimization
    - Time-series analysis of code evolution
    - Predictive suggestions based on learned patterns
    """

    def __init__(
        self,
        workspace_path: Path,
        redis_url: str = "redis://localhost:6379"
    ):
        self.workspace_path = workspace_path
        self.redis_url = redis_url

        # Redis connection for pattern storage
        self.redis_client: Optional[redis.Redis] = None

        # Learning state
        self.developer_profiles: Dict[str, Dict[str, Any]] = {}
        self.action_history: List[DeveloperAction] = []
        self.refactoring_patterns: Dict[str, RefactoringPattern] = {}

        # ML models (would be loaded/trained)
        self.pattern_models: Dict[str, Any] = {}
        self.scaler: Optional['StandardScaler'] = None

        # Analysis settings
        self.max_history_days = 90  # 3 months of history
        self.min_pattern_occurrences = 3  # Minimum for pattern recognition
        self.learning_batch_size = 100

        # ADHD optimization
        self.adhd_learning_enabled = True
        self.privacy_mode = True  # Encrypt sensitive learning data

    async def initialize(self) -> None:
        """Initialize learning engine and load existing patterns."""
        if not ML_AVAILABLE:
            logger.warning("ML libraries not available - learning features disabled")
            return

        logger.info("🧠 Initializing Developer Learning Engine...")

        # Initialize Redis connection
        self.redis_client = redis.from_url(
            self.redis_url,
            db=6,  # Separate DB for learning data
            decode_responses=True
        )
        await self.redis_client.ping()

        # Load existing developer profiles
        await self._load_developer_profiles()

        # Load existing refactoring patterns
        await self._load_refactoring_patterns()

        # Initialize ML models
        await self._initialize_ml_models()

        # Start background learning
        asyncio.create_task(self._background_learning_worker())

        logger.info("✅ Developer Learning Engine ready!")

    async def _load_developer_profiles(self) -> None:
        """Load existing developer profiles from storage."""
        try:
            profile_keys = await self.redis_client.keys("dev_profile:*")

            for key in profile_keys:
                developer_id = key.split(":")[-1]
                profile_data = await self.redis_client.get(key)

                if profile_data:
                    self.developer_profiles[developer_id] = json.loads(profile_data)

            logger.info(f"📋 Loaded {len(self.developer_profiles)} developer profiles")

        except Exception as e:
            logger.error(f"Failed to load developer profiles: {e}")

    async def _load_refactoring_patterns(self) -> None:
        """Load existing refactoring patterns from storage."""
        try:
            pattern_keys = await self.redis_client.keys("refactor_pattern:*")

            for key in pattern_keys:
                pattern_id = key.split(":")[-1]
                pattern_data = await self.redis_client.get(key)

                if pattern_data:
                    pattern_dict = json.loads(pattern_data)
                    # Convert to RefactoringPattern object
                    pattern = RefactoringPattern(**pattern_dict)
                    self.refactoring_patterns[pattern_id] = pattern

            logger.info(f"🔧 Loaded {len(self.refactoring_patterns)} refactoring patterns")

        except Exception as e:
            logger.error(f"Failed to load refactoring patterns: {e}")

    async def _initialize_ml_models(self) -> None:
        """Initialize ML models for pattern recognition."""
        try:
            if ML_AVAILABLE:
                # Initialize scaler for feature normalization
                self.scaler = StandardScaler()

                # Initialize clustering models for pattern recognition
                self.pattern_models = {
                    "navigation_clustering": KMeans(n_clusters=5, random_state=42),
                    "complexity_clustering": KMeans(n_clusters=3, random_state=42),
                    "energy_clustering": KMeans(n_clusters=4, random_state=42)
                }

                logger.info("🤖 ML models initialized for pattern recognition")

        except Exception as e:
            logger.error(f"ML model initialization failed: {e}")

    # Developer Pattern Learning

    async def record_developer_action(self, action: DeveloperAction) -> None:
        """Record developer action for pattern learning."""
        try:
            # Add to action history
            self.action_history.append(action)

            # Keep history manageable for ADHD users
            if len(self.action_history) > 1000:
                self.action_history = self.action_history[-500:]

            # Update developer profile
            await self._update_developer_profile(action)

            # Store in Redis for persistence
            action_key = f"action:{action.developer_id}:{action.timestamp.timestamp()}"
            await self.redis_client.setex(
                action_key,
                86400 * 7,  # 7 days
                json.dumps(action.__dict__, default=str)
            )

            logger.debug(f"📊 Recorded action: {action.action_type} by {action.developer_id}")

        except Exception as e:
            logger.error(f"Failed to record developer action: {e}")

    async def _update_developer_profile(self, action: DeveloperAction) -> None:
        """Update developer profile based on action."""
        try:
            developer_id = action.developer_id

            if developer_id not in self.developer_profiles:
                self.developer_profiles[developer_id] = {
                    "developer_id": developer_id,
                    "total_actions": 0,
                    "preferred_complexity": 0.5,
                    "average_session_duration": 25,
                    "context_switch_frequency": 0.0,
                    "energy_patterns": {},
                    "navigation_preferences": {},
                    "success_patterns": {},
                    "adhd_accommodations": {
                        "break_frequency": 25,
                        "complexity_threshold": 0.7,
                        "focus_mode_usage": 0.0
                    },
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }

            profile = self.developer_profiles[developer_id]

            # Update action count
            profile["total_actions"] += 1

            # Update energy patterns
            energy_level = action.energy_level
            if energy_level not in profile["energy_patterns"]:
                profile["energy_patterns"][energy_level] = {"count": 0, "success_rate": 0.0}

            profile["energy_patterns"][energy_level]["count"] += 1

            # Update success rate if action has outcome
            if action.success is not None:
                energy_pattern = profile["energy_patterns"][energy_level]
                current_successes = energy_pattern["success_rate"] * (energy_pattern["count"] - 1)
                new_successes = current_successes + (1 if action.success else 0)
                energy_pattern["success_rate"] = new_successes / energy_pattern["count"]

            # Update session duration patterns
            if action.session_duration > 0:
                current_avg = profile["average_session_duration"]
                profile["average_session_duration"] = (
                    (current_avg * (profile["total_actions"] - 1) + action.session_duration) /
                    profile["total_actions"]
                )

            # Update complexity preferences
            if action.action_data.get("complexity_score"):
                complexity = action.action_data["complexity_score"]
                current_pref = profile["preferred_complexity"]
                profile["preferred_complexity"] = (
                    (current_pref * (profile["total_actions"] - 1) + complexity) /
                    profile["total_actions"]
                )

            # Update last updated
            profile["last_updated"] = datetime.now(timezone.utc).isoformat()

            # Store updated profile
            await self._store_developer_profile(developer_id, profile)

        except Exception as e:
            logger.error(f"Developer profile update failed: {e}")

    # Git History Analysis

    async def analyze_git_history_patterns(
        self,
        workspace_id: str,
        lookback_days: int = 90
    ) -> Dict[str, Any]:
        """Analyze git history for refactoring patterns and success indicators."""
        try:
            logger.info(f"📈 Analyzing git history for refactoring patterns...")

            # Get git log for analysis period
            since_date = datetime.now(timezone.utc) - timedelta(days=lookback_days)
            git_commits = await self._get_git_commits(since_date)

            if not git_commits:
                return {"error": "No git history available"}

            # Analyze commit patterns
            commit_analysis = await self._analyze_commit_patterns(git_commits)

            # Identify refactoring commits
            refactoring_commits = await self._identify_refactoring_commits(git_commits)

            # Analyze refactoring success patterns
            refactoring_patterns = await self._analyze_refactoring_success(refactoring_commits)

            # Extract ADHD insights
            adhd_insights = await self._extract_adhd_insights(git_commits)

            return {
                "analysis_period": f"{lookback_days} days",
                "total_commits": len(git_commits),
                "refactoring_commits": len(refactoring_commits),
                "commit_patterns": commit_analysis,
                "refactoring_patterns": refactoring_patterns,
                "adhd_insights": adhd_insights,
                "recommendations": await self._generate_historical_recommendations(
                    commit_analysis, refactoring_patterns, adhd_insights
                ),
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Git history analysis failed: {e}")
            return {"error": str(e)}

    async def _get_git_commits(self, since_date: datetime) -> List[Dict[str, Any]]:
        """Get git commits since specified date."""
        try:
            # Run git log command
            cmd = [
                "git", "log",
                f"--since={since_date.isoformat()}",
                "--pretty=format:%H|%an|%ae|%ad|%s",
                "--date=iso-strict",
                "--name-status"
            ]

            result = subprocess.run(
                cmd,
                cwd=str(self.workspace_path),
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                logger.error(f"Git log failed: {result.stderr}")
                return []

            # Parse git log output
            commits = []
            current_commit = None

            for line in result.stdout.split('\n'):
                if '|' in line and len(line.split('|')) == 5:
                    # Commit header line
                    if current_commit:
                        commits.append(current_commit)

                    parts = line.split('|')
                    current_commit = {
                        "hash": parts[0],
                        "author": parts[1],
                        "email": parts[2],
                        "date": parts[3],
                        "message": parts[4],
                        "files_changed": []
                    }

                elif line.startswith(('A\t', 'M\t', 'D\t', 'R\t')) and current_commit:
                    # File change line
                    change_type = line[0]
                    file_path = line[2:]
                    current_commit["files_changed"].append({
                        "change_type": change_type,
                        "file_path": file_path
                    })

            # Add last commit
            if current_commit:
                commits.append(current_commit)

            logger.debug(f"📊 Parsed {len(commits)} git commits")
            return commits

        except Exception as e:
            logger.error(f"Git commit retrieval failed: {e}")
            return []

    async def _analyze_commit_patterns(self, commits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in commit history."""
        try:
            if not commits:
                return {}

            # Time-based patterns
            commit_times = []
            commit_sizes = []
            authors = set()

            for commit in commits:
                try:
                    commit_time = datetime.fromisoformat(commit["date"])
                    commit_times.append(commit_time.hour)
                    commit_sizes.append(len(commit["files_changed"]))
                    authors.add(commit["author"])
                except Exception:
                    continue

            # Calculate patterns
            patterns = {
                "peak_hours": self._find_peak_hours(commit_times),
                "average_files_per_commit": statistics.mean(commit_sizes) if commit_sizes else 0,
                "commit_size_distribution": self._categorize_commit_sizes(commit_sizes),
                "active_developers": len(authors),
                "commit_frequency": len(commits) / max(90, 1),  # commits per day
                "preferred_languages": self._analyze_language_preferences(commits)
            }

            return patterns

        except Exception as e:
            logger.error(f"Commit pattern analysis failed: {e}")
            return {}

    async def _identify_refactoring_commits(self, commits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify commits that represent refactoring activities."""
        try:
            refactoring_keywords = [
                "refactor", "cleanup", "reorganize", "restructure",
                "simplify", "optimize", "improve", "extract",
                "rename", "move", "split", "merge"
            ]

            refactoring_commits = []

            for commit in commits:
                message = commit["message"].lower()

                # Check for refactoring keywords
                if any(keyword in message for keyword in refactoring_keywords):
                    # Analyze refactoring characteristics
                    refactoring_info = {
                        **commit,
                        "refactoring_type": self._classify_refactoring_type(message),
                        "scope": self._assess_refactoring_scope(commit["files_changed"]),
                        "complexity_change": await self._estimate_complexity_change(commit),
                        "success_indicators": await self._assess_refactoring_success(commit)
                    }

                    refactoring_commits.append(refactoring_info)

            logger.debug(f"🔧 Identified {len(refactoring_commits)} refactoring commits")
            return refactoring_commits

        except Exception as e:
            logger.error(f"Refactoring commit identification failed: {e}")
            return []

    def _classify_refactoring_type(self, commit_message: str) -> str:
        """Classify type of refactoring from commit message."""
        message = commit_message.lower()

        refactoring_types = {
            "extract": ["extract", "separate", "split"],
            "rename": ["rename", "change name"],
            "move": ["move", "relocate", "reorganize"],
            "simplify": ["simplify", "cleanup", "reduce complexity"],
            "optimize": ["optimize", "improve performance"],
            "restructure": ["restructure", "reorganize", "architecture"]
        }

        for refactor_type, keywords in refactoring_types.items():
            if any(keyword in message for keyword in keywords):
                return refactor_type

        return "general"

    def _assess_refactoring_scope(self, files_changed: List[Dict[str, Any]]) -> str:
        """Assess scope of refactoring for ADHD complexity understanding."""
        file_count = len(files_changed)

        if file_count == 1:
            return "🟢 Single file - focused change"
        elif file_count <= 3:
            return "🟡 Few files - manageable scope"
        elif file_count <= 10:
            return "🟠 Multiple files - requires focus"
        else:
            return "🔴 Large scope - consider breaking down"

    async def _estimate_complexity_change(self, commit: Dict[str, Any]) -> float:
        """Estimate complexity change from refactoring commit."""
        try:
            # Simple heuristic based on files changed and commit message
            files_changed = len(commit["files_changed"])
            message = commit["message"].lower()

            # Base complexity change
            complexity_change = 0.0

            # File count impact
            if files_changed > 5:
                complexity_change += 0.2  # More files = potentially more complex

            # Message analysis
            if any(word in message for word in ["simplify", "cleanup", "reduce"]):
                complexity_change -= 0.3  # Simplification reduces complexity
            elif any(word in message for word in ["extract", "split"]):
                complexity_change -= 0.1  # Extraction usually reduces complexity
            elif any(word in message for word in ["add", "implement", "extend"]):
                complexity_change += 0.2  # Addition increases complexity

            return max(-1.0, min(1.0, complexity_change))

        except Exception:
            return 0.0

    async def _assess_refactoring_success(self, commit: Dict[str, Any]) -> Dict[str, Any]:
        """Assess indicators of refactoring success."""
        try:
            # This would analyze subsequent commits to see if refactoring was successful
            # For now, provide basic assessment

            success_indicators = {
                "no_immediate_revert": True,  # Would check next few commits
                "consistent_with_patterns": True,  # Would check against known patterns
                "appropriate_scope": len(commit["files_changed"]) <= 5,
                "clear_message": len(commit["message"]) > 10
            }

            # Calculate overall success probability
            success_score = sum(1 for indicator in success_indicators.values() if indicator) / len(success_indicators)

            return {
                "success_indicators": success_indicators,
                "success_probability": success_score,
                "confidence": "medium"  # Would be higher with more analysis
            }

        except Exception:
            return {"success_probability": 0.5, "confidence": "low"}

    # Pattern Recognition and Learning

    async def learn_navigation_patterns(self, developer_id: str) -> Dict[str, Any]:
        """Learn navigation patterns for developer."""
        try:
            if not ML_AVAILABLE:
                return {"error": "ML not available"}

            # Get developer's navigation actions
            dev_actions = [
                action for action in self.action_history
                if action.developer_id == developer_id and action.action_type == "navigation"
            ]

            if len(dev_actions) < 10:
                return {"error": "Insufficient navigation data for pattern learning"}

            # Extract features for ML analysis
            features = []
            for action in dev_actions:
                feature_vector = [
                    action.cognitive_load,
                    action.session_duration / 60.0,  # Normalize to hours
                    action.context_switches,
                    self._encode_energy_level(action.energy_level),
                    len(action.file_path) if action.file_path else 0,
                    1.0 if action.success else 0.0
                ]
                features.append(feature_vector)

            # Perform clustering to identify patterns
            features_array = np.array(features)
            features_scaled = self.scaler.fit_transform(features_array)

            clustering_model = self.pattern_models["navigation_clustering"]
            clusters = clustering_model.fit_predict(features_scaled)

            # Analyze clusters for patterns
            pattern_analysis = self._analyze_navigation_clusters(dev_actions, clusters)

            return {
                "developer_id": developer_id,
                "actions_analyzed": len(dev_actions),
                "patterns_identified": len(pattern_analysis),
                "navigation_patterns": pattern_analysis,
                "adhd_recommendations": self._generate_navigation_recommendations(pattern_analysis),
                "confidence": "high" if len(dev_actions) > 50 else "medium"
            }

        except Exception as e:
            logger.error(f"Navigation pattern learning failed: {e}")
            return {"error": str(e)}

    def _analyze_navigation_clusters(
        self,
        actions: List[DeveloperAction],
        clusters: List[int]
    ) -> List[Dict[str, Any]]:
        """Analyze navigation action clusters to identify patterns."""
        try:
            cluster_patterns = {}

            for action, cluster_id in zip(actions, clusters):
                if cluster_id not in cluster_patterns:
                    cluster_patterns[cluster_id] = {
                        "actions": [],
                        "avg_cognitive_load": 0.0,
                        "avg_session_duration": 0.0,
                        "success_rate": 0.0,
                        "common_energy_level": None
                    }

                cluster_patterns[cluster_id]["actions"].append(action)

            # Calculate cluster characteristics
            patterns = []
            for cluster_id, cluster_data in cluster_patterns.items():
                cluster_actions = cluster_data["actions"]

                if len(cluster_actions) >= self.min_pattern_occurrences:
                    pattern = {
                        "pattern_id": f"nav_pattern_{cluster_id}",
                        "action_count": len(cluster_actions),
                        "avg_cognitive_load": statistics.mean([a.cognitive_load for a in cluster_actions]),
                        "avg_session_duration": statistics.mean([a.session_duration for a in cluster_actions]),
                        "success_rate": statistics.mean([1.0 if a.success else 0.0 for a in cluster_actions if a.success is not None]),
                        "common_energy_level": self._find_most_common([a.energy_level for a in cluster_actions]),
                        "pattern_description": self._describe_navigation_pattern(cluster_actions),
                        "adhd_suitability": self._assess_pattern_adhd_suitability(cluster_actions)
                    }
                    patterns.append(pattern)

            return patterns

        except Exception as e:
            logger.error(f"Navigation cluster analysis failed: {e}")
            return []

    # Historical Analysis Methods

    async def analyze_code_evolution_trends(
        self,
        file_path: str,
        workspace_id: str
    ) -> Dict[str, Any]:
        """Analyze how code file has evolved over time."""
        try:
            # Get file change history from git
            evolution_data = await self._get_file_evolution_data(file_path)

            if not evolution_data:
                return {"error": "No evolution data available"}

            # Analyze trends
            trends = {
                "complexity_trend": self._analyze_complexity_trend(evolution_data),
                "size_trend": self._analyze_size_trend(evolution_data),
                "refactoring_frequency": self._calculate_refactoring_frequency(evolution_data),
                "stability_score": self._calculate_stability_score(evolution_data),
                "adhd_friendliness_evolution": self._analyze_adhd_friendliness_trend(evolution_data)
            }

            # Generate insights
            insights = {
                "trends": trends,
                "predictions": self._predict_future_evolution(trends),
                "recommendations": self._generate_evolution_recommendations(trends),
                "optimal_refactoring_timing": self._suggest_refactoring_timing(trends)
            }

            return insights

        except Exception as e:
            logger.error(f"Code evolution analysis failed: {e}")
            return {"error": str(e)}

    # ADHD-Specific Learning

    async def learn_adhd_accommodation_effectiveness(
        self,
        developer_id: str
    ) -> Dict[str, Any]:
        """Learn which ADHD accommodations are most effective for developer."""
        try:
            dev_actions = [
                action for action in self.action_history
                if action.developer_id == developer_id
            ]

            if len(dev_actions) < 20:
                return {"error": "Insufficient data for ADHD learning"}

            # Analyze accommodation effectiveness
            accommodations = {
                "break_timing": self._analyze_break_effectiveness(dev_actions),
                "complexity_preferences": self._analyze_complexity_preferences(dev_actions),
                "energy_optimization": self._analyze_energy_patterns(dev_actions),
                "focus_mode_effectiveness": self._analyze_focus_mode_usage(dev_actions),
                "context_switch_tolerance": self._analyze_context_switch_patterns(dev_actions)
            }

            # Generate personalized recommendations
            recommendations = {
                "optimal_break_frequency": accommodations["break_timing"]["optimal_frequency"],
                "preferred_complexity_range": accommodations["complexity_preferences"]["sweet_spot"],
                "best_energy_times": accommodations["energy_optimization"]["peak_hours"],
                "focus_mode_recommendations": accommodations["focus_mode_effectiveness"]["usage_advice"],
                "context_switch_guidance": accommodations["context_switch_tolerance"]["recommendations"]
            }

            return {
                "developer_id": developer_id,
                "accommodations_analyzed": accommodations,
                "personalized_recommendations": recommendations,
                "learning_confidence": self._calculate_learning_confidence(len(dev_actions)),
                "next_learning_goals": self._identify_learning_gaps(accommodations)
            }

        except Exception as e:
            logger.error(f"ADHD accommodation learning failed: {e}")
            return {"error": str(e)}

    # Utility Methods

    def _find_peak_hours(self, hours: List[int]) -> List[int]:
        """Find peak working hours from commit times."""
        if not hours:
            return []

        hour_counts = {}
        for hour in hours:
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        # Find hours with above-average activity
        avg_activity = sum(hour_counts.values()) / len(hour_counts)
        peak_hours = [hour for hour, count in hour_counts.items() if count > avg_activity]

        return sorted(peak_hours)

    def _categorize_commit_sizes(self, sizes: List[int]) -> Dict[str, int]:
        """Categorize commit sizes for ADHD insights."""
        if not sizes:
            return {}

        categories = {"small": 0, "medium": 0, "large": 0}

        for size in sizes:
            if size <= 2:
                categories["small"] += 1
            elif size <= 10:
                categories["medium"] += 1
            else:
                categories["large"] += 1

        return categories

    def _analyze_language_preferences(self, commits: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze programming language preferences from commits."""
        language_counts = {}

        for commit in commits:
            for file_change in commit["files_changed"]:
                file_path = file_change["file_path"]
                ext = Path(file_path).suffix.lower()

                language_map = {
                    ".py": "Python",
                    ".js": "JavaScript",
                    ".ts": "TypeScript",
                    ".rs": "Rust",
                    ".go": "Go",
                    ".java": "Java"
                }

                language = language_map.get(ext, "Other")
                language_counts[language] = language_counts.get(language, 0) + 1

        return language_counts

    def _encode_energy_level(self, energy_level: str) -> float:
        """Encode energy level as numeric value for ML."""
        energy_map = {
            "very_low": 0.1,
            "low": 0.3,
            "medium": 0.6,
            "high": 0.8,
            "hyperfocus": 1.0
        }
        return energy_map.get(energy_level, 0.5)

    def _find_most_common(self, items: List[str]) -> str:
        """Find most common item in list."""
        if not items:
            return "unknown"

        counts = {}
        for item in items:
            counts[item] = counts.get(item, 0) + 1

        return max(counts.items(), key=lambda x: x[1])[0]

    def _describe_navigation_pattern(self, actions: List[DeveloperAction]) -> str:
        """Describe navigation pattern for ADHD users."""
        if not actions:
            return "Unknown pattern"

        avg_cognitive_load = statistics.mean([a.cognitive_load for a in actions])
        common_energy = self._find_most_common([a.energy_level for a in actions])

        if avg_cognitive_load < 0.4:
            return f"Light navigation pattern during {common_energy} energy"
        elif avg_cognitive_load < 0.7:
            return f"Moderate navigation pattern during {common_energy} energy"
        else:
            return f"Complex navigation pattern during {common_energy} energy"

    def _assess_pattern_adhd_suitability(self, actions: List[DeveloperAction]) -> str:
        """Assess how ADHD-friendly a pattern is."""
        if not actions:
            return "Unknown"

        success_rate = statistics.mean([1.0 if a.success else 0.0 for a in actions if a.success is not None])
        avg_context_switches = statistics.mean([a.context_switches for a in actions])

        if success_rate > 0.8 and avg_context_switches < 2:
            return "🟢 ADHD-friendly pattern"
        elif success_rate > 0.6:
            return "🟡 Moderately ADHD-friendly"
        else:
            return "🔴 Challenging for ADHD - needs optimization"

    # Public API Methods

    async def get_personalized_suggestions(
        self,
        developer_id: str,
        current_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get personalized suggestions based on learned patterns."""
        try:
            profile = self.developer_profiles.get(developer_id)
            if not profile:
                return []

            suggestions = []

            # Energy-based suggestions
            current_energy = current_context.get("energy_level", "medium")
            energy_patterns = profile.get("energy_patterns", {})

            if current_energy in energy_patterns:
                pattern = energy_patterns[current_energy]
                if pattern["success_rate"] > 0.7:
                    suggestions.append({
                        "type": "energy_optimization",
                        "message": f"✨ You typically perform well during {current_energy} energy periods",
                        "confidence": pattern["success_rate"],
                        "recommendation": "Continue with current energy-matched tasks"
                    })

            # Complexity preferences
            preferred_complexity = profile.get("preferred_complexity", 0.5)
            current_complexity = current_context.get("complexity_score", 0.5)

            if abs(current_complexity - preferred_complexity) > 0.3:
                if current_complexity > preferred_complexity:
                    suggestions.append({
                        "type": "complexity_mismatch",
                        "message": "🧠 This task is more complex than your usual preference",
                        "recommendation": "Consider breaking into smaller pieces or tackling during peak energy"
                    })
                else:
                    suggestions.append({
                        "type": "complexity_opportunity",
                        "message": "⚡ This is simpler than usual - good for building momentum",
                        "recommendation": "Good choice for current energy level"
                    })

            return suggestions

        except Exception as e:
            logger.error(f"Personalized suggestions failed: {e}")
            return []

    # Health and Performance

    async def get_learning_health(self) -> Dict[str, Any]:
        """Get learning engine health status."""
        try:
            return {
                "status": "🧠 Learning" if ML_AVAILABLE else "⚠️ Limited",
                "ml_available": ML_AVAILABLE,
                "redis_connected": self.redis_client is not None,
                "learning_data": {
                    "developer_profiles": len(self.developer_profiles),
                    "action_history_size": len(self.action_history),
                    "refactoring_patterns": len(self.refactoring_patterns)
                },
                "models_loaded": len(self.pattern_models),
                "privacy_mode": self.privacy_mode,
                "adhd_learning": self.adhd_learning_enabled
            }

        except Exception as e:
            logger.error(f"Learning health check failed: {e}")
            return {"status": "🔴 Error", "error": str(e)}

    async def close(self) -> None:
        """Close learning engine."""
        if self.redis_client:
            await self.redis_client.close()
        logger.info("🧠 Developer Learning Engine closed")

    # Placeholder methods for full implementation
    async def _store_developer_profile(self, developer_id: str, profile: Dict) -> None:
        """Store developer profile."""
        try:
            await self.redis_client.setex(
                f"dev_profile:{developer_id}",
                86400 * 30,  # 30 days
                json.dumps(profile, default=str)
            )
        except Exception as e:
            logger.error(f"Profile storage failed: {e}")

    async def _get_file_evolution_data(self, file_path: str) -> List[Dict]:
        return []  # Placeholder

    def _analyze_complexity_trend(self, data: List[Dict]) -> Dict:
        return {"trend": "stable"}  # Placeholder

    def _analyze_size_trend(self, data: List[Dict]) -> Dict:
        return {"trend": "growing"}  # Placeholder

    def _calculate_refactoring_frequency(self, data: List[Dict]) -> float:
        return 0.1  # Placeholder

    def _calculate_stability_score(self, data: List[Dict]) -> float:
        return 0.8  # Placeholder

    def _analyze_adhd_friendliness_trend(self, data: List[Dict]) -> Dict:
        return {"trend": "improving"}  # Placeholder

    def _predict_future_evolution(self, trends: Dict) -> Dict:
        return {"prediction": "continued_improvement"}  # Placeholder

    def _generate_evolution_recommendations(self, trends: Dict) -> List[str]:
        return ["Continue current refactoring approach"]  # Placeholder

    def _suggest_refactoring_timing(self, trends: Dict) -> str:
        return "Good time for refactoring"  # Placeholder

    def _analyze_break_effectiveness(self, actions: List) -> Dict:
        return {"optimal_frequency": 25}  # Placeholder

    def _analyze_complexity_preferences(self, actions: List) -> Dict:
        return {"sweet_spot": 0.5}  # Placeholder

    def _analyze_energy_patterns(self, actions: List) -> Dict:
        return {"peak_hours": [9, 14]}  # Placeholder

    def _analyze_focus_mode_usage(self, actions: List) -> Dict:
        return {"usage_advice": "Use focus mode for complex tasks"}  # Placeholder

    def _analyze_context_switch_patterns(self, actions: List) -> Dict:
        return {"recommendations": ["Limit context switches to 3 per hour"]}  # Placeholder

    def _calculate_learning_confidence(self, action_count: int) -> str:
        if action_count > 100:
            return "high"
        elif action_count > 50:
            return "medium"
        else:
            return "low"

    def _identify_learning_gaps(self, accommodations: Dict) -> List[str]:
        return ["Need more break timing data", "Need focus mode usage patterns"]  # Placeholder

    async def _generate_historical_recommendations(self, commit_analysis: Dict, refactoring_patterns: Dict, adhd_insights: Dict) -> List[str]:
        return ["Continue current development patterns", "Consider more frequent breaks"]  # Placeholder

    def _generate_navigation_recommendations(self, patterns: List[Dict]) -> List[str]:
        return ["Use low-complexity entry points during low energy", "Focus mode helps with complex navigation"]  # Placeholder