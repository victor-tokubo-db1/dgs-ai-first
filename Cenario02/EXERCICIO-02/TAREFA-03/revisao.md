# Revisão Crítica - Tasks 1 e 2 (Query Endpoint)

Data: 2026-06-14  
Escopo: T1 (types/errors) e T2 (validator/handler)

## Findings (ordenados por severidade)

### 1. Alta - zod em devDependencies, mas usado em runtime
- Evidência:
  - [package.json](package.json#L18)
  - [src/functions/query/validator.ts](src/functions/query/validator.ts#L1)
- Problema:
  - O endpoint depende de zod em execução. Em ambientes com instalação de produção (sem devDependencies), pode ocorrer falha de import em runtime.
- Ajuste recomendado:
  - Mover zod para dependencies.

### 2. Média - Resposta 200 do handler não está ancorada em contrato estável
- Evidência:
  - [src/functions/query/handler.ts](src/functions/query/handler.ts#L70)
  - [src/shared/types.ts](src/shared/types.ts#L18)
- Problema:
  - O payload de sucesso atual mistura campos de debug/input e não está explicitamente alinhado ao contrato de saída já definido (QueryResponse).
- Ajuste recomendado:
  - Retornar shape alinhado ao contrato final desde já (ou definir envelope estável de transição).

### 3. Média - Logger criado localmente no handler pode quebrar padronização
- Evidência:
  - [src/functions/query/handler.ts](src/functions/query/handler.ts#L6)
  - [src/shared/logger.ts](src/shared/logger.ts)
- Problema:
  - O uso de logger inline tende a gerar inconsistência de formato/correlação entre funções.
- Ajuste recomendado:
  - Centralizar logger compartilhado em shared/logger e reutilizar em handlers/serviços.

### 4. Média - Falta de testes para critérios de aceite de T2
- Evidência:
  - Critérios exigem cenários de 400/200 na task (question ausente, >500, turn inválido, UUID inválido).
- Problema:
  - Sem testes automatizados, regressões de validação e contrato HTTP podem entrar no PR sem sinalização.
- Ajuste recomendado:
  - Adicionar testes unitários do validator e pelo menos um teste de handler (happy path + erro de validação).

### 5. Baixa - Import de ZodIssue pode ser type-only
- Evidência:
  - [src/functions/query/validator.ts](src/functions/query/validator.ts#L1)
- Problema:
  - Não é bug funcional, mas type-only import melhora clareza e evita import de runtime desnecessário.
- Ajuste recomendado:
  - Usar import type para ZodIssue.

## Riscos residuais antes de code review formal
- Contrato HTTP ainda sujeito a mudança quando T8/T9 forem implementadas.
- Observabilidade pode ficar inconsistente se logger compartilhado não for padronizado agora.
- Critérios de aceite estão só validados manualmente, não por suíte automatizada.

## Recomendação de gate para PR
- Bloquear aprovação até corrigir:
  1. Dependência zod em runtime.
  2. Contrato mínimo estável da resposta 200.
- Solicitar como follow-up imediato:
  1. Padronização de logger compartilhado.
  2. Testes mínimos de validação/handler.