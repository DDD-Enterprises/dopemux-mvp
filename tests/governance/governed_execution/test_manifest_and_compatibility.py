"""Manifest integrity and v1 -> v2 compatibility tests.

Covers: manifest sha256 entries match file bytes; kit v1 schema sha256
match the manifest's ADOPTED entries; every v1 property in the two kit
schemas exists in its v2 successor with an equal type (additive-only, no
retyping); the kit's own template instances validate against kit v1 and
fail v2 only on the newly added required fields; and no schema in this set
declares an inline duplicate enum literal list (every enum is $ref'd from
enums.v1).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft7Validator, validators
from referencing import Registry

REPO_ROOT = Path(__file__).resolve().parents[3]
GOV_DIR = REPO_ROOT / "schemas" / "governed_execution"
CT_DIR = REPO_ROOT / ".control-tower"
MANIFEST_PATH = GOV_DIR / "manifest.v1.json"


def _load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="ascii") as fh:
        return json.load(fh)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_manifest_entries_match_file_bytes() -> None:
    manifest = _load(MANIFEST_PATH)
    for entry in manifest["entries"]:
        path = REPO_ROOT / entry["path"]
        assert path.is_file(), f"manifest entry path does not exist: {entry['path']}"
        actual = _sha256(path)
        assert actual == entry["sha256"], (
            f"{entry['path']}: manifest sha256 {entry['sha256']} != actual {actual}"
        )


def test_kit_v1_schemas_are_adopted_and_byte_identical() -> None:
    manifest = _load(MANIFEST_PATH)
    adopted = {e["path"]: e for e in manifest["entries"] if e["status"] == "ADOPTED"}
    kit_paths = {
        ".control-tower/schemas/supervisor_macro_packet.schema.json",
        ".control-tower/schemas/execution_binding.schema.json",
    }
    assert kit_paths <= set(adopted), f"kit schemas missing from ADOPTED entries: {kit_paths - set(adopted)}"
    for rel in kit_paths:
        entry = adopted[rel]
        actual = _sha256(REPO_ROOT / rel)
        assert actual == entry["sha256"], f"{rel}: kit file changed since manifest was written"


def test_manifest_lists_every_repo_owned_schema() -> None:
    manifest = _load(MANIFEST_PATH)
    manifest_paths = {e["path"] for e in manifest["entries"]}
    on_disk = {
        f"schemas/governed_execution/{p.name}"
        for p in GOV_DIR.glob("*.schema.json")
    }
    assert on_disk <= manifest_paths, f"schema files missing from manifest: {on_disk - manifest_paths}"


# ---------------------------------------------------------------------------
# v1 -> v2 compatibility: every v1 property retained with an equal type.
# ---------------------------------------------------------------------------

_KIT_TO_V2 = {
    "supervisor_macro_packet.schema.json": "macro_packet.v2.schema.json",
    "execution_binding.schema.json": "execution_binding.v2.schema.json",
}


def _resolve(schema_node: dict, registry: Registry, base_uri: str) -> dict:
    if "$ref" in schema_node:
        resolver = registry.resolver(base_uri=base_uri)
        resolved = resolver.lookup(schema_node["$ref"])
        return resolved.contents
    return schema_node


def _leaf_type_signature(node: dict, registry: Registry, base_uri: str) -> tuple:
    node = _resolve(node, registry, base_uri)
    node_type = node.get("type")
    enum_vals = node.get("enum")
    const_val = node.get("const")
    if enum_vals is not None:
        return ("enum", tuple(sorted(enum_vals)))
    if const_val is not None:
        return ("const-type", type(const_val).__name__)
    if node_type is not None:
        return ("type", node_type if isinstance(node_type, str) else tuple(sorted(node_type)))
    return ("object", None) if "properties" in node else ("unknown", None)


def _walk_v1_properties(node: dict, prefix: str = "") -> dict[str, dict]:
    """Flatten every v1 property path -> its schema node.

    Recurses into nested objects (one level of object nesting per call) and
    into arrays-of-objects (workstreams[], joins[], alternatives_considered[],
    upstream_obligations[], allowed_fallbacks[]), using a "name[]." path
    segment for the latter so array-item properties are covered too.
    """
    out: dict[str, dict] = {}
    props = node.get("properties", {})
    for name, sub in props.items():
        path = f"{prefix}{name}"
        out[path] = sub
        if sub.get("type") == "object" and "properties" in sub:
            out.update(_walk_v1_properties(sub, prefix=f"{path}."))
        elif sub.get("type") == "array":
            items = sub.get("items")
            if isinstance(items, dict) and items.get("type") == "object" and "properties" in items:
                out.update(_walk_v1_properties(items, prefix=f"{path}[]."))
    return out


@pytest.mark.parametrize("kit_file,v2_file", sorted(_KIT_TO_V2.items()))
def test_v1_properties_retained_with_equal_type_in_v2(kit_file, v2_file, registry) -> None:
    v1_schema = _load(CT_DIR / "schemas" / kit_file)
    v2_schema = _load(GOV_DIR / v2_file)
    v2_base_uri = v2_schema["$id"]
    v1_flat = _walk_v1_properties(v1_schema)
    v2_flat = _walk_v1_properties(v2_schema)
    missing = set(v1_flat) - set(v2_flat)
    assert not missing, f"{v2_file}: v1 properties dropped: {sorted(missing)}"
    for path, v1_node in v1_flat.items():
        v2_node = v2_flat[path]
        # v1's oneOf(packet_id|macro_id) is a keyword, not a property; type
        # equality is checked property-by-property, which already covers
        # packet_id/macro_id as ordinary optional/required string fields.
        # schema_version's const VALUE is intentionally different between
        # v1 and v2 (that is what a version bump means); only its type
        # (string const) is required to match, which the signature already
        # captures via ("const-type", "str") regardless of the literal value.
        v1_sig = _leaf_type_signature(v1_node, registry, v2_base_uri)
        v2_sig = _leaf_type_signature(v2_node, registry, v2_base_uri)
        if v1_sig[0] == "object" or v2_sig[0] == "object":
            # Nested objects are compared property-by-property via recursion
            # in _walk_v1_properties; skip the coarse whole-object signature.
            continue
        assert v1_sig == v2_sig, f"{v2_file}:{path}: type changed {v1_sig} -> {v2_sig}"


# ---------------------------------------------------------------------------
# Kit template instances: valid against v1 (2020-12), and fail v2 only on
# the newly added required fields.
# ---------------------------------------------------------------------------

_EXECUTION_BINDING_ADDED: dict[tuple, set[str]] = {
    (): {
        "macro_id",
        "runner_version",
        "effort_requested",
        "effort_observed",
        "auth_profile_ref",
        "network_posture",
        "containment_posture",
        "fallback_outcome",
        "response_claimed_model",
        "provider_attested_model",
        "independence_class",
        "qualification_receipt_ref",
    },
}

_MACRO_PACKET_ADDED: dict[tuple, set[str]] = {
    ("team_lead",): {"binding_policy"},
    ("workstreams", 0): {"audit_group", "return_contract"},
}

_TEMPLATE_CASES = [
    (
        ".control-tower/templates/EXECUTION_BINDING.template.json",
        "execution_binding.v2.schema.json",
        _EXECUTION_BINDING_ADDED,
    ),
    (
        ".control-tower/templates/SUPERVISOR_MACRO_PACKET.template.json",
        "macro_packet.v2.schema.json",
        _MACRO_PACKET_ADDED,
    ),
]


def _kit_v1_validator(kit_file: str) -> Draft7Validator:
    schema = _load(CT_DIR / "schemas" / kit_file)
    validator_cls = validators.validator_for(schema)
    validator_cls.check_schema(schema)
    return validator_cls(schema)


@pytest.mark.parametrize(
    "template_rel,v2_file,added_map",
    _TEMPLATE_CASES,
    ids=[c[0] for c in _TEMPLATE_CASES],
)
def test_template_valid_v1_and_additive_only_v2(template_rel, v2_file, added_map, registry) -> None:
    template = _load(REPO_ROOT / template_rel)
    kit_file = "supervisor_macro_packet.schema.json" if "MACRO_PACKET" in template_rel else "execution_binding.schema.json"

    v1_validator = _kit_v1_validator(kit_file)
    v1_errors = list(v1_validator.iter_errors(template))
    assert not v1_errors, f"{template_rel} must validate against kit v1: {[e.message for e in v1_errors]}"

    v2_schema = _load(GOV_DIR / v2_file)
    v2_validator = Draft7Validator(v2_schema, registry=registry)
    v2_errors = list(v2_validator.iter_errors(template))
    assert v2_errors, f"{template_rel} unexpectedly satisfies {v2_file} with no added-field gaps"

    required_errors = []
    for err in v2_errors:
        path = tuple(err.absolute_path)
        # schema_version's const VALUE necessarily differs between v1 and v2
        # (that is what a version bump means); this is not a retyped or
        # removed v1 field, so it is the one allowed non-required error.
        if path == ("schema_version",) and err.validator == "const":
            continue
        assert err.validator == "required", (
            f"{template_rel} against {v2_file}: non-required error at "
            f"{path} ({err.validator}) indicates a retyped/removed v1 field: {err.message}"
        )
        required_errors.append(err)

    for err in required_errors:
        path = tuple(err.absolute_path)
        allowed = added_map.get(path)
        assert allowed is not None, f"{template_rel}: unexpected required-error path {path}"
        missing = set(err.validator_value) - set(err.instance.keys())
        unexpected = missing - allowed
        assert not unexpected, (
            f"{template_rel} at {path}: required-error names fields outside the added set: {unexpected}"
        )


# ---------------------------------------------------------------------------
# No inline duplicate enum literal lists outside enums.v1.
# ---------------------------------------------------------------------------


def _find_enum_keywords(node: Any, path: str, hits: list[str]) -> None:
    if isinstance(node, dict):
        if "enum" in node:
            hits.append(path or "<root>")
        for key, value in node.items():
            _find_enum_keywords(value, f"{path}.{key}", hits)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            _find_enum_keywords(item, f"{path}[{i}]", hits)


def test_no_inline_enum_outside_enums_v1(schemas) -> None:
    for shortname, schema in schemas.items():
        if shortname == "enums.v1":
            continue
        hits: list[str] = []
        _find_enum_keywords(schema, "", hits)
        assert not hits, f"{shortname}: inline enum literal list(s) found at {hits}; use $ref to enums.v1 instead"
