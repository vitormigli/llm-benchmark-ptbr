FROM python:3.11-slim

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml uv.lock* README.md ./
RUN uv sync --no-install-project || true

COPY . .
RUN uv sync

CMD ["uv", "run", "python", "evals/run_benchmark.py"]
