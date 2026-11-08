"""ConPort tenant resolution and provisioning (design D5, Task 4).

Every database call goes through a recording fake ``psql`` (or a recording
``cmd_runner`` that answers the psql argv); no test ever reaches a real
docker or Postgres. Passwords here are obviously fake values.
"""

from __future__ import annotations

import ast
import json
import re
import stat
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pytest
from click.testing import CliRunner

from dopemux.mcp import conport_tenant as ct
from dopemux.mcp import docker_runtime as dr
from dopemux.mcp.runtime_state import resolve_identity_view

FAKE_ENVRC_PASSWORD = "fake-envrc-password-not-real"
FAKE_PROVISIONED_PASSWORD = "f00d" * 12  # 48 hex chars, like token_hex(24)

SEVEN_TABLES = (
    "custom_data",
    "decisions",
    "entity_relationships",
    "progress_entries",
    "search_cache",
    "session_snapshots",
    "workspace_contexts",
)


# --- fakes ------------------------------------------------------------------


def _out(text: str, rc: int = 0, err: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(["psql"], rc, text, err)


def _aligned(value: str) -> str:
    """What `psql` (aligned, with header) prints for a one-column, one-row SELECT."""
    return f" ?column? \n----------\n {value}\n(1 row)\n\n"


class FakePsql:
    """Recording ``(database, sql)`` runner with canned answers by SQL marker."""

    def __init__(
        self,
        *,
        legacy_count: int = 0,
        tables: Sequence[str] = SEVEN_TABLES,
        role_exists: bool = False,
        db_exists: bool = False,
        schema_present: bool = False,
        rc: int = 0,
        raises: Optional[BaseException] = None,
        fail_on: Optional[str] = None,
        existing: Sequence[str] = (),
        already_applied: Sequence[str] = (),
        probe_rc: int = 0,
        probe_answer: Optional[str] = None,
    ) -> None:
        self.calls: List[Tuple[str, str]] = []
        self.fail_on = fail_on
        # Gate-style objects (``view:pattern_statistics``) a DPMX_APPLIED probe finds.
        self.existing = set(existing)
        # Migrations already committed: resending one fails like 001/002's CREATE VIEW.
        self.already_applied = set(already_applied)
        self.probe_rc = probe_rc
        self.probe_answer = probe_answer
        self.legacy_count = legacy_count
        self.tables = tables
        self.role_exists = role_exists
        self.db_exists = db_exists
        self.schema_present = schema_present
        self.rc = rc
        self.raises = raises

    def __call__(self, database: str, sql: str) -> subprocess.CompletedProcess:
        self.calls.append((database, sql))
        if self.raises is not None:
            raise self.raises
        if self.rc:
            return _out("", self.rc, "psql: error: connection refused")
        if self.fail_on and self.fail_on in sql:
            return _out("", 3, "ERROR:  simulated failure (killed mid-provisioning)")
        if "DPMX_APPLIED=" in sql:
            return self._applied(sql)
        if (
            self.already_applied
            and (_label(sql) or "").removeprefix("migration:") in self.already_applied
        ):
            return _out("", 3, 'ERROR:  relation "replayed_object" already exists')
        if "DPMX_TABLES=" in sql:
            return _out(_aligned("DPMX_TABLES=" + ",".join(self.tables)))
        if "DPMX_COUNT=" in sql:
            return _out(_aligned(f"DPMX_COUNT={self.legacy_count}"))
        if "DPMX_ROLE=" in sql:
            return _out(_aligned(f"DPMX_ROLE={1 if self.role_exists else 0}"))
        if "DPMX_DB=" in sql:
            return _out(_aligned(f"DPMX_DB={1 if self.db_exists else 0}"))
        if "DPMX_PRESENT=" in sql:
            return _out(
                _aligned(f"DPMX_PRESENT={'true' if self.schema_present else 'false'}")
            )
        if "DPMX_VERIFY=" in sql:
            return _out(_aligned("DPMX_VERIFY=12,0,0,1"))
        return _out("")

    def _applied(self, sql: str) -> subprocess.CompletedProcess:
        if self.probe_rc:
            return _out("", self.probe_rc, "ERROR:  simulated probe failure")
        if self.probe_answer is not None:
            return _out(self.probe_answer)
        asked = _probed_object(sql)
        if asked is None:
            return _out("")  # an unrecognised probe gets no marker
        known = {  # view:x -> x, column:t:c -> t.c
            obj.split(":", 1)[1].replace(":", ".") for obj in self.existing
        }
        found = asked in known
        return _out(_aligned(f"DPMX_APPLIED={'true' if found else 'false'}"))

    def steps(self) -> List[str]:
        """Applied probes (``probe:<object>``) and migration runs, in issue order."""
        out: List[str] = []
        for _db, sql in self.calls:
            if "DPMX_APPLIED=" in sql:
                out.append(f"probe:{_probed_object(sql)}")
            elif (_label(sql) or "").startswith("migration:"):
                out.append(str(_label(sql)))
        return out

    def migrations(self) -> List[str]:
        """Migration files whose SQL was sent, in issue order."""
        return [
            step.removeprefix("migration:")
            for step in self.steps()
            if step.startswith("migration:")
        ]


def _probed_object(sql: str) -> Optional[str]:
    """The relation (``pattern_statistics``) or column (``custom_data.write_principal``) asked about."""
    column = re.search(
        r"table_schema\s*=\s*'public'\s+AND\s+table_name\s*=\s*'(\w+)'"
        r"\s+AND\s+column_name\s*=\s*'(\w+)'",
        sql,
    )
    if column:
        return f"{column.group(1)}.{column.group(2)}"
    relation = re.search(r"to_regclass\('public\.(\w+)'\)", sql)
    return relation.group(1) if relation else None


def _label(sql: str) -> Optional[str]:
    """Name of a mutating statement, independent of the query wording."""
    if "CREATE TABLE workspace_contexts" in sql:
        return "schema"
    for m in sorted(ct.migrations_dir().glob("0*.sql")):
        if "rollback" not in m.name and m.read_text() in sql:
            return f"migration:{m.stem}"
    for marker, name in (
        ("CREATE ROLE", "create_role"),
        ("ALTER ROLE", "alter_role"),
        ("CREATE DATABASE", "create_database"),
        ("REVOKE CONNECT", "revoke"),
        ("CREATE EXTENSION", "extension"),
        ("INSERT INTO workspaces", "workspace_rows"),
    ):
        if marker in sql:
            return name
    return None


def _labels(calls: Sequence[Tuple[str, str]]) -> List[str]:
    """Mutating statements in issue order; consecutive extension calls squashed."""
    out: List[str] = []
    for _db, sql in calls:
        name = _label(sql)
        if name and not (name == "extension" and out and out[-1] == "extension"):
            out.append(name)
    return out


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _repo(tmp_path: Path, name: str = "Tenant-Proj") -> Path:
    repo = tmp_path / name
    repo.mkdir()
    _git(repo, "init", "-q")
    return repo.resolve()


@pytest.fixture(autouse=True)
def _isolated(tmp_path: Path, monkeypatch):
    """Locks, registries and the default secrets dir all live under tmp_path."""
    monkeypatch.setenv(
        "DOPEMUX_MCP_RUNTIME_REGISTRY", str(tmp_path / "rt" / "instances.json")
    )
    monkeypatch.setenv(
        "DOPEMUX_MCP_PORT_LEASE_REGISTRY", str(tmp_path / "rt" / "port-leases.json")
    )


def _identity(repo: Path):
    identity = resolve_identity_view(repo)
    assert identity.project_id
    return identity


def _envrc_creds() -> Dict[str, str]:
    return {
        "CONPORT_DB_NAME": "conport_fake_tenant",
        "CONPORT_DB_USER": "conport_fake_tenant",
        "CONPORT_DB_PASSWORD": FAKE_ENVRC_PASSWORD,
    }


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


# --- Step 1: resolution order ----------------------------------------------------


def test_resolve_tenant_prefers_secrets_file(tmp_path: Path):
    identity = _identity(_repo(tmp_path))
    root = tmp_path / "secrets"
    path = ct.secrets_path(identity.project_id, secrets_root=root)
    ct.write_secrets(
        path,
        ct.TenantCredentials(
            "conport_from_file", "conport_from_file", "fake-file-pw", "secrets"
        ),
    )
    psql = FakePsql(legacy_count=7)

    creds = ct.resolve_tenant(
        identity, envrc_values=_envrc_creds(), psql=psql, secrets_root=root
    )

    assert creds.source == "secrets"
    assert (creds.db_name, creds.db_user, creds.db_password) == (
        "conport_from_file",
        "conport_from_file",
        "fake-file-pw",
    )
    assert psql.calls == []


def test_resolve_tenant_adopts_envrc_and_copies_to_secrets(tmp_path: Path):
    identity = _identity(_repo(tmp_path))
    root = tmp_path / "secrets"
    psql = FakePsql()

    creds = ct.resolve_tenant(
        identity, envrc_values=_envrc_creds(), psql=psql, secrets_root=root
    )

    assert creds.source == "legacy_envrc"
    assert creds.db_password == FAKE_ENVRC_PASSWORD
    path = ct.secrets_path(identity.project_id, secrets_root=root)
    assert _mode(path) == 0o600
    assert _mode(path.parent) == 0o700
    copied = ct.load_secrets(path)
    assert (copied.db_name, copied.db_user, copied.db_password) == (
        "conport_fake_tenant",
        "conport_fake_tenant",
        FAKE_ENVRC_PASSWORD,
    )
    assert copied.source == "secrets"
    assert psql.calls == []
    # Second resolution reads the copy, not the envrc.
    again = ct.resolve_tenant(identity, envrc_values={}, psql=psql, secrets_root=root)
    assert again.source == "secrets" and again.db_password == FAKE_ENVRC_PASSWORD


def test_resolve_tenant_legacy_shared_when_rows_exist(tmp_path: Path):
    identity = _identity(_repo(tmp_path))
    root = tmp_path / "secrets"
    psql = FakePsql(legacy_count=3)

    creds = ct.resolve_tenant(identity, envrc_values={}, psql=psql, secrets_root=root)

    assert creds.source == "legacy_shared"
    assert (creds.db_name, creds.db_user, creds.db_password) == (
        "dopemux_knowledge_graph",
        "",
        "",
    )
    assert ct.tenant_compose_env(creds) == {}
    assert _labels(psql.calls) == []
    assert not any("CREATE " in sql for _db, sql in psql.calls)
    assert all(db == "dopemux_knowledge_graph" for db, _sql in psql.calls)
    assert not ct.secrets_path(identity.project_id, secrets_root=root).exists()


def test_resolve_tenant_provisions_when_no_history(tmp_path: Path, monkeypatch):
    identity = _identity(_repo(tmp_path))
    root = tmp_path / "secrets"
    psql = FakePsql(legacy_count=0)
    monkeypatch.setattr(ct.secrets, "token_hex", lambda n: FAKE_PROVISIONED_PASSWORD)

    creds = ct.resolve_tenant(identity, envrc_values={}, psql=psql, secrets_root=root)

    assert creds.source == "provisioned"
    assert creds.gate_pending is True
    assert creds.db_password == FAKE_PROVISIONED_PASSWORD
    assert creds.db_name == creds.db_user
    assert re.fullmatch(r"conport_[a-z][a-z0-9_]{0,40}", creds.db_name)
    expected_migrations = [f"migration:{m}" for m in ct.PROVISION_MIGRATIONS]
    assert _labels(psql.calls) == [
        "create_role",
        "create_database",
        "revoke",
        "extension",
        "schema",
        *expected_migrations,
        "workspace_rows",
    ]
    # The schema and every migration run AS the tenant role, never as the superuser.
    for _db, sql in psql.calls:
        if _label(sql) in {"schema", "workspace_rows"} or (
            _label(sql) or ""
        ).startswith("migration:"):
            assert sql.lstrip().startswith(f"SET ROLE {creds.db_user};"), sql[:80]
    # The seed block of the sealed schema never reaches the database.
    schema_sql = next(
        sql for _db, sql in psql.calls if "CREATE TABLE workspace_contexts" in sql
    )
    assert "INSERT INTO" not in schema_sql
    assert (
        "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO dopemux_age"
        in schema_sql
    )
    # Workspace registration uses the project root (path form).
    ws_sql = next(sql for _db, sql in psql.calls if _label(sql) == "workspace_rows")
    assert str(identity.project_root) in ws_sql
    # Secrets were written, 0600, and match what was provisioned.
    path = ct.secrets_path(identity.project_id, secrets_root=root)
    assert _mode(path) == 0o600
    stored = ct.load_secrets(path)
    assert (stored.db_name, stored.db_password) == (
        creds.db_name,
        FAKE_PROVISIONED_PASSWORD,
    )
    # The gate is still owed (it needs this instance's conport container).
    assert (
        ct.pending_gate_credentials(identity.project_id, secrets_root=root) is not None
    )


def test_provision_migrations_match_the_sealed_gate_required_set():
    """The gate verifies REQUIRED_MIGRATIONS; psql-then-adopt must apply all of them."""
    gate = (ct.migrations_dir() / "conport_migration_gate.py").read_text()
    block = re.search(r"REQUIRED_MIGRATIONS = \{(.*?)\}", gate, re.S).group(1)
    required = sorted(Path(name).stem for name in re.findall(r'"([^"]+\.sql)"', block))
    assert sorted(ct.PROVISION_MIGRATIONS) == required


def _gate_schema_checks() -> Dict[int, Tuple[str, ...]]:
    """``migration_schema_errors``' per-version objects, read from the sealed gate's source."""
    tree = ast.parse((ct.migrations_dir() / "conport_migration_gate.py").read_text())
    func = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "migration_schema_errors"
    )
    checks = next(
        node
        for node in ast.walk(func)
        if isinstance(node, ast.AnnAssign)
        and getattr(node.target, "id", "") == "checks"
    )
    return ast.literal_eval(checks.value)


