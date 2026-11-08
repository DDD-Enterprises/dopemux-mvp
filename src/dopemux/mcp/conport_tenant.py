"""ConPort tenants (design D5): per-project database credentials, resolved automatically.

Resolution order (``resolve_tenant``):

1. ``<runtime parent>/projects/<project_id>/secrets.env`` (0600, dir 0700).
2. Legacy ``CONPORT_DB_*`` in the checkout's ``.envrc.dopemux-mcp`` (or, for a
   linked worktree without them, the main checkout's): copied into (1) once.
3. No history for this project in the shared ``dopemux_knowledge_graph`` store:
   provision a database and LOGIN role (``CONNECT`` revoked from ``PUBLIC``)
   under ``provision_lock(project_id)``, ported from the sealed
   ``scripts/migration/provision_conport_project_db.sh``.
4. History in the shared store: keep the shared store (``legacy_shared``,
   Option A); migration to a tenant is M2. When the row count is unavailable
   (Postgres or docker did not answer) the history is unknown and resolution
   fails closed with ``CONPORT_TENANT_UNKNOWN_HISTORY``; nothing is changed.

Provisioning has two phases. The database phase (role, database, extensions,
filtered schema, SQL migrations as the role, workspace rows) runs here,
before any sidecar starts. The gate phase (``adopt_with_gate``: the sealed
``conport_migration_gate.py`` adopts the already-applied SQL, then verifies)
needs this instance's conport container, so the lifecycle runs it after the
container is up. A small state file beside the secrets records which phase
is still owed (``database``, ``database:<last applied migration>``, ``gate``),
so an interrupted run resumes exactly where it stopped instead of
re-provisioning or re-running non-idempotent SQL.

Administration uses ``docker exec`` into ``dopemux-postgres-age`` as the
bootstrap superuser, exactly like the script. SQL travels on psql's stdin,
never argv. A password is never printed, logged, put in argv or rotated:
an existing role without a secrets file fails closed. ``CREATE ROLE`` carries
a SCRAM-SHA-256 verifier (RFC 5802/7677), so the plaintext never reaches the
server (or its statement log); only the 0600 secrets file holds it, for the
client.
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import hmac
import os
import re
import secrets
import subprocess
import tempfile
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Mapping,
    Optional,
    Sequence,
    Tuple,
)
from urllib.parse import quote

from . import docker_runtime as dr
from .envrc import load_envrc
from .locks import _mkdir_private, project_dir, provision_lock

__all__ = [
    "MIGRATION_APPLIED_PROBES",
    "PROVISION_MIGRATIONS",
    "PsqlRunner",
    "TenantCredentials",
    "TenantError",
    "WORKSPACE_TABLES",
    "adopt_with_gate",
    "count_legacy_rows",
    "default_psql_runner",
    "legacy_workspace_aliases",
    "load_secrets",
    "mark_gate_done",
    "os_error_detail",
    "migrations_dir",
    "pending_gate_credentials",
    "provision_database",
    "psql_command",
    "redacted_tail",
    "resolve_tenant",
    "schema_path",
    "scram_sha256_verifier",
    "secrets_path",
    "tenant_compose_env",
    "tenant_slug",
    "write_secrets",
]

AGE_CONTAINER = "dopemux-postgres-age"
SUPERUSER = "dopemux_age"
SHARED_DB = "dopemux_knowledge_graph"
UNREACHABLE_EVIDENCE = "postgres unreachable"
UNKNOWN_HISTORY = "CONPORT_TENANT_UNKNOWN_HISTORY"
ENVRC_FILENAME = ".envrc.dopemux-mcp"
SECRETS_FILENAME = "secrets.env"
STATE_FILENAME = "conport-tenant.state"
STATE_DATABASE = "database"
STATE_GATE = "gate"
CRED_KEYS = ("CONPORT_DB_NAME", "CONPORT_DB_USER", "CONPORT_DB_PASSWORD")
GATE_SCRIPT = "migrations/conport_migration_gate.py"
GATE_APPLY_ENV = "DPMX_CONPORT_MIGRATION_APPLY"

# Workspace-scoped tables of the sealed schema.sql (each has workspace_id).
WORKSPACE_TABLES = (
    "workspace_contexts",
    "decisions",
    "progress_entries",
    "session_snapshots",
    "custom_data",
    "entity_relationships",
    "search_cache",
)

# psql-then-adopt: every migration the sealed gate requires (its
# REQUIRED_MIGRATIONS), applied with psql before the gate runs. The script
# predates 008; leaving 008 to the gate would run psql inside the gate's own
# open transaction, which 008's header documents as a deadlock on a fresh DB.
PROVISION_MIGRATIONS = (
    "001_enhanced_decision_model",
    "002_decision_patterns_table",
    "003_multi_tenancy_foundation",
    "004_unified_query_indexes",
    "007_worktree_support_simple",
    "008_write_principal",
)

# The migrations that cannot be re-run (001 and 002: one BEGIN/COMMIT each,
# with a bare CREATE VIEW/TRIGGER), each with the last object its transaction
# creates, as the sealed gate's ``kind:name`` (``migration_schema_errors``)
# split on ":"; that object existing means the migration committed. A resume
# probes these before replaying them. Every other migration is made only of
# idempotent statements and is simply replayed, which also completes one a
# kill left half applied (003 and 004 are not transactions).
MIGRATION_APPLIED_PROBES: Dict[str, Tuple[str, ...]] = {
    "001_enhanced_decision_model": ("view", "decisions_needing_review"),
    "002_decision_patterns_table": ("view", "pattern_statistics"),
}

Source = Literal["secrets", "legacy_envrc", "provisioned", "legacy_shared"]
PsqlRunner = Callable[[str, str], subprocess.CompletedProcess]

_SLUG_RE = re.compile(r"^[a-z][a-z0-9_]{0,40}$")
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_HEX_PASSWORD_RE = re.compile(r"^[0-9a-f]{32,}$")
_SAFE_VALUE_RE = re.compile(r"^[A-Za-z0-9_.,:/@%+=-]*$")


class TenantError(RuntimeError):
    """A tenant failure with a finding code; the text never carries a password."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class TenantCredentials:
    db_name: str
    db_user: str
    db_password: str = field(repr=False)
    source: Source = "secrets"
    evidence: str = ""
    gate_pending: bool = False


