"""W05: join-type evaluation and the AggregateReturnEnvelope builder.

Public API re-exported here for convenience; see types.py, evaluate.py and
envelope.py for the implementation and docstrings.
"""
from __future__ import annotations

from .envelope import EnvelopeInvalid, build_envelope
from .evaluate import derive_macro_status, evaluate_all, evaluate_join, next_legal_action
from .types import ConditionError, JoinDecl, JoinResult, JoinType, ReturnRef, WorkstreamResult

__all__ = [
    "ConditionError",
    "EnvelopeInvalid",
    "JoinDecl",
    "JoinResult",
    "JoinType",
    "ReturnRef",
    "WorkstreamResult",
    "build_envelope",
    "derive_macro_status",
    "evaluate_all",
    "evaluate_join",
    "next_legal_action",
]
