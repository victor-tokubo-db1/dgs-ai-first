
- Link compartilhado da conversa realizada usando Chat GPT: https://chatgpt.com/share/6a1e2f57-91dc-83e9-b099-c7fd9491a6da
- Tentativa de copiar toda a conversa abaixo.

##=====================================================


Como desenvolvedor da empresa de desenvolvimento de software sob demanda DB1, tenho o seguinte cenario: 

## O Cenário
A NovaTech é uma empresa de médio porte do setor de logística com 1.200 funcionários. Sua operação depende de um conjunto extenso de documentação interna: manuais de procedimento operacional, políticas de compliance, tabelas de SLA por tipo de cliente, regras de cálculo de frete, e normas de segurança de carga. Hoje, essa documentação está espalhada em três fontes: um SharePoint corporativo com ~800 documentos (PDFs e Word), uma wiki interna no Confluence com ~400 páginas, e uma pasta de rede com planilhas de referência atualizadas mensalmente. O problema: a equipe de atendimento ao cliente (45 pessoas) gasta em média 12 minutos por chamado buscando informações nessas fontes para responder dúvidas de clientes sobre prazos, regras de frete, políticas de devolução e procedimentos de reclamação. Isso gera atrasos, respostas inconsistentes e frustração tanto dos atendentes quanto dos clientes. A NovaTech contratou a DB1 para construir um assistente de IA que permita aos atendentes fazer perguntas em linguagem natural e receber respostas fundamentadas na documentação oficial da empresa, com indicação da fonte. O assistente será integrado ao ambiente Microsoft da NovaTech (Teams + SharePoint). 

### Informações adicionais fornecidas pela NovaTech 
- O volume médio é de 320 chamados/dia, dos quais ~60% envolvem consulta a documentação. 
- A documentação é atualizada mensalmente por 3 áreas diferentes (Operações, Compliance, Comercial), sem processo unificado de revisão. 
- Alguns documentos se contradizem entre versões — a equipe de atendimento hoje resolve isso "perguntando para quem sabe". 
- A NovaTech já tem licenças Microsoft 365 E3 e está disposta a provisionar Azure AI Services. - O projeto tem orçamento para 3 meses de discovery + desenvolvimento + go-live. 
- A expectativa da diretoria é reduzir o tempo médio de busca de 12 para menos de 2 minutos por chamado.

Esse cenário é um caso clássico para uma solução de RAG (Retrieval-Augmented Generation) corporativa integrada ao ecossistema Microsoft. Como desenvolvedor da DB1, eu estruturaria a proposta considerando não apenas a implementação técnica, mas também os riscos de governança documental que aparecem claramente no problema.

1. Entendimento do problema
O problema real da NovaTech não é apenas "buscar documentos".

Existem três dores distintas:

Localização da informação

Informação distribuída entre SharePoint, Confluence e planilhas.

Busca manual lenta.

Confiabilidade

Documentos contraditórios.

Ausência de governança de versões.

Dependência de especialistas informais ("quem sabe").

Produtividade operacional

320 chamados/dia.

60% exigem consulta documental.

Aproximadamente 192 consultas por dia.

Atualmente:

192 consultas × 12 minutos = 2.304 minutos/dia

≈ 38 horas/dia gastas apenas procurando informação

Meta:

192 × 2 minutos = 384 minutos/dia

≈ 6,4 horas/dia

Economia potencial:

≈ 32 horas de trabalho por dia

Esse é o principal ROI do projeto.

2. Objetivos da solução
O assistente deve:

Funcionais
✅ Responder perguntas em linguagem natural

Exemplo:

"Qual o SLA para clientes Premium da região Sul?"

✅ Citar a fonte utilizada

Exemplo:

Conforme documento "Política Comercial v4.2", seção 3.4.

✅ Exibir trecho utilizado

Exemplo:

Fonte:

"Clientes Premium possuem SLA de entrega de 24 horas..."

✅ Priorizar documentos mais recentes

✅ Informar quando houver conflito documental

Exemplo:

Foram encontradas duas regras divergentes:

Documento A (2025)

Documento B (2024)

✅ Integrar ao Teams

3. Arquitetura recomendada
Visão geral
SharePoint
     |
Confluence
     |
Planilhas
     |
     v

Pipeline de Ingestão
(Azure Functions)

     |
     v

Processamento
- OCR
- Chunking
- Metadata

     |
     v

