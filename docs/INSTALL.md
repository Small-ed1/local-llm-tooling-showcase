# Install

## Recommended Setup

```bash
git clone https://github.com/Small-ed1/local-llm-tooling-showcase.git
cd local-llm-tooling-showcase
./install.sh
tooling-showcase serve
```

`./install.sh` can create `.venv`, use the first available `python3` or `python` that is version 3.11+, upgrade `pip`, install `.[dev]`, run tests, run the frontend JS syntax check, and prompt for benchmarking when more than three Ollama models are installed.

On Windows, run `.\install-windows.ps1` from PowerShell instead. It uses the repository folder it was launched from, validates Python 3.11+, installs `.[dev]`, and runs the test suite before handing control back.

Check the resulting environment with:

```bash
tooling-showcase doctor
```

## Manual Setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
tooling-showcase doctor
pytest tests/
node --check src/tooling_showcase/static/app-data.js
node --check src/tooling_showcase/static/markdown.js
node --check src/tooling_showcase/static/app.js
```

`pytest tests/test_browser_smoke.py` runs an optional Playwright boot check for the DOM app and skips when Playwright Chromium is not installed.

Manual Windows setup:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest tests/
tooling-showcase doctor
```

## Wheel Install Check

```bash
python -m build --wheel
python -m venv /tmp/showcase-wheel-venv
. /tmp/showcase-wheel-venv/bin/activate
pip install dist/local_llm_tooling_showcase-*.whl
tooling-showcase doctor
```

If the package is not installed in the current shell, use `PYTHONPATH=src` for CLI smoke checks:

```bash
PYTHONPATH=src python -m tooling_showcase.cli benchmark --list-models
```

## Linux Notes

Ubuntu needs Python, venv, pip, git, curl, and optionally Node/Ollama:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip git curl nodejs npm
```

Arch needs Python, git, curl, and optionally Node/Ollama:

```bash
sudo pacman -S python python-pip git curl nodejs npm
```

Ollama is optional for deterministic tools, but required for open-ended model answers and benchmarking.

## Clean Clone Verification

From a fresh clone, the release gate is:

```bash
pip install -e '.[dev]'
tooling-showcase doctor
git diff --check
node --check src/tooling_showcase/static/app-data.js
node --check src/tooling_showcase/static/markdown.js
node --check src/tooling_showcase/static/app.js
python -m compileall -q src tests
bash -n install.sh && bash -n start-servers.sh
pytest tests/
```
