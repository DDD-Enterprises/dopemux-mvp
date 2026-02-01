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

    def negate_condition(self, tree: ast.AST) -> ast.AST:
        """Negate a conditional expression (research-based operator from GP literature)."""
        class ConditionNegator(ast.NodeTransformer):
            def visit_Compare(self, node):
                # Handle comparison operators: > ’ <=, < ’ >=, == ’ !=, etc.
                if len(node.ops) == 1:
                    op = node.ops[0]
                    if isinstance(op, ast.Gt):
                        # > ’ <=
                        node.ops[0] = ast.LtE()
                    elif isinstance(op, ast.Lt):
                        # < ’ >=
                        node.ops[0] = ast.GtE()
                    elif isinstance(op, ast.GtE):
                        # >= ’ <
                        node.ops[0] = ast.Lt()
                    elif isinstance(op, ast.LtE):
                        # <= ’ >
                        node.ops[0] = ast.Gt()
                    elif isinstance(op, ast.Eq):
                        # == ’ !=
                        node.ops[0] = ast.NotEq()
                    elif isinstance(op, ast.NotEq):
                        # != ’ ==
                        node.ops[0] = ast.Eq()
                return self.generic_visit(node)

            def visit_If(self, node):
                # Negate if condition and swap branches (if A then B else C ’ if !A then C else B)
                if node.orelse:  # Has else clause
                    # Swap the bodies
                    node.body, node.orelse = node.orelse, node.body
                    # Negate the condition
                    node.test = ast.UnaryOp(op=ast.Not(), operand=node.test)
                return self.generic_visit(node)

        negator = ConditionNegator()
        return negator.visit(copy.deepcopy(tree))

    def swap_operator(self, tree: ast.AST) -> ast.AST:
        """Swap operators in expressions (research-based operator from GP literature)."""
        class OperatorSwapper(ast.NodeTransformer):
            def visit_BinOp(self, node):
                # Swap arithmetic operators: + ” -, * ” /
                if isinstance(node.op, ast.Add):
                    node.op = ast.Sub()
                elif isinstance(node.op, ast.Sub):
                    node.op = ast.Add()
                elif isinstance(node.op, ast.Mult):
                    node.op = ast.Div()
                elif isinstance(node.op, ast.Div):
                    node.op = ast.Mult()
                elif isinstance(node.op, ast.FloorDiv):
                    node.op = ast.Mod()
                elif isinstance(node.op, ast.Mod):
                    node.op = ast.FloorDiv()
                return self.generic_visit(node)

            def visit_BoolOp(self, node):
                # Swap logical operators: and ” or
                if isinstance(node.op, ast.And):
                    node.op = ast.Or()
                elif isinstance(node.op, ast.Or):
                    node.op = ast.And()
                return self.generic_visit(node)

        swapper = OperatorSwapper()
        return swapper.visit(copy.deepcopy(tree))

    def hunk_edit(self, tree: ast.AST, edit_type: str = "insert") -> ast.AST:
        """Perform hunk edits (GenProg research): insert/delete statement blocks."""
        nodes = self._get_all_nodes(tree)

        if edit_type == "insert":
            # Insert a pass statement at a random location
            if nodes:
                target_node = random.choice(nodes)
                if hasattr(target_node, 'body') and isinstance(target_node.body, list):
                    # Insert pass statement
                    pass_stmt = ast.Pass()
                    insert_pos = random.randint(0, len(target_node.body))
                    target_node.body.insert(insert_pos, pass_stmt)

        elif edit_type == "delete":
            # Delete a random statement (safely)
            stmt_nodes = [n for n in nodes if isinstance(n, (ast.Expr, ast.Assign, ast.Return))]
            if stmt_nodes and len(stmt_nodes) > 1:  # Keep at least one statement
                target_stmt = random.choice(stmt_nodes)
                # Find parent and remove
                for node in ast.walk(tree):
                    if hasattr(node, 'body') and isinstance(node.body, list):
                        if target_stmt in node.body:
                            node.body.remove(target_stmt)
                            break

        return tree

    def ast_safe_mutation(self, tree: ast.AST) -> ast.AST:
        """Apply AST-safe mutations based on GP research patterns."""
        mutations = [
            self.negate_condition,
            self.swap_operator,
            lambda t: self.hunk_edit(t, "insert"),
            lambda t: self.hunk_edit(t, "delete"),
            self.hoist_mutation
        ]

        # Randomly select and apply a mutation
        mutation = random.choice(mutations)
        result = mutation(tree)

        # Validate the result is still AST-valid
        if self.validate_ast(result):
            return result
        else:
            return tree  # Return original if mutation broke AST

    def simplify_tree(self, tree: ast.AST, max_complexity: int = 50) -> ast.AST:
        """Simplify tree if it exceeds maximum complexity."""
        complexity = self.get_tree_complexity(tree)
        if complexity <= max_complexity:
            return tree

        # Simple simplification: remove unnecessary nodes
        # This is a placeholder - more sophisticated simplification could be implemented
        return tree