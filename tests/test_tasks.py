from llm_benchmark.tasks import score_extraction, score_intent


def test_score_intent_correct():
    example = {"text": "Quero cancelar", "label": "cancelamento"}
    result = score_intent(example, "cancelamento")
    assert result["correct"] is True


def test_score_intent_incorrect():
    example = {"text": "Quero cancelar", "label": "cancelamento"}
    result = score_intent(example, "elogio")
    assert result["correct"] is False


def test_score_intent_case_insensitive():
    example = {"text": "x", "label": "reclamacao"}
    result = score_intent(example, "  RECLAMACAO  ".lower())
    assert result["correct"] is True


def test_score_extraction_all_correct():
    example = {
        "label": {
            "nome_cliente": "Ana",
            "quantidade": 3,
            "produto": "kit iniciante",
            "endereco_entrega": "Rua A, 10",
            "quando": "amanhã",
        }
    }
    response = (
        '{"nome_cliente": "Ana", "quantidade": 3, "produto": "kit iniciante", '
        '"endereco_entrega": "Rua A, 10", "quando": "amanhã"}'
    )
    result = score_extraction(example, response)
    assert result["correct_fields"] == 5
    assert result["total_fields"] == 5


def test_score_extraction_handles_malformed_json():
    example = {"label": {"nome_cliente": "Ana"}}
    result = score_extraction(example, "not json at all")
    assert result["correct_fields"] == 0
    assert result["parsed"] is None


def test_score_extraction_partial_match():
    example = {"label": {"nome_cliente": "Ana", "quantidade": 3}}
    response = '{"nome_cliente": "Ana", "quantidade": 5}'
    result = score_extraction(example, response)
    assert result["correct_fields"] == 1
