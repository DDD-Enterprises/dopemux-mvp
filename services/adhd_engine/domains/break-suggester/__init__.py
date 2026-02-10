"""
F-NEW-8: Proactive Break Suggester Service

Entry point for break suggestion engine.
"""

from engine import (
    BreakSuggestionEngine,
    BreakSuggestion,
    get_break_suggestion_engine
)

from event_consumer import (
    BreakSuggestionConsumer,
    run_break_suggester_service
)

__all__ = [
    'BreakSuggestionEngine',
    'BreakSuggestion',
    'get_break_suggestion_engine',
    'BreakSuggestionConsumer',
    'run_break_suggester_service',
    'start_break_suggester_service'
]


async def start_break_suggester_service(user_id: str = "default"):
    """
    Start break suggester as background service.

    Args:
        user_id: User identifier

    Returns:
        Task handle for background service

    Usage:
        import asyncio
        from services.break_suggester import start_break_suggester_service

        # Start in background
        task = asyncio.create_task(start_break_suggester_service("alice"))

        # Service runs indefinitely, monitoring events
        # Generates break suggestions when patterns detected
    """
    import asyncio

    consumer = BreakSuggestionConsumer(user_id=user_id)
    await consumer.initialize()

    # Start consuming in background
    task = asyncio.create_task(consumer.start_consuming())

    return task
