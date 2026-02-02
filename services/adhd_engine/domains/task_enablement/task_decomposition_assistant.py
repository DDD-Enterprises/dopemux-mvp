"""
Task Decomposition Assistant

Automatically breaks down complex tasks into ADHD-friendly micro-tasks:
- Detects large/complex tasks (>2h estimate or high complexity)
- Auto-suggests subtask breakdown with 5-15min chunks
- Energy-aware scheduling (complex tasks in peak hours)
- Smart prioritization (urgency + ADHD-suitability)
- Micro-commitment generation ("Just 5 minutes on X")

ADHD Benefit: Eliminates decision paralysis, reduces task initiation resistance
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import re

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """Task complexity levels."""
    TRIVIAL = "trivial"  # <15 min
    SIMPLE = "simple"  # 15-30 min
    MODERATE = "moderate"  # 30-60 min
    COMPLEX = "complex"  # 1-2 hours
    VERY_COMPLEX = "very_complex"  # 2-4 hours
    EPIC = "epic"  # 4+ hours


class EnergyRequirement(Enum):
    """Energy level required for task."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class MicroTask:
    """5-15 minute micro-task."""
    task_id: str
    description: str
    estimated_minutes: int
    energy_required: EnergyRequirement
    order: int  # Sequence in parent task
    parent_task_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    completed: bool = False
    
    def is_adhd_friendly(self) -> bool:
        """Check if task meets ADHD-friendly criteria."""
        return (
            self.estimated_minutes <= 15 and
            len(self.description.split()) <= 10  # Simple, clear description
        )


@dataclass
class TaskDecomposition:
    """Decomposed task with micro-tasks."""
    original_task_id: str
    original_description: str
    original_complexity: TaskComplexity
    micro_tasks: List[MicroTask]
    recommended_order: List[str]  # Optimal sequence
    total_estimated_minutes: int
    adhd_friendly_score: float  # 0.0-1.0
    
    def get_next_micro_task(self) -> Optional[MicroTask]:
        """Get next uncompleted micro-task in sequence."""
        for task_id in self.recommended_order:
            task = next((mt for mt in self.micro_tasks if mt.task_id == task_id), None)
            if task and not task.completed:
                return task
        return None


