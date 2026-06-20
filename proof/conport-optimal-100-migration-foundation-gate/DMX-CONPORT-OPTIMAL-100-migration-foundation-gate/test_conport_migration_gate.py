import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CONPORT_DIR = ROOT / "docker" / "mcp-servers-source" / "conport"
GATE_PATH = CONPORT_DIR / "migrations" / "conport_migration_gate.py"

spec = importlib.util.spec_from_file_location("conport_migration_gate", GATE_PATH)
gate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = gate
spec.loader.exec_module(gate)


def _write_required_migrations(base: Path) -> None:
    for name in gate.REQUIRED_MIGRATIONS:
        (base / name).write_text(f"-- {name}\n", encoding="utf-8")
    (base / "007_rollback.sql").write_text("-- rollback\n", encoding="utf-8")
    (base / "README.md").write_text("# docs\n", encoding="utf-8")


def test_discover_migrations_is_deterministic_and_excludes_rollback(tmp_path):
    _write_required_migrations(tmp_path)

    migrations = gate.discover_migrations(tmp_path)

    assert [migration.filename for migration in migrations] == [
        "001_enhanced_decision_model.sql",
        "002_decision_patterns_table.sql",
        "003_multi_tenancy_foundation.sql",
        "004_unified_query_indexes.sql",
        "007_worktree_support_simple.sql",
    ]
    assert all("rollback" not in migration.filename for migration in migrations)


def test_discover_migrations_fails_closed_when_required_file_missing(tmp_path):
    _write_required_migrations(tmp_path)
    (tmp_path / "003_multi_tenancy_foundation.sql").unlink()

    try:
        gate.discover_migrations(tmp_path)
    except gate.GateError as exc:
        assert "required migration files missing" in str(exc)
    else:
        raise AssertionError("missing required migration must fail closed")


def test_apply_requires_explicit_operator_gate(tmp_path, monkeypatch):
    _write_required_migrations(tmp_path)
    monkeypatch.delenv(gate.APPLY_ENV, raising=False)

    code = gate.main(
        [
            "apply",
            "--database-url",
            "postgresql://user:pass@localhost/db",
            "--migrations-dir",
            str(tmp_path),
        ]
    )

    assert code == 2


def test_schema_identifier_validation_fails_closed(tmp_path, monkeypatch):
    _write_required_migrations(tmp_path)
    monkeypatch.delenv(gate.APPLY_ENV, raising=False)

    code = gate.main(
        [
            "verify",
            "--database-url",
            "postgresql://user:pass@localhost/db",
            "--migrations-dir",
            str(tmp_path),
            "--schema",
            "public;drop schema public",
        ]
    )

    assert code == 2


def test_non_public_schema_is_rejected_before_migration_execution(tmp_path, monkeypatch):
    _write_required_migrations(tmp_path)
    monkeypatch.setenv(gate.APPLY_ENV, "1")

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("non-public schema must fail before connecting")

    monkeypatch.setattr(gate, "connect", fail_if_called)

    code = gate.main(
        [
            "apply",
            "--database-url",
            "postgresql://user:pass@localhost/db",
            "--migrations-dir",
            str(tmp_path),
            "--schema",
            "tenant_a",
        ]
    )

    assert code == 2


def test_ledger_validation_detects_checksum_mismatch(tmp_path):
    _write_required_migrations(tmp_path)
    migrations = gate.discover_migrations(tmp_path)
    rows = {
        migration.version: {
            "filename": migration.filename,
            "checksum_sha256": migration.checksum,
            "success": True,
        }
        for migration in migrations
    }
    rows[4]["checksum_sha256"] = "bad-checksum"

    errors = gate.validate_ledger_rows(migrations, rows)

    assert "checksum mismatch for 004_unified_query_indexes.sql" in errors


def test_apply_preflights_base_schema_before_ledger_mutation(tmp_path, monkeypatch):
    _write_required_migrations(tmp_path)
    monkeypatch.setenv(gate.APPLY_ENV, "1")

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("ledger must not be touched before base schema preflight")

    monkeypatch.setattr(gate, "connect", lambda _database_url: FakeConnection())
    monkeypatch.setattr(
        gate,
        "preflight_base_schema",
        lambda _conn, _schema: [
            "missing base table public.decisions; run schema.sql before gated migrations"
        ],
    )
    monkeypatch.setattr(gate, "ensure_ledger", fail_if_called)

    code = gate.main(
        [
            "apply",
            "--database-url",
            "postgresql://user:pass@localhost/db",
            "--migrations-dir",
            str(tmp_path),
        ]
    )

    assert code == 2


