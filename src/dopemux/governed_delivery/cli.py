"""Read-only inspection CLI for the governed-delivery evidence spine.

    python -m dopemux.governed_delivery.cli validate-ref <json>
    python -m dopemux.governed_delivery.cli validate-envelope <json>
    python -m dopemux.governed_delivery.cli equivalence --audited <p> --successor <p>
    python -m dopemux.governed_delivery.cli snapshot --repo-root <p> --packet <p> --evidence <p>

No command mutates external state, contacts the network, or dispatches anything.
Exit codes: 0 accepted, 1 denied or not equivalent, 2 usage or input error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from .equivalence import ProofOnlyBundle, evaluate_proof_only_equivalence
from .models import (
    Denial,
    EnvelopeKind,
    EvidenceReference,
    GovernedDeliveryEnvelope,
    Identity,
    Subject,
)
from .snapshot import SnapshotInput, build_snapshot, read_git_fact

EXIT_OK = 0
EXIT_DENIED = 1
EXIT_USAGE = 2


def _load_json(raw: str) -> Any:
    """Accept either a literal JSON string or a path to a JSON file."""
    candidate = Path(raw)
    try:
        if candidate.exists():
            return json.loads(candidate.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SystemExit(f"cannot read {raw}: {exc}")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"not valid JSON and not an existing file: {raw} ({exc})")


def _emit(payload: Any) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _cmd_validate_ref(args: argparse.Namespace) -> int:
    raw = _load_json(args.document)
    try:
        reference = EvidenceReference.from_dict(raw)
    except Denial as denial:
        _emit({"accepted": False, "normalized_class": denial.normalized_class.value,
               "reason": denial.reason})
        return EXIT_DENIED
    _emit({"accepted": True, "evidence_id": reference.evidence_id,
           "freshness_state": reference.freshness_state.value,
           "authority_effect": reference.authority_effect.value,
           "canonical": reference.as_dict()})
    return EXIT_OK


def _cmd_validate_envelope(args: argparse.Namespace) -> int:
    raw = _load_json(args.document)
    try:
        envelope = GovernedDeliveryEnvelope(
            envelope_id=raw.get("envelope_id", ""),
            kind=EnvelopeKind(raw.get("kind", "")),
            event_type=raw.get("event_type", ""),
            identity=Identity(
                project_id=raw.get("project_id", ""),
                repository_id=raw.get("repository_id", ""),
                packet_id=raw.get("packet_id"),
            ),
            producer=raw.get("producer", ""),
            consumer=raw.get("consumer", ""),
            created_at=raw.get("created_at", ""),
            subject_ref=raw.get("subject_ref", ""),
            idempotency_key=raw.get("idempotency_key", ""),
            payload_schema=raw.get("payload_schema", ""),
            payload=raw.get("payload", {}),
            evidence_refs=[
                EvidenceReference.from_dict(item) for item in raw.get("evidence_refs", [])
            ],
            work_item_id=raw.get("work_item_id"),
        )
    except (Denial, ValueError) as exc:
        reason = exc.reason if isinstance(exc, Denial) else str(exc)
        normalized = exc.normalized_class.value if isinstance(exc, Denial) else "INVALID_INPUT_OR_ARTIFACT"
        _emit({"accepted": False, "normalized_class": normalized, "reason": reason})
        return EXIT_DENIED
    _emit({"accepted": True, "kind": envelope.kind.value, "event_type": envelope.event_type,
           "mutation_authorized": False, "canonical": envelope.as_dict()})
    return EXIT_OK


def _cmd_equivalence(args: argparse.Namespace) -> int:
    audited = _load_json(args.audited)
    successor = _load_json(args.successor)

    result = evaluate_proof_only_equivalence(
        equivalence_id=args.equivalence_id,
        audited_head=audited.get("head", ""),
        successor_head=successor.get("head", ""),
        audited_bundle=ProofOnlyBundle(audited.get("documents", {})),
        successor_bundle=ProofOnlyBundle(successor.get("documents", {})),
        allowed_paths=audited.get("allowed_paths", []),
        actual_changed_paths=successor.get("changed_paths", []),
        raw_diff_digest=successor.get("raw_diff_digest", ""),
        ancestry_established=bool(successor.get("ancestry_established", False)),
        ancestry_basis=successor.get("ancestry_basis", "UNKNOWN"),
        raw_diff_contains_no_substantive_source_change=bool(
            successor.get("raw_diff_contains_no_substantive_source_change", False)
        ),
        content_tree_equivalent_under_exclusion=bool(
            successor.get("content_tree_equivalent_under_exclusion", False)
        ),
        audited_packet_digest=audited.get("packet_digest"),
        successor_packet_digest=successor.get("packet_digest"),
        audited_policy_digest=audited.get("policy_digest"),
        successor_policy_digest=successor.get("policy_digest"),
        audited_audit_result_digest=audited.get("audit_result_digest"),
        successor_audit_result_digest=successor.get("audit_result_digest"),
        merge_base=successor.get("merge_base"),
    )
    _emit(result.as_dict())
    return EXIT_OK if result.passed else EXIT_DENIED


def _cmd_snapshot(args: argparse.Namespace) -> int:
    packet = _load_json(args.packet)
    binding = packet.get("repo_binding", {})

    evidence: list[EvidenceReference] = []
    if args.evidence:
        raw = _load_json(args.evidence)
        items = raw if isinstance(raw, list) else [raw]
        try:
            evidence = [EvidenceReference.from_dict(item) for item in items]
        except Denial as denial:
            _emit({"accepted": False, "normalized_class": denial.normalized_class.value,
                   "reason": denial.reason})
            return EXIT_DENIED

    repo_root = Path(args.repo_root)
    # Fill an unsupplied head from local git identity rather than guessing it.
    head_sha = args.head_sha or read_git_fact(repo_root, ["rev-parse", "HEAD"])

    try:
        source = SnapshotInput(
            identity=Identity(
                project_id=binding.get("project_id", ""),
                repository_id=args.repository_id
                or read_git_fact(repo_root, ["config", "--get", "remote.origin.url"])
                or binding.get("project_id", ""),
                packet_id=packet.get("id"),
            ),
            work_item_id=packet.get("id", ""),
            as_of=args.as_of,
            subject=Subject(base_sha=args.base_sha, head_sha=head_sha),
            evidence_refs=evidence,
            packet_ref=packet.get("id"),
        )
        payload = build_snapshot(source)
    except Denial as denial:
        _emit({"accepted": False, "normalized_class": denial.normalized_class.value,
               "reason": denial.reason})
        return EXIT_DENIED

    _emit(payload)
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m dopemux.governed_delivery.cli",
        description="Read-only governed-delivery inspection. Mutates nothing.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ref = sub.add_parser("validate-ref", help="validate an EvidenceReference document")
    ref.add_argument("document", help="JSON literal or path to a JSON file")
    ref.set_defaults(func=_cmd_validate_ref)

    env = sub.add_parser("validate-envelope", help="validate a GovernedDeliveryEnvelope document")
    env.add_argument("document", help="JSON literal or path to a JSON file")
    env.set_defaults(func=_cmd_validate_envelope)

    eq = sub.add_parser("equivalence", help="evaluate proof-only successor equivalence")
    eq.add_argument("--audited", required=True)
    eq.add_argument("--successor", required=True)
    eq.add_argument("--equivalence-id", default="equivalence-cli")
    eq.set_defaults(func=_cmd_equivalence)

    snap = sub.add_parser("snapshot", help="build a read-only delivery snapshot")
    snap.add_argument("--repo-root", default=".")
    snap.add_argument("--packet", required=True)
    snap.add_argument("--evidence", default=None)
    snap.add_argument("--as-of", required=True, help="explicit ISO-8601 instant; no clock is read")
    snap.add_argument("--repository-id", default=None)
    snap.add_argument("--base-sha", default=None)
    snap.add_argument("--head-sha", default=None)
    snap.set_defaults(func=_cmd_snapshot)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except Denial as denial:
        _emit({"accepted": False, "normalized_class": denial.normalized_class.value,
               "reason": denial.reason})
        return EXIT_DENIED
    except SystemExit as exc:
        if isinstance(exc.code, str):
            print(exc.code, file=sys.stderr)
            return EXIT_USAGE
        return int(exc.code or EXIT_OK)


if __name__ == "__main__":
    raise SystemExit(main())
