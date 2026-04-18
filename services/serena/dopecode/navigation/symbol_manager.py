from __future__ import annotations

"""Module for symbol management and ID generation."""
import logging
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SymbolID:
    workspace_id: str
    file_path: str
    symbol_name: str
    line: int

    @classmethod
    def parse(cls, symbol_id_str: str) -> SymbolID:
        """Parse string format: <workspace>::<file_path>::<symbol_name>::<line>"""
        parts = symbol_id_str.split("::")
        if len(parts) != 4:
            raise ValueError(f"Invalid SymbolID format: {symbol_id_str}")
        return cls(
            workspace_id=parts[0],
            file_path=parts[1],
            symbol_name=parts[2],
            line=int(parts[3])
        )

    def __str__(self) -> str:
        return f"{self.workspace_id}::{self.file_path}::{self.symbol_name}::{self.line}"

class SymbolManager:
    """Manages symbol identification and reconstruction for dopeCode."""
    
    def __init__(self, workspace_root: Path, workspace_id: str):
        self.workspace_root = workspace_root.resolve()
        self.workspace_id = workspace_id

    def create_id(self, relative_path: str, symbol_name: str, line: int) -> str:
        return str(SymbolID(self.workspace_id, relative_path, symbol_name, line))

    def resolve_path(self, relative_path: str) -> Path:
        full_path = (self.workspace_root / relative_path).resolve()
        if not str(full_path).startswith(str(self.workspace_root)):
            raise ValueError(f"Path traversal detected: {relative_path}")
        return full_path
