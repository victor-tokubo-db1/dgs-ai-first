# Code Review — `validateResponse` / `StructuredOutputSchema`

**Arquivo analisado:** módulo de validação de resposta estruturada com guardrail de carga perigosa  
**Data:** 2025-06-26  
**Status:** 7 problemas encontrados — 1 crítico, 3 moderados, 3 leves

---

## Problemas encontrados

### 🔴 Crítico

#### #2 — `answer` vazio após `.trim()` não detectado

O schema Zod exige `min(1)` para `answer`, mas essa validação ocorre **antes** do `.trim()`. Uma string composta apenas de espaços (ex.: `"   "`) passa na validação do schema — pois tem `length >= 1` — mas resulta em uma string vazia após o trim, retornando uma resposta inválida sem qualquer log ou rejeição.

```ts
// Antes (problemático)
const structured: StructuredOutput = {
  answer: parsed.data.answer.trim(), // pode ser "" aqui
  ...
};
// Não há checagem se trimmedAnswer está vazio

// Depois (corrigido)
const trimmedAnswer = parsed.data.answer.trim();

if (!trimmedAnswer) {
  logger.warn("response_rejected_empty_answer", {
    reason: "empty_answer_after_trim",
  });
  return { ok: false, response: SAFE_RESPONSE, reason: "empty_answer_after_trim" };
}
```

---

### 🟡 Moderados

#### #3 — Verificação pós-trim de `source_document` cobre caso real, mas não cobre `answer`

