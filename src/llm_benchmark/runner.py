"""Runs the benchmark: calls each model on each task's examples, with a
filesystem cache so re-running `make benchmark` doesn't re-spend on unchanged
model/task/example combinations."""

import json
import time
from dataclasses import dataclass
from pathlib import Path

from anthropic import Anthropic

from llm_benchmark import tasks
from llm_benchmark.judge import judge_summary

MODELS = {
    "claude-opus-5": {"input": 5.00, "output": 25.00},
    "claude-sonnet-5": {"input": 2.00, "output": 10.00},
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
}

TASKS = ["intent", "extraction", "summarization"]


@dataclass
class CallResult:
    text: str
    input_tokens: int
    output_tokens: int
    latency_seconds: float


def _cache_path(cache_dir: Path, model: str, task: str, example_id: str) -> Path:
    return cache_dir / model / task / f"{example_id}.json"


def call_model(
    client: Anthropic,
    model: str,
    prompt: str,
    *,
    cache_dir: Path,
    task: str,
    example_id: str,
    max_tokens: int = 300,
) -> CallResult:
    path = _cache_path(cache_dir, model, task, example_id)
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        return CallResult(**data)

    start = time.monotonic()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    latency = time.monotonic() - start
    text = "".join(b.text for b in response.content if b.type == "text")

    result = CallResult(
        text=text,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        latency_seconds=latency,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def run_intent(client, model, examples, cache_dir) -> list[dict]:
    rows = []
    for ex in examples:
        result = call_model(
            client, model, tasks.intent_prompt(ex), cache_dir=cache_dir,
            task="intent", example_id=ex["id"], max_tokens=200,
        )
        scored = tasks.score_intent(ex, result.text)
        rows.append({**scored, "id": ex["id"], "call": result.__dict__})
    return rows


def run_extraction(client, model, examples, cache_dir) -> list[dict]:
    rows = []
    for ex in examples:
        result = call_model(
            client, model, tasks.extraction_prompt(ex), cache_dir=cache_dir,
            task="extraction", example_id=ex["id"], max_tokens=200,
        )
        scored = tasks.score_extraction(ex, result.text)
        rows.append({**scored, "id": ex["id"], "call": result.__dict__})
    return rows


def run_summarization(client, model, examples, cache_dir, *, judge_cache_dir: Path) -> list[dict]:
    rows = []
    for ex in examples:
        result = call_model(
            client, model, tasks.summarization_prompt(ex), cache_dir=cache_dir,
            task="summarization", example_id=ex["id"], max_tokens=150,
        )

        judge_path = judge_cache_dir / model / "summarization_judge" / f"{ex['id']}.json"
        if judge_path.exists():
            judgment = json.loads(judge_path.read_text(encoding="utf-8"))
        else:
            judgment = judge_summary(ex["text"], result.text, client=client)
            judge_path.parent.mkdir(parents=True, exist_ok=True)
            judge_path.write_text(
                json.dumps(judgment, ensure_ascii=False, indent=2), encoding="utf-8"
            )

        rows.append({"id": ex["id"], "judge": judgment, "call": result.__dict__})
    return rows


TASK_RUNNERS = {
    "intent": run_intent,
    "extraction": run_extraction,
    "summarization": run_summarization,
}
