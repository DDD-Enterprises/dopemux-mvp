from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from .navigation.ast_engine import ASTEngine
from .policy.mutation_policy import MutationPolicy
from .transform.refactor_layer import RefactorLayer
from .transform.write_layer import WriteLayer


class DopeCodeRuntime:
    """Bundle the dopeCode policy, navigation, and transform layers."""

    def __init__(
        self,
        workspace_root: Path,
        workspace_id: str,
        tree_sitter: Optional[Any] = None,
        lsp: Optional[Any] = None,
    ) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_id = workspace_id
        self.policy = MutationPolicy(self.workspace_root, workspace_id)
        self.write_layer = WriteLayer(self.workspace_root, workspace_id, policy=self.policy)
        self.ast_engine = ASTEngine(self.workspace_root, workspace_id, tree_sitter, lsp)
        self.refactor_layer = RefactorLayer(self.write_layer, self.ast_engine, policy=self.policy)

    def set_dependencies(self, tree_sitter: Optional[Any] = None, lsp: Optional[Any] = None) -> None:
        self.ast_engine.set_dependencies(tree_sitter=tree_sitter, lsp=lsp)
