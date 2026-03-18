import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

logger = logging.getLogger(__name__)

class DependencyGraph:
    def __init__(self):
        self.nodes: Set[str] = set()
        self.edges: List[Tuple[str, str]] = []
        self.adjacency: Dict[str, Set[str]] = {}
        self.reverse_adjacency: Dict[str, Set[str]] = {}

    def add_node(self, path: str):
        self.nodes.add(path)
        if path not in self.adjacency:
            self.adjacency[path] = set()
        if path not in self.reverse_adjacency:
            self.reverse_adjacency[path] = set()

    def add_edge(self, source: str, target: str):
        self.add_node(source)
        self.add_node(target)
        if target not in self.adjacency[source]:
            self.edges.append((source, target))
            self.adjacency[source].add(target)
            self.reverse_adjacency[target].add(source)

    def build_from_code_intelligence(self, code_intel: List[Dict[str, Any]], manifest: List[Any]):
        """
        Build graph from extracted imports.
        Currently handles simple relative and absolute imports within the same repo.
        """
        # Create a mapping of module names to paths for better resolution
        module_to_path = {}
        for entry in manifest:
            rel_path = entry.get("rel_path", "")
            if not rel_path: continue
            
            p = Path(rel_path)
            # Python mapping
            if rel_path.endswith(".py"):
                parts = p.with_suffix("").parts
                module_name = ".".join(parts)
                module_to_path[module_name] = rel_path
                if parts[-1] == "__init__":
                    module_to_path[".".join(parts[:-1])] = rel_path
            
            # JS/TS mapping
            if rel_path.endswith((".js", ".ts", ".tsx", ".jsx")):
                module_to_path[str(p.with_suffix(""))] = rel_path
                if p.name == "index.ts" or p.name == "index.js":
                    module_to_path[str(p.parent)] = rel_path

        for intel in code_intel:
            source_path = intel["rel_path"]
            self.add_node(source_path)
            
            for imp in intel.get("imports", []):
                # Try to resolve import to a path in the repo
                target_path = self._resolve_import(source_path, imp, module_to_path)
                if target_path:
                    self.add_edge(source_path, target_path)

    def _resolve_import(self, source_path: str, import_str: str, module_to_path: Dict[str, str]) -> str | None:
        # Simple resolution logic
        # 1. Exact module match
        if import_str in module_to_path:
            return module_to_path[import_str]
            
        # 2. Relative resolution (Python)
        if import_str.startswith("."):
            source_dir = Path(source_path).parent
            # ... more complex relative resolution would go here
            
        # 3. Path-based resolution (JS/TS)
        if import_str.startswith("./") or import_str.startswith("../"):
            source_dir = Path(source_path).parent
            try:
                target = (source_dir / import_str).resolve()
                # Find matching node
                for node in self.nodes:
                    if Path(node).with_suffix("") == target or Path(node) == target:
                        return node
            except:
                pass
                
        return None

    def find_clusters(self) -> List[Set[str]]:
        """Find strongly connected components (clusters)."""
        visited = set()
        stack = []

        def fill_order(v, visited, stack):
            visited.add(v)
            for i in self.adjacency.get(v, []):
                if i not in visited:
                    fill_order(i, visited, stack)
            stack.append(v)

        def get_transpose():
            g = DependencyGraph()
            for v in self.nodes:
                for i in self.adjacency.get(v, []):
                    g.add_edge(i, v)
            return g

        def dfs_util(v, visited, cluster):
            visited.add(v)
            cluster.add(v)
            for i in self.adjacency.get(v, []):
                if i not in visited:
                    dfs_util(i, visited, cluster)

        # 1. Fill stack according to finishing times
        for i in list(self.nodes):
            if i not in visited:
                fill_order(i, visited, stack)

        # 2. Transpose graph
        gr = get_transpose()

        # 3. Process all vertices in order defined by stack
        visited = set()
        clusters = []
        while stack:
            i = stack.pop()
            if i not in visited:
                cluster = set()
                gr.dfs_util_external(i, visited, cluster)
                clusters.append(cluster)
        
        return [c for c in clusters if len(c) > 1]

    def dfs_util_external(self, v, visited, cluster):
        visited.add(v)
        cluster.add(v)
        for i in self.adjacency.get(v, []):
            if i not in visited:
                self.dfs_util_external(i, visited, cluster)

    def get_topological_order(self) -> List[str]:
        """Return a topological sort of the graph (nodes with fewer dependencies first)."""
        # This is a simplified version that handles cycles by breaking them
        visited = set()
        order = []

        def visit(n):
            if n in visited:
                return
            visited.add(n)
            for m in self.adjacency.get(n, []):
                visit(m)
            order.append(n)

        for node in sorted(self.nodes):
            visit(node)
            
        return order[::-1]

    # ── Extended methods (Part C) ──────────────────────────────────────────

    def compute_pagerank(
        self,
        damping: float = 0.85,
        iterations: int = 50,
        epsilon: float = 1e-6,
    ) -> Dict[str, float]:
        """Pure-Python iterative PageRank. No NetworkX dependency.

        Higher score = more important file (many things depend on it
        transitively).  Returns {rel_path: rank} normalized to sum ≈ 1.0.
        """
        if not self.nodes:
            return {}

        n = len(self.nodes)
        node_list = sorted(self.nodes)
        idx = {node: i for i, node in enumerate(node_list)}
        rank = [1.0 / n] * n

        for _ in range(iterations):
            new_rank = [(1.0 - damping) / n] * n
            for node in node_list:
                out_degree = len(self.adjacency.get(node, set()))
                if out_degree == 0:
                    # Distribute rank equally (dangling node)
                    share = damping * rank[idx[node]] / n
                    for j in range(n):
                        new_rank[j] += share
                else:
                    share = damping * rank[idx[node]] / out_degree
                    for target in self.adjacency.get(node, set()):
                        if target in idx:
                            new_rank[idx[target]] += share

            # Check convergence
            diff = sum(abs(new_rank[i] - rank[i]) for i in range(n))
            rank = new_rank
            if diff < epsilon:
                break

        return {node_list[i]: rank[i] for i in range(n)}

    def get_in_degree(self, node: str) -> int:
        """Direct import count (how many files import this one)."""
        return len(self.reverse_adjacency.get(node, set()))

    def get_out_degree(self, node: str) -> int:
        """Direct dependency count (how many files this one imports)."""
        return len(self.adjacency.get(node, set()))

    def find_entry_points(self, manifest: List[Any]) -> Set[str]:
        """Identify entry points via multiple signals."""
        entry_points: Set[str] = set()

        # Signal 1: FileEntry.is_entry_point
        for m in manifest:
            if isinstance(m, dict) and m.get("is_entry_point"):
                entry_points.add(m["rel_path"])

        # Signal 2: In-degree 0 + out-degree > 0
        for node in self.nodes:
            if self.get_in_degree(node) == 0 and self.get_out_degree(node) > 0:
                entry_points.add(node)

        # Signal 3: Pattern match
        entry_patterns = (
            "cli.py", "main.py", "app.py", "manage.py", "__main__.py",
            "wsgi.py", "asgi.py", "server.py",
        )
        for node in self.nodes:
            p = Path(node)
            if p.name in entry_patterns:
                entry_points.add(node)

        return entry_points

    def compute_reachability(self, entry_points: Set[str]) -> Dict[str, int]:
        """BFS from all entry points. Returns {node: min_distance}.

        Nodes NOT in result are unreachable = dead code candidates.
        """
        from collections import deque

        distances: Dict[str, int] = {}
        queue: deque[tuple[str, int]] = deque()

        for ep in entry_points:
            if ep in self.nodes:
                distances[ep] = 0
                queue.append((ep, 0))

        while queue:
            node, dist = queue.popleft()
            for target in self.adjacency.get(node, set()):
                if target not in distances:
                    distances[target] = dist + 1
                    queue.append((target, dist + 1))

        return distances

    def find_hub_files(self, top_n: int = 15) -> List[Dict[str, Any]]:
        """Files with highest in-degree (most imported)."""
        hubs = []
        for node in self.nodes:
            in_deg = self.get_in_degree(node)
            if in_deg > 0:
                hubs.append({
                    "rel_path": node,
                    "in_degree": in_deg,
                    "out_degree": self.get_out_degree(node),
                })

        hubs.sort(key=lambda x: x["in_degree"], reverse=True)
        return hubs[:top_n]

    def to_json(self) -> str:
        data = {
            "nodes": list(self.nodes),
            "edges": [{"source": s, "target": t} for s, t in self.edges],
            "clusters": [list(c) for c in self.find_clusters()],
            "topological_order": self.get_topological_order()
        }
        return json.dumps(data, indent=2)
