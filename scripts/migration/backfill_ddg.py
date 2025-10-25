#!/usr/bin/env python3
"""
Backfill DDG with historical decisions from ConPort PostgreSQL.

Publishes decision_logged events to EventBus for each decision.
DDG ingestion task will consume events and create embeddings.
"""

import asyncio
import asyncpg
import httpx
from typing import List, Dict, Any
from datetime import datetime
import sys
from pathlib import Path


class DDGBackfill:
    """Backfill DDG with historical ConPort decisions"""

    def __init__(self, conport_db_url: str, integration_bridge_url: str):
        self.conport_db_url = conport_db_url
        self.integration_bridge_url = integration_bridge_url
        self.conn = None

    async def connect(self):
        """Connect to ConPort PostgreSQL"""
        print("🔌 Connecting to ConPort PostgreSQL...")
        self.conn = await asyncpg.connect(self.conport_db_url)
        print("   ✅ Connected")

    async def close(self):
        """Close connection"""
        if self.conn:
            await self.conn.close()

    async def fetch_all_decisions(self) -> List[Dict[str, Any]]:
        """Fetch all decisions from ConPort PostgreSQL"""
        print("\n📋 Fetching decisions from ConPort...")

        rows = await self.conn.fetch("""
            SELECT id, workspace_id, summary, rationale, alternatives, tags,
                   confidence_level, decision_type, created_at, updated_at
            FROM ag_catalog.decisions
            ORDER BY created_at ASC
        """)

        decisions = []
        for row in rows:
            decision = dict(row)
            decision['id'] = str(decision['id'])  # UUID to string
            decision['created_at'] = decision['created_at'].isoformat()
            decision['updated_at'] = decision['updated_at'].isoformat()
            decisions.append(decision)

        print(f"   ✅ Found {len(decisions)} decisions")
        return decisions

    async def publish_decision_event(
        self,
        decision: Dict[str, Any],
        client: httpx.AsyncClient
    ) -> bool:
        """
        Publish decision_logged event to Integration Bridge.

        The bridge will forward to EventBus, DDG will ingest.
        """
        try:
            event_data = {
                "type": "decision_logged",
                "source": "conport-backfill",
                "data": {
                    "decision_id": decision['id'],
                    "workspace_id": decision['workspace_id'],
                    "summary": decision['summary'],
                    "rationale": decision.get('rationale', ''),
                    "tags": decision.get('tags', []),
                    "timestamp": decision['created_at']
                },
                "workspace_id": decision['workspace_id']
            }

            response = await client.post(
                f"{self.integration_bridge_url}/events/publish",
                json=event_data,
                timeout=10.0
            )

            if response.status_code == 200:
                return True
            else:
                print(f"   ⚠️  Event publish failed (HTTP {response.status_code}): {decision['id']}")
                return False

        except Exception as e:
            print(f"   ⚠️  Event publish error: {e}")
            return False

    async def backfill_all_decisions(self, batch_size: int = 10) -> Dict[str, int]:
        """
        Backfill all decisions to DDG via EventBus.

        Args:
            batch_size: Number of events to publish per batch

        Returns:
            Statistics
        """
        decisions = await self.fetch_all_decisions()

        if not decisions:
            print("\n⚠️  No decisions to backfill")
            return {"total": 0, "published": 0, "failed": 0}

        print(f"\n📡 Publishing {len(decisions)} events to EventBus...")
        print(f"   Bridge URL: {self.integration_bridge_url}")
        print(f"   Batch size: {batch_size}")

        published = 0
        failed = 0

        async with httpx.AsyncClient() as client:
            for i, decision in enumerate(decisions, 1):
                success = await self.publish_decision_event(decision, client)

                if success:
                    published += 1
                else:
                    failed += 1

                # Progress indicator
                if i % batch_size == 0:
                    print(f"   Progress: {i}/{len(decisions)} ({published} published, {failed} failed)")
                    # Small delay to avoid overwhelming the system
                    await asyncio.sleep(0.1)

        stats = {
            "total": len(decisions),
            "published": published,
            "failed": failed
        }

        print("\n" + "=" * 60)
        print("✅ BACKFILL COMPLETE")
        print("=" * 60)
        print(f"Total decisions:  {stats['total']}")
        print(f"Published:        {stats['published']}")
        print(f"Failed:           {stats['failed']}")
        print(f"Success rate:     {100 * stats['published'] / stats['total']:.1f}%")

        return stats

    async def verify_ddg_ingestion(self, ddg_db_url: str) -> bool:
        """
        Verify DDG successfully ingested decisions.

        Args:
            ddg_db_url: DDG PostgreSQL connection URL

        Returns:
            True if ingestion successful
        """
        print("\n🔍 Verifying DDG ingestion...")

        try:
            ddg_conn = await asyncpg.connect(ddg_db_url)

            # Check decision count
            decision_count = await ddg_conn.fetchval(
                "SELECT COUNT(*) FROM ddg_decisions"
            )

            # Check embedding count
            embedding_count = await ddg_conn.fetchval(
                "SELECT COUNT(*) FROM ddg_embeddings"
            )

            await ddg_conn.close()

            print(f"   DDG Decisions:  {decision_count}")
            print(f"   DDG Embeddings: {embedding_count}")

            if decision_count > 0:
                print("   ✅ DDG ingestion working!")
                return True
            else:
                print("   ⚠️  DDG still empty (may need time to process)")
                return False

        except Exception as e:
            print(f"   ⚠️  Verification failed: {e}")
            return False


async def main(
    conport_db_url: str,
    integration_bridge_url: str,
    ddg_db_url: str,
    batch_size: int = 10,
    verify: bool = True
):
    """Main backfill workflow"""

    backfill = DDGBackfill(conport_db_url, integration_bridge_url)

    try:
        await backfill.connect()

        # Run backfill
        stats = await backfill.backfill_all_decisions(batch_size=batch_size)

        # Verify if requested
        if verify and stats['published'] > 0:
            print("\n⏳ Waiting 5 seconds for DDG to process events...")
            await asyncio.sleep(5)
            await backfill.verify_ddg_ingestion(ddg_db_url)

        return stats

    finally:
        await backfill.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Backfill DDG with ConPort decisions")
    parser.add_argument(
        "--conport-db",
        type=str,
        default="postgresql://dopemux_age:dopemux_age_dev_password@localhost:5455/dopemux_knowledge_graph",
        help="ConPort PostgreSQL URL (must be migrated first!)"
    )
    parser.add_argument(
        "--bridge-url",
        type=str,
        default="http://localhost:3016",
        help="Integration Bridge URL"
    )
    parser.add_argument(
        "--ddg-db",
        type=str,
        default="postgresql://dopemux_age:dopemux_age_dev_password@localhost:5455/dopemux_knowledge_graph",
        help="DDG PostgreSQL URL (for verification)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Batch size for event publishing"
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip DDG verification"
    )

    args = parser.parse_args()

    print("🚀 DDG Backfill Script")
    print("=" * 60)
    print(f"ConPort DB:  {args.conport_db}")
    print(f"Bridge:      {args.bridge_url}")
    print(f"Batch size:  {args.batch_size}")
    print()

    try:
        stats = asyncio.run(main(
            conport_db_url=args.conport_db,
            integration_bridge_url=args.bridge_url,
            ddg_db_url=args.ddg_db,
            batch_size=args.batch_size,
            verify=not args.no_verify
        ))

        if stats['failed'] == 0:
            print("\n🎉 Backfill 100% successful!")
            sys.exit(0)
        else:
            print(f"\n⚠️  Backfill completed with {stats['failed']} failures")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Backfill failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
