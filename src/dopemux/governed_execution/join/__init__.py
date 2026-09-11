"""W05: join-type evaluation and the AggregateReturnEnvelope builder.

Public API re-exported here for convenience; see types.py and evaluate.py
for the implementation and docstrings. envelope.py is added to this
package's public surface in slice S2.
"""
from __future__ import annotations

from .evaluate import derive_macro_status, evaluate_all, evaluate_join, next_legal_action
from .types import ConditionError, JoinDecl, JoinResult, JoinType, ReturnRef, WorkstreamResult

__all__ = [
    "ConditionError",
    "JoinDecl",
    "JoinResult",
    "JoinType",
    "ReturnRef",
    "WorkstreamResult",
    "derive_macro_status",
    "evaluate_all",
    "evaluate_join",
    "next_legal_action",
]
