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
pytest tests/
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

Before `v1.0.0`, document breaking changes from alpha in `CHANGELOG.md`.
