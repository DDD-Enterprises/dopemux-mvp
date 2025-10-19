"""
Task-Orchestrator Adapters

Data contract adapters for Architecture 3.0 integration.
"""

from .conport_adapter import ConPortEventAdapter, orchestration_task_to_conport_progress, conport_progress_to_orchestration_task
from .conport_insight_publisher import ConPortInsightPublisher, AIDecisionEvent, create_architecture_decision, create_code_review_decision
from .schema_mapping import (
    encode_energy_tag, encode_complexity_tag, encode_priority_tag, encode_all_adhd_tags,
    decode_energy_tag, decode_complexity_tag, decode_priority_tag, decode_all_adhd_tags,
    build_task_description, parse_task_description,
    map_task_status_to_conport, map_conport_status_to_task,
    validate_adhd_metadata, validate_conport_progress_data,
    build_adhd_query_tags, filter_tasks_by_adhd_criteria
)

__all__ = [
    "ConPortEventAdapter",
    "orchestration_task_to_conport_progress",
    "conport_progress_to_orchestration_task",
    "ConPortInsightPublisher",
    "AIDecisionEvent",
    "create_architecture_decision",
    "create_code_review_decision",
    "encode_energy_tag",
    "encode_complexity_tag",
    "encode_priority_tag",
    "encode_all_adhd_tags",
    "decode_all_adhd_tags",
    "build_task_description",
    "parse_task_description",
    "validate_adhd_metadata",
    "validate_conport_progress_data",
    "build_adhd_query_tags",
    "filter_tasks_by_adhd_criteria"
]