# --- paths -----------------------------------------------------------------------


def secrets_path(project_id: str, *, secrets_root: Optional[Path] = None) -> Path:
    """``<runtime parent>/projects/<project_id>/secrets.env``; ``secrets_root`` replaces ``.../projects``."""
    base = project_dir(project_id)  # validates the id even when a root is given
    if secrets_root is not None:
        base = Path(secrets_root) / str(project_id)
    return base / SECRETS_FILENAME


def _state_path(secrets_file: Path) -> Path:
    return Path(secrets_file).parent / STATE_FILENAME


def schema_path() -> Path:
    return (
        dr.product_root() / "docker" / "mcp-servers-source" / "conport" / "schema.sql"
    )


def migrations_dir() -> Path:
    return schema_path().parent / "migrations"


# --- secrets file ----------------------------------------------------------------


def _format_value(value: str) -> str:
    if any(ch in value for ch in ("\n", "\r", "\x00")):
        raise TenantError(
            "CONPORT_TENANT_SECRETS_INVALID", "credential values must be one line"
        )
    if _SAFE_VALUE_RE.match(value):
        return value
    if "'" not in value:
        return f"'{value}'"
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _parse_value(raw: str) -> str:
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] == "'":
        return raw[1:-1]
    if len(raw) >= 2 and raw[0] == raw[-1] == '"':
        return re.sub(r"\\(.)", r"\1", raw[1:-1])
    return raw


def _atomic_write(path: Path, text: str) -> None:
    """Temp file in the same directory, 0600, fsync, ``os.replace``."""
    path = Path(path)
    _mkdir_private(path.parent)
    os.chmod(path.parent, 0o700)
    fd, tmp = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
        os.chmod(path, 0o600)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp)
        raise


def write_secrets(path: Path, creds: TenantCredentials) -> None:
    """``KEY=VALUE`` lines for the three ``CONPORT_DB_*`` keys; dir 0700, file 0600, atomic."""
    values = (creds.db_name, creds.db_user, creds.db_password)
    body = "".join(
        f"{key}={_format_value(val)}\n" for key, val in zip(CRED_KEYS, values)
    )
    _atomic_write(Path(path), body)


def load_secrets(path: Path) -> Optional[TenantCredentials]:
    """None when the file is absent; ``TenantError`` when present but unusable."""
    path = Path(path)
    if not path.exists():
        return None
    remedy = (
        f"{path} is unusable; restore the file from backup or ask the operator "
        "(without it the existing tenant role cannot be reused)"
    )
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise TenantError(
            "CONPORT_TENANT_SECRETS_INVALID", f"{remedy} ({exc.__class__.__name__})"
        ) from None
    values: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        key, sep, raw = line.partition("=")
        if sep:
            values[key.strip()] = _parse_value(raw)
    if not all(values.get(key) for key in CRED_KEYS):
        raise TenantError(
            "CONPORT_TENANT_SECRETS_INVALID", f"{remedy} (needs {', '.join(CRED_KEYS)})"
        )
    return TenantCredentials(
        db_name=values["CONPORT_DB_NAME"],
        db_user=values["CONPORT_DB_USER"],
        db_password=values["CONPORT_DB_PASSWORD"],
        source="secrets",
    )


