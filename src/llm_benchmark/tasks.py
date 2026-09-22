"""Prompt construction and scoring for the three benchmark tasks."""

import json
import re

from llm_benchmark.datasets import INTENT_LABELS

# ---------------------------------------------------------------------------
# Task 1: intent classification
# ---------------------------------------------------------------------------


def intent_prompt(example: dict) -> str:
    labels = ", ".join(INTENT_LABELS)
    return (
        "Classifique a intenção da seguinte mensagem de atendimento ao cliente em "
        f"português. Responda APENAS com um destes rótulos, exatamente como escrito: "
        f"{labels}.\n\nMensagem: {example['text']}"
    )


def score_intent(example: dict, response_text: str) -> dict:
    cleaned = response_text.strip().lower()
    predicted = next((label for label in INTENT_LABELS if label in cleaned), None)
    correct = predicted == example["label"]
    return {"correct": correct, "predicted": predicted, "expected": example["label"]}


# ---------------------------------------------------------------------------
# Task 2: free-text field extraction
# ---------------------------------------------------------------------------


def extraction_prompt(example: dict) -> str:
    return (
        "Extraia os seguintes campos da mensagem abaixo e responda APENAS com um "
        "objeto JSON, sem nenhum texto adicional: nome_cliente (string), "
        "quantidade (número inteiro), produto (string), endereco_entrega (string), "
        "quando (string, expressão de tempo como dita no texto).\n\n"
        f"Mensagem: {example['text']}"
    )


def _extract_json(text: str) -> dict | None:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def score_extraction(example: dict, response_text: str) -> dict:
    parsed = _extract_json(response_text)
    expected = example["label"]
    if parsed is None:
        return {"correct_fields": 0, "total_fields": len(expected), "parsed": None}

    correct = 0
    for key, exp_val in expected.items():
        act_val = parsed.get(key)
        if isinstance(exp_val, str) and isinstance(act_val, str):
            if exp_val.strip().lower() == act_val.strip().lower():
                correct += 1
        elif exp_val == act_val:
            correct += 1
    return {"correct_fields": correct, "total_fields": len(expected), "parsed": parsed}


# ---------------------------------------------------------------------------
# Task 3: conversation summarization (scored separately by judge.py)
# ---------------------------------------------------------------------------


def summarization_prompt(example: dict) -> str:
    return (
        "Resuma a conversa de atendimento abaixo em 1 a 2 frases, em português, "
        "como uma nota de handoff para outro atendente humano assumir o caso. "
        "Inclua o problema do cliente e o status/resolução. Responda apenas com o "
        f"resumo, sem texto adicional.\n\nConversa:\n{example['text']}"
    )
