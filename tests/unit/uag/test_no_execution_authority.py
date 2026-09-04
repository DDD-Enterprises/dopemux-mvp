"""No-execution / no-approval authority exposure tests."""

from __future__ import annotations


from dopemux.uag import (
    AttemptLineage,
    AttemptRecord,
    IdentityChain,
    MappingLedger,
    SemanticCore,
)
from dopemux.uag.enums import (
    AttemptSemanticState,
)
from dopemux.uag.ir import RequestedOutputContract
from dopemux.uag.enums import OutputContractClass
from dopemux.uag.request import LogicalRequest, WorkspaceBinding

FORBIDDEN_METHOD_NAMES = {
    "execute",
    "exec",
    "approve",
    "run",
    "retry",
    "fallback",
    "grant",
    "route",
    "call",
    "invoke",
}


def _public_methods(obj) -> set[str]:
    return {
        name
        for name in dir(obj)
        if not name.startswith("_") and callable(getattr(obj, name))
    }


def test_no_execution_or_approval_surface():
    lineage = AttemptLineage()
    ledger = MappingLedger()
    chain = IdentityChain()
    for obj in (lineage, ledger, chain):
        public = _public_methods(obj)
        overlap = public & FORBIDDEN_METHOD_NAMES
        assert not overlap, f"{type(obj).__name__} exposes forbidden methods: {overlap}"


def test_semantic_core_has_no_execution_surface():
    request = LogicalRequest(
        logical_request_id="req-1",
        binding=WorkspaceBinding("p", "/w", "req-1"),
        requested_output_contract=RequestedOutputContract(
            output_class=OutputContractClass.PUBLIC_TEXT
        ),
    )
    core = SemanticCore(
        request=request,
        identity_chain=IdentityChain(),
        attempt_lineage=AttemptLineage(),
        ledger=MappingLedger(),
        receipts=(),
    )
    public = _public_methods(core)
    assert not (public & FORBIDDEN_METHOD_NAMES)


def test_attempt_record_exposes_no_execution_methods():
    record = AttemptRecord(
        attempt_id="a1",
        semantic_state=AttemptSemanticState.NOT_SENT,
        selected_route_profile_id="p1",
    )
    assert not (_public_methods(record) & FORBIDDEN_METHOD_NAMES)


def test_no_retry_semantics_invented():
    # SENT_ACCEPTANCE_UNKNOWN is not retry-safe; the core offers no retry path.
    from dopemux.uag.enums import AttemptSemanticState as S

    record = AttemptRecord(
        attempt_id="a1",
        semantic_state=S.SENT_ACCEPTANCE_UNKNOWN,
        selected_route_profile_id="p1",
    )
    assert not hasattr(record, "retry")
    assert not hasattr(record, "should_retry")
