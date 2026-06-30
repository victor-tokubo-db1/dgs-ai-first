---
name: typescript-conventions
description: Ative esta skill ao criar, refatorar, padronizar ou revisar codigo TypeScript para aplicar strict typing, naming conventions, type vs interface, imports/exports e proibicoes.
---

# Skill Foundation: TypeScript Conventions

## Contexto
Esta skill define as convencoes obrigatorias de TypeScript para todo o repositorio. Como skill de nivel Foundation, ela deve ser aplicada antes de skills Domain e Artifact.

Objetivo: garantir legibilidade, previsibilidade de manutencao e menor risco de regressao ao criar ou alterar codigo TypeScript em qualquer pasta do projeto.

## Regras Prescritivas

### 1) Strict typing e proibicoes
- Deve respeitar modo estrito do projeto.
- Nao deve usar any explicito.
- Nao deve usar inferencia frouxa quando o contrato pode ser declarado.

Criterio objetivo:
- Qualquer aparicao de : any em codigo novo ou alterado e nao conforme.

### 2) Naming conventions
- Deve usar PascalCase para tipos, interfaces e classes.
- Deve usar camelCase para variaveis, funcoes e metodos.
- Deve usar SCREAMING_SNAKE_CASE para constantes de ambiente.

Criterio objetivo:
- Nome de interface/tipo iniciado por minuscula e nao conforme.

### 3) Type vs Interface
- Deve usar interface para contratos de objetos externos (request/response/payload publico).
- Deve usar type para unions, intersections e aliases.

Criterio objetivo:
- Union modelada com interface e nao conforme.

### 4) Imports e exports
- Deve manter imports estaveis e sem ciclos.
- Deve preferir named exports internamente.
- Pode usar export default apenas em modulo de entry point quando necessario.

Criterio objetivo:
- Arquivo de utilitario com multiplos defaults e nao conforme.

### 5) Non-null assertion
- Nao deve usar operador ! sem comentario justificando risco e garantia de nulidade.

Criterio objetivo:
- token ! em acesso a valor potencialmente nulo sem comentario explicito e nao conforme.

### 6) Logging em producao
- Nao deve usar console.log em codigo de producao.
- Deve usar logger estruturado da camada compartilhada quando houver log operacional.

Criterio objetivo:
- Presenca de console.log em src/ e nao conforme.

## Exemplos Concretos (DO/DON'T)

### Regra 1: tipagem estrita

DON'T
```ts
export function parsePayload(payload: any) {
  return payload.query;
}
```

DO
```ts
interface QueryPayload {
  query: string;
  sessionId?: string;
}

export function parsePayload(payload: QueryPayload): string {
  return payload.query;
}
```

### Regra 2: naming

DON'T
```ts
type queryresponse = {
  answer_text: string;
};

const MAX_tokens = 8000;
```

DO
```ts
type QueryResponse = {
  answerText: string;
};

const MAX_TOKENS = 8000;
```

### Regra 3: interface vs type

DON'T
```ts
interface SearchMode {
  mode: "semantic" | "keyword";
}
```

DO
```ts
type SearchMode = "semantic" | "keyword";

interface QueryRequest {
  query: string;
  mode: SearchMode;
}
```

### Regra 4: exports

DON'T
```ts
export default function normalize(text: string) {
  return text.trim();
}

export default function sanitize(text: string) {
  return text.replace(/\s+/g, " ");
}
```

DO
```ts
export function normalize(text: string): string {
  return text.trim();
}

export function sanitize(text: string): string {
  return text.replace(/\s+/g, " ");
}
```

### Regra 5: non-null assertion

DON'T
```ts
const correlationId = request.headers.get("x-correlation-id")!;
```

DO
```ts
const correlationId = request.headers.get("x-correlation-id");
if (!correlationId) {
  throw new Error("x-correlation-id ausente");
}
```

DO (excecao justificada)
```ts
// Seguro aqui: middleware garante x-correlation-id para chamadas internas.
const correlationId = request.headers.get("x-correlation-id")!;
```

### Regra 6: logging

DON'T
```ts
console.log("Query recebida", query);
```

DO
```ts
import { logger } from "@/shared/logger";

logger.info({ query }, "Query recebida");
```

## Anti-padroes

1. Tipagem de atalho com any
- Risco: perde validacao estatic, aumenta erro em runtime.
- Correcao: declarar contrato com interface/type e retornar tipos explicitos.

2. Objeto externo modelado com type complexo sem necessidade
- Risco: dificulta leitura de contratos publicos.
- Correcao: usar interface para request/response e reservar type para unioes/aliases.

3. Export default indiscriminado em modulos internos
- Risco: dificulta refactor e padronizacao de imports.
- Correcao: usar named exports; limitar default a entry point quando exigido.

4. Non-null assertion para silenciar erro de compilacao
- Risco: quebra em runtime com valores nulos/indefinidos.
- Correcao: tratar nulo explicitamente ou documentar garantia com comentario tecnico.

5. Uso de console.log em src/
- Risco: log nao estruturado e baixa rastreabilidade operacional.
- Correcao: utilizar logger compartilhado com metadados.

## Checklist de aplicacao rapida
- Nao existe any explicito no diff.
- Nomes seguem PascalCase/camelCase/SCREAMING_SNAKE_CASE conforme contexto.
- Contratos externos usam interface; unions/aliases usam type.
- Modulos internos priorizam named exports.
- Nao ha non-null assertion sem justificativa.
- Nao ha console.log em codigo de producao.
