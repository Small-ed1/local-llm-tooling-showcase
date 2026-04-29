#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
export TOOLING_SHOWCASE_ROOT="$ROOT"
export PYTHONPATH="$ROOT/src"

ags quit -i tooling-showcase-sidebar >/dev/null 2>&1 || true

exec ags run --gtk 4 "$SCRIPT_DIR/ags/app.ts"
