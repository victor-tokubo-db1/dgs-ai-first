# Tasks — Query Endpoint

> **Gerado por:** Dev Sênior com apoio de IA
> **Baseado em:** `specs/query-endpoint/plan.md`
> **Aprovação:** Tech Lead
> **Skills de referência:** `skills/foundation/typescript-conventions.md`, `skills/foundation/error-handling.md`, `skills/domain/azure-functions-endpoint.md`, `skills/domain/azure-ai-search-integration.md`, `skills/artifact/create-rag-endpoint.md`

---

## Visão geral

Fluxo de execução que estas tasks constroem:

```
POST /api/query
  → [T1] Tipos e contratos do domínio
  → [T2] Scaffold do endpoint e validação de input
  → [T3] Helper withRetry (backoff)
  → [T4] Serviço de embedding
  → [T5] Serviço de busca semântica
  → [T6] Montagem do prompt (context budget)
  → [T7] Chamada ao GPT-4o
  → [T8] Response builder
  → [T9] Orquestração do handler
  → [T10] Fixtures de teste
  → [T11] Testes unitários
  → [T12] Testes de integração
```

---

## T1 — Tipos e contratos do domínio

**Arquivos:** `src/shared/types.ts`, `src/shared/errors.ts`
**Skills:** `typescript-conventions.md`
**Estimativa:** P
**Dependências:** nenhuma

### Descrição

Definir todos os tipos TypeScript e custom errors que as demais tasks vão importar. Feito primeiro para que o compilador valide os contratos desde o início — nenhuma task posterior usa `any`.

### O que criar

Em `src/shared/types.ts`:
```ts
interface ChunkResult {
  content: string;
  source_document: string;
  score: number;
  vigencia: string; // ISO date
}

interface Turn {
  role: 'user' | 'assistant';
  content: string;
}

interface PromptPayload {
  systemPrompt: string;
  userMessage: string;
  history: Turn[];
  estimatedTokens: number;
}

interface QueryResponse {
  answer: string;
  source_document: string;
  confidence: 'high' | 'medium' | 'low';
  turn: number;
}
```

Em `src/shared/errors.ts`:
```ts
class AppError extends Error { constructor(message: string, public readonly code: string) }
class ValidationError extends AppError {}
class EmbeddingError extends AppError { constructor(msg, public originalError: unknown, public attempt: number) }
class SearchError extends AppError {}
class CompletionError extends AppError { constructor(msg, public statusCode: number, public estimatedTokens: number) }
```

### Critérios de aceite
- [ ] `src/shared/types.ts` compila sem erros com `strict: true`
- [ ] `src/shared/errors.ts` exporta todas as 5 classes; cada uma estende `AppError`
- [ ] Nenhum `any` explícito
- [ ] Nenhuma dependência externa — só TypeScript puro

---

## T2 — Scaffold do endpoint e validação de input

**Arquivos:** `src/functions/query/handler.ts`, `src/functions/query/validator.ts`
**Skills:** `typescript-conventions.md`, `azure-functions-endpoint.md`
**Estimativa:** P
**Dependências:** T1

### Descrição

Criar o HTTP trigger e o schema de validação Zod. Sem chamadas externas — serviços são stubs comentados. Estabelece o esqueleto que as tasks T4–T9 vão preencher.

### O que criar

`validator.ts` — schema Zod e função `validateInput`:
```ts
// Input
{ question: string (1–500 chars), conversation_id?: uuid, turn?: number (1–3) }
// Retorno discriminado
type ValidationResult = { ok: true; data: QueryInput } | { ok: false; error: string; details: ZodIssue[] }
```

`handler.ts` — Azure Functions v4:
- `app.http('query', { methods: ['POST'], authLevel: 'function', route: 'query' })`
- `request_id` via `crypto.randomUUID()` no topo do handler
- Log pino: `info` ao receber, `info` ao finalizar com `{ duration_ms }`
- Retorna 400 se `validateInput` falhar
- TODOs marcados para T4–T9 onde cada serviço será chamado
- Exportar `queryFunction` — sem default export

### Critérios de aceite
- [ ] POST com body válido → 200 (stub)
- [ ] POST com `question` ausente → 400 com `{ error, details }`
- [ ] POST com `question` de 501 chars → 400
- [ ] POST com `turn: 4` → 400
- [ ] POST com `conversation_id` malformado → 400
- [ ] `queryFunction` exportado como named export