#: Where a migration creates a gate-style object (first match in its SQL).
_CREATES = {
    "table": r"CREATE TABLE (?:IF NOT EXISTS )?{0}\b",
    "view": r"CREATE (?:OR REPLACE )?VIEW {0}\b",
    "index": r"INDEX (?:IF NOT EXISTS )?{0}\b",
    "column": r"ALTER TABLE {0}\s+ADD COLUMN IF NOT EXISTS {1}\b",
}


def _created_at(sql: str, obj: str) -> int:
    kind, *parts = obj.split(":")
    match = re.search(_CREATES[kind].format(*map(re.escape, parts)), sql)
    assert match, f"{obj} is not created by this migration"
    return match.start()


def test_applied_probes_are_the_gates_evidence_and_each_migrations_last_object():
    """Each probe is a gate-checked object, the last object its single transaction creates."""
    checks = _gate_schema_checks()
    assert set(ct.MIGRATION_APPLIED_PROBES) <= set(ct.PROVISION_MIGRATIONS)
    for name, probe in ct.MIGRATION_APPLIED_PROBES.items():
        gate_objects = checks[int(name[:3])]
        assert ":".join(probe) in gate_objects, name
        sql = (ct.migrations_dir() / f"{name}.sql").read_text()
        order = sorted(gate_objects, key=lambda obj: _created_at(sql, obj))
        assert order[-1] == ":".join(probe), (name, order)
        # One BEGIN/COMMIT holds it, and nothing is created or altered after it.
        begins = [m.start() for m in re.finditer(r"^BEGIN;", sql, re.M)]
        commits = [m.start() for m in re.finditer(r"^COMMIT;", sql, re.M)]
        assert len(begins) == len(commits) == 1, name
        at = _created_at(sql, ":".join(probe))
        assert begins[0] < at < commits[0], name
        after = sql[at + 1 : commits[0]]
        assert not re.search(r"^\s*(?:CREATE|ALTER|DROP)\b", after, re.M | re.I), name


#: Statements a replay leaves as they were, matched on the statement with
#: comments and DO blocks removed, parenthesised parts collapsed to "_" and
#: whitespace collapsed. Anything else makes a migration not re-runnable.
_RERUNNABLE = tuple(
    re.compile(pattern, re.I)
    for pattern in (
        r"BEGIN|COMMIT",
        r"CREATE TABLE IF NOT EXISTS .*",
        r"CREATE (?:UNIQUE )?INDEX IF NOT EXISTS .*",
        r"CREATE OR REPLACE (?:VIEW|FUNCTION|TRIGGER) .*",
        r"DROP (?:INDEX|VIEW|TABLE|TRIGGER|FUNCTION) IF EXISTS [^,]*",
        r"ALTER TABLE \S+ (?:ADD COLUMN IF NOT EXISTS|ALTER COLUMN \w+ SET NOT NULL)[^,]*",
        r"INSERT INTO .* ON CONFLICT .* DO (?:NOTHING|UPDATE .*)",
        r"UPDATE (\w+) SET (\w+) = NULL WHERE \2 IS NULL",
        r"ANALYZE [^,]*",
        r"COMMENT ON .*",
    )
)
_DO_BLOCK = re.compile(r"\bDO\s+(\$\w*\$)(.*?)\1\s*;", re.S | re.I)
_SIDE_EFFECT = re.compile(
    r"^\s*(?:CREATE|ALTER|DROP|INSERT|UPDATE|DELETE|TRUNCATE|GRANT|REVOKE|EXECUTE)\b",
    re.M | re.I,
)


def _not_rerunnable(sql: str) -> List[str]:
    """Statements of a migration a replay could fail on or change; empty when re-runnable.

    A DO block counts as guarded only while it has no side effect (checks and
    RAISE only); one that writes anything is reported for a human to classify.
    """
    sql = re.sub(r"--[^\n]*", "", sql)
    bad = [
        "DO block: " + " ".join(block.group(2).split())[:60]
        for block in _DO_BLOCK.finditer(sql)
        if _SIDE_EFFECT.search(block.group(2))
    ]
    for statement in _DO_BLOCK.sub("", sql).split(";"):
        flat = " ".join(statement.split())
        while re.search(r"\([^()]*\)", flat):
            flat = re.sub(r"\([^()]*\)", " _ ", flat)
        flat = " ".join(flat.split())
        if flat and not any(p.fullmatch(flat) for p in _RERUNNABLE):
            bad.append(flat[:80])
    return bad


