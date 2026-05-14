#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

git diff --check
node --check src/tooling_showcase/static/app-data.js
node --check src/tooling_showcase/static/markdown.js
node --check src/tooling_showcase/static/app.js
python -m compileall -q src tests
bash -n install.sh
bash -n start-servers.sh
PYTHONPATH=src python -m tooling_showcase.cli doctor
pytest tests/

if python -m ruff --version >/dev/null 2>&1; then
  python -m ruff check src tests
else
  echo "ruff not installed; install with pip install -e '.[dev]' to run lint locally."
fi

if git ls-files | grep -E '(^state/|^dist/|\.venv/|\.ruff_cache/|events\.jsonl|model_benchmarks\.json|model_live_note\.txt|add_library_tools\.py|showcase_static_ui_patch\.zip|showcase_ui_bundle/)' >/dev/null; then
  echo "Release-blocking tracked local artifact detected." >&2
  exit 1
fi

echo "Release checks passed."
