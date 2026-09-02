#!/usr/bin/env bash
# Reproduce the daily lab-write-up Workbench compare without a live model.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -x "${ROOT}/.venv/bin/evidence-inspector" ]]; then
  CLI=("${ROOT}/.venv/bin/evidence-inspector")
elif command -v evidence-inspector >/dev/null 2>&1; then
  CLI=(evidence-inspector)
else
  echo "error: install the package first: python -m pip install -e '.[dev]'" >&2
  exit 2
fi

OUT="${1:-${ROOT}/acceptance/local-20260902-workbench-compare-demo}"
BUNDLE="${ROOT}/examples/daily_lab_writeup.json"
REVIEW="${ROOT}/examples/daily_lab_review.json"

mkdir -p "${OUT}"

echo "== validate =="
"${CLI[@]}" validate "${BUNDLE}"

echo "== compare fixture vs fixture-b =="
"${CLI[@]}" compare "${BUNDLE}" --out "${OUT}" --models fixture,fixture-b

OUT="${OUT}" python3 - <<'PY'
import json
import os
from pathlib import Path

out = Path(os.environ["OUT"])
report = json.loads((out / "compare.json").read_text(encoding="utf-8"))
print("compare.md:", out / "compare.md")
print("min-cost:", report["min_cost"]["selected_model_id"])
print("quality/task-fit:", report["quality_task_fit"]["selected_model_id"])
print("label verification:", report["label_verification_available"])
print("run ids:")
for row in report["models"]:
    print(f"  {row['model_id']}: {row['run_id']}")
PY

echo
echo "Read ${OUT}/compare.md then one report.md under that folder."
echo "Optional human review (replace RUN_ID with a run id printed above):"
echo "  ${CLI[*]} review RUN_ID ${REVIEW} --runs ${OUT}"
