# 1. Cache API responses on disk, keyed by (model, task, example id)

## Status

Accepted

## Context

The benchmark's "pronto" criterion is that `make benchmark` reproduces the published
results. If every run re-calls every model on every example, re-running the benchmark
(e.g. in CI, or when someone clones the repo to check the numbers) costs real money
and never guarantees the same numbers back (LLM outputs aren't fully deterministic).

## Decision

Cache every model call's raw response (text + token usage + latency) to
`evals/cache/<model>/<task>/<example_id>.json`, and commit that cache to the repo.
`run_benchmark.py` checks the cache before calling the API.

## Consequences

- Re-running `make benchmark` after the first time is free and instant.
- The published results are exactly reproducible from the committed cache.
- To get fresh numbers (e.g. after a model update), the relevant cache files must be
  deleted first — this is a deliberate, visible action rather than something that
  happens silently on every run.
