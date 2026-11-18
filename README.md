# Criador Automático de Conteúdo

Estúdio editorial web em português do Brasil para planejar, editar, revisar e exportar apostilas, cursos e e-books.

## Instalação e execução

Requisito: Python 3.10 ou superior. A versão demonstrativa usa somente a biblioteca padrão do Python e os recursos do navegador.

```sh
python3 app.py
```

Abra `http://127.0.0.1:8000` no navegador. Use **Carregar exemplo**, gere o sumário e o conteúdo, edite os módulos, envie para revisão, aprove cada módulo e baixe o arquivo Word. As alterações são guardadas no navegador atual. Alterar um módulo invalida a revisão atual e a aprovação daquele módulo. O formulário distribui as páginas estimadas pelo sumário. A paginação efetiva depende do conteúdo final e da formatação no Word.

```sh
python3 -m unittest discover -s tests -v
node --check web/app.js
```

O Node.js é opcional e serve para a checagem de sintaxe acima.

## Arquitetura

| Componente | Responsabilidade |
| --- | --- |
| `web/` | Interface, navegação editorial e persistência local de um projeto por navegador |
| `app.py` | Servidor local e rotas JSON de planejamento, geração, revisão e exportação |
| `editorial.py` | Validação e contrato `EditorialProvider`, com implementação de demonstração |
| `export.py` | Exportação do documento editorial para Word Open XML |

As rotas `POST /api/plan`, `/api/write`, `/api/review` e `/api/export` operam sobre um briefing (`theme`, `audience`, `kind`, `level`, `pages`, `count`) e uma sequência ordenada de módulos. Cada módulo de conteúdo contém `id`, `title`, `goal`, `pages`, `content` e `approved`. Um futuro adaptador de diagramação pode receber o briefing e os módulos aprovados como JSON e gerar seu próprio formato, usando a mesma fronteira que o exportador Word. O sumário exportado usa os títulos finais dos módulos.

## Etapas

1. **Implementada · Demonstração local.** Formulário, sumário automático, rascunhos por módulo com progressão e referências entre capítulos, revisão por regras, edição, aprovação e exportação.
2. **Futura · Integração editorial com IA.** Implementar outro `EditorialProvider` para planejamento especializado, capítulos extensos, controle de coerência e revisão semântica. A demonstração usa modelos de texto determinísticos, inclui um exemplo de marketing de conteúdo e não faz chamadas externas. Qualidade comercial e precisão factual exigem avaliação editorial.
3. **Futura · Diagramação e uso compartilhado.** Conectar um adaptador independente, acrescentar projetos persistidos no servidor, histórico de revisões e autenticação conforme o fluxo de trabalho.

## Credenciais e dados

A demonstração dispensa credenciais. Uma integração futura deve ler a chave no processo do servidor, por exemplo via `CONTENT_AI_API_KEY`, injetada pelo gerenciador de segredos do ambiente ou como variável de sessão local. `.env.example` documenta o nome reservado para a aplicação e arquivos `.env` reais são ignorados pelo Git. O servidor atual não lê arquivos `.env`. Mantenha valores reais fora do código, do navegador e dos logs. O servidor local embutido é destinado a desenvolvimento. Os projetos ficam no armazenamento do navegador e podem ser perdidos ao limpar os dados do site.