@pytest.mark.parametrize(
    "probe, asked",
    [
        (("view", "pattern_statistics"), "pattern_statistics"),
        (("index", "idx_progress_instance"), "idx_progress_instance"),
        (("table", "users"), "users"),
        (("column", "custom_data", "write_principal"), "custom_data.write_principal"),
        (("trigger", "update_patterns_modtime"), None),
    ],
)
def test_applied_probe_sql_covers_the_gate_kinds(probe, asked):
    sql = ct._applied_probe_sql(probe)
    if asked is None:  # a kind the gate does not check: no SQL, so the probe refuses
        assert sql is None
        return
    assert sql.startswith("SELECT 'DPMX_APPLIED=' || (") and sql.endswith(")::text;\n")
    assert _probed_object(sql) == asked


def test_only_migrations_that_cannot_be_rerun_are_probed():
    """A migration made only of idempotent statements is replayed; any other one is probed.

    A static scan of the sealed SQL: an edit that adds, say, a bare CREATE VIEW
    to 003 trips this until that migration gets a probe.
    """
    for name in ct.PROVISION_MIGRATIONS:
        bad = _not_rerunnable((ct.migrations_dir() / f"{name}.sql").read_text())
        assert bool(bad) == (name in ct.MIGRATION_APPLIED_PROBES), (name, bad)
    assert set(ct.MIGRATION_APPLIED_PROBES) == {
        "001_enhanced_decision_model",
        "002_decision_patterns_table",
    }


def test_provision_refuses_existing_role_without_secrets(tmp_path: Path):
    identity = _identity(_repo(tmp_path))
    root = tmp_path / "secrets"
    psql = FakePsql(legacy_count=0, role_exists=True)

    with pytest.raises(ct.TenantError) as excinfo:
        ct.resolve_tenant(identity, envrc_values={}, psql=psql, secrets_root=root)

    assert excinfo.value.code == "ROLE_EXISTS_WITHOUT_SECRETS"
    assert _labels(psql.calls) == []
    assert not any("ALTER ROLE" in sql or "PASSWORD" in sql for _db, sql in psql.calls)
    path = ct.secrets_path(identity.project_id, secrets_root=root)
    assert not path.exists()
    assert str(path) in str(excinfo.value)


def test_provision_database_refuses_existing_role_directly():
    psql = FakePsql(role_exists=True)
    with pytest.raises(ct.TenantError) as excinfo:
        ct.provision_database(
            slug="fake_tenant",
            workspace_id="/tmp/fake",
            password=FAKE_PROVISIONED_PASSWORD,
            psql=psql,
            schema_path=ct.schema_path(),
            migrations_dir=ct.migrations_dir(),
        )
    assert excinfo.value.code == "ROLE_EXISTS_WITHOUT_SECRETS"
    assert _labels(psql.calls) == []


@pytest.mark.parametrize(
    "psql",
    [FakePsql(rc=2), FakePsql(raises=OSError("docker: not found"))],
    ids=["nonzero-exit", "exception"],
)
def test_resolve_tenant_unknown_history_fails_closed(tmp_path: Path, psql):
    # final review R2: an unknown row count is no longer read as "has history"
    identity = _identity(_repo(tmp_path))
    root = tmp_path / "secrets"

    for provision in (True, False):  # a start and the doctor both refuse to guess
        with pytest.raises(ct.TenantError) as excinfo:
            ct.resolve_tenant(
                identity,
                envrc_values={},
                psql=psql,
                secrets_root=root,
                provision=provision,
            )
        assert excinfo.value.code == "CONPORT_TENANT_UNKNOWN_HISTORY"
        assert "nothing was changed" in excinfo.value.detail
        assert "postgres" in excinfo.value.detail.lower()
    assert _labels(psql.calls) == []
    assert not ct.secrets_path(identity.project_id, secrets_root=root).exists()


def test_count_legacy_rows_is_zero_when_shared_tables_absent():
    psql = FakePsql(tables=())
    assert ct.count_legacy_rows(["/x/proj", "proj"], psql=psql) == 0
    assert not any("DPMX_COUNT=" in sql for _db, sql in psql.calls)


def test_count_legacy_rows_unions_the_seven_tables_with_escaped_aliases():
    psql = FakePsql(legacy_count=4)
    assert ct.count_legacy_rows(["/x/o'brien", "o'brien"], psql=psql) == 4
    sql = next(sql for _db, sql in psql.calls if "DPMX_COUNT=" in sql)
    for table in SEVEN_TABLES:
        assert f"FROM public.{table} WHERE workspace_id IN" in sql
    assert "'/x/o''brien'" in sql and "'o''brien'" in sql
    assert sql.count("UNION ALL") == 6


def test_legacy_aliases_include_worktrees(tmp_path: Path):
    repo = _repo(tmp_path, "aliasproj")
    _git(
        repo,
        "-c",
        "user.email=t@example.invalid",
        "-c",
        "user.name=t",
        "commit",
        "--allow-empty",
        "-q",
        "-m",
        "init",
    )
    linked = tmp_path / "linked-wt"
    _git(repo, "worktree", "add", "-q", str(linked))

    aliases = ct.legacy_workspace_aliases(_identity(repo))

    assert aliases[0] == str(repo)
    assert "aliasproj" in aliases
    assert str(linked.resolve()) in [
        str(Path(a).resolve()) for a in aliases if "/" in a
    ]
    assert len(aliases) == len(set(aliases))


def test_secrets_never_in_mcp_env():
    env = {
        "CONPORT_DB_NAME": "conport_fake_tenant",
        "CONPORT_DB_USER": "conport_fake_tenant",
        "CONPORT_DB_PASSWORD": FAKE_ENVRC_PASSWORD,
        "CONPORT_HTTP_PORT": 3040,
    }
    text = dr.generate_mcp_env(env)
    assert "PASSWORD" not in text
    assert FAKE_ENVRC_PASSWORD not in text
    assert "CONPORT_HTTP_PORT=3040" in text


def test_tenant_credentials_repr_hides_password():
    creds = ct.TenantCredentials(
        "conport_x", "conport_x", FAKE_ENVRC_PASSWORD, "secrets"
    )
    assert FAKE_ENVRC_PASSWORD not in repr(creds)


def test_write_secrets_is_atomic_0600_and_round_trips_odd_values(tmp_path: Path):
    path = tmp_path / "p" / "secrets.env"
    odd = "fake pw with 'quote' #hash $dollar"
    ct.write_secrets(
        path, ct.TenantCredentials("conport_x", "conport_x", odd, "secrets")
    )
    assert _mode(path) == 0o600 and _mode(path.parent) == 0o700
    assert [p.name for p in path.parent.iterdir()] == ["secrets.env"]
    assert ct.load_secrets(path).db_password == odd
    text = path.read_text()
    assert "export" not in text
    assert set(re.findall(r"^([A-Z_]+)=", text, re.M)) == {
        "CONPORT_DB_NAME",
        "CONPORT_DB_USER",
        "CONPORT_DB_PASSWORD",
    }


def test_incomplete_secrets_file_fails_closed(tmp_path: Path):
    identity = _identity(_repo(tmp_path))
    root = tmp_path / "secrets"
    path = ct.secrets_path(identity.project_id, secrets_root=root)
    path.parent.mkdir(parents=True)
    path.write_text("CONPORT_DB_NAME=conport_x\n")
    psql = FakePsql()
    with pytest.raises(ct.TenantError) as excinfo:
        ct.resolve_tenant(identity, envrc_values={}, psql=psql, secrets_root=root)
    assert excinfo.value.code == "CONPORT_TENANT_SECRETS_INVALID"
    assert str(path) in str(excinfo.value)
    assert "restore" in str(excinfo.value) and "operator" in str(excinfo.value)
    assert "delete" not in str(excinfo.value)
    assert psql.calls == []


def test_doctor_mode_never_writes_or_provisions(tmp_path: Path):
    identity = _identity(_repo(tmp_path))
    root = tmp_path / "secrets"
    psql = FakePsql(legacy_count=0)
    assert (
        ct.resolve_tenant(
            identity, envrc_values={}, psql=psql, secrets_root=root, provision=False
        )
        is None
    )
    assert _labels(psql.calls) == []
    adopted = ct.resolve_tenant(
        identity,
        envrc_values=_envrc_creds(),
        psql=psql,
        secrets_root=root,
        provision=False,
    )
    assert adopted.source == "legacy_envrc"
    assert not ct.secrets_path(identity.project_id, secrets_root=root).exists()


def test_main_checkout_envrc_is_adopted_from_a_linked_worktree(tmp_path: Path):
    """A worktree without its own envrc must not provision past a hand-made tenant."""
    repo = _repo(tmp_path, "handmade")
    _git(
        repo,
        "-c",
        "user.email=t@example.invalid",
        "-c",
        "user.name=t",
        "commit",
        "--allow-empty",
        "-q",
        "-m",
        "init",
    )
    lines = [f"export {k}={v}" for k, v in _envrc_creds().items()]
    (repo / ".envrc.dopemux-mcp").write_text("\n".join(lines) + "\n")
    linked = tmp_path / "wt"
    _git(repo, "worktree", "add", "-q", str(linked))
    root = tmp_path / "secrets"
    psql = FakePsql(legacy_count=0)

    creds = ct.resolve_tenant(
        resolve_identity_view(linked), envrc_values={}, psql=psql, secrets_root=root
    )

    assert creds.source == "legacy_envrc"
    assert creds.db_name == "conport_fake_tenant"
    assert psql.calls == []


