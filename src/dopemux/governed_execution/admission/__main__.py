"""Read-only synthetic owner-fixture inspection; no dispatch or native installation."""

import argparse
import json
from pathlib import Path
import sys

from .identity import AdmissionError, ExpectedScope
from .local_owner import LocalOwnerResolver
from .owner_admission import OwnerAdmitter, strict_json


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    inspect = sub.add_parser("check-fixture", help="Inspect only explicit synthetic owner fixtures")
    inspect.add_argument("--owner-root", type=Path, required=True)
    inspect.add_argument("--request", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        request = strict_json(args.request.read_bytes())
        if not isinstance(request, dict) or set(request) != {
            "receipt_ref",
            "principal_ref",
            "expected_scope",
            "expected_generation",
            "owner_domain",
        }:
            raise AdmissionError("E_SCHEMA", "Unknown or missing fixture request fields")
        admitted = OwnerAdmitter(
            request["owner_domain"], LocalOwnerResolver(args.owner_root, fixture_mode=True)
        ).admit(
            request["receipt_ref"],
            request["principal_ref"],
            ExpectedScope.from_dict(request["expected_scope"]),
            request["expected_generation"],
        )
        print(
            json.dumps(
                {
                    "fixture_only": True,
                    "execution_authorized": False,
                    "admission": admitted.projection,
                },
                sort_keys=True,
            )
        )
        return 0
    except AdmissionError as exc:
        code, detail = exc.code, str(exc)
    except (OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
        code, detail = "E_SCHEMA", str(exc)
    print(
        json.dumps(
            {"code": code, "detail": detail, "execution_authorized": False, "authority": "NONE"}
        ),
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
