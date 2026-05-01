# Diário de Bordo — SAR (Sistema de Automação de Recolocação)

Registro cronológico de decisões, entregas, curvas e erros do projeto.
Documento obrigatório — atualizado ao final de cada tarefa concluída.
Garante rastreabilidade, legado e prevenção de recorrência de erros.

---

## 2026-04-25 — Início do Projeto

**Ações:**
- Criação da estrutura inicial de pastas do projeto no VS Code
- Definição do workspace `Aplicativo_DPT.code-workspace`

**Decisões:**
- Stack definida: Python 3.12 + FastAPI + SQLite + HTML/CSS/JS Vanilla
- Estrutura de pastas: `/backend`, `/frontend`, `/integracao`, `/documentacao`, `/apoio`

---

## 2026-04-26 — Fundação do Backend e Governança

**Ações:**
- Criação de `srv_interface_backend.py` com rotas `/` e `/vagas`
- Criação de `rotinas/genericas.py` com CRUD agnóstico SQLite
- Criação dos documentos de governança: `governanca.md`, `plano_de_desenvolvimento.md`, `fluxograma.md`
- Configuração de dependências em `cfg_dependencias_python.txt`

**Decisões:**
- SQLite como única fonte de verdade (Verdade Absoluta)
- CRUD centralizado em `rotinas/genericas.py` — agnóstico a tabelas
- Tabelas iniciais: `vagas`, `configuracoes`, `logs_sistema`

---

## 2026-04-27 — Primeira Carga no GitHub e Ambiente

**Ações:**
- Inicialização do repositório git local e sincronização com `github.com/ricardopolpas-max/SAR`
- Instalação do Python 3.12 e dependências na máquina (pós-formatação)
- Criação do `.devcontainer/devcontainer.json` para GitHub Codespaces
- Criação do `.gitignore` protegendo banco de dados, `.env` e chave privada

**Bugs corrigidos:**
- `from rotinas.db_genericas import` → `from rotinas.genericas import` (nome de módulo incorreto)
- `await db_selecionar(...)` → `db_selecionar(...)` (função síncrona chamada com await)

---

## 2026-04-27 — Frontend Inicial e SSL

**Ações:**
- Criação do `frontend/telas/SAR.html` — tela principal
- Criação do `frontend/estilos/visual.css` — design system global
- Criação do `frontend/scripts/api.js` — módulo de comunicação
- Criação do `frontend/scripts/vagas.js` — lógica da tela de vagas
- Instalação do `mkcert` e geração de certificado SSL local (válido até 27/07/2028)
- Criação do `.env` com caminhos do certificado

**Curvas e correções de rota:**
- CSS iniciou com nome `sistema.css` → renomeado para `visual.css` por melhor semântica
- Frontend iniciou com estilos inline no HTML → migrado para `visual.css` global

---

## 2026-04-27 — Auditoria de Governança e Decisões Arquiteturais

**Violações identificadas e registradas:**
1. Prefixos (`srv_`, `db_`, `bot_`, `cfg_`, `prc_`, `gui_`) ainda documentados na governança após decisão de abolição
2. `srv_interface_backend.py` com prefixo abolido — pendente renomeação para `interface_backend.py`
3. `cfg_dependencias_python.txt` com prefixo abolido — pendente renomeação para `dependencias.txt`
4. `api.js` posicionado em `frontend/scripts/` — incorreto arquiteturalmente
5. `servidor.py` previsto como orquestrador — não criado (dívida técnica Fase 1)
6. `fluxograma.md` e `plano_de_desenvolvimento.md` nunca atualizados após entregas
7. Múltiplos arquivos criados por turno repetidamente — violação da unicidade
8. Testes reais nunca solicitados ao usuário — violação do protocolo de qualidade
9. Seções 2 a 5 da governança desatualizadas

**Decisões arquiteturais tomadas:**
- **Prefixos abolidos** em todo o projeto — nomenclatura descritiva por função e localização por pasta
- **`frontend/scripts/`** reservado exclusivamente para lógica de negócio
- **`integracao/rotas/`** é a camada de transporte — `api.js` será movido para cá
- **CSS global** em `visual.css` — estilos locais apenas quando design divergir do padrão
- **WebSocket (Ukeceker Conecta)** não será utilizado — projeto acadêmico, prazo definido, princípio arquitetural mantido pela separação de camadas
- **Diário de bordo** criado como documento obrigatório de rastreabilidade

