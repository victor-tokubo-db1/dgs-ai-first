# Code Review — `feedback/handler.ts`

**Revisor:** Tech Lead  
**Data:** 2025  
**Arquivo analisado:** `feedback-handler.ts` (gerado pelo Copilot)  
**Local correto no repo:** `src/functions/feedback/handler.ts`  
**Veredicto:** ❌ Bloqueado para merge

---

## Resumo

| Severidade | Quantidade |
|---|---|
| 🔴 Bloqueador | 3 |
| 🟡 Aviso | 2 |
| 🔵 Melhoria | 1 |

O Copilot gerou o módulo sem o AGENTS.md no contexto. O código é funcionalmente coerente na lógica, mas ignora todas as convenções do projeto. Os três bloqueadores precisam ser corrigidos antes de qualquer aprovação — o item de PII em log é o mais crítico, pois o ambiente de staging já está ativo com 5 atendentes-piloto.

---

## 🔴 Bloqueadores

### B1 · Log de dados sensíveis com a ferramenta errada

**Arquivo:** `handler.ts` · linha 14  
**Regras violadas (AGENTS.md):** `pino para logging (nunca console.log)` · `Nunca logar dados pessoais (e-mail, nome)`

A linha abaixo viola duas regras do AGENTS.md simultaneamente: usa `console.log` em vez do logger `pino` do projeto, e serializa o objeto completo de feedback incluindo `attendantEmail` — um dado pessoal proibido nos logs.

```typescript
// ❌ Atual
console.log('Feedback recebido:', JSON.stringify(feedback));
```

```typescript
// ✅ Correção — usar o logger do projeto, sem dados pessoais
import { logger } from '../../shared/logger';

logger.info('Feedback recebido', { queryId: feedback.queryId, rating: feedback.rating });
```

---

### B2 · Nenhuma validação de input (Zod ausente)

**Arquivo:** `handler.ts` · linha 5  
**Regra violada (AGENTS.md):** `Zod para validação de input`

O body é recebido como `any` e os campos são acessados diretamente sem schema. Se `queryId` vier nulo ou `rating` vier como string, o dado é persistido corrompido no Cosmos. O AGENTS.md exige Zod em todos os endpoints — o arquivo `validator.ts` sequer foi criado.

```typescript
// ❌ Atual
const body = await request.json() as any;
const feedback = {
  queryId: body.queryId,
  rating: body.rating,
  ...
};
```

```typescript
// ✅ Correção — schema Zod em validator.ts separado, conforme Anexo C
import { FeedbackInputSchema } from './validator';

const parsed = FeedbackInputSchema.safeParse(await request.json());
if (!parsed.success) {
  return { status: 400, body: JSON.stringify(parsed.error) };
}
const feedback = parsed.data;
```

O `validator.ts` deve ser criado em `src/functions/feedback/validator.ts` com o schema Zod completo.

---

### B3 · `require()` dinâmico dentro de função async

**Arquivo:** `handler.ts` · linha 16  
**Regra violada (AGENTS.md):** `Imports estáticos no topo (nunca require dinâmico)`

`require('@azure/cosmos')` dentro do handler cria uma instância nova do `CosmosClient` a cada request — sem connection pooling, sem singleton — esgotando conexões sob carga. Além disso, é um padrão CommonJS incompatível com o projeto TypeScript/ESM.

```typescript
// ❌ Atual — dentro do handler, a cada chamada
const { CosmosClient } = require('@azure/cosmos');
const client = new CosmosClient(process.env.COSMOS_CONNECTION_STRING);
```

```typescript
// ✅ Correção — import estático no topo, singleton compartilhado
import { CosmosClient } from '@azure/cosmos';

const client = new CosmosClient(process.env.COSMOS_CONNECTION_STRING!);
```

---

## 🟡 Avisos

### A1 · Nenhum tratamento de erro no acesso ao Cosmos

**Arquivo:** `handler.ts` · linhas 17–22

Se o Cosmos estiver indisponível, o handler lança uma exceção não tratada e o Azure Functions retorna 500 sem contexto. O padrão do projeto usa custom errors e logging estruturado via `src/shared/errors.ts`.

```typescript
// ✅ Correção
try {
  await container.items.create(feedback);
  return {
    status: 201,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id: feedback.queryId }),
  };
} catch (err) {
  logger.error('Falha ao persistir feedback', { err, queryId: feedback.queryId });
  return { status: 503, body: 'Serviço indisponível' };
}
```

---

### A2 · Status HTTP incorreto na criação

**Arquivo:** `handler.ts` · linha 24

POST que cria um recurso deve retornar `201 Created`, não `200 OK`. Além disso, retornar a string `'OK'` não é JSON válido — clientes que esperam JSON vão falhar no parse.

```typescript
// ❌ Atual
return { status: 200, body: 'OK' };

// ✅ Correção
return {
  status: 201,
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ id: feedback.queryId }),
};
```

---

## 🔵 Melhoria

### M1 · Nenhum teste unitário criado junto com o módulo

O Copilot gerou apenas o handler, sem o arquivo de teste correspondente em `tests/unit/feedback/`. O projeto está em 75% de cobertura e precisa manter esse patamar. Um teste unitário deve cobrir no mínimo:

- Input inválido → retorna `400`
- Cosmos indisponível → retorna `503`
- Feedback válido → retorna `201` com o ID

Usar a skill `create-integration-test.md` como referência para o padrão de testes do projeto.

---

## Causa raiz

Todos os problemas têm origem comum: o Copilot gerou o módulo sem o AGENTS.md e sem as skills do projeto no contexto (`.mcp/mcp.json` não estava configurado apontando para `./specs` e `./skills`). O output reflete exatamente isso — lógica correta, convenções ignoradas.

## Checklist de aprovação para PRs gerados com IA

Antes de qualquer merge de código gerado por Copilot, verificar:

- [ ] O input usa Zod (ou referencia um `validator.ts`)?
- [ ] Algum `console.log` com dados de usuário?
- [ ] Imports são estáticos no topo do arquivo?
- [ ] Existe teste unitário correspondente?

Se qualquer resposta for "não" → bloqueio automático.
