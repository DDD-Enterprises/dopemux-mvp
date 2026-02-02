#!/usr/bin/env python3
"""
Tier 1: Overview Queries
ADHD-optimized top-level decision discovery

Limits cognitive load with:
- Maximum 3 results (prevents overwhelm)
- High-level summaries only
- Recent decisions first

Phase 4 Refactor: Uses AGEClient with connection pooling (Decision #117)
"""

import os

import logging

logger = logging.getLogger(__name__)

import sys
import subprocess
from typing import List, Union, Optional
from dataclasses import dataclass, field
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from age_client import AGEClient
    from queries.models import DecisionCard, DecisionSummary
except ImportError:
    # Fallback for testing
    sys.path.insert(0, '/Users/hue/code/dopemux-mvp/services/conport_kg')
    from age_client import AGEClient
    # Import models inline for testing
    # Safe fallback import instead of exec
    import importlib.util
    _models_path = '/Users/hue/code/dopemux-mvp/services/conport_kg/queries/models.py'
    spec = importlib.util.spec_from_file_location('queries.models_fallback', _models_path)
    models_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(models_mod)
    DecisionCard = models_mod.DecisionCard
    DecisionSummary = models_mod.DecisionSummary


# Feature flag for rollback safety
USE_DIRECT_CONNECTION = os.getenv('KG_DIRECT_CONNECTION', 'true').lower() == 'true'


