#!/usr/bin/env bash
set -euo pipefail
COV_MIN="${HOOKS_COV_MIN:-90}"
TEST_ARGS="${HOOKS_TEST_ARGS:--q}"
RUFF_EXIT_ZERO="${HOOKS_RUFF_EXIT_ZERO:-0}"
echo "[hooks] Running quality gates (ruff, mypy, pytest --cov>=$COV_MIN%)..." >&2
is_python_repo() {
  [[ -f pyproject.toml || -f setup.cfg || -f setup.py ]] && return 0
  ls requirements*.txt >/dev/null 2>&1 && return 0
  find tests -type f -name '*.py' >/dev/null 2>&1 && return 0
  return 1
}
if ! is_python_repo; then
  echo "[hooks] No Python project detected (skipping gates)." >&2
  exit 0
fi
if command -v ruff >/dev/null 2>&1; then
  if [[ "$RUFF_EXIT_ZERO" == "1" ]]; then ruff check --exit-zero .; else ruff check .; fi
else
  echo "[hooks] ruff not found (skipping)." >&2
fi
if command -v mypy >/dev/null 2>&1; then
  if [[ -d src ]]; then mypy src; else mypy . || true; fi
else
  echo "[hooks] mypy not found (skipping)." >&2
fi
if command -v pytest >/dev/null 2>&1; then
  TARGET="."; [[ -d src ]] && TARGET="src"
  set +e; pytest --cov="$TARGET" --cov-fail-under="${COV_MIN}" ${TEST_ARGS}; code=$?; set -e
  if [[ $code -eq 5 ]]; then echo "[hooks] pytest: no tests collected (not failing the hook)." >&2; code=0; fi
  exit $code
else
  if command -v uvx >/dev/null 2>&1; then
    TARGET="."; [[ -d src ]] && TARGET="src"
    set +e; uvx --from pytest-cov pytest --cov="$TARGET" --cov-fail-under="${COV_MIN}" ${TEST_ARGS}; code=$?; set -e
    if [[ $code -eq 5 ]]; then echo "[hooks] pytest: no tests collected (not failing the hook)." >&2; code=0; fi
    exit $code
  else
    echo "[hooks] pytest not found (skipping)." >&2
    exit 0
  fi
fi
