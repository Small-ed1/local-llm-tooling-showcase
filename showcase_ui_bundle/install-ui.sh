#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-/home/small_ed/Projects/local-llm-tooling-showcase}"
BUNDLE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "${PROJECT_ROOT}/src/tooling_showcase/static"
cp "${BUNDLE_ROOT}/src/tooling_showcase/static/index.html" "${PROJECT_ROOT}/src/tooling_showcase/static/index.html"
cp "${BUNDLE_ROOT}/src/tooling_showcase/static/app.css" "${PROJECT_ROOT}/src/tooling_showcase/static/app.css"
cp "${BUNDLE_ROOT}/src/tooling_showcase/static/app.js" "${PROJECT_ROOT}/src/tooling_showcase/static/app.js"
cp "${BUNDLE_ROOT}/src/tooling_showcase/server.py" "${PROJECT_ROOT}/src/tooling_showcase/server.py"

echo "Installed Showcase UI into ${PROJECT_ROOT}"
echo "Run: cd ${PROJECT_ROOT} && PYTHONPATH=src tooling-showcase serve --host 0.0.0.0 --port 8123"