class TaskDecompositionAssistant:
    """
    ADHD-aware task decomposition assistant.
    
    Features:
    - Analyzes task complexity from description
    - Breaks down large tasks into 5-15min micro-tasks
    - Energy-aware scheduling recommendations
    - Smart prioritization by urgency + ADHD-suitability
    - Micro-commitment generation for task initiation
    """
    
    # Complexity indicators (keywords that suggest higher complexity)
    COMPLEXITY_KEYWORDS = {
        "high": ["architecture", "refactor", "redesign", "migrate", "integrate", "research"],
        "medium": ["implement", "create", "build", "add feature", "optimize", "debug"],
        "low": ["update", "fix typo", "rename", "format", "document", "review"]
    }
    
    # Energy requirement keywords
    ENERGY_KEYWORDS = {
        "high": ["design", "architecture", "research", "learn", "decide", "plan"],
        "medium": ["implement", "code", "write", "create", "build"],
        "low": ["review", "test", "document", "format", "organize"]
    }
    
    def __init__(self, energy_predictor=None):
        """
        Initialize task decomposition assistant.
        
        Args:
            energy_predictor: Optional energy predictor for scheduling
        """
        self.energy_predictor = energy_predictor
        self.decomposition_history: List[TaskDecomposition] = []
    
    def analyze_task_complexity(self, task_description: str, time_estimate: Optional[int] = None) -> Tuple[TaskComplexity, EnergyRequirement]:
        """
        Analyze task complexity and energy requirement.
        
        Args:
            task_description: Task description text
            time_estimate: Optional time estimate in minutes
        
        Returns:
            Tuple of (complexity level, energy requirement)
        """
        desc_lower = task_description.lower()
        
        # Complexity scoring
        complexity_score = 0
        
        # Check keywords
        for keyword in self.COMPLEXITY_KEYWORDS["high"]:
            if keyword in desc_lower:
                complexity_score += 3
        for keyword in self.COMPLEXITY_KEYWORDS["medium"]:
            if keyword in desc_lower:
                complexity_score += 2
        for keyword in self.COMPLEXITY_KEYWORDS["low"]:
            if keyword in desc_lower:
                complexity_score += 1
        
        # Factor in time estimate if provided
        if time_estimate:
            if time_estimate > 240:  # 4+ hours
                complexity = TaskComplexity.EPIC
            elif time_estimate > 120:  # 2-4 hours
                complexity = TaskComplexity.VERY_COMPLEX
            elif time_estimate > 60:  # 1-2 hours
                complexity = TaskComplexity.COMPLEX
            elif time_estimate > 30:  # 30-60 min
                complexity = TaskComplexity.MODERATE
            elif time_estimate > 15:  # 15-30 min
                complexity = TaskComplexity.SIMPLE
            else:  # <15 min
                complexity = TaskComplexity.TRIVIAL
        else:
            # Use keyword scoring
            if complexity_score >= 6:
                complexity = TaskComplexity.VERY_COMPLEX
            elif complexity_score >= 4:
                complexity = TaskComplexity.COMPLEX
            elif complexity_score >= 2:
                complexity = TaskComplexity.MODERATE
            elif complexity_score >= 1:
                complexity = TaskComplexity.SIMPLE
            else:
                complexity = TaskComplexity.TRIVIAL
        
        # Energy requirement
        energy_score = 0
        for keyword in self.ENERGY_KEYWORDS["high"]:
            if keyword in desc_lower:
                energy_score += 3
        for keyword in self.ENERGY_KEYWORDS["medium"]:
            if keyword in desc_lower:
                energy_score += 2
        for keyword in self.ENERGY_KEYWORDS["low"]:
            if keyword in desc_lower:
                energy_score += 1
        
        if energy_score >= 5:
            energy = EnergyRequirement.HIGH
        elif energy_score >= 2:
            energy = EnergyRequirement.MEDIUM
        else:
            energy = EnergyRequirement.LOW
        
        return complexity, energy
    
    def should_decompose(self, complexity: TaskComplexity, time_estimate: Optional[int] = None) -> bool:
        """Check if task should be decomposed."""
        # Always decompose complex, very complex, and epic tasks
        if complexity in [TaskComplexity.COMPLEX, TaskComplexity.VERY_COMPLEX, TaskComplexity.EPIC]:
            return True
        
        # Decompose moderate tasks if time estimate >45 min
        if complexity == TaskComplexity.MODERATE and time_estimate and time_estimate > 45:
            return True
        
        return False
    
    def decompose_task(
        self,
        task_id: str,
        task_description: str,
        time_estimate: Optional[int] = None,
        current_energy: str = "medium"
    ) -> TaskDecomposition:
        """
        Decompose task into micro-tasks.
        
        Args:
            task_id: Task identifier
            task_description: Task description
            time_estimate: Optional time estimate in minutes
            current_energy: Current energy level (high/medium/low)
        
        Returns:
            TaskDecomposition with micro-tasks
        """
        complexity, energy_req = self.analyze_task_complexity(task_description, time_estimate)
        
        if not self.should_decompose(complexity, time_estimate):
            # Task is already ADHD-friendly
            return TaskDecomposition(
                original_task_id=task_id,
                original_description=task_description,
                original_complexity=complexity,
                micro_tasks=[
                    MicroTask(
                        task_id=f"{task_id}_1",
                        description=task_description,
                        estimated_minutes=time_estimate or 15,
                        energy_required=energy_req,
                        order=1,
                        parent_task_id=task_id
                    )
                ],
                recommended_order=[f"{task_id}_1"],
                total_estimated_minutes=time_estimate or 15,
                adhd_friendly_score=1.0
            )
        
        # Generate micro-tasks based on complexity
        micro_tasks = self._generate_micro_tasks(
            task_id,
            task_description,
            complexity,
            energy_req,
            time_estimate
        )
        
        # Optimize order based on current energy
        recommended_order = self._optimize_order(micro_tasks, current_energy)
        
        # Calculate ADHD-friendly score
        adhd_score = sum(1 for mt in micro_tasks if mt.is_adhd_friendly()) / len(micro_tasks)
        
        total_time = sum(mt.estimated_minutes for mt in micro_tasks)
        
        decomposition = TaskDecomposition(
            original_task_id=task_id,
            original_description=task_description,
            original_complexity=complexity,
            micro_tasks=micro_tasks,
            recommended_order=recommended_order,
            total_estimated_minutes=total_time,
            adhd_friendly_score=adhd_score
        )
        
        self.decomposition_history.append(decomposition)
        
        return decomposition
    
    def _generate_micro_tasks(
        self,
        parent_id: str,
        description: str,
        complexity: TaskComplexity,
        energy_req: EnergyRequirement,
        time_estimate: Optional[int]
    ) -> List[MicroTask]:
        """Generate micro-tasks from parent task."""
        micro_tasks = []
        
        # Standard decomposition pattern based on task type
        desc_lower = description.lower()
        
        # Pattern 1: Implementation task
        if any(keyword in desc_lower for keyword in ["implement", "create", "build", "add"]):
            micro_tasks.extend([
                MicroTask(
                    task_id=f"{parent_id}_1",
                    description="Read docs/understand requirements",
                    estimated_minutes=10,
                    energy_required=EnergyRequirement.MEDIUM,
                    order=1,
                    parent_task_id=parent_id
                ),
                MicroTask(
                    task_id=f"{parent_id}_2",
                    description="Write failing test case",
                    estimated_minutes=10,
                    energy_required=EnergyRequirement.MEDIUM,
                    order=2,
                    parent_task_id=parent_id,
                    dependencies=[f"{parent_id}_1"]
                ),
                MicroTask(
                    task_id=f"{parent_id}_3",
                    description="Implement minimal version",
                    estimated_minutes=15,
                    energy_required=energy_req,
                    order=3,
                    parent_task_id=parent_id,
                    dependencies=[f"{parent_id}_2"]
                ),
                MicroTask(
                    task_id=f"{parent_id}_4",
                    description="Make test pass",
                    estimated_minutes=10,
                    energy_required=EnergyRequirement.MEDIUM,
                    order=4,
                    parent_task_id=parent_id,
                    dependencies=[f"{parent_id}_3"]
                ),
                MicroTask(
                    task_id=f"{parent_id}_5",
                    description="Add edge case handling",
                    estimated_minutes=10,
                    energy_required=EnergyRequirement.LOW,
                    order=5,
                    parent_task_id=parent_id,
                    dependencies=[f"{parent_id}_4"]
                )
            ])
        
        # Pattern 2: Refactoring task
        elif any(keyword in desc_lower for keyword in ["refactor", "redesign", "cleanup"]):
            micro_tasks.extend([
                MicroTask(
                    task_id=f"{parent_id}_1",
                    description="Review current implementation",
                    estimated_minutes=10,
                    energy_required=EnergyRequirement.MEDIUM,
                    order=1,
                    parent_task_id=parent_id
                ),
                MicroTask(
                    task_id=f"{parent_id}_2",
                    description="Identify improvement areas (3 max)",
                    estimated_minutes=10,
                    energy_required=EnergyRequirement.HIGH,
                    order=2,
                    parent_task_id=parent_id,
                    dependencies=[f"{parent_id}_1"]
                ),
                MicroTask(
                    task_id=f"{parent_id}_3",
                    description="Add tests if missing",
                    estimated_minutes=15,
                    energy_required=EnergyRequirement.MEDIUM,
                    order=3,
                    parent_task_id=parent_id,
                    dependencies=[f"{parent_id}_2"]
                ),
                MicroTask(
                    task_id=f"{parent_id}_4",
                    description="Refactor one area",
                    estimated_minutes=15,
                    energy_required=EnergyRequirement.HIGH,
                    order=4,
                    parent_task_id=parent_id,
                    dependencies=[f"{parent_id}_3"]
                ),
                MicroTask(
                    task_id=f"{parent_id}_5",
                    description="Verify tests still pass",
                    estimated_minutes=5,
                    energy_required=EnergyRequirement.LOW,
                    order=5,
                    parent_task_id=parent_id,
                    dependencies=[f"{parent_id}_4"]
                )
            ])
        
        # Pattern 3: Bug fix
        elif any(keyword in desc_lower for keyword in ["fix", "bug", "debug", "error"]):
            micro_tasks.extend([
                MicroTask(
                    task_id=f"{parent_id}_1",
                    description="Reproduce the bug",
                    estimated_minutes=10,
                    energy_required=EnergyRequirement.MEDIUM,
                    order=1,
                    parent_task_id=parent_id
                ),
                MicroTask(
                    task_id=f"{parent_id}_2",
                    description="Write test that fails",
                    estimated_minutes=10,
                    energy_required=EnergyRequirement.MEDIUM,
                    order=2,
                    parent_task_id=parent_id,
                    dependencies=[f"{parent_id}_1"]
                ),
                MicroTask(
                    task_id=f"{parent_id}_3",
                    description="Identify root cause",
                    estimated_minutes=15,
                    energy_required=EnergyRequirement.HIGH,
                    order=3,
                    parent_task_id=parent_id,
                    dependencies=[f"{parent_id}_2"]
                ),
                MicroTask(
                    task_id=f"{parent_id}_4",
                    description="Implement fix",
                    estimated_minutes=10,
                    energy_required=EnergyRequirement.MEDIUM,
                    order=4,
                    parent_task_id=parent_id,
                    dependencies=[f"{parent_id}_3"]
                ),
                MicroTask(
                    task_id=f"{parent_id}_5",
                    description="Verify fix works",
                    estimated_minutes=5,
                    energy_required=EnergyRequirement.LOW,
                    order=5,
                    parent_task_id=parent_id,
                    dependencies=[f"{parent_id}_4"]
                )
            ])
        
        # Pattern 4: Generic decomposition (fallback)
        else:
            num_chunks = min(6, max(3, (time_estimate or 60) // 15))
            chunk_time = (time_estimate or 60) // num_chunks
            
            for i in range(num_chunks):
                micro_tasks.append(MicroTask(
                    task_id=f"{parent_id}_{i+1}",
                    description=f"Work on: {description[:40]}... (part {i+1}/{num_chunks})",
                    estimated_minutes=chunk_time,
                    energy_required=energy_req if i < num_chunks // 2 else EnergyRequirement.LOW,
                    order=i+1,
                    parent_task_id=parent_id,
                    dependencies=[f"{parent_id}_{i}"] if i > 0 else []
                ))
        
        return micro_tasks
    
    def _optimize_order(self, micro_tasks: List[MicroTask], current_energy: str) -> List[str]:
        """
        Optimize micro-task order based on current energy.
        
        Strategy:
        - High energy: Start with high-energy tasks
        - Medium energy: Mix high and low
        - Low energy: Start with low-energy tasks for momentum
        """
        # Respect dependencies first
        ordered = []
        remaining = micro_tasks.copy()
        
        while remaining:
            # Find tasks with no unmet dependencies
            available = [
                mt for mt in remaining
                if all(dep_id in ordered for dep_id in mt.dependencies)
            ]
            
            if not available:
                # Circular dependency or error - just take next
                available = remaining[:1]
            
            # Sort available by energy match
            if current_energy == "high":
                # Prioritize high-energy tasks
                available.sort(key=lambda mt: (
                    0 if mt.energy_required == EnergyRequirement.HIGH else
                    1 if mt.energy_required == EnergyRequirement.MEDIUM else 2
                ))
            elif current_energy == "low":
                # Prioritize low-energy tasks for momentum
                available.sort(key=lambda mt: (
                    0 if mt.energy_required == EnergyRequirement.LOW else
                    1 if mt.energy_required == EnergyRequirement.MEDIUM else 2
                ))
            else:  # medium
                # Balanced approach
                available.sort(key=lambda mt: mt.order)
            
            # Take first available
            next_task = available[0]
            ordered.append(next_task.task_id)
            remaining.remove(next_task)
        
        return ordered
    
    def generate_micro_commitment(self, task_description: str) -> str:
        """
        Generate 5-minute micro-commitment for task initiation.
        
        ADHD Strategy: Lower activation energy by committing to just 5 minutes
        """
        desc_lower = task_description.lower()
        
        if "implement" in desc_lower or "build" in desc_lower:
            return f"Just spend 5 minutes reading the requirements for: {task_description}"
        elif "fix" in desc_lower or "bug" in desc_lower:
            return f"Just spend 5 minutes trying to reproduce: {task_description}"
        elif "refactor" in desc_lower:
            return f"Just spend 5 minutes reviewing the current code for: {task_description}"
        elif "test" in desc_lower:
            return f"Just spend 5 minutes writing one simple test for: {task_description}"
        else:
            return f"Just spend 5 minutes planning how to approach: {task_description}"
    
    def get_adhd_suitability_score(
        self,
        task: MicroTask,
        current_energy: str,
        current_attention: str
    ) -> float:
        """
        Calculate ADHD suitability score (0.0-1.0).
        
        Factors:
        - Time estimate (shorter = better for scattered attention)
        - Energy match
        - Clarity of description
        """
        score = 0.0
        
        # Time factor (15 min or less is ideal)
        if task.estimated_minutes <= 5:
            score += 0.4
        elif task.estimated_minutes <= 10:
            score += 0.3
        elif task.estimated_minutes <= 15:
            score += 0.2
        else:
            score += 0.1
        
        # Energy match
        if current_energy == "high" and task.energy_required == EnergyRequirement.HIGH:
            score += 0.3
        elif current_energy == "medium" and task.energy_required == EnergyRequirement.MEDIUM:
            score += 0.3
        elif current_energy == "low" and task.energy_required == EnergyRequirement.LOW:
            score += 0.3
        else:
            score += 0.1
        
        # Attention match
        if current_attention == "focused":
            # Can handle any task
            score += 0.3
        elif current_attention == "scattered":
            # Prefer simple, low-energy tasks
            if task.energy_required == EnergyRequirement.LOW and task.estimated_minutes <= 10:
                score += 0.3
            else:
                score += 0.1
        
        return min(1.0, score)
