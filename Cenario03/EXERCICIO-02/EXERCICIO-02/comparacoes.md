# Resposta do exercício 01

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

 # Comparações

### B1 · Log de dados sensíveis com a ferramenta errada
Mencionado com "Usando console.log para logging ao invés de pino;"

### B2 · Nenhuma validação de input (Zod ausente)
Mencionado com "Não está validando input com zod;"

### B3 · `require()` dinâmico dentro de função async
Mencionado em "Realizando require dinâmico, nesse caso require('@azure/cosmos');"

### A1 · Nenhum tratamento de erro no acesso ao Cosmos
Não mencionado

### A2 · Status HTTP incorreto na criação
Não mencionado

### M1 · Nenhum teste unitário criado junto com o módulo
Não mencionado