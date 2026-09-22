"""Synthetic dataset generation for the three benchmark tasks. All content is
generated (Faker pt-BR + templates) — no real customer messages."""

import random

from faker import Faker

fake = Faker("pt_BR")

INTENT_LABELS = [
    "duvida_produto",
    "reclamacao",
    "elogio",
    "cancelamento",
    "suporte_tecnico",
    "financeiro",
]

PRODUCTS = [
    "plano premium",
    "assinatura mensal",
    "produto X200",
    "kit iniciante",
    "serviço de entrega",
    "aplicativo",
    "pedido",
    "curso online",
]

INTENT_TEMPLATES: dict[str, list[str]] = {
    "duvida_produto": [
        "Oi, o {produto} funciona também no fim de semana?",
        "Vocês têm o {produto} disponível em outras cores?",
        "Quero saber mais sobre o {produto} antes de comprar.",
        "O {produto} é compatível com Android?",
    ],
    "reclamacao": [
        "Meu {produto} chegou quebrado, isso é um absurdo.",
        "Já é a segunda vez que o {produto} apresenta o mesmo problema.",
        "Estou muito insatisfeito com o atendimento sobre o {produto}.",
        "O {produto} que recebi não é o que eu pedi.",
    ],
    "elogio": [
        "Só passando pra dizer que o {produto} superou minhas expectativas!",
        "Atendimento excelente, o {produto} chegou antes do prazo.",
        "Parabéns pela qualidade do {produto}, recomendo demais.",
        "Adorei o {produto}, com certeza vou comprar de novo.",
    ],
    "cancelamento": [
        "Quero cancelar minha assinatura do {produto} imediatamente.",
        "Não preciso mais do {produto}, como faço pra cancelar?",
        "Por favor cancelem meu {produto}, não vou renovar.",
        "Gostaria de encerrar o contrato do {produto} esse mês.",
    ],
    "suporte_tecnico": [
        "O {produto} não está abrindo, aparece uma tela em branco.",
        "Não consigo fazer login pra usar o {produto}.",
        "O {produto} trava toda vez que eu tento salvar.",
        "Estou com erro 500 ao acessar o {produto}.",
    ],
    "financeiro": [
        "Fui cobrado duas vezes pelo {produto} esse mês.",
        "Não reconheço essa cobrança do {produto} no meu cartão.",
        "Quero uma segunda via do boleto do {produto}.",
        "Meu pagamento do {produto} não foi processado, podem verificar?",
    ],
}


def generate_intent_examples(n_per_label: int, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    examples = []
    idx = 0
    for label in INTENT_LABELS:
        templates = INTENT_TEMPLATES[label]
        for _ in range(n_per_label):
            template = rng.choice(templates)
            produto = rng.choice(PRODUCTS)
            text = template.format(produto=produto)
            examples.append({"id": f"intent_{idx:03d}", "text": text, "label": label})
            idx += 1
    rng.shuffle(examples)
    return examples


EXTRACTION_TEMPLATES = [
    "Oi, meu nome é {nome} e queria {quantidade} unidades de {produto} "
    "entregues em {endereco} {quando}.",
    "Olá, sou {nome}. Preciso de {quantidade}x {produto} pra {endereco}, "
    "se possível {quando}.",
    "{nome} aqui! Pode me mandar {quantidade} {produto} pro endereço "
    "{endereco}? Prefiro {quando}.",
    "Bom dia, gostaria de pedir {quantidade} {produto}. Entregar em "
    "{endereco}, {quando} está bom.",
]

WHEN_OPTIONS = ["amanhã", "ainda hoje", "na sexta-feira", "no próximo sábado", "essa semana"]


def generate_extraction_examples(n: int, seed: int = 42) -> list[dict]:
    fake.seed_instance(seed)
    rng = random.Random(seed)
    examples = []
    for i in range(n):
        nome = fake.first_name()
        quantidade = rng.randint(1, 6)
        produto = rng.choice(PRODUCTS)
        endereco = fake.street_address()
        quando = rng.choice(WHEN_OPTIONS)
        template = rng.choice(EXTRACTION_TEMPLATES)
        text = template.format(
            nome=nome, quantidade=quantidade, produto=produto, endereco=endereco, quando=quando
        )
        examples.append(
            {
                "id": f"extraction_{i:03d}",
                "text": text,
                "label": {
                    "nome_cliente": nome,
                    "quantidade": quantidade,
                    "produto": produto,
                    "endereco_entrega": endereco,
                    "quando": quando,
                },
            }
        )
    return examples


CONVERSATION_ISSUES = [
    (
        "acesso",
        [
            "Cliente: Não consigo entrar na minha conta, esqueci a senha.",
            "Atendente: Sem problemas, vou te enviar um link de redefinição por e-mail.",
            "Cliente: Recebi, já troquei a senha e consegui entrar. Obrigado!",
        ],
    ),
    (
        "cobrança",
        [
            "Cliente: Fui cobrado duas vezes esse mês no meu cartão.",
            "Atendente: Verifiquei aqui e realmente houve uma duplicidade, peço desculpas.",
            "Atendente: Já solicitei o estorno, deve cair em até 5 dias úteis.",
            "Cliente: Ok, vou aguardar o estorno então.",
        ],
    ),
    (
        "entrega",
        [
            "Cliente: Meu pedido deveria ter chegado ontem e não chegou.",
            "Atendente: Peço desculpas pelo atraso, vou verificar com a transportadora.",
            "Atendente: O pedido está a caminho, previsão de chegada é amanhã.",
            "Cliente: Tudo bem, vou aguardar até amanhã então.",
        ],
    ),
    (
        "produto com defeito",
        [
            "Cliente: O produto que recebi veio com um defeito na tela.",
            "Atendente: Sinto muito, vamos providenciar a troca sem custo.",
            "Atendente: Já gerei a etiqueta de devolução, chega no seu e-mail.",
            "Cliente: Perfeito, muito obrigado pela agilidade.",
        ],
    ),
]


def generate_summarization_examples(n: int, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    examples = []
    for i in range(n):
        issue, base_lines = rng.choice(CONVERSATION_ISSUES)
        conversation = "\n".join(base_lines)
        examples.append(
            {
                "id": f"summary_{i:03d}",
                "text": conversation,
                "label": {"issue_topic": issue},
            }
        )
    return examples
