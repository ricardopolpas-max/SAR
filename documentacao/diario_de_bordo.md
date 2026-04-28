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

## Pendências Abertas

| # | Pendência | Prioridade |
|---|---|---|
| 1 | Teste real do sistema completo pelo usuário (servidor + `/sar` + Ctrl+C limpo) | Alta |
| 2 | Certificar Fase 1 como concluída após validação | Média |
| 3 | Atualizar `fluxograma.md` e `plano_de_desenvolvimento.md` para refletir estado atual | Média |

---

*Documento mantido pela equipe de desenvolvimento. Atualização obrigatória a cada turno de trabalho concluído.*