def test_default_psql_runner_feeds_sql_on_stdin_never_argv():
    seen: Dict[str, Any] = {}

    def runner(cmd, **kwargs):
        seen["cmd"] = list(cmd)
        seen["input"] = kwargs.get("input")
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    psql = ct.default_psql_runner(runner=runner)
    result = psql("conport_x", "CREATE ROLE conport_x LOGIN PASSWORD 'fake';")

    assert seen["cmd"] == [
        "docker",
        "exec",
        "-i",
        "dopemux-postgres-age",
        "psql",
        "-v",
        "ON_ERROR_STOP=1",
        "-U",
        "dopemux_age",
        "-d",
        "conport_x",
    ]
    assert seen["input"].startswith("CREATE ROLE")
    assert result.returncode == 0 and result.stdout == "ok"


def test_default_psql_runner_refuses_real_docker_under_pytest():
    result = ct.default_psql_runner()("dopemux_knowledge_graph", "SELECT 1;")
    assert result.returncode != 0


# --- init: tenant + pre-build, never printing the password ---------------------


def _init_catalog() -> Dict[str, Any]:
    return {
        "version": 1,
        "defaults": {"per_worktree": ["conport", "dope-memory"]},
        "servers": {
            "conport": {
                "scope": "per-worktree",
                "transport": "sse",
                "url_template": "http://localhost:${CONPORT_MCP_PORT:-3005}/sse",
                "port_var": "CONPORT_MCP_PORT",
                "default_port_base": 3005,
                "extra_port_vars": [
                    {"var": "CONPORT_HTTP_PORT", "base": 3004},
                    {"var": "CONPORT_INFO_PORT", "base": 4004},
                ],
            },
            "dope-memory": {
                "scope": "per-worktree",
                "transport": "http",
                "url_template": "http://localhost:${DOPE_MEMORY_PORT:-3020}/mcp",
                "port_var": "DOPE_MEMORY_PORT",
                "default_port_base": 3020,
            },
        },
    }


class FakeCmdRunner:
    """subprocess.run stand-in: answers psql (via FakePsql) and docker calls."""

    def __init__(
        self, psql: FakePsql, *, image_present: bool = False, build_rc: int = 0
    ):
        self.psql = psql
        self.calls: List[Dict[str, Any]] = []
        self.image_present = image_present
        self.build_rc = build_rc

    def __call__(self, cmd, **kwargs):
        cmd = list(cmd)
        self.calls.append(
            {"cmd": cmd, "timeout": kwargs.get("timeout"), "env": kwargs.get("env")}
        )
        if cmd[:4] == ["docker", "exec", "-i", "dopemux-postgres-age"]:
            res = self.psql(cmd[-1], kwargs.get("input") or "")
            return SimpleNamespace(
                returncode=res.returncode, stdout=res.stdout, stderr=res.stderr
            )
        if cmd[:3] == ["docker", "image", "inspect"]:
            if self.image_present:
                return SimpleNamespace(returncode=0, stdout="sha256:fake\n", stderr="")
            return SimpleNamespace(
                returncode=1, stdout="", stderr=f"Error: No such image: {cmd[3]}"
            )
        if "build" in cmd:
            return SimpleNamespace(
                returncode=self.build_rc, stdout="build log line\n", stderr=""
            )
        return SimpleNamespace(returncode=0, stdout="", stderr="")


def _invoke_init(repo: Path, monkeypatch, runner: FakeCmdRunner):
    from dopemux.commands import mcp_commands

    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda *_a, **_k: _init_catalog())
    monkeypatch.setattr(mcp_commands, "_catalog_path", lambda *_a, **_k: None)
    monkeypatch.setattr(mcp_commands, "_INIT_RUNNER", runner)
    return CliRunner().invoke(mcp_commands.mcp, ["init", "--repo", str(repo)])


def test_password_never_printed(tmp_path: Path, monkeypatch, capsys):
    repo = _repo(tmp_path)
    monkeypatch.setattr(ct.secrets, "token_hex", lambda n: FAKE_PROVISIONED_PASSWORD)
    runner = FakeCmdRunner(FakePsql(legacy_count=0))

    result = _invoke_init(repo, monkeypatch, runner)

    captured = capsys.readouterr()
    shown = result.output + captured.out + captured.err
    assert result.exit_code == 0, shown
    assert "provisioned" in shown
    assert FAKE_PROVISIONED_PASSWORD not in shown
    assert not any(
        FAKE_PROVISIONED_PASSWORD in " ".join(c["cmd"]) for c in runner.calls
    )
    # final review M7: Postgres gets a SCRAM verifier on stdin, never the plaintext
    # (which would land in the server log on a statement error).
    assert not any(FAKE_PROVISIONED_PASSWORD in sql for _db, sql in runner.psql.calls)
    assert any("PASSWORD 'SCRAM-SHA-256$4096:" in sql for _db, sql in runner.psql.calls)
    # Both sidecar images were pre-built synchronously with the #1459 budget.
    builds = [c for c in runner.calls if "build" in c["cmd"]]
    assert [b["cmd"][-1] for b in builds] == ["conport", "dope-memory"]
    assert all(b["timeout"] == dr.build_timeout_secs() for b in builds)
    # The tenant user is not printed either.
    user = ct.load_secrets(ct.secrets_path(_identity(repo).project_id)).db_user
    assert user not in shown


def test_init_skips_prebuild_when_images_exist_and_reports_build_failure(
    tmp_path: Path, monkeypatch
):
    repo = _repo(tmp_path)
    present = FakeCmdRunner(FakePsql(legacy_count=3), image_present=True)
    ok = _invoke_init(repo, monkeypatch, present)
    assert ok.exit_code == 0, ok.output
    assert "legacy_shared" in ok.output
    assert not [c for c in present.calls if "build" in c["cmd"]]

    repo2 = _repo(tmp_path, "BuildFails")
    failing = FakeCmdRunner(FakePsql(legacy_count=3), build_rc=1)
    bad = _invoke_init(repo2, monkeypatch, failing)
    assert bad.exit_code != 0
    assert "FAIL" in bad.output and "build.log" in bad.output
    # The config written before the build stays.
    assert (repo2 / ".mcp.json").exists()
    assert (repo2 / ".envrc.dopemux-mcp").exists()


# --- Step 4: lifecycle (compose env, gate phase) and the R3 ambient scrub --------


def test_compose_interpolation_env_ignores_ambient_vars(monkeypatch):
    for name in dr.AMBIENT_SCRUB_VARS:
        monkeypatch.setenv(name, "ambient-from-another-checkout")
    monkeypatch.setenv("CONPORT_DB_PASSWORD", "ambient-foreign-pw")
    monkeypatch.setenv("DOPE_MEMORY_PORT", "39998")
    monkeypatch.setenv("AGE_PASSWORD", "fake-age-pw")
    monkeypatch.setenv("CONPORT_MAX_CHILD_FAILURES", "9")
    monkeypatch.setenv("DOPEMUX_MCP_BUILD_TIMEOUT_SECS", "42")

    env = dr.env_with_compose_interpolation(
        product=Path("/x/y/dopemux-mvp"),
        extra={"CONPORT_DB_PASSWORD": "fake-extra-pw"},
        scrub_ambient=True,
    )

    assert env["CONPORT_DB_PASSWORD"] == "fake-extra-pw"
    assert "DOPE_MEMORY_PORT" not in env
    assert not [
        n for n in dr.AMBIENT_SCRUB_VARS if n != "CONPORT_DB_PASSWORD" and n in env
    ]
    # Not scrubbed: exact set, not a prefix sweep.
    assert env["AGE_PASSWORD"] == "fake-age-pw"
    assert env["CONPORT_MAX_CHILD_FAILURES"] == "9"
    assert env["DOPEMUX_MCP_BUILD_TIMEOUT_SECS"] == "42"
    # Legacy cwd-compose callers keep the operator's sourced envrc.
    legacy = dr.env_with_compose_interpolation(product=Path("/x/y/dopemux-mvp"))
    assert legacy["DOPE_MEMORY_PORT"] == "39998"


def test_launcher_lifecycle_env_uses_the_shared_scrub_set(monkeypatch):
    from dopemux.mcp import launcher

    env = {name: "ambient" for name in dr.AMBIENT_SCRUB_VARS}
    env.update({"PATH": "/bin", "AGE_PASSWORD": "fake-age-pw"})
    kept = launcher._lifecycle_env(env, {"servers": {}})
    assert kept == {"PATH": "/bin", "AGE_PASSWORD": "fake-age-pw"}
    assert not hasattr(launcher, "_IDENTITY_ENV")


def _lc_catalog() -> Dict[str, Any]:
    return {
        "version": 1,
        **{k: v for k, v in _init_catalog().items() if k != "version"},
    }


def _lc_repo(tmp_path: Path) -> Path:
    repo = _repo(tmp_path, "LcProj")
    (repo / ".mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "conport": {
                        "type": "sse",
                        "url": "http://localhost:${CONPORT_MCP_PORT:-3005}/sse",
                    },
                    "dope-memory": {
                        "type": "http",
                        "url": "http://localhost:${DOPE_MEMORY_PORT:-3020}/mcp",
                    },
                }
            }
        )
    )
    return repo


def _lc_product(tmp_path: Path) -> Path:
    product = tmp_path / "product"
    if not product.exists():
        (product / "scripts" / "mcp-wrappers").mkdir(parents=True)
        (product / "compose.yml").write_text("services: {}\n")
    return product


