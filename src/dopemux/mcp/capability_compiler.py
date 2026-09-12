"""Deterministic shadow compiler for MCP client capability decisions."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator

from dopemux.mcp.fleet_catalog import DuplicateKeyError, load_yaml_no_duplicate_keys


CLIENTS = ("claude", "codex", "opencode", "gemini", "copilot")
KNOWN_NON_TARGET_CLIENTS = frozenset({"chatgpt"})
COMPILATION_SCHEMA_VERSION = "mcp-capability-compilation.v1"
POLICY_SCHEMA_VERSION = "mcp-capability-policy.v1"
_POLICY_FIELDS = {
    "schema_version",
    "mode",
    "client_order",
    "lifecycle_decisions",
    "transport_decisions",
    "clients",
}
_LIFECYCLE_DECISIONS = {
    "active": "evaluate",
    "operator-managed": "evaluate",
    "planned-active": "deferred",
    "decision-required": "blocked",
}
_TRANSPORT_DECISIONS = {
    "http": "evaluate",
    "sse": "evaluate",
    "stdio": "evaluate",
    "external": "deferred",
}
_EXPOSURE_DECISIONS = {
    "full": "direct",
    "full-sequenced": "sequenced",
    "read-plane": "facade",
    "facade": "facade",
    "none": "omitted",
}


class CapabilityCompilationError(ValueError):
    """Raised when capability policy or catalog semantics are not explicit."""


def load_shadow_policy(policy_path: Path, schema_path: Path) -> dict[str, Any]:
    """Load and schema-validate the repository-owned shadow policy."""

    try:
        policy = load_yaml_no_duplicate_keys(policy_path)
    except DuplicateKeyError as exc:
        raise CapabilityCompilationError(str(exc)) from exc
    if not isinstance(policy, dict):
        raise CapabilityCompilationError(f"{policy_path}: policy must be a mapping")
    with schema_path.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    Draft7Validator.check_schema(schema)
    errors = sorted(
        Draft7Validator(schema).iter_errors(policy),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.absolute_path) or "<root>"
        raise CapabilityCompilationError(
            f"{policy_path}: policy schema validation failed at {location}: {first.message}"
        )
    return policy


def load_catalog(catalog_path: Path) -> dict[str, Any]:
    """Load a catalog using the fleet's duplicate-key-safe YAML loader."""

    catalog = load_yaml_no_duplicate_keys(catalog_path)
    if not isinstance(catalog, dict):
        raise CapabilityCompilationError(f"{catalog_path}: catalog must be a mapping")
    return catalog


def _exposure_for(spec: Mapping[str, Any], client: str) -> str:
    agents = spec.get("agents")
    if agents == "none" or agents is None:
        return "none"
    if not isinstance(agents, Mapping):
        raise CapabilityCompilationError("server `agents` must be a mapping or `none`")
    unknown_clients = set(agents) - set(CLIENTS) - KNOWN_NON_TARGET_CLIENTS
    if unknown_clients:
        raise CapabilityCompilationError(
            f"server `agents` has unknown client keys: {sorted(unknown_clients)!r}"
        )
    return str(agents.get(client, "none"))


def _validate_policy_semantics(policy: Mapping[str, Any]) -> None:
    fields = set(policy)
    if fields != _POLICY_FIELDS:
        raise CapabilityCompilationError(
            f"unexpected policy fields: {sorted(fields ^ _POLICY_FIELDS)!r}"
        )
    if policy.get("schema_version") != POLICY_SCHEMA_VERSION:
        raise CapabilityCompilationError(
            f"schema_version must be `{POLICY_SCHEMA_VERSION}`"
        )
    if policy.get("mode") != "shadow":
        raise CapabilityCompilationError("capability policy mode must be `shadow`")
    if tuple(policy.get("client_order") or ()) != CLIENTS:
        raise CapabilityCompilationError(
            f"client_order must be exactly {list(CLIENTS)!r}"
        )
    if policy.get("lifecycle_decisions") != _LIFECYCLE_DECISIONS:
        raise CapabilityCompilationError("lifecycle decisions do not match T0 contract")
    if policy.get("transport_decisions") != _TRANSPORT_DECISIONS:
        raise CapabilityCompilationError("transport decisions do not match T0 contract")

    clients_policy = policy.get("clients")
    if not isinstance(clients_policy, Mapping) or set(clients_policy) != set(CLIENTS):
        raise CapabilityCompilationError(f"clients must be exactly {list(CLIENTS)!r}")
    for client in CLIENTS:
        client_policy = clients_policy[client]
        if not isinstance(client_policy, Mapping) or set(client_policy) != {
            "exposure_decisions"
        }:
            raise CapabilityCompilationError(
                f"client `{client}` policy must contain only exposure decisions"
            )
        if client_policy.get("exposure_decisions") != _EXPOSURE_DECISIONS:
            raise CapabilityCompilationError(
                f"client `{client}` exposure decisions do not match T0 contract"
            )


