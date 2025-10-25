#!/usr/bin/env python3
"""
Backfill embeddings for existing DDG decisions using Qdrant.

Creates Voyage-3-large embeddings for all decisions in ddg_decisions table
and stores them in Qdrant for fast semantic search.

Based on proven dope-context pattern: Qdrant + Voyage + reranking
"""

import asyncio
import asyncpg
import sys
import os
from pathlib import Path

# Add dope-context to path to reuse VectorStore + Voyage
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "dope-context" / "src"))

from core.vector_store import VectorStore
from embeddings.voyage_embedder import VoyageEmbedder


class EmbeddingBackfill:
    """Backfill Voyage embeddings for DDG decisions to Qdrant"""

    def __init__(self, ddg_db_url: str, qdrant_url: str, qdrant_port: int, voyage_api_key: str):
        self.ddg_db_url = ddg_db_url
        self.qdrant_url = qdrant_url
        self.qdrant_port = qdrant_port
        self.voyage_api_key = voyage_api_key
        self.conn = None
        self.vector_store = None
        self.voyage_embedder = None

    async def connect(self):
        """Connect to DDG PostgreSQL and Qdrant"""
        print("🔌 Connecting to DDG PostgreSQL...")
        self.conn = await asyncpg.connect(self.ddg_db_url)
        print("   ✅ PostgreSQL connected")

        print("🔌 Initializing Qdrant vector store...")
        self.vector_store = VectorStore(
            collection_name="ddg_global_decisions",
            url=self.qdrant_url,
            port=self.qdrant_port,
            vector_size=1024  # voyage-3-large dimension
        )
        await self.vector_store.initialize()
        print("   ✅ Qdrant initialized (collection: ddg_global_decisions)")

        print("🔌 Initializing Voyage embedder...")
        self.voyage_embedder = VoyageEmbedder(
            api_key=self.voyage_api_key,
            default_model="voyage-3-large"
        )
        print("   ✅ Voyage embedder ready (model: voyage-3-large)")

    async def close(self):
        """Close connections"""
        if self.conn:
            await self.conn.close()
        if self.vector_store:
            await self.vector_store.close()

    async def fetch_all_decisions(self) -> List[Dict[str, Any]]:
        """Fetch all decisions from DDG database"""
        print("\n📋 Fetching all DDG decisions...")

        rows = await self.conn.fetch("""
            SELECT id, workspace_id, instance_id, summary, tags, source, created_at
            FROM ddg_decisions
            ORDER BY created_at ASC
        """)

        decisions = [dict(row) for row in rows]
        print(f"   ✅ Found {len(decisions)} decisions")
        return decisions

    async def check_existing_in_qdrant(self, decision_id: str) -> bool:
        """Check if decision already has embedding in Qdrant"""
        try:
            result = await self.vector_store.search(
                query_vector=[0.0] * 1024,  # Dummy vector
                filter_conditions={"decision_id": decision_id},
                limit=1
            )
            return len(result) > 0
        except:
            return False

    async def upsert_embedding(self, decision: Dict[str, Any]) -> bool:
        """
        Create and store embedding for a decision in Qdrant.

        Args:
            decision: Decision dict with id, summary, workspace_id, tags

        Returns:
            True if successful
        """
        try:
            decision_id = decision['id']
            summary = decision['summary'] or ""

            # Skip if empty summary
            if not summary.strip():
                return True  # Silent skip

            # Check if already exists
            if await self.check_existing_in_qdrant(decision_id):
                return True  # Already embedded

            # Create embedding text
            text = summary  # Just summary for now, can add rationale later

            # Generate Voyage embedding
            embeddings = await self.voyage_embedder.embed([text], model="voyage-3-large")
            vector = embeddings[0]

            # Store in Qdrant
            metadata = {
                "decision_id": decision_id,
                "workspace_id": decision['workspace_id'],
                "instance_id": decision.get('instance_id', ''),
                "summary": summary[:500],  # Truncate for metadata
                "tags": decision.get('tags', []),
                "source": decision.get('source', ''),
                "created_at": decision['created_at'].isoformat() if decision.get('created_at') else None
            }

            await self.vector_store.upsert(
                doc_id=f"decision_{decision_id}",
                vector=vector,
                metadata=metadata
            )

            return True

        except Exception as e:
            print(f"   ⚠️  Failed for {decision.get('id', 'unknown')}: {e}")
            return False

    async def backfill_all_embeddings(self, batch_size: int = 50) -> Dict[str, int]:
        """
        Backfill embeddings for all decisions to Qdrant.

        Args:
            batch_size: Batch size for progress reporting

        Returns:
            Statistics
        """
        decisions = await self.fetch_all_decisions()

        if not decisions:
            print("\n⚠️  No decisions found!")
            return {"total": 0, "created": 0, "failed": 0, "skipped": 0}

        print(f"\n🎨 Creating Qdrant embeddings for {len(decisions)} decisions...")
        print(f"   Model: voyage-3-large (1024 dimensions)")
        print(f"   Target: Qdrant collection 'ddg_global_decisions'")
        print(f"   Batch size: {batch_size}")

        created = 0
        failed = 0
        skipped = 0

        for i, decision in enumerate(decisions, 1):
            # Check if exists first
            exists = await self.check_existing_in_qdrant(decision['id'])
            if exists:
                skipped += 1
                continue

            success = await self.upsert_embedding(decision)

            if success:
                created += 1
            else:
                failed += 1

            # Progress
            if i % batch_size == 0:
                print(f"   Progress: {i}/{len(decisions)} ({created} created, {skipped} skipped, {failed} failed)")
                await asyncio.sleep(0.2)  # Rate limiting

        stats = {
            "total": len(decisions),
            "created": created,
            "failed": failed,
            "skipped": skipped
        }

        print("\n" + "=" * 60)
        print("✅ QDRANT EMBEDDING BACKFILL COMPLETE")
        print("=" * 60)
        print(f"Total decisions:    {stats['total']}")
        print(f"Embeddings created: {stats['created']}")
        print(f"Skipped (existing): {stats['skipped']}")
        print(f"Failed:             {stats['failed']}")
        if stats['total'] > 0:
            print(f"Success rate:       {100 * stats['created'] / (stats['total'] - stats['skipped']):.1f}%")

        return stats