class LifecycleRunner(FakeCmdRunner):
    """Adds compose `up` (flips the port probe) and the gate's `docker exec`."""

    def __init__(
        self,
        psql: FakePsql,
        *,
        gate_rc: int = 0,
        gate_stderr: str = "",
        gate_raises: Optional[BaseException] = None,
        on_up=None,
        lock_state: Optional[Dict[str, int]] = None,
    ):
        super().__init__(psql, image_present=True)
        self.up = False
        self.gate_rc = gate_rc
        self.gate_stderr = gate_stderr
        self.gate_raises = gate_raises
        self.on_up = on_up
        self.lock_state = lock_state
        self.gate_files: List[Dict[str, Any]] = []
        self.gate_lock_held: List[int] = []

    def __call__(self, cmd, **kwargs):
        cmd = list(cmd)
        if cmd[:3] == ["docker", "exec", "--env-file"]:
            if self.lock_state is not None:
                self.gate_lock_held.append(self.lock_state["held"])
            if self.gate_raises is not None:
                raise self.gate_raises
            env_file = Path(cmd[3])
            self.gate_files.append(
                {
                    "path": env_file,
                    "text": env_file.read_text(),
                    "mode": _mode(env_file),
                }
            )
            self.calls.append(
                {"cmd": cmd, "timeout": kwargs.get("timeout"), "env": None}
            )
            return SimpleNamespace(
                returncode=self.gate_rc, stdout="", stderr=self.gate_stderr
            )
        result = super().__call__(cmd, **kwargs)
        if "up" in cmd and "compose" in cmd:
            self.up = True
            if self.on_up is not None:
                self.on_up()
        return result

    def kinds(self) -> List[str]:
        out = []
        for c in self.calls:
            cmd = c["cmd"]
            if cmd[:4] == ["docker", "exec", "-i", "dopemux-postgres-age"]:
                out.append("psql")
            elif cmd[:3] == ["docker", "exec", "--env-file"]:
                out.append(f"gate:{cmd[-1]}")
            elif "up" in cmd and "compose" in cmd:
                out.append("up")
        squashed: List[str] = []
        for k in out:
            if not (squashed and squashed[-1] == k == "psql"):
                squashed.append(k)
        return squashed


def _lc_start(tmp_path: Path, repo: Path, runner: LifecycleRunner):
    from dopemux.mcp.lifecycle import run_lifecycle

    return run_lifecycle(
        "start",
        repo=repo,
        services=["conport"],
        catalog=_lc_catalog(),
        dry_run=False,
        registry_path=tmp_path / "rt" / "instances.json",
        docker_runner=lambda *a, **k: SimpleNamespace(
            returncode=0, stdout="", stderr=""
        ),
        cmd_runner=runner,
        product_root=_lc_product(tmp_path),
        process_env={},
        skip_doctor=True,
        port_is_free_fn=lambda port: not runner.up,
    )


def _conport(result) -> Dict[str, Any]:
    return next(s for s in result.services if s["service"] == "conport")


def test_start_passes_tenant_env_to_compose_only(tmp_path: Path, monkeypatch):
    repo = _lc_repo(tmp_path)
    identity = _identity(repo)
    ct.write_secrets(
        ct.secrets_path(identity.project_id),
        ct.TenantCredentials(
            "conport_lc_tenant", "conport_lc_tenant", "fake-lc-pw", "secrets"
        ),
    )
    # Another checkout's sourced envrc in the process environment.
    monkeypatch.setenv("CONPORT_DB_NAME", "conport_foreign")
    monkeypatch.setenv("CONPORT_DB_USER", "conport_foreign")
    monkeypatch.setenv("CONPORT_DB_PASSWORD", "ambient-fake")
    monkeypatch.setenv("CONPORT_HTTP_PORT", "39999")
    monkeypatch.setenv("DOPE_MEMORY_PORT", "39998")
    runner = LifecycleRunner(FakePsql())

    result = _lc_start(tmp_path, repo, runner)

    assert result.exit_code == 0, result.to_dict()
    up = next(c for c in runner.calls if "up" in c["cmd"] and "compose" in c["cmd"])
    assert up["env"]["CONPORT_DB_NAME"] == "conport_lc_tenant"
    assert up["env"]["CONPORT_DB_USER"] == "conport_lc_tenant"
    assert up["env"]["CONPORT_DB_PASSWORD"] == "fake-lc-pw"
    assert "ambient-fake" not in json.dumps(up["env"])
    assert up["env"].get("CONPORT_HTTP_PORT") != "39999"
    assert "DOPE_MEMORY_PORT" not in up["env"]
    # Only the compose `up` gets the credentials (not the image probe/build env).
    others = [c for c in runner.calls if c is not up and c["env"]]
    assert others and all("CONPORT_DB_PASSWORD" not in c["env"] for c in others)
    # The service's ports still reach compose, through mcp.env on disk.
    env_file = Path(up["cmd"][up["cmd"].index("--env-file") + 1])
    mcp_env = env_file.read_text()
    ports = _conport(result)["ports"]
    assert f"CONPORT_HTTP_PORT={ports['CONPORT_HTTP_PORT']}" in mcp_env
    assert f"CONPORT_MCP_PORT={ports['CONPORT_MCP_PORT']}" in mcp_env
    assert "CONPORT_DB_" not in mcp_env and "fake-lc-pw" not in mcp_env
    # Source `secrets`, nothing owed: no psql, no gate.
    assert runner.psql.calls == []
    assert not [k for k in runner.kinds() if k.startswith("gate:")]


def _assert_password_absent(
    password: str, *, runner, result, capsys, tmp_path: Path
) -> None:
    for call in runner.calls:
        assert password not in " ".join(call["cmd"])
    assert password not in json.dumps(result.to_dict())
    for svc in result.services:
        for finding in svc.get("findings") or []:
            assert password not in json.dumps(finding)
    captured = capsys.readouterr()
    assert password not in captured.out and password not in captured.err
    for artifact in result.runtime_artifacts:
        assert password not in Path(artifact).read_text()
    plans = list(tmp_path.rglob("start-plan.json"))
    assert plans and all(password not in p.read_text() for p in plans)


def test_start_runs_gate_after_first_provision(tmp_path: Path, monkeypatch, capsys):
    repo = _lc_repo(tmp_path)
    identity = _identity(repo)
    monkeypatch.setattr(ct.secrets, "token_hex", lambda n: FAKE_PROVISIONED_PASSWORD)
    runner = LifecycleRunner(FakePsql(legacy_count=0))

    result = _lc_start(tmp_path, repo, runner)

    assert result.exit_code == 0, result.to_dict()
    # Database phase before the sidecar starts; gate phase (apply, verify) after it.
    assert runner.kinds() == ["psql", "up", "gate:apply", "gate:verify"]
    assert "create_role" in _labels(runner.psql.calls)
    cname = _conport(result)["container_names"][0]
    apply_cmd, verify_cmd = [
        c["cmd"]
        for c in runner.calls
        if c["cmd"][:3] == ["docker", "exec", "--env-file"]
    ]
    assert apply_cmd[4:] == [
        "-e",
        "DPMX_CONPORT_MIGRATION_APPLY=1",
        cname,
        "python",
        "migrations/conport_migration_gate.py",
        "apply",
    ]
    assert verify_cmd[4:] == [
        cname,
        "python",
        "migrations/conport_migration_gate.py",
        "verify",
    ]
    assert "--database-url" not in apply_cmd + verify_cmd
    # The URL travelled in a 0600 temp env file that is gone afterwards.
    for seen in runner.gate_files:
        assert seen["mode"] == 0o600
        assert seen["text"].startswith("DATABASE_URL=postgresql://")
        assert FAKE_PROVISIONED_PASSWORD in seen["text"]
        assert "@dopemux-postgres-age:5432/" in seen["text"]
        assert not seen["path"].exists()
    up = next(c for c in runner.calls if "up" in c["cmd"] and "compose" in c["cmd"])
    assert up["env"]["CONPORT_DB_PASSWORD"] == FAKE_PROVISIONED_PASSWORD
    assert ct.pending_gate_credentials(identity.project_id) is None
    _assert_password_absent(
        FAKE_PROVISIONED_PASSWORD,
        runner=runner,
        result=result,
        capsys=capsys,
        tmp_path=tmp_path,
    )


def test_gate_failure_is_fail_and_next_start_retries_without_reprovisioning(
    tmp_path: Path, monkeypatch, capsys
):
    repo = _lc_repo(tmp_path)
    identity = _identity(repo)
    monkeypatch.setattr(ct.secrets, "token_hex", lambda n: FAKE_PROVISIONED_PASSWORD)
    leaky = f"could not connect to postgresql://u:{FAKE_PROVISIONED_PASSWORD}@x/db"
    first = LifecycleRunner(FakePsql(legacy_count=0), gate_rc=1, gate_stderr=leaky)

    failed = _lc_start(tmp_path, repo, first)

    assert failed.exit_code == 1
    finding = next(
        f
        for f in _conport(failed)["findings"]
        if f["code"] == "CONPORT_TENANT_GATE_FAILED"
    )
    assert finding["severity"] == "FAIL"
    assert str(ct.secrets_path(identity.project_id)) in finding["message"]
    _assert_password_absent(
        FAKE_PROVISIONED_PASSWORD,
        runner=first,
        result=failed,
        capsys=capsys,
        tmp_path=tmp_path,
    )
    assert ct.pending_gate_credentials(identity.project_id) is not None

    second = LifecycleRunner(FakePsql(legacy_count=0))
    retried = _lc_start(tmp_path, repo, second)

    assert retried.exit_code == 0, retried.to_dict()
    assert second.psql.calls == []  # never re-provision, never rotate
    assert [k for k in second.kinds() if k.startswith("gate:")] == [
        "gate:apply",
        "gate:verify",
    ]
    assert ct.pending_gate_credentials(identity.project_id) is None