def test_adopt_existing_migrations_records_verified_schema_without_replay(monkeypatch):
    migration = gate.Migration(
        version=1,
        filename="001_enhanced_decision_model.sql",
        path=Path("001_enhanced_decision_model.sql"),
        checksum="abc",
    )
    recorded = []

    monkeypatch.setattr(gate, "migration_already_applied", lambda *_args: True)
    monkeypatch.setattr(
        gate,
        "record_migration",
        lambda _conn, _schema, item, _seconds, success: recorded.append(
            (item.filename, success)
        ),
    )

    rows = {}
    adopted = gate.adopt_existing_migrations(object(), "public", [migration], rows)

    assert adopted == ["001_enhanced_decision_model.sql"]
    assert recorded == [("001_enhanced_decision_model.sql", True)]
    assert rows[1]["checksum_sha256"] == "abc"


def test_marker_based_adoption_still_requires_final_view_verification(monkeypatch):
    migration = gate.Migration(
        version=2,
        filename="002_decision_patterns_table.sql",
        path=Path("002_decision_patterns_table.sql"),
        checksum="def",
    )

    monkeypatch.setattr(
        gate,
        "migration_schema_errors",
        lambda *_args: ["missing view public.pattern_statistics"],
    )
    monkeypatch.setattr(gate, "migration_marker_exists", lambda *_args: True)
    monkeypatch.setattr(gate, "table_exists", lambda *_args: True)
    monkeypatch.setattr(gate, "column_exists", lambda *_args: True)
    monkeypatch.setattr(gate, "index_exists", lambda *_args: True)
    monkeypatch.setattr(
        gate,
        "view_exists",
        lambda _conn, _schema, view: view != "pattern_statistics",
    )

    assert gate.migration_already_applied(object(), "public", migration)
    assert "missing view public.pattern_statistics" in gate.verify_schema_objects(
        object(), "public"
    )


def test_migration_007_adoption_requires_workspace_instance_unique_index(monkeypatch):
    monkeypatch.setattr(gate, "table_exists", lambda *_args: True)
    monkeypatch.setattr(gate, "column_exists", lambda *_args: True)
    monkeypatch.setattr(gate, "view_exists", lambda *_args: True)
    monkeypatch.setattr(
        gate,
        "index_exists",
        lambda _conn, _schema, index: index != "idx_workspace_contexts_workspace_instance",
    )

    errors = gate.migration_schema_errors(object(), "public", 7)

    assert "missing index public.idx_workspace_contexts_workspace_instance" in errors


def test_psql_invocation_keeps_password_out_of_process_args(tmp_path):
    migration = gate.Migration(
        version=1,
        filename="001_enhanced_decision_model.sql",
        path=tmp_path / "001_enhanced_decision_model.sql",
        checksum="abc",
    )

    args, env = gate.build_psql_invocation(
        "postgresql://user:secret%20value@localhost:5432/dbname",
        migration,
    )

    assert "secret" not in " ".join(args)
    assert env["PGPASSWORD"] == "secret value"
    assert args[:2] == ["psql", "-v"]
    assert "-f" in args


def test_psql_invocation_preserves_libpq_uri_options(tmp_path):
    migration = gate.Migration(
        version=1,
        filename="001_enhanced_decision_model.sql",
        path=tmp_path / "001_enhanced_decision_model.sql",
        checksum="abc",
    )

    args, env = gate.build_psql_invocation(
        "postgresql://user:secret@db.example.com:5432/conport?sslmode=require&connect_timeout=5",
        migration,
    )

    command = " ".join(args)
    assert "secret" not in command
    assert env["PGPASSWORD"] == "secret"
    assert "-d" in args
    database_arg = args[args.index("-d") + 1]
    assert database_arg == (
        "postgresql://user@db.example.com:5432/conport"
        "?sslmode=require&connect_timeout=5"
    )