def compile_capability_matrix(
    catalog: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> dict[str, Any]:
    """Compile catalog exposure semantics into an audit-only client projection."""

    _validate_policy_semantics(policy)

    clients_policy = policy.get("clients")
    if not isinstance(clients_policy, Mapping):
        raise CapabilityCompilationError(
            "capability policy requires a `clients` mapping"
        )
    lifecycle_decisions = policy.get("lifecycle_decisions")
    if not isinstance(lifecycle_decisions, Mapping):
        raise CapabilityCompilationError(
            "capability policy requires `lifecycle_decisions`"
        )
    transport_decisions = policy.get("transport_decisions")
    if not isinstance(transport_decisions, Mapping):
        raise CapabilityCompilationError(
            "capability policy requires `transport_decisions`"
        )

    servers = catalog.get("servers")
    if not isinstance(servers, Mapping):
        raise CapabilityCompilationError("MCP catalog requires a `servers` mapping")

    compiled_clients: list[dict[str, Any]] = []
    for client in CLIENTS:
        client_policy = clients_policy.get(client)
        if not isinstance(client_policy, Mapping):
            raise CapabilityCompilationError(
                f"missing capability policy for client `{client}`"
            )
        exposure_decisions = client_policy.get("exposure_decisions")
        if not isinstance(exposure_decisions, Mapping):
            raise CapabilityCompilationError(
                f"client `{client}` requires `exposure_decisions`"
            )

        compiled_servers: list[dict[str, str]] = []
        for name, raw_spec in sorted(servers.items()):
            if not isinstance(raw_spec, Mapping):
                raise CapabilityCompilationError(f"server `{name}` must be a mapping")
            lifecycle = str(raw_spec.get("lifecycle"))
            transport = str(raw_spec.get("transport"))
            exposure = _exposure_for(raw_spec, client)
            lifecycle_decision = lifecycle_decisions.get(lifecycle)
            if not isinstance(lifecycle_decision, str):
                raise CapabilityCompilationError(
                    f"server `{name}` has unknown lifecycle `{lifecycle}`"
                )
            transport_decision = transport_decisions.get(transport)
            if not isinstance(transport_decision, str):
                raise CapabilityCompilationError(
                    f"server `{name}` has unknown transport `{transport}`"
                )
            exposure_decision = exposure_decisions.get(exposure)
            if not isinstance(exposure_decision, str):
                raise CapabilityCompilationError(
                    f"client `{client}` has no decision for exposure `{exposure}`"
                )
            if lifecycle_decision != "evaluate":
                decision = lifecycle_decision
                reason = f"lifecycle:{lifecycle}"
            elif transport_decision != "evaluate":
                decision = transport_decision
                reason = f"transport:{transport}"
            else:
                decision = exposure_decision
                reason = f"exposure:{exposure}"
            compiled_servers.append(
                {
                    "decision": decision,
                    "exposure": exposure,
                    "lifecycle": lifecycle,
                    "name": str(name),
                    "reason": reason,
                    "transport": transport,
                }
            )
        compiled_clients.append({"client": client, "servers": compiled_servers})

    return {
        "schema_version": COMPILATION_SCHEMA_VERSION,
        "mode": "shadow",
        "clients": compiled_clients,
    }