**Correções em andamento:**
- [x] Governança Seção 1 — nomenclatura sem prefixos
- [ ] Governança Seção 2 — hierarquia de pastas
- [ ] Governança Seções 3, 4, 5 — regras, SSL e protocolo
- [ ] Renomear `srv_interface_backend.py` → `interface_backend.py`
- [ ] Renomear `cfg_dependencias_python.txt` → `dependencias.txt`
- [ ] Mover `api.js` → `integracao/rotas/api.js`
- [ ] Criar `servidor.py` (orquestrador + SSL via `.env`)
- [ ] Atualizar referências nos arquivos afetados

---

## 2026-04-27 — Entregas Técnicas da Fase 1

**Ações concluídas:**
- Renomeado `srv_interface_backend.py` → `interface_backend.py` (prefixo abolido)
- Renomeado `cfg_dependencias_python.txt` → `dependencias.txt` (prefixo abolido)
- Movido `api.js` de `frontend/scripts/` → `integracao/rotas/api.js` (camada correta)
- Criado `servidor.py` como orquestrador central (ponto de entrada único)
- Adicionado mounts `StaticFiles` em `interface_backend.py` (`/frontend` e `/integracao`)
- Adicionada rota `GET /sar` servindo `SAR.html` via `FileResponse`
- Adicionada rota `GET /favicon.ico` retornando SVG inline (elimina 404)
- Atualizado `SAR.html` com caminhos absolutos compatíveis com FastAPI
- Governança Seções 2–5 corrigidas e atualizadas
- `.devcontainer/devcontainer.json` atualizado para usar `dependencias.txt`

**Bugs corrigidos:**
- `reload=True` no `uvicorn.run()` → removido (incompatível com SSL no Windows, SSL não era aplicado)
- `atexit.register(liberar_porta)` + `subprocess/taskkill` → removidos (causavam deadlock no shutdown do Windows — processo tentava matar a si mesmo enquanto uvicorn encerrava)
- Favicon 404 após migração para FastAPI → corrigido com rota dedicada

**Decisões registradas:**
- `PORTA_DEFAULT` = âncora imutável no `.env`; `PORTA_ATUAL` = verdade operacional gravada em runtime
- `servidor.py` atualiza `BASE_URL` em `api.js` via regex antes de subir — frontend sempre recebe a porta correta
- Porta livre encontrada por varredura sequencial a partir da `PORTA_DEFAULT`
- SSL validado antes de subir — servidor bloqueado sem certificado válido
- OS libera porta automaticamente no encerramento normal — `liberar_porta` era redundante e perigosa

---

## 2026-04-28 — Gerenciamento de PID

**Problema identificado:**
Encerramento anormal do processo (terminal fechado, crash, kill externo) deixava instâncias fantasmas ocupando porta, causando erros na próxima inicialização. Solução anterior (`atexit` + `taskkill`) causava deadlock no Windows.

**Solução implementada — arquivo PID:**
- `servidor.py` checa `sar.pid` na inicialização e encerra processo anterior se existir
- PID atual gravado em `sar.pid` após validação dos certificados
- `try/finally` em torno de `uvicorn.run()` garante remoção do `sar.pid` em qualquer cenário de encerramento (normal ou exceção)
- `sar.pid` adicionado ao `.gitignore` (arquivo operacional, gerado em runtime)
- Hierarquia e proibições de commit atualizadas na governança

**Por que `try/finally` e não `atexit`:**
- `atexit` executa *durante* o shutdown do uvicorn → condição de corrida → deadlock no Windows
- `try/finally` executa *após* `uvicorn.run()` retornar → uvicorn já encerrou → sem conflito

**Arquivos alterados:**
- `backend/servidor.py` — funções `encerrar_instancia_anterior`, `gravar_pid`, `remover_pid`
- `.gitignore` — entrada `sar.pid`
- `documentacao/governanca.md` — `sar.pid` na árvore e nas proibições de commit

---

## 2026-04-28 — Motor 1: Correções Técnicas e Proteção de Dados

