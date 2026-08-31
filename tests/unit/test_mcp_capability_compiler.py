from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


CLIENTS = ("claude", "codex", "opencode", "gemini", "copilot")
REPO_ROOT = Path(__file__).resolve().parents[2]


def _compiler_module():
    try:
        return importlib.import_module("dopemux.mcp.capability_compiler")
    except ModuleNotFoundError as exc:
        pytest.fail(f"capability compiler is missing: {exc}")


def _shadow_policy() -> dict:
    return {
        "schema_version": "mcp-capability-policy.v1",
        "mode": "shadow",
        "client_order": list(CLIENTS),
        "lifecycle_decisions": {
            "active": "evaluate",
            "operator-managed": "evaluate",
            "planned-active": "deferred",
            "decision-required": "blocked",
        },
        "transport_decisions": {
            "http": "evaluate",
            "sse": "evaluate",
            "stdio": "evaluate",
            "external": "deferred",
        },
        "clients": {
            client: {
                "exposure_decisions": {
                    "full": "direct",
                    "full-sequenced": "sequenced",
                    "read-plane": "facade",
                    "facade": "facade",
                    "none": "omitted",
                }
            }
            for client in CLIENTS
        },
    }


def test_compile_emits_stable_five_client_projection():
    compiler = _compiler_module()
    catalog = {
        "version": 1,
        "servers": {
            "alpha": {
                "lifecycle": "active",
                "transport": "http",
                "agents": {
                    "claude": "full",
                    "codex": "full-sequenced",
                    "opencode": "read-plane",
                    "gemini": "none",
                    "copilot": "facade",
                },
            }
        },
    }

    result = compiler.compile_capability_matrix(catalog, _shadow_policy())

    assert result == {
        "schema_version": "mcp-capability-compilation.v1",
        "mode": "shadow",
        "clients": [
            {
                "client": "claude",
                "servers": [
                    {
                        "decision": "direct",
                        "exposure": "full",
                        "lifecycle": "active",
                        "name": "alpha",
                        "reason": "exposure:full",
                        "transport": "http",
                    }
                ],
            },
            {
                "client": "codex",
                "servers": [
                    {
                        "decision": "sequenced",
                        "exposure": "full-sequenced",
                        "lifecycle": "active",
                        "name": "alpha",
                        "reason": "exposure:full-sequenced",
                        "transport": "http",
                    }
                ],
            },
            {
                "client": "opencode",
                "servers": [
                    {
                        "decision": "facade",
                        "exposure": "read-plane",
                        "lifecycle": "active",
                        "name": "alpha",
                        "reason": "exposure:read-plane",
                        "transport": "http",
                    }
                ],
            },
            {
                "client": "gemini",
                "servers": [
                    {
                        "decision": "omitted",
                        "exposure": "none",
                        "lifecycle": "active",
                        "name": "alpha",
                        "reason": "exposure:none",
                        "transport": "http",
                    }
                ],
            },
            {
                "client": "copilot",
                "servers": [
                    {
                        "decision": "facade",
                        "exposure": "facade",
                        "lifecycle": "active",
                        "name": "alpha",
                        "reason": "exposure:facade",
                        "transport": "http",
                    }
                ],
            },
        ],
    }


def test_compile_applies_overrides_and_ignores_catalog_mapping_order():
    compiler = _compiler_module()
    server_specs = {
        "active": {
            "lifecycle": "active",
            "transport": "http",
            "agents": {client: "full" for client in CLIENTS},
        },
        "external": {
            "lifecycle": "active",
            "transport": "external",
            "agents": {client: "full" for client in CLIENTS},
        },
        "planned": {
            "lifecycle": "planned-active",
            "transport": "http",
            "agents": {client: "full" for client in CLIENTS},
        },
        "quarantined": {
            "lifecycle": "decision-required",
            "transport": "http",
            "agents": {client: "full" for client in CLIENTS},
        },
    }
    forward = {"version": 1, "servers": dict(server_specs.items())}
    reverse = {"version": 1, "servers": dict(reversed(server_specs.items()))}

    forward_result = compiler.compile_capability_matrix(forward, _shadow_policy())
    reverse_result = compiler.compile_capability_matrix(reverse, _shadow_policy())

    assert reverse_result == forward_result
    assert [
        (server["name"], server["decision"], server["reason"])
        for server in forward_result["clients"][0]["servers"]
    ] == [
        ("active", "direct", "exposure:full"),
        ("external", "deferred", "transport:external"),
        ("planned", "deferred", "lifecycle:planned-active"),
        ("quarantined", "blocked", "lifecycle:decision-required"),
    ]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("lifecycle", "mystery", "unknown lifecycle"),
        ("transport", "websocket", "unknown transport"),
        ("exposure", "admin", "no decision for exposure"),
    ],
)
def test_compile_rejects_unknown_catalog_semantics(field, value, message):
    compiler = _compiler_module()
    spec = {
        "lifecycle": "active",
        "transport": "http",
        "agents": {client: "full" for client in CLIENTS},
    }
    if field == "exposure":
        spec["agents"]["claude"] = value
    else:
        spec[field] = value

    with pytest.raises(compiler.CapabilityCompilationError, match=message):
        compiler.compile_capability_matrix(
            {"version": 1, "servers": {"alpha": spec}},
            _shadow_policy(),
        )


