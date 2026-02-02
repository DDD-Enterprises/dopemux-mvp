#!/usr/bin/env python3
"""
ConPort Schema Upgrade + AGE Migration Master Script
Part of CONPORT-KG-2025 Two-Phase Migration (Decision #112)

Orchestrates complete two-phase migration:
Phase 1: ConPort schema upgrade (UUID→INTEGER, 4→8 relationship types)
Phase 2: Simple AGE migration (clean 1:1 copy)

Usage:
    python migrate.py --dry-run          # Test with 10 decisions
    python migrate.py --phase1           # ConPort upgrade only
    python migrate.py --phase2           # AGE migration only
    python migrate.py --full             # Complete migration
"""

import asyncio

import logging

logger = logging.getLogger(__name__)

import argparse
import sys
from pathlib import Path
from datetime import datetime


async def run_phase1(dry_run: bool = False):
    """
    Phase 1: ConPort Schema Upgrade

    Steps:
    1. Export data
    2. Create v2 tables
    3. Transform and re-ingest
    4. Validate
    5. Switchover
    """

    logger.info("\n" + "=" * 60)
    logger.info("PHASE 1: ConPort Schema Upgrade")
    logger.info("=" * 60)

    # Import modules
    from export_conport import ConPortExporter
    from reingest import ConPortReingester
    from validate import MigrationValidator
    from switchover import SchemaSwitchover

    DB_URL = "postgresql://dopemux:dopemux_dev_password@localhost:5432/dopemux_memory"
    WORKSPACE_ID = "/Users/hue/code/dopemux-mvp"

    try:
        # Step 1: Export
        logger.info("\nStep 1/5: Exporting data...")
        exporter = ConPortExporter(DB_URL)
        export_file = Path("conport_backup_dopemux-mvp.json")
        await exporter.export_all(WORKSPACE_ID, export_file)

        # Step 2: Create v2 tables
        logger.info("\nStep 2/5: Creating upgraded schema...")
        logger.info("  Run: psql < scripts/migration/001_create_decisions_v2.sql")
        logger.info("  Run: psql < scripts/migration/002_create_relationships_v2.sql")
        input("  Press Enter when complete...")

        # Step 3: Re-ingest
        logger.info("\nStep 3/5: Re-ingesting with transformation...")
        reingester = ConPortReingester(DB_URL)
        await reingester.reingest_all(export_file)

        # Step 4: Validate
        logger.info("\nStep 4/5: Validating migration...")
        validator = MigrationValidator(DB_URL)
        all_passed, checks = await validator.validate_all()

        if not all_passed:
            logger.error("\n✗ Validation failed - aborting")
            return False

        if dry_run:
            logger.info("\n✓ DRY-RUN COMPLETE")
            logger.info("Data validated successfully - ready for production")
            return True

        # Step 5: Switchover
        logger.info("\nStep 5/5: Executing switchover...")
        logger.info("\n⚠️  STOP ConPort MCP server before continuing!")
        input("  Press Enter when MCP server stopped...")

        switcher = SchemaSwitchover(DB_URL)
        success = await switcher.execute_switchover()

        if success:
            logger.info("\n✓ PHASE 1 COMPLETE")
            return True
        else:
            logger.error("\n✗ PHASE 1 FAILED")
            return False

    except Exception as e:
        logger.error(f"\n✗ Phase 1 error: {e}")
        return False