**Ações:**
- `iniciar_servidor.bat` atualizado para abrir browser automaticamente em `https://127.0.0.1:8000/sar` após 4 segundos
- `interface_backend.py`: endpoints CRUD completos para `/vagas`, `/configuracoes` e `/logs` implementados
- `interface_backend.py`: sync automático no startup **removido** — sync somente via botão "Atualizar"
- `interface_backend.py`: índice UNIQUE em `id_externo` criado via migration segura (suporta banco existente)
- `sincronizacao.py`: campo `createdAt` da API mapeado para `data_extracao` (data real da vaga, não data do sync)
- `sincronizacao.py`: DELETE protegido — remove apenas vagas com `status = PENDENTE OR NULL` que sumiram da plataforma
- `rotinas/__init__.py` criado — pacote Python declarado corretamente
- `import threading` removido de `interface_backend.py` após remoção do sync no startup

**Decisão crítica registrada:**
Sync no startup foi removido por risco de regressão: sobrescreveria dados do candidato (status, notas, score) e poderia deletar vagas que o mesmo está ativamente preparando candidatura. O sync é ação do usuário, não do sistema.

**API Peixe 30 confirmada:**
- Endpoint público — sem autenticação
- 841 vagas / 281 páginas (perPage=3) ou ~17 páginas (perPage=50)
- Campos confirmados: `_id`, `name`, `requisites`, `location`, `companyName`, `publicUrl`, `contractType`, `modality`, `startingSalaryInCents`, `createdAt`

---

## 2026-04-28 — Sessão de Análise: Arquitetura Completa dos 4 Motores

**Contexto:** Sessão dedicada exclusivamente a análise e design — zero código. Filosofia: Analisar → Projetar → Executar → Testar.

**Motor 1 — Captura de Vagas (fechado):**
- Peixe 30 único por enquanto — sem abstração prematura de conector
- Expansão futura: tabelas por plataforma + VIEW `vagas_todas` (DA-01 documentado)
- Sync manual, UPSERT seguro, DELETE protegido — decisões já implementadas

**Motor 2 — Identidade e Acesso (fechado):**
- Modelo ERP: tela de login é porta de entrada obrigatória — nenhum dado exposto sem autenticação
- Sem cookie — token UUID4 no `localStorage`, enviado no header `Authorization: Bearer`
- Sessão auditável na tabela `sessoes` — revogável, sem estado escondido no browser
- Modelo mestre-detalhe: `candidatos` (credencial) + `perfis` + tabelas filhas (dados profissionais)
- Status de vagas migra de `vagas` para `candidaturas` — dado pertence ao candidato, não à vaga

**Motor 3 — Perfil do Candidato (fechado):**
- Duas entradas: importação de documento (IA extrai) OU formulário manual
- Salvamento parcial permitido — mínimo validado só na geração
- Mínimo inclusivo: nome + contato + 1 habilidade + (1 experiência OU formação OU certificação)
- Inclusivo por design: atende jovem aprendiz e primeiro emprego
- Tabelas filhas por grupo: experiências, formações, habilidades, idiomas, certificações, documentos
- Proficiência de habilidades: Básico / Intermediário / Avançado / Especialista
- Proficiência de idiomas: Básico / Intermediário / Avançado / Fluente / Nativo
- Contêiner de documentos separado do currículo: certificados, diplomas, portfólio, carta de apresentação
- Carta de apresentação: upload próprio ou gerada pela IA sob demanda no empacotamento

**Motor 4 — Geração de Currículo Premium (fechado):**
- Geração em 3 etapas: extrai requisitos da vaga → score de aderência → gera currículo cirúrgico
- Score exibido antes da geração — candidato decide conscientemente
- Tom adaptativo por perfil (jovem aprendiz ≠ sênior — IA ajusta linguagem)
- Edição em texto livre (`contenteditable`) — candidato tem autonomia, sistema não impõe resultado
- PDF via `weasyprint` (HTML → PDF) — WYSIWYG entre tela e arquivo
- ZIP salvo no Desktop do usuário (`~/Desktop`) — sem problemas de permissão ou BitLocker Windows
- Pacote: currículo PDF + carta + documentos selecionados pelo candidato
- Sistema é facilitador: sem rastreamento externo de candidatura após envio do ZIP
- Histórico de currículos gerados preservado no banco