def test_load_repo_shadow_policy_and_compile_real_catalog():
    compiler = _compiler_module()
    load_policy = getattr(compiler, "load_shadow_policy", None)
    if load_policy is None:
        pytest.fail("capability compiler is missing load_shadow_policy")

    policy = load_policy(
        REPO_ROOT / "config/mcp/capability-shadow-policy.yaml",
        REPO_ROOT / "schemas/mcp/capability-semantic-contract.schema.json",
    )
    catalog = compiler.load_catalog(REPO_ROOT / "mcp_catalog.yaml")
    result = compiler.compile_capability_matrix(catalog, policy)

    assert [entry["client"] for entry in result["clients"]] == list(CLIENTS)
    assert {
        entry["decision"] for client in result["clients"] for entry in client["servers"]
    } <= {
        "blocked",
        "deferred",
        "direct",
        "facade",
        "omitted",
        "sequenced",
    }
    assert all(
        len(client["servers"]) == len(catalog["servers"])
        for client in result["clients"]
    )


def test_load_shadow_policy_rejects_unknown_fields(tmp_path):
    compiler = _compiler_module()
    invalid_policy = _shadow_policy()
    invalid_policy["activation"] = True
    policy_path = tmp_path / "invalid-policy.yaml"
    policy_path.write_text(json.dumps(invalid_policy), encoding="utf-8")

    with pytest.raises(
        compiler.CapabilityCompilationError,
        match="policy schema validation failed",
    ):
        compiler.load_shadow_policy(
            policy_path,
            REPO_ROOT / "schemas/mcp/capability-semantic-contract.schema.json",
        )


def test_load_shadow_policy_normalizes_duplicate_key_failure(tmp_path):
    compiler = _compiler_module()
    policy_path = tmp_path / "duplicate-policy.yaml"
    policy_path.write_text("mode: shadow\nmode: active\n", encoding="utf-8")

    with pytest.raises(
        compiler.CapabilityCompilationError,
        match="duplicate YAML key 'mode'",
    ):
        compiler.load_shadow_policy(
            policy_path,
            REPO_ROOT / "schemas/mcp/capability-semantic-contract.schema.json",
        )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda policy: policy.update({"activation": True}),
            "unexpected policy fields",
        ),
        (
            lambda policy: policy.update(
                {"schema_version": "mcp-capability-policy.v2"}
            ),
            "schema_version",
        ),
        (
            lambda policy: policy["clients"].update(
                {"chatgpt": policy["clients"]["claude"]}
            ),
            "clients must be exactly",
        ),
        (
            lambda policy: policy["clients"]["claude"]["exposure_decisions"].update(
                {"full": "blocked"}
            ),
            "exposure decisions",
        ),
    ],
)
def test_compile_rejects_policy_that_bypasses_schema_loader(mutation, message):
    compiler = _compiler_module()
    policy = _shadow_policy()
    mutation(policy)

    with pytest.raises(compiler.CapabilityCompilationError, match=message):
        compiler.compile_capability_matrix(
            {
                "version": 1,
                "servers": {
                    "alpha": {
                        "lifecycle": "active",
                        "transport": "http",
                        "agents": {client: "full" for client in CLIENTS},
                    }
                },
            },
            policy,
        )


def test_compile_rejects_unknown_catalog_client_key():
    compiler = _compiler_module()
    agents = {client: "full" for client in CLIENTS}
    agents.update({"chatgpt": "facade", "fable": "full"})

    with pytest.raises(
        compiler.CapabilityCompilationError,
        match="unknown client keys.*fable",
    ):
        compiler.compile_capability_matrix(
            {
                "version": 1,
                "servers": {
                    "alpha": {
                        "lifecycle": "active",
                        "transport": "http",
                        "agents": agents,
                    }
                },
            },
            _shadow_policy(),
        )
