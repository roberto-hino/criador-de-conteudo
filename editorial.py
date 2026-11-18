"""Model and replaceable local editorial provider."""
from typing import Protocol

TYPES = ("Apostila", "Curso", "E-book")
LEVELS = ("Introdutório", "Intermediário", "Avançado")
STAGES = (
    ("Fundamentos", "identificar conceitos e definir um objetivo de aprendizagem"),
    ("Primeiros passos", "aplicar os conceitos em uma situação simples"),
    ("Método e prática", "comparar abordagens por meio de exercícios"),
    ("Aplicações e avaliação", "avaliar resultados e planejar a aplicação"),
)


def validate_brief(data):
    if not isinstance(data, dict):
        raise ValueError("Informe os dados do material.")
    result = {}
    for key, label, limit in (("theme", "tema", 160), ("audience", "público-alvo", 200)):
        value = data.get(key)
        if not isinstance(value, str) or not 1 <= len(value.strip()) <= limit:
            raise ValueError(f"Informe {label} com até {limit} caracteres.")
        result[key] = value.strip()
    for key, label, low, high in (("pages", "páginas", 1, 500), ("count", "módulos", 1, 20)):
        value = data.get(key)
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"Informe entre {low} e {high} {label}.")
        result[key] = value
    if result["pages"] < result["count"]:
        raise ValueError("Informe ao menos uma página por módulo.")
    for key, choices in (("kind", TYPES), ("level", LEVELS)):
        if data.get(key) not in choices:
            raise ValueError("Selecione um tipo e um nível válidos.")
        result[key] = data[key]
    return result


MARKETING_EXAMPLES = (
    "Uma cafeteria quer aumentar as reservas para oficinas. Antes de publicar, ela lista as dúvidas que os clientes têm sobre moagem e escolhe a mais frequente.",
    "A cafeteria transforma a dúvida em um guia com título direto, três orientações e um convite para a oficina. Leia o título em voz alta para conferir se ele promete o que o guia entrega.",
    "A equipe adapta o guia para dois canais. No e-mail, apresenta uma dica e inclui um link. Na rede social, demonstra a dica em uma sequência de imagens.",
    "A equipe compara cliques no convite e reservas concluídas. Se houver muitos cliques e poucas reservas, ela examina a página de inscrição antes de publicar outro guia.",
)


class EditorialProvider(Protocol):
    def plan(self, brief: dict) -> list[dict]: ...
    def write(self, brief: dict, outline: list[dict]) -> list[dict]: ...
    def review(self, modules: list[dict]) -> list[dict]: ...


class DemoProvider:
    def plan(self, brief):
        pages, extra = divmod(brief["pages"], brief["count"])
        outline = []
        count = brief["count"]
        for index in range(count):
            phase = index * (len(STAGES) - 1) // max(1, count - 1)
            title, goal = STAGES[phase]
            if count > len(STAGES):
                title = f"{title} ({index + 1})"
            title = f"{title} · {brief['theme']}"
            outline.append({
                "id": index + 1,
                "title": title,
                "goal": goal,
                "pages": pages + (index < extra),
            })
        return outline

    def write(self, brief, outline):
        modules = []
        for index, item in enumerate(outline):
            bridge = "Comece registrando o que você já sabe sobre o tema."
            if index:
                previous = outline[index - 1]
                bridge = f"Retome as anotações do módulo {previous['id']} antes de avançar."
            depth = {
                "Introdutório": "Explique os termos principais em suas próprias palavras.",
                "Intermediário": "Compare duas estratégias e justifique a mais adequada ao contexto.",
                "Avançado": "Explicite suas premissas e avalie os limites da estratégia escolhida.",
            }[brief["level"]]
            exercise = (
                f"Escolha uma situação de {brief['audience']} relacionada a {brief['theme']}. "
                f"{depth} Registre uma evidência de que atingiu o objetivo do módulo."
            )
            example = ""
            if brief["theme"].casefold() == "marketing de conteúdo":
                phase = index * (len(MARKETING_EXAMPLES) - 1) // max(1, len(outline) - 1)
                example = f"\n\nExemplo\n{MARKETING_EXAMPLES[phase]}"
            content = (
                f"Objetivo\nAo final deste módulo, você poderá {item['goal']} no contexto de "
                f"{brief['theme']}.\n\n{bridge}{example}\n\nAtividade prática\n{exercise}\n\n"
                "Síntese\nAnote o que funcionou, o que precisa ser ajustado e qual será seu próximo passo."
            )
            modules.append({**item, "content": content, "approved": False})
        return modules

    def review(self, modules):
        notes = []
        for index, module in enumerate(modules):
            messages = []
            content = module["content"].strip()
            if len(content.split()) < 60:
                messages.append("Desenvolva o texto com explicações e exemplos específicos.")
            if "atividade" not in content.casefold():
                messages.append("Considere incluir uma atividade prática.")
            if index and any(other["content"].strip() == content for other in modules[:index]):
                messages.append("Este texto repete integralmente um módulo anterior.")
            notes.append({"id": module["id"], "notes": messages})
        return notes


def validate_modules(data, require_approval=False):
    if not isinstance(data, list) or not 1 <= len(data) <= 20:
        raise ValueError("Informe de 1 a 20 módulos.")
    for index, module in enumerate(data, 1):
        if not isinstance(module, dict) or type(module.get("id")) is not int or module["id"] != index:
            raise ValueError("A ordem dos módulos é inválida.")
        for key, limit in (("title", 250), ("content", 60000)):
            value = module.get(key)
            if not isinstance(value, str) or not value.strip() or len(value) > limit:
                raise ValueError(f"Confira o título e o conteúdo do módulo {index}.")
        if require_approval and module.get("approved") is not True:
            raise ValueError("Aprove todos os módulos antes de exportar.")
    return data


def validate_outline(data, brief):
    if not isinstance(data, list) or len(data) != brief["count"]:
        raise ValueError("O sumário deve conter o número de módulos do projeto.")
    for index, item in enumerate(data, 1):
        if not isinstance(item, dict) or type(item.get("id")) is not int or item["id"] != index:
            raise ValueError("A ordem do sumário é inválida.")
        for key, limit in (("title", 250), ("goal", 500)):
            value = item.get(key)
            if not isinstance(value, str) or not value.strip() or len(value) > limit:
                raise ValueError(f"Confira o título e o objetivo do módulo {index}.")
        if type(item.get("pages")) is not int or item["pages"] < 1:
            raise ValueError("A estimativa de páginas do sumário é inválida.")
    if sum(item["pages"] for item in data) != brief["pages"]:
        raise ValueError("O total estimado do sumário difere do briefing.")
    return data
