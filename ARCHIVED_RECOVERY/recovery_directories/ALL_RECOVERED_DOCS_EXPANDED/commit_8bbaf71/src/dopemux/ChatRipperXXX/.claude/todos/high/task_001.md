## Task: Repository cleanup, tooling, and baseline quality gates
- **ID**: 20250906-185622
- **Priority**: High
- **Status**: DONE
- **Context**: taskmaster_migration
- **Dependencies**: None

### Description
Restructure repository, standardize tooling, enforce type/lint/test gates, and prepare for async + multi-provider architecture.

### Implementation Details
Implementation:
- Restructure to src layout
  - src/chatripper/__init__.py
  - src/chatripper/config/
  - src/chatripper/storage/
  - src/chatripper/embeddings/ (providers, cache, abstractions)
  - src/chatripper/utils/ (logging, errors, feature_flags)
  - src/chatripper/cli/
  - tests/
  - docs/
- pyproject.toml with tools:
  - python>=3.10
  - ruff>=0.6.9, mypy>=1.11, pytest>=8.3, pytest-asyncio>=0.23
  - black (optional if ruff-format), coverage[toml]>=7.6
  - type stubs: types-requests, types-setuptools as needed
- Add dependencies (pin conservative upper bounds):
  - neo4j>=5.23,<6
  - sentence-transformers>=3.2.1,<4
  - transformers>=4.44.2,<5
  - torch>=2.4.1,<2.6; platform-specific CUDA builds if GPU available
  - bitsandbytes>=0.43.3,<0.44 (optional for 4-bit quant)
  - accelerate>=1.2.1,<2 (optional)
  - cohere>=5.5.0,<6
  - httpx>=0.27,<0.28 (for any async HTTP utils)
  - pydantic>=2.8,<3; pydantic-settings>=2.4,<3
  - aiosqlite>=0.20,<0.21; blake3>=0.4,<0.5; numpy>=1.26,<3
  - structlog>=24.4,<25
  - watchdog>=4.0,<5 (for hot-swap file watch)
  - testcontainers[neo4j]>=4.7,<5 (for integration tests)
- Pre-commit hooks: ruff, mypy, pytest -q (quick subset), check-merge-conflict, end-of-file-fixer
- Add CODEOWNERS, CONTRIBUTING.md, SECURITY.md, and docs/adr/0001-repo-structure.md
- Implement feature flags via environment + pydantic-settings:
  - ALLOW_CLOUD (bool), ENABLE_SOTA (bool), DEFAULT_PROVIDER (str), FALLBACK_CHAIN (comma list)
- Structured logging with structlog, JSON logs in non-dev
- Add Makefile/justfile targets: fmt, lint, typecheck, test, cov, bench
- Set coverage fail-under to 90%
Pseudocode:
- pydantic settings
class Settings(BaseSettings):
  allow_cloud: bool = False
  enable_sota: bool = True
  default_provider: str = "stella"
  fallback_chain: list[str] = ["stella","cohere","legacy"]
  neo4j_uri: str
  neo4j_user: str
  neo4j_password: str
  model_ids: dict[str,str] = {}
settings = Settings()


### Test Strategy
- Run pre-commit across repository to ensure lint/type/test gates pass
- Verify settings load from .env and environment overrides
- Snapshot tests for logging format in dev vs prod
- Ensure coverage reports >=90% on sample tests

### Migration Notes
- Originally Task ID: 1
- Migrated from taskmaster on: 2025-09-06 18:56:22
- Priority mapping: high
- Status mapping: done
- Dependencies: []

### Related Files
- Original: .taskmaster/tasks/tasks.json