Embeddings
Azure OpenAI

     |
     v

Vector Database
Azure AI Search

     |
     v

RAG Service
(API .NET)

     |
     v

Microsoft Teams Bot
4. Componentes Azure
Azure AI Search
Principal escolha para o projeto.

Motivos:

Integração nativa com Azure OpenAI.

Busca vetorial.

Busca híbrida.

Filtros por metadados.

Menor esforço operacional.

Azure OpenAI
Modelos:

GPT-4.1

GPT-4o

GPT-4.1-mini para custos menores

Funções:

Embeddings

Geração de resposta

Azure Functions
Responsável por:

Capturar documentos

Atualizar índice

Processar alterações mensais

Azure Blob Storage
Armazenamento dos documentos originais.

Teams Bot
Interface principal do usuário.

Exemplo:

Atendente:

Qual é o prazo para devolução
de carga avariada?

Assistente:

O prazo é de 5 dias úteis após a
constatação da avaria.

Fonte:
Manual Operacional v3.8
Capítulo 7.2
Atualizado em 14/02/2026
5. Estratégia de ingestão
Fonte 1: SharePoint
~800 documentos

Conector:

Microsoft Graph API

Tipos:

PDF

DOCX

Fonte 2: Confluence
~400 páginas

Conector:

REST API do Confluence

Fonte 3: Planilhas
Planilhas mensais.

Transformação para:

{
  "tipo": "sla",
  "cliente": "premium",
  "regiao": "sul",
  "prazo": "24h"
}
Isso melhora muito a recuperação.

6. Estratégia de indexação
Cada documento deve ser quebrado em chunks.

Exemplo:

Documento:
Política de Frete
50 páginas
Transformar em:

Chunk 1
Chunk 2
Chunk 3
...
Chunk 150
Com metadados:

{
  "documento": "PoliticaFrete_v5.pdf",
  "versao": "5.0",
  "area": "Comercial",
  "dataAtualizacao": "2026-03-10",
  "pagina": 12
}
7. Tratamento de conflitos documentais
Este é o ponto mais crítico do cenário.

A IA não deve simplesmente responder.

Ela deve detectar conflitos.

Exemplo:

Documento A:

Prazo de devolução: 5 dias.
Documento B:

Prazo de devolução: 7 dias.
Resposta:

Foram encontradas informações divergentes.

Documento:
Política Comercial v4.2
Prazo: 5 dias

Documento:
Manual Operacional v3.1
Prazo: 7 dias

Sugestão:
Validar com a área responsável.
Além disso, criar uma tabela de prioridade:

Compliance > Comercial > Operações
ou

Documento mais recente vence
Essa regra precisa ser definida com a NovaTech.

8. Segurança
Como a empresa já usa Microsoft 365:

Autenticação
Microsoft Entra ID (Azure AD)

Autorização
Permissões herdadas do SharePoint.

Exemplo:

Atendente nível 1
↓
Não vê documentos internos de compliance
Isso evita vazamento de informação.

9. Métricas de sucesso
Operacionais
Tempo médio de busca

Antes:

12 minutos
Meta:

< 2 minutos
Qualidade
Taxa de respostas corretas

Meta:

> 90%
Adoção
Consultas por dia

Cobertura
Percentual de perguntas respondidas sem escalonamento.

10. Roadmap para 3 meses
Fase 1 — Discovery (3 semanas)
Mapeamento documental

Entendimento dos conflitos

Definição de governança

PoC de RAG

Entrega:

Arquitetura validada

Fase 2 — Desenvolvimento (5 semanas)
Ingestão SharePoint

Ingestão Confluence

Azure AI Search

Azure OpenAI

API .NET

Teams Bot

Entrega:

MVP funcional

Fase 3 — Piloto (2 semanas)
Equipe de atendimento:

10 usuários

Medições:

Tempo de resposta

Precisão

Feedback

Fase 4 — Go Live (2 semanas)
Treinamento

Monitoramento

Ajustes

Riscos que eu destacaria para a diretoria da NovaTech
Documentação inconsistente → maior risco do projeto.

Ausência de governança de conteúdo → a IA amplifica erros existentes.

Expectativa de "IA sabe tudo" → é necessário definir limites claros.

Atualizações mensais sem processo unificado → exige pipeline automatizado de reindexação.

Controle de acesso → respostas devem respeitar as permissões dos documentos de origem.

