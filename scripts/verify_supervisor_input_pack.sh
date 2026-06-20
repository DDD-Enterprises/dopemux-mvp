#!/usr/bin/env bash
# Verify TP-DMX-MEMORY-TRINITY-001 supervisor input pack before upload.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

ZIP="${1:-audit_inputs/TP-DMX-MEMORY-TRINITY-001-supervisor-input-pack.zip}"
INVENTORY_PATH="audit_inputs/TP-DMX-MEMORY-TRINITY-001-supervisor-input-pack/PACK_INVENTORY.json"

if [[ ! -f "$ZIP" ]]; then
  echo "FAIL: zip not found: $ZIP" >&2
  exit 1
fi

bytes=$(stat -f%z "$ZIP" 2>/dev/null || stat -c%s "$ZIP")
sha256=$(shasum -a 256 "$ZIP" | awk '{print $1}')
entries=$(unzip -l "$ZIP" | tail -1 | awk '{print $(NF-1)}')

echo "zip: $ZIP"
echo "zip_bytes: $bytes"
echo "zip_sha256: $sha256"
echo "entry_count: $entries"

# Reject known stale partial packs
if (( bytes < 120000 )); then
  echo "FAIL: zip_bytes < 120000 — stale partial pack (v1/v2). Run ./scripts/build_supervisor_input_pack.sh" >&2
  exit 1
fi

if (( entries < 44 )); then
  echo "FAIL: entry_count < 44 — missing proof/final-review/l0_membership layer" >&2
  exit 1
fi

critical=(
  "proof/TP-DMX-MEMORY-TRINITY-001/SUPERVISOR_FINAL_REVIEW.md"
  "proof/TP-DMX-MEMORY-TRINITY-001/SUPERVISOR_FINAL_REVIEW.json"
  "proof/TP-DMX-MEMORY-TRINITY-001/PR_939_LIVE_REFRESH.md"
  "proof/TP-DMX-MEMORY-TRINITY-001/PROOF.json"
  "templates/plugin/l0_membership.json"
  "audit_inputs/TP-DMX-MEMORY-TRINITY-001-supervisor-input-pack/PACK_INVENTORY.json"
  "audit_inputs/TP-DMX-MEMORY-TRINITY-001-supervisor-input-pack/D2_D3_D4_EVIDENCE.md"
  "docs/docs_index.yaml"
)

missing=()
for f in "${critical[@]}"; do
  if ! unzip -l "$ZIP" | awk '{print $4}' | grep -Fxq "$f"; then
    missing+=("$f")
  fi
done

if ((${#missing[@]} > 0)); then
  echo "FAIL: zip missing critical entries:" >&2
  printf '  - %s\n' "${missing[@]}" >&2
  exit 1
fi

if [[ -f "$INVENTORY_PATH" ]]; then
  python3 - <<'PY' "$INVENTORY_PATH" "$ZIP" "$bytes"
import hashlib, io, json, sys, zipfile
from pathlib import Path

inv_path, zip_path, zip_bytes = sys.argv[1:4]
inv = json.loads(Path(inv_path).read_text(encoding="utf-8"))
bad = [k for k, ok in inv.get("required_present", {}).items() if not ok]
if bad:
    raise SystemExit(f"FAIL: PACK_INVENTORY required_present false: {bad}")
if abs(int(inv.get("zip_bytes", 0)) - int(zip_bytes)) > 2:
    raise SystemExit(f"FAIL: PACK_INVENTORY zip_bytes mismatch ({inv.get('zip_bytes')} vs {zip_bytes})")
scope = inv.get("zip_sha256_scope", "full_zip")
exclude = "audit_inputs/TP-DMX-MEMORY-TRINITY-001-supervisor-input-pack/PACK_INVENTORY.json"
if scope == "all_entries_except_PACK_INVENTORY.json":
    buf = io.BytesIO()
    with zipfile.ZipFile(zip_path, "r") as zin, zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == exclude:
                continue
            zout.writestr(item, zin.read(item.filename))
    calc_sha = hashlib.sha256(buf.getvalue()).hexdigest()
else:
    calc_sha = hashlib.sha256(Path(zip_path).read_bytes()).hexdigest()
if inv.get("zip_sha256") != calc_sha:
    raise SystemExit(f"FAIL: PACK_INVENTORY zip_sha256 mismatch (scope={scope})")
head = inv.get("repo_head_sha", "")
print(f"PASS: critical entries present; PACK_INVENTORY aligned (head={head[:8]})")
PY
else
  echo "PASS: critical entries present (no sidecar PACK_INVENTORY.json on disk)"
fi