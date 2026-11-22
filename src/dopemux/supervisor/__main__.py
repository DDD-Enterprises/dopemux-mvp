"""Lean local coordinator CLI: no service startup, dotenv or provider imports."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from .runtime import Runtime
from .transport import ReturnReceiver, read_json


def main(argv=None):
    parser = argparse.ArgumentParser(description="Bounded trusted local project mandates")
    parser.add_argument("--state-root", type=Path)
    parser.add_argument("--return-root", type=Path, required=True)
    parser.add_argument("--receiver-ref", required=True)
    commands = parser.add_subparsers(dest="action", required=True)
    admit = commands.add_parser("admit", help="Admit an already authorized exact mandate")
    admit.add_argument("manifest", type=Path)
    admit.add_argument("--authorization-ref", required=True)
    for name in ("run", "status", "deliver", "receive"):
        commands.add_parser(name)
    control = commands.add_parser("control", help="Current local UID narrows a live mandate")
    control.add_argument("grant_id")
    control.add_argument("--sequence", type=int, required=True)
    control.add_argument("--receipt-ref", required=True)
    control.add_argument(
        "--action", dest="control_action", choices=["deny", "revoke", "stop"], required=True
    )
    control.add_argument("--gate")
    control.add_argument("--condition")
    gates = commands.add_parser("observe-gates", help="Trusted current gate evidence")
    gates.add_argument("work_id")
    gates.add_argument("--receipt-ref", required=True)
    gates.add_argument("--gates-json", required=True)
    accept = commands.add_parser(
        "record-acceptance", help="Record independently verified native acceptance"
    )
    accept.add_argument("work_id")
    accept.add_argument("--receipt-ref", required=True)
    accept.add_argument("--capability", required=True)
    settle = commands.add_parser(
        "reconcile", help="Trusted evidence-based unknown custody settlement"
    )
    settle.add_argument("work_id")
    settle.add_argument("--receipt-ref", required=True)
    settle.add_argument("--outcome", choices=["SUCCEEDED", "FAILED"], required=True)
    settle.add_argument("--spent-micros", type=int, required=True)
    settle.add_argument("--elapsed-seconds", type=float, required=True)
    settle.add_argument("--process-closed", action="store_true", required=True)
    settle.add_argument("--evidence-ref", action="append", required=True)
    args = parser.parse_args(argv)
    runtime = None
    try:
        if args.action == "receive":
            result = {
                "local_delivery_records_created": ReturnReceiver(
                    args.return_root, args.receiver_ref
                ).receive(),
                "native_acceptance": "NOT_ASSERTED",
                "master_ack": "NOT_ASSERTED",
            }
        else:
            if args.state_root is None:
                parser.error("--state-root is required for coordinator operations")
            runtime = Runtime(args.state_root, args.return_root, args.receiver_ref)
            if args.action == "admit":
                runtime.admit(
                    read_json(args.manifest, 65536),
                    authorization_ref=args.authorization_ref,
                )
            elif args.action == "run":
                asyncio.run(runtime.run())
            elif args.action == "deliver":
                with runtime.coordinator():
                    asyncio.run(runtime.deliver_returns())
            elif args.action == "control":
                runtime.kernel.control_mandate(
                    args.grant_id,
                    sequence=args.sequence,
                    receipt_ref=args.receipt_ref,
                    action=args.control_action,
                    gate=args.gate,
                    condition=args.condition,
                )
            elif args.action == "observe-gates":
                with runtime.coordinator():
                    runtime.kernel.update_gates(
                        args.work_id,
                        gates=json.loads(args.gates_json),
                        receipt_ref=args.receipt_ref,
                    )
            elif args.action == "record-acceptance":
                with runtime.coordinator():
                    runtime.kernel.accept(
                        args.work_id,
                        receipt_ref=args.receipt_ref,
                        capability=args.capability,
                    )
            elif args.action == "reconcile":
                with runtime.coordinator():
                    runtime.kernel.resolve_unknown(
                        args.work_id,
                        outcome=args.outcome,
                        spent_micros=args.spent_micros,
                        elapsed_seconds=args.elapsed_seconds,
                        evidence_refs=tuple(args.evidence_ref),
                        receipt_ref=args.receipt_ref,
                        process_closed=args.process_closed,
                    )
            result = runtime.status()
        print(json.dumps(result, sort_keys=True, allow_nan=False))
        if args.action == "run":
            statuses = {x["status"] for x in result["mandates"].values()}
            if "HELD" in statuses:
                return 3
            if statuses - {"COMPLETED_PENDING_NATIVE_ACCEPTANCE"}:
                return 4
        return 0
    except (ValueError, KeyError, OSError) as exc:
        print(
            json.dumps({"error": type(exc).__name__, "detail": str(exc), "authority": "NONE"}),
            file=sys.stderr,
        )
        return 2
    finally:
        if runtime is not None:
            runtime.close()


if __name__ == "__main__":
    raise SystemExit(main())
