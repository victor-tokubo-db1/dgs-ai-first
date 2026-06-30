# Árvore de Skills — NovaTech Assistant

> Hierarquia Foundation → Domain → Artifact que governa a geração consistente de código e artefatos ao longo do projeto.

---

## Visão geral

```
skills/
├── foundation/
│   ├── typescript-conventions.md
│   ├── error-handling.md
│   └── project-structure.md
├── domain/
│   ├── azure-functions-endpoint.md
│   ├── azure-ai-search-integration.md
│   ├── react-components.md
│   └── testing-patterns.md
└── artifact/
    ├── create-rag-endpoint.md
    ├── create-integration-test.md
    └── create-react-card.md
```

**Regra de dependência:** uma skill de nível superior é pré-requisito implícito para os níveis abaixo. Ao gerar um artefato com `create-rag-endpoint`, o agente deve ter lido `azure-functions-endpoint` + `azure-ai-search-integration` (Domain) e `typescript-conventions` + `error-handling` (Foundation).

---

## Foundation — Convenções globais do projeto

Skills que se aplicam a qualquer arquivo do repositório, independente de camada.

### `typescript-conventions.md`

**Propósito:** Garantir consistência em todo código TypeScript do projeto.

**Cobre:**
- `strict: true` habilitado — sem exceções
- Naming: `PascalCase` para tipos/interfaces, `camelCase` para variáveis e funções, `SCREAMING_SNAKE_CASE` para constantes de ambiente
- Imports: absolutos via path aliases (`@/services/...`, `@/shared/...`); sem imports circulares
- Exports: um `export default` por módulo de entry point; usar named exports internamente
- Uso de `type` vs `interface`: `interface` para contratos de objetos externos (requests, responses); `type` para unions, intersections e aliases
- Proibido: `any` explícito, `!` non-null assertion sem comentário justificando, `console.log` em código de produção

**Artefatos que produz:** qualquer arquivo `.ts` do projeto

---

### `error-handling.md`

**Propósito:** Tratamento de erros previsível e rastreável em todo o projeto.

**Cobre:**
- Hierarquia de custom errors em `src/shared/errors.ts`: `AppError` (base) → `ValidationError`, `SearchError`, `CompletionError`, `NotFoundError`
- Padrão `Result<T, E>`: funções que podem falhar retornam `{ ok: true, value: T } | { ok: false, error: E }` em vez de lançar exceções
- Onde usar `throw`: apenas em erros não recuperáveis (inicialização, configuração inválida)
- Logging de erros: sempre via `logger.error({ err }, mensagem)` com contexto estruturado — nunca `console.error`
- Propagação em Azure Functions: handler captura `AppError`, mapeia para HTTP status; erros desconhecidos retornam 500 com correlation ID

**Artefatos que produz:** handlers, services, qualquer função que faça I/O

---

### `project-structure.md`

**Propósito:** Definir onde cada arquivo vive e como os módulos se comunicam.

**Cobre:**
- Regras de onde criar arquivos: lógica de negócio em `src/services/`, HTTP em `src/functions/`, tipos em `src/shared/types.ts`
- `src/shared/` é o único código importável por qualquer camada — sem imports de `functions/` para `services/` e vice-versa cruzando camadas erradas
- Barrel exports (`index.ts`) apenas em `src/shared/` — não em `functions/` nem `services/`
- Fixtures de teste em `tests/fixtures/`, nunca inline nos arquivos de teste
- Variáveis de ambiente acessadas somente via `src/shared/config.ts` — nunca `process.env.X` direto no código

**Artefatos que produz:** qualquer novo módulo, reorganização de arquivos

---

## Domain — Padrões por camada técnica

Skills que definem como cada camada técnica do projeto é estruturada.

### `azure-functions-endpoint.md`

**Propósito:** Estrutura padrão para qualquer Azure Function HTTP trigger do projeto.

