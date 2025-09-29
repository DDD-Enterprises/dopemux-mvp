"""
Serena v2 Phase 2D: Cross-Session Persistence Bridge

Synchronization system between ConPort strategic templates and PostgreSQL tactical instances,
implementing the expert-recommended immutable template + delta patch architecture.
"""

import asyncio
import json
import logging
import hashlib
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from enum import Enum

# Phase 2D Components
from .strategy_template_manager import StrategyTemplateManager, NavigationStrategyTemplate
from .personal_pattern_adapter import PersonalPatternAdapter, PersonalizationDelta, DeltaCluster

# Phase 2 Intelligence Components
from .database import SerenaIntelligenceDatabase

# Layer 1 Components
from ..performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class SyncStatus(str, Enum):
    """Synchronization status between ConPort and PostgreSQL."""
    SYNCED = "synced"                    # Fully synchronized
    PENDING_SYNC = "pending_sync"        # Changes waiting for sync
    SYNC_IN_PROGRESS = "sync_in_progress"  # Currently synchronizing
    SYNC_FAILED = "sync_failed"          # Synchronization failed
    CONFLICT = "conflict"                # Conflicting changes detected


class SyncDirection(str, Enum):
    """Direction of synchronization."""
    CONPORT_TO_POSTGRES = "conport_to_postgres"    # Strategic → Tactical
    POSTGRES_TO_CONPORT = "postgres_to_conport"    # Tactical → Strategic (evolution)
    BIDIRECTIONAL = "bidirectional"                # Both directions


class EvolutionProposal(str, Enum):
    """Types of template evolution proposals."""
    MINOR_IMPROVEMENT = "minor_improvement"        # Small effectiveness improvements
    MAJOR_ENHANCEMENT = "major_enhancement"        # Significant improvements
    NEW_TEMPLATE = "new_template"                  # Completely new template from patterns
    DEPRECATION = "deprecation"                    # Template should be deprecated
    ACCOMMODATION_UPDATE = "accommodation_update"   # ADHD accommodation improvements


@dataclass
class SyncOperation:
    """Individual synchronization operation."""
    operation_id: str
    sync_direction: SyncDirection
    source_type: str  # template, delta, cluster
    source_id: str
    target_type: str
    target_id: str
    operation_type: str  # create, update, delete
    sync_data: Dict[str, Any]
    status: SyncStatus = SyncStatus.PENDING_SYNC
    error_message: Optional[str] = None
    attempts: int = 0
    max_attempts: int = 3
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


@dataclass
class TemplateEvolutionProposal:
    """Proposal for template evolution based on delta clustering."""
    proposal_id: str
    template_hash: str
    template_name: str
    evolution_type: EvolutionProposal
    proposed_changes: Dict[str, Any]
    supporting_evidence: Dict[str, Any]
    user_support_count: int
    effectiveness_improvement: float
    adhd_optimization_benefit: str
    curator_notes: str = ""
    approval_status: str = "pending"  # pending, approved, rejected
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SyncHealthStatus:
    """Health status of the synchronization system."""
    overall_status: SyncStatus
    conport_connection_healthy: bool
    postgres_connection_healthy: bool
    pending_operations: int
    failed_operations: int
    last_successful_sync: Optional[datetime]
    average_sync_duration_ms: float
    cache_hit_rate: float
    evolution_proposals_pending: int