async def main(
    ddg_db_url: str,
    qdrant_url: str,
    qdrant_port: int,
    voyage_api_key: str,
    batch_size: int = 50
):
    """Main backfill workflow"""

    if not voyage_api_key:
        print("❌ VOYAGE_API_KEY not set!")
        print("   export VOYAGE_API_KEY=your_key")
        sys.exit(1)

    backfill = EmbeddingBackfill(ddg_db_url, qdrant_url, qdrant_port, voyage_api_key)

    try:
        await backfill.connect()
        stats = await backfill.backfill_all_embeddings(batch_size=batch_size)
        return stats
    finally:
        await backfill.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Backfill embeddings for DDG decisions")
    parser.add_argument(
        "--ddg-db",
        type=str,
        default="postgresql://dopemux_age:dopemux_age_dev_password@localhost:5455/dopemux_knowledge_graph",
        help="DDG PostgreSQL URL"
    )
    parser.add_argument(
        "--qdrant-url",
        type=str,
        default="localhost",
        help="Qdrant URL"
    )
    parser.add_argument(
        "--qdrant-port",
        type=int,
        default=6333,
        help="Qdrant port"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=os.getenv("VOYAGE_API_KEY"),
        help="Voyage API key (or set VOYAGE_API_KEY env var)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Batch size for progress reporting"
    )

    args = parser.parse_args()

    print("🚀 DDG Embedding Backfill to Qdrant")
    print("=" * 60)
    print(f"DDG DB:      {args.ddg_db}")
    print(f"Qdrant:      {args.qdrant_url}:{args.qdrant_port}")
    print(f"API Key:     {'✅ Set' if args.api_key else '❌ Missing'}")
    print(f"Batch size:  {args.batch_size}")
    print()

    try:
        stats = asyncio.run(main(
            ddg_db_url=args.ddg_db,
            qdrant_url=args.qdrant_url,
            qdrant_port=args.qdrant_port,
            voyage_api_key=args.api_key,
            batch_size=args.batch_size
        ))

        if stats['failed'] == 0:
            print("\n🎉 Embedding backfill 100% successful!")
            sys.exit(0)
        else:
            print(f"\n⚠️  Backfill completed with {stats['failed']} failures")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Backfill failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