def test_start_marks_legacy_shared_store_and_passes_no_credentials(tmp_path: Path):
    repo = _lc_repo(tmp_path)
    runner = LifecycleRunner(FakePsql(legacy_count=5))

    result = _lc_start(tmp_path, repo, runner)

    assert result.exit_code == 0, result.to_dict()
    codes = {(f["code"], f["severity"]) for f in _conport(result)["findings"]}
    assert ("CONPORT_LEGACY_SHARED_STORE", "WARN") in codes
    up = next(c for c in runner.calls if "up" in c["cmd"] and "compose" in c["cmd"])
    assert not [k for k in up["env"] if k.startswith("CONPORT_DB_")]
    assert not [k for k in runner.kinds() if k.startswith("gate:")]


def test_start_refuses_conport_when_the_shared_history_is_unknown(tmp_path: Path):
    repo = _lc_repo(tmp_path)
    runner = LifecycleRunner(FakePsql(rc=2))  # postgres does not answer

    result = _lc_start(tmp_path, repo, runner)

    assert result.exit_code == 1
    finding = next(
        f
        for f in _conport(result)["findings"]
        if f["code"] == "CONPORT_TENANT_UNKNOWN_HISTORY"
    )
    assert finding["severity"] == "FAIL"
    assert "up" not in runner.kinds()  # conport never started on a guessed store


def test_start_turns_existing_role_into_fail_finding(tmp_path: Path):
    repo = _lc_repo(tmp_path)
    identity = _identity(repo)
    runner = LifecycleRunner(FakePsql(legacy_count=0, role_exists=True))

    result = _lc_start(tmp_path, repo, runner)

    assert result.exit_code == 1
    finding = next(
        f
        for f in _conport(result)["findings"]
        if f["code"] == "ROLE_EXISTS_WITHOUT_SECRETS"
    )
    assert finding["severity"] == "FAIL"
    assert str(ct.secrets_path(identity.project_id)) in finding["message"]
    assert "up" not in runner.kinds()


def test_adopt_with_gate_refuses_real_docker_under_pytest():
    creds = ct.TenantCredentials(
        "conport_x", "conport_x", "fake-gate-pw", "provisioned"
    )
    with pytest.raises(ct.TenantError) as excinfo:
        ct.adopt_with_gate("dopemux-x-conport", creds)
    assert excinfo.value.code == "CONPORT_TENANT_GATE_FAILED"
    assert "fake-gate-pw" not in str(excinfo.value)


# --- fix round 1 -------------------------------------------------------------------


def _state(identity, root: Optional[Path] = None) -> str:
    path = (
        ct.secrets_path(identity.project_id, secrets_root=root).parent
        / ct.STATE_FILENAME
    )
    return path.read_text().strip() if path.exists() else ""


def _passwords(monkeypatch, *values: str) -> None:
    """Each token_hex call returns the next fake; a resume must not draw a new one."""
    queue = list(values)
    monkeypatch.setattr(ct.secrets, "token_hex", lambda n: queue.pop(0))


SECOND_FAKE_PASSWORD = "beef" * 12


def test_resume_after_create_database_failure_keeps_password_and_role(
    tmp_path, monkeypatch
):
    identity = _identity(_repo(tmp_path))
    root = tmp_path / "secrets"
    _passwords(monkeypatch, FAKE_PROVISIONED_PASSWORD, SECOND_FAKE_PASSWORD)
    first = FakePsql(legacy_count=0, fail_on="CREATE DATABASE")

    with pytest.raises(ct.TenantError) as excinfo:
        ct.resolve_tenant(identity, envrc_values={}, psql=first, secrets_root=root)

    assert excinfo.value.code == "CONPORT_TENANT_PROVISION_FAILED"
    assert FAKE_PROVISIONED_PASSWORD not in str(excinfo.value)
    assert _labels(first.calls) == [
        "create_role",
        "create_database",
    ]  # the second one failed
    assert _state(identity, root) == "database"

    second = FakePsql(role_exists=True, db_exists=False)
    creds = ct.resolve_tenant(identity, envrc_values={}, psql=second, secrets_root=root)

    assert creds.source == "provisioned" and creds.gate_pending
    assert creds.db_password == FAKE_PROVISIONED_PASSWORD
    labels = _labels(second.calls)
    assert "create_role" not in labels and "alter_role" not in labels
    assert labels[:2] == ["create_database", "revoke"]
    assert labels[-1] == "workspace_rows"
    assert not any("DPMX_TABLES=" in sql for _db, sql in second.calls)  # no re-count
    stored = ct.load_secrets(ct.secrets_path(identity.project_id, secrets_root=root))
    assert stored.db_password == FAKE_PROVISIONED_PASSWORD
    assert _state(identity, root) == "gate"


def test_resume_after_migration_003_failure_applies_exactly_the_rest(
    tmp_path, monkeypatch
):
    identity = _identity(_repo(tmp_path))
    root = tmp_path / "secrets"
    _passwords(monkeypatch, FAKE_PROVISIONED_PASSWORD, SECOND_FAKE_PASSWORD)
    first = FakePsql(legacy_count=0, fail_on="-- Migration 003")

    with pytest.raises(ct.TenantError):
        ct.resolve_tenant(identity, envrc_values={}, psql=first, secrets_root=root)

    applied = [lbl for lbl in _labels(first.calls) if lbl.startswith("migration:")]
    assert applied == [
        "migration:001_enhanced_decision_model",
        "migration:002_decision_patterns_table",
        "migration:003_multi_tenancy_foundation",  # attempted, failed
    ]
    assert _state(identity, root) == "database:002_decision_patterns_table"

    second = FakePsql(role_exists=True, db_exists=True, schema_present=True)
    creds = ct.resolve_tenant(identity, envrc_values={}, psql=second, secrets_root=root)

    assert creds.db_password == FAKE_PROVISIONED_PASSWORD
    assert _labels(second.calls) == [
        "revoke",
        "extension",
        "migration:003_multi_tenancy_foundation",
        "migration:004_unified_query_indexes",
        "migration:007_worktree_support_simple",
        "migration:008_write_principal",
        "workspace_rows",
    ]
    assert _state(identity, root) == "gate"


# --- PR #1503 review (Codex P2): a committed migration is never replayed ------------

COMMITTED_001_002 = ("view:decisions_needing_review", "view:pattern_statistics")


def _provision_resumed(psql: FakePsql, checkpoints: List[str], applied_through: str):
    ct.provision_database(
        slug="fake_tenant",
        workspace_id="/tmp/fake",
        password=FAKE_PROVISIONED_PASSWORD,
        psql=psql,
        schema_path=ct.schema_path(),
        migrations_dir=ct.migrations_dir(),
        resume=True,
        applied_through=applied_through,
        on_migration=checkpoints.append,
    )


def test_resume_after_a_lost_002_checkpoint_does_not_replay_002(tmp_path, monkeypatch):
    """002 committed, then its checkpoint write failed: the next start must not resend it."""
    identity = _identity(_repo(tmp_path))
    root = tmp_path / "secrets"
    _passwords(monkeypatch, FAKE_PROVISIONED_PASSWORD, SECOND_FAKE_PASSWORD)
    real_write_state = ct._write_state

    def lose_the_002_checkpoint(path: Path, state: str) -> None:
        if state == "database:002_decision_patterns_table":
            raise OSError(28, "No space left on device")
        real_write_state(path, state)

    monkeypatch.setattr(ct, "_write_state", lose_the_002_checkpoint)
    first = FakePsql(legacy_count=0)
    with pytest.raises(OSError):
        ct.resolve_tenant(identity, envrc_values={}, psql=first, secrets_root=root)
    assert first.migrations() == [
        "001_enhanced_decision_model",
        "002_decision_patterns_table",  # committed; its checkpoint was lost
    ]
    assert _state(identity, root) == "database:001_enhanced_decision_model"

    written: List[str] = []

    def record(path: Path, state: str) -> None:
        written.append(state)
        real_write_state(path, state)

    monkeypatch.setattr(ct, "_write_state", record)
    second = FakePsql(
        role_exists=True,
        db_exists=True,
        schema_present=True,
        existing=COMMITTED_001_002,
        already_applied=("001_enhanced_decision_model", "002_decision_patterns_table"),
    )
    creds = ct.resolve_tenant(identity, envrc_values={}, psql=second, secrets_root=root)

    assert creds.source == "provisioned" and creds.gate_pending
    assert creds.db_password == FAKE_PROVISIONED_PASSWORD
    assert second.steps() == [
        "probe:pattern_statistics",
        "migration:003_multi_tenancy_foundation",
        "migration:004_unified_query_indexes",
        "migration:007_worktree_support_simple",
        "migration:008_write_principal",
    ]
    # 002 is checkpointed without being resent; the rest as each one applies.
    assert written == [f"database:{m}" for m in ct.PROVISION_MIGRATIONS[1:]] + ["gate"]
    assert _state(identity, root) == "gate"
    assert _labels(second.calls)[-1] == "workspace_rows"