---

## T3 — Helper `withRetry` (exponential backoff)

**Arquivo:** `src/shared/errors.ts`
**Skills:** `error-handling.md`
**Estimativa:** P
**Dependências:** T1

### Descrição

Extrair o padrão de retry num helper genérico reutilizado por T4, T5 e T7. Centralizar aqui evita duplicação e garante comportamento uniforme (backoff, jitter, logging).

### Contrato
```ts
async function withRetry<T>(
  fn: () => Promise<T>,
  options: { attempts: number; baseDelayMs: number; jitterMs: number; onRetry?: (attempt: number, error: unknown) => void }
): Promise<T>
```

### Comportamento
- Tenta `fn()` até `attempts` vezes
- Entre tentativas: `await sleep(baseDelayMs * 2^(attempt-1) + random(0, jitterMs))`
- Se todas as tentativas falharem: relança o último erro sem modificar
- `onRetry` chamado antes de cada nova tentativa (usado para logging nos serviços)

### Critérios de aceite
- [ ] Resolve na primeira tentativa se `fn` resolve
- [ ] Tenta exatamente `attempts` vezes se `fn` sempre rejeita
- [ ] Delay entre tentativas respeita a fórmula (testável com `vi.useFakeTimers`)
- [ ] `onRetry` é chamado `attempts - 1` vezes em caso de falha total
- [ ] Função é genérica — funciona com qualquer `T`

---

## T4 — Serviço de embedding

**Arquivo:** `src/services/completion.ts`
**Skills:** `typescript-conventions.md`, `error-handling.md`
**Estimativa:** M
**Dependências:** T1, T3

### Descrição

Gerar o vetor de embedding da pergunta do atendente via Azure OpenAI. Primeiro contato real com SDK externo — estabelece o padrão de retry e error handling que T7 vai replicar.

### Contrato
```ts
export async function generateEmbedding(text: string): Promise<number[]>
```

### O que implementar
- SDK: `@azure/openai`; deployment: `config.EMBEDDING_DEPLOYMENT` (`text-embedding-ada-002`)
- Retry via `withRetry` (T3): 3 tentativas, base 500 ms, jitter ±100 ms
- `onRetry`: `log.warn({ attempt }, 'embedding retry')`
- Falha definitiva: lançar `EmbeddingError(msg, originalError, attempt)`
- Sucesso: `log.debug({ dimensions: result.length }, 'embedding generated')`

### Critérios de aceite
- [ ] Retorna `number[]` para texto válido (mock do SDK)
- [ ] Lança `EmbeddingError` após 3 tentativas com falha
- [ ] `EmbeddingError.attempt` reflete o número de tentativas realizadas
- [ ] Log `warn` emitido a cada retry; `debug` emitido no sucesso
- [ ] Nenhuma chamada real ao Azure em testes (SDK mockado via `vi.mock`)

---

## T5 — Serviço de busca semântica

**Arquivo:** `src/services/search.ts`
**Skills:** `azure-ai-search-integration.md`, `error-handling.md`
**Estimativa:** M
**Dependências:** T1, T3

### Descrição

Buscar os top-5 chunks mais relevantes no Azure AI Search usando o embedding gerado em T4. Implementa também o filtro de documentos obsoletos (ADR-0003) e a ordenação por vigência.

### Contrato
```ts
export async function searchChunks(embedding: number[]): Promise<ChunkResult[]>
```

### O que implementar
- SDK: `@azure/search-documents`; índice: `config.SEARCH_INDEX`
- Parâmetros: `top: 5`, `select: ['content', 'source_document', 'vigencia', 'is_obsolete']`
- **Filtro obrigatório:** `$filter=is_obsolete eq false` — nunca retornar obsoletos (ADR-0003)
- Filtrar resultado: descartar chunks com `score < 0.75`
- Ordenar por `vigencia desc` (ADR-0003: versão mais recente tem precedência)
- Mapear para `ChunkResult[]` (definido em T1)
- Mesmo padrão de retry (T3) com `SearchError` em falha definitiva

