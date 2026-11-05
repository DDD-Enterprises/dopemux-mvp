"""Explicit synthetic OS-user-protected owner port; no native ledger installation.

Local ownership verifies the configured fixture custodian, not a cryptographic
identity or protection from hostile code running as that same OS account.
"""

import hashlib
import math
import os
from pathlib import Path
import stat
import time

from .identity import AdmissionError, ExpectedScope
from .owner_admission import OwnerEvidence, canonical, strict_json


def protected_bytes(path, *, directory=False, limit=262144):
    path = Path(path)
    if not path.is_absolute() or path.resolve() != path:
        raise AdmissionError("E_CUSTODY", "Noncanonical owner path")
    try:
        flags = os.O_RDONLY | os.O_NOFOLLOW
        fd = os.open(path, flags)
        try:
            st = os.fstat(fd)
            if st.st_uid != os.getuid() or st.st_mode & 0o077:
                raise AdmissionError(
                    "E_AUTHENTICITY", "Owner custody is not private current-user custody"
                )
            if directory:
                if not stat.S_ISDIR(st.st_mode):
                    raise AdmissionError("E_CUSTODY", "Owner root is not a directory")
                return b""
            if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or st.st_size > limit:
                raise AdmissionError("E_CUSTODY", "Unsafe owner record")
            raw = os.read(fd, limit + 1)
            if len(raw) > limit:
                raise AdmissionError("E_SCHEMA", "Owner record limit exceeded")
            return raw
        finally:
            os.close(fd)
    except OSError as exc:
        raise AdmissionError("E_ISSUER_UNAVAILABLE", "Owner source is unavailable") from exc


class LocalOwnerResolver:
    def __init__(self, root, *, fixture_mode=False):
        self.root, self.fixture_mode = Path(root), fixture_mode

    def resolve(self, receipt_ref, principal_ref):
        if self.fixture_mode is not True:
            raise AdmissionError("E_ISSUER_UNAVAILABLE", "No live native owner binding installed")
        protected_bytes(self.root, directory=True)
        owner = strict_json(protected_bytes(self.root / "owner.json"))
        required = {
            "fixture_only",
            "owner_domain",
            "issuer_ref",
            "generation",
            "registry_generation",
            "registry_file",
            "revoked",
            "expires_at",
            "principals",
            "trust_digest",
            "receipts",
        }
        if (
            not isinstance(owner, dict)
            or set(owner) != required
            or owner["fixture_only"] is not True
        ):
            raise AdmissionError("E_SCHEMA", "Expected explicitly synthetic owner fixture binding")
        if owner["revoked"] is True:
            raise AdmissionError("E_REVOKED", "Owner binding was revoked")
        if (
            type(owner["expires_at"]) not in (int, float)
            or not math.isfinite(owner["expires_at"])
            or owner["expires_at"] <= time.time()
        ):
            raise AdmissionError("E_STALE", "Owner binding expired")
        if (
            type(owner["generation"]) is not int
            or owner["generation"] < 1
            or type(owner["registry_generation"]) is not int
            or owner["registry_generation"] < 1
            or type(owner["revoked"]) is not bool
            or not isinstance(owner["principals"], dict)
            or not isinstance(owner["receipts"], dict)
            or not isinstance(owner["registry_file"], str)
        ):
            raise AdmissionError("E_SCHEMA", "Malformed owner binding")
        principal = owner["principals"].get(principal_ref)
        if (
            not isinstance(principal, dict)
            or type(principal.get("uid")) is not int
            or principal.get("uid") != os.getuid()
        ):
            raise AdmissionError("E_AUTHENTICITY", "Principal is not mapped to actual local UID")
        if not isinstance(principal.get("roles"), list) or any(
            not isinstance(role, str) for role in principal["roles"]
        ):
            raise AdmissionError("E_SCHEMA", "Malformed principal roles")
        if owner["owner_domain"] not in principal["roles"]:
            raise AdmissionError("E_ROLE", "Principal does not hold the configured owner role")
        record = owner["receipts"].get(receipt_ref["ref_id"])
        if not isinstance(record, dict) or record.get("evidence") != receipt_ref:
            raise AdmissionError("E_AUTHENTICITY", "Receipt is not the current owner-mapped record")
        if set(record) != {
            "evidence",
            "kind",
            "generation",
            "revoked",
            "expires_at",
            "scope",
            "delegation_depth_limit",
        }:
            raise AdmissionError("E_SCHEMA", "Malformed owner receipt record")
        if (
            type(record["generation"]) is not int
            or type(record["revoked"]) is not bool
            or type(record["delegation_depth_limit"]) is not int
            or not 0 <= record["delegation_depth_limit"] <= 16
            or type(record["expires_at"]) not in (int, float)
            or not math.isfinite(record["expires_at"])
        ):
            raise AdmissionError("E_SCHEMA", "Malformed receipt limits")
        if record.get("revoked") is True:
            raise AdmissionError("E_REVOKED", "Source receipt revoked")
        if record["generation"] != owner["generation"]:
            raise AdmissionError("E_STALE", "Source and owner generations differ")
        relative = Path(receipt_ref["locator"])
        registry_relative = Path(owner["registry_file"])
        for path in (relative, registry_relative):
            if path.is_absolute() or ".." in path.parts:
                raise AdmissionError("E_CUSTODY", "Owner reference escapes configured root")
        path = self.root / relative
        raw = protected_bytes(path)
        if hashlib.sha256(raw).hexdigest() != receipt_ref["sha256"]:
            raise AdmissionError("E_DRIFT", "Canonical source bytes changed")
        native = strict_json(raw)
        grant = ExpectedScope.from_dict(record["scope"])
        if not isinstance(native, dict):
            raise AdmissionError("E_SCHEMA", "Canonical source must be an object")
        if native.get("allowlist_digest") != hashlib.sha256(canonical(record["scope"])).hexdigest():
            raise AdmissionError("E_DRIFT", "Canonical allowlist no longer binds the owner scope")
        registry_path = self.root / registry_relative
        strict_json(protected_bytes(registry_path))
        return OwnerEvidence(
            owner["owner_domain"],
            owner["issuer_ref"],
            principal_ref,
            owner["generation"],
            min(owner["expires_at"], record["expires_at"]),
            owner["trust_digest"],
            record["kind"],
            raw,
            dict(receipt_ref),
            grant,
            record["delegation_depth_limit"],
            registry_path,
            owner["registry_generation"],
            True,
        )
