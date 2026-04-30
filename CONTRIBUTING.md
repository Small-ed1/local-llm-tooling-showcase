# Contributing

## Setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
tooling-showcase doctor
```

## Checks

```bash
git diff --check
node --check src/tooling_showcase/static/app.js
python -m compileall -q src tests
bash -n install.sh && bash -n start-servers.sh
python -m ruff check src tests
pytest tests/
```

## Release Hygiene

- Keep version values in `pyproject.toml` and `src/tooling_showcase/__init__.py` in sync.
- Do not commit ignored `state/` files, benchmark results, logs, event journals, local venvs, or personal paths.
- Add planner-visible tools only through `tool_protocol.py` and tests.
- Validate frontend edits with `node --check`; there is no frontend build step.
- Use `scripts/release-check.sh` before tagging.
