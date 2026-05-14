#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ask_yes_no() {
  local prompt="$1"
  local default="${2:-y}"
  local suffix="[y/N]"
  [[ "$default" == "y" ]] && suffix="[Y/n]"
  local reply
  read -r -p "$prompt $suffix " reply || reply=""
  reply="${reply:-$default}"
  [[ "$reply" =~ ^[Yy]$ ]]
}

run_if_yes() {
  local prompt="$1"
  shift
  if ask_yes_no "$prompt" "y"; then
    "$@"
  fi
}

pick_python() {
  local candidate
  for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
      "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1 && {
        printf '%s\n' "$candidate"
        return 0
      }
    fi
  done
  return 1
}

echo "Local LLM Tooling Showcase setup"
echo "Workspace: $(pwd)"

if ! PYTHON_BIN="$(pick_python)"; then
  echo "Python 3.11+ is required. Install python3.11 and python3-venv, then rerun this script."
  exit 1
fi

echo "Using Python: $PYTHON_BIN"

if ask_yes_no "Create or reuse .venv?" "y"; then
  if [[ ! -d .venv ]]; then
    "$PYTHON_BIN" -m venv .venv
  fi
  # shellcheck disable=SC1091
  . .venv/bin/activate
  PYTHON_BIN="python"
fi

run_if_yes "Upgrade pip in the current environment?" "$PYTHON_BIN" -m pip install --upgrade pip
run_if_yes "Install package with development tools?" "$PYTHON_BIN" -m pip install -e ".[dev]"
run_if_yes "Run Python tests?" "$PYTHON_BIN" -m pytest tests/

if command -v node >/dev/null 2>&1; then
  run_if_yes "Run frontend JavaScript syntax check?" node --check src/tooling_showcase/static/app.js
else
  echo "Skipping JavaScript syntax check: node not found."
fi

echo "Checking local Ollama model inventory..."
MODEL_COUNT=0
BENCHMARKED_COUNT=0
NEW_MODEL_COUNT=0
HAS_BENCHMARKS=0
MODEL_ERROR=1
while IFS='=' read -r key value; do
  case "$key" in
    MODEL_COUNT|BENCHMARKED_COUNT|NEW_MODEL_COUNT|HAS_BENCHMARKS|MODEL_ERROR)
      printf -v "$key" '%s' "$value"
      ;;
  esac
done < <("$PYTHON_BIN" -m tooling_showcase.cli benchmark --shell-summary 2>/dev/null || true)

if [[ "${MODEL_ERROR:-1}" != "0" ]]; then
  echo "Ollama model inventory is unavailable. Start Ollama and run this script again to benchmark models."
elif (( MODEL_COUNT > 3 )); then
  if (( NEW_MODEL_COUNT > 0 )); then
    echo "Detected ${MODEL_COUNT} Ollama models; ${NEW_MODEL_COUNT} have no benchmark profile yet."
    if ask_yes_no "Run benchmark suite for unbenchmarked models now?" "y"; then
      "$PYTHON_BIN" -m tooling_showcase.cli benchmark
    fi
  elif (( HAS_BENCHMARKS == 0 )); then
    echo "Detected ${MODEL_COUNT} Ollama models and no benchmark profiles."
    if ask_yes_no "Run benchmark suite now?" "y"; then
      "$PYTHON_BIN" -m tooling_showcase.cli benchmark --all
    fi
  else
    echo "Benchmark profiles are current for detected models."
  fi
else
  echo "Detected ${MODEL_COUNT} Ollama models. Benchmark prompt appears once more than 3 models are installed."
fi

echo "Setup complete. Run: tooling-showcase serve"
