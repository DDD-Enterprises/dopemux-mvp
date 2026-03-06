"""Feature-level detection for universal repo-truth-extractor.

Extends archetype classification with granular feature detection.
Scans the repo for specific technologies, frameworks, and patterns
to determine which extraction steps are applicable.

Output: AUTO_FEATURES.json
"""

from __future__ import annotations

import fnmatch
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .fingerprint import deterministic_generated_at

AUTO_FEATURES_FILENAME = "AUTO_FEATURES.json"

# Feature detection rules: (feature_id, description, detection_globs, content_patterns, maps_to_steps)
# Each rule produces a detected feature with confidence and evidence.


@dataclass(frozen=True)
class FeatureRule:
    feature_id: str
    label: str
    description: str
    # Glob patterns that indicate the feature exists
    file_globs: Tuple[str, ...]
    # Regex patterns to search in file content (optional, for higher confidence)
    content_patterns: Tuple[str, ...] = ()
    # Extraction steps this feature maps to
    maps_to_steps: Tuple[str, ...] = ()
    # Phase(s) this feature is relevant to
    maps_to_phases: Tuple[str, ...] = ()
    # Minimum glob matches for "high" confidence
    high_confidence_threshold: int = 2


# --------------------------------------------------------------------------- #
#  Built-in feature rules
# --------------------------------------------------------------------------- #