**Cobre:**
- Anatomia de um handler: `app.http(name, { methods, authLevel, handler })`
- Responsabilidades do handler: validar input (Zod) → chamar service → montar resposta — sem lógica de negócio no handler
- Injeção de dependências: services instanciados fora do handler (module scope) para reuso entre invocações
- authLevel padrão: `'function'` para endpoints internos; `'anonymous'` apenas para health check
- Tratamento de erros: `try/catch` no handler, mapeamento de `AppError` para status HTTP via helper `toHttpResponse(err)`
- Headers obrigatórios na resposta: `Content-Type: application/json`, `X-Correlation-Id`
- Estrutura de pastas: cada endpoint em sua própria pasta dentro de `src/functions/` com `handler.ts` + `validator.ts`

**Artefatos que produz:** qualquer endpoint em `src/functions/`

---

### `azure-ai-search-integration.md`

**Propósito:** Padrão para consultas ao índice de documentos via Azure AI Search.

**Cobre:**
- Inicialização do `SearchClient` via `src/services/search.ts` com credenciais de `config.ts`
- Parâmetros de busca padrão: `queryType: 'semantic'`, `semanticConfiguration`, `top: 5` (5 chunks conforme ADR-0002)
- Campos retornados obrigatórios: `id`, `content`, `source`, `lastModified`, `isObsolete`
- Filtro de obsolescência: sempre aplicar `$filter=isObsolete eq false` salvo override explícito
- Ordenação por vigência: documentos com `lastModified` mais recente têm score aumentado via scoring profile (ADR-0003)
- Mapeamento para `SearchResult`: tipo em `src/shared/types.ts`; nunca expor o tipo raw do SDK para o resto do código
- Tratamento de falha: `SearchError` com campo `query` para rastreamento

**Artefatos que produz:** qualquer código que consulte o índice em `src/services/search.ts`

---

### `react-components.md`

**Propósito:** Organização e padrões de componentes React do painel web.

**Cobre:**
- Estrutura de componente: `src/web/src/components/<NomeComponente>/index.tsx` + `<NomeComponente>.test.tsx`
- Props tipadas com `interface` nomeada `<NomeComponente>Props` no mesmo arquivo
- Estado local com `useState`; sem estado global (sem Redux, Zustand) nesta fase
- Estilização: Tailwind CSS utility classes — sem CSS modules, sem styled-components
- Componentes de exibição (cards, badges) são pure functions — sem side effects
- Componentes de formulário (feedback) usam controlled inputs
- Acessibilidade mínima: `aria-label` em botões icon-only, `role` semântico em regiões principais

**Artefatos que produz:** componentes em `src/web/src/components/`

---

### `testing-patterns.md`

**Propósito:** Como escrever testes consistentes em cada camada do projeto.

**Cobre:**
- Framework: Vitest (configurado em `vitest.config.ts`)
- **Unit tests** (`tests/unit/`): sem chamadas externas; todos os módulos externos mockados via `vi.mock()`; nomenclatura `describe('NomeModulo') > it('should ...')`
- **Integration tests** (`tests/integration/`): APIs externas (Azure AI Search, Azure OpenAI) interceptadas via `msw`; fixtures de `tests/fixtures/` para chunks e queries
- **E2e tests** (`tests/e2e/`): usados com cautela — consomem tokens reais; executados apenas em pipeline de staging
- Fixtures compartilhadas: `chunks.ts`, `queries.ts`, `expected-responses.ts` — nunca duplicar dados de teste inline
- Asserções: prefer `expect(result).toMatchObject(...)` para respostas parciais; `toEqual` para comparações exatas
- Cobertura mínima exigida no CI: 80% para `src/services/`, 70% para `src/functions/`

**Artefatos que produz:** qualquer arquivo de teste em `tests/unit/` ou `tests/integration/`

---

## Artifact — Receitas de geração concreta

Skills que encapsulam o passo-a-passo para gerar outputs específicos e recorrentes do projeto.

### `create-rag-endpoint.md`

