.PHONY: benchmark test lint

benchmark:
	uv run python evals/run_benchmark.py

test:
	uv run pytest

lint:
	uv run ruff check .
