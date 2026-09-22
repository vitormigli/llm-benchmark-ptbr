"""LLM-as-judge scoring for the summarization task, using a fixed rubric."""

import json
import re

from anthropic import Anthropic

JUDGE_MODEL = "claude-opus-5"

RUBRIC = """Você é um avaliador de qualidade de resumos de atendimento ao cliente.

Dada a conversa original e um resumo gerado para handoff a um atendente humano, avalie
o resumo de 1 a 5 nestes critérios, e dê uma nota geral de 1 a 5:

- Cobre o problema do cliente?
- Cobre o status/resolução?
- É conciso (1-2 frases, sem informação irrelevante)?

Responda APENAS com um objeto JSON: {{"score": <1-5>, "reasoning": "<justificativa breve>"}}

Conversa original:
{conversation}

Resumo a avaliar:
{summary}
"""


def judge_summary(conversation: str, summary: str, *, client: Anthropic | None = None) -> dict:
    client = client or Anthropic()
    prompt = RUBRIC.format(conversation=conversation, summary=summary)
    response = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in response.content if b.type == "text")
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {"score": None, "reasoning": "judge did not return valid JSON", "raw": text}
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {"score": None, "reasoning": "judge JSON did not parse", "raw": text}
    return parsed