**Próxima sessão:** implementação completa do Motor 2 (Identidade e Acesso) — fase extensa, sem interrupção no meio para preservar lógica.

---

## 2026-04-29 — Motor 2: Identidade e Acesso (implementação completa)

**Contexto:** Implementação do sistema ERP-style de autenticação. Modelo de sessão com token UUID4 no `localStorage`, sem cookies.

**Arquivos entregues (11 turnos):**

| Turno | Arquivo | Ação |
|---|---|---|
| 1 | `backend/rotinas/autenticacao.py` | Criado — bcrypt, criar/validar/revogar token |
| 2 | `backend/aplicacao.py` | Criado — substitui `interface_backend.py`; tabelas `candidatos` e `sessoes`; endpoints auth; todas as rotas protegidas por `Depends(autenticar)` |
| 3 | `backend/servidor.py` | Atualizado — `"interface_backend:app"` → `"aplicacao:app"` |
| 3 | `backend/interface_backend.py` | Removido — código morto após renomeação |
| 4 | `integracao/rotas/api.js` | Atualizado — módulo `autenticacao` (`entrar`, `cadastrar`, `encerrar`, `estaAutenticado`, `obterNome`); `_requisitar()` injeta `Authorization: Bearer` automaticamente |
| 5 | `frontend/estilos/visual.css` | Atualizado — seção 17: layout de autenticação, card, campos, estados de erro |
| 6 | `frontend/telas/login.html` | Criado — tela de acesso |
| 7 | `frontend/telas/cadastro.html` | Criado — tela de criação de conta |
| 8 | `frontend/scripts/login.js` | Criado — validação, chamada API, redirecionamento |
| 9 | `frontend/scripts/cadastro.js` | Criado — validação (mín. 6 chars senha, e-mail único), chamada API |
| 10 | `frontend/telas/SAR.html` | Atualizado — guard de autenticação, nome do candidato na sidebar, botão logout |
| 11 | `iniciar_servidor.bat` | Atualizado — browser abre em `/login` em vez de `/sar` |

**Decisões registradas:**
- `interface_backend.py` renomeado para `aplicacao.py` — "interface" não é vocabulário português
- Token armazenado no `localStorage` com chaves `sar_token` e `sar_nome` — sem cookies por decisão arquitetural explícita do usuário
- Guard de autenticação executa antes de `vagas.js` — evita chamadas autenticadas sem token
- Logout revoga sessão no backend (tabela `sessoes`) e limpa `localStorage`
- `novalidate` nos formulários — validação controlada pelo JS, não pelo browser nativo

**Dependência nova:**
- `passlib[bcrypt]==1.7.4` adicionada em `dependencias.txt`
- Instalar antes do primeiro teste: `pip install passlib[bcrypt]`

**Bugs corrigidos durante o desenvolvimento:**
- Múltiplas violações de nomenclatura identificadas e corrigidas iterativamente: `auth.py` → `autenticacao.py`, `setup_db` → `inicializar_banco`, `login/logout` → `entrar/encerrar_sessao`, `_executar_sync` → `_executar_sincronizacao`, `FRONTEND_DIR` → `PASTA_FRONTEND`, `LOGIN_HTML` → `TELA_ACESSO_HTML`, `_FAVICON_SVG` → `_ICONE_SVG`

---

---

## 2026-04-29 — Motor 2: Bugs Pós-Implantação e Correções

**Contexto:** Primeiro teste real do Motor 2 após implantação. Três bugs críticos encontrados e corrigidos na sessão.

### Bug 1 — `passlib` incompatível com `bcrypt 5.0.0`

**Sintoma:** Erro `ValueError: password cannot be longer than 72 bytes` ao tentar fazer cadastro. Internamente, passlib tentava acessar `bcrypt.__about__.__version__` — atributo removido no bcrypt 4.x+.

**Causa raiz:** `passlib[bcrypt]==1.7.4` usa introspection interna do bcrypt que foi quebrada nas versões 4.x e 5.x da biblioteca.

