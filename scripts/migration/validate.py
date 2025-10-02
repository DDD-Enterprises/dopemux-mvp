#!/usr/bin/env python3
"""
ConPort Migration Validator
Part of CONPORT-KG-2025 Two-Phase Migration (Decision #112)

4-point validation system:
1. Decision count (old = new)
2. Relationship count (old = new)
3. No orphaned edges
4. UUID mapping complete
"""

import asyncio
import asyncpg
import sys
from typing import List, Tuple


class MigrationValidator:
    """Validates ConPort schema upgrade migration"""

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.conn = None

    async def connect(self):
        """Establish database connection"""
        self.conn = await asyncpg.connect(self.db_url)

    async def disconnect(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()

    async def validate_decision_count(self) -> Tuple[bool, str]:
        """Validate all decisions migrated"""

        old_count = await self.conn.fetchval("SELECT COUNT(*) FROM decisions")
        new_count = await self.conn.fetchval("SELECT COUNT(*) FROM decisions_v2")

        passed = (old_count == new_count)
        details = f"{old_count} → {new_count}"

        return passed, details

    async def validate_relationship_count(self) -> Tuple[bool, str]:
        """Validate all relationships migrated"""

        old_count = await self.conn.fetchval("""
            SELECT COUNT(*) FROM entity_relationships
            WHERE source_type = 'decision' AND target_type = 'decision'
        """)

        new_count = await self.conn.fetchval("""
            SELECT COUNT(*) FROM entity_relationships_v2
        """)

        passed = (old_count == new_count)
        details = f"{old_count} → {new_count}"

        return passed, details

    async def validate_no_orphans(self) -> Tuple[bool, str]:
        """Validate no orphaned relationships"""

        orphan_count = await self.conn.fetchval("""
            SELECT COUNT(*)
            FROM entity_relationships_v2 r
            WHERE NOT EXISTS (
                SELECT 1 FROM decisions_v2 WHERE id = r.source_id
            )
            OR NOT EXISTS (
                SELECT 1 FROM decisions_v2 WHERE id = r.target_id
            )
        """)

        passed = (orphan_count == 0)
        details = f"{orphan_count} orphaned edges found"

        return passed, details

    async def validate_uuid_mapping(self) -> Tuple[bool, str]:
        """Validate all decisions have UUID mapping"""

        unmapped_count = await self.conn.fetchval("""
            SELECT COUNT(*) FROM decisions_v2 WHERE old_uuid IS NULL
        """)

        total_count = await self.conn.fetchval("SELECT COUNT(*) FROM decisions_v2")

        passed = (unmapped_count == 0)
        details = f"{unmapped_count}/{total_count} unmapped"

        return passed, details

    async def validate_all(self) -> Tuple[bool, List[Dict]]:
        """Run all validation checks"""

        await self.connect()

        try:
            checks = [
                ("Decision count", await self.validate_decision_count()),
                ("Relationship count", await self.validate_relationship_count()),
                ("No orphaned edges", await self.validate_no_orphans()),
                ("UUID mapping complete", await self.validate_uuid_mapping())
            ]

            all_passed = all(check[1][0] for check in checks)

            return all_passed, [
                {
                    'name': check[0],
                    'passed': check[1][0],
                    'details': check[1][1]
                }
                for check in checks
            ]

        finally:
            await self.disconnect()


async def main():
    """Main validation procedure"""

    # Configuration
    DB_URL = "postgresql://dopemux:dopemux_dev_password@localhost:5432/dopemux_memory"

    print("=" * 60)
    print("ConPort Migration Validation")
    print("=" * 60)
    print()

    validator = MigrationValidator(DB_URL)

    try:
        all_passed, checks = await validator.validate_all()

        print("Validation Results:")
        print("-" * 60)

        for check in checks:
            status = "✓ PASS" if check['passed'] else "✗ FAIL"
            print(f"{status} | {check['name']:<25} | {check['details']}")

        print("-" * 60)

        if all_passed:
            print("\n✓ SUCCESS: All validation checks passed")
            print("\nNext steps:")
            print("  1. Review migrated data")
            print("  2. Run switchover.py when ready")
            return 0
        else:
            print("\n✗ FAILURE: Some validation checks failed")
            print("\nRecommended actions:")
            print("  1. Review error details above")
            print("  2. Check transformation logic")
            print("  3. Re-run reingest.py after fixes")
            return 1

    except Exception as e:
        print(f"\n✗ ERROR: Validation failed")
        print(f"  {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