def test_psql_invocation_preserves_empty_host_libpq_uri(tmp_path):
    migration = gate.Migration(
        version=1,
        filename="001_enhanced_decision_model.sql",
        path=tmp_path / "001_enhanced_decision_model.sql",
        checksum="abc",
    )

    args, _env = gate.build_psql_invocation(
        "postgresql:///conport?host=/var/run/postgresql&connect_timeout=5",
        migration,
    )

    database_arg = args[args.index("-d") + 1]
    assert database_arg == (
        "postgresql:///conport?host=/var/run/postgresql&connect_timeout=5"
    )


def test_psql_invocation_keeps_query_password_out_of_process_args(tmp_path):
    migration = gate.Migration(
        version=1,
        filename="001_enhanced_decision_model.sql",
        path=tmp_path / "001_enhanced_decision_model.sql",
        checksum="abc",
    )

    args, env = gate.build_psql_invocation(
        "postgresql:///conport?user=conport&password=secret%20value&sslmode=require",
        migration,
    )

    command = " ".join(args)
    assert "secret" not in command
    assert "password=" not in command
    assert env["PGPASSWORD"] == "secret value"
    database_arg = args[args.index("-d") + 1]
    assert database_arg == "postgresql:///conport?user=conport&sslmode=require"


def test_unknown_migration_version_is_not_adopted_without_schema_checks(monkeypatch):
    migration = gate.Migration(
        version=99,
        filename="099_future_migration.sql",
        path=Path("099_future_migration.sql"),
        checksum="future",
    )

    monkeypatch.setattr(gate, "migration_marker_exists", lambda *_args: True)

    assert not gate.migration_already_applied(object(), "public", migration)


def test_asyncpg_url_is_normalized_for_psycopg2_and_psql():
    assert (
        gate.normalize_database_url("postgresql+asyncpg://user:pass@db:5432/name")
        == "postgresql://user:pass@db:5432/name"
    )


def test_dockerfile_packages_migrations_directory():
    dockerfile = (CONPORT_DIR / "Dockerfile").read_text(encoding="utf-8")

    assert "COPY docker/mcp-servers-source/conport/migrations /app/migrations" in dockerfile


def test_startup_no_longer_runs_hidden_enhanced_schema_alters():
    source = (CONPORT_DIR / "enhanced_server.py").read_text(encoding="utf-8")

    assert "ADD COLUMN IF NOT EXISTS instance_id" not in source
    assert "ADD COLUMN IF NOT EXISTS created_by_instance" not in source
    assert "conport_migration_gate.py" in source


def test_base_schema_matches_instance_route_contract():
    source = (CONPORT_DIR / "schema.sql").read_text(encoding="utf-8")

    assert "instance_id VARCHAR(255)" in source
    assert "created_by_instance VARCHAR(255)" in source
    assert "idx_workspace_contexts_workspace_instance" in source
    assert "idx_progress_instance" in source
    assert "idx_progress_workspace_instance" in source
    assert "ON CONFLICT (workspace_id, (COALESCE(instance_id, ''::VARCHAR)))" in source


def test_migration_004_targets_public_schema_not_ag_catalog():
    source = (CONPORT_DIR / "migrations" / "004_unified_query_indexes.sql").read_text(
        encoding="utf-8"
    )

    assert "ag_catalog" not in source
    assert "ON public.decisions USING GIN" in source
    assert "ON public.progress_entries" in source
    assert "ON public.custom_data" in source


# ---------------------------------------------------------------------------
# Ledger-compatibility hardening (ported from PR #928).
#
# These cover the two fail-closed properties #928 added that #917 lacked:
#  - an incompatible/foreign ledger schema (or an unexpected DB error while
#    inspecting the ledger) must surface as a STRUCTURED fail-closed result,
#    never an uncaught traceback;
#  - `apply` must refuse to mutate a pre-existing ledger whose schema this gate
#    does not own ("legacy migration ledger cannot be mutated by this gate").
# ---------------------------------------------------------------------------


class _CtxConn:
    """Minimal context-manager connection stub for main() flow tests."""

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def test_native_ledger_columns_constant_matches_ledger_schema():
    # The gate's own ledger DDL must stay in sync with the column set the
    # compatibility guard treats as native, or the guard would reject the
    # ledger the gate itself creates.
    assert gate.NATIVE_LEDGER_COLUMNS == {
        "version",
        "filename",
        "checksum_sha256",
        "success",
    }