A principal mensagem para a NovaTech seria: o desafio técnico de construir o assistente é relativamente simples com Azure OpenAI + Azure AI Search; o verdadeiro fator de sucesso está na governança da documentação, tratamento de conflitos e confiança das respostas. Isso deve fazer parte do escopo do projeto desde o discovery.


📄 Arquivo gerado:

Download do arquivo TXT

O arquivo contém somente a análise técnica da estratégia de chunking para o cenário da NovaTech, considerando os tipos de perguntas dos atendentes, o processo de retrieval e os impactos do efeito lost in the middle na qualidade das respostas. 



analise-tecnica-novatech.txt
Documento
Faça uma revisão desse documento contendo análise técnica. Identifique pontos fracos, estimativas otimistas demais ou riscos que não considerados. Mostre todos os pontos que foram identificados 

O documento está bem estruturado para uma fase de discovery, mas apresenta alguns pontos que eu classificaria como estimativas otimistas, lacunas técnicas e riscos arquiteturais não explicitados. Em uma banca técnica, entrevista de arquitetura ou defesa de proposta para cliente, esses seriam os principais pontos que poderiam ser questionados.

1. A estimativa de tamanho da base provavelmente está subdimensionada
Problema
Foi assumido:

500 palavras por página PDF
para todos os 8.000 PDFs.

Mas o próprio cenário informa:

tabelas complexas

fluxogramas

documentos escaneados

anexos

Em ambientes logísticos é comum encontrar:

páginas com pouco texto e muitas tabelas;

páginas com imagens;

páginas contendo apenas diagramas.

Risco
A estimativa de:

6,2 milhões de tokens
pode estar significativamente errada.

Dependendo da estratégia de extração:

Cenário	Tokens
Conservador	6M
Realista	8M–12M
Com OCR + descrições	12M–18M
Recomendação
Executar um piloto em:

50 PDFs
50 páginas wiki
5 planilhas
antes de estimar custos definitivos.

2. O custo de embeddings não foi considerado
Problema
O documento fala da quantidade de tokens.

Mas não traduz isso em:

custo de embeddings;

custo de reindexação mensal.

Risco
A NovaTech atualiza documentos mensalmente.

Logo:

Novo documento
↓
Rechunking
↓
Novos embeddings
↓
Reindexação
gera custo recorrente.

O que faltou
Estimativa de:

Embedding inicial
+
Embeddings mensais
3. Não foi considerada deduplicação documental
Problema
O cenário afirma:

Alguns documentos se contradizem entre versões.

Isso normalmente significa:

Politica_v1
Politica_v2
Politica_v3
todas presentes.

Impacto
Sem deduplicação:

chunks redundantes;

embeddings redundantes;

retrieval poluído.

Risco
O modelo pode recuperar:

Versão 2024
Versão 2025
Versão 2026
simultaneamente.

O que faltou
Estratégia explícita de:

versionamento;

priorização;

arquivamento.

4. Conflitos documentais foram tratados superficialmente
Problema
O documento identifica o problema.

Mas não explica como detectar conflito.

Exemplo:

Documento A:

Prazo = 5 dias
Documento B:

Prazo = 7 dias
Risco
O LLM não detecta conflito de forma confiável.

Muitas vezes ele simplesmente escolhe uma resposta.

O que faltou
Mecanismo explícito:

Chunk A
↓
Chunk B
↓
Comparação semântica
↓
Flag de conflito
5. Não foi considerado permission-aware retrieval
Problema
A solução menciona Entra ID.

Mas não detalha:

Busca
↓
Filtragem por ACL
↓
Retorno
Risco
Atendente visualizar:

regras de compliance;

políticas internas;

informações comerciais restritas.

O que faltou
Estratégia de:

security trimming;

ACL indexing;

permission-aware search.

6. Tabelas de frete talvez não devam ser RAG
Problema
Foi sugerido:

JSON estruturado
o que é correto.

Mas ainda dentro da visão de recuperação documental.

Risco
Frete é regra operacional.

Não é conhecimento textual.

Melhor abordagem
Transformar:

Tabela
em

Base consultável
ou

Rule Engine
Impacto
Maior precisão.

Menos alucinação.

7. Fórmulas de planilha estão subestimadas
Problema
O documento sugere:

Extrair fórmula
Mas planilhas corporativas frequentemente possuem:

referências cruzadas;

abas ocultas;

macros VBA;

