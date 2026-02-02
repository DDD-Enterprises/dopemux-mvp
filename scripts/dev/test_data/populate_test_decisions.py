#!/usr/bin/env python3
"""
Populate ConPort with realistic test decisions for Quick Win validation.

Creates 20 test decisions with varied:
- Ages (0-120 days old)
- Types (architectural, technical, process, adhd-pattern, tooling)
- Tags (realistic development patterns)
- Confidence levels (when field exists)
"""

import asyncio
import asyncpg
from datetime import datetime, timedelta
import random

# Database connection
DATABASE_URL = "postgresql://dopemux_age:dopemux_age_dev_password@localhost:5455/dopemux_knowledge_graph"
WORKSPACE_ID = "dopemux-mvp"

# Test decision templates
DECISIONS = [
    # Recent decisions (0-7 days)
    {
        "summary": "Migrate from SQLite to PostgreSQL AGE for ConPort",
        "rationale": "Need graph database for decision genealogy and relationship tracking",
        "decision_type": "architectural",
        "tags": ["database", "architecture", "migration"],
        "days_ago": 2
    },
    {
        "summary": "Use Rich library for CLI terminal formatting",
        "rationale": "Provides ADHD-friendly visual output with minimal code",
        "decision_type": "technical",
        "tags": ["cli", "adhd-optimization", "dependencies"],
        "days_ago": 5
    },
    {
        "summary": "Implement energy logging before full ADHD dashboard",
        "rationale": "Quick win provides immediate value and validates design approach",
        "decision_type": "process",
        "tags": ["adhd-optimization", "incremental-delivery", "quick-wins"],
        "days_ago": 1
    },

    # Medium age (8-30 days)
    {
        "summary": "Add asyncpg for PostgreSQL instead of psycopg2",
        "rationale": "Async operations prevent CLI blocking on database queries",
        "decision_type": "technical",
        "tags": ["database", "async", "performance"],
        "days_ago": 12
    },
    {
        "summary": "Store energy logs in custom_data table initially",
        "rationale": "Avoids schema migration for Quick Win, moves to adhd_metrics in Phase 1",
        "decision_type": "technical",
        "tags": ["adhd-optimization", "pragmatic", "phase-plan"],
        "days_ago": 15
    },
    {
        "summary": "Use basename for workspace_id instead of full path",
        "rationale": "Matches ConPort MCP format, simpler for users to understand",
        "decision_type": "technical",
        "tags": ["consistency", "ux", "worktrees"],
        "days_ago": 20
    },
    {
        "summary": "Progressive disclosure for decision statistics",
        "rationale": "Show essentials first (summary, count), details on demand - reduces ADHD cognitive load",
        "decision_type": "adhd-pattern",
        "tags": ["adhd-optimization", "ux", "progressive-disclosure"],
        "days_ago": 25
    },

    # Older decisions (31-60 days) - Should trigger review
    {
        "summary": "Implement ConPort enhancement roadmap in 7 sprints",
        "rationale": "Breaks down massive scope into manageable ADHD-friendly chunks",
        "decision_type": "process",
        "tags": ["planning", "adhd-optimization", "project-management"],
        "days_ago": 35
    },
    {
        "summary": "Use Click framework for CLI instead of argparse",
        "rationale": "More ergonomic API, better help generation, industry standard",
        "decision_type": "tooling",
        "tags": ["cli", "developer-experience", "dependencies"],
        "days_ago": 42
    },
    {
        "summary": "Separate ConPort enhancements into phases instead of Big Bang",
        "rationale": "Allows incremental delivery, reduces risk, provides early feedback opportunities",
        "decision_type": "process",
        "tags": ["agile", "risk-management", "incremental-delivery"],
        "days_ago": 50
    },
    {
        "summary": "Tag all decisions for pattern detection in Phase 3",
        "rationale": "Manual tags bootstrap ML pattern learning, human-validated ground truth",
        "decision_type": "process",
        "tags": ["pattern-learning", "data-quality", "ml-foundation"],
        "days_ago": 55
    },

    # Old decisions (61-90 days) - Should show as overdue
    {
        "summary": "Use Docker Compose for MCP server orchestration",
        "rationale": "Simplifies deployment, isolates services, enables easy scaling",
        "decision_type": "architectural",
        "tags": ["infrastructure", "docker", "deployment"],
        "days_ago": 65
    },
    {
        "summary": "Implement 25-minute focus sessions with break reminders",
        "rationale": "Pomodoro technique proven effective for ADHD, prevents burnout",
        "decision_type": "adhd-pattern",
        "tags": ["adhd-optimization", "focus", "session-management"],
        "days_ago": 72
    },
    {
        "summary": "Use Redis for ConPort caching layer",
        "rationale": "Sub-millisecond reads for frequently accessed context data",
        "decision_type": "technical",
        "tags": ["caching", "performance", "redis"],
        "days_ago": 80
    },
    {
        "summary": "Add confidence tracking to all decisions",
        "rationale": "Low confidence decisions need more review, higher risk of change",
        "decision_type": "process",
        "tags": ["decision-quality", "risk-management", "metadata"],
        "days_ago": 88
    },

    # Very old decisions (>90 days) - Should be marked overdue
    {
        "summary": "Implement two-plane architecture (PM + Cognitive)",
        "rationale": "Separates concerns, enables specialized tools per plane, reduces cognitive load",
        "decision_type": "architectural",
        "tags": ["architecture", "system-design", "foundational"],
        "days_ago": 95
    },
    {
        "summary": "Use Voyage AI for semantic embeddings instead of OpenAI",
        "rationale": "Better code understanding, lower cost, specialized for technical content",
        "decision_type": "technical",
        "tags": ["embeddings", "semantic-search", "cost-optimization"],
        "days_ago": 105
    },
    {
        "summary": "Implement worktree-based parallel development",
        "rationale": "ADHD benefit: switch context without losing state, physical directory = mental boundary",
        "decision_type": "adhd-pattern",
        "tags": ["worktrees", "adhd-optimization", "context-preservation"],
        "days_ago": 110
    },
    {
        "summary": "Add pattern learning to ConPort for decision recommendations",
        "rationale": "Decisions should inform future decisions, reduce repeated analysis",
        "decision_type": "architectural",
        "tags": ["pattern-learning", "ml-foundation", "automation"],
        "days_ago": 115
    },
    {
        "summary": "Use git worktree isolation for MCP server configurations",
        "rationale": "Each worktree can have independent MCP settings, prevents conflicts",
        "decision_type": "technical",
        "tags": ["worktrees", "mcp-integration", "isolation"],
        "days_ago": 118
    },
    {
        "summary": "Build ADHD dashboard before advanced ML features",
        "rationale": "Real-time energy/focus feedback has immediate utility, ML can enhance later",
        "decision_type": "process",
        "tags": ["prioritization", "adhd-optimization", "pragmatic"],
        "days_ago": 120
    },
]