class OverviewQueries:
    """
    Tier 1: Overview - Top-3 Pattern

    Provides highest-level view of decision landscape.
    Designed for quick orientation and context loading.

    Now uses AGEClient for <50ms performance (was 50-100ms with docker exec)
    """

    @staticmethod
    def _validate_limit(limit: int, max_limit: int = 100) -> int:
        """
        Validate and sanitize limit parameter to prevent SQL injection

        Security: CRITICAL - Prevents SQL injection via LIMIT clause

        Args:
            limit: User-provided limit value
            max_limit: Maximum allowed limit (default 100)

        Returns:
            Validated integer limit

        Raises:
            ValueError: If limit is invalid or out of range
        """
        # Ensure it's an integer (prevents SQL injection)
        if not isinstance(limit, int):
            try:
                limit = int(limit)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid limit: must be integer, got {type(limit).__name__}") from e

        # Range validation
        if limit < 1:
            raise ValueError(f"Invalid limit: must be >= 1, got {limit}")
        if limit > max_limit:
            raise ValueError(f"Invalid limit: must be <= {max_limit}, got {limit}")

        return limit

    def __init__(self, age_url: str = None, use_direct: bool = None):
        """
        Initialize with AGEClient or fallback to docker exec

        Args:
            age_url: Optional connection URL (uses defaults if not provided)
            use_direct: Override feature flag for testing
        """
        self.use_direct = use_direct if use_direct is not None else USE_DIRECT_CONNECTION

        if self.use_direct:
            try:
                self.client = AGEClient()
                logger.info(f"✅ OverviewQueries using AGEClient (direct connection)")
            except Exception as e:
                logger.error(f"⚠️  AGEClient failed, falling back to docker exec: {e}")
                self.client = None
                self.use_direct = False
        else:
            self.client = None
            logger.info(f"ℹ️  OverviewQueries using docker exec (feature flag disabled)")

    def _execute_cypher_direct(self, cypher: str, workspace_path: Optional[str] = None) -> List[dict]:
        """Execute via AGEClient (fast path)"""
        return self.client.execute_cypher(cypher, workspace_path=workspace_path)

    def _execute_cypher_fallback(self, cypher: str) -> List[dict]:
        """Execute via docker exec (fallback path)"""
        cmd = [
            'docker', 'exec', 'dopemux-postgres-age',
            'psql', '-U', 'dopemux_age', '-d', 'dopemux_knowledge_graph',
            '-t', '-c', f"LOAD 'age'; SET search_path = ag_catalog, conport_knowledge, public; {cypher}"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            raise Exception(f"Query failed: {result.stderr}")

        # Parse simple results
        lines = [l.strip() for l in result.stdout.strip().split('\n') if l.strip() and '(' not in l]

        # Convert to list of dicts (matching AGEClient format)
        parsed_results = []
        for line in lines:
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                # This is a simplified parser - AGEClient handles this better
                parsed_results.append({'raw': line, 'parts': parts})

        return parsed_results

    def _execute_cypher(self, cypher: str, workspace_path: Optional[str] = None) -> List[dict]:
        """Execute Cypher query via best available method"""
        if self.use_direct and self.client:
            return self._execute_cypher_direct(cypher, workspace_path=workspace_path)
        else:
            return self._execute_cypher_fallback(cypher)

    def get_recent_decisions(self, limit: int = 3, workspace_path: Optional[str] = None) -> List[DecisionCard]:
        """
        Get most recent decisions (Top-3 pattern)

        ADHD Optimization: Limits to 3 for quick scanning

        Args:
            limit: Maximum number of decisions to return
            workspace_path: Optional workspace path for scoped queries

        Returns: List[DecisionCard] with typed data
        """
        # Security: Validate limit to prevent SQL injection
        limit = self._validate_limit(limit, max_limit=100)

        cypher = f"""
            SELECT * FROM cypher('conport_knowledge', $$
                MATCH (d:Decision)
                RETURN d.id, d.summary, d.timestamp
                ORDER BY d.timestamp DESC
                LIMIT {limit}
            $$) as (id agtype, summary agtype, timestamp agtype);
        """

        results = self._execute_cypher(cypher, workspace_path=workspace_path)

        decisions = []
        for row in results:
            if self.use_direct:
                # AGEClient returns parsed dicts
                decisions.append(DecisionCard(
                    id=int(row['id']),
                    summary=str(row['summary']),
                    timestamp=str(row['timestamp'])
                ))
            else:
                # Fallback parser
                parts = row.get('parts', [])
                if len(parts) >= 3:
                    decisions.append(DecisionCard(
                        id=int(parts[0]),
                        summary=parts[1].strip('"'),
                        timestamp=parts[2]
                    ))

        return decisions

    def get_decision_summary(self, decision_id: int, workspace_path: Optional[str] = None) -> DecisionSummary:
        """
        Get single decision with 1-hop context count

        Shows decision + count of related (doesn't load full related decisions)

        Args:
            decision_id: ID of decision to retrieve
            workspace_path: Optional workspace path for scoped queries

        Returns: DecisionSummary with typed data
        """

        cypher = f"""
            SELECT * FROM cypher('conport_knowledge', $$
                MATCH (d:Decision {{id: {decision_id}}})
                OPTIONAL MATCH (d)-[r]-(related:Decision)
                WITH d, COUNT(DISTINCT related) as rel_count, COLLECT(DISTINCT type(r)) as rel_types
                RETURN d.id, d.summary, d.rationale, rel_count, rel_types
            $$) as (id agtype, summary agtype, rationale agtype, rel_count agtype, rel_types agtype);
        """

        results = self._execute_cypher(cypher, workspace_path=workspace_path)

        if results and len(results) > 0:
            row = results[0]

            if self.use_direct:
                return DecisionSummary(
                    id=int(row['id']),
                    summary=str(row['summary']),
                    timestamp="",  # Not queried in this view
                    rationale=str(row.get('rationale', '')),
                    related_count=int(row.get('rel_count', 0)),
                    relationship_types=row.get('rel_types', [])
                )
            else:
                # Fallback parser
                parts = row.get('parts', [])
                if len(parts) >= 3:
                    return DecisionSummary(
                        id=int(parts[0]),
                        summary=parts[1].strip('"'),
                        timestamp="",
                        rationale=parts[2].strip('"') if len(parts) > 2 else '',
                        related_count=int(parts[3]) if len(parts) > 3 else 0
                    )

        return DecisionSummary(id=decision_id, summary="Not found", timestamp="")

    def get_root_decisions(self, limit: int = 3, workspace_path: Optional[str] = None) -> List[DecisionCard]:
        """
        Get root decisions (no incoming edges)

        These are foundational decisions that others build upon.
        Good starting point for genealogy exploration.

        Args:
            limit: Maximum number of decisions to return
            workspace_path: Optional workspace path for scoped queries

        Returns: List[DecisionCard] with typed data
        """
        # Security: Validate limit to prevent SQL injection
        limit = self._validate_limit(limit, max_limit=100)

        cypher = f"""
            SELECT * FROM cypher('conport_knowledge', $$
                MATCH (d:Decision)
                WHERE NOT EXISTS {{
                    MATCH (d)<-[]-(other:Decision)
                }}
                RETURN d.id, d.summary, d.timestamp
                ORDER BY d.id DESC
                LIMIT {limit}
            $$) as (id agtype, summary agtype, timestamp agtype);
        """

        results = self._execute_cypher(cypher, workspace_path=workspace_path)

        decisions = []
        for row in results:
            if self.use_direct:
                decisions.append(DecisionCard(
                    id=int(row['id']),
                    summary=str(row['summary']),
                    timestamp=str(row.get('timestamp', ''))
                ))
            else:
                parts = row.get('parts', [])
                if len(parts) >= 2:
                    decisions.append(DecisionCard(
                        id=int(parts[0]),
                        summary=parts[1].strip('"'),
                        timestamp=parts[2] if len(parts) > 2 else ''
                    ))

        return decisions

    def search_by_tag(self, tag: str, limit: int = 3, workspace_path: Optional[str] = None) -> List[DecisionCard]:
        """
        Search decisions by tag (Top-3 pattern)

        ADHD Optimization: Limits to 3 for quick scanning
        Tags are stored as JSONB array in AGE

        Args:
            tag: Tag to search for
            limit: Maximum number of decisions to return
            workspace_path: Optional workspace path for scoped queries

        Returns: List[DecisionCard] with typed data
        """
        # Security: Validate limit to prevent SQL injection
        limit = self._validate_limit(limit, max_limit=100)

        # AGE doesn't support ANY function, use array contains check
        cypher = f"""
            SELECT * FROM cypher('conport_knowledge', $$
                MATCH (d:Decision)
                WHERE d.tags @> ['"{tag}"']
                RETURN d.id, d.summary, d.timestamp
                ORDER BY d.timestamp DESC
                LIMIT {limit}
            $$) as (id agtype, summary agtype, timestamp agtype);
        """

        results = self._execute_cypher(cypher, workspace_path=workspace_path)

        decisions = []
        for row in results:
            if self.use_direct:
                decisions.append(DecisionCard(
                    id=int(row['id']),
                    summary=str(row['summary']),
                    timestamp=str(row['timestamp'])
                ))
            else:
                parts = row.get('parts', [])
                if len(parts) >= 3:
                    decisions.append(DecisionCard(
                        id=int(parts[0]),
                        summary=parts[1].strip('"'),
                        timestamp=parts[2]
                    ))

        return decisions


if __name__ == "__main__":
    # Test Tier 1 queries with AGEClient
    logger.info("=" * 60)
    logger.info("Tier 1: Overview Queries (ADHD Top-3 Pattern)")
    logger.info("Using: AGEClient with connection pooling" if USE_DIRECT_CONNECTION else "Using: Docker exec fallback")
    logger.info("=" * 60)

    queries = OverviewQueries()

    logger.info("\n[1] Recent Decisions (Top 3):")
    recent = queries.get_recent_decisions(3)
    for i, d in enumerate(recent, 1):
        logger.info(f"  {i}. #{d.id}: {d.summary[:60]}...")
        logger.info(f"     Type: {type(d).__name__}")

    logger.info("\n[2] Root Decisions (Foundational):")
    roots = queries.get_root_decisions(3)
    for i, d in enumerate(roots, 1):
        logger.info(f"  {i}. #{d.id}: {d.summary[:60]}...")
        logger.info(f"     Type: {type(d).__name__}")

    logger.info("\n[3] Decision Summary (with context count):")
    summary = queries.get_decision_summary(85)
    logger.info(f"  ID: {summary.id}")
    logger.info(f"  Summary: {summary.summary[:60]}...")
    logger.info(f"  Related decisions: {summary.related_count}")
    logger.info(f"  Cognitive load: {summary.get_cognitive_load()}")
    logger.info(f"  Type: {type(summary).__name__}")

    logger.info("\n[4] Search by tag:")
    tag_results = queries.search_by_tag("adhd-optimization", 3)
    logger.info(f"  Found {len(tag_results)} decisions with tag 'adhd-optimization'")
    for i, d in enumerate(tag_results, 1):
        logger.info(f"  {i}. #{d.id}: {d.summary[:60]}...")

    logger.info(f"\n✅ All queries returning typed models ({type(recent[0]).__name__ if recent else 'N/A'})")