### Critérios de aceite
- [ ] Retorna `ChunkResult[]` ordenado por `vigencia desc`
- [ ] Chunks com `score < 0.75` não aparecem no resultado
- [ ] Chunks com `is_obsolete: true` nunca aparecem no resultado
- [ ] Lança `SearchError` após retries esgotados
- [ ] SDK mockado em todos os testes; nenhuma chamada real

---

## T6 — Montagem do prompt (context budget)

**Arquivo:** `src/services/prompt-builder.ts`
**Skills:** `typescript-conventions.md`, `create-rag-endpoint.md`
**Estimativa:** M
**Dependências:** T1

### Descrição

Montar o payload de mensagens enviado ao GPT-4o respeitando o context budget definido na ADR-0002. Função pura — facilita testes unitários sem mocks.

### Contrato
```ts
export function buildPrompt(
  chunks: ChunkResult[],
  question: string,
  history: Turn[]
): PromptPayload
```

### Budget (ADR-0002)
| Slot | Limite |
|---|---|
| System prompt | ≤ 4.096 tokens |
| Chunks | ≤ 8.192 tokens |
| Histórico | máx. 3 turnos (descartar os mais antigos primeiro) |

Estimativa de tokens: `Math.ceil(text.length / 4)` — suficiente para controle de budget sem tiktoken.

### O que implementar
- Ler system prompt de `config.SYSTEM_PROMPT_PATH` (carregado no cold start, não a cada chamada)
- Se system prompt exceder 4.096 tokens: truncar e emitir `log.warn`
- Encaixar chunks até o limite de 8.192 tokens (pior caso: 5 × ~1.500 = 7.500)
- Histórico: manter os 3 turnos mais recentes
- Retornar `PromptPayload` com `estimatedTokens` = soma dos três slots

### Critérios de aceite
- [ ] `estimatedTokens` nunca excede 12.288 (4.096 + 8.192)
- [ ] System prompt truncado se exceder o limite; `log.warn` emitido
- [ ] Histórico com 4+ turnos: apenas os 3 mais recentes são incluídos
- [ ] Função sem side effects — mesma entrada sempre produz mesma saída
- [ ] Zero imports externos (puro TypeScript)

---

## T7 — Chamada ao GPT-4o com retry

**Arquivo:** `src/services/completion.ts`
**Skills:** `error-handling.md`, `create-rag-endpoint.md`
**Estimativa:** M
**Dependências:** T1, T3, T4 (reutiliza `withRetry` e o cliente OpenAI)

### Descrição

Enviar o payload montado em T6 ao GPT-4o e retornar a resposta textual. Tratamento especial para `429 RateLimitError` — respeitar o `retry-after` do Azure antes de fazer nova tentativa.

### Contrato
```ts
export async function generateCompletion(payload: PromptPayload): Promise<string>
```

### O que implementar
- Parâmetros fixos: `model: config.COMPLETION_DEPLOYMENT`, `temperature: 0`, `max_tokens: 800`
- Retry via `withRetry` (T3): 3 tentativas, base 1.000 ms, jitter ±200 ms
- Tratamento especial `429`: ler header `retry-after` (segundos) e aguardar antes do próximo ciclo
- Falha definitiva: lançar `CompletionError(msg, statusCode, payload.estimatedTokens)`
- Sucesso: retornar `choices[0].message.content` como `string`

### Critérios de aceite
- [ ] Retorna string para resposta válida do modelo (mock)
- [ ] Em `429`: aguarda `retry-after` antes de tentar novamente
- [ ] Lança `CompletionError` com `statusCode: 429` após retries esgotados
- [ ] `CompletionError.estimatedTokens` reflete o payload enviado
- [ ] SDK mockado; nenhuma chamada real

---

## T8 — Response builder

**Arquivo:** `src/functions/query/response-builder.ts`
**Skills:** `typescript-conventions.md`, `azure-functions-endpoint.md`
**Estimativa:** P
**Dependências:** T1

### Descrição

Montar o objeto de resposta HTTP a partir da resposta do modelo e dos chunks recuperados. Função pura — testável sem mocks.

### Contrato
```ts
export function buildResponse(
  answer: string,
  chunks: ChunkResult[],
  turn: number
): QueryResponse
```

