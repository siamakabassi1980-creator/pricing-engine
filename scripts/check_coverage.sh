#!/usr/bin/env bash
# Independent per-module coverage gate for the three deterministic modules.
#
# Unlike a single combined `source` + `fail_under` (whose average can hide a
# weak module behind strong ones), this runs three separate `pytest --cov`
# calls, each with its own --cov-fail-under=80. A module is gated on its OWN
# coverage, independent of the others.
#
# Usage:  bash scripts/check_coverage.sh
# Works on Git Bash (Windows), Linux, and macOS.
#
# Uses the project venv if present (see SETUP.md — always use venv python,
# not system python, or pydantic_settings etc. won't be found).

set -euo pipefail

# Locate the venv python: prefer venv/Scripts (Windows) then venv/bin (unix).
if [ -x "venv/Scripts/python.exe" ]; then
  PY="venv/Scripts/python.exe"
elif [ -x "venv/bin/python" ]; then
  PY="venv/bin/python"
else
  PY="python"
fi

THRESHOLD=80

echo "=== Independent per-module coverage gate (threshold: ${THRESHOLD}%) ==="
echo ""

# Each module is gated independently. `&&` chains them so the first failure
# stops the run (Fail Fast). The module name is the dotted import path.
for MODULE in app.decision app.anomaly app.catalog; do
  echo "--- ${MODULE} ---"
  # --cov-fail-under exits non-zero if the module's own coverage < threshold.
  # --cov-report=term-missing shows which lines/branches are uncovered.
  "$PY" -m pytest --cov="${MODULE}" \
    --cov-report=term-missing \
    --cov-fail-under="${THRESHOLD}" \
    -q
  echo ""
done

echo "=== All three modules passed the ${THRESHOLD}% gate independently. ==="