def test_schema_present_without_a_checkpoint_runs_only_the_uncommitted_migrations():
    psql = FakePsql(
        role_exists=True,
        db_exists=True,
        schema_present=True,
        existing=COMMITTED_001_002,
        already_applied=("001_enhanced_decision_model", "002_decision_patterns_table"),
    )
    checkpoints: List[str] = []

    _provision_resumed(psql, checkpoints, applied_through="")

    assert psql.steps() == [
        "probe:decisions_needing_review",
        "probe:pattern_statistics",
        *(f"migration:{m}" for m in ct.PROVISION_MIGRATIONS[2:]),
    ]
    assert checkpoints == list(ct.PROVISION_MIGRATIONS)
    assert "schema" not in _labels(psql.calls)
    probes = [sql for _db, sql in psql.calls if "DPMX_APPLIED=" in sql]
    assert len(probes) == 2
    for sql in probes:  # read-only, as the tenant role, no secret
        assert sql.startswith("SET ROLE conport_fake_tenant;\nSELECT 'DPMX_APPLIED='")
        assert FAKE_PROVISIONED_PASSWORD not in sql


@pytest.mark.parametrize(
    "failure",
    [
        {"probe_rc": 1},
        {"probe_answer": ""},
        {"probe_answer": _aligned("DPMX_APPLIED=maybe")},
    ],
    ids=["psql-exit-1", "no-marker", "unexpected-answer"],
)
def test_a_failing_applied_probe_refuses_and_runs_no_migration(failure):
    psql = FakePsql(role_exists=True, db_exists=True, schema_present=True, **failure)
    checkpoints: List[str] = []

    with pytest.raises(ct.TenantError) as excinfo:
        _provision_resumed(psql, checkpoints, applied_through="")

    assert excinfo.value.code == "CONPORT_TENANT_PROVISION_FAILED"
    assert "applied probe" in excinfo.value.detail
    assert psql.migrations() == [] and checkpoints == []
    assert "workspace_rows" not in _labels(psql.calls)
    assert FAKE_PROVISIONED_PASSWORD not in str(excinfo.value)


def test_a_partly_applied_rerunnable_migration_is_replayed_not_skipped():
    """003 is not one transaction: a kill can leave its table without its indexes."""
    psql = FakePsql(
        role_exists=True,
        db_exists=True,
        schema_present=True,
        existing=(*COMMITTED_001_002, "table:user_workspace_access"),
        already_applied=("001_enhanced_decision_model", "002_decision_patterns_table"),
    )  # index:idx_access_workspace (003 L66) is missing
    checkpoints: List[str] = []

    _provision_resumed(psql, checkpoints, applied_through="002_decision_patterns_table")

    assert psql.steps() == [f"migration:{m}" for m in ct.PROVISION_MIGRATIONS[2:]]
    assert checkpoints == list(ct.PROVISION_MIGRATIONS[2:])


def test_fresh_database_runs_every_migration_without_probes():
    every_probe_object = [
        obj for objs in _gate_schema_checks().values() for obj in objs
    ]  # a probe, if one were sent, would report each migration applied
    psql = FakePsql(existing=every_probe_object)
    checkpoints: List[str] = []

    ct.provision_database(
        slug="fake_tenant",
        workspace_id="/tmp/fake",
        password=FAKE_PROVISIONED_PASSWORD,
        psql=psql,
        schema_path=ct.schema_path(),
        migrations_dir=ct.migrations_dir(),
        on_migration=checkpoints.append,
    )

    assert psql.steps() == [f"migration:{m}" for m in ct.PROVISION_MIGRATIONS]
    assert not any("DPMX_APPLIED=" in sql for _db, sql in psql.calls)
    assert checkpoints == list(ct.PROVISION_MIGRATIONS)


def test_unreadable_state_file_fails_closed(tmp_path):
    repo = _lc_repo(tmp_path)
    identity = _identity(repo)
    path = ct.secrets_path(identity.project_id)
    ct.write_secrets(
        path, ct.TenantCredentials("conport_s", "conport_s", "fake-state-pw", "secrets")
    )
    state_path = path.parent / ct.STATE_FILENAME
    state_path.mkdir()  # reading it raises IsADirectoryError

    with pytest.raises(ct.TenantError) as excinfo:
        ct.resolve_tenant(identity, envrc_values={}, psql=FakePsql())
    assert excinfo.value.code == "TENANT_STATE_UNREADABLE"
    assert str(state_path) in str(excinfo.value)

    runner = LifecycleRunner(FakePsql())
    result = _lc_start(tmp_path, repo, runner)
    assert result.exit_code == 1
    finding = next(
        f
        for f in _conport(result)["findings"]
        if f["code"] == "TENANT_STATE_UNREADABLE"
    )
    assert finding["severity"] == "FAIL" and str(state_path) in finding["message"]
    assert "up" not in runner.kinds()


def _lock_spy(monkeypatch):
    from contextlib import contextmanager

    from dopemux.mcp import lifecycle as lc

    real = lc.provision_lock
    state = {"held": 0, "taken": 0}

    @contextmanager
    def spy(project_id):
        with real(project_id):
            state["held"] += 1
            state["taken"] += 1
            try:
                yield
            finally:
                state["held"] -= 1

    monkeypatch.setattr(lc, "provision_lock", spy)
    return state


def test_gate_runs_under_provision_lock(tmp_path, monkeypatch):
    repo = _lc_repo(tmp_path)
    lock = _lock_spy(monkeypatch)
    runner = LifecycleRunner(FakePsql(legacy_count=0), lock_state=lock)

    result = _lc_start(tmp_path, repo, runner)

    assert result.exit_code == 0, result.to_dict()
    assert runner.gate_lock_held == [1, 1]  # apply and verify both under the lock
    assert lock["held"] == 0


def test_gate_skipped_when_another_start_already_adopted(tmp_path, monkeypatch):
    repo = _lc_repo(tmp_path)
    identity = _identity(repo)
    lock = _lock_spy(monkeypatch)
    # Another launcher finishes the gate while this start runs compose up.
    runner = LifecycleRunner(
        FakePsql(legacy_count=0),
        lock_state=lock,
        on_up=lambda: ct.mark_gate_done(identity.project_id),
    )

    result = _lc_start(tmp_path, repo, runner)

    assert result.exit_code == 0, result.to_dict()
    assert not [k for k in runner.kinds() if k.startswith("gate:")]
    assert lock["taken"] == 1  # the state was re-read under the lock
    notes = [
        f
        for f in _conport(result)["findings"]
        if f["code"] == "CONPORT_TENANT_GATE_ADOPTED"
    ]
    assert notes and "already" in notes[0]["message"]


def test_gate_runner_oserror_is_a_gate_failed_finding(tmp_path, monkeypatch):
    repo = _lc_repo(tmp_path)
    identity = _identity(repo)
    monkeypatch.setattr(ct.secrets, "token_hex", lambda n: FAKE_PROVISIONED_PASSWORD)
    before = set(Path(tempfile.gettempdir()).glob("dopemux-conport-gate-*.env"))
    runner = LifecycleRunner(
        FakePsql(legacy_count=0),
        gate_raises=PermissionError(13, "Permission denied", "/fake/bin/docker"),
    )

    result = _lc_start(tmp_path, repo, runner)

    assert result.exit_code == 1
    finding = next(
        f
        for f in _conport(result)["findings"]
        if f["code"] == "CONPORT_TENANT_GATE_FAILED"
    )
    assert finding["severity"] == "FAIL"
    assert "Permission denied" in finding["message"]
    assert str(ct.secrets_path(identity.project_id)) in finding["message"]
    assert FAKE_PROVISIONED_PASSWORD not in json.dumps(result.to_dict())
    assert ct.pending_gate_credentials(identity.project_id) is not None
    # The gate env file was still removed.
    assert set(Path(tempfile.gettempdir()).glob("dopemux-conport-gate-*.env")) == before


def test_start_reports_oserror_filename_and_strerror(tmp_path):
    repo = _lc_repo(tmp_path)
    identity = _identity(repo)
    projects = ct.secrets_path(identity.project_id).parent.parent
    projects.parent.mkdir(parents=True, exist_ok=True)
    projects.write_text("not a directory\n")  # the per-project dir cannot be created
    runner = LifecycleRunner(FakePsql(legacy_count=0))

    result = _lc_start(tmp_path, repo, runner)

    assert result.exit_code == 1
    finding = next(f for f in _conport(result)["findings"] if f["severity"] == "FAIL")
    assert finding["code"] == "CONPORT_TENANT_PROVISION_FAILED"
    assert "Not a directory" in finding["message"]
    assert str(projects) in finding["message"]


def test_init_reports_oserror_filename_and_strerror(tmp_path, monkeypatch, capsys):
    from dopemux.commands import mcp_commands

    repo = _repo(tmp_path)
    identity = _identity(repo)
    projects = ct.secrets_path(identity.project_id).parent.parent
    projects.parent.mkdir(parents=True, exist_ok=True)
    projects.write_text("not a directory\n")
    monkeypatch.setattr(
        mcp_commands, "_INIT_RUNNER", FakeCmdRunner(FakePsql(legacy_count=0))
    )

    ok = mcp_commands._init_sidecars(repo, ["conport"], {})

    out = capsys.readouterr().out
    assert ok is False
    assert "FAIL CONPORT_TENANT_PROVISION_FAILED" in out
    assert "Not a directory" in out and str(projects) in out