async def run_phase2():
    """
    Phase 2: AGE Migration

    Steps:
    1. Load nodes
    2. Load edges
    3. Create indexes
    4. Compute hop_distance
    5. Benchmark performance
    """

    logger.info("\n" + "=" * 60)
    logger.info("PHASE 2: AGE Migration")
    logger.info("=" * 60)

    from load_age_nodes import AGENodeLoader
    from load_age_edges import AGEEdgeLoader
    from compute_hop_distance import HopDistanceComputer
    from benchmark_age import AGEBenchmarker

    CONPORT_URL = "postgresql://dopemux:dopemux_dev_password@localhost:5432/dopemux_memory"
    AGE_URL = "postgresql://dopemux_age:dopemux_age_password@localhost:5455/dopemux_knowledge_graph"
    WORKSPACE_ID = "/Users/hue/code/dopemux-mvp"

    try:
        # Step 1: Load nodes
        logger.info("\nStep 1/5: Loading nodes to AGE...")
        node_loader = AGENodeLoader(CONPORT_URL, AGE_URL)
        success = await node_loader.load_all_nodes(WORKSPACE_ID)

        if not success:
            logger.error("\n✗ Node loading failed - aborting")
            return False

        # Step 2: Load edges
        logger.info("\nStep 2/5: Loading edges to AGE...")
        edge_loader = AGEEdgeLoader(CONPORT_URL, AGE_URL)
        success = await edge_loader.load_all_edges()

        if not success:
            logger.error("\n✗ Edge loading failed - aborting")
            return False

        # Step 3: Create indexes
        logger.info("\nStep 3/5: Creating AGE indexes...")
        logger.info("  Run: psql < scripts/migration/003_create_age_indexes.sql")
        input("  Press Enter when complete...")

        # Step 4: Compute hop_distance
        logger.info("\nStep 4/5: Computing hop distances...")
        computer = HopDistanceComputer(AGE_URL)
        computer.compute_hop_distances()

        # Step 5: Benchmark
        logger.info("\nStep 5/5: Performance benchmarking...")
        benchmarker = AGEBenchmarker(AGE_URL)
        all_pass = benchmarker.run_benchmarks(WORKSPACE_ID)

        if all_pass:
            logger.info("\n✓ PHASE 2 COMPLETE")
            return True
        else:
            logger.warning("\n⚠️  PHASE 2 COMPLETE (with performance warnings)")
            return True  # Not critical failure

    except Exception as e:
        logger.error(f"\n✗ Phase 2 error: {e}")
        return False


async def main():
    """Main migration orchestrator"""

    parser = argparse.ArgumentParser(description='CONPORT-KG-2025 Migration Tool')
    parser.add_argument('--dry-run', action='store_true', help='Test migration with validation only')
    parser.add_argument('--phase1', action='store_true', help='Run Phase 1 only (ConPort upgrade)')
    parser.add_argument('--phase2', action='store_true', help='Run Phase 2 only (AGE migration)')
    parser.add_argument('--full', action='store_true', help='Run complete migration (both phases)')

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("CONPORT-KG-2025: Two-Phase Migration")
    logger.info("=" * 60)
    logger.info(f"Started: {datetime.now().isoformat()}")
    logger.info()

    try:
        if args.dry_run:
            logger.info("Mode: DRY-RUN (validation only)")
            success = await run_phase1(dry_run=True)
            return 0 if success else 1

        elif args.phase1:
            logger.info("Mode: Phase 1 only (ConPort upgrade)")
            success = await run_phase1(dry_run=False)
            return 0 if success else 1

        elif args.phase2:
            logger.info("Mode: Phase 2 only (AGE migration)")
            success = await run_phase2()
            return 0 if success else 1

        elif args.full:
            logger.info("Mode: FULL migration (both phases)")

            # Phase 1
            success = await run_phase1(dry_run=False)
            if not success:
                logger.error("\n✗ Phase 1 failed - aborting")
                return 1

            # Phase 2
            success = await run_phase2()
            if not success:
                logger.error("\n✗ Phase 2 failed")
                return 1

            logger.info("\n" + "=" * 60)
            logger.info("✓ COMPLETE MIGRATION SUCCESSFUL")
            logger.info("=" * 60)
            logger.info("\nBoth ConPort and AGE upgraded successfully!")
            return 0

        else:
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Migration interrupted by user")
        logger.info("Run rollback.py if needed")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
