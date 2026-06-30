```typescript
// feedback-handler.ts — gerado pelo Copilot
import { app, HttpRequest, HttpResponseInit } from '@azure/functions';

export async function feedbackHandler(
  request: HttpRequest
): Promise<HttpResponseInit> {
  const body = await request.json() as any;

  const feedback = {
    queryId: body.queryId,
    rating: body.rating,
    comment: body.comment,
    attendantEmail: body.attendantEmail,
    timestamp: new Date().toISOString()
  };

  console.log('Feedback recebido:', JSON.stringify(feedback));

  const { CosmosClient } = require('@azure/cosmos');
  const client = new CosmosClient(process.env.COSMOS_CONNECTION_STRING);
  const database = client.database('novatech');
  const container = database.container('feedbacks');

  await container.items.create(feedback);

  return { status: 200, body: 'OK' };
}

app.http('feedback', {
  methods: ['POST'],
  handler: feedbackHandler
});
```

- O AGENTS.md do projeto, construído no cenário 2 (resumo): *"TypeScript strict mode. Zod para validação de input. pino para logging (nunca console.log). Nunca logar dados pessoais (e-mail, nome). Imports estáticos no topo (nunca require dinâmico)."*

1. Faça sua própria revisão ANTES de usar o Claude. Liste os problemas, classificando cada um (violação do AGENTS.md, problema de segurança, ou bug potencial).

- Violação do AGENTS.md:
  - Conversão de json para any;
  - Não está validando input com zod;
  - Usando console.log para logging ao invés de pino;
  - Logando dados pessoais, nesse caso attendantEmail;
  - Realizando require dinâmico, nesse caso require('@azure/cosmos');

- problema de segurança:
  - Logando dados pessoais, nesse caso attendantEmail;

- bug potencial:
  - Sempre retornar status 200
  - Caso "process.env.COSMOS_CONNECTION_STRING" venha vazio, pode ocorrer erro não tratado