def test_start_legacy_shared_never_passes_ambient_tenant_vars(tmp_path, monkeypatch):
    repo = _lc_repo(tmp_path)
    monkeypatch.setenv("CONPORT_DB_NAME", "conport_ambient_fake")
    monkeypatch.setenv("CONPORT_DB_USER", "conport_ambient_fake")
    monkeypatch.setenv("CONPORT_DB_PASSWORD", "ambient-fake-pw")
    runner = LifecycleRunner(FakePsql(legacy_count=5))

    result = _lc_start(tmp_path, repo, runner)

    assert result.exit_code == 0, result.to_dict()
    assert ("CONPORT_LEGACY_SHARED_STORE", "WARN") in {
        (f["code"], f["severity"]) for f in _conport(result)["findings"]
    }
    up = next(c for c in runner.calls if "up" in c["cmd"] and "compose" in c["cmd"])
    assert not [k for k in up["env"] if k.startswith("CONPORT_DB_")]
    assert "ambient-fake" not in json.dumps(up["env"])
    env_file = Path(up["cmd"][up["cmd"].index("--env-file") + 1])
    text = env_file.read_text()
    assert "CONPORT_DB_" not in text and "ambient-fake" not in text


# --- final review M7: CREATE ROLE carries a SCRAM-SHA-256 verifier ---------------------

_SCRAM_RE = re.compile(
    r"SCRAM-SHA-256\$4096:(?P<salt>[A-Za-z0-9+/=]+)\$(?P<stored>[A-Za-z0-9+/=]+):(?P<server>[A-Za-z0-9+/=]+)"
)


def test_create_role_sends_a_scram_verifier_not_the_password(
    tmp_path: Path, monkeypatch
):
    import base64
    import hashlib
    import hmac

    identity = _identity(_repo(tmp_path))
    psql = FakePsql(legacy_count=0)
    monkeypatch.setattr(ct.secrets, "token_hex", lambda n: FAKE_PROVISIONED_PASSWORD)

    creds = ct.resolve_tenant(
        identity, envrc_values={}, psql=psql, secrets_root=tmp_path / "s"
    )

    create = next(sql for _db, sql in psql.calls if sql.startswith("CREATE ROLE"))
    assert FAKE_PROVISIONED_PASSWORD not in create
    match = _SCRAM_RE.search(create)
    assert match, create
    salt = base64.b64decode(match["salt"])
    assert len(salt) == 16
    # the verifier is the one the plaintext in the secrets file logs in with
    salted = hashlib.pbkdf2_hmac("sha256", creds.db_password.encode(), salt, 4096)
    client_key = hmac.new(salted, b"Client Key", "sha256").digest()
    assert base64.b64decode(match["stored"]) == hashlib.sha256(client_key).digest()
    assert (
        base64.b64decode(match["server"])
        == hmac.new(salted, b"Server Key", "sha256").digest()
    )
    stored = ct.load_secrets(
        ct.secrets_path(identity.project_id, secrets_root=tmp_path / "s")
    )
    assert (
        stored.db_password == FAKE_PROVISIONED_PASSWORD
    )  # the client still gets plaintext


def test_scram_verifier_matches_the_rfc_7677_exchange():
    """RFC 7677 section 3 test vector (user "user", password "pencil")."""
    import base64
    import hashlib
    import hmac

    verifier = ct.scram_sha256_verifier(
        "pencil", salt=base64.b64decode("W22ZaJ0SNY7soEsUEjb6gQ==")
    )
    match = _SCRAM_RE.fullmatch(verifier)
    assert match and match["salt"] == "W22ZaJ0SNY7soEsUEjb6gQ=="
    stored = base64.b64decode(match["stored"])
    server = base64.b64decode(match["server"])
    nonce = "rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0"
    auth = (
        "n=user,r=rOprNGfwEbeRWgbNEkqO,"
        f"r={nonce},s=W22ZaJ0SNY7soEsUEjb6gQ==,i=4096,"
        f"c=biws,r={nonce}"
    ).encode()
    signature = hmac.new(server, auth, "sha256").digest()
    assert (
        base64.b64encode(signature).decode()
        == "6rriTRBi23WpRR/wtup+mMhUZUn/dB5nLTJRsjl95G4="
    )
    proof = base64.b64decode("dHzbZapWIk4jUhN+Ute9ytag9zjfMHgsqmmiz7AndVQ=")
    client_key = bytes(
        a ^ b for a, b in zip(proof, hmac.new(stored, auth, "sha256").digest())
    )
    assert hashlib.sha256(client_key).digest() == stored


def test_a_failing_create_role_never_echoes_the_verifier():
    inner = FakePsql(legacy_count=0)

    def psql(database: str, sql: str):
        if sql.startswith("CREATE ROLE"):  # Postgres echoes the failing statement
            return subprocess.CompletedProcess(
                ["psql"], 1, "", f"ERROR: boom\nSTATEMENT: {sql}"
            )
        return inner(database, sql)

    with pytest.raises(ct.TenantError) as excinfo:
        ct.provision_database(
            slug="fake_tenant",
            workspace_id="/tmp/fake",
            password=FAKE_PROVISIONED_PASSWORD,
            psql=psql,
            schema_path=ct.schema_path(),
            migrations_dir=ct.migrations_dir(),
        )
    assert "STATEMENT" in excinfo.value.detail and "***" in excinfo.value.detail
    assert "SCRAM-SHA-256$" not in excinfo.value.detail
    assert FAKE_PROVISIONED_PASSWORD not in excinfo.value.detail


# --- final review P1: the tenant gate reports failure by flag, not by detail text ----


def test_gate_failure_with_an_empty_detail_is_still_a_failure(
    tmp_path: Path, monkeypatch
):
    from dopemux.mcp import lifecycle as lc

    identity = _identity(_repo(tmp_path))
    creds = ct.TenantCredentials(
        "conport_x", "conport_x", "fake-gate-pw", "provisioned"
    )
    monkeypatch.setattr(ct, "pending_gate_credentials", lambda project_id: creds)

    def gate_fails_silently(*_a, **_k):
        raise ct.TenantError("CONPORT_TENANT_GATE_FAILED", "")

    monkeypatch.setattr(ct, "adopt_with_gate", gate_fails_silently)
    findings = lc._run_tenant_gate(identity, "dopemux-x-conport", None, expected=True)
    assert [(f["code"], f["severity"]) for f in findings] == [
        ("CONPORT_TENANT_GATE_FAILED", "FAIL")
    ]


# --- residual fix B3: redact before the error tail is cut to 300 characters ----------


def test_a_cut_verifier_fragment_never_survives_the_error_tail():
    inner = FakePsql(legacy_count=0)
    seen: Dict[str, str] = {}
    padding = "x" * 238  # the 300-character cut lands inside the verifier

    def psql(database: str, sql: str):
        if sql.startswith("CREATE ROLE"):
            seen["verifier"] = re.search(r"'(SCRAM-SHA-256\$[^']+)'", sql).group(1)
            echoed = f"ERROR: boom\nSTATEMENT: {sql}\n{padding}"
            return subprocess.CompletedProcess(["psql"], 1, "", echoed)
        return inner(database, sql)

    with pytest.raises(ct.TenantError) as excinfo:
        ct.provision_database(
            slug="fake_tenant",
            workspace_id="/tmp/fake",
            password=FAKE_PROVISIONED_PASSWORD,
            psql=psql,
            schema_path=ct.schema_path(),
            migrations_dir=ct.migrations_dir(),
        )
    detail = excinfo.value.detail
    verifier = seen["verifier"]
    for size in (20, 40, 60):  # no tail fragment of the verifier is left
        assert verifier[-size:] not in detail
    assert "***" in detail


def test_a_cut_password_fragment_never_survives_the_gate_error_tail():
    password = "f00d" * 12
    creds = ct.TenantCredentials("conport_x", "conport_x", password, "provisioned")

    def runner(cmd, **kwargs):
        leak = (
            f"could not connect: postgresql://conport_x:{password}@host/db\n"
            + "y" * 260
        )
        return SimpleNamespace(returncode=1, stdout="", stderr=leak)

    with pytest.raises(ct.TenantError) as excinfo:
        ct.adopt_with_gate("dopemux-x-conport", creds, runner=runner)
    assert password[-20:] not in excinfo.value.detail


def test_init_fails_closed_when_the_shared_history_is_unknown(
    tmp_path: Path, monkeypatch
):
    repo = _repo(tmp_path)
    runner = FakeCmdRunner(FakePsql(rc=2))  # postgres does not answer

    result = _invoke_init(repo, monkeypatch, runner)

    assert result.exit_code != 0
    assert "FAIL CONPORT_TENANT_UNKNOWN_HISTORY" in result.output
    assert "nothing was changed" in result.output
    # it stops before the images; the config written before the tenant step stays
    assert not [c for c in runner.calls if "build" in c["cmd"]]
    assert not ct.secrets_path(_identity(repo).project_id).exists()
    assert (repo / ".mcp.json").exists()
