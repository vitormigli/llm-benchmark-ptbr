# Project instructions for Claude

This project follows the rules of the portfolio master plan:

1. No client code or data — synthetic only (see `src/llm_benchmark/datasets.py`).
2. No committed secrets — use `.env` (gitignored) and keep `.env.example` up to
   date. `gitleaks` runs on pre-commit and in CI.
3. Every project reports numeric evaluation metrics — see `evals/results.md`.
4. Everything runs with a single command: `docker compose up` or `make benchmark`.
5. README in English, with a short "Resumo em português" section at the end.
6. Small, descriptive commits using Conventional Commits.
7. Prefer simplicity — Claude API used directly via the `anthropic` SDK.

## Layout

- `src/llm_benchmark/datasets.py` — synthetic dataset generation for the 3 tasks.
- `src/llm_benchmark/tasks.py` — prompts + scoring for intent/extraction.
- `src/llm_benchmark/judge.py` — LLM-as-judge scoring for summarization.
- `src/llm_benchmark/runner.py` — model calls with filesystem caching.
- `evals/run_benchmark.py` — orchestrates a full run, writes results + chart.
- `evals/cache/` — cached API responses, committed so `make benchmark` is free to
  re-run as published.