**Propósito:** Receita completa para criar um endpoint que executa o pipeline RAG (search → prompt → completion).

**Depende de:** `azure-functions-endpoint`, `azure-ai-search-integration`, `typescript-conventions`, `error-handling`

**Passo a passo:**
1. Criar pasta `src/functions/<nome-endpoint>/` com `handler.ts` e `validator.ts`
2. `validator.ts`: schema Zod para o body da requisição (mínimo: `query: string`, `sessionId?: string`)
3. `handler.ts`: validar input → chamar `SearchService.query()` → chamar `PromptBuilder.build()` → chamar `CompletionService.complete()` → retornar resposta estruturada
4. Resposta padrão: `{ answer: string, sources: Source[], correlationId: string }`
5. `Source` inclui: `documentId`, `title`, `excerpt`, `lastModified`
6. Registrar o handler em `src/functions/index.ts`
7. Criar teste de integração correspondente com `create-integration-test`

**Contexto do projeto (ADR-0002):** context budget de ~8K tokens para chunks (5 × ~1.500 tokens); histórico limitado a 3 turnos; documentos obsoletos filtrados antes do search.

**Artefatos que produz:** endpoint completo com handler, validador e types

---

### `create-integration-test.md`

**Propósito:** Receita para criar teste de integração para um endpoint ou service.

**Depende de:** `testing-patterns`, `error-handling`, `project-structure`

**Passo a passo:**
1. Criar arquivo em `tests/integration/<nome-modulo>.test.ts`
2. Setup do msw: `setupServer(...handlers)` com handlers para Azure AI Search e Azure OpenAI
3. Importar fixtures de `tests/fixtures/` — nunca definir dados inline
4. Estrutura do teste: `describe` com o nome do módulo → `beforeAll` (start server) → `afterEach` (reset handlers) → `afterAll` (close server) → `it` por cenário
5. Cenários obrigatórios para endpoints RAG: resposta nominal, query sem resultados, timeout do search, resposta com documento obsoleto filtrado
6. Asserção de resposta: verificar `answer`, `sources` e `correlationId` presentes
7. Asserção de erros: verificar status HTTP e estrutura do erro retornado

**Artefatos que produz:** arquivo de teste em `tests/integration/`

---

### `create-react-card.md`

**Propósito:** Receita para criar um card de resposta ou formulário de feedback no painel web.

**Depende de:** `react-components`, `typescript-conventions`

**Passo a passo:**
1. Criar pasta `src/web/src/components/<NomeCard>/`
2. Definir `interface <NomeCard>Props` com todos os dados que o card exibe
3. Para **cards de resposta**: exibir `answer` (texto), `sources` (lista colapsável com título + excerpt), timestamp
4. Para **formulários de feedback**: inputs controlled (`thumbsUp/thumbsDown`, `comment?: string`); callback `onSubmit(feedback: FeedbackPayload): void` via prop
5. Estilização com Tailwind: container `rounded-lg border border-gray-200 p-4`, sources em `text-sm text-gray-600`
6. Acessibilidade: botões de thumbs com `aria-label="Resposta útil"` / `aria-label="Resposta não útil"`
7. Criar `<NomeCard>.test.tsx` com render test e interação básica (Vitest + React Testing Library)

**Artefatos que produz:** componente em `src/web/src/components/` com teste correspondente

---

## Mapeamento: artefato recorrente → skills necessárias

| Artefato recorrente | Skills a carregar |
|---|---|
| Novo endpoint RAG | `create-rag-endpoint` + `azure-functions-endpoint` + `azure-ai-search-integration` + `error-handling` + `typescript-conventions` |
| Teste de integração | `create-integration-test` + `testing-patterns` + `project-structure` |
| Componente React | `create-react-card` + `react-components` + `typescript-conventions` |
| Qualquer service novo | `azure-functions-endpoint` ou `azure-ai-search-integration` + `error-handling` + `typescript-conventions` |
| Qualquer arquivo novo | `project-structure` + `typescript-conventions` |
