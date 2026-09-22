from llm_benchmark.datasets import (
    INTENT_LABELS,
    generate_extraction_examples,
    generate_intent_examples,
    generate_summarization_examples,
)


def test_generate_intent_examples_covers_all_labels():
    examples = generate_intent_examples(n_per_label=2)
    labels_seen = {ex["label"] for ex in examples}
    assert labels_seen == set(INTENT_LABELS)
    assert len(examples) == 2 * len(INTENT_LABELS)


def test_generate_intent_examples_deterministic():
    a = generate_intent_examples(n_per_label=2, seed=7)
    b = generate_intent_examples(n_per_label=2, seed=7)
    assert a == b


def test_generate_extraction_examples_shape():
    examples = generate_extraction_examples(n=5)
    assert len(examples) == 5
    for ex in examples:
        assert set(ex["label"].keys()) == {
            "nome_cliente",
            "quantidade",
            "produto",
            "endereco_entrega",
            "quando",
        }


def test_generate_summarization_examples_shape():
    examples = generate_summarization_examples(n=3)
    assert len(examples) == 3
    for ex in examples:
        assert "text" in ex and ex["text"]
