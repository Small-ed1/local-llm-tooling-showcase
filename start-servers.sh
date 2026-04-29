#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
mkdir -p state/logs

SERVER_PORT="${SHOWCASE_SERVER_PORT:-8123}"
WRAPPER_PORT="${SHOWCASE_WRAPPER_PORT:-11436}"
OLLAMA_ENDPOINT="${SHOWCASE_OLLAMA_ENDPOINT:-http://127.0.0.1:11434/api/chat}"

export PYTHONPATH=src

python -m tooling_showcase serve --host 127.0.0.1 --port "$SERVER_PORT" \
  > state/logs/server.log 2>&1 &
echo "Started server on http://127.0.0.1:${SERVER_PORT}"

python -m tooling_showcase serve-ollama --host 127.0.0.1 --port "$WRAPPER_PORT" \
  --ollama-endpoint "$OLLAMA_ENDPOINT" > state/logs/wrapper.log 2>&1 &
echo "Started wrapper on http://127.0.0.1:${WRAPPER_PORT}"

wait
