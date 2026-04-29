#!/bin/bash
set -euo pipefail

ROOT="/home/small_ed/Projects/local-llm-tooling-showcase"
export TOOLING_SHOWCASE_ROOT="$ROOT"
export PYTHONPATH="$ROOT/src"

ags quit -i tooling-showcase-sidebar >/dev/null 2>&1 || true

exec ags run --gtk 4 "$ROOT/desktop/hypr-sidebar/ags/app.ts"