async def populate_decisions():
    """Insert test decisions into ConPort database."""

    conn = await asyncpg.connect(DATABASE_URL)

    try:
        print(f"📝 Populating {len(DECISIONS)} test decisions...")
        print(f"   Workspace: {WORKSPACE_ID}\n")

        inserted = 0

        for i, decision in enumerate(DECISIONS, 1):
            # Calculate timestamp
            created_at = datetime.now() - timedelta(days=decision["days_ago"])

            # Insert decision
            await conn.execute("""
                INSERT INTO decisions (
                    workspace_id,
                    summary,
                    rationale,
                    decision_type,
                    tags,
                    created_at,
                    updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $6)
            """,
                WORKSPACE_ID,
                decision["summary"],
                decision["rationale"],
                decision["decision_type"],
                decision["tags"],
                created_at
            )

            inserted += 1

            # Show progress
            age_category = (
                "Recent (0-7d)" if decision["days_ago"] <= 7
                else "Medium (8-30d)" if decision["days_ago"] <= 30
                else "Review (31-60d)" if decision["days_ago"] <= 60
                else "Overdue (>60d)"
            )

            print(f"  [{i:2d}/20] {age_category:15} | {decision['decision_type']:15} | {decision['summary'][:50]}...")

        print(f"\n✅ Inserted {inserted} test decisions")

        # Show distribution
        print("\n📊 Age Distribution:")
        recent = sum(1 for d in DECISIONS if d["days_ago"] <= 7)
        medium = sum(1 for d in DECISIONS if 8 <= d["days_ago"] <= 30)
        review = sum(1 for d in DECISIONS if 31 <= d["days_ago"] <= 60)
        overdue = sum(1 for d in DECISIONS if d["days_ago"] > 60)

        print(f"  Recent (0-7d):   {recent:2d} decisions")
        print(f"  Medium (8-30d):  {medium:2d} decisions")
        print(f"  Review (31-60d): {review:2d} decisions")
        print(f"  Overdue (>60d):  {overdue:2d} decisions")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(populate_decisions())
