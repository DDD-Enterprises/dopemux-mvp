#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[verify] profile week2 integration: unit/profile suites"
pytest -q --no-cov \
  tests/unit/test_profile_analytics.py \
  tests/unit/test_profile_cli_registration.py \
  tests/unit/test_profile_usage_analysis_command.py \
  tests/unit/test_profile_analyzer.py \
  tests/unit/test_profile_wizard.py

echo "[verify] profile week2 integration: dope-context unified search suites (asyncio backend subset)"
PYTHONPATH="$ROOT_DIR/services/dope-context" pytest -q --no-cov -k 'not trio' \
  services/dope-context/tests/test_mcp_server.py

echo "[verify] profile week2 integration: docs parity checks"
python scripts/docs_validator.py \
  docs/01-tutorials/profile-user-guide.md \
  docs/01-tutorials/profile-migration-guide.md \
  docs/02-how-to/profile-usage-3.md \
  docs/03-reference/profile-developer-guide.md \
  docs/05-audit-reports/dope-context-decision-auto-index-unified-search-verification-2026-02-06-2.md \
  docs/05-audit-reports/profile-optimization-suggestions-verification-2026-02-06-2.md \
  docs/05-audit-reports/profile-usage-analysis-and-init-wizard-verification-2026-02-06-2.md \
  docs/05-audit-reports/profile-documentation-completion-verification-2026-02-06-2.md \
  docs/05-audit-reports/conport-underrepresented-execution-packet-2026-02-06-2.md \
  docs/05-audit-reports/final-state-feature-baseline-and-execution-plan-2026-02-06-2.md

echo "[verify] profile week2 integration: PASS"
