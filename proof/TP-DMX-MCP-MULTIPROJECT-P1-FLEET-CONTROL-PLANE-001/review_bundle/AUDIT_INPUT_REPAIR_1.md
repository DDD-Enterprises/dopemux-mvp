You are performing an independent Tier-1 embedded audit (L3, non-metered route) of a bounded bug-fix commit on top of an already-implemented feature branch. You have real filesystem access to the repo via --add-dir; use it to read files directly and recompute anything you need rather than trusting anything asserted below.

CONTEXT
Repo: DDD-Enterprises/dopemux-mvp, PR #1313 "feat(mcp): implement multiproject P1 fleet control plane", branch codex/mcp-multiproject-p1-fleet-control-plane.
Repo root for this audit: the directory mounted via --add-dir is the worktree at that exact branch/commit.
Prior head 896ef0e7f had CI green but 6 unresolved Copilot review comments on the diff. A repair commit 36620e6a5 (current HEAD of this worktree) was written to address exactly those 6 findings, nothing else. Task packet: task-packets/TP-DMX-MCP-MULTIPROJECT-P1-FLEET-CONTROL-PLANE-001.json (read it for invariants/scope if useful).

THE SIX FINDINGS (verbatim from GitHub Copilot review, PR #1313)
1. src/dopemux/mcp/identity.py:116 -- "resolve_execution_identity compares cwd to stored aliases by exact string; without normalization, callers passing a relative path, a path with symlinks, or different slash semantics can fail to match an otherwise-registered alias. Normalize cwd defensively before matching."
2. src/dopemux/mcp/runtime_state.py:43 -- "canonical_identity_summary emits schema_version dopemux.mcp.resolved-execution-identity.v1 but omits actor_id/client_id/aliases. For VERIFIED identities, that produces a dict that cannot validate against schemas/mcp/resolved-execution-identity.schema.json and may break consumers that treat schema_version as authoritative."
3. src/dopemux/mcp/docker_inspect.py:325 -- "inspect_container_mounts currently records a mount if either Source or Destination is present, which can yield ':/path' or '/path:' entries. Docstring promises '<source>:<destination>'; filter to mounts with both fields to keep evidence stable/meaningful."
4. tests/arch/test_mcp_multiproject_contracts.py:518 -- "test_no_runtime_effect_diff assumes git available; it skips on CalledProcessError but will hard-fail with FileNotFoundError/OSError if git missing. Since this is a governance guard, skipping gracefully when history/tooling absent is better than failing the whole suite."
5. tests/mcp/test_fleet_catalog_v2_runtime.py:212 -- "Test uses subprocess.check_output(['git', ...]) but only skips on CalledProcessError. In minimal CI/unit-test environments without git binary, this will hard-fail with FileNotFoundError instead of skipping as intended."
6. src/dopemux/mcp/fleet_catalog.py:1473 -- "Docstring starts with 4 quotes (\"\"\"\"singleton...), which reads like an accidental extra quote and is easy to misread when grepping or rendering docs. Prefer normal triple-quote docstring and put the quoted words in the content instead."

WHAT THE REPAIR COMMIT (36620e6a5) CLAIMS TO DO, in the repo's own commit message and diff (attached below as a patch, but VERIFY against the live files in the mounted directory rather than trusting the patch text):
- Added `PATH_ALIAS_KINDS` and a new `normalize_path_alias_value()` helper in identity_registry.py (expanduser + resolve), applied both in `_normalize_alias` (the single choke point for every register_project/register_workspace/register_instance/add_alias call) and in identity.py's `resolve_execution_identity` before matching cwd against registered aliases.
- Extended `canonical_identity_summary` in runtime_state.py to also emit actor_id, client_id, aliases.
- Changed `if source or dest:` to `if source and dest:` in docker_inspect.py's inspect_container_mounts.
- Added `except (FileNotFoundError, OSError):` alongside the existing `except subprocess.CalledProcessError:` in both flagged test files.
- Fixed the docstring in fleet_catalog.py's legacy_client_placement.
- Added new regression tests: two in tests/mcp/test_identity_registry_v2.py (relative-cwd and symlinked-cwd resolution against a registered alias), one new file tests/mcp/test_runtime_state_identity_summary.py (asserts canonical_identity_summary's keys equal ResolvedExecutionIdentity.to_schema_dict()'s keys, and validates the summary against schemas/mcp/resolved-execution-identity.schema.json for UNKNOWN/CONFLICTING/VERIFIED cases), one in tests/mcp/test_ownership_v2.py (rejects one-sided mount evidence).

YOUR JOB
1. For each of the 6 findings, independently read the actual current file content at the cited location in the mounted directory and determine: is the finding now actually fixed, partially fixed, or not fixed? Do not just check that code was touched -- verify the logic is correct (e.g. for finding 1, actually trace whether a relative or symlinked cwd would now match a registered absolute alias; check that registration-side normalization and resolution-side normalization use the literal same function so they cannot drift).
2. Check schemas/mcp/resolved-execution-identity.schema.json yourself and confirm canonical_identity_summary's full key set now satisfies it (additionalProperties:false, so extra keys would also be a defect -- check for that too).
3. Run the test suite yourself if you have the ability to execute shell commands in the mounted directory (pytest tests/mcp tests/arch -q). If you cannot execute code, say so explicitly rather than assuming the suite passes.
4. Check for regressions: did this bounded repair touch anything outside the 6 findings' files, or change behavior of anything not called out? (git diff 896ef0e7f 36620e6a5 -- <the touched files>, or read the attached patch and cross-check against live files.)
5. Flag anything you find that is NOT one of the six findings but looks like a real defect in the touched files or their immediate callers -- do not silently expand scope, just report it.

OUTPUT FORMAT (be terse, structured, one block per finding):
FINDING_1_IDENTITY_NORMALIZATION: FIXED | PARTIALLY_FIXED | NOT_FIXED -- one-sentence reason
FINDING_2_SCHEMA_COMPLETENESS: ...
FINDING_3_MOUNT_EVIDENCE: ...
FINDING_4_GIT_MISSING_TEST_1: ...
FINDING_5_GIT_MISSING_TEST_2: ...
FINDING_6_DOCSTRING: ...
TEST_EXECUTION: RAN (paste pass/fail counts) | NOT_RUN (say why)
SCOPE_CREEP: NONE | <list>
NEW_DEFECTS_FOUND: NONE | <list, each with file:line and a one-sentence failure scenario>
OVERALL_VERDICT: PASS | PASS_WITH_RISKS | FAIL
AUDITOR_MODEL: <state your exact model identifier>
INDEPENDENCE_NOTE: confirm you reached these conclusions from the mounted repo state and the schema file, not merely restating the claims in this prompt.

Patch for reference only (verify against live files, do not trust this text as ground truth):
----PATCH-START----
diff --git a/src/dopemux/mcp/docker_inspect.py b/src/dopemux/mcp/docker_inspect.py
index c911fe6f9..7eeb946fc 100644
--- a/src/dopemux/mcp/docker_inspect.py
+++ b/src/dopemux/mcp/docker_inspect.py
@@ -321,7 +321,7 @@ def inspect_container_mounts(
             continue
         source = str(mount.get("Source") or "")
         dest = str(mount.get("Destination") or "")
-        if source or dest:
+        if source and dest:
             out.append(f"{source}:{dest}")
     return sorted(set(out))

diff --git a/src/dopemux/mcp/fleet_catalog.py b/src/dopemux/mcp/fleet_catalog.py
index 35d07d1c3..553766540 100644
--- a/src/dopemux/mcp/fleet_catalog.py
+++ b/src/dopemux/mcp/fleet_catalog.py
@@ -1470,7 +1470,7 @@ def compile_catalog_v2(v1_catalog: dict[str, Any], topology: dict[str, Any]) ->


 def legacy_client_placement(v2_catalog: dict[str, Any], server_id: str) -> str:
-    """"singleton" or "per-worktree" for one server, from the v2 catalog's
+    """Return "singleton" or "per-worktree" for one server, from the v2 catalog's
     ``defaults.per_worktree`` compatibility list -- the same list v1 already
     uses (see test_root_catalog_defaults_are_declared_per_worktree_servers).
     Sharing_class/identity_scope are NOT used here: they encode the R2
diff --git a/src/dopemux/mcp/identity.py b/src/dopemux/mcp/identity.py
index 18c3970ad..09c46d54c 100644
--- a/src/dopemux/mcp/identity.py
+++ b/src/dopemux/mcp/identity.py
@@ -20,15 +20,14 @@ from dataclasses import dataclass, field
 from pathlib import Path
 from typing import Any, Dict, List, Optional

-from dopemux.mcp.identity_registry import IdentityRegistry
+from dopemux.mcp.identity_registry import (
+    PATH_ALIAS_KINDS,
+    IdentityRegistry,
+    normalize_path_alias_value,
+)

 SCHEMA_VERSION = "dopemux.mcp.resolved-execution-identity.v1"

-# Alias kinds treated as filesystem locators for cwd-based resolution. Any
-# other alias kind (origin_url, container_label, mcp_session, ...) is stored
-# as evidence but is never matched against a bare cwd here.
-PATH_ALIAS_KINDS = frozenset({"path", "worktree_root", "project_root", "git_common_dir"})
-

 @dataclass(frozen=True)
 class IdentityClaim:
@@ -110,7 +109,10 @@ def resolve_execution_identity(
     if not actor_id or not actor_id.strip() or not client_id or not client_id.strip():
         return _denied(status="UNKNOWN", actor_id=actor_id, client_id=client_id)

-    cwd_str = str(cwd)
+    # Normalize the same way path-kind aliases are normalized on registration
+    # (identity_registry._normalize_alias) so a relative cwd, a trailing
+    # slash, or a symlinked directory still matches its registered alias.
+    cwd_str = normalize_path_alias_value(str(cwd))
     evidence_aliases: List[Dict[str, str]] = [
         {"kind": "cwd", "value": cwd_str, "role": "EVIDENCE_ONLY"}
     ]
diff --git a/src/dopemux/mcp/identity_registry.py b/src/dopemux/mcp/identity_registry.py
index 6912be96b..a16d9f527 100644
--- a/src/dopemux/mcp/identity_registry.py
+++ b/src/dopemux/mcp/identity_registry.py
@@ -30,6 +30,14 @@ SCHEMA_VERSION = "dopemux.mcp.identity-registry.v1"
 REGISTRY_ENV = "DOPEMUX_MCP_IDENTITY_REGISTRY"
 DEFAULT_RELATIVE = Path(".dopemux/mcp/registry/identity.json")

+# Alias kinds treated as filesystem locators. Values of these kinds are
+# normalized (expanduser + resolve) both on write (_normalize_alias, used by
+# every register_*/add_alias call) and on read (identity.py's resolver
+# normalizes cwd the same way before matching) so a relative path, a
+# trailing slash, or a symlinked directory still matches its registered
+# alias -- see identity.py's ``resolve_execution_identity``.
+PATH_ALIAS_KINDS = frozenset({"path", "worktree_root", "project_root", "git_common_dir"})
+

 class IdentityRegistryError(RuntimeError):
     """Raised when the identity registry cannot be loaded, is corrupt, or a
@@ -61,11 +69,26 @@ def _empty_registry() -> Dict[str, Any]:
     }


+def normalize_path_alias_value(value: str) -> str:
+    """Canonicalize a filesystem-locator alias value: expand ``~`` and
+    resolve ``.``/``..``/symlinks so equivalent paths compare equal. Falls
+    back to the input unchanged if resolution fails (e.g. permission
+    errors) rather than raising -- this is a comparison aid, not validation.
+    """
+
+    try:
+        return str(Path(value).expanduser().resolve())
+    except OSError:
+        return value
+
+
 def _normalize_alias(kind: str, value: str) -> Dict[str, str]:
     if not kind or not kind.strip():
         raise IdentityRegistryError("alias kind must be non-empty")
     if not value or not value.strip():
         raise IdentityRegistryError("alias value must be non-empty")
+    if kind in PATH_ALIAS_KINDS:
+        value = normalize_path_alias_value(value)
     return {"kind": kind, "value": value}


diff --git a/src/dopemux/mcp/runtime_state.py b/src/dopemux/mcp/runtime_state.py
index 04af70912..70b2ac975 100644
--- a/src/dopemux/mcp/runtime_state.py
+++ b/src/dopemux/mcp/runtime_state.py
@@ -22,14 +22,16 @@ PROJECT_MCP_FILENAME = ".mcp.json"


 def canonical_identity_summary(resolved: "Any") -> Dict[str, Any]:
-    """A ``ProjectIdentityView.to_dict()``-shaped read-only summary of a P1
-    ``identity.ResolvedExecutionIdentity``, for inclusion alongside the
-    v1 identity view in diagnostics.
+    """A schema-complete ``schemas/mcp/resolved-execution-identity.schema.json``
+    rendering of a P1 ``identity.ResolvedExecutionIdentity``, for inclusion
+    alongside the v1 identity view in diagnostics.

     Purely additive: nothing in this module calls it, and no existing
     function's output changes. ``resolved`` is typed ``Any`` here to avoid a
     hard import-time dependency from this v1 module onto P1's identity.py --
-    callers pass a ``dopemux.mcp.identity.ResolvedExecutionIdentity``.
+    callers pass a ``dopemux.mcp.identity.ResolvedExecutionIdentity``. Every
+    field the schema declares must be present here, or a consumer trusting
+    ``schema_version`` as authoritative gets an object that fails validation.
     """

     return {
@@ -39,7 +41,10 @@ def canonical_identity_summary(resolved: "Any") -> Dict[str, Any]:
         "project_id": getattr(resolved, "project_id", None),
         "workspace_id": getattr(resolved, "workspace_id", None),
         "instance_id": getattr(resolved, "instance_id", None),
+        "actor_id": getattr(resolved, "actor_id", None),
+        "client_id": getattr(resolved, "client_id", None),
         "registry_generation": getattr(resolved, "registry_generation", None),
+        "aliases": list(getattr(resolved, "aliases", None) or []),
     }


diff --git a/tests/arch/test_mcp_multiproject_contracts.py b/tests/arch/test_mcp_multiproject_contracts.py
index efddcca2b..d3aabf58a 100644
--- a/tests/arch/test_mcp_multiproject_contracts.py
+++ b/tests/arch/test_mcp_multiproject_contracts.py
@@ -521,3 +521,5 @@ def test_no_runtime_effect_diff():
                 pytest.fail(f"Forbidden path mutated in P0's own merge range: {c}")
     except subprocess.CalledProcessError:
         pytest.skip("P0 merge range not available in this checkout")
+    except (FileNotFoundError, OSError):
+        pytest.skip("git binary not available in this environment")
diff --git a/tests/mcp/test_fleet_catalog_v2_runtime.py b/tests/mcp/test_fleet_catalog_v2_runtime.py
index 464068ec8..8a26b20ef 100644
--- a/tests/mcp/test_fleet_catalog_v2_runtime.py
+++ b/tests/mcp/test_fleet_catalog_v2_runtime.py
@@ -210,6 +210,8 @@ def test_live_catalog_files_are_untouched_by_this_packet():
         ).decode()
     except subprocess.CalledProcessError:
         pytest.skip("no trusted base ref available for git diff")
+    except (FileNotFoundError, OSError):
+        pytest.skip("git binary not available in this environment")
     changed = set(diff.splitlines())
     assert "mcp_catalog.yaml" not in changed
     assert "src/dopemux/mcp/default_catalog.yaml" not in changed
diff --git a/tests/mcp/test_identity_registry_v2.py b/tests/mcp/test_identity_registry_v2.py
index 7d35ec014..04dca8f4e 100644
--- a/tests/mcp/test_identity_registry_v2.py
+++ b/tests/mcp/test_identity_registry_v2.py
@@ -163,6 +163,50 @@ def test_full_chain_alias_resolves_verified(tmp_path: Path):
     assert resolved.registry_generation == reg.generation


+def test_relative_cwd_resolves_registered_absolute_alias(tmp_path: Path, monkeypatch):
+    real_dir = tmp_path / "repo"
+    real_dir.mkdir()
+    reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
+    pid = reg.register_project(aliases=[])
+    wid = reg.register_workspace(project_id=pid, aliases=[])
+    iid = reg.register_instance(
+        project_id=pid, workspace_id=wid, aliases=[{"kind": "worktree_root", "value": str(real_dir)}]
+    )
+
+    monkeypatch.chdir(tmp_path)
+    resolved = resolve_execution_identity(
+        cwd=Path("repo"), registry=reg, actor_id="operator", client_id="claude"
+    )
+    _validate(resolved)
+    assert resolved.resolution_status == "VERIFIED"
+    assert resolved.project_id == pid
+    assert resolved.workspace_id == wid
+    assert resolved.instance_id == iid
+
+
+def test_symlinked_cwd_resolves_registered_real_path_alias(tmp_path: Path):
+    real_dir = tmp_path / "real-repo"
+    real_dir.mkdir()
+    symlink_dir = tmp_path / "repo-link"
+    symlink_dir.symlink_to(real_dir)
+
+    reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
+    pid = reg.register_project(aliases=[])
+    wid = reg.register_workspace(project_id=pid, aliases=[])
+    iid = reg.register_instance(
+        project_id=pid, workspace_id=wid, aliases=[{"kind": "worktree_root", "value": str(real_dir)}]
+    )
+
+    resolved = resolve_execution_identity(
+        cwd=symlink_dir, registry=reg, actor_id="operator", client_id="claude"
+    )
+    _validate(resolved)
+    assert resolved.resolution_status == "VERIFIED"
+    assert resolved.project_id == pid
+    assert resolved.workspace_id == wid
+    assert resolved.instance_id == iid
+
+
 def test_fx_ident_01_identical_basenames_distinct_projects(tmp_path: Path):
     """FX-IDENT-01: identical directory basenames across two projects must
     resolve to distinct registry project_id/endpoints; no alias-based
diff --git a/tests/mcp/test_ownership_v2.py b/tests/mcp/test_ownership_v2.py
index 326b97bcd..15d1a4535 100644
--- a/tests/mcp/test_ownership_v2.py
+++ b/tests/mcp/test_ownership_v2.py
@@ -234,6 +234,23 @@ def test_inspect_container_mounts_never_raises_on_malformed_json():
     assert inspect_container_mounts("abc123", runner=runner) == []


+def test_inspect_container_mounts_rejects_one_sided_evidence():
+    def runner(*args, **kwargs):
+        return _fake_completed(
+            json.dumps(
+                [
+                    {"Source": "", "Destination": "/data"},
+                    {"Source": "/var/lib/dopemux/conport", "Destination": ""},
+                    {"Source": "/var/lib/dopemux/conport", "Destination": "/data"},
+                ]
+            )
+        )
+
+    mounts = inspect_container_mounts("abc123", runner=runner)
+    assert mounts == ["/var/lib/dopemux/conport:/data"]
+    assert not any(m.startswith(":") or m.endswith(":") for m in mounts)
+
+
 def test_inspect_container_mounts_never_invokes_mutating_docker_commands():
     seen_args: list = []

diff --git a/tests/mcp/test_runtime_state_identity_summary.py b/tests/mcp/test_runtime_state_identity_summary.py
new file mode 100644
index 000000000..e30cf52fc
--- /dev/null
+++ b/tests/mcp/test_runtime_state_identity_summary.py
@@ -0,0 +1,60 @@
+"""canonical_identity_summary must stay schema-complete for
+schemas/mcp/resolved-execution-identity.schema.json -- a consumer trusting
+its schema_version as authoritative must be able to validate the result.
+"""
+
+from __future__ import annotations
+
+import json
+from pathlib import Path
+
+import jsonschema
+import pytest
+
+from dopemux.mcp.identity import IdentityClaim, resolve_execution_identity
+from dopemux.mcp.identity_registry import IdentityRegistry
+from dopemux.mcp.runtime_state import canonical_identity_summary
+
+REPO_ROOT = Path(__file__).resolve().parents[2]
+IDENTITY_SCHEMA = REPO_ROOT / "schemas/mcp/resolved-execution-identity.schema.json"
+
+
+def _schema() -> dict:
+    return json.loads(IDENTITY_SCHEMA.read_text())
+
+
+def test_summary_keys_are_superset_of_schema_dict_keys(tmp_path: Path):
+    reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
+    resolved = resolve_execution_identity(
+        cwd=Path("/nowhere"), registry=reg, actor_id="operator", client_id="claude"
+    )
+    assert set(canonical_identity_summary(resolved).keys()) == set(resolved.to_schema_dict().keys())
+
+
+@pytest.mark.parametrize(
+    "claim",
+    [
+        None,
+        IdentityClaim(project_id="prj_x", workspace_id="ws_x", instance_id="inst_x"),
+    ],
+)
+def test_summary_validates_against_schema_for_unknown_and_conflicting(tmp_path: Path, claim):
+    reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
+    resolved = resolve_execution_identity(
+        cwd=Path("/nowhere"), registry=reg, actor_id="operator", client_id="claude", claim=claim
+    )
+    jsonschema.validate(canonical_identity_summary(resolved), _schema())
+
+
+def test_summary_validates_against_schema_for_verified(tmp_path: Path):
+    reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
+    pid = reg.register_project(aliases=[])
+    wid = reg.register_workspace(project_id=pid, aliases=[])
+    reg.register_instance(
+        project_id=pid, workspace_id=wid, aliases=[{"kind": "worktree_root", "value": "/repo/a"}]
+    )
+    resolved = resolve_execution_identity(
+        cwd=Path("/repo/a"), registry=reg, actor_id="operator", client_id="claude"
+    )
+    assert resolved.resolution_status == "VERIFIED"
+    jsonschema.validate(canonical_identity_summary(resolved), _schema())
----PATCH-END----
