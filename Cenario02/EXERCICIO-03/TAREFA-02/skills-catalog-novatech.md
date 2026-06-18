# Catálogo de Skills — NovaTech Assistant

> Para cada skill: nome, frase-ativação que um agente reconheceria, quem cria, quem consome (papel + agente) e frequência de uso estimada.

---

## Foundation — Convenções globais

### `typescript-conventions`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Crie um novo arquivo TypeScript seguindo os padrões do projeto" |
| **Cria** | Tech Lead |
| **Consome (papel)** | Dev Pleno, Dev Sênior |
| **Consome (agente)** | Copilot, Claude Code |
| **Frequência** | Alta — toda sprint |

**Justificativa:** base de qualquer arquivo `.ts` gerado no projeto. É a primeira skill carregada em qualquer tarefa de código.

---

### `error-handling`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Adicione tratamento de erro a esta função / Crie um custom error" |
| **Cria** | Tech Lead |
| **Consome (papel)** | Dev Pleno, Dev Sênior |
| **Consome (agente)** | Copilot, Claude Code |
| **Frequência** | Alta — toda sprint |

**Justificativa:** qualquer função que faça I/O (endpoints, services, pipeline) precisa desta skill para tratar falhas com `AppError` e o padrão `Result<T, E>`.

---

### `project-structure`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Onde devo criar este módulo? / Organize estes arquivos seguindo a estrutura do projeto" |
| **Cria** | Tech Lead |
| **Consome (papel)** | Dev Pleno, Dev Sênior |
| **Consome (agente)** | Copilot, Claude Code |
| **Frequência** | Média — a cada 2–3 sprints |

**Justificativa:** consultada ao criar novos módulos ou reorganizar código. Após o projeto estar estruturado, é acionada com menor frequência.

---

## Domain — Padrões por camada

### `azure-functions-endpoint`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Crie um novo endpoint / Adicione um HTTP trigger ao projeto" |
| **Cria** | Dev Sênior |
| **Consome (papel)** | Dev Pleno, Dev Sênior |
| **Consome (agente)** | Copilot, Claude Code |
| **Frequência** | Alta — toda sprint |

**Justificativa:** cada um dos 5 módulos da spec gera ao menos um endpoint. É o padrão estrutural mais repetido no projeto.

---

### `azure-ai-search-integration`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Implemente a busca de documentos / Integre com o índice do Azure AI Search" |
| **Cria** | Dev Sênior |
| **Consome (papel)** | Dev Pleno, Dev Sênior |
| **Consome (agente)** | Copilot, Claude Code |
| **Frequência** | Alta — toda sprint |

**Justificativa:** o pipeline RAG depende desta integração em qualquer endpoint de query. Carregada junto com `azure-functions-endpoint` na receita `create-rag-endpoint`.

---

### `react-components`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Crie um componente React para o painel / Adicione um card ao dashboard" |
| **Cria** | Dev Sênior |
| **Consome (papel)** | Dev Pleno |
| **Consome (agente)** | Copilot, Claude Code |
| **Frequência** | Média — a cada 2–3 sprints |

**Justificativa:** escopo limitado ao módulo `painel-web`. Acionada ao criar novos componentes de visualização ou interação no dashboard.

---

### `testing-patterns`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Escreva testes para este módulo / Como devo mockar esta dependência?" |
| **Cria** | QA + Dev Sênior (co-autoria) |
| **Consome (papel)** | Dev Pleno, QA |
| **Consome (agente)** | Copilot, Claude Code |
| **Frequência** | Alta — toda sprint |

**Justificativa:** co-criada por QA (asserções e cenários) e Dev Sênior (mocks, fixtures, estrutura). Usada em paralelo com qualquer skill de artifact que produza código testável.

---

## Artifact — Receitas de geração

### `create-rag-endpoint`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Implemente o endpoint de query RAG / Crie um endpoint que busca documentos e gera resposta" |
| **Cria** | Tech Lead |
| **Consome (papel)** | Dev Pleno, Dev Sênior |
| **Consome (agente)** | Claude Code |
| **Frequência** | Alta — toda sprint |
| **Depende de** | `azure-functions-endpoint`, `azure-ai-search-integration`, `typescript-conventions`, `error-handling` |

**Justificativa:** receita mais crítica do projeto — encapsula o fluxo completo search → prompt → completion seguindo os ADRs de contexto (ADR-0002) e documentos contraditórios (ADR-0003). Usada Claude Code (não Copilot) por exigir raciocínio sobre múltiplos arquivos simultaneamente.

---

### `create-integration-test`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Crie o teste de integração para este endpoint / Escreva um teste que cobre o fluxo completo" |
| **Cria** | QA + Dev Sênior (co-autoria) |
| **Consome (papel)** | Dev Pleno, QA |
| **Consome (agente)** | Copilot, Claude Code |
| **Frequência** | Alta — toda sprint |
| **Depende de** | `testing-patterns`, `error-handling`, `project-structure` |

**Justificativa:** cada endpoint gerado com `create-rag-endpoint` exige um teste de integração correspondente. Par inseparável na prática do projeto.

---

### `create-react-card`

| Campo | Valor |
|---|---|
| **Frase-ativação** | "Crie o card de resposta / Implemente o formulário de feedback no painel" |
| **Cria** | Dev Sênior |
| **Consome (papel)** | Dev Pleno |
| **Consome (agente)** | Copilot, Claude Code |
| **Frequência** | Baixa — uma vez por fase |
| **Depende de** | `react-components`, `typescript-conventions` |

**Justificativa:** os tipos de cards do painel são limitados (resposta + feedback). Após criados, evoluem por edição — não por geração de novos artefatos. Menor rotatividade que as skills de endpoint e teste.

---

## Resumo executivo

| Skill | Nível | Cria | Frequência |
|---|---|---|---|
| `typescript-conventions` | Foundation | Tech Lead | Alta |
| `error-handling` | Foundation | Tech Lead | Alta |
| `project-structure` | Foundation | Tech Lead | Média |
| `azure-functions-endpoint` | Domain | Dev Sênior | Alta |
| `azure-ai-search-integration` | Domain | Dev Sênior | Alta |
| `react-components` | Domain | Dev Sênior | Média |
| `testing-patterns` | Domain | QA + Dev Sênior | Alta |
| `create-rag-endpoint` | Artifact | Tech Lead | Alta |
| `create-integration-test` | Artifact | QA + Dev Sênior | Alta |
| `create-react-card` | Artifact | Dev Sênior | Baixa |

**Legenda de frequência:**
- Alta — acionada toda sprint (múltiplas vezes por módulo)
- Média — acionada a cada 2–3 sprints (por fase ou grupo de módulos)
- Baixa — acionada uma vez por fase (escopo fixo e limitado)