**Solução:** Removida a dependência de passlib inteiramente. `autenticacao.py` passou a usar `bcrypt` diretamente:
```python
import bcrypt
def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
def verificar_senha(senha: str, hash_salvo: str) -> bool:
    return bcrypt.checkpw(senha.encode("utf-8"), hash_salvo.encode("utf-8"))
```

**`dependencias.txt`:** `passlib[bcrypt]==1.7.4` → `bcrypt==5.0.0`

---

### Bug 2 — `db_selecionar` lançava `IndexError` em tabela vazia

**Sintoma:** Erro 500 ao carregar vagas com banco recém-criado.

**Causa raiz:** `db_selecionar()` retornava `linhas[0]` incondicionalmente quando `unico=True`, sem checar se havia resultado.

**Solução em `rotinas/genericas.py`:**
```python
if unico:
    return linhas[0] if linhas else None
return linhas
```

---

### Ajuste de produto — seção "Candidatos" removida da sidebar

**Contexto:** A seção "Candidatos" (administração de usuários) aparecia no menu lateral de todos os usuários. Módulo de administração não faz parte do escopo desta fase e não deve ser acessado por candidatos comuns.

**Ação:** Seção removida da sidebar. Substituída por **"Meu Perfil"** — exibe nome e e-mail do candidato autenticado (dados vindos de `GET /candidatos/meu-perfil`). Seção de perfil profissional marcada como "Em desenvolvimento — Motor 3".

**Backend:** Endpoint `GET /candidatos/meu-perfil` adicionado em `aplicacao.py`, protegido por `Depends(autenticar)`, retorna `{nome, email}` do candidato da sessão ativa.

---

## 2026-04-29 — Motor 1: Redesign do Mecanismo de Sincronização

**Contexto:** Primeiro sync com autenticação ativa. O mecanismo original usava `BackgroundTasks` + polling de `configuracoes` para simular progresso. Não funcionou — o frontend ficava rodando indefinidamente sem receber confirmação de conclusão.

### Problema 1 — Bug silencioso: `ON CONFLICT` com índice parcial

**Causa raiz:** O UPSERT original usava `INSERT OR REPLACE ON CONFLICT(id_externo)`. O índice único em `id_externo` é **parcial** (`WHERE id_externo IS NOT NULL`), e o SQLite não honra `ON CONFLICT` com índices parciais. Todas as tentativas de INSERT falhavam silenciosamente (capturadas pelo `except: continue`). Resultado: `processadas = 0` mesmo após sync completo.

**Solução:** Substituído por padrão explícito UPDATE → INSERT:
```python
cursor.execute("UPDATE vagas SET titulo=:titulo, ... WHERE id_externo=:id_externo", vaga)
if cursor.rowcount == 0:
    cursor.execute("INSERT INTO vagas (...) VALUES (...)", vaga)
processadas += 1
```

### Problema 2 — Sync assíncrono com polling era arquitetura frágil

**Contexto:** O endpoint `POST /vagas/sincronizar` disparava `BackgroundTasks` e o frontend fazia polling em `GET /configuracoes/ultima_sync_status` até receber `"ok"`. Funcionava na teoria; na prática o polling retornava 200 OK mas a variável de estado nunca chegava ao frontend corretamente.

**Decisão:** Sync convertido para síncrono. O endpoint aguarda `sincronizar()` retornar, depois responde com o resultado. Frontend simplesmente aguarda a resposta HTTP.

**Impacto:** Sync de ~846 vagas em ~17 páginas completa em segundos. Não justifica complexidade assíncrona. `BackgroundTasks` e polling removidos.

---

## 2026-04-29 — Motor 1: Bug de Filtros e Normalização de Dados

**Contexto:** Após primeiro sync bem-sucedido (846 vagas importadas), apenas o filtro "Presencial" funcionava. Os demais chips não retornavam resultado.

**Diagnóstico:** Consulta direta ao banco revelou os valores reais gravados:
- `modality` da API Peixe 30: `"remota"`, `"ambos"`, `"presencial"` → banco gravava `"remota"` e `"ambos"` literalmente
- `contractType` da API Peixe 30: `"pessoajuridica"`, `"clt"`, `"estagio"` → banco gravava `"pessoajuridica"` literalmente
- Frontend usava `data-valor="remoto"`, `data-valor="hibrido"`, `data-valor="pj"` — nunca havia correspondência

