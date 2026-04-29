#!/bin/bash
set -euo pipefail

cd /home/small_ed/Projects/local-llm-tooling-showcase

SERVER_PORT="${SHOWCASE_SERVER_PORT:-8123}"
WRAPPER_PORT="${SHOWCASE_WRAPPER_PORT:-11436}"
OLLAMA_ENDPOINT="${SHOWCASE_OLLAMA_ENDPOINT:-http://127.0.0.1:11434/api/chat}"

pkill -f "tooling_showcase serve --host 0.0.0.0 --port ${SERVER_PORT}" 2>/dev/null || true
pkill -f "tooling_showcase serve-ollama --host 0.0.0.0 --port ${WRAPPER_PORT}" 2>/dev/null || true
sleep 1

export PYTHONPATH=src
nohup python -m tooling_showcase serve --host 0.0.0.0 --port "${SERVER_PORT}" > state/logs/server.log 2>&1 &
echo "Started server on port ${SERVER_PORT}"

nohup python -m tooling_showcase serve-ollama --host 0.0.0.0 --port "${WRAPPER_PORT}" --ollama-endpoint "${OLLAMA_ENDPOINT}" > state/logs/wrapper.log 2>&1 &
echo "Started wrapper on port ${WRAPPER_PORT}"

sleep 3
ss -tlnp | grep -E "${SERVER_PORT}|${WRAPPER_PORT}|11434"
