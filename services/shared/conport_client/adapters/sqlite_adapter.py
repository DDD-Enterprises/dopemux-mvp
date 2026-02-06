"""SQLite adapter shim for ConPort client.

This implementation currently reuses the JSON file-backed adapter behavior
until a dedicated SQLite schema migration is introduced.
"""

from ..backends import BackendType
from .file_adapter import FileAdapter


class SQLiteAdapter(FileAdapter):
    """Compatibility adapter that satisfies the SQLite backend import contract."""

    backend_type = BackendType.SQLITE