def os_error_detail(exc: BaseException) -> str:
    """Class, strerror and filename(s) of an OSError (a ValueError's message); never file contents."""
    if isinstance(exc, OSError):
        parts = [exc.__class__.__name__]
        parts += [str(v) for v in (exc.strerror, exc.filename, exc.filename2) if v]
        return ": ".join(parts)
    return f"{exc.__class__.__name__}: {exc}"


def _read_state(secrets_file: Path) -> str:
    """The owed phase; "" when there is no state file. Unreadable is never "nothing owed"."""
    path = _state_path(secrets_file)
    try:
        return path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""
    except OSError as exc:
        raise TenantError(
            "TENANT_STATE_UNREADABLE",
            f"{path} cannot be read ({os_error_detail(exc)}); fix its permissions or restore "
            "it, or ask the operator",
        ) from None


def _database_progress(state: str) -> Optional[str]:
    """None unless the database phase is owed; "" before any migration, else the last applied."""
    if state == STATE_DATABASE:
        return ""
    if state.startswith(STATE_DATABASE + ":"):
        return state[len(STATE_DATABASE) + 1 :]
    return None


def _remaining_migrations(applied_through: str) -> Tuple[str, ...]:
    if not applied_through:
        return PROVISION_MIGRATIONS
    if applied_through not in PROVISION_MIGRATIONS:
        raise TenantError(
            "CONPORT_TENANT_PROVISION_FAILED",
            f"recorded migration {applied_through!r} is not one this provisioner applies",
        )
    return PROVISION_MIGRATIONS[PROVISION_MIGRATIONS.index(applied_through) + 1 :]


def _write_state(secrets_file: Path, state: str) -> None:
    _atomic_write(_state_path(secrets_file), state + "\n")


def _clear_state(secrets_file: Path) -> None:
    with contextlib.suppress(FileNotFoundError):
        _state_path(secrets_file).unlink()


def pending_gate_credentials(
    project_id: str, *, secrets_root: Optional[Path] = None
) -> Optional[TenantCredentials]:
    """Credentials whose migration gate is still owed (no psql call)."""
    path = secrets_path(project_id, secrets_root=secrets_root)
    if _read_state(path) != STATE_GATE:
        return None
    creds = load_secrets(path)
    return replace(creds, gate_pending=True) if creds is not None else None


def mark_gate_done(project_id: str, *, secrets_root: Optional[Path] = None) -> None:
    _clear_state(secrets_path(project_id, secrets_root=secrets_root))


def tenant_compose_env(creds: Optional[TenantCredentials]) -> Dict[str, str]:
    """``CONPORT_DB_*`` for one ``compose up``; empty for the shared store (compose defaults)."""
    if creds is None or creds.source == "legacy_shared" or not creds.db_password:
        return {}
    return dict(zip(CRED_KEYS, (creds.db_name, creds.db_user, creds.db_password)))


# --- psql ------------------------------------------------------------------------


def psql_command(database: str) -> List[str]:
    if not _IDENT_RE.match(database):
        raise ValueError(f"unsafe database name: {database!r}")
    return [
        "docker", "exec", "-i", AGE_CONTAINER,
        "psql", "-v", "ON_ERROR_STOP=1", "-U", SUPERUSER, "-d", database,
    ]  # fmt: skip


def _hermetic_refusal() -> bool:
    """Under pytest a default (real) runner is refused: tests inject fakes."""
    return bool(os.environ.get("PYTEST_CURRENT_TEST"))


def default_psql_runner(
    runner: Optional[dr.Runner] = None, *, timeout: float = 120.0
) -> PsqlRunner:
    """``(database, sql)`` as the bootstrap superuser; the SQL goes to psql's stdin."""

    def _psql(database: str, sql: str) -> subprocess.CompletedProcess:
        argv = psql_command(database)
        if runner is None and _hermetic_refusal():
            return subprocess.CompletedProcess(
                argv,
                1,
                "",
                "refused: a real psql under pytest needs an injected runner",
            )
        res = dr.run_cmd(argv, runner=runner, input_text=sql, timeout=timeout)
        return subprocess.CompletedProcess(argv, res.exit_code, res.stdout, res.stderr)

    return _psql


def _marker(result: subprocess.CompletedProcess, name: str) -> Optional[str]:
    match = re.search(rf"\b{name}=([^\s|]*)", str(result.stdout or ""))
    return match.group(1) if match else None


def _literal(value: str) -> str:
    if "\x00" in value:
        raise ValueError("NUL in SQL literal")
    return "'" + value.replace("'", "''") + "'"


SCRAM_ITERATIONS = 4096
SCRAM_SALT_BYTES = 16


