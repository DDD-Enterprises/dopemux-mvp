#!/usr/bin/env python3
"""
Integration module for Automatic Snapshots in Working Memory Assistant

This module provides the integration points to add automatic snapshots functionality
to the main WMA FastAPI application.
"""

import logging

logger = logging.getLogger(__name__)

# Add these imports to main.py
AUTOMATIC_SNAPSHOTS_IMPORTS = """

import logging

logger = logging.getLogger(__name__)

from automatic_snapshots import create_automatic_snapshots_service
from automatic_snapshots_api import router as automatic_router
from adhd_engine_client import ADHDEngineClient
"""

# Add this service initialization in the lifespan function
AUTOMATIC_SNAPSHOTS_LIFESPAN = """
    # Initialize Automatic Snapshots Service
    adhd_client = ADHDEngineClient()
    automatic_snapshots_service = create_automatic_snapshots_service(
        pool, redis_client, adhd_client
    )

    # Store service instance globally for API access
    from automatic_snapshots import _automatic_snapshots_service
    _automatic_snapshots_service = automatic_snapshots_service

    # Start automatic snapshots monitoring
    await automatic_snapshots_service.start_monitoring()
    logger.info("Automatic snapshots monitoring started")

    yield

    # Cleanup on shutdown
    await automatic_snapshots_service.stop_monitoring()
    logger.info("Automatic snapshots monitoring stopped")
"""

# Add this router inclusion after the existing routes
AUTOMATIC_SNAPSHOTS_ROUTER = """
# Include automatic snapshots API
app.include_router(automatic_router)
"""

logger.info("Automatic Snapshots Integration Ready!")
logger.info("=" * 50)
logger.info("To integrate automatic snapshots into main.py:")
logger.info("1. Add the imports at the top:")
logger.info(AUTOMATIC_SNAPSHOTS_IMPORTS)
logger.info()
logger.info("2. Modify the lifespan function to include:")
logger.info(AUTOMATIC_SNAPSHOTS_LIFESPAN)
logger.info()
logger.info("3. Add the router inclusion:")
logger.info(AUTOMATIC_SNAPSHOTS_ROUTER)
logger.info("=" * 50)
