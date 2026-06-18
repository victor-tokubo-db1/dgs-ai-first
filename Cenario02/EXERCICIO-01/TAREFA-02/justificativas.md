# Justificativas

## novatech-code
- ESCOPO: src/ specs/ skills/ — único server com permissão de escrita. Justificativa de mínimo: o agente precisa ler e gerar código, specs e skills, mas não tem razão legítima de tocar em docs de negócio, corpus de chunks ou histórico git diretamente.

## novatech-docs
- ESCOPO: docs/novatech/ — somente leitura via env read_only. Justificativa de mínimo: docs de negócio são fonte da verdade imutável para o agente; escrita criaria risco de corrupção silenciosa do domínio. O agente consulta, nunca edita.

## novatech-corpus
- ESCOPO: data/retrieval-corpus/ — somente leitura via env read_only. Justificativa de mínimo: o corpus é gravado exclusivamente pelo pipeline de ingestão (processo separado, não MCP). O agente e o QA só precisam inspecionar chunks; escrita aqui corromperia os dados do RAG sem rastreabilidade.

## novatech-git
- ESCOPO: repositório local inteiro — o server git só expõe operações de leitura por protocolo (log, diff, show, blame, status, branch). Justificativa de mínimo: commits são atos humanos intencionais; o agente obtém contexto de mudanças recentes mas jamais escreve no histórico.

## novatech-memory
- ESCOPO: grafo local persistido em .mcp/memory.jsonl (criado automaticamente na primeira execução). Justificativa de mínimo: o server memory não acessa o filesystem do projeto — opera em seu próprio arquivo de grafo isolado. Leitura+escrita necessária porque o agente registra novos termos e decisões em tempo real.
