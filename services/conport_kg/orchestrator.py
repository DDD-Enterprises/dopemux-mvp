#!/usr/bin/env python3
"""
KG Intelligence Orchestrator
Part of CONPORT-KG-2025 Phase 8 (Automation Layer)

Makes the knowledge graph run automatically, implicitly, and intelligently:
- Event-driven query triggers
- Background analysis and suggestions
- ADHD-safe proactive assistance
- Seamless Two-Plane integration

Decision #118 (to be logged)
"""

import asyncio
import os
import sys
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Add Integration Bridge client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from queries.overview import OverviewQueries
    from queries.exploration import ExplorationQueries
    from queries.deep_context import DeepContextQueries
    from queries.models import DecisionCard
except ImportError:
    print("⚠️  Query modules not yet available")

try:
    from src.integrations.bridge_client import IntegrationBridgeClient
    BRIDGE_AVAILABLE = True
except ImportError:
    BRIDGE_AVAILABLE = False
    print("⚠️  Integration Bridge client not available (will skip event publishing)")


@dataclass
class KGEvent:
    """Event structure for KG automation"""
    event_type: str
    payload: Dict[str, Any]
    timestamp: str
    priority: str = "normal"  # normal, high, critical


class KGOrchestrator:
    """
    Knowledge Graph Intelligence Orchestrator

    Automatically triggers queries based on events:
    - decision.logged → Find similar + check for tasks
    - task.started → Load decision context
    - file.opened → Show related decisions
    - sprint.planning → Pre-cache genealogy

    ADHD-Safe: All operations are background/passive
    """

    def __init__(self, redis_client=None, attention_monitor=None):
        """
        Initialize orchestrator

        Args:
            redis_client: For event bus and caching
            attention_monitor: ADHD attention state tracking
        """
        self.redis = redis_client
        self.attention_monitor = attention_monitor

        # Initialize query classes
        self.overview = OverviewQueries()
        self.exploration = ExplorationQueries()
        self.deep_context = DeepContextQueries()

        # Initialize Integration Bridge client for event publishing
        self.bridge = IntegrationBridgeClient() if BRIDGE_AVAILABLE else None

        status = "with Integration Bridge" if self.bridge else "without Integration Bridge (events disabled)"
        print(f"✅ KG Orchestrator initialized {status}")
        print("   Event handlers: decision.logged, task.started, file.opened")

    async def on_decision_logged(self, event: KGEvent):
        """
        Automatic trigger: New decision logged

        Actions (all background):
        1. Find similar decisions (similarity analysis)
        2. Check for IMPLEMENTS relationships → auto-create tasks
        3. Store suggestions in Redis (non-interruptive)

        User sees: "💡 3 related decisions found" (collapsed sidebar)
        """

        decision_id = event.payload.get('decision_id')
        summary = event.payload.get('summary', '')

        print(f"\n[KG Orchestrator] decision.logged: #{decision_id}")

        # Background: Find similar decisions
        try:
            similar = self.deep_context.search_full_text(
                summary.split()[0] if summary else "",  # First word
                limit=10
            )

            # Filter out self
            similar = [d for d in similar if d.id != decision_id]

            if self.redis and similar:
                # Store suggestions (non-interruptive)
                await self.redis.set(
                    f'kg:suggestions:{decision_id}',
                    [d.id for d in similar[:5]],  # Top 5
                    ex=3600  # 1 hour TTL
                )

                print(f"   → Found {len(similar)} similar decisions")
                print(f"   → Stored top 5 suggestions in Redis")

        except Exception as e:
            print(f"   ⚠️  Similarity analysis failed: {e}")

        # Background: Check for IMPLEMENTS relationships
        try:
            impl_decisions = self.exploration.find_by_relationship_type(
                decision_id,
                'IMPLEMENTS',
                'outgoing'
            )

            if impl_decisions and self.bridge:
                print(f"   → Found {len(impl_decisions)} IMPLEMENTS relationships")
                print(f"   → Publishing decision.requires_implementation event to Integration Bridge")

                # Publish event to Integration Bridge
                await self.bridge.save_custom_data(
                    workspace_id=os.getenv("WORKSPACE_ID", "/Users/hue/code/dopemux-mvp"),
                    category="automation_events",
                    key=f"decision_{decision_id}_requires_implementation",
                    value={
                        "event_type": "decision.requires_implementation",
                        "decision_id": decision_id,
                        "implementation_decisions": [d.id for d in impl_decisions],
                        "timestamp": event.timestamp,
                        "priority": event.priority
                    }
                )
                print(f"   ✅ Event published to Integration Bridge")

        except Exception as e:
            print(f"   ⚠️  IMPLEMENTS check failed: {e}")

    async def on_task_started(self, event: KGEvent):
        """
        Automatic trigger: Task started

        Actions (background):
        1. Load decision context for task.decision_refs
        2. Build genealogy map
        3. Pre-cache in Redis for instant Serena display

        User sees: Serena sidebar auto-populated when opening task files
        """

        task_id = event.payload.get('task_id')
        decision_refs = event.payload.get('decision_refs', [])

        if not decision_refs:
            return  # No decisions linked to task

        print(f"\n[KG Orchestrator] task.started: Task {task_id}")

        # TODO: PERFORMANCE - N+1 Query Problem (Issue from audit 2025-10-16)
        # Current: Loads decisions one-by-one (10 decisions = 10 queries)
        # Fix: Add ExplorationQueries.get_multiple_neighborhoods(decision_refs) for batch loading
        # Impact: 10x performance improvement for tasks with multiple decisions
        # Priority: MEDIUM (not blocking production, but degrades performance)

        # Background: Pre-load decision contexts
        contexts = []
        for decision_id in decision_refs:
            try:
                context = self.exploration.get_decision_neighborhood(
                    decision_id,
                    max_hops=2,
                    limit_per_hop=5  # Smaller for caching
                )
                contexts.append(context)

                print(f"   → Loaded context for decision #{decision_id}")
                print(f"      1-hop: {len(context.hop_1_neighbors)}, 2-hop: {len(context.hop_2_neighbors)}")

            except Exception as e:
                print(f"   ⚠️  Context loading failed for #{decision_id}: {e}")

        if self.redis and contexts:
            # Cache for Serena to use
            await self.redis.set(
                f'task:{task_id}:decision_context',
                contexts,
                ex=3600
            )
            print(f"   → Cached {len(contexts)} decision contexts")

    async def on_file_opened(self, event: KGEvent):
        """
        Automatic trigger: File opened in editor

        Actions (background):
        1. Extract module name from file path
        2. Search for related decisions
        3. Update Serena sidebar (passive display)

        User sees: "Related Decisions" panel in sidebar (collapsed by default)
        """

        file_path = event.payload.get('file_path', '')
        module_name = self._extract_module_name(file_path)

        if not module_name:
            return  # Can't extract module

        print(f"\n[KG Orchestrator] file.opened: {file_path}")
        print(f"   Module: {module_name}")

        # Background: Search for related decisions
        try:
            # Use Top-3 for sidebar (ADHD)
            related = self.overview.search_by_tag(module_name, limit=3)

            if not related:
                # Fallback: Full-text search
                related = self.deep_context.search_full_text(module_name, limit=5)[:3]

            print(f"   → Found {len(related)} related decisions")

            # TODO: Update Serena sidebar
            # await serena.update_sidebar('Related Decisions', related, collapsed=True)

        except Exception as e:
            print(f"   ⚠️  Related decision search failed: {e}")

    async def on_sprint_planning(self, event: KGEvent):
        """
        Automatic trigger: Sprint planning session started

        Actions (background):
        1. Load all sprint-tagged decisions
        2. Build genealogy map
        3. Calculate dependency risk score
        4. Pre-cache for Leantime dashboard

        User sees: Leantime dashboard with decision badges and risk score
        """

        sprint_id = event.payload.get('sprint_id')

        print(f"\n[KG Orchestrator] sprint.planning: {sprint_id}")

        # Background: Load sprint decisions
        try:
            sprint_decisions = self.overview.search_by_tag(sprint_id, limit=20)

            print(f"   → Found {len(sprint_decisions)} decisions for sprint")

            # Build genealogy for each
            genealogies = {}
            for decision in sprint_decisions:
                try:
                    neighborhood = self.exploration.get_decision_neighborhood(
                        decision.id,
                        max_hops=1
                    )
                    genealogies[decision.id] = neighborhood
                except:
                    pass

            print(f"   → Built genealogy for {len(genealogies)} decisions")

            # TODO: Cache for Leantime
            # await redis.set(f'sprint:{sprint_id}:context', genealogies, ex=7200)

        except Exception as e:
            print(f"   ⚠️  Sprint context loading failed: {e}")

    def _extract_module_name(self, file_path: str) -> Optional[str]:
        """Extract module name from file path"""
        # Simple extraction: filename without extension
        if not file_path:
            return None

        parts = file_path.split('/')
        if parts:
            filename = parts[-1]
            return filename.replace('.py', '').replace('.ts', '').replace('.js', '')

        return None


# Standalone test
if __name__ == "__main__":
    print("=" * 70)
    print("KG Orchestrator Test - Event Automation")
    print("=" * 70)

    orchestrator = KGOrchestrator()

    # Simulate events
    print("\n" + "=" * 70)
    print("SIMULATION: Testing Event Handlers")
    print("=" * 70)

    # Test 1: New decision logged
    event1 = KGEvent(
        event_type="decision.logged",
        payload={'decision_id': 117, 'summary': 'Phase 2 Query API'},
        timestamp=datetime.now().isoformat()
    )
    asyncio.run(orchestrator.on_decision_logged(event1))

    # Test 2: Task started
    event2 = KGEvent(
        event_type="task.started",
        payload={'task_id': 'T-123', 'decision_refs': [85, 92]},
        timestamp=datetime.now().isoformat()
    )
    asyncio.run(orchestrator.on_task_started(event2))

    # Test 3: File opened
    event3 = KGEvent(
        event_type="file.opened",
        payload={'file_path': 'services/serena/v2/mcp_client.py'},
        timestamp=datetime.now().isoformat()
    )
    asyncio.run(orchestrator.on_file_opened(event3))

    print("\n✅ All event handlers tested!")
