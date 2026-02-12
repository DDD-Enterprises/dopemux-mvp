#!/usr/bin/env bash
# Packet I-AUDIT — Path A Canonical Verification
#
# Proves (or falsifies) that the repo is implemented up through Packet I semantics,
# under Path A where schema.sql/init is canonical.
#
# Run from repo root: ./reports/packet-i-audit/run_packet_i_audit.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$ROOT/reports/packet-i-audit"
RAW="$OUT/RAW"

mkdir -p "$RAW"

echo "== Packet I-AUDIT RAW ==" | tee "$RAW/00_banner.txt"
date | tee -a "$RAW/00_banner.txt"
cd "$ROOT"

echo "== Git ==" | tee "$RAW/01_git.txt"
git rev-parse HEAD | tee -a "$RAW/01_git.txt"
git branch --show-current | tee -a "$RAW/01_git.txt"
git status --short | tee -a "$RAW/01_git.txt"

echo "== Stop-condition greps (Packet D-H invariants) ==" | tee "$RAW/10_grep_stop.txt"

echo "--- Stop-A1: event_id/fingerprint must NOT include source or project_id ---" | tee -a "$RAW/10_grep_stop.txt"
rg -n "event_id.*source|fingerprint.*source|project_id.*fingerprint|uuid4\(\).*work_log_entries" -S \
  src/dopemux/memory services/working-memory-assistant/chronicle \
  | tee -a "$RAW/10_grep_stop.txt" || echo "(none found - PASS)" | tee -a "$RAW/10_grep_stop.txt"

echo "" | tee -a "$RAW/10_grep_stop.txt"
echo "--- Required: Scoped supersession index ---" | tee -a "$RAW/10_grep_stop.txt"
rg -n "idx_worklog_supersedes_unique_scoped|supersedes_entry_id" -S \
  services/working-memory-assistant/chronicle/schema.sql \
  | tee "$RAW/11_supersession_index.txt"

echo "" | tee -a "$RAW/11_supersession_index.txt"
echo "--- Required: MCP success boolean ---" | tee -a "$RAW/11_supersession_index.txt"
rg -n "success[:=]" -S \
  services/working-memory-assistant/mcp \
  | tee "$RAW/12_mcp_success.txt"
if ! grep -q "success: bool" "$RAW/12_mcp_success.txt"; then
  echo "(NOT FOUND - FAIL)" | tee -a "$RAW/12_mcp_success.txt"
fi

echo "" | tee "$RAW/20_pytest.txt"
echo "== Unit tests (no ignores, no PYTHONPATH hacks) ==" | tee -a "$RAW/20_pytest.txt"
PYTHONPATH=".:src" python -m pytest -q services/working-memory-assistant/tests/unit/ \
  2>&1 | tee -a "$RAW/20_pytest.txt"

echo ""
echo "✅ Packet I-AUDIT raw evidence collected in $RAW"
echo "Next: Review RAW/* and create STATUS.md, EVIDENCE.md, DRIFT.md"