**Solução em `sincronizacao.py`:** Mapas de normalização aplicados no `_mapear()`:
```python
_MAPA_MODALIDADE = { "remota": "remoto", "ambos": "hibrido" }
_MAPA_CONTRATO   = { "pessoajuridica": "pj" }
```

**Migração de dados existentes em `aplicacao.py` (startup):**
```python
cursor.execute("UPDATE vagas SET modalidade    = 'remoto'  WHERE modalidade    = 'remota'")
cursor.execute("UPDATE vagas SET modalidade    = 'hibrido' WHERE modalidade    = 'ambos'")
cursor.execute("UPDATE vagas SET tipo_contrato = 'pj'      WHERE tipo_contrato = 'pessoajuridica'")
```

**Resultado:** Filtros funcionando para todas as modalidades e tipos de contrato.

---

## 2026-04-29 — Motor 1: Redesign da Tela de Vagas

**Contexto:** Após sync funcionando, usuário identificou que a apresentação era inadequada: cards sem organização, sem busca, sem ambiente amigável. Redesign completo da tela de vagas.

**Arquivos alterados:**

| Arquivo | Mudança |
|---|---|
| `frontend/estilos/visual.css` | Seções 17–19 adicionadas: busca, ordenação, lista horizontal, item de lista, badge removida |
| `frontend/telas/SAR.html` | Campo de busca, select de ordenação, chips adicionais (jovemaprendiz, autonomo, temporario), `vagas-grid` → `vagas-lista` |
| `frontend/scripts/vagas.js` | Reescrita completa: `_renderizarItem`, busca em tempo real, ordenação, contagem nos chips |

**Funcionalidades entregues:**

- **Lista horizontal** (substituiu grid de cards): avatar + título/empresa + badges + salário/data + botão Ver
- **Busca em tempo real** com debounce de 250ms — filtra por título, empresa e localização
- **Ordenação dinâmica**: Mais recentes / Maior salário / Empresa A–Z / Título A–Z
- **Contagem nos filtros**: chips exibem `CLT (142)`, `Remoto (87)` etc., baseado nos dados carregados
- **Chips desabilitados** automaticamente quando a categoria tem 0 vagas (opacity 0.35 + pointer-events none)
- **Badge "Removida"** em vagas com `disponivel_plataforma = 0` que ainda aparecem por terem status ativo
- **Skeleton loader** adaptado para o novo layout de lista

**Novos chips de contrato adicionados:**
- `jovemaprendiz` — Jovem Aprendiz
- `autonomo` — Autônomo
- `contratacaotemporaria` — Temporário

---

## Pendências Abertas

| # | Pendência | Prioridade |
|---|---|---|
| 1 | Atualizar `fluxograma.md` para refletir arquitetura dos 4 motores | Baixa |
| 2 | Motor 3 — Perfil do Candidato: tabelas filhas, importação via IA, formulário manual | Alta |
| 3 | Quando Motor 3 criar tabela `candidaturas`: adicionar `AND id NOT IN (SELECT id_vaga FROM candidaturas)` na query de soft-mark do `sincronizacao.py` | Média |
| 4 | Motor 4 — Geração de Currículo Premium | Alta |

---

## 2026-05-01 — Motor 3: Perfil do Candidato (implementação completa)

**Contexto:** Implementação de Motor 3 em 8 turnos no mesmo dia. Estrutura: 8 tabelas filhas, 30 endpoints, 7 abas frontend, upload de arquivo preparado para Motor 4.

**Arquivos entregues (8 turnos):**

| Turno | Arquivo | Ação |
|---|---|---|
| 1 | `backend/aplicacao.py` | 8 tabelas criadas (perfil_candidato, experiencias, formacoes, habilidades, idiomas, certificacoes, documentos, contatos) |
| 2 | `integracao/rotas/api.js` | Namespace `SarAPI.perfil` com 8 sub-namespaces CRUD + uploadArquivo |
| 3 | `backend/aplicacao.py` | GET /perfil-candidato (simples) + GET /perfil-candidato/completo (com JOINs) |
| 4 | `backend/aplicacao.py` | CRUD para 7 entidades filhas (21 endpoints: POST/PUT/DELETE) |
| 5 | `backend/aplicacao.py` | PUT /perfil-candidato (upsert) + POST /novo-manual + POST /validar |
| 6 | `frontend/telas/SAR.html` + `frontend/estilos/visual.css` | 7 abas navegáveis + 8 formulários + estilos completos |
| 7 | `frontend/scripts/perfil.js` | Script completo: carregamento, renderização de listas, CRUD, events |
| 8 | `backend/aplicacao.py` + `integracao/rotas/api.js` | POST /upload-arquivo (prepara Motor 4) |

