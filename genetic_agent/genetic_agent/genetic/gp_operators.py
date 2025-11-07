"""Genetic Programming operators for code repair."""

import ast
import copy
from typing import List, Tuple, Optional
import random


class GPOperators:
    """Genetic programming operators for code manipulation."""

    def __init__(self, max_tree_depth: int = 10):
        self.max_tree_depth = max_tree_depth

    def subtree_crossover(self, parent1: ast.AST, parent2: ast.AST) -> Tuple[ast.AST, ast.AST]:
        """Perform subtree crossover between two AST trees."""
        # Find all nodes in both trees
        nodes1 = self._get_all_nodes(parent1)
        nodes2 = self._get_all_nodes(parent2)

        if not nodes1 or not nodes2:
            return copy.deepcopy(parent1), copy.deepcopy(parent2)

        # Select random subtrees
        subtree1 = random.choice(nodes1)
        subtree2 = random.choice(nodes2)

        # Create offspring by swapping subtrees
        offspring1 = self._replace_subtree(copy.deepcopy(parent1), subtree1, subtree2)
        offspring2 = self._replace_subtree(copy.deepcopy(parent2), subtree2, subtree1)

        return offspring1, offspring2

    def hoist_mutation(self, tree: ast.AST) -> ast.AST:
        """Perform hoist mutation by moving a subtree up in the hierarchy."""
        nodes = self._get_all_nodes(tree)

        if not nodes or len(nodes) < 2:
            return copy.deepcopy(tree)

        # Select a random node (not root)
        node = random.choice(nodes[1:])  # Skip root

        # Find parent of selected node
        parent = self._find_parent(tree, node)

        if parent is None:
            return copy.deepcopy(tree)

        # Replace parent with selected node (hoist the subtree up)
        return self._replace_node(copy.deepcopy(tree), parent, node)

    def node_replacement(self, tree: ast.AST, replacement_pool: List[ast.AST]) -> ast.AST:
        """Replace a random node with a node from the replacement pool."""
        nodes = self._get_all_nodes(tree)

        if not nodes or not replacement_pool:
            return copy.deepcopy(tree)

        # Select node to replace (not root to avoid complete replacement)
        target_node = random.choice(nodes[1:])

        # Select replacement
        replacement = random.choice(replacement_pool)

        # Replace the node
        return self._replace_node(copy.deepcopy(tree), target_node, copy.deepcopy(replacement))

    def _get_all_nodes(self, tree: ast.AST) -> List[ast.AST]:
        """Get all nodes in the AST tree."""
        nodes = []
        for node in ast.walk(tree):
            nodes.append(node)
        return nodes

    def _find_parent(self, tree: ast.AST, target: ast.AST) -> Optional[ast.AST]:
        """Find the parent of a target node in the AST."""
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                if child is target:
                    return node
        return None

    def _replace_subtree(self, tree: ast.AST, old_subtree: ast.AST, new_subtree: ast.AST) -> ast.AST:
        """Replace a subtree in the AST."""
        return self._replace_node(tree, old_subtree, new_subtree)

    def _replace_node(self, tree: ast.AST, old_node: ast.AST, new_node: ast.AST) -> ast.AST:
        """Replace a node in the AST with another node."""
        class NodeReplacer(ast.NodeTransformer):
            def visit(self, node):
                if node is old_node:
                    return new_node
                return self.generic_visit(node)

        replacer = NodeReplacer()
        return replacer.visit(tree)

    def validate_ast(self, tree: ast.AST) -> bool:
        """Validate that the AST represents valid Python code."""
        try:
            # Try to compile the AST
            compile(tree, '<string>', 'exec')
            return True
        except (SyntaxError, TypeError):
            return False

    def tree_to_code(self, tree: ast.AST) -> str:
        """Convert AST back to Python code."""
        return ast.unparse(tree)

    def code_to_tree(self, code: str) -> Optional[ast.AST]:
        """Convert Python code to AST tree."""
        try:
            return ast.parse(code)
        except SyntaxError:
            return None

    def get_tree_complexity(self, tree: ast.AST) -> int:
        """Calculate tree complexity (number of nodes)."""
        return len(self._get_all_nodes(tree))

    def simplify_tree(self, tree: ast.AST, max_complexity: int = 50) -> ast.AST:
        """Simplify tree if it exceeds maximum complexity."""
        complexity = self.get_tree_complexity(tree)
        if complexity <= max_complexity:
            return tree

        # Simple simplification: remove unnecessary nodes
        # This is a placeholder - more sophisticated simplification could be implemented
        return tree