# Benchmarking

The benchmark command scores local Ollama models by task category and writes profiles to `state/model_benchmarks.json`.

## Commands

```bash
tooling-showcase benchmark --list-models
tooling-showcase benchmark --limit-tasks 2
tooling-showcase benchmark
tooling-showcase benchmark --all
```

Default behavior benchmarks only unprofiled local models. Use `--all` only when intentionally rebuilding every profile.

## Install Flow

`./install.sh` checks local model inventory. If more than three Ollama models are installed, it prompts before running benchmarks. If inventory fails because Ollama is unavailable, setup continues and prints a clear message.

## State

Benchmark results are local ignored state. Do not commit `state/model_benchmarks.json` unless a future release intentionally adds fixture data.
