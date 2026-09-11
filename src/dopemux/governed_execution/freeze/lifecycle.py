"""Freeze lifecycle state machine.

A pure state machine over ``FreezeState`` (mirroring
``enums.v1.schema.json#/definitions/freeze_state``: FROZEN, UNFROZEN,
SUPERSEDED, UNKNOWN) and the events
``FROZEN -> UNFREEZE -> REPAIR -> REVALIDATE -> REVIEW_SETTLE -> NEW_FREEZE``
documented in docs/03-reference/governance/governed-execution-contract-v2.md.

``FreezeLifecycle`` is immutable: ``apply`` always returns a new instance and
never mutates the receipt payload it was built from (evidence is
append-only; a FreezeReceipt's own ``freeze_state`` field, once authored, is
never rewritten). A predecessor superseded by NEW_FREEZE is recorded as a
child ``FreezeLifecycle`` (with its ``state`` set to ``SUPERSEDED``) on the
new lifecycle's ``predecessor`` attribute, never by mutating the old
receipt's stored bytes.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Any, Mapping, Union

from dopemux.governed_execution.receipts.store import EvidenceRef


class FreezeState(str, Enum):
    FROZEN = "FROZEN"
    UNFROZEN = "UNFROZEN"
    SUPERSEDED = "SUPERSEDED"
    UNKNOWN = "UNKNOWN"


class IllegalTransition(Exception):
    """Raised by ``FreezeLifecycle.apply`` for any transition not in the
    legal set FROZEN--UNFREEZE-->UNFROZEN--{REPAIR_RECORDED,REVALIDATED,
    REVIEW_SETTLED}-->UNFROZEN--NEW_FREEZE-->FROZEN.
    """


class AuditBeforeFreeze(Exception):
    """Raised by ``attach_audit_ref`` when the subject is not FROZEN, or the
    audited head does not equal the FreezeReceipt's own head_sha.
    """


@dataclass(frozen=True)
class Unfreeze:
    reason: str


@dataclass(frozen=True)
class RepairRecorded:
    ref: EvidenceRef


@dataclass(frozen=True)
class Revalidated:
    refs: tuple[EvidenceRef, ...]


@dataclass(frozen=True)
class ReviewSettled:
    refs: tuple[EvidenceRef, ...]


@dataclass(frozen=True)
class NewFreeze:
    receipt: Mapping[str, Any]


FreezeEvent = Union[Unfreeze, RepairRecorded, Revalidated, ReviewSettled, NewFreeze]


@dataclass(frozen=True)
class FreezeLifecycle:
    """The current lifecycle state for one FreezeReceipt subject.

    ``FreezeLifecycle(receipt)`` constructs directly in the FROZEN state (a
    freshly authored FreezeReceipt always records ``freeze_state ==
    "FROZEN"``), matching the packet's ``FreezeLifecycle(receipt)`` shape.
    ``FreezeLifecycle.start(receipt)`` is the same construction with an
    explicit guard that ``receipt`` actually records FROZEN, for callers that
    want that checked rather than assumed.
    """

    receipt: Mapping[str, Any]
    state: FreezeState = FreezeState.FROZEN
    predecessor: "FreezeLifecycle | None" = None

    @classmethod
    def start(cls, receipt: Mapping[str, Any]) -> "FreezeLifecycle":
        """Begin a lifecycle from a freshly authored FreezeReceipt.

        The receipt must itself record ``freeze_state == "FROZEN"`` (what
        ``author_freeze_receipt`` always produces); anything else is not a
        legal starting point and raises ``IllegalTransition``.
        """
        if receipt.get("freeze_state") != FreezeState.FROZEN.value:
            raise IllegalTransition("initial receipt must record freeze_state FROZEN")
        return cls(receipt=receipt, state=FreezeState.FROZEN)

    def apply(self, event: FreezeEvent) -> "FreezeLifecycle":
        """Apply ``event``, returning a new ``FreezeLifecycle``.

        Raises ``IllegalTransition`` for any (state, event) pair outside the
        documented legal set.
        """
        if self.state is FreezeState.FROZEN and isinstance(event, Unfreeze):
            return replace(self, state=FreezeState.UNFROZEN)

        if self.state is FreezeState.UNFROZEN and isinstance(
            event, (RepairRecorded, Revalidated, ReviewSettled)
        ):
            return replace(self, state=FreezeState.UNFROZEN)

        if self.state is FreezeState.UNFROZEN and isinstance(event, NewFreeze):
            if event.receipt.get("freeze_state") != FreezeState.FROZEN.value:
                raise IllegalTransition("NEW_FREEZE receipt must record freeze_state FROZEN")
            if event.receipt.get("supersedes_freeze_ref") is None:
                raise IllegalTransition(
                    "NEW_FREEZE receipt must set supersedes_freeze_ref"
                )
            superseded = replace(self, state=FreezeState.SUPERSEDED)
            return FreezeLifecycle(
                receipt=event.receipt,
                state=FreezeState.FROZEN,
                predecessor=superseded,
            )

        raise IllegalTransition(f"{self.state.value} does not accept {type(event).__name__}")


def attach_audit_ref(
    lifecycle: FreezeLifecycle, audit_ref: EvidenceRef, audited_head: str
) -> EvidenceRef:
    """Bind ``audit_ref`` to ``lifecycle``'s subject, returning it unchanged.

    Raises ``AuditBeforeFreeze`` unless ``lifecycle.state`` is FROZEN and
    ``audited_head`` equals the FreezeReceipt's own ``head_sha`` -- any
    substantive mutation after FROZEN forces UNFREEZE first, and an audit ref
    can never legally attach to anything but the exact frozen head.
    """
    if lifecycle.state is not FreezeState.FROZEN:
        raise AuditBeforeFreeze(f"subject is {lifecycle.state.value}, not FROZEN")
    if audited_head != lifecycle.receipt["head_sha"]:
        raise AuditBeforeFreeze(
            f"audited_head {audited_head!r} != frozen head_sha "
            f"{lifecycle.receipt['head_sha']!r}"
        )
    return audit_ref