### Regras de negócio
- `source_document`: `chunks[0].source_document` (chunk de maior score — já ordenado por T5)
- `confidence`: mapear score do primeiro chunk:
  - ≥ 0.90 → `'high'`
  - 0.75–0.89 → `'medium'`
  - < 0.75 → `'low'` (defensivo; filtro de T5 deve impedir este caso)
- Se `chunks` vier vazio: retornar `source_document: ''`, `confidence: 'low'`

### Critérios de aceite
- [ ] Score 0.92 → `confidence: 'high'`
- [ ] Score 0.85 → `confidence: 'medium'`
- [ ] Score 0.60 → `confidence: 'low'`
- [ ] `source_document` vem do chunk de índice 0
- [ ] Chunks vazio → resposta válida com `source_document: ''` e `confidence: 'low'`
- [ ] Função pura — sem I/O, sem side effects

---

## T9 — Orquestração do handler

**Arquivo:** `src/functions/query/handler.ts`
**Skills:** `azure-functions-endpoint.md`, `error-handling.md`
**Estimativa:** M
**Dependências:** T2, T4, T5, T6, T7, T8

### Descrição

Substituir os stubs do T2 pelas chamadas reais e implementar o mapeamento de erros para HTTP status codes. Última task de produção — o endpoint fica funcionalmente completo aqui.

### Pipeline a orquestrar
```
validateInput → generateEmbedding → searchChunks → buildPrompt → generateCompletion → buildResponse
```

### Mapeamento de erros → HTTP
| Erro | Status |
|---|---|
| `ValidationError` | 400 |
| `EmbeddingError` / `SearchError` / `CompletionError` | 502 |
| Qualquer outro | 500 |

### Log final (todos os campos obrigatórios)
```ts
log.info({ request_id, duration_ms, chunks_used: chunks.length, estimated_tokens, confidence })
```

### Critérios de aceite
- [ ] Fluxo completo retorna `QueryResponse` com todos os campos preenchidos
- [ ] `EmbeddingError` → 502 com `{ error: 'Upstream service unavailable', requestId }`
- [ ] `SearchError` → 502
- [ ] `CompletionError` → 502
- [ ] Erro inesperado → 500 sem vazar stack trace no body
- [ ] Log final emitido em todos os caminhos (sucesso e erro)

---

## T10 — Fixtures de teste

**Arquivos:** `tests/fixtures/chunks.ts`, `tests/fixtures/queries.ts`
**Skills:** `testing-patterns.md`
**Estimativa:** P
**Dependências:** T1

### Descrição

Criar os dados compartilhados que T11 e T12 vão importar. Feito antes dos testes para que ambas as tasks usem os mesmos inputs — evita fixtures divergentes.

### O que criar

`tests/fixtures/chunks.ts` — 5 `ChunkResult` com scores variados:
```ts
export const mockChunks: ChunkResult[] = [
  { content: '...', source_document: 'politica-ferias-v3.pdf', score: 0.92, vigencia: '2024-01-01' },
  { content: '...', source_document: 'beneficios-2024.pdf',    score: 0.85, vigencia: '2024-03-15' },
  { content: '...', source_document: 'rh-manual.pdf',          score: 0.78, vigencia: '2023-06-01' },
  { content: '...', source_document: 'politica-ferias-v2.pdf', score: 0.76, vigencia: '2022-01-01' },
  { content: '...', source_document: 'beneficios-2023.pdf',    score: 0.62, vigencia: '2023-01-01' },
]
```

`tests/fixtures/queries.ts` — 3 perguntas representativas do domínio NovaTech:
```ts
export const mockQueries = {
  ferias:     'Qual é a política de férias para colaboradores CLT?',
  beneficios: 'Quais são os benefícios oferecidos pela empresa?',
  reembolso:  'Como solicitar reembolso de despesas de viagem?',
}
```

### Critérios de aceite
- [ ] `mockChunks` tem exatamente 5 itens com scores distintos cobrindo os 3 níveis de `confidence`
- [ ] `mockQueries` tem exatamente 3 perguntas, todas strings não-vazias
- [ ] Ambos os arquivos compilam sem erros; zero lógica (só dados)

---

## T11 — Testes unitários

**Arquivos:** `tests/unit/query/validator.test.ts`, `tests/unit/query/prompt-builder.test.ts`, `tests/unit/query/response-builder.test.ts`
**Skills:** `testing-patterns.md`
**Estimativa:** M
**Dependências:** T2, T6, T8, T10