BUILTIN_RULES: Tuple[FeatureRule, ...] = (
    # --- HTTP API frameworks ---
    FeatureRule(
        feature_id="http_api_python",
        label="Python HTTP API",
        description="Python web framework (FastAPI, Flask, Django, Starlette)",
        file_globs=(
            "**/*routes*.py", "**/*views*.py", "**/*endpoints*.py",
            "**/*app*.py", "**/*api*.py", "**/*server*.py",
        ),
        content_patterns=(
            r"from\s+fastapi\s+import", r"from\s+flask\s+import",
            r"from\s+django\s", r"from\s+starlette\s",
            r"@app\.(get|post|put|delete|patch)\(",
            r"@router\.(get|post|put|delete|patch)\(",
        ),
        maps_to_steps=("C1", "C14", "C15"),
        maps_to_phases=("C",),
        high_confidence_threshold=2,
    ),
    FeatureRule(
        feature_id="http_api_node",
        label="Node/TS HTTP API",
        description="Node.js web framework (Express, Fastify, Nest, Koa, Hono)",
        file_globs=(
            "**/*routes*.ts", "**/*routes*.js", "**/*controller*.ts",
            "**/*controller*.js", "**/*app*.ts", "**/*server*.ts",
        ),
        content_patterns=(
            r"from\s+['\"]express['\"]", r"require\(['\"]express['\"]\)",
            r"from\s+['\"]fastify['\"]", r"from\s+['\"]@nestjs/",
            r"from\s+['\"]koa['\"]", r"from\s+['\"]hono['\"]",
            r"app\.(get|post|put|delete|patch)\(",
        ),
        maps_to_steps=("C1", "C15"),
        maps_to_phases=("C",),
        high_confidence_threshold=2,
    ),
    FeatureRule(
        feature_id="http_api_go",
        label="Go HTTP API",
        description="Go web framework (net/http, Gin, Echo, Chi, Fiber)",
        file_globs=(
            "**/*handler*.go", "**/*routes*.go", "**/*server*.go",
            "**/*api*.go",
        ),
        content_patterns=(
            r"\"net/http\"", r"\"github\.com/gin-gonic/gin\"",
            r"\"github\.com/labstack/echo\"", r"\"github\.com/go-chi/chi\"",
            r"http\.HandleFunc\(", r"r\.GET\(",
        ),
        maps_to_steps=("C1", "C15"),
        maps_to_phases=("C",),
    ),
    FeatureRule(
        feature_id="grpc_api",
        label="gRPC API",
        description="gRPC service definitions and generated code",
        file_globs=(
            "**/*.proto", "**/*_grpc.py", "**/*_pb2*.py",
            "**/*_grpc.go", "**/*.pb.go",
        ),
        content_patterns=(
            r"service\s+\w+\s*\{", r"rpc\s+\w+\s*\(",
            r"grpc\.Server\(", r"grpc\.NewServer\(",
        ),
        maps_to_steps=("C1", "C15"),
        maps_to_phases=("C",),
    ),
    FeatureRule(
        feature_id="graphql_api",
        label="GraphQL API",
        description="GraphQL schema definitions and resolvers",
        file_globs=(
            "**/*.graphql", "**/*schema*.graphql", "**/*resolver*.py",
            "**/*resolver*.ts", "**/*resolver*.js",
        ),
        content_patterns=(
            r"type\s+Query\s*\{", r"type\s+Mutation\s*\{",
            r"from\s+['\"]graphql['\"]", r"@strawberry\.",
        ),
        maps_to_steps=("C1", "C15"),
        maps_to_phases=("C",),
    ),
    # --- Event Systems ---
    FeatureRule(
        feature_id="event_bus",
        label="Event Bus / Message Queue",
        description="Event-driven architecture (Redis Streams, RabbitMQ, Kafka, NATS, custom)",
        file_globs=(
            "**/*event_bus*", "**/*eventbus*", "**/*producer*",
            "**/*consumer*", "**/*subscriber*", "**/*publisher*",
            "**/*message_queue*", "**/*broker*",
        ),
        content_patterns=(
            r"event_bus", r"EventBus", r"publish\(", r"subscribe\(",
            r"redis\.xadd\(", r"pika\.", r"kafka\.",
            r"nats\.", r"celery\.",
        ),
        maps_to_steps=("C2", "A13"),
        maps_to_phases=("C", "A"),
    ),
    # --- Database ---
    FeatureRule(
        feature_id="database_relational",
        label="Relational Database",
        description="SQL database (PostgreSQL, MySQL, SQLite) with migrations",
        file_globs=(
            "**/migrations/**", "**/*schema*.sql", "**/alembic/**",
            "**/alembic.ini", "**/*models*.py", "**/*orm*.py",
        ),
        content_patterns=(
            r"from\s+sqlalchemy\s", r"import\s+psycopg",
            r"CREATE\s+TABLE", r"ALTER\s+TABLE",
            r"from\s+django\.db\s+import\s+models",
        ),
        maps_to_steps=("C6", "C7"),
        maps_to_phases=("C",),
    ),
    FeatureRule(
        feature_id="database_graph",
        label="Graph Database",
        description="Graph database (Neo4j, AGE, ArangoDB)",
        file_globs=(
            "**/*graph*.py", "**/*cypher*", "**/*neo4j*",
        ),
        content_patterns=(
            r"neo4j\.", r"MATCH\s*\(", r"CREATE\s*\(",
            r"from\s+age\s", r"apache_age",
        ),
        maps_to_steps=("C6", "C16"),
        maps_to_phases=("C",),
    ),
    FeatureRule(
        feature_id="database_vector",
        label="Vector Database",
        description="Vector/embedding database (Qdrant, Pinecone, Weaviate, ChromaDB)",
        file_globs=(
            "**/*qdrant*", "**/*pinecone*", "**/*weaviate*",
            "**/*chroma*", "**/*embedding*",
        ),
        content_patterns=(
            r"qdrant_client", r"pinecone\.", r"weaviate\.",
            r"chromadb\.", r"from\s+langchain.*vector",
        ),
        maps_to_steps=("C6",),
        maps_to_phases=("C",),
    ),
    # --- CI/CD ---
    FeatureRule(
        feature_id="ci_github_actions",
        label="GitHub Actions CI",
        description="GitHub Actions workflows",
        file_globs=(".github/workflows/*.yml", ".github/workflows/*.yaml"),
        maps_to_steps=("G1", "E0"),
        maps_to_phases=("G", "E"),
        high_confidence_threshold=1,
    ),
    FeatureRule(
        feature_id="ci_gitlab",
        label="GitLab CI",
        description="GitLab CI/CD pipeline",
        file_globs=(".gitlab-ci.yml",),
        maps_to_steps=("G1", "E0"),
        maps_to_phases=("G", "E"),
        high_confidence_threshold=1,
    ),
    FeatureRule(
        feature_id="ci_jenkins",
        label="Jenkins CI",
        description="Jenkins pipeline",
        file_globs=("Jenkinsfile", "jenkins/**"),
        maps_to_steps=("G1", "E0"),
        maps_to_phases=("G", "E"),
        high_confidence_threshold=1,
    ),
    # --- Docker / Container ---
    FeatureRule(
        feature_id="docker_compose",
        label="Docker Compose",
        description="Docker Compose service definitions",
        file_globs=(
            "docker-compose*.yml", "docker-compose*.yaml",
            "compose.yml", "compose.yaml",
        ),
        maps_to_steps=("A0", "A2", "C1"),
        maps_to_phases=("A", "C"),
        high_confidence_threshold=1,
    ),
    FeatureRule(
        feature_id="dockerfile",
        label="Dockerfiles",
        description="Container build definitions",
        file_globs=("**/Dockerfile", "**/Dockerfile.*"),
        maps_to_steps=("A0", "E3"),
        maps_to_phases=("A", "E"),
    ),
    # --- MCP (Model Context Protocol) ---
    FeatureRule(
        feature_id="mcp_tools",
        label="MCP Tools",
        description="Model Context Protocol server/tool definitions",
        file_globs=(
            "**/*mcp*", "**/.claude.json", "**/mcp-proxy-config*",
            "**/*mcp_server*", "**/*mcp_tools*",
        ),
        content_patterns=(
            r"mcp_server", r"MCPServer", r"tool_definition",
            r"@mcp\.", r"mcp\.types\.",
        ),
        maps_to_steps=("A4", "A5", "C10"),
        maps_to_phases=("A", "C"),
    ),
    # --- CLI ---
    FeatureRule(
        feature_id="cli_python",
        label="Python CLI",
        description="Python CLI application (Click, Typer, argparse)",
        file_globs=(
            "**/*cli*.py", "**/*commands*.py", "**/*main*.py",
        ),
        content_patterns=(
            r"import\s+click", r"from\s+click\s+import",
            r"import\s+typer", r"from\s+typer\s+import",
            r"argparse\.ArgumentParser\(",
        ),
        maps_to_steps=("C8", "C9"),
        maps_to_phases=("C",),
    ),
    FeatureRule(
        feature_id="cli_node",
        label="Node CLI",
        description="Node.js CLI application (Commander, Yargs, Oclif)",
        file_globs=(
            "**/*cli*.ts", "**/*cli*.js", "**/bin/*",
        ),
        content_patterns=(
            r"from\s+['\"]commander['\"]", r"require\(['\"]commander['\"]\)",
            r"from\s+['\"]yargs['\"]",
        ),
        maps_to_steps=("C8", "C9"),
        maps_to_phases=("C",),
    ),
    # --- Documentation ---
    FeatureRule(
        feature_id="docs_structured",
        label="Structured Documentation",
        description="Organized documentation directory with markdown/RST",
        file_globs=("docs/**/*.md", "docs/**/*.rst"),
        maps_to_steps=("D0", "D1", "D2", "D3", "D4", "D5"),
        maps_to_phases=("D",),
        high_confidence_threshold=3,
    ),
    FeatureRule(
        feature_id="docs_api_spec",
        label="API Specification",
        description="OpenAPI/Swagger API specification",
        file_globs=(
            "**/*openapi*.yml", "**/*openapi*.yaml", "**/*openapi*.json",
            "**/*swagger*.yml", "**/*swagger*.yaml", "**/*swagger*.json",
        ),
        maps_to_steps=("C15", "D1"),
        maps_to_phases=("C", "D"),
        high_confidence_threshold=1,
    ),
    # --- Testing ---
    FeatureRule(
        feature_id="testing_python",
        label="Python Tests",
        description="Python test suite (pytest, unittest)",
        file_globs=("tests/**/*.py", "test_*.py", "**/test_*.py"),
        content_patterns=(
            r"import\s+pytest", r"from\s+pytest\s+import",
            r"class\s+Test\w+",
        ),
        maps_to_steps=("E0", "E6"),
        maps_to_phases=("E",),
    ),
    FeatureRule(
        feature_id="testing_node",
        label="Node/TS Tests",
        description="JavaScript/TypeScript test suite (Jest, Vitest, Mocha)",
        file_globs=(
            "**/*.test.ts", "**/*.test.js", "**/*.spec.ts", "**/*.spec.js",
            "**/__tests__/**",
        ),
        content_patterns=(
            r"describe\(", r"it\(", r"expect\(",
            r"from\s+['\"]vitest['\"]", r"from\s+['\"]jest['\"]",
        ),
        maps_to_steps=("E0", "E6"),
        maps_to_phases=("E",),
    ),
    # --- Package / Dependency Management ---
    FeatureRule(
        feature_id="python_packaging",
        label="Python Packaging",
        description="Python package management (pyproject.toml, setup.py, requirements.txt)",
        file_globs=(
            "pyproject.toml", "setup.py", "setup.cfg",
            "requirements*.txt", "Pipfile", "uv.lock",
        ),
        maps_to_steps=("A0", "C14", "C16"),
        maps_to_phases=("A", "C"),
        high_confidence_threshold=1,
    ),
    FeatureRule(
        feature_id="node_packaging",
        label="Node Packaging",
        description="Node.js package management (package.json, yarn, pnpm)",
        file_globs=(
            "package.json", "yarn.lock", "pnpm-lock.yaml",
            "package-lock.json", ".npmrc",
        ),
        maps_to_steps=("A0", "C16"),
        maps_to_phases=("A", "C"),
        high_confidence_threshold=1,
    ),
    FeatureRule(
        feature_id="go_packaging",
        label="Go Modules",
        description="Go module management (go.mod, go.sum)",
        file_globs=("go.mod", "go.sum"),
        maps_to_steps=("A0", "C16"),
        maps_to_phases=("A", "C"),
        high_confidence_threshold=1,
    ),
    FeatureRule(
        feature_id="rust_packaging",
        label="Rust Cargo",
        description="Rust package management (Cargo.toml)",
        file_globs=("Cargo.toml", "Cargo.lock"),
        maps_to_steps=("A0", "C16"),
        maps_to_phases=("A", "C"),
        high_confidence_threshold=1,
    ),
    # --- Infrastructure ---
    FeatureRule(
        feature_id="kubernetes",
        label="Kubernetes",
        description="Kubernetes manifests and Helm charts",
        file_globs=(
            "**/*deployment*.yaml", "**/*service*.yaml", "**/k8s/**",
            "**/helm/**", "**/charts/**", "**/*kustomization*.yaml",
        ),
        content_patterns=(
            r"apiVersion:\s+apps/v1", r"kind:\s+Deployment",
            r"kind:\s+Service",
        ),
        maps_to_steps=("E3", "E4"),
        maps_to_phases=("E",),
    ),
    FeatureRule(
        feature_id="terraform",
        label="Terraform / IaC",
        description="Infrastructure as Code (Terraform, Pulumi, CloudFormation)",
        file_globs=(
            "**/*.tf", "**/main.tf", "**/*pulumi*",
            "**/cloudformation*.yaml",
        ),
        maps_to_steps=("E3", "E4"),
        maps_to_phases=("E",),
    ),
    # --- Agent / AI Patterns ---
    FeatureRule(
        feature_id="agent_orchestration",
        label="Agent Orchestration",
        description="AI agent or bot orchestration patterns",
        file_globs=(
            "**/*agent*", "**/*orchestrat*", "**/*workflow*",
            "**/*pipeline*", "**/AGENTS.md",
        ),
        content_patterns=(
            r"class\s+\w*Agent", r"class\s+\w*Orchestrator",
            r"langchain\.", r"autogen\.", r"crewai\.",
        ),
        maps_to_steps=("C12",),
        maps_to_phases=("C",),
    ),
    # --- Plugin Systems ---
    FeatureRule(
        feature_id="plugin_system",
        label="Plugin System",
        description="Plugin/extension architecture",
        file_globs=(
            "plugins/**", "**/*plugin*.py", "**/*plugin*.ts",
            "**/*extension*.py", "**/*hook*.py",
        ),
        content_patterns=(
            r"class\s+\w*Plugin", r"register_plugin\(",
            r"load_plugins\(", r"hook_impl",
        ),
        maps_to_steps=("B0", "B1"),
        maps_to_phases=("B",),
    ),
    # --- Configuration ---
    FeatureRule(
        feature_id="config_yaml",
        label="YAML Configuration",
        description="YAML-based configuration files",
        file_globs=("config/**/*.yaml", "config/**/*.yml", "**/*config*.yaml"),
        maps_to_steps=("A0", "E0"),
        maps_to_phases=("A", "E"),
    ),
    FeatureRule(
        feature_id="config_toml",
        label="TOML Configuration",
        description="TOML-based configuration files",
        file_globs=("**/*config*.toml", "**/*.toml"),
        maps_to_steps=("A0", "E0"),
        maps_to_phases=("A", "E"),
    ),
    # --- Monitoring / Observability ---
    FeatureRule(
        feature_id="monitoring",
        label="Monitoring / Observability",
        description="Logging, metrics, tracing (Prometheus, Grafana, OpenTelemetry)",
        file_globs=(
            "**/*prometheus*", "**/*grafana*", "**/*otel*",
            "**/*opentelemetry*", "**/*datadog*",
        ),
        content_patterns=(
            r"prometheus_client", r"opentelemetry\.",
            r"from\s+datadog\s", r"metrics\.counter\(",
        ),
        maps_to_steps=("E5", "W0"),
        maps_to_phases=("E", "W"),
    ),
    # --- Dopemux-specific features (detected but flagged as domain-specific) ---
    FeatureRule(
        feature_id="dopemux_core",
        label="Dopemux Core",
        description="Dopemux-specific core components (ConPort, Dope-Memory, TaskX, ADHD Engine)",
        file_globs=(
            "**/*conport*", "**/*dope_memory*", "**/*dope-memory*",
            "**/*taskx*", "**/*task-orchestrator*", "**/*adhd*",
            "**/*dopemux*",
        ),
        content_patterns=(
            r"ConPort", r"DopeMemory", r"TaskOrchestrator",
            r"ADHDEngine", r"dopemux",
        ),
        maps_to_steps=("C3", "C4", "C5", "C11", "C13", "C17"),
        maps_to_phases=("C",),
    ),
    FeatureRule(
        feature_id="dopemux_home_control",
        label="Dopemux Home Control",
        description="Dopemux user-home control plane (~/.dopemux, ~/.config/dopemux)",
        file_globs=(
            "**/*home_control*", "**/*dotfiles*",
        ),
        content_patterns=(
            r"\.dopemux", r"\.config/dopemux",
        ),
        maps_to_steps=("H0", "H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "H9"),
        maps_to_phases=("H",),
    ),
    FeatureRule(
        feature_id="dopemux_task_packets",
        label="Dopemux Task Packets",
        description="Dopemux task packet system",
        file_globs=(
            "**/*task_packet*", "**/*task-packet*",
            "**/TASK_PACKET*.md", "task-packets/**",
        ),
        content_patterns=(
            r"TASK_PACKET", r"task.packet",
        ),
        maps_to_steps=("T0", "T1", "T2", "T3", "T4", "T5", "T9"),
        maps_to_phases=("T",),
    ),
    # --- LLM Integration ---
    FeatureRule(
        feature_id="llm_integration",
        label="LLM Integration",
        description="LLM/AI model integration (LiteLLM, OpenAI, Anthropic)",
        file_globs=(
            "**/*litellm*", "**/*openai*", "**/*anthropic*",
            "**/*llm*",
        ),
        content_patterns=(
            r"import\s+litellm", r"import\s+openai",
            r"from\s+anthropic\s", r"ChatCompletion",
        ),
        maps_to_steps=("A7", "A8"),
        maps_to_phases=("A",),
    ),
    # --- Workflow / Task Management ---
    FeatureRule(
        feature_id="task_management",
        label="Task Management",
        description="Task/project management integration (Leantime, Jira, Linear)",
        file_globs=(
            "**/*leantime*", "**/*jira*", "**/*linear*",
            "**/*project_management*",
        ),
        content_patterns=(
            r"leantime", r"jira\.", r"linear\.",
        ),
        maps_to_steps=("C5", "C11"),
        maps_to_phases=("C",),
    ),
)


def _glob_count_with_evidence(
    root: Path,
    pattern: str,
    max_hits: int = 20,
) -> List[str]:
    """Return repo-relative paths matching a glob, up to max_hits."""
    hits: List[str] = []
    try:
        for p in sorted(root.glob(pattern)):
            if p.is_file():
                try:
                    hits.append(p.resolve().relative_to(root.resolve()).as_posix())
                except ValueError:
                    continue
                if len(hits) >= max_hits:
                    break
    except Exception:
        pass
    return hits


def _content_matches(
    root: Path,
    evidence_paths: List[str],
    patterns: Tuple[str, ...],
    max_files: int = 5,
    read_limit: int = 50_000,
) -> List[str]:
    """Check file content for regex patterns. Returns evidence strings."""
    if not patterns:
        return []
    compiled = [re.compile(p) for p in patterns]
    matches: List[str] = []
    for rel in evidence_paths[:max_files]:
        fpath = root / rel
        try:
            text = fpath.read_bytes()[:read_limit].decode("utf-8", errors="ignore")
        except Exception:
            continue
        for regex in compiled:
            m = regex.search(text)
            if m:
                # find line number
                line_no = text[: m.start()].count("\n") + 1
                matches.append(f"{rel}:{line_no}")
                break
    return matches


def detect_features(
    *,
    root: Path,
    run_id: str,
    repo_fingerprint: Optional[Dict[str, Any]] = None,
    archetypes_payload: Optional[Dict[str, Any]] = None,
    extra_rules: Optional[List[FeatureRule]] = None,
) -> Dict[str, Any]:
    """Detect features in the repository.

    Returns AUTO_FEATURES.json payload with detected features,
    confidence scores, evidence, and a suggested phase plan.
    """
    rules = list(BUILTIN_RULES)
    if extra_rules:
        rules.extend(extra_rules)

    detected: List[Dict[str, Any]] = []
    feature_index: Dict[str, Dict[str, Any]] = {}

    for rule in rules:
        # Gather glob evidence
        all_evidence: List[str] = []
        scan_roots: List[str] = []

        for glob_pat in rule.file_globs:
            hits = _glob_count_with_evidence(root, glob_pat)
            all_evidence.extend(hits)

        if not all_evidence:
            continue

        # Deduplicate evidence
        all_evidence = sorted(set(all_evidence))

        # Determine scan roots from evidence (top-level directories)
        root_dirs: set[str] = set()
        for ev in all_evidence:
            parts = ev.split("/")
            if len(parts) > 1:
                root_dirs.add(parts[0] + "/")
            else:
                root_dirs.add("./")
        scan_roots = sorted(root_dirs)

        # Check content patterns for higher confidence
        content_evidence: List[str] = []
        if rule.content_patterns:
            content_evidence = _content_matches(
                root, all_evidence, rule.content_patterns
            )

        # Determine confidence
        if content_evidence and len(all_evidence) >= rule.high_confidence_threshold:
            confidence = "high"
        elif content_evidence or len(all_evidence) >= rule.high_confidence_threshold:
            confidence = "medium"
        else:
            confidence = "low"

        entry = {
            "feature_id": rule.feature_id,
            "label": rule.label,
            "description": rule.description,
            "confidence": confidence,
            "evidence": all_evidence[:10],  # cap evidence list
            "content_evidence": content_evidence[:5],
            "maps_to_steps": list(rule.maps_to_steps),
            "maps_to_phases": list(rule.maps_to_phases),
            "scan_roots": scan_roots,
            "file_count": len(all_evidence),
        }
        detected.append(entry)
        feature_index[rule.feature_id] = entry

    # Build suggested phase plan from detected features
    include_phases: set[str] = set()
    for feat in detected:
        include_phases.update(feat["maps_to_phases"])

    # Always include universal phases
    universal_phases = {"A", "D", "Q", "R", "X", "Z", "S"}
    include_phases.update(universal_phases)

    # Determine which phases to skip vs include conditionally
    all_possible = {"A", "H", "D", "C", "E", "W", "B", "G", "Q", "R", "X", "T", "Z", "S", "M"}
    skip_phases = all_possible - include_phases

    # Dopemux-specific phases skip unless dopemux features detected
    dopemux_features = {"dopemux_core", "dopemux_home_control", "dopemux_task_packets"}
    has_dopemux = bool(dopemux_features & set(feature_index.keys()))

    if not has_dopemux:
        skip_phases.update({"H", "T"})
        include_phases.discard("H")
        include_phases.discard("T")

    payload = {
        "version": "AUTO_FEATURES_V1",
        "generated_at": deterministic_generated_at(run_id),
        "run_id": run_id,
        "repo_root": str(root.resolve()),
        "detected_features": detected,
        "feature_count": len(detected),
        "feature_ids": sorted(feature_index.keys()),
        "is_dopemux_repo": has_dopemux,
        "suggested_phase_plan": {
            "include": sorted(include_phases),
            "skip": sorted(skip_phases),
        },
    }

    return payload