cálculos condicionais.

Risco
A fórmula textual não representa a lógica real.

O que faltou
Inventário técnico:

Excel
↓
Mapear:
- Fórmulas
- VBA
- Macros
- Dependências
8. O impacto das macros do Confluence pode ser muito maior
Problema
Foi assumido:

Renderizar HTML
Mas algumas macros:

chamam sistemas externos;

executam consultas;

exibem dados dinâmicos.

Risco
O conteúdo indexado pode ficar obsoleto imediatamente.

O que faltou
Classificação:

Macro estática
Macro dinâmica
Macro integração
9. A estratégia de chunking pode estar simplificada demais
Problema
Foi proposto:

500–800 tokens
para grande parte da base.

Risco
Nem todo conteúdo se comporta igual.

Exemplo:

Procedimento
800 tokens
funciona bem.

Tabela
800 tokens
não faz sentido.

Política
Talvez:

300 tokens
seja melhor.

O que faltou
Avaliação empírica:

Chunk 300
Chunk 500
Chunk 800
Chunk 1200
e medir:

Recall@K

Precision@K

Groundedness

10. Lost in the Middle foi tratado corretamente, mas existe um problema maior
Problema
O documento assume:

Top 5–10 chunks
Risco
Perguntas complexas exigem múltiplas fontes.

Exemplo:

SLA
+
Frete
+
Compliance
+
Devolução
Resultado
5 chunks podem ser insuficientes.

O que faltou
Estratégia de:

Query Decomposition
Pergunta
↓
Subperguntas
↓
Recuperação independente
↓
Síntese
11. Não foi considerada avaliação contínua do RAG
Este é provavelmente o maior risco ausente.

O documento fala de:
chunking;

retrieval;

embeddings.

Mas não fala de:

Como saber se está funcionando?
O que faltou
Conjunto de avaliação:

100 perguntas reais
com:

resposta esperada;

fonte correta;

score de groundedness.

Métricas
Recall@K

Precision@K

MRR

Faithfulness

Answer Relevance

Groundedness

12. O prazo de 3 meses pode ser otimista
O documento assume implicitamente que tudo ocorrerá conforme planejado.

Mas existe uma grande dependência de:

qualidade documental;

acesso SharePoint;

acesso Confluence;

tratamento de OCR;

conflitos de versões.

Risco real
A fase de discovery descobrir que:

30% da documentação
está inconsistente.

Nesse cenário:

3 meses
pode virar:

4–6 meses
facilmente.

Resumo Executivo dos Principais Pontos Fracos
Tema	Severidade
Estimativa de tokens possivelmente subdimensionada	🔴 Alta
Custos de embeddings e reindexação não considerados	🔴 Alta
Ausência de estratégia de versionamento/deduplicação	🔴 Alta
Detecção de conflitos pouco detalhada	🔴 Alta
Permission-aware retrieval não detalhado	🔴 Alta
Tabelas de frete talvez devam virar rule engine	🔴 Alta
Complexidade real das planilhas subestimada	🔴 Alta
Macros dinâmicas do Confluence não avaliadas	🟠 Média-Alta
Chunking sem validação empírica	🟠 Média
Falta de query decomposition	🟠 Média
Ausência de framework de avaliação RAG	🔴 Alta
Cronograma de 3 meses potencialmente otimista	🔴 Alta
Se eu estivesse revisando essa proposta como arquiteto principal da DB1 antes de apresentar para a NovaTech, os pontos que eu exigiria complementar obrigatoriamente seriam: governança/versionamento documental, segurança por ACL, framework de avaliação do RAG, estratégia para regras de negócio em planilhas/tabelas e estimativa financeira de embeddings/reindexação. Esses cinco itens representam o maior risco técnico e financeiro do projeto.


Gere um novo arquivo de texto já aplicado sua revisão que foi realizada do documento analise-tecnica-novatech.txt

📄 Arquivo revisado gerado:

Download do arquivo TXT revisado

O documento já incorpora os principais ajustes identificados na revisão técnica, incluindo:

Governança e versionamento documental;

Permission-aware retrieval (ACL/Security Trimming);

Revisão das estimativas de volume de tokens;

Custos de embeddings e reindexação;

Complexidade de planilhas, macros e tabelas de frete;

Estratégia de avaliação contínua do RAG;

Query Decomposition para perguntas complexas;

Revisão do cronograma e riscos do projeto.