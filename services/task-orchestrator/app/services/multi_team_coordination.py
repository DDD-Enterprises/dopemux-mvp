"""
Multi-Team Coordination Engine for Task Orchestrator
ADHD-Optimized Cross-Team Dependency Management

Handles distributed cognitive load balancing and cross-team workflow orchestration
with discretion and minimal cognitive overhead.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class TeamType(str, Enum):
    """Different team types for coordination."""
    DEVELOPMENT = "development"
    QA = "qa"
    DESIGN = "design"
    PRODUCT = "product"
    DEVOPS = "devops"
    EXTERNAL = "external"


class CoordinationPriority(str, Enum):
    """Priority levels for cross-team coordination."""
    CRITICAL = "critical"        # Blocking multiple teams
    HIGH = "high"               # Blocking one team
    MEDIUM = "medium"           # Moderate impact
    LOW = "low"                 # Minimal impact
    BACKGROUND = "background"   # Can be batched


@dataclass
class TeamProfile:
    """Team profile with ADHD considerations."""
    team_id: str
    team_type: TeamType
    capacity: float                    # 0.0-1.0 current capacity
    cognitive_load: float              # 0.0-1.0 current cognitive load
    peak_hours: List[str]              # ["09:00", "14:00"] peak performance
    communication_preference: str      # "async", "sync", "mixed"
    context_switch_cost: float         # Time penalty for switching contexts
    max_parallel_projects: int         # Maximum concurrent projects
    adhd_members: int                  # Number of ADHD team members
    current_projects: Set[str]         # Active project IDs


@dataclass
class CrossTeamDependency:
    """Dependency between teams with coordination metadata."""
    dependency_id: str
    source_team: str
    target_team: str
    task_id: str
    description: str
    priority: CoordinationPriority
    estimated_effort: float            # Hours
    deadline: Optional[datetime]
    blocking_tasks: List[str]          # Tasks blocked by this dependency
    communication_history: List[Dict] # Previous coordination attempts
    cognitive_impact: float            # Impact on team cognitive load
    created_at: datetime
    status: str = "pending"            # pending, in_progress, completed, blocked


class MultiTeamCoordinationEngine:
    """
    Intelligent multi-team coordination with ADHD-optimized workflows.

    Features:
    - Cognitive load balancing across teams
    - Discrete coordination with minimal interruption
    - Smart batching of cross-team communications
    - Context-aware dependency resolution
    - ADHD-friendly notification patterns
    """

    def __init__(self, conport_client=None, pal_client=None):
        self.conport = conport_client
        self.pal = pal_client

        # Team management
        self.teams: Dict[str, TeamProfile] = {}
        self.dependencies: Dict[str, CrossTeamDependency] = {}
        self.coordination_queue: List[str] = []
        self._monitor_task: Optional[asyncio.Task] = None

        # ADHD optimizations
        self.batch_window = timedelta(hours=2)  # Batch communications
        self.max_interruptions_per_day = 3     # Per team
        self.context_switch_buffer = timedelta(minutes=15)

        # Analytics
        self.coordination_stats = {
            "dependencies_resolved": 0,
            "context_switches_prevented": 0,
            "cognitive_load_balanced": 0,
            "teams_coordinated": 0
        }

    async def initialize(self) -> None:
        """Initialize the coordination engine."""
        try:
            await self._load_team_profiles()
            await self._restore_coordination_state()
            await self._start_coordination_monitor()
            logger.info("Multi-team coordination engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize coordination engine: {e}")

    async def register_team(self, team_profile: TeamProfile) -> bool:
        """Register a new team for coordination."""
        try:
            self.teams[team_profile.team_id] = team_profile
            logger.info(f"Registered team: {team_profile.team_id}")

            # Log to ConPort if available
            if self.conport:
                await self._log_team_registration(team_profile)

            return True
        except Exception as e:
            logger.error(f"Failed to register team {team_profile.team_id}: {e}")
            return False

    async def create_cross_team_dependency(
        self,
        source_team: str,
        target_team: str,
        task_id: str,
        description: str,
        priority: CoordinationPriority,
        estimated_effort: float,
        deadline: Optional[datetime] = None
    ) -> Optional[str]:
        """Create a new cross-team dependency."""
        try:
            dependency_id = f"dep_{uuid.uuid4().hex[:8]}"

            # Calculate cognitive impact
            cognitive_impact = await self._calculate_cognitive_impact(
                source_team, target_team, priority, estimated_effort
            )

            dependency = CrossTeamDependency(
                dependency_id=dependency_id,
                source_team=source_team,
                target_team=target_team,
                task_id=task_id,
                description=description,
                priority=priority,
                estimated_effort=estimated_effort,
                deadline=deadline,
                blocking_tasks=[],
                communication_history=[],
                cognitive_impact=cognitive_impact,
                created_at=datetime.now()
            )

            self.dependencies[dependency_id] = dependency

            # Smart coordination scheduling
            await self._schedule_coordination(dependency)

            logger.info(f"Created cross-team dependency: {dependency_id}")
            return dependency_id

        except Exception as e:
            logger.error(f"Failed to create cross-team dependency: {e}")
            return None

    async def optimize_team_workload(self, team_id: str) -> Dict[str, Any]:
        """Optimize workload distribution for a specific team."""
        try:
            team = self.teams.get(team_id)
            if not team:
                return {"error": "Team not found"}

            # Analyze current workload
            current_load = await self._analyze_team_workload(team_id)

            # Generate optimization recommendations
            recommendations = await self._generate_workload_recommendations(team, current_load)

            # Apply ADHD-specific optimizations
            adhd_optimizations = await self._apply_adhd_optimizations(team, recommendations)

            result = {
                "team_id": team_id,
                "current_load": current_load,
                "recommendations": recommendations,
                "adhd_optimizations": adhd_optimizations,
                "estimated_improvement": await self._estimate_workload_improvement(team, recommendations)
            }

            self.coordination_stats["cognitive_load_balanced"] += 1
            return result

        except Exception as e:
            logger.error(f"Failed to optimize workload for team {team_id}: {e}")
            return {"error": str(e)}

    async def resolve_coordination_conflicts(self) -> List[Dict[str, Any]]:
        """Resolve conflicts in cross-team coordination."""
        try:
            conflicts = await self._detect_coordination_conflicts()
            resolutions = []

            for conflict in conflicts:
                resolution = await self._resolve_single_conflict(conflict)
                resolutions.append(resolution)

            return resolutions

        except Exception as e:
            logger.error(f"Failed to resolve coordination conflicts: {e}")
            return []

    async def get_team_coordination_status(self) -> Dict[str, Any]:
        """Get overall coordination status across all teams."""
        try:
            status = {
                "total_teams": len(self.teams),
                "active_dependencies": len([d for d in self.dependencies.values() if d.status != "completed"]),
                "coordination_queue_length": len(self.coordination_queue),
                "average_cognitive_load": await self._calculate_average_cognitive_load(),
                "coordination_stats": self.coordination_stats,
                "team_status": {}
            }

            for team_id, team in self.teams.items():
                status["team_status"][team_id] = {
                    "capacity": team.capacity,
                    "cognitive_load": team.cognitive_load,
                    "active_projects": len(team.current_projects),
                    "pending_dependencies": len([d for d in self.dependencies.values()
                                               if d.target_team == team_id and d.status == "pending"])
                }

            return status

        except Exception as e:
            logger.error(f"Failed to get coordination status: {e}")
            return {"error": str(e)}

    # Private implementation methods

    async def _load_team_profiles(self) -> None:
        """Load team profiles from ConPort or configuration."""
        if self.teams:
            return

        loaded_profiles: List[TeamProfile] = []

        if self.conport and hasattr(self.conport, "get_team_profiles"):
            try:
                result = self.conport.get_team_profiles()
                if asyncio.iscoroutine(result):
                    result = await result
                for item in result or []:
                    team_type_raw = str(item.get("team_type", TeamType.DEVELOPMENT.value)).lower()
                    try:
                        team_type = TeamType(team_type_raw)
                    except ValueError:
                        team_type = TeamType.DEVELOPMENT

                    loaded_profiles.append(
                        TeamProfile(
                            team_id=str(item.get("team_id") or item.get("id")),
                            team_type=team_type,
                            capacity=float(item.get("capacity", 0.8)),
                            cognitive_load=float(item.get("cognitive_load", 0.35)),
                            peak_hours=list(item.get("peak_hours", ["09:00", "14:00"])),
                            communication_preference=str(item.get("communication_preference", "async")),
                            context_switch_cost=float(item.get("context_switch_cost", 0.2)),
                            max_parallel_projects=int(item.get("max_parallel_projects", 3)),
                            adhd_members=int(item.get("adhd_members", 0)),
                            current_projects=set(item.get("current_projects", [])),
                        )
                    )
            except Exception as exc:
                logger.debug("Failed to load team profiles from ConPort: %s", exc)

        if not loaded_profiles:
            loaded_profiles = [
                TeamProfile(
                    team_id="dev",
                    team_type=TeamType.DEVELOPMENT,
                    capacity=0.8,
                    cognitive_load=0.35,
                    peak_hours=["09:00", "14:00"],
                    communication_preference="async",
                    context_switch_cost=0.2,
                    max_parallel_projects=3,
                    adhd_members=1,
                    current_projects=set(),
                ),
                TeamProfile(
                    team_id="qa",
                    team_type=TeamType.QA,
                    capacity=0.7,
                    cognitive_load=0.3,
                    peak_hours=["10:00", "15:00"],
                    communication_preference="mixed",
                    context_switch_cost=0.15,
                    max_parallel_projects=2,
                    adhd_members=0,
                    current_projects=set(),
                ),
            ]

        for team in loaded_profiles:
            self.teams[team.team_id] = team

    async def _restore_coordination_state(self) -> None:
        """Restore coordination state from persistent storage."""
        if not self.conport:
            return

        state = None
        for method_name in ("get_coordination_state", "get_multi_team_coordination_state"):
            if not hasattr(self.conport, method_name):
                continue
            try:
                result = getattr(self.conport, method_name)()
                if asyncio.iscoroutine(result):
                    result = await result
                if result:
                    state = result
                    break
            except Exception as exc:
                logger.debug("Failed to restore state via %s: %s", method_name, exc)

        if not state:
            return

        self.coordination_queue = list(state.get("coordination_queue", []))

        for item in state.get("dependencies", []):
            dependency_id = str(item.get("dependency_id") or item.get("id", f"dep_{uuid.uuid4().hex[:8]}"))
            priority_raw = str(item.get("priority", CoordinationPriority.MEDIUM.value)).lower()
            try:
                priority = CoordinationPriority(priority_raw)
            except ValueError:
                priority = CoordinationPriority.MEDIUM

            deadline_raw = item.get("deadline")
            deadline = None
            if isinstance(deadline_raw, str):
                try:
                    deadline = datetime.fromisoformat(deadline_raw)
                except ValueError:
                    deadline = None
            elif isinstance(deadline_raw, datetime):
                deadline = deadline_raw

            self.dependencies[dependency_id] = CrossTeamDependency(
                dependency_id=dependency_id,
                source_team=str(item.get("source_team", "unknown")),
                target_team=str(item.get("target_team", "unknown")),
                task_id=str(item.get("task_id", "unknown")),
                description=str(item.get("description", "")),
                priority=priority,
                estimated_effort=float(item.get("estimated_effort", 1.0)),
                deadline=deadline,
                blocking_tasks=list(item.get("blocking_tasks", [])),
                communication_history=list(item.get("communication_history", [])),
                cognitive_impact=float(item.get("cognitive_impact", 0.1)),
                created_at=datetime.now(),
                status=str(item.get("status", "pending")),
            )

    async def _start_coordination_monitor(self) -> None:
        """Start background monitoring for coordination opportunities."""
        if self._monitor_task and not self._monitor_task.done():
            return
        self._monitor_task = asyncio.create_task(self._coordination_monitor_loop())

    async def _coordination_monitor_loop(self) -> None:
        """Background loop that incrementally resolves coordination conflicts."""
        try:
            while True:
                await asyncio.sleep(60)
                conflicts = await self._detect_coordination_conflicts()
                if not conflicts:
                    continue
                for conflict in conflicts:
                    await self._resolve_single_conflict(conflict)
        except asyncio.CancelledError:
            logger.debug("Coordination monitor loop cancelled")
            raise
        except Exception as exc:
            logger.error("Coordination monitor loop crashed: %s", exc)

    async def _calculate_cognitive_impact(
        self, source_team: str, target_team: str,
        priority: CoordinationPriority, effort: float
    ) -> float:
        """Calculate the cognitive impact of a cross-team dependency."""
        # Implementation would calculate cognitive load impact
        base_impact = effort * 0.1
        priority_multiplier = {
            CoordinationPriority.CRITICAL: 2.0,
            CoordinationPriority.HIGH: 1.5,
            CoordinationPriority.MEDIUM: 1.0,
            CoordinationPriority.LOW: 0.7,
            CoordinationPriority.BACKGROUND: 0.3
        }
        return base_impact * priority_multiplier.get(priority, 1.0)

    async def _schedule_coordination(self, dependency: CrossTeamDependency) -> None:
        """Schedule coordination for a dependency."""
        if dependency.dependency_id not in self.coordination_queue:
            self.coordination_queue.append(dependency.dependency_id)

        priority_rank = {
            CoordinationPriority.CRITICAL: 0,
            CoordinationPriority.HIGH: 1,
            CoordinationPriority.MEDIUM: 2,
            CoordinationPriority.LOW: 3,
            CoordinationPriority.BACKGROUND: 4,
        }

        def queue_key(dep_id: str) -> Tuple[int, datetime]:
            dep = self.dependencies.get(dep_id)
            if not dep:
                return (999, datetime.max)
            deadline = dep.deadline or datetime.max
            return (priority_rank.get(dep.priority, 2), deadline)

        self.coordination_queue.sort(key=queue_key)

    async def _analyze_team_workload(self, team_id: str) -> Dict[str, Any]:
        """Analyze current team workload."""
        # Implementation would analyze workload metrics
        return {"utilization": 0.7, "stress_level": 0.4}

    async def _generate_workload_recommendations(
        self, team: TeamProfile, current_load: Dict[str, Any]
    ) -> List[str]:
        """Generate workload optimization recommendations."""
        # Implementation would generate smart recommendations
        return ["Reduce parallel projects", "Batch similar tasks"]

    async def _apply_adhd_optimizations(
        self, team: TeamProfile, recommendations: List[str]
    ) -> List[str]:
        """Apply ADHD-specific optimizations."""
        adhd_optimizations = []
        if team.adhd_members > 0:
            adhd_optimizations.extend([
                "Schedule focus blocks during peak hours",
                "Minimize context switching between projects",
                "Use async communication where possible"
            ])
        return adhd_optimizations

    async def _estimate_workload_improvement(
        self, team: TeamProfile, recommendations: List[str]
    ) -> Dict[str, float]:
        """Estimate improvement from workload optimizations."""
        return {"productivity_gain": 0.15, "stress_reduction": 0.25}

    async def _detect_coordination_conflicts(self) -> List[Dict[str, Any]]:
        """Detect conflicts in team coordination."""
        # Implementation would detect scheduling/resource conflicts
        return []

    async def _resolve_single_conflict(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve a single coordination conflict."""
        # Implementation would resolve conflicts intelligently
        return {"conflict_id": conflict.get("id"), "resolution": "Rescheduled"}

    async def _calculate_average_cognitive_load(self) -> float:
        """Calculate average cognitive load across all teams."""
        if not self.teams:
            return 0.0
        total_load = sum(team.cognitive_load for team in self.teams.values())
        return total_load / len(self.teams)

    async def _log_team_registration(self, team_profile: TeamProfile) -> None:
        """Log team registration to ConPort."""
        if not self.conport:
            return

        payload = {
            "team_id": team_profile.team_id,
            "team_type": team_profile.team_type.value,
            "capacity": team_profile.capacity,
            "cognitive_load": team_profile.cognitive_load,
            "max_parallel_projects": team_profile.max_parallel_projects,
            "adhd_members": team_profile.adhd_members,
            "registered_at": datetime.now().isoformat(),
        }

        for method_name in (
            "record_team_registration",
            "upsert_team_profile",
            "log_coordination_event",
            "add_observation",
        ):
            if not hasattr(self.conport, method_name):
                continue
            try:
                result = getattr(self.conport, method_name)(payload)
                if asyncio.iscoroutine(result):
                    await result
                return
            except Exception as exc:
                logger.debug("ConPort %s failed: %s", method_name, exc)