### Descrição

Testar as três funções puras do pipeline — as que não fazem I/O e por isso não precisam de mocks de SDK. Cobertura deve ser ≥ 80% nestas funções.

### `validator.test.ts`
- Input mínimo válido → `ok: true`
- Input completo válido → `ok: true`
- `question` ausente → `ok: false` com path `['question']`
- `question` vazia → `ok: false`
- `question` 501 chars → `ok: false`
- `turn: 0` e `turn: 4` → `ok: false`
- `turn` não-inteiro → `ok: false`
- `conversation_id` malformado → `ok: false`
- Body não-objeto → `ok: false`

### `prompt-builder.test.ts`
- 5 chunks dentro do budget → todos incluídos
- Chunks que excedem 8.192 tokens → truncamento correto (últimos descartados)
- Histórico com 4 turnos → apenas 3 mais recentes incluídos
- System prompt longo → truncado; `estimatedTokens` ≤ 12.288
- Função pura: mesma entrada → mesma saída em 3 chamadas consecutivas

### `response-builder.test.ts`
- Score 0.92 → `confidence: 'high'`
- Score 0.85 → `confidence: 'medium'`
- Score 0.62 → `confidence: 'low'`
- `source_document` = `chunks[0].source_document`
- Chunks vazio → `source_document: ''`, `confidence: 'low'`

### Critérios de aceite
- [ ] Todos os casos acima implementados e passando
- [ ] Zero mocks de SDK (funções puras não precisam)
- [ ] `npm test tests/unit` finaliza em < 2 s

---

## T12 — Testes de integração

**Arquivo:** `tests/integration/query/handler.test.ts`
**Skills:** `testing-patterns.md`, `create-integration-test.md`
**Estimativa:** G
**Dependências:** T9, T10, T11

### Descrição

Testar o handler de ponta a ponta com SDKs Azure mockados via `vi.mock`. Valida a orquestração e o mapeamento de erros — os cenários que os testes unitários não alcançam por isolarem funções puras.

### Cenários obrigatórios

| Cenário | Setup do mock | Resultado esperado |
|---|---|---|
| Sucesso completo | todos os serviços resolvem com `mockChunks[0]` e answer válido | 200 com `QueryResponse` completo |
| Embedding falha | `generateEmbedding` rejeita com `EmbeddingError` | 502 com `{ error: 'Upstream service unavailable' }` |
| Search retorna vazio | `searchChunks` resolve com `[]` | 200 com `confidence: 'low'`, `source_document: ''` |
| Completion 429 | `generateCompletion` rejeita com `CompletionError(msg, 429, N)` | 502 |
| Body inválido | body sem `question` | 400 sem chamar nenhum serviço |
| Erro inesperado | `searchChunks` lança `new Error('unexpected')` | 500 sem stack trace no body |

### Critérios de aceite
- [ ] Todos os 6 cenários implementados e passando
- [ ] Nenhuma chamada real ao Azure (verificar via `expect(mockFn).toHaveBeenCalledTimes`)
- [ ] `request_id` presente em todas as respostas de erro
- [ ] `npm test tests/integration` finaliza em < 5 s

---

## Grafo de dependências

```
T1 (tipos)
├── T2 (scaffold/validação)
├── T3 (withRetry)
│   ├── T4 (embedding)   ─┐
│   └── T5 (search)      ─┤
├── T6 (prompt builder)  ─┤→ T9 (orquestração) → T12 (integração)
├── T7 (completion)      ─┘
├── T8 (response builder)
└── T10 (fixtures) → T11 (unitários) → T12
```

Ordem sugerida para execução com 2 devs:
- **Dev A:** T1 → T2 → T6 → T8 → T10 → T11
- **Dev B:** T3 → T4 → T5 → T7
- **Juntos:** T9 → T12

---

## Definition of Done

- [ ] Todas as tasks com todos os critérios de aceite marcados ✅
- [ ] `npm test` passa sem erros
- [ ] `npm run lint` sem warnings
- [ ] Nenhum `any` explícito no código de produção
- [ ] Logs estruturados em todas as funções de serviço
- [ ] PR aprovado pelo Tech Lead com referência às tasks concluídas
