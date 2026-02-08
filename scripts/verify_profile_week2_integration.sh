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
  docs/02-how-to/PROFILE-USAGE.md \
  docs/03-reference/profile-developer-guide.md \
  docs/05-audit-reports/DOPE_CONTEXT_DECISION_AUTO_INDEX_UNIFIED_SEARCH_VERIFICATION_2026-02-06.md \
  docs/05-audit-reports/PROFILE_OPTIMIZATION_SUGGESTIONS_VERIFICATION_2026-02-06.md \
  docs/05-audit-reports/PROFILE_USAGE_ANALYSIS_AND_INIT_WIZARD_VERIFICATION_2026-02-06.md \
  docs/05-audit-reports/PROFILE_DOCUMENTATION_COMPLETION_VERIFICATION_2026-02-06.md \
  docs/05-audit-reports/CONPORT_UNDERREPRESENTED_EXECUTION_PACKET_2026-02-06.md \
  docs/05-audit-reports/FINAL_STATE_FEATURE_BASELINE_AND_EXECUTION_PLAN_2026-02-06.md

echo "[verify] profile week2 integration: PASS"