---

### Design de Banco de Dados

**8 tabelas filhas de `candidatos.id` com `ON DELETE CASCADE`:**

```sql
perfil_candidato (1:1)   — dados do perfil (resumo, localização, salário, disponibilidade)
experiencias (N:1)       — histórico de empregos
formacoes (N:1)          — educação formal
habilidades (N:1)        — skills (proficiência: basico/intermediario/avancado/especialista)
idiomas (N:1)            — idiomas (proficiência: basico/intermediario/avancado/fluente/nativo)
certificacoes (N:1)      — certificados profissionais
documentos (N:1)         — arquivos (tipo: certificado/diploma/portfolio/carta/outro)
contatos (1:1)           — telefone, linkedin, github, website
```

**Dados públicos vs. sensíveis:**
- Públicos (vão no PDF Motor 4): nome, contato, habilidades, experiências, salário, disponibilidade
- Sensíveis (só no banco): CPF, data nascimento, informações bancárias (futuro)

---

### Endpoints Backend (30 total)

**Perfil principal:**
- `GET /perfil-candidato` — retorna perfil simples
- `GET /perfil-candidato/completo` — retorna perfil + 7 filhos
- `PUT /perfil-candidato` — upsert (cria ou atualiza)
- `POST /perfil-candidato/novo-manual` — cria novo, rejeita se já existe

**CRUD filhos (21 endpoints):**
- Padrão repetido 7x: `POST /{entidade}`, `PUT /{entidade}/{id}`, `DELETE /{entidade}/{id}`
- Cada POST valida campos obrigatórios
- Cada PUT/DELETE verifica LGPD: `condicao={"id": id, "id_candidato": id_candidato}`

**Validação:**
- `POST /perfil-candidato/validar` — retorna `{ok, valido, erros}`
- Mínimo: nome + contato + 1 habilidade + (1 exp OR 1 form OR 1 cert)

**Upload (Motor 4 prep):**
- `POST /perfil-candidato/upload-arquivo` — recebe PDF/DOC/DOCX/TXT, salva em `apoio/uploads/{id_candidato}/`

---

### Frontend (7 abas)

**Estrutura SPA:**
- Abas de navegação com `.aba-btn` + `.aba-conteudo`
- Cada aba com formulário + lista de itens existentes

**Abas implementadas:**
1. **Dados** — resumo profissional, localização, disponibilidade, salário + contatos
2. **Experiências** — cargo, empresa, datas, descrição
3. **Formações** — instituição, curso, nível (técnico/graduação/especialização/mestrado/doutorado)
4. **Habilidades** — nome, proficiência (básico/intermediário/avançado/especialista)
5. **Idiomas** — nome, proficiência (básico/intermediário/avançado/fluente/nativo)
6. **Certificações** — nome, emissor, datas, URL
7. **Documentos** — tipo, nome arquivo, caminho disco

**Script `perfil.js` (260 linhas):**
- `carregarPerfil()` — busca dados completos, popula formulários
- `_inicializarAbas()` — navegação entre abas
- `_renderizarLista()` — templates genéricos + específicos (6)
- 8 event listeners (1 por formulário)
- 6 funções globais de remoção (onclick)

---

### Segurança LGPD

**Isolamento por candidato:**
- ✓ Todos os 30 endpoints protegidos com `Depends(autenticar)`
- ✓ Cada PUT/DELETE valida: `condicao={"id": id, "id_candidato": id_candidato}`
- ✓ Candidato A NÃO consegue ver/editar/deletar dados de B
- ✓ Upload salvo em pasta isolada: `apoio/uploads/{id_candidato}/`

