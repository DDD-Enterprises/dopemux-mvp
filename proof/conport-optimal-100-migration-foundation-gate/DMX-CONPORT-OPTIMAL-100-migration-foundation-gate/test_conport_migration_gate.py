import importlib.util
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


def test_migration_004_targets_public_schema_not_ag_catalog():
    source = (CONPORT_DIR / "migrations" / "004_unified_query_indexes.sql").read_text(
        encoding="utf-8"
    )

    assert "ag_catalog" not in source
    assert "ON public.decisions USING GIN" in source
    assert "ON public.progress_entries" in source
    assert "ON public.custom_data" in source
