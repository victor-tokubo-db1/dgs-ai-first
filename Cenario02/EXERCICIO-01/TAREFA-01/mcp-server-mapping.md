# MCP Server Mapping — NovaTech Assistant

> Fase 2 · Configuração de ambiente · Repositório: `novatech-assistant`

---

## Visão geral

Cada necessidade de acesso do projeto é atendida por um *reference server* gratuito e local. As três instâncias de `filesystem` rodam como processos separados — isolamento total entre código, documentação e corpus de chunks.

| Necessidade | Server | Modo | Escopo |
|---|---|---|---|
| Ler/escrever código, specs e skills | `filesystem` (instância 1) | R/W | `./src` `./specs` `./skills` |
| Ler documentação de negócio | `filesystem` (instância 2) | R | `./docs/novatech/` |
| Inspecionar corpus de chunks | `filesystem` (instância 3) | R | `./data/retrieval-corpus/` |
| Histórico, diff e branches | `git` | R | repositório local |
| Glossário e decisões persistentes | `memory` | R/W | grafo local |

---

## Detalhamento por server

### 1. `filesystem` — Código, specs e skills

**Escopo:** `./src` · `./specs` · `./skills`
**Modo de acesso:** leitura e escrita

**Necessidade no projeto**

- Ler e escrever código TypeScript (backend, bot) e React (painel web) e Bicep (IaC).
- Ler e escrever specs no modelo Spec Driven Development (SDD, ADRs, contratos de API).
- Ler e escrever skills reutilizáveis que encapsulam os padrões do projeto.

**Tools e resources expostos**

| Primitiva | Tipo | Descrição |
|---|---|---|
| `read_file` | tool | Lê conteúdo de um arquivo |
| `write_file` | tool | Cria ou sobrescreve um arquivo |
| `list_directory` | tool | Lista arquivos e subdiretórios |
| `search_files` | tool | Busca por padrão/glob no escopo |
| `create_directory` | tool | Cria diretório |

**Quem consome**

- **Claude Code / Copilot** — geração, revisão e refatoração de código guiada por specs.
- **Tech Lead e Devs** — consulta de specs e padrões de projeto via agente durante desenvolvimento.

---

### 2. `filesystem` — Documentação de negócio

**Escopo:** `./docs/novatech/`
**Modo de acesso:** somente leitura

**Necessidade no projeto**

- Ler regras de negócio, glossário e políticas da NovaTech (equivalente ao Confluence da fase 1).
- Fornecer contexto de domínio ao agente durante geração de specs e código.

**Tools e resources expostos**

| Primitiva | Tipo | Descrição |
|---|---|---|
| `read_file` | tool | Lê conteúdo de um documento |
| `list_directory` | tool | Lista documentos disponíveis |
| `search_files` | tool | Busca por termo nos documentos |

> Escrita vedada nesta instância para preservar a integridade da fonte da verdade de negócio.

**Quem consome**

- **Claude Code / Copilot** — enriquece o contexto de prompts com regras e terminologia de negócio antes de gerar specs ou código.
- **Product Specialist** — valida aderência das specs e histórias às regras de negócio via agente.

---

### 3. `filesystem` — Corpus de chunks (retrieval)

**Escopo:** `./data/retrieval-corpus/`
**Modo de acesso:** somente leitura

**Necessidade no projeto**

- Simular localmente o comportamento do Azure AI Search durante desenvolvimento e testes.
- Inspecionar chunks gerados pelo pipeline de ingestão para validar estratégia de chunking (ADR-0004).

**Tools e resources expostos**

| Primitiva | Tipo | Descrição |
|---|---|---|
| `read_file` | tool | Lê um chunk específico |
| `list_directory` | tool | Lista chunks disponíveis |
| `search_files` | tool | Busca por conteúdo nos chunks |

> O pipeline de ingestão escreve diretamente nesta pasta — não via MCP. O server MCP expõe apenas leitura para inspeção.

**Quem consome**

- **Claude Code** — lê chunks para gerar testes de integração do pipeline de RAG.
- **QA** — inspeção manual de chunks via agente para validar cobertura e qualidade do chunking.

---

### 4. `git` — Histórico e branches

**Escopo:** repositório local `novatech-assistant`
**Modo de acesso:** somente leitura

**Necessidade no projeto**

- Navegar histórico de commits (substitui acesso ao GitHub na fase local, conforme Anexo D).
- Consultar diffs e blame para entender a evolução do código antes de gerar alterações.
- Listar branches ativas e verificar status do working tree.

**Tools expostos**

| Primitiva | Tipo | Descrição |
|---|---|---|
| `git_log` | tool | Histórico de commits com filtros |
| `git_diff` | tool | Diferenças entre commits ou working tree |
| `git_show` | tool | Conteúdo de um commit específico |
| `git_blame` | tool | Autoria linha a linha de um arquivo |
| `git_status` | tool | Estado atual do working tree |
| `git_branch` | tool | Lista e metadados de branches |

> Somente leitura por design: commits são atos intencionais. O agente pode sugerir mensagens de commit, mas `git commit` e `git push` ficam a cargo do desenvolvedor.

**Quem consome**

- **Claude Code / Copilot** — obtém contexto de mudanças recentes antes de gerar ou alterar código.
- **Tech Lead** — code review assistido por agente, consultando diff e histórico sem sair do contexto.

---

### 5. `memory` — Glossário e decisões persistentes

**Escopo:** grafo local (entities + relations)
**Modo de acesso:** leitura e escrita

**Necessidade no projeto**

- Persistir a linguagem ubíqua do domínio NovaTech (termos, definições, bounded contexts).
- Registrar decisões arquiteturais (ADRs) em forma navegável e relacionável.
- Manter relações entre entidades: `ADR → componente → bounded context → termo`.

**Tools expostos**

| Primitiva | Tipo | Descrição |
|---|---|---|
| `create_entities` | tool | Cria nós no grafo (termos, ADRs, componentes) |
| `create_relations` | tool | Cria arestas entre entidades |
| `add_observations` | tool | Adiciona fatos a uma entidade existente |
| `search_nodes` | tool | Busca por entidades no grafo |
| `open_nodes` | tool | Expande uma entidade e suas relações |
| `delete_entities` | tool | Remove entidade obsoleta do grafo |

**Fluxo de uso**

1. Agente descobre novo termo ou decisão durante geração de código ou spec.
2. Registra imediatamente via `create_entities` + `create_relations`.
3. Tech Lead audita o grafo periodicamente e corrige ou expande via `add_observations`.

**Quem consome**

- **Claude Code / Copilot** — consulta o grafo antes de nomear classes, funções e módulos, garantindo consistência com a linguagem ubíqua.
- **Tech Lead** — audita e mantém o grafo de decisões; ponto de entrada para onboarding de novos membros.
- **Product Specialist** — valida se os termos gravados refletem o domínio de negócio corretamente.

---

## Notas de configuração

### Isolamento entre instâncias de `filesystem`

As três instâncias são processos MCP separados, cada um com seu próprio `--allowed-paths`. Um agente com acesso à instância de código (`./src`) não enxerga o corpus de chunks (`./data/retrieval-corpus/`) nem os docs de negócio (`./docs/novatech/`). O princípio é escopo mínimo necessário por processo.

### Política de escrita

| Server | Agente pode escrever? | Humano valida? |
|---|---|---|
| `filesystem` — código/specs/skills | sim | sim (code review) |
| `filesystem` — docs de negócio | **não** | — |
| `filesystem` — corpus | **não** | — (pipeline escreve diretamente) |
| `git` | **não** | — (commits são ato humano) |
| `memory` | sim | sim (auditoria periódica do Tech Lead) |