def scram_sha256_verifier(
    password: str, *, salt: Optional[bytes] = None, iterations: int = SCRAM_ITERATIONS
) -> str:
    """Postgres ``SCRAM-SHA-256$<iter>:<salt>$<StoredKey>:<ServerKey>`` (RFC 5802/7677).

    ``CREATE ROLE ... PASSWORD '<verifier>'`` stores it as is, so the plaintext
    never reaches the server. ``password`` must already be SASLprep-normalised
    (provisioning only uses generated hex). ``salt`` defaults to 16 random bytes.
    """
    salt = secrets.token_bytes(SCRAM_SALT_BYTES) if salt is None else salt
    salted = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    client_key = hmac.new(salted, b"Client Key", "sha256").digest()
    stored_key = hashlib.sha256(client_key).digest()
    server_key = hmac.new(salted, b"Server Key", "sha256").digest()

    def b64(raw: bytes) -> str:
        return base64.b64encode(raw).decode("ascii")

    return f"SCRAM-SHA-256${iterations}:{b64(salt)}${b64(stored_key)}:{b64(server_key)}"


def _redact(text: str, secret: str) -> str:
    if not secret:
        return text
    for form in {secret, quote(secret, safe="")}:
        text = text.replace(form, "***")
    return text


#: ``scheme://user:password@``: the password of any URL is masked.
_URL_PASSWORD_RE = re.compile(r"([A-Za-z][A-Za-z0-9+.-]*://[^\s:/@]+:)([^\s@/]+)(@)")


def _redacted_tail(
    text: str, secrets_: Sequence[str], limit: Optional[int] = 300
) -> str:
    """The last ``limit`` characters of ``text`` with every secret replaced first.

    Each value in ``secrets_`` (and its URL-quoted form) and the password of any
    ``scheme://user:password@`` URL become ``***``. Redacting after the cut would
    miss a secret the cut split, leaving a fragment. ``limit=None`` keeps it all.
    """
    clean = str(text or "").strip()
    for secret in secrets_:
        clean = _redact(clean, secret)
    clean = _URL_PASSWORD_RE.sub(r"\1***\3", clean)
    return clean if limit is None else clean[-limit:]


#: Shared with the launcher's start-failure text.
redacted_tail = _redacted_tail


# --- legacy history in the shared store ---------------------------------------------


