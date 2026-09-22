"""Runs the full benchmark (3 tasks x N models), aggregates metrics, and writes
evals/results.json, evals/results.md, and evals/quality_vs_cost.png."""

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from anthropic import Anthropic
from dotenv import load_dotenv

from llm_benchmark.datasets import (
    generate_extraction_examples,
    generate_intent_examples,
    generate_summarization_examples,
)
from llm_benchmark.runner import MODELS, TASK_RUNNERS

load_dotenv()

EVALS_DIR = Path(__file__).parent
CACHE_DIR = EVALS_DIR / "cache"
N_PER_TASK = 15


def build_datasets() -> dict[str, list[dict]]:
    return {
        "intent": generate_intent_examples(n_per_label=max(1, N_PER_TASK // 6)),
        "extraction": generate_extraction_examples(n=N_PER_TASK),
        "summarization": generate_summarization_examples(n=N_PER_TASK),
    }


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    k = (len(values) - 1) * p
    f, c = int(k), min(int(k) + 1, len(values) - 1)
    if f == c:
        return values[f]
    return values[f] + (values[c] - values[f]) * (k - f)


def _cost(rows: list[dict], prices: dict) -> float:
    total = 0.0
    for r in rows:
        call = r["call"]
        total += (
            call["input_tokens"] / 1_000_000 * prices["input"]
            + call["output_tokens"] / 1_000_000 * prices["output"]
        )
    return total


def summarize_model(model: str, results: dict[str, list[dict]], prices: dict) -> dict:
    intent_rows = results["intent"]
    extraction_rows = results["extraction"]
    summary_rows = results["summarization"]

    intent_acc = sum(r["correct"] for r in intent_rows) / len(intent_rows)
    extraction_acc = sum(r["correct_fields"] for r in extraction_rows) / sum(
        r["total_fields"] for r in extraction_rows
    )
    judge_scores = [
        r["judge"]["score"]
        for r in summary_rows
        if isinstance(r["judge"].get("score"), (int, float))
    ]
    avg_judge_score = statistics.mean(judge_scores) if judge_scores else None

    # Cost is measured only for the model under test's own calls (intent, extraction,
    # summarization generation) — the judge call uses a fixed judge model and its cost
    # doesn't vary by which model is under test, so it's excluded from this comparison.
    all_rows = intent_rows + extraction_rows + summary_rows
    all_latencies = [r["call"]["latency_seconds"] for r in all_rows]
    n_calls = len(all_rows)
    total_cost = _cost(all_rows, prices)

    return {
        "intent_accuracy": intent_acc,
        "extraction_field_accuracy": extraction_acc,
        "summarization_judge_score": avg_judge_score,
        "avg_latency_seconds": statistics.mean(all_latencies),
        "p50_latency_seconds": _percentile(all_latencies, 0.5),
        "p95_latency_seconds": _percentile(all_latencies, 0.95),
        "total_cost_usd": total_cost,
        "cost_per_1000_calls_usd": (total_cost / n_calls) * 1000 if n_calls else 0,
        "n_calls": n_calls,
    }


def quality_score(summary: dict) -> float:
    """Single quality number (0-1) averaging the three task metrics, judge score
    normalized to 0-1."""
    parts = [summary["intent_accuracy"], summary["extraction_field_accuracy"]]
    if summary["summarization_judge_score"] is not None:
        parts.append(summary["summarization_judge_score"] / 5)
    return statistics.mean(parts)


def write_chart(summaries: dict[str, dict], output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 4.5))
    for model, s in summaries.items():
        ax.scatter(s["cost_per_1000_calls_usd"], quality_score(s) * 100, s=120)
        ax.annotate(model, (s["cost_per_1000_calls_usd"], quality_score(s) * 100),
                    textcoords="offset points", xytext=(8, 4))
    ax.set_xlabel("Cost per 1,000 calls (USD)")
    ax.set_ylabel("Quality score (%)")
    ax.set_title("Quality vs. cost by model")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)


def write_report(summaries: dict[str, dict], output_dir: Path) -> None:
    lines = ["# Benchmark Results", ""]
    lines.append(
        "| Model | Intent accuracy | Extraction field acc. | Summary judge score (1-5) | "
        "Cost/1000 calls | p50 latency | p95 latency |"
    )
    lines.append("|---|---|---|---|---|---|---|")
    for model, s in summaries.items():
        judge = f"{s['summarization_judge_score']:.2f}" if s["summarization_judge_score"] else "n/a"
        lines.append(
            f"| {model} | {s['intent_accuracy']:.1%} | {s['extraction_field_accuracy']:.1%} | "
            f"{judge} | ${s['cost_per_1000_calls_usd']:.2f} | "
            f"{s['p50_latency_seconds']:.2f}s | {s['p95_latency_seconds']:.2f}s |"
        )
    lines.append("")
    lines.append("![Quality vs cost](quality_vs_cost.png)")
    (output_dir / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    client = Anthropic()
    datasets = build_datasets()

    all_summaries = {}
    for model, prices in MODELS.items():
        print(f"=== {model} ===")
        results = {}
        for task_name, examples in datasets.items():
            runner = TASK_RUNNERS[task_name]
            kwargs = {"judge_cache_dir": CACHE_DIR} if task_name == "summarization" else {}
            results[task_name] = runner(client, model, examples, CACHE_DIR, **kwargs)
            print(f"  {task_name}: {len(results[task_name])} examples done")
        all_summaries[model] = summarize_model(model, results, prices)

    (EVALS_DIR / "results.json").write_text(
        json.dumps(all_summaries, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    write_chart(all_summaries, EVALS_DIR / "quality_vs_cost.png")
    write_report(all_summaries, EVALS_DIR)

    print("\n=== Summary ===")
    print(json.dumps(all_summaries, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
