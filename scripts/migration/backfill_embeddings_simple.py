#!/usr/bin/env python3
"""
Simple embedding backfill for DDG decisions.
No complex imports - just Qdrant + Voyage APIs directly.
"""

import asyncio
import asyncpg
import httpx
import json
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import sys
import os


async def main():
    """Backfill embeddings to Qdrant"""

    # Configuration
    DDG_DB = "postgresql://dopemux_age:dopemux_age_dev_password@localhost:5455/dopemux_knowledge_graph"
    QDRANT_URL = "localhost"
    QDRANT_PORT = 6333
    VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")

    if not VOYAGE_API_KEY:
        print("❌ VOYAGE_API_KEY not set!")
        sys.exit(1)

    print("🚀 DDG Embedding Backfill (Simplified)")
    print("=" * 60)
    print(f"DDG DB:  {DDG_DB}")
    print(f"Qdrant:  {QDRANT_URL}:{QDRANT_PORT}")
    print()

    # Connect to PostgreSQL
    print("🔌 Connecting to PostgreSQL...")
    conn = await asyncpg.connect(DDG_DB)
    print("   ✅ Connected")

    # Initialize Qdrant
    print("🔌 Initializing Qdrant...")
    qdrant = QdrantClient(url=QDRANT_URL, port=QDRANT_PORT)

    # Create collection if not exists
    try:
        qdrant.create_collection(
            collection_name="ddg_global_decisions",
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
        )
        print("   ✅ Created collection: ddg_global_decisions")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("   ✅ Collection exists: ddg_global_decisions")
        else:
            print(f"   ⚠️  Collection error: {e}")

    # Fetch decisions
    print("\n📋 Fetching decisions...")
    rows = await conn.fetch("""
        SELECT id, workspace_id, instance_id, summary, tags, source, created_at
        FROM ddg_decisions
        ORDER BY created_at ASC
    """)

    decisions = [dict(row) for row in rows]
    print(f"   ✅ Found {len(decisions)} decisions")

    # HTTP client for Voyage API
    http_client = httpx.AsyncClient(timeout=60.0)

    # Backfill
    print(f"\n🎨 Creating embeddings...")
    print(f"   Model: voyage-3-large (1024 dimensions)")

    created = 0
    failed = 0
    skipped = 0

    for i, decision in enumerate(decisions, 1):
        try:
            decision_id = decision['id']
            summary = decision['summary'] or ""

            if not summary.strip():
                skipped += 1
                continue

            # Check if exists
            try:
                search_result = qdrant.scroll(
                    collection_name="ddg_global_decisions",
                    scroll_filter={"must": [{"key": "decision_id", "match": {"value": decision_id}}]},
                    limit=1
                )
                if search_result[0]:  # Has points
                    skipped += 1
                    continue
            except:
                pass  # Collection might not exist yet

            # Generate Voyage embedding
            response = await http_client.post(
                "https://api.voyageai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {VOYAGE_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "input": [summary],
                    "model": "voyage-3-large"
                }
            )

            if response.status_code != 200:
                print(f"   ⚠️  Voyage API error {response.status_code}: {decision_id}")
                failed += 1
                continue

            result = response.json()
            vector = result['data'][0]['embedding']

            # Store in Qdrant (use UUID directly as ID)
            point = PointStruct(
                id=decision_id,  # Just UUID, no prefix
                vector=vector,
                payload={
                    "decision_id": decision_id,
                    "workspace_id": decision['workspace_id'],
                    "instance_id": decision.get('instance_id', ''),
                    "summary": summary[:500],
                    "tags": decision.get('tags', []) or [],
                    "source": decision.get('source', ''),
                    "created_at": decision['created_at'].isoformat() if decision.get('created_at') else None
                }
            )

            qdrant.upsert(
                collection_name="ddg_global_decisions",
                points=[point]
            )

            created += 1

            # Progress
            if i % 50 == 0:
                print(f"   Progress: {i}/{len(decisions)} ({created} created, {skipped} skipped, {failed} failed)")
                await asyncio.sleep(0.2)  # Rate limit

        except Exception as e:
            print(f"   ⚠️  Failed {decision_id}: {e}")
            failed += 1

    # Final stats
    print("\n" + "=" * 60)
    print("✅ EMBEDDING BACKFILL COMPLETE")
    print("=" * 60)
    print(f"Total decisions:    {len(decisions)}")
    print(f"Embeddings created: {created}")
    print(f"Skipped (existing): {skipped}")
    print(f"Failed:             {failed}")

    # Cleanup
    await conn.close()
    await http_client.aclose()

    # Test search
    if created > 0:
        print("\n🔍 Testing Qdrant search...")
        test_results = qdrant.search(
            collection_name="ddg_global_decisions",
            query_vector=[0.1] * 1024,  # Dummy query
            limit=3
        )
        print(f"   ✅ Search works! Found {len(test_results)} results")

    print(f"\n🎉 Success! {created} embeddings created in Qdrant")


if __name__ == "__main__":
    asyncio.run(main())