def legacy_workspace_aliases(identity: Any) -> List[str]:
    """``project_root``, its basename and every ``git worktree list`` path."""
    root = str(getattr(identity, "project_root", "") or "")
    aliases: List[str] = []

    def add(value: str) -> None:
        if value and value not in aliases:
            aliases.append(value)

    add(root)
    add(Path(root).name if root else "")
    if root:
        try:
            proc = subprocess.run(
                ["git", "-C", root, "worktree", "list", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            proc = None
        if proc is not None and proc.returncode == 0:
            for line in proc.stdout.splitlines():
                if line.startswith("worktree "):
                    add(line[len("worktree ") :].strip())
    return aliases


_TABLES_SQL = (
    "SELECT 'DPMX_TABLES=' || coalesce(string_agg(c.relname::text, ',' ORDER BY c.relname), '')\n"
    "FROM pg_catalog.pg_class c\n"
    "JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace\n"
    "WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p')\n"
    "  AND c.relname IN (" + ", ".join(_literal(t) for t in WORKSPACE_TABLES) + ");\n"
)


def count_legacy_rows(aliases: Sequence[str], *, psql: PsqlRunner) -> Optional[int]:
    """Rows for ``aliases`` across the shared store's workspace tables; None when psql fails.

    Tables the shared database never got (a host whose shared conport never
    ran) count as zero rows rather than as an unreachable server.
    """
    names = [a for a in aliases if a]
    if not names:
        return 0
    try:
        listed = psql(SHARED_DB, _TABLES_SQL)
        if listed.returncode != 0:
            return None
        found = _marker(listed, "DPMX_TABLES")
        if found is None:
            return None
        existing = set(filter(None, found.split(",")))
        present = [t for t in WORKSPACE_TABLES if t in existing]
        if not present:
            return 0
        in_list = ", ".join(_literal(a) for a in names)
        union = "\n    UNION ALL\n    ".join(
            f"SELECT 1 FROM public.{t} WHERE workspace_id IN ({in_list})"
            for t in present
        )
        result = psql(
            SHARED_DB,
            f"SELECT 'DPMX_COUNT=' || count(*) FROM (\n    {union}\n) AS legacy;\n",
        )
        if result.returncode != 0:
            return None
        value = _marker(result, "DPMX_COUNT")
        return int(value) if value and value.isdigit() else None
    except Exception:  # noqa: BLE001 - any failure means "unknown", never a raise
        return None


# --- provisioning (database phase) ----------------------------------------------------


def tenant_slug(identity: Any) -> str:
    """``<basename>_<project hash[:8]>``: unique per project root, SQL-identifier safe."""
    root = str(getattr(identity, "project_root", "") or "")
    base = re.sub(r"[^a-z0-9]+", "_", Path(root).name.lower()).strip("_") or "workspace"
    if not base[0].isalpha():
        base = f"p_{base}"
    base = base[:24].rstrip("_")
    digest = str(getattr(identity, "project_hash", "") or "").lower()
    if not re.fullmatch(r"[0-9a-f]{8,}", digest):
        digest = hashlib.sha256(root.encode("utf-8")).hexdigest()
    slug = f"{base}_{digest[:8]}"
    if not _SLUG_RE.match(slug):
        raise TenantError(
            "CONPORT_TENANT_PROVISION_FAILED", f"cannot derive a tenant slug for {root}"
        )
    return slug


def filtered_schema(path: Path) -> str:
    """schema.sql without its sample-data block (the script's awk filter)."""
    out: List[str] = []
    skipping = False
    for line in Path(path).read_text(encoding="utf-8").splitlines(keepends=True):
        if line.startswith("-- INITIAL DATA MIGRATION"):
            skipping = True
        if line.startswith("-- Grant permissions to the ConPort"):
            skipping = False
        if not skipping:
            out.append(line)
    sql = "".join(out)
    if re.search(r"^INSERT INTO", sql, re.M):
        raise TenantError(
            "CONPORT_TENANT_PROVISION_FAILED",
            "schema seed filter left INSERT statements",
        )
    return sql


def _workspace_rows_sql(workspace_id: str, db: str) -> str:
    ws = _literal(workspace_id)
    desc = _literal(f"Canonical workspace for {db} (project-walled {db})")
    return (
        "INSERT INTO users (id, email, display_name)\n"
        "VALUES ('default', 'default@localhost', 'Default User')\n"
        "ON CONFLICT (id) DO NOTHING;\n"
        "INSERT INTO workspaces (id, owner_user_id, name, description)\n"
        f"VALUES ({ws}, 'default', {ws}, {desc})\n"
        "ON CONFLICT (id) DO NOTHING;\n"
        "INSERT INTO user_workspace_access (user_id, workspace_id, role)\n"
        f"VALUES ('default', {ws}, 'owner')\n"
        "ON CONFLICT (user_id, workspace_id) DO NOTHING;\n"
    )


_VERIFY_SQL = (
    "SELECT 'DPMX_VERIFY='"
    " || (SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public')"
    " || ',' || (SELECT count(*) FROM decisions)"
    " || ',' || (SELECT count(*) FROM progress_entries)"
    " || ',' || (SELECT count(*) FROM workspaces);\n"
)


def _applied_probe_sql(probe: Tuple[str, ...]) -> Optional[str]:
    """Read-only ``DPMX_APPLIED=true|false`` for one gate-style object; None for an unknown kind."""
    kind, parts = probe[0], probe[1:]
    if kind in ("table", "view", "index") and len(parts) == 1:
        exists = f"to_regclass({_literal('public.' + parts[0])}) IS NOT NULL"
    elif kind == "column" and len(parts) == 2:
        exists = (
            "EXISTS (SELECT 1 FROM information_schema.columns"
            " WHERE table_schema = 'public'"
            f" AND table_name = {_literal(parts[0])}"
            f" AND column_name = {_literal(parts[1])})"
        )
    else:
        return None
    return f"SELECT 'DPMX_APPLIED=' || ({exists})::text;\n"


def _migration_applied(
    db: str,
    name: str,
    scalar: Callable[[str, str, str, str], str],
    as_role: str,
) -> bool:
    """Whether migration ``name`` already committed, judged from the object it creates.

    Fail closed: a psql error, a missing marker or any answer but true/false
    raises ``CONPORT_TENANT_PROVISION_FAILED``; doubt never replays SQL.
    """
    what = f"applied probe for migration {name}"
    probe = MIGRATION_APPLIED_PROBES.get(name, ())
    sql = _applied_probe_sql(probe) if probe else None
    if sql is None:
        raise TenantError("CONPORT_TENANT_PROVISION_FAILED", f"{what}: no usable probe")
    answer = scalar(db, as_role + sql, "DPMX_APPLIED", what)
    if answer not in ("true", "false"):
        raise TenantError(
            "CONPORT_TENANT_PROVISION_FAILED", f"{what}: unexpected psql output"
        )
    return answer == "true"


def provision_database(
    *,
    slug: str,
    workspace_id: str,
    password: str,
    psql: PsqlRunner,
    schema_path: Path,
    migrations_dir: Path,
    resume: bool = False,
    persist: Optional[Callable[[], None]] = None,
    applied_through: str = "",
    on_migration: Optional[Callable[[str], None]] = None,
) -> None:
    """The script's database phase: role, database, wall, extensions, schema, migrations, rows, checks.

    A role that already exists raises ``ROLE_EXISTS_WITHOUT_SECRETS`` (never
    ``ALTER ROLE ... PASSWORD``) unless ``resume`` says this run's own secrets
    file already holds its password. ``persist`` runs after that check and
    before ``CREATE ROLE``, so the password is on disk before Postgres has it.
    When the schema already exists, only the migrations after
    ``applied_through`` run. The ones that cannot be re-run (001/002, listed in
    ``MIGRATION_APPLIED_PROBES``) are first probed for the object they create,
    the gate's own evidence: one that committed before its checkpoint was
    written is checkpointed, not replayed, and a failing probe refuses. The
    idempotent rest are replayed. ``on_migration`` is told each one as soon as
    it has applied, so progress survives a kill.
    """
    if not _SLUG_RE.match(slug):
        raise TenantError(
            "CONPORT_TENANT_PROVISION_FAILED", f"unsafe tenant slug {slug!r}"
        )
    if not _HEX_PASSWORD_RE.match(password):
        raise TenantError(
            "CONPORT_TENANT_PROVISION_FAILED", "tenant password must be generated hex"
        )
    role = db = f"conport_{slug}"
    as_role = f"SET ROLE {role};\n"
    hidden = [password]  # plus the SCRAM verifier once there is one

    def run(database: str, sql: str, what: str) -> subprocess.CompletedProcess:
        try:
            res = psql(database, sql)
        except Exception as exc:  # noqa: BLE001
            raise TenantError(
                "CONPORT_TENANT_PROVISION_FAILED", f"{what}: {exc.__class__.__name__}"
            ) from None
        if res.returncode != 0:
            tail = _redacted_tail(str(res.stderr or res.stdout or ""), hidden)
            raise TenantError(
                "CONPORT_TENANT_PROVISION_FAILED",
                f"{what} failed (psql exit {res.returncode}): {tail}",
            )
        return res

    def scalar(database: str, sql: str, name: str, what: str) -> str:
        value = _marker(run(database, sql, what), name)
        if value is None:
            raise TenantError(
                "CONPORT_TENANT_PROVISION_FAILED", f"{what}: unexpected psql output"
            )
        return value

    # 1. role + database (superuser); the wall: no PUBLIC connect
    role_sql = f"SELECT 'DPMX_ROLE=' || count(*) FROM pg_catalog.pg_roles WHERE rolname = {_literal(role)};"
    role_exists = scalar("postgres", role_sql, "DPMX_ROLE", "role lookup") != "0"
    if role_exists and not resume:
        raise TenantError(
            "ROLE_EXISTS_WITHOUT_SECRETS",
            f"role {role} already exists but this project has no secrets file for it; restore "
            f"that file, or have an operator drop role and database {db} "
            "(provisioning never resets a password)",
        )
    if persist is not None:
        persist()
    if not role_exists:
        # A SCRAM verifier, never the plaintext: a failing statement is logged verbatim.
        verifier = scram_sha256_verifier(password)
        hidden.append(verifier)
        run(
            "postgres",
            f"CREATE ROLE {role} LOGIN PASSWORD {_literal(verifier)};",
            "CREATE ROLE",
        )
    db_sql = f"SELECT 'DPMX_DB=' || count(*) FROM pg_catalog.pg_database WHERE datname = {_literal(db)};"
    if scalar("postgres", db_sql, "DPMX_DB", "database lookup") == "0":
        run("postgres", f"CREATE DATABASE {db} OWNER {role};", "CREATE DATABASE")
    run(
        "postgres",
        f"REVOKE CONNECT ON DATABASE {db} FROM PUBLIC;\nGRANT ALL PRIVILEGES ON DATABASE {db} TO {role};\n",
        "REVOKE CONNECT",
    )
    # 2. extensions (superuser-only); AGE is optional, as in the script
    run(
        db,
        'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";\nCREATE EXTENSION IF NOT EXISTS "pg_trgm";\n',
        "extensions",
    )
    with contextlib.suppress(Exception):
        psql(db, "CREATE EXTENSION IF NOT EXISTS age;\n")
    # 3. + 4. filtered schema and SQL migrations AS the role (it owns its tables);
    # skipped when a previous run already created them (schema.sql is not idempotent)
    probe = (
        as_role
        + "SELECT 'DPMX_PRESENT=' || (to_regclass('public.decisions') IS NOT NULL)::text;\n"
    )
    present = scalar(db, probe, "DPMX_PRESENT", "schema probe") == "true"
    todo: Tuple[str, ...]
    if not present:
        run(
            db,
            as_role + "BEGIN;\n" + filtered_schema(schema_path) + "\nCOMMIT;\n",
            "schema",
        )
        todo = PROVISION_MIGRATIONS
    else:
        todo = _remaining_migrations(applied_through)
    for name in todo:
        if (
            present
            and name in MIGRATION_APPLIED_PROBES
            and _migration_applied(db, name, scalar, as_role)
        ):
            # Committed, but its checkpoint was never written (a kill, a failed
            # state write): replaying 001/002 fails on CREATE VIEW/TRIGGER.
            if on_migration is not None:
                on_migration(name)
            continue
        sql = (Path(migrations_dir) / f"{name}.sql").read_text(encoding="utf-8")
        run(db, as_role + sql, f"migration {name}")
        if on_migration is not None:
            on_migration(name)
    # 5. canonical workspace rows (real FKs to users)
    run(db, as_role + _workspace_rows_sql(workspace_id, db), "workspace registration")
    # 6. verification
    counts = scalar(db, as_role + _VERIFY_SQL, "DPMX_VERIFY", "verification").split(",")
    try:
        _tables, decisions, progress, workspaces = (int(c) for c in counts)
    except ValueError:
        raise TenantError(
            "CONPORT_TENANT_PROVISION_FAILED", "verification: unexpected counts"
        ) from None
    if not present and (decisions or progress):
        raise TenantError(
            "CONPORT_TENANT_PROVISION_FAILED",
            "verification: seed rows leaked into the tenant",
        )
    if workspaces < 1:
        raise TenantError(
            "CONPORT_TENANT_PROVISION_FAILED", "verification: workspace not registered"
        )


# --- gate phase ---------------------------------------------------------------------


def _gate_database_url(creds: TenantCredentials) -> str:
    user, pw, db = (
        quote(v, safe="") for v in (creds.db_user, creds.db_password, creds.db_name)
    )
    return f"postgresql://{user}:{pw}@{AGE_CONTAINER}:5432/{db}"


def adopt_with_gate(
    container_name: str,
    creds: TenantCredentials,
    *,
    runner: Optional[dr.Runner] = None,
    timeout: float = 180.0,
) -> None:
    """``conport_migration_gate.py apply`` (adopts the psql-applied SQL), then ``verify``.

    The gate reads ``DATABASE_URL`` from its environment, so the URL goes in a
    0600 temp env file (``docker exec --env-file``) and argv carries only the
    file's path. The file is removed in ``finally``.
    """
    if creds.source == "legacy_shared" or not creds.db_password:
        raise TenantError(
            "CONPORT_TENANT_GATE_FAILED", "no tenant credentials to adopt"
        )
    if runner is None and _hermetic_refusal():
        raise TenantError(
            "CONPORT_TENANT_GATE_FAILED",
            "refused: a real docker exec under pytest needs an injected runner",
        )
    fd, tmp = tempfile.mkstemp(prefix="dopemux-conport-gate-", suffix=".env")
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(f"DATABASE_URL={_gate_database_url(creds)}\n")
        for command in ("apply", "verify"):
            argv = ["docker", "exec", "--env-file", tmp]
            if command == "apply":
                argv += ["-e", f"{GATE_APPLY_ENV}=1"]
            argv += [container_name, "python", GATE_SCRIPT, command]
            res = dr.run_cmd(argv, runner=runner, timeout=timeout)
            if res.exit_code != 0:
                tail = _redacted_tail(
                    res.stderr or res.stdout or "", [creds.db_password]
                )
                raise TenantError(
                    "CONPORT_TENANT_GATE_FAILED",
                    f"migration gate {command} in {container_name} exited {res.exit_code}: {tail}",
                )
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp)


# --- resolution -----------------------------------------------------------------------


def _envrc_credentials(
    values: Optional[Mapping[str, str]],
) -> Optional[TenantCredentials]:
    vals = values or {}
    if not all(str(vals.get(key) or "").strip() for key in CRED_KEYS):
        return None
    name, user, password = (str(vals[key]).strip() for key in CRED_KEYS)
    return TenantCredentials(name, user, password, "legacy_envrc")


def _main_checkout_envrc(identity: Any) -> Dict[str, str]:
    root = getattr(identity, "project_root", None)
    if not root:
        return {}
    try:
        return dict(load_envrc(Path(str(root)) / ENVRC_FILENAME).values)
    except Exception:  # noqa: BLE001
        return {}


def _legacy_shared(evidence: str) -> TenantCredentials:
    return TenantCredentials(SHARED_DB, "", "", "legacy_shared", evidence=evidence)


def _with_path(exc: TenantError, path: Path) -> TenantError:
    detail = (
        f"{exc.detail}; secrets file {path}" if exc.detail else f"secrets file {path}"
    )
    return TenantError(exc.code, detail)


def _current(path: Path) -> Optional[TenantCredentials]:
    creds = load_secrets(path)
    if creds is None:
        return None
    state = _read_state(path)
    owed = state == STATE_GATE or _database_progress(state) is not None
    return replace(creds, gate_pending=owed)


def _record_migration(path: Path) -> Callable[[str], None]:
    return lambda name: _write_state(path, f"{STATE_DATABASE}:{name}")


def _resume_locked(identity: Any, path: Path, psql: PsqlRunner) -> TenantCredentials:
    """Finish an interrupted database phase with the password already on disk."""
    creds = load_secrets(path)
    if creds is None:
        raise TenantError(
            "CONPORT_TENANT_SECRETS_INVALID", f"{path} vanished during provisioning"
        )
    if not creds.db_name.startswith("conport_"):
        raise TenantError(
            "CONPORT_TENANT_PROVISION_FAILED", f"{path} names no provisioned tenant"
        )
    progress = _database_progress(_read_state(path)) or ""
    try:
        provision_database(
            slug=creds.db_name[len("conport_") :],
            workspace_id=str(identity.project_root),
            password=creds.db_password,
            psql=psql,
            schema_path=schema_path(),
            migrations_dir=migrations_dir(),
            resume=True,
            applied_through=progress,
            on_migration=_record_migration(path),
        )
    except TenantError as exc:
        raise _with_path(exc, path) from None
    _write_state(path, STATE_GATE)
    return replace(creds, source="provisioned", gate_pending=True)


def _provision_locked(identity: Any, path: Path, psql: PsqlRunner) -> TenantCredentials:
    slug = tenant_slug(identity)
    password = secrets.token_hex(24)
    creds = TenantCredentials(
        f"conport_{slug}", f"conport_{slug}", password, "provisioned", gate_pending=True
    )

    def persist() -> None:
        _write_state(
            path, STATE_DATABASE
        )  # before the secrets: a crash in between re-provisions
        write_secrets(path, creds)

    try:
        provision_database(
            slug=slug,
            workspace_id=str(identity.project_root),
            password=password,
            psql=psql,
            schema_path=schema_path(),
            migrations_dir=migrations_dir(),
            persist=persist,
            on_migration=_record_migration(path),
        )
    except TenantError as exc:
        raise _with_path(exc, path) from None
    _write_state(path, STATE_GATE)
    return creds


def resolve_tenant(
    identity: Any,
    *,
    envrc_values: Optional[Mapping[str, str]],
    psql: PsqlRunner,
    secrets_root: Optional[Path] = None,
    provision: bool = True,
) -> Optional[TenantCredentials]:
    """Secrets file → legacy envrc → shared store with history → provision.

    ``provision=False`` (doctor) never writes and never provisions: it returns
    None where a start would provision. An unavailable legacy row count raises
    ``CONPORT_TENANT_UNKNOWN_HISTORY`` either way. ``identity`` is the lifecycle's own
    identity object (``project_id``, ``project_root``, ``project_hash``).
    """
    project_id = str(getattr(identity, "project_id", "") or "")
    if not project_id:
        raise TenantError(
            "PROJECT_IDENTITY_UNKNOWN", "conport tenant needs a git project identity"
        )
    path = secrets_path(project_id, secrets_root=secrets_root)

    current = _current(path)
    if current is not None:
        if _database_progress(_read_state(path)) is None:
            return current
        if not provision:
            return replace(current, evidence="tenant provisioning incomplete")
        with provision_lock(project_id):
            if _database_progress(_read_state(path)) is None:
                return _current(path) or current
            return _resume_locked(identity, path, psql)

    adopted = _envrc_credentials(envrc_values) or _envrc_credentials(
        _main_checkout_envrc(identity)
    )
    if adopted is not None:
        if not provision:
            return adopted
        with provision_lock(project_id):
            existing = _current(path)
            if existing is not None:
                return existing
            write_secrets(path, adopted)
            _clear_state(path)
        return adopted

    count = count_legacy_rows(legacy_workspace_aliases(identity), psql=psql)
    if count is None:
        # Unknown is not "has history": guessing either way could split a project's
        # data between the shared store and a new tenant (final review R2).
        raise TenantError(
            UNKNOWN_HISTORY,
            f"{UNREACHABLE_EVIDENCE}: this project's history in the shared {SHARED_DB} "
            f"store is unknown; start Postgres ({AGE_CONTAINER}) or fix docker, then "
            "retry; nothing was changed",
        )
    if count > 0:
        return _legacy_shared(
            f"{count} rows for this project in the shared {SHARED_DB} store"
        )
    if not provision:
        return None
    with provision_lock(project_id):
        existing = _current(path)  # another launcher may have provisioned meanwhile
        if existing is not None:
            if _database_progress(_read_state(path)) is not None:
                return _resume_locked(identity, path, psql)
            return existing
        return _provision_locked(identity, path, psql)
