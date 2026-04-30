# Install

## Recommended Setup

```bash
git clone https://github.com/Small-ed1/local-llm-tooling-showcase.git
cd local-llm-tooling-showcase
./install.sh
tooling-showcase serve
```

`./install.sh` can create `.venv`, install the package editable, run tests, run the frontend JS syntax check, and prompt for benchmarking when more than three Ollama models are installed.

## Manual Setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pytest tests/
node --check src/tooling_showcase/static/app.js
```

If the package is not installed in the current shell, use `PYTHONPATH=src` for CLI smoke checks:

```bash
PYTHONPATH=src python -m tooling_showcase.cli benchmark --list-models
```

## Linux Notes

Ubuntu needs Python, venv, pip, git, and optionally Node/Ollama:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip git nodejs npm
```

Arch needs Python, git, and optionally Node/Ollama:

```bash
sudo pacman -S python python-pip git nodejs npm
```

Ollama is optional for deterministic tools, but required for open-ended model answers and benchmarking.

## Clean Clone Verification

From a fresh clone, the release gate is:

```bash
pip install -e '.[dev]'
git diff --check
node --check src/tooling_showcase/static/app.js
python -m compileall -q src tests
bash -n install.sh && bash -n start-servers.sh
pytest tests/
```