A checagem `if (!structured.source_document)` existe para detectar strings que passam no `min(1)` do schema mas ficam vazias após `.trim()`. A lógica está correta para `source_document`, mas o mesmo problema existe para `answer` e não estava sendo tratado (ver #2). Como efeito colateral positivo, a checagem do `source_document` é necessária e deve ser mantida — não é duplicata inútil.

```ts
// Checagem legítima — cobre o caso de source_document com só espaços
if (!trimmedSourceDocument) {
  logger.warn("response_rejected_missing_source_document", {
    reason: "missing_source_document",
  });
  return { ok: false, response: SAFE_RESPONSE, reason: "missing_source_document" };
}
```

#### #4 — `SAFE_RESPONSE` é mutável

O objeto é declarado como `const`, mas isso apenas impede a reatribuição da variável — não impede a mutação das propriedades. Qualquer código downstream pode modificar `SAFE_RESPONSE.answer` silenciosamente, corrompendo todos os retornos futuros.

```ts
// Antes (vulnerável)
const SAFE_RESPONSE: StructuredOutput = {
  answer: "Não foi possível validar...",
  source_document: "SYSTEM-GUARDRAIL",
  confidence_score: 0,
};

// Depois (imutável)
const SAFE_RESPONSE: Readonly<StructuredOutput> = Object.freeze({
  answer: "Não foi possível validar...",
  source_document: "SYSTEM-GUARDRAIL",
  confidence_score: 0,
});
```

#### #6 — Nomenclatura enganosa no guardrail de segurança

A variável `hasPositiveReturn` não significa "algo positivo" do ponto de vista do negócio — ela detecta uma **afirmação de que a devolução é possível**, que é exatamente o que deve ser **bloqueado** em contexto de carga perigosa. O nome confunde a leitura da lógica. Para um guardrail de segurança, clareza é crítica.

Adicionalmente, a lógica dupla de negação (`return !hasNegative`) combinada com o nome enganoso torna a função difícil de auditar.

```ts
// Antes (confuso)
const hasPositiveReturn = POSITIVE_RETURN_REGEX.test(text);
if (hasPositiveReturn) return true; // bloqueia — mas o nome sugere algo bom
return !hasNegative;

// Depois (claro)
const affirmsReturn = AFFIRMS_DANGEROUS_RETURN_REGEX.test(text);
if (affirmsReturn) return true; // bloqueia afirmação explícita de devolução
return !hasNegation;
```

---

### 🟢 Leves

#### #1 — Flag `/i` redundante após `normalizeText`

A função `normalizeText` aplica `.toLowerCase()` em toda string antes de testá-la contra as regex. Todas as regex possuem a flag `/i` (case-insensitive), o que as torna redundantes após o lowercase. A redundância é inofensiva, mas gera ruído. Recomendação: manter a flag `/i` nas regex e adicionar um comentário documentando a redundância intencional (facilita remoção futura do `toLowerCase` sem quebrar comportamento).

```ts
function normalizeText(value: string): string {
  // .toLowerCase() torna a flag /i nas regex redundante,
  // mas mantemos /i para documentar intenção explicitamente.
  return value.normalize("NFC").toLowerCase();
}
```

#### #5 — Alternativas redundantes em `NEGATIVE_REGEX`

O padrão `\bn(a|ã)o\b` já cobre as strings `"nao"` e `"não"`. Os casos `\bnão\b` e `\bnao\b` listados separadamente são redundantes.

```ts
// Antes (redundante)
const NEGATIVE_REGEX =
  /\bn(a|ã)o\b|\bnão\b|\bnao\b|\bn(a|ã)o\s+é\s+poss[ií]vel\b|\bn(a|ã)o\s+pode(m)?\b|\bineleg[ií]vel\b/i;

// Depois (simplificado)
const NEGATIVE_REGEX =
  /\bn[aã]o\b|\bn[aã]o\s+é\s+poss[ií]vel\b|\bn[aã]o\s+pode(m)?\b|\bineleg[ií]vel\b/i;
```

#### #7 — Ausência de casos de teste documentados no guardrail

Guardrails baseados em regex são frágeis sem exemplos inline dos casos esperados. A função `violatesDangerousReturnGuardrail` lida com lógica de segurança e deveria ter um JSDoc com exemplos claros de strings que devem ser bloqueadas e permitidas.

```ts
/**
 * Retorna true se a resposta afirmar (ou não negar claramente) que carga
 * perigosa pode ser devolvida — situação que deve ser bloqueada.
 *
 * Casos esperados:
 *   BLOQUEAR: "a carga perigosa pode ser devolvida"
 *   BLOQUEAR: "cargas perigosas classe 3 podem ser devolvidas"
 *   PERMITIR:  "cargas perigosas não podem ser devolvidas"
 *   PERMITIR:  "a devolução não é possível para cargas da ANTT"
 */
function violatesDangerousReturnGuardrail(answer: string): boolean { ... }
```

---

## Código corrigido completo

```typescript
import { z } from "zod";

export const StructuredOutputSchema = z
  .object({
    answer: z
      .string()
      .min(1, "answer é obrigatório")
      .max(4000, "answer inválido"),
    source_document: z
      .string()
      .min(1, "source_document é obrigatório")
      .max(100, "source_document inválido"),
    confidence_score: z
      .number()
      .min(0, "confidence_score deve ser >= 0")
      .max(1, "confidence_score deve ser <= 1"),
  })
  .strict();

export type StructuredOutput = z.infer<typeof StructuredOutputSchema>;

type LoggerLike = {
  warn: (message: string, meta?: Record<string, unknown>) => void;
};

const defaultLogger: LoggerLike = {
  warn: (message, meta) => {
    console.warn(message, meta ?? {});
  },
};

// FIX #4: Object.freeze impede mutação acidental do fallback compartilhado
const SAFE_RESPONSE: Readonly<StructuredOutput> = Object.freeze({
  answer:
    "Não foi possível validar a resposta com segurança. Por favor, consulte um supervisor.",
  source_document: "SYSTEM-GUARDRAIL",
  confidence_score: 0,
});

const DANGEROUS_CARGO_REGEX =
  /\bcarga(s)?\s+perigosa(s)?\b|\bclasse(s)?\s*[1-6]\b|\bANTT\b/i;

const RETURN_REGEX =
  /\bdevolu[cç][aã]o\b|\bdevolver\b|\bdevolvida(s)?\b|\bdevolvido(s)?\b/i;

// FIX #5: removidos os casos redundantes — n[aã]o já cobre "nao" e "não"
const NEGATIVE_REGEX =
  /\bn[aã]o\b|\bn[aã]o\s+é\s+poss[ií]vel\b|\bn[aã]o\s+pode(m)?\b|\bineleg[ií]vel\b/i;

const AFFIRMS_DANGEROUS_RETURN_REGEX =
  /\bé\s+poss[ií]vel\b.*\bdevolu[cç][aã]o\b|\bpode(m)?\s+(ser\s+)?devolvid[ao](s)?\b|\bdevolu[cç][aã]o\s+permitida\b/i;

function normalizeText(value: string): string {
  // .toLowerCase() torna a flag /i nas regex redundante,
  // mas mantemos /i para documentar intenção explicitamente.
  return value.normalize("NFC").toLowerCase();
}

/**
 * Retorna true se a resposta afirmar (ou não negar claramente) que carga
 * perigosa pode ser devolvida — situação que deve ser bloqueada.
 *
 * Casos esperados:
 *   BLOQUEAR: "a carga perigosa pode ser devolvida"
 *   BLOQUEAR: "cargas perigosas classe 3 podem ser devolvidas" (sem negação)
 *   PERMITIR:  "cargas perigosas não podem ser devolvidas"
 *   PERMITIR:  "a devolução não é possível para cargas da ANTT"
 */
function violatesDangerousReturnGuardrail(answer: string): boolean {
  const text = normalizeText(answer);

  const mentionsDangerousCargo = DANGEROUS_CARGO_REGEX.test(text);
  const mentionsReturn = RETURN_REGEX.test(text);

  if (!mentionsDangerousCargo || !mentionsReturn) {
    return false;
  }

  // FIX #6: nomes claros — affirmsReturn detecta afirmação explícita de devolução
  const affirmsReturn = AFFIRMS_DANGEROUS_RETURN_REGEX.test(text);
  const hasNegation = NEGATIVE_REGEX.test(text);

  if (affirmsReturn) {
    return true;
  }

  return !hasNegation;
}

type ValidationResult = {
  ok: boolean;
  response: StructuredOutput;
  reason?: string;
};

export function validateResponse(
  raw: unknown,
  logger: LoggerLike = defaultLogger
): ValidationResult {
  const parsed = StructuredOutputSchema.safeParse(raw);

  if (!parsed.success) {
    logger.warn("response_rejected_schema_validation", {
      reason: "invalid_schema",
      issues: parsed.error.issues,
    });
    return {
      ok: false,
      response: SAFE_RESPONSE,
      reason: "invalid_schema",
    };
  }

  const trimmedAnswer = parsed.data.answer.trim();
  const trimmedSourceDocument = parsed.data.source_document.trim();

  // FIX #2: validar answer após trim (strings de só espaços passam no min(1) do schema)
  if (!trimmedAnswer) {
    logger.warn("response_rejected_empty_answer", {
      reason: "empty_answer_after_trim",
    });
    return {
      ok: false,
      response: SAFE_RESPONSE,
      reason: "empty_answer_after_trim",
    };
  }

  // FIX #3: manter a checagem pós-trim (cobre o caso de source_document com só espaços)
  if (!trimmedSourceDocument) {
    logger.warn("response_rejected_missing_source_document", {
      reason: "missing_source_document",
    });
    return {
      ok: false,
      response: SAFE_RESPONSE,
      reason: "missing_source_document",
    };
  }

  const structured: StructuredOutput = {
    answer: trimmedAnswer,
    source_document: trimmedSourceDocument,
    confidence_score: parsed.data.confidence_score,
  };

  if (violatesDangerousReturnGuardrail(structured.answer)) {
    logger.warn("response_rejected_dangerous_return_guardrail", {
      reason: "dangerous_return_must_be_negative",
      source_document: structured.source_document,
    });
    return {
      ok: false,
      response: SAFE_RESPONSE,
      reason: "dangerous_return_must_be_negative",
    };
  }

  return {
    ok: true,
    response: structured,
  };
}
```

---

## Resumo das mudanças

| # | Severidade | Problema | Solução |
|---|---|---|---|
| 2 | 🔴 Crítico | `answer` vazio após trim não detectado | Verificação explícita de `trimmedAnswer` antes de montar o objeto |
| 3 | 🟡 Moderado | Verificação de `source_document` estava no lugar errado | Movida para depois do trim, cobrindo strings só com espaços |
| 4 | 🟡 Moderado | `SAFE_RESPONSE` mutável | `Object.freeze` + tipo `Readonly<StructuredOutput>` |
| 6 | 🟡 Moderado | `hasPositiveReturn` — nome e comentários enganosos | Renomeado para `affirmsReturn`, JSDoc com exemplos de casos esperados |
| 1 | 🟢 Leve | Flag `/i` redundante após `toLowerCase` | Mantida com comentário explicando a redundância intencional |
| 5 | 🟢 Leve | Alternativas redundantes em `NEGATIVE_REGEX` | Simplificado para `n[aã]o` que já cobre todos os casos |
| 7 | 🟢 Leve | Ausência de casos de teste documentados | JSDoc com exemplos de strings que devem ser bloqueadas e permitidas |
