"""
Dopemux: ADHD-Optimized Development Platform

Event-driven architecture for multi-instance development coordination.
"""

__version__ = "0.1.0"
__author__ = "Dopemux Team"

from .event_bus import (
    DopemuxEvent, EventBus, RedisStreamsAdapter, InMemoryAdapter,
    Priority, CognitiveLoad, ADHDMetadata
)
from .attention_mediator import AttentionMediator, FocusState, InterruptionTolerance
from .instance_registry import InstanceRegistry, InstanceStatus
from .producers import MCPEventProducer, ConPortEventProducer

__all__ = [
    # Core event system
    "DopemuxEvent",
    "EventBus",
    "RedisStreamsAdapter",
    "InMemoryAdapter",
    "Priority",
    "CognitiveLoad",
    "ADHDMetadata",

    # ADHD optimization
    "AttentionMediator",
    "FocusState",
    "InterruptionTolerance",

    # Multi-instance coordination
    "InstanceRegistry",
    "InstanceStatus",

    # Event producers
    "MCPEventProducer",
    "ConPortEventProducer"
]