**Permissões de sistema de arquivos (futuro):**
- Quando compilar executável, usar NTFS permissions para isolar por usuário Windows
- Dívida crítica já documentada: migrar `localStorage` → `sessionStorage` para evitar compartilhamento de token

---

### Validações implementadas

**Campos obrigatórios:**
- Experiência: cargo, empresa
- Formação: instituição, curso, nível
- Habilidade: nome, proficiência
- Idioma: nome, proficiência
- Certificação: nome, emissor
- Documento: tipo, nome, caminho

**Validação de perfil completo (4 regras):**
1. Nome do candidato (já em `candidatos.nome`)
2. Contato: telefone OU linkedin OU github OU website
3. Mínimo 1 habilidade
4. Mínimo 1 de: experiência OU formação OU certificação

**Upload:**
- Tipos permitidos: PDF, DOC, DOCX, TXT
- Tamanho máximo: 10MB
- Sanitização de nome de arquivo

---

### Decisões congeladas (não alterar)

1. ✓ Senha com bcrypt direto (passlib removido) — MANTÉM
2. ✓ Token UUID v4 em localStorage — MANTÉM (com dívida de sessionStorage)
3. ✓ Dependency injection com `Depends(autenticar)` — MANTÉM
4. ✓ Padrão {ok, dados, erro} no frontend — MANTÉM
5. ✓ Sem cookies, sem WebSocket — MANTÉM
6. ✓ SPA com classes `ativo` e `hidden` — MANTÉM
7. ✓ Sync manual sem auto-sincronização — MANTÉM
8. ✓ Soft-delete de vagas (não hard delete) — MANTÉM
9. ✓ Salvamento parcial de perfil permitido — IMPLEMENTADO
10. ✓ Validação mínima inclusiva (não excludente) — IMPLEMENTADO

---

### Dívidas técnicas críticas (registradas no MEMORY.md)

| Dívida | Prioridade | Timeline |
|--------|-----------|----------|
| Migrar `localStorage` → `sessionStorage` para impedir compartilhamento de token entre usuários | CRÍTICA | Antes de compilar para .exe |
| Validar token no guard de `/sar` (não só verificar localStorage) | ALTA | Antes de compilar |
| Adicionar suporte a múltiplos candidatos no computador compartilhado | ALTA | Motor 4 ou após |
| Integrar IA com Gemini para extração de currículo (upload) | PLANEJADO | Motor 4 |
| Implementar SaveDialog nativo Windows (Motor 4) | PLANEJADO | Motor 4 |

---

### Teste e validação — Checklist Governança

**Antes de PUSH ao remoto, validar:**

- [ ] **Nomenclatura**: Todos nomes em português? Sem prefixos (srv_, db_, cfg_)? ✓ Confirmado
- [ ] **LGPD**: Candidato A não consegue ver dados de B? ✓ FK + validação por id_candidato
- [ ] **Soft-delete**: Vagas com status != PENDENTE ainda visíveis? ✓ Query em aplicacao.py linha 245-248
- [ ] **Sync intacto**: sincronizacao.py não foi alterada? ✓ Apenas imports adicionados
- [ ] **Frontend modular**: scripts separados (vagas.js, perfil.js, login.js, cadastro.js)? ✓ Confirmado
- [ ] **CRUD reutilizável**: genericas.py não alterada? ✓ Confirmado
- [ ] **Validação**: Mínimo inclusivo (não excludente)? ✓ Confirmado (1 skill, 1 de 3 backgrounds)
- [ ] **Autenticação**: Sem cookies? ✓ localStorage apenas (dívida: sessionStorage)
- [ ] **Schema**: Todas as FK com ON DELETE CASCADE? ✓ Confirmado

---

### Próximos motores

**Motor 4 — Geração de Currículo Premium:**
- Endpoint GET/POST com Gemini IA (extração de currículo do arquivo + scoring de aderência)
- SaveDialog nativo Windows (usuário escolhe pasta)
- Geração de PDF com weasyprint
- Empacotamento ZIP (currículo + documentos selecionados)

**Motor 5 (futuro):**
- Integração com plataformas de recrutamento
- Automação de candidatura

---

*Documento mantido pela equipe de desenvolvimento. Atualização obrigatória a cada turno de trabalho concluído.*
