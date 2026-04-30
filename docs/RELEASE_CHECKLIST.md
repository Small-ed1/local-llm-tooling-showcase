# Release Checklist

Run from repo root before tagging:

```bash
scripts/release-check.sh
```

Manual release flow:

```bash
git status --short
git diff --check
node --check src/tooling_showcase/static/app.js
python -m compileall -q src tests
bash -n install.sh && bash -n start-servers.sh
tooling-showcase doctor
python -m ruff check src tests
pytest tests/
```

Wheel check:

```bash
python -m build --wheel
python -m venv /tmp/showcase-wheel-venv
. /tmp/showcase-wheel-venv/bin/activate
python -m pip install dist/local_llm_tooling_showcase-*.whl
tooling-showcase doctor
```

Smoke checks:

```bash
tooling-showcase ask "find file README"
TOOLING_SHOWCASE_OLLAMA_ENABLED=false tooling-showcase ask "find file README"
tooling-showcase benchmark --list-models
```

Wrapper curl check:

```bash
tooling-showcase serve-ollama --host 127.0.0.1 --port 11436
curl -s http://127.0.0.1:11436/api/tags
```

Optional lint check after installing `.[dev]`:

```bash
python -m ruff check src tests
```

For a release archive:

```bash
git archive --format=zip --prefix="local-llm-tooling-showcase-<tag>/" --output="dist/local-llm-tooling-showcase-<tag>.zip" <tag>
```

Inspect the archive for:

- required docs and screenshots
- `install.sh`, `start-servers.sh`, and package static files
- no `state/`, `.venv/`, `.ruff_cache/`, benchmark outputs, event journals, logs, or personal paths
- no temporary transfer artifacts such as `showcase_ui_bundle/`, `model_live_note.txt`, `add_library_tools.py`, or `showcase_static_ui_patch.zip`

For `v1.0.0`, keep breaking changes and migration notes in `CHANGELOG.md`.