def test_ensure_ledger_compatible_passes_for_native_schema(monkeypatch):
    monkeypatch.setattr(
        gate,
        "ledger_columns",
        lambda *_args: set(gate.NATIVE_LEDGER_COLUMNS) | {"applied_at"},
    )

    # Should not raise for either mode when native columns are present.
    gate.ensure_ledger_compatible(object(), "public", for_apply=False)
    gate.ensure_ledger_compatible(object(), "public", for_apply=True)


def test_verify_on_incompatible_ledger_fails_closed(monkeypatch):
    monkeypatch.setattr(
        gate, "ledger_columns", lambda *_args: {"name", "rank", "checksum", "status"}
    )

    try:
        gate.ensure_ledger_compatible(object(), "public", for_apply=False)
    except gate.GateError as exc:
        assert str(exc) == "migration ledger validation failed"
    else:
        raise AssertionError("incompatible ledger must fail closed on verify")


def test_apply_refuses_to_mutate_incompatible_ledger(monkeypatch):
    monkeypatch.setattr(
        gate, "ledger_columns", lambda *_args: {"name", "rank", "checksum", "status"}
    )

    try:
        gate.ensure_ledger_compatible(object(), "public", for_apply=True)
    except gate.GateError as exc:
        assert str(exc) == "legacy migration ledger cannot be mutated by this gate"
    else:
        raise AssertionError("apply must refuse to mutate a foreign ledger")


def test_ledger_inspection_db_error_is_wrapped_not_raw_traceback(monkeypatch):
    def boom(*_args, **_kwargs):
        raise RuntimeError("connection reset by peer")

    monkeypatch.setattr(gate, "ledger_columns", boom)

    try:
        gate.ensure_ledger_compatible(object(), "public", for_apply=False)
    except gate.GateError as exc:
        assert str(exc) == "migration ledger validation failed"
    except RuntimeError:  # pragma: no cover - explicit failure path
        raise AssertionError("raw DB error must be wrapped as a GateError")
    else:
        raise AssertionError("unexpected ledger DB error must fail closed")


def test_main_verify_emits_structured_fail_closed_on_foreign_ledger(
    tmp_path, monkeypatch, capsys
):
    _write_required_migrations(tmp_path)
    monkeypatch.setattr(gate, "connect", lambda _database_url: _CtxConn())
    monkeypatch.setattr(gate, "ledger_exists", lambda *_args: True)
    monkeypatch.setattr(
        gate, "ledger_columns", lambda *_args: {"name", "rank", "checksum", "status"}
    )

    code = gate.main(
        [
            "verify",
            "--database-url",
            "postgresql://user:pass@localhost/db",
            "--migrations-dir",
            str(tmp_path),
        ]
    )

    assert code == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "fail-closed"
    assert payload["error"] == "migration ledger validation failed"


def test_connect_failure_fails_closed_not_raw_traceback(monkeypatch):
    class _FakePsycopg2:
        class Error(Exception):
            pass

        @staticmethod
        def connect(*_args, **_kwargs):
            raise _FakePsycopg2.Error("connection refused")

    monkeypatch.setitem(sys.modules, "psycopg2", _FakePsycopg2)

    try:
        gate.connect("postgresql://user:pass@localhost/db")
    except gate.GateError as exc:
        assert str(exc) == "database connection failed"
    except Exception:  # pragma: no cover - explicit failure path
        raise AssertionError("driver error must be wrapped as a GateError")
    else:
        raise AssertionError("connection failure must fail closed")


def test_apply_checks_ledger_compatibility_before_mutating(tmp_path, monkeypatch):
    _write_required_migrations(tmp_path)
    monkeypatch.setenv(gate.APPLY_ENV, "1")
    monkeypatch.setattr(gate, "connect", lambda _database_url: _CtxConn())
    monkeypatch.setattr(gate, "preflight_base_schema", lambda *_args: [])
    monkeypatch.setattr(gate, "ledger_exists", lambda *_args: True)
    monkeypatch.setattr(
        gate, "ledger_columns", lambda *_args: {"name", "rank", "checksum", "status"}
    )

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("foreign ledger must not be created/mutated")

    monkeypatch.setattr(gate, "ensure_ledger", fail_if_called)

    code = gate.main(
        [
            "apply",
            "--database-url",
            "postgresql://user:pass@localhost/db",
            "--migrations-dir",
            str(tmp_path),
        ]
    )

    assert code == 2