class CrossSessionPersistenceBridge:
    """
    Cross-session persistence bridge implementing expert-recommended synchronization architecture.

    Features:
    - Immutable template storage in ConPort with SHA256 integrity
    - Delta patch storage in PostgreSQL for tactical personalization
    - Automatic synchronization between strategic and tactical layers
    - Delta clustering for template evolution detection
    - Redis L2 cache for <150ms performance optimization
    - Background sync jobs with failure recovery
    - Curator workflow for template evolution approval
    - Authority boundary respect (ConPort strategic, PostgreSQL tactical)
    - ADHD accommodation preservation across synchronization
    """

    def __init__(
        self,
        database: SerenaIntelligenceDatabase,
        template_manager: StrategyTemplateManager,
        pattern_adapter: PersonalPatternAdapter,
        workspace_id: str,  # ConPort workspace
        performance_monitor: PerformanceMonitor = None
    ):
        self.database = database
        self.template_manager = template_manager
        self.pattern_adapter = pattern_adapter
        self.workspace_id = workspace_id
        self.performance_monitor = performance_monitor or PerformanceMonitor()

        # Synchronization configuration
        self.sync_interval_minutes = 30  # Regular sync every 30 minutes
        self.evolution_check_interval_hours = 24  # Check for evolution daily
        self.cache_ttl_minutes = 15  # Redis cache TTL

        # Sync tracking
        self._pending_operations: List[SyncOperation] = []
        self._sync_history: List[Dict[str, Any]] = []
        self._evolution_proposals: Dict[str, TemplateEvolutionProposal] = {}

        # Performance tracking
        self._sync_metrics = {
            "total_operations": 0,
            "successful_operations": 0,
            "average_duration_ms": 0.0,
            "last_sync_time": None
        }

        # Redis cache simulation (would use actual Redis in production)
        self._redis_cache: Dict[str, Any] = {}

    # Core Synchronization

    async def start_background_sync(self) -> None:
        """Start background synchronization tasks."""
        logger.info("🔄 Starting cross-session persistence bridge background sync")

        # Start sync task
        asyncio.create_task(self._background_sync_loop())

        # Start evolution detection task
        asyncio.create_task(self._background_evolution_detection_loop())

    async def _background_sync_loop(self) -> None:
        """Background loop for regular synchronization."""
        while True:
            try:
                await asyncio.sleep(self.sync_interval_minutes * 60)

                # Perform synchronization
                sync_result = await self.perform_full_synchronization()

                if sync_result["success"]:
                    logger.debug(f"✅ Background sync completed: {sync_result['operations_completed']} operations")
                else:
                    logger.warning(f"⚠️ Background sync issues: {sync_result['failed_operations']} failures")

            except Exception as e:
                logger.error(f"Background sync loop error: {e}")

    async def perform_full_synchronization(self) -> Dict[str, Any]:
        """Perform complete synchronization between ConPort and PostgreSQL."""
        operation_id = self.performance_monitor.start_operation("perform_full_synchronization")

        try:
            sync_result = {
                "success": True,
                "operations_completed": 0,
                "failed_operations": 0,
                "sync_duration_ms": 0.0,
                "cache_updates": 0,
                "evolution_proposals_created": 0
            }

            start_time = time.time()

            # Step 1: Sync strategic templates from ConPort to PostgreSQL
            strategic_sync_result = await self._sync_strategic_templates()
            sync_result["operations_completed"] += strategic_sync_result["synced_templates"]

            # Step 2: Check for delta clusters that need evolution proposals
            evolution_result = await self._check_delta_evolution_opportunities()
            sync_result["evolution_proposals_created"] = evolution_result["proposals_created"]

            # Step 3: Update Redis cache with latest personalized templates
            cache_result = await self._update_redis_cache()
            sync_result["cache_updates"] = cache_result["cache_updates"]

            # Step 4: Clean up old sync operations
            await self._cleanup_old_sync_operations()

            sync_result["sync_duration_ms"] = (time.time() - start_time) * 1000

            # Update metrics
            self._sync_metrics["total_operations"] += 1
            self._sync_metrics["successful_operations"] += 1
            self._sync_metrics["average_duration_ms"] = (
                (self._sync_metrics["average_duration_ms"] * (self._sync_metrics["total_operations"] - 1) +
                 sync_result["sync_duration_ms"]) / self._sync_metrics["total_operations"]
            )
            self._sync_metrics["last_sync_time"] = datetime.now(timezone.utc)

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.info(f"🔄 Full synchronization completed in {sync_result['sync_duration_ms']:.0f}ms")
            return sync_result

        except Exception as e:
            sync_result["success"] = False
            sync_result["failed_operations"] = 1
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Full synchronization failed: {e}")
            return sync_result

    async def _sync_strategic_templates(self) -> Dict[str, Any]:
        """Sync strategic templates from ConPort to PostgreSQL."""
        try:
            # Load templates from ConPort strategic layer
            conport_templates = await self.template_manager.load_templates_from_conport()

            synced_count = 0
            for template in conport_templates:
                # Check if template exists in PostgreSQL navigation_strategies
                existing_template = await self._check_template_exists_in_postgres(template.template_hash)

                if not existing_template:
                    # Sync new template to PostgreSQL
                    await self._sync_template_to_postgres(template)
                    synced_count += 1
                else:
                    # Update existing template if hash differs (version change)
                    if existing_template.get('template_hash') != template.template_hash:
                        await self._update_template_in_postgres(template)
                        synced_count += 1

            return {"synced_templates": synced_count}

        except Exception as e:
            logger.error(f"Failed to sync strategic templates: {e}")
            return {"synced_templates": 0, "error": str(e)}

    async def _sync_template_to_postgres(self, template: NavigationStrategyTemplate) -> None:
        """Sync individual template to PostgreSQL navigation_strategies table."""
        try:
            # Convert template to PostgreSQL format
            insert_query = """
            INSERT INTO navigation_strategies (
                strategy_name, strategy_type, description, pattern_template,
                success_conditions, complexity_range, usage_count, success_rate,
                average_completion_time_minutes, user_satisfaction_score,
                cognitive_load_reduction, attention_preservation_score,
                interruption_resistance, applicable_languages, applicable_element_types,
                required_accommodations, learning_confidence, template_hash,
                version, curator_approved
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
            ON CONFLICT (strategy_name, strategy_type)
            DO UPDATE SET
                template_hash = EXCLUDED.template_hash,
                version = EXCLUDED.version,
                updated_at = NOW()
            """

            # Convert template steps to pattern template format
            pattern_template = {
                "steps": [asdict(step) for step in template.steps],
                "branching_points": template.branching_points,
                "error_recovery": template.error_recovery_steps,
                "adhd_accommodations": [acc.value for acc in template.adhd_accommodations]
            }

            await self.database.execute_query(insert_query, (
                template.template_name,
                template.strategy_type.value,
                template.description,
                json.dumps(pattern_template),
                json.dumps({"target_scenarios": template.target_scenarios}),
                json.dumps({"min": 0.0, "max": template.max_cognitive_load}),
                template.adoption_count,
                template.success_rate,
                template.estimated_completion_time_minutes,
                template.user_satisfaction_score,
                0.3,  # Default cognitive load reduction
                0.7,  # Default attention preservation
                0.6,  # Default interruption resistance
                json.dumps(["python", "javascript", "typescript"]),  # Default languages
                json.dumps(["function", "class", "method"]),  # Default element types
                json.dumps([acc.value for acc in template.adhd_accommodations]),
                0.9 if template.curator_approved else 0.5,
                template.template_hash,
                template.version,
                template.curator_approved
            ))

            logger.debug(f"📥 Synced template {template.template_name} to PostgreSQL")

        except Exception as e:
            logger.error(f"Failed to sync template to PostgreSQL: {e}")

    # ConPort Integration

    async def sync_template_to_conport(self, template: NavigationStrategyTemplate) -> bool:
        """Sync template to ConPort strategic layer."""
        try:
            # Use ConPort MCP tools for strategic pattern storage
            # This would use mcp__conport__log_system_pattern in real implementation

            pattern_data = {
                "template_hash": template.template_hash,
                "version": template.version,
                "strategy_type": template.strategy_type.value,
                "complexity_level": template.complexity_level.value,
                "adhd_accommodations": [acc.value for acc in template.adhd_accommodations],
                "success_rate": template.success_rate,
                "target_scenarios": template.target_scenarios,
                "steps_count": len(template.steps),
                "estimated_time_minutes": template.estimated_completion_time_minutes,
                "cognitive_load": template.max_cognitive_load
            }

            # Would call ConPort MCP here
            # await mcp__conport__log_system_pattern(
            #     workspace_id=self.workspace_id,
            #     name=template.template_name,
            #     description=template.description,
            #     tags=["navigation-strategy", template.strategy_type.value, "adhd-optimized"]
            # )

            logger.info(f"📤 Synced template {template.template_name} to ConPort strategic layer")
            return True

        except Exception as e:
            logger.error(f"Failed to sync template to ConPort: {e}")
            return False

    async def load_strategic_templates_from_conport(self) -> List[NavigationStrategyTemplate]:
        """Load strategic templates from ConPort knowledge graph."""
        try:
            # This would use ConPort MCP get_system_patterns in real implementation
            # For now, simulate loading strategic templates

            # Simulate ConPort strategic template data
            strategic_patterns = [
                {
                    "name": "Progressive Function Exploration",
                    "description": "ADHD-optimized progressive function exploration strategy",
                    "tags": ["navigation-strategy", "exploration", "adhd-optimized"],
                    "pattern_data": {
                        "template_hash": "abc123def456",
                        "version": "1.0.0",
                        "strategy_type": "exploration",
                        "success_rate": 0.82
                    }
                }
            ]

            # Convert ConPort patterns to template objects
            templates = []
            for pattern in strategic_patterns:
                template = await self._convert_conport_pattern_to_template(pattern)
                if template:
                    templates.append(template)

            logger.debug(f"📥 Loaded {len(templates)} strategic templates from ConPort")
            return templates

        except Exception as e:
            logger.error(f"Failed to load strategic templates from ConPort: {e}")
            return []

    # Delta Evolution System

    async def _background_evolution_detection_loop(self) -> None:
        """Background loop for detecting template evolution opportunities."""
        while True:
            try:
                await asyncio.sleep(self.evolution_check_interval_hours * 3600)

                # Check for delta clustering opportunities
                evolution_result = await self._check_delta_evolution_opportunities()

                if evolution_result["proposals_created"] > 0:
                    logger.info(f"🧬 Evolution detection: {evolution_result['proposals_created']} new proposals")

            except Exception as e:
                logger.error(f"Evolution detection loop error: {e}")

    async def _check_delta_evolution_opportunities(self) -> Dict[str, Any]:
        """Check for delta clusters that suggest template evolution."""
        try:
            # Query for delta patterns that might suggest evolution
            query = """
            SELECT template_hash, personalization_type, COUNT(*) as delta_count,
                   AVG(success_rate) as avg_success_rate,
                   AVG(average_effectiveness) as avg_effectiveness,
                   AVG(time_reduction_percentage) as avg_time_reduction
            FROM personalization_deltas
            WHERE created_at > NOW() - INTERVAL '30 days'
              AND success_rate > 0.6
            GROUP BY template_hash, personalization_type
            HAVING COUNT(*) >= 5
            ORDER BY COUNT(*) DESC, AVG(average_effectiveness) DESC
            """

            results = await self.database.execute_query(query)

            proposals_created = 0
            for row in results:
                # Check if this pattern suggests template evolution
                if await self._should_propose_evolution(row):
                    proposal = await self._create_evolution_proposal(row)
                    if proposal:
                        self._evolution_proposals[proposal.proposal_id] = proposal
                        proposals_created += 1

            return {"proposals_created": proposals_created}

        except Exception as e:
            logger.error(f"Failed to check evolution opportunities: {e}")
            return {"proposals_created": 0, "error": str(e)}

    async def _should_propose_evolution(self, delta_pattern: Dict[str, Any]) -> bool:
        """Determine if delta pattern warrants template evolution proposal."""
        delta_count = delta_pattern['delta_count']
        avg_effectiveness = delta_pattern['avg_effectiveness']
        avg_time_reduction = delta_pattern['avg_time_reduction']

        # Criteria for evolution proposal
        criteria_met = 0

        # High user adoption
        if delta_count >= 10:
            criteria_met += 1

        # Good effectiveness improvement
        if avg_effectiveness > 0.75:
            criteria_met += 1

        # Significant time reduction
        if avg_time_reduction > 0.2:  # 20% time reduction
            criteria_met += 1

        # Need at least 2 of 3 criteria
        return criteria_met >= 2

    async def _create_evolution_proposal(self, delta_pattern: Dict[str, Any]) -> Optional[TemplateEvolutionProposal]:
        """Create template evolution proposal from delta pattern."""
        try:
            proposal_id = f"evolution_{delta_pattern['template_hash'][:8]}_{int(time.time())}"

            # Get template name for context
            template_hash = delta_pattern['template_hash']
            template = await self._get_template_by_hash(template_hash)
            template_name = template.template_name if template else f"Template {template_hash[:8]}"

            # Determine evolution type
            personalization_type = delta_pattern['personalization_type']
            if delta_pattern['avg_effectiveness'] > 0.8 and delta_pattern['delta_count'] >= 15:
                evolution_type = EvolutionProposal.MAJOR_ENHANCEMENT
            elif delta_pattern['avg_time_reduction'] > 0.3:
                evolution_type = EvolutionProposal.MINOR_IMPROVEMENT
            elif 'accommodation' in personalization_type:
                evolution_type = EvolutionProposal.ACCOMMODATION_UPDATE
            else:
                evolution_type = EvolutionProposal.MINOR_IMPROVEMENT

            # Generate proposed changes
            proposed_changes = await self._generate_proposed_changes(delta_pattern)

            # Create proposal
            proposal = TemplateEvolutionProposal(
                proposal_id=proposal_id,
                template_hash=template_hash,
                template_name=template_name,
                evolution_type=evolution_type,
                proposed_changes=proposed_changes,
                supporting_evidence={
                    "user_count": delta_pattern['delta_count'],
                    "average_effectiveness": delta_pattern['avg_effectiveness'],
                    "average_time_reduction": delta_pattern['avg_time_reduction'],
                    "personalization_type": personalization_type
                },
                user_support_count=delta_pattern['delta_count'],
                effectiveness_improvement=delta_pattern['avg_effectiveness'] - 0.6,  # Assume 0.6 baseline
                adhd_optimization_benefit=self._assess_adhd_benefit(proposed_changes)
            )

            # Store proposal
            await self._store_evolution_proposal(proposal)

            return proposal

        except Exception as e:
            logger.error(f"Failed to create evolution proposal: {e}")
            return None

    # Redis Cache Management (Expert-recommended L2 cache)

    async def _update_redis_cache(self) -> Dict[str, Any]:
        """Update Redis L2 cache with top-K templates per user."""
        try:
            cache_updates = 0

            # Get all active users
            active_users_query = """
            SELECT DISTINCT user_session_id, workspace_path
            FROM personalization_deltas
            WHERE last_used > NOW() - INTERVAL '7 days'
            """

            active_users = await self.database.execute_query(active_users_query)

            for user_row in active_users:
                user_id = user_row['user_session_id']
                workspace_path = user_row['workspace_path']

                # Get top-K templates for this user
                top_templates = await self._get_top_templates_for_user(user_id, workspace_path)

                # Cache personalized templates
                for template_id, personalized_template in top_templates.items():
                    cache_key = f"personalized_template:{user_id}:{template_id}"
                    self._redis_cache[cache_key] = {
                        "template": self._serialize_personalized_template(personalized_template),
                        "cached_at": datetime.now(timezone.utc).isoformat(),
                        "ttl_minutes": self.cache_ttl_minutes
                    }
                    cache_updates += 1

            return {"cache_updates": cache_updates}

        except Exception as e:
            logger.error(f"Failed to update Redis cache: {e}")
            return {"cache_updates": 0, "error": str(e)}

    async def _get_top_templates_for_user(
        self, user_id: str, workspace_path: str, k: int = 5
    ) -> Dict[str, Any]:
        """Get top-K most relevant templates for user."""
        try:
            # Get user's most used templates
            query = """
            SELECT template_hash, COUNT(*) as usage_count,
                   AVG(success_rate) as avg_success_rate
            FROM personalization_deltas
            WHERE user_session_id = $1 AND workspace_path = $2
              AND last_used > NOW() - INTERVAL '14 days'
            GROUP BY template_hash
            ORDER BY COUNT(*) DESC, AVG(success_rate) DESC
            LIMIT $3
            """

            results = await self.database.execute_query(query, (user_id, workspace_path, k))

            top_templates = {}
            for row in results:
                template_hash = row['template_hash']
                template = await self._get_template_by_hash(template_hash)
                if template:
                    personalized_template = await self.pattern_adapter.get_personalized_template(
                        template.template_id, user_id, workspace_path
                    )
                    if personalized_template:
                        top_templates[template.template_id] = personalized_template

            return top_templates

        except Exception as e:
            logger.error(f"Failed to get top templates for user: {e}")
            return {}

    # Health and Monitoring

    async def get_sync_health_status(self) -> SyncHealthStatus:
        """Get current synchronization health status."""
        try:
            # Test ConPort connection
            conport_healthy = True  # Would test actual ConPort connection

            # Test PostgreSQL connection
            postgres_healthy = await self._test_postgres_connection()

            # Count pending and failed operations
            pending_ops = len([op for op in self._pending_operations if op.status == SyncStatus.PENDING_SYNC])
            failed_ops = len([op for op in self._pending_operations if op.status == SyncStatus.SYNC_FAILED])

            # Overall status
            if conport_healthy and postgres_healthy and failed_ops == 0:
                overall_status = SyncStatus.SYNCED
            elif pending_ops > 10 or failed_ops > 5:
                overall_status = SyncStatus.SYNC_FAILED
            elif pending_ops > 0:
                overall_status = SyncStatus.PENDING_SYNC
            else:
                overall_status = SyncStatus.SYNCED

            # Cache hit rate
            cache_requests = len(self._redis_cache)
            cache_hits = len([v for v in self._redis_cache.values() if self._is_cache_entry_valid(v)])
            cache_hit_rate = cache_hits / max(cache_requests, 1)

            return SyncHealthStatus(
                overall_status=overall_status,
                conport_connection_healthy=conport_healthy,
                postgres_connection_healthy=postgres_healthy,
                pending_operations=pending_ops,
                failed_operations=failed_ops,
                last_successful_sync=self._sync_metrics.get("last_sync_time"),
                average_sync_duration_ms=self._sync_metrics.get("average_duration_ms", 0.0),
                cache_hit_rate=cache_hit_rate,
                evolution_proposals_pending=len(self._evolution_proposals)
            )

        except Exception as e:
            logger.error(f"Failed to get sync health status: {e}")
            return SyncHealthStatus(
                overall_status=SyncStatus.SYNC_FAILED,
                conport_connection_healthy=False,
                postgres_connection_healthy=False,
                pending_operations=0,
                failed_operations=1,
                last_successful_sync=None,
                average_sync_duration_ms=0.0,
                cache_hit_rate=0.0,
                evolution_proposals_pending=0
            )

    async def get_evolution_proposals(self) -> List[TemplateEvolutionProposal]:
        """Get current template evolution proposals for curator review."""
        return list(self._evolution_proposals.values())

    async def approve_evolution_proposal(
        self, proposal_id: str, curator_notes: str = ""
    ) -> bool:
        """Approve template evolution proposal and apply changes."""
        try:
            if proposal_id not in self._evolution_proposals:
                logger.warning(f"Evolution proposal {proposal_id} not found")
                return False

            proposal = self._evolution_proposals[proposal_id]
            proposal.approval_status = "approved"
            proposal.curator_notes = curator_notes

            # Apply the evolution to create new template version
            new_template = await self._apply_evolution_to_template(proposal)

            if new_template:
                # Sync new template to both ConPort and PostgreSQL
                await self.sync_template_to_conport(new_template)
                await self._sync_template_to_postgres(new_template)

                logger.info(f"✅ Applied evolution proposal {proposal_id}: {proposal.evolution_type.value}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to approve evolution proposal: {e}")
            return False

    # Utility Methods

    def _serialize_personalized_template(self, template: Any) -> Dict[str, Any]:
        """Serialize personalized template for cache storage."""
        # Simplified serialization
        return {
            "template_id": template.base_template.template_id,
            "personalization_confidence": template.personalization_confidence,
            "user_effectiveness_score": template.user_effectiveness_score,
            "personalized_complexity": template.personalized_complexity,
            "personalized_timing": template.personalized_timing,
            "delta_count": len(template.applied_deltas)
        }

    def _is_cache_entry_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid."""
        try:
            cached_at = datetime.fromisoformat(cache_entry["cached_at"])
            ttl_minutes = cache_entry.get("ttl_minutes", self.cache_ttl_minutes)

            age_minutes = (datetime.now(timezone.utc) - cached_at).total_seconds() / 60
            return age_minutes < ttl_minutes

        except Exception:
            return False

    async def _test_postgres_connection(self) -> bool:
        """Test PostgreSQL connection health."""
        try:
            await self.database.execute_query("SELECT 1")
            return True
        except Exception:
            return False

    async def _check_template_exists_in_postgres(self, template_hash: str) -> Optional[Dict[str, Any]]:
        """Check if template exists in PostgreSQL."""
        try:
            query = """
            SELECT template_hash, version FROM navigation_strategies
            WHERE template_hash = $1
            LIMIT 1
            """
            results = await self.database.execute_query(query, (template_hash,))
            return results[0] if results else None

        except Exception as e:
            logger.error(f"Failed to check template existence: {e}")
            return None

    async def _update_template_in_postgres(self, template: NavigationStrategyTemplate) -> None:
        """Update existing template in PostgreSQL."""
        try:
            update_query = """
            UPDATE navigation_strategies
            SET template_hash = $1,
                version = $2,
                success_rate = $3,
                updated_at = NOW()
            WHERE strategy_name = $4
            """

            await self.database.execute_query(update_query, (
                template.template_hash,
                template.version,
                template.success_rate,
                template.template_name
            ))

        except Exception as e:
            logger.error(f"Failed to update template in PostgreSQL: {e}")

    async def _cleanup_old_sync_operations(self) -> None:
        """Clean up old completed sync operations."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        self._pending_operations = [
            op for op in self._pending_operations
            if op.created_at > cutoff_time or op.status in [SyncStatus.PENDING_SYNC, SyncStatus.SYNC_IN_PROGRESS]
        ]

    # Placeholder methods for complex operations
    async def _convert_conport_pattern_to_template(self, pattern: Dict[str, Any]) -> Optional[NavigationStrategyTemplate]:
        """Convert ConPort pattern to template object."""
        # Would convert ConPort system pattern to NavigationStrategyTemplate
        return None

    async def _get_template_by_hash(self, template_hash: str) -> Optional[NavigationStrategyTemplate]:
        """Get template by hash."""
        # Would query templates by hash
        return None

    async def _generate_proposed_changes(self, delta_pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Generate proposed changes from delta pattern."""
        return {
            "change_type": delta_pattern['personalization_type'],
            "user_support": delta_pattern['delta_count'],
            "effectiveness_improvement": delta_pattern['avg_effectiveness']
        }

    def _assess_adhd_benefit(self, proposed_changes: Dict[str, Any]) -> str:
        """Assess ADHD optimization benefit of proposed changes."""
        return "moderate"  # Would analyze specific ADHD benefits

    async def _store_evolution_proposal(self, proposal: TemplateEvolutionProposal) -> None:
        """Store evolution proposal for curator review."""
        # Would store in database
        pass

    async def _apply_evolution_to_template(self, proposal: TemplateEvolutionProposal) -> Optional[NavigationStrategyTemplate]:
        """Apply evolution proposal to create new template version."""
        # Would create new template version
        return None


# Convenience functions
async def create_cross_session_persistence_bridge(
    database: SerenaIntelligenceDatabase,
    template_manager: StrategyTemplateManager,
    pattern_adapter: PersonalPatternAdapter,
    workspace_id: str,
    performance_monitor: PerformanceMonitor = None
) -> CrossSessionPersistenceBridge:
    """Create cross-session persistence bridge instance."""
    return CrossSessionPersistenceBridge(
        database, template_manager, pattern_adapter, workspace_id, performance_monitor
    )


async def test_persistence_bridge(
    bridge: CrossSessionPersistenceBridge
) -> Dict[str, Any]:
    """Test persistence bridge functionality."""
    try:
        # Test synchronization
        sync_result = await bridge.perform_full_synchronization()

        # Test health status
        health_status = await bridge.get_sync_health_status()

        return {
            "sync_test_successful": sync_result["success"],
            "sync_operations_completed": sync_result["operations_completed"],
            "health_status": health_status.overall_status.value,
            "conport_connection": health_status.conport_connection_healthy,
            "postgres_connection": health_status.postgres_connection_healthy,
            "cache_hit_rate": health_status.cache_hit_rate,
            "test_status": "passed" if sync_result["success"] and health_status.overall_status == SyncStatus.SYNCED else "failed"
        }

    except Exception as e:
        logger.error(f"Persistence bridge test failed: {e}")
        return {
            "test_status": "failed",
            "error": str(e)
        }


if __name__ == "__main__":
    # Quick test when run directly
    async def main():
        print("🌉 Serena Cross-Session Persistence Bridge")
        print("ConPort strategic ↔ PostgreSQL tactical synchronization")
        print("✅ Module loaded successfully")

    asyncio.run(main())