# Diário de Bordo — SAR (Sistema de Automação de Recolocação)

Registro cronológico de decisões, entregas, curvas e erros do projeto.
Documento obrigatório — atualizado ao final de cada tarefa concluída.
Garante rastreabilidade, legado e prevenção de recorrência de erros.

---

## 2026-05-18 — Sessão de correções críticas, agnóstico e empacotamento

**Correções críticas validadas:**
- Base de análise corrigida: `_obter_base_perfil()` passa a usar sempre `_montar_perfil_texto()` — currículos premium gerados são produto final, nunca fonte de análise. Eliminava score 0% para vagas fora da área jurídica
- Merge incremental na importação: substituído DELETE + INSERT por lógica de deduplicação por chave natural — dados existentes preservados, apenas novos registros inseridos
- Prompts totalmente agnósticos: `_PROMPT_SCORE`, `_PROMPT_RECRUTADOR` e `_PROMPT_CURRICULO` removem referência a "Direito brasileiro" — sistema avalia qualquer área profissional
- `_PROMPT_RECRUTADOR` reformulado: recrutador orientado a identificar lacunas de informação (não de capacidade), aprofundando especificamente nos requisitos da vaga

**Melhorias de perfil e UI:**
- Botão "Adicionar currículo" substitui "Reimportar" — semântica correta, sem risco de sobrescrita
- Botão "Salvar alterações" adicionado ao perfil
- `Cache-Control: no-store` em todos os arquivos estáticos — elimina necessidade de Ctrl+Shift+R
- Tela Sobre atualizada: professora/coordenadora Waleria Medeiros Lima, 10 membros em ordem alfabética, card do desenvolvedor com nome e links corretos

**Distribuição — versão demo acadêmica:**
- `servidor.py`: trava de expiração em 30/06/2026
- `servidor.py`: leitura de `.env` e `sar.key` remotamente via URLs no `instalacao.dat` (`%APPDATA%\SAR\`)
- Modo dev (sem `instalacao.dat`) usa `.env` local — sem regressão no ambiente de desenvolvimento
- `instalar.bat`: copia `instalacao.dat` para `%APPDATA%\SAR\` e cria atalho na área de trabalho
- `modo_dev.bat`: remove `instalacao.dat` reativando modo desenvolvimento
- PyInstaller: `SAR.exe` autocontido com Python, frontend, integracao e certificado SSL embutidos
- Abertura automática do browser em `https://127.0.0.1:8000/login` no modo frozen
- `sys._MEIPASS` usado como RAIZ no modo frozen em `servidor.py` e `aplicacao.py`

**Pendente:**
- Inno Setup: geração de `SAR_Setup.exe` instalador profissional
- Múltiplos currículos base por candidato (arquitetura discutida — implementação futura)
- Tom adaptativo do Recrutador IA (sênior vs. jovem aprendiz)
- Carta de apresentação gerada pela IA
- Pacote ZIP (currículo + carta + documentos)
- Link externo (DA-03) após ciclo completo

---

## 2026-05-25 — Tela home, responsividade e card EXPODPT

**Tela Home:**
- Sidebar lateral removida (oculta via CSS — lógica JS preservada no DOM)
- Nova `#secao-home` com imagem de fundo `tela_fundo.png` gerada por IA
- 4 cards de acesso rápido: Explorar Vagas, Meu Perfil, Currículo Premium, Sobre
- Barra de status fixa no rodapé: logo SAR (clicável → home), status de conexão, nome e logout
- Botão `← Início` em todas as seções para retornar à home
- Saudação dinâmica (Bom dia/tarde/noite + primeiro nome do candidato)
- `app.mount("/imagens")` adicionado ao backend para servir `apoio/Imagens/` como estático

**Responsividade — abordagem profissional:**
- Variável `--vh` calculada via JS (`window.innerHeight * 0.01`) — corrige o bug de `100vh` no Safari/Chrome mobile que não desconta barras do browser
- Atualizada em `resize` e `orientationchange` (com delay de 150ms para estabilizar após rotação)
- `app-layout` usa `height: calc(var(--vh, 1vh) * 100)` em vez de `100vh` fixo
- Home reescrita com classes semânticas (`home-secao`, `home-corpo`, `home-card--*`) — sem inline styles
- Fundo e gradiente com `position: fixed` — cobrem a tela independente do tamanho do conteúdo
- Home com `overflow-y: auto` — scroll nativo em qualquer resolução
- Breakpoints: mobile ≤ 600px | tablet portrait 601–768px | tablet landscape 769–1024px | desktop ≥ 1025px
- Cards de vaga no mobile: CSS Grid com áreas nomeadas (`info / meta / badges / acoes`) — sem cortes laterais
- Avatar oculto no mobile (inicial da empresa sem contexto visual)
- Filtros: chips no desktop, dois selects (Contrato + Modalidade) no mobile — sincronizados com `_filtrosAtivos`
- Modais: bottom-sheet no mobile, centralizados no tablet/desktop

**Card EXPODPT:**
- `apoio/Imagens/card_expodpt.html` — card 1080×1080px para divulgação do evento acadêmico
- Prompt gerado para IA de imagem (Gemini Nano Banana 2) — card final aprovado pela equipe em votação
- `apoio/Imagens/tela_fundo.png` — imagem de fundo do sistema gerada com mesmo prompt (sem textos)
- `apoio/Imagens/logo_nassao.png` — logo oficial UNINASSAU

---

## 2026-05-13 — Ponto de parada — agenda da próxima sessão

**Implementado hoje (pendente teste físico — NÃO commitar antes de validar):**
- Restauração do histórico de chat e score ao retornar à seção Currículo Premium
  - Corrigido double-wrap: `conv.dados.dados.historico` (era `conv.dados.historico`)
  - Flag `_curriculoGerado` controla estado: entrevista em andamento ≠ currículo já gerado
  - Botão "← Voltar ao currículo" no chat quando há currículo gerado
- Editor de texto: `contenteditable="true"` no `div#curriculos-texto-display`
  - Copiar e PDF leem via `innerText` (refletem edições do candidato)
  - CSS: cursor `text`, borda azul no foco
- Aviso não-bloqueante de vaga indisponível (banner amarelo)
- `_prepararCandidatura()` centraliza lógica dos dois pontos de entrada (card + modal)

**Testes obrigatórios antes de commitar:**
1. Restauração: sair do sistema, voltar, verificar se histórico e score aparecem corretamente
2. Editor: gerar currículo, editar o texto, verificar se "Copiar" e "PDF" refletem as edições
3. Aviso: clicar "Preparar" em vaga com `disponivel_plataforma = 0` e verificar banner

**Agenda da próxima sessão — executar nesta ordem:**
1. Validar os testes acima e commitar
2. Prompts agnósticos — `_PROMPT_RECRUTADOR` e `_PROMPT_CURRICULO` sem referência a área jurídica
3. Tom adaptativo — Recrutador identifica perfil (sênior / jovem aprendiz) e ajusta linguagem e perguntas
4. Carta de apresentação — gerada pela IA junto com o currículo, personalizada para a vaga
5. Pacote ZIP — currículo PDF + carta + documentos apensos, salvo no Desktop
6. Link externo (DA-03) — botão "Candidatar-me" liberado após pacote gerado
7. Certificação end-to-end — teste completo do fluxo importação → entrevista → score 75% → geração → edição → PDF → candidatura

---

## 2026-05-11 — Motor 4 Blocos 3–6: Entrevista IA, Score, Currículo Premium, Restauração de Sessão (Implementado)

**Ações:**
- Implementada entrevista guiada com Recrutador IA — uma pergunta por vez, histórico persistido na tabela `conversas`
- Score de aderência progressivo exibido em barra visual com marca de 75% — botão "Gerar currículo" liberado ao atingir a meta
- Upload de documentos complementares durante a entrevista (📎) — texto extraído enviado à IA como contexto adicional
- Geração de currículo personalizado por vaga via IA — cada geração salva como arquivo `.txt` independente com timestamp (DA-02)
- Prompt ABNT: estrutura rígida definida no `_PROMPT_CURRICULO` — sem markdown, sem datas nos cabeçalhos de seção, formato `Mês/AAAA`, candidato multidisciplinar
- PDF via `window.print()` com `@page { size: A4; margin: 2cm }` — suprime cabeçalho/rodapé do browser, fonte Times New Roman
- Exibição do currículo como `div.curriculo-display` com texto justificado e `white-space: pre-wrap` — substituída textarea monospace
- Camada IA abstrata `rotinas/ia.py` — Gemini primário + Groq fallback automático com tratamento de quota
- Onboarding gate: menus Vagas e Currículo Premium bloqueados até importar currículo — desbloqueio automático após importação
- Restauração de sessão: `GET /perfil-candidato/curriculos-gerados` retorna todos os currículos com conteúdo — ao retornar ao sistema o último gerado é exibido automaticamente
- Prompt de importação corrigido — removida referência exclusiva ao mercado jurídico; candidato multidisciplinar contemplado

**Correções críticas:**
- Regressão de onboarding: `verificarOnboarding` checava `resultado.dados.perfil.id` (undefined) — corrigido para `resultado.dados.dados` (path real após double-wrap do `_requisitar`)
- Mesma correção em `_iniciarChat`: `checaPerfil.dados.id` → `checaPerfil.dados.dados`

**Decisões:**
- DA-02 reforçada: múltiplos currículos premium por candidato — nunca sobrescritos, todos usados como contexto multidisciplinar pela IA
- `_obter_base_perfil`: lê TODOS os `curriculo_gerado` do candidato e os combina como seções rotuladas — IA vê o perfil completo, não apenas o mais recente
- PDF por `window.print()` em vez de weasyprint — solução leve sem dependência adicional; weasyprint avaliada para versão futura
- Tabelas `candidaturas` e `curriculos_gerados` substituídas por uso da tabela `conversas` (chat) e `documentos` (arquivos gerados) — arquitetura simplificada sem perda funcional

**Resultado:** Motor 4 com fluxo completo implementado — importação → perfil → entrevista IA → score → geração ABNT → PDF → restauração de sessão. **Pendente teste físico end-to-end.**

---

## 2026-05-10 — Motor 4 Bloco 2: Modal "Ver descrição" + botão "Preparar candidatura" (Implementado)

**Ações:**
- Substituído botão `Ver ↗` (link externo) por dois botões empilhados em cada card de vaga: "Ver descrição" e "Preparar"
- Criado modal interno `#modal-vaga` em `SAR.html` com cabeçalho, badges, corpo com descrição e rodapé com "Preparar candidatura"
- Adicionadas funções `_abrirModalVaga`, `_fecharModal`, `_inicializarModal` em `vagas.js`
- Modal usa delegação de eventos no `vagas-lista` (itens renderizados dinamicamente)
- Modal fecha via botão ✕, clique fora da caixa ou tecla Escape
- "Preparar" (card) e "Preparar candidatura" (modal) navegam para seção Currículos dentro do SPA — stub para próximos blocos
- Adicionados estilos `.item-acoes` e todo o stack `.modal-*` em `visual.css`

**Decisões:**
- DA-03 aplicada: link externo removido completamente dos cards de vagas
- Dados do modal preenchidos a partir de `_todasVagas` (memória) — zero chamadas extras ao backend
- `ConnectionResetError [WinError 10054]` no console do uvicorn é ruído do Windows (socket fechado pelo browser), não indica falha

**Resultado:** Cards de vagas sem link externo. Modal interno operacional. Bloco 2 implementado — **pendente teste físico**.

---

## 2026-05-08 — Motor 4 Bloco 1: Importação de Currículo com IA (Validado)

**Ações:**
- Instaladas dependências: `pdfplumber==0.11.9`, `python-docx==1.2.0`, `google-generativeai==0.8.6`
- Criado `backend/rotinas/importacao.py`: extração de texto PDF/DOCX + chamada Gemini
- Adicionado endpoint `POST /perfil-candidato/importar` em `aplicacao.py`
- Adicionado `SarAPI.perfil.importar(arquivo)` em `api.js`
- Expandida `secao-perfil` em `SAR.html` com 3 estados: importar / processando / completo
- Implementados todos os blocos de complementação manual (experiências, formações, habilidades, idiomas, certificações)
- Carregamento de `perfil.js` reativado em `SAR.html`
- Corrigido conflito de escopo: `const el` renomeado para `const elPerfil` em `perfil.js`

**Decisões / Problemas resolvidos:**
- `google-generativeai==0.8.6` usa `v1beta`; `gemini-1.5-flash` não disponível nessa versão da API
- Modelo confirmado via `list_models()`: `gemini-2.5-flash` operacional na chave configurada
- `gemini-2.0-flash` e `gemini-2.0-flash-lite` retornam quota `limit: 0` no free tier desta conta
- `load_dotenv()` sem caminho explícito não encontrava `.env` na raiz do projeto; corrigido com `Path(__file__).resolve().parent.parent.parent / ".env"`
- Conflito de variável global `const el` entre `vagas.js` e `perfil.js` causava `SyntaxError` silencioso que impedia todos os event handlers; corrigido renomeando para `elPerfil`

**Resultado:** Importação de PDF/DOCX → Gemini extrai → 8 tabelas populadas automaticamente — **validado fisicamente em 2026-05-08**.

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

## 2026-05-01 — Correção Arquitetural Crítica: Unicidade e Consistência do Banco

**Contexto:** Teste físico de Motor 3 revelou banco de dados vazio. Investigação identificou dois arquivos de banco em disco (`/armazenamento_dados/` e `/backend/armazenamento_dados/`), criados por `DB_PATH` relativo em `genericas.py` dependente do CWD no momento da inicialização. Candidatos cadastrados em sessões anteriores perdidos por gravação em banco diferente do lido.

**Causa raiz:** `DB_PATH = "armazenamento_dados/sar_repositorio.db"` — path relativo sem âncora absoluta.

**Correções aplicadas (5 arquivos):**

| Arquivo | Correção |
|---------|----------|
| `backend/rotinas/genericas.py` | DB_PATH → `%APPDATA%\SAR\sar_repositorio.db` — portável, isolado por usuário Windows |
| `backend/aplicacao.py` | 3 chamadas diretas `sqlite3.connect()` → `_obter_conexao()` |
| `backend/rotinas/sincronizacao.py` | `sqlite3.connect()` direto → `_obter_conexao()` + PRAGMA redundante removido |
| `integracao/rotas/api.js` | `obterNome()` usava `localStorage` — corrigido para `sessionStorage` (legado de antes da migração de segurança) |
| `documentacao/governanca.md` | Seção 3.1 adicionada: regras invioláveis sobre banco, paths e ponto único de acesso |

**Decisão de produto — AppData:**
Banco reside em `%APPDATA%\SAR\sar_repositorio.db`. Padrão Windows para dados de aplicação: portável, sem permissão de admin, isolado por usuário, funciona em executável compilado. Elimina dependência de estrutura de pastas do projeto.

**Garantia pós-correção:**
`sqlite3.connect()` existe apenas em `backend/rotinas/genericas.py`. Verificado via grep. Todo acesso ao banco passa por `_obter_conexao()`.

**Status de teste:** Aguardando teste físico em próxima sessão. Commit e push realizados com ressalva.

**Dívidas encerradas nesta sessão:**
- ~~Migrar `localStorage` → `sessionStorage` em `obterNome()`~~ — RESOLVIDO
- ~~DB_PATH relativo causando múltiplos bancos~~ — RESOLVIDO

---

### Próximos motores

**Motor 4 — Geração de Currículo Premium:**
- Endpoint GET/POST com Gemini IA (extração de currículo do arquivo + scoring de aderência)
- PDF via `window.print()` com formatação ABNT (solução definitiva — sistema 100% web)

**Motor 5 (futuro):**
- Integração com plataformas de recrutamento
- Automação de candidatura

---

## 2026-05-02 — Teste Físico Motor 3: Pendências Levantadas

**Contexto:** Primeiro teste físico real do Motor 3 após correção arquitetural do banco. Quatro pendências identificadas pelo usuário — nenhum código alterado nesta sessão.

---

### Pendência 1 — Tela de Cadastro: Confirmação de Senha e Visibilidade
- Falta campo de **confirmação de senha** para evitar erro de digitação silencioso
- Falta **botão olho** (toggle de visibilidade) nos campos de senha
- Risco: usuário cadastra senha errada sem perceber e perde acesso à conta

### Pendência 2 — Tela de Vagas: Filtro por Localidade
- Adicionar combobox (select) no canto superior direito, ao lado dos botões de sincronização e classificação
- Popular dinamicamente com localidades distintas: `SELECT DISTINCT localizacao FROM vagas`
- Aplicar `WHERE localizacao = ?` na listagem em conjunto com busca textual
- Valor padrão: "Todas as localidades"
- Objetivo: estreitar conjunto por localidade, busca textual refina dentro do conjunto

### Pendência 3 — UX Perfil: Avaliar Página Única vs Abas
- Usuário tem aversão a troca de páginas desnecessária
- Avaliar substituição das 7 abas por layout de página única (scroll contínuo ou seções colapsáveis)
- Manter organização visual sem forçar navegação entre abas

### Pendência 4 — Bug Crítico: Formulários das Abas do Perfil Não Abrem
- Abas do perfil criadas mas formulários não respondem ao clique
- Provável desconexão entre `data-aba` nos botões e `.aba-conteudo` no HTML
- Bloqueia uso completo do Motor 3 — prioridade alta

---

**Status:** Teste físico **NÃO CONCLUÍDO** — interrompido após levantamento das 4 pendências. Retomar na próxima sessão antes de qualquer avanço de funcionalidade.

---

## 2026-05-03 — Alinhamento de Documentação: Correção Cirúrgica

**Contexto:** Início de nova sessão com leitura completa da governança, skill `dev-governado` e todos os arquivos de memória. Identificado que `plano_de_desenvolvimento.md` e `fluxograma.md` estavam severamente desatualizados — Motors 2 e 3 apareciam como não implementados, nomes de tabelas estavam incorretos e referências a arquivos renomeados persistiam.

**Ações:**
- Leitura de `.instructions.dev-governado.md`, `governanca.md` e todos os 5 arquivos de memória
- Atualização cirúrgica de `plano_de_desenvolvimento.md` (9 edições pontuais, nenhuma reescrita)
- Atualização cirúrgica de `fluxograma.md` (5 edições pontuais, nenhuma reescrita)

**Correções aplicadas em `plano_de_desenvolvimento.md`:**
- Data de atualização: `2026-04-28` → `2026-05-03`
- `interface_backend.py` → `aplicacao.py` (hierarquia de pastas + tabela Fase 1)
- `localStorage` → `sessionStorage` (descrição Motor 2)
- Motor 2: status ⏳ → ✅, todos os itens ❌ → ✅
- Motor 3: status ⏳ → ✅, itens atualizados com pendências reais identificadas em 2026-05-02
- Nomes de tabelas corrigidos: `perfis` → `perfil_candidato`, `candidato_*` → nomes reais do banco
- Tabela `contatos` adicionada ao esquema (existia no banco, ausente na documentação)
- `candidatos` movida de "Tabelas previstas" para "Tabelas existentes"

**Correções aplicadas em `fluxograma.md`:**
- Data: `2026-04-27` → `2026-05-03`
- Roadmap de fases reescrito para refletir arquitetura por Motores (1, 2, 3, 4)
- Fase ativa atualizada: Fase 1 → Motor 3 (implementado, certificação pendente)
- Seções Concluído/Pendente/Próximo atualizadas com estado real
- DB path: `armazenamento_dados/sar_repositorio.db` → `%APPDATA%\SAR\sar_repositorio.db`
- `interface_backend.py` → `aplicacao.py` no diagrama de fluxo de dados
- Próximos passos: substituídas tarefas antigas por pendências reais do Motor 3 e Motor 4

**Registro de conduta:**
- Memória `feedback_intervencao_incremental.md` criada: intervenções devem ser sempre pontuais e cirúrgicas, nunca reescritas totais.

**Status:** Documentação alinhada com estado real do projeto. Próximo passo: resolver bug crítico (Pendência 4 — formulários das abas do perfil).

---

## 2026-05-03 — Implementações Motor 3 + Decisões Arquiteturais Motor 4

### Implementações realizadas — aguardando teste físico do usuário para atestação

**Regressão de login:** usuário cadastrado com typo no e-mail (`riccg_@hgotmail.com` → `riccg_@hotmail.com`). Banco íntegro (610 KB). Correção cirúrgica via SQL parametrizado — nenhum arquivo de código alterado.

**Bug duplo aninhamento `/perfil-candidato/completo`:** endpoint retornava `{ ok, dados: { perfil, ... } }` causando duplo wrapper com `_requisitar`. Frontend acessava `dados.perfil` mas recebia `undefined`. Corrigido em `aplicacao.py` — flat dict direto.

**Tags orphans `SAR.html`:** `</div></section>` após fechamento correto de `secao-perfil`. Removidos.

**Cadastro — confirmação de senha + eye toggle:** campos e botões adicionados em `cadastro.html`, validação e toggle em `cadastro.js`, estilos `.input-senha-wrapper` e `.btn-olho` em `visual.css`.

**Vagas — filtro de localidade:** select `select-localidade` adicionado em `SAR.html`, lógica `_popularLocalidades` + estado `_localidade` + filtro em `_aplicarFiltros` adicionados em `vagas.js`.

### Decisões arquiteturais registradas

**DA-02 — Currículo como ativo reutilizável (2026-05-03):**
Motivação: candidato não pode perder trabalho produzido se vaga sumir durante a produção do currículo.
- Aviso não-bloqueante quando vaga fica indisponível — candidato decide se continua
- "Salvar como base" desvincula currículo da vaga para reaproveitamento futuro
- Nova candidatura oferece carregar base salva como ponto de partida
- Tabela `curriculos_gerados`: `status` = `rascunho` | `base_salva` | `finalizado`; `id_vaga` nullable

**DA-03 — Contenção na plataforma (2026-05-03):**
Motivação: "Ver ↗" enviava candidato para plataforma externa antes de estar preparado para candidatura.
- Botão "Ver ↗" removido do card de vagas
- "Ver descrição" → modal interno com dados do JSON local (zero chamada externa)
- "Preparar candidatura" → única entrada no Motor 4
- Link externo (`vagas.link`) liberado somente ao final do Motor 4

**Verificação periódica de disponibilidade (decidida, pendente de implementação):**
- Endpoint leve `GET /vagas/verificar-disponibilidade` — atualiza só `disponivel_plataforma`
- Ciclo automático a cada 20 minutos via frontend (`setInterval`)
- Comportamento: aviso não-bloqueante quando vaga fica indisponível durante uso ativo

---

## 2026-05-04 — Redefinição de Escopo Motor 3 / Motor 4 + Certificação Motor 3

### Decisão de escopo (2026-05-04)

**Contexto:** Durante o teste físico e revisão da tela "Meu Perfil", o usuário identificou inconsistência fundamental de fluxo: o sistema força o candidato a redigitar manualmente dados que já estão documentados no currículo existente.

**Decisão:** Redefinição das fronteiras de Motor 3 e Motor 4:

| Motor | Escopo correto |
|---|---|
| Motor 3 | Cadastro básico (nome, e-mail, senha) + Acesso (login, sessão, token) + Infraestrutura de dados (8 tabelas criadas) |
| Motor 4 | Importação de currículo existente (PDF/DOCX → IA extrai) + Complementação manual do perfil + Geração de currículo personalizado por vaga |

**Motivação:** Se o candidato já possui currículo com todas as informações, forçar redigitação é contra o propósito do sistema. O fluxo correto é: upload do currículo → IA popula perfil automaticamente → candidato complementa/revisa → seleciona vaga → Motor 4 gera currículo otimizado.

**Impacto em código:**
- `SAR.html` — `secao-perfil` simplificada: exibe apenas dados de acesso (readonly). Os 9 blocos de formulário removidos da interface (Motor 4).
- `perfil.js` — descarregado do `SAR.html`. Arquivo preservado no codebase para Motor 4.
- Backend: tabelas e endpoints de perfil intactos — prontos para Motor 4.

**Fases são controle interno:** Sinalização de fases ("Motor 4", "Em desenvolvimento") não é exposta ao candidato. O sistema apresenta experiência coerente — o que está disponível funciona, o que não está não aparece.

### Motor 3 — Certificado

Com o escopo correto definido, Motor 3 está **certificado**:
- ✅ Cadastro: nome, e-mail, senha, confirmação de senha, eye toggle
- ✅ Login: e-mail + senha → token UUID4 → sessionStorage
- ✅ Sessão: middleware protege todas as rotas, logout revoga token
- ✅ Tela principal: vagas, filtros, localidade, sync — funcionando
- ✅ Meu Perfil: exibe nome e e-mail do candidato autenticado
- ✅ Infraestrutura de banco: 8 tabelas de perfil criadas e prontas para Motor 4

### Próximo: Motor 4

Ordem de execução:
1. Importação de currículo (PDF/DOCX) → Gemini extrai dados → popula tabelas de perfil
2. Interface de complementação: blocos de experiências, formações, habilidades, idiomas, certificações
3. Modal "Ver descrição" + botão "Preparar candidatura" no card de vagas
4. Verificação periódica de disponibilidade de vagas (ciclo 20 min)
5. Score de aderência + geração do currículo personalizado
6. Exportação PDF via `window.print()` com formatação ABNT

---

---

## 2026-05-21 — Refinamentos Motor 4: Robustez de IA, Enriquecimento Incremental e Restauração de Sessão

### Correções e implementações aplicadas

**Fix fallback de IA (`rotinas/ia.py`):**
Qualquer exceção em qualquer provedor agora aciona o próximo — anteriormente apenas erros de cota/rate disparavam o fallback. Erros como `503 UNAVAILABLE` e `ConnectError` eram propagados imediatamente, bloqueando o sistema mesmo com provedores alternativos disponíveis.

**Fix score 0% para candidatos com habilidades técnicas (`rotinas/importacao.py`):**
`_PROMPT_SCORE` reescrito com 6 instruções obrigatórias: percorre perfil estruturado E currículo premium antes de calcular o score; proíbe score zero se houver habilidades técnicas relevantes declaradas; considera habilidades transferíveis (HTML/CSS/JS relevantes para vagas Front-End).

**Fix "Preparar candidatura" abrindo currículo de vaga anterior (`frontend/scripts/curriculos.js`, `vagas.js`):**
`iniciarGeracaoCurriculo` reseta `_curriculoGerado=false` de forma síncrona antes do nav click. `_prepararCandidatura` chama `iniciarGeracaoCurriculo` antes do `.click()`.

**Fix modal `addEventListener` em null (`frontend/telas/SAR.html`):**
Modais movidos para antes das tags `<script>` — scripts executavam antes dos elementos existirem no DOM.

**Fix BASE_URL sobrescrita na VM (`backend/servidor.py`):**
Variável `DOMINIO` no `.env` — quando definida, `atualizar_api_js` usa `https://{DOMINIO}` em vez de `https://{HOST}:{porta}`. Elimina sobrescrita com `0.0.0.0:1024` a cada startup.

**Enriquecimento incremental pós-entrevista (`rotinas/importacao.py`, `aplicacao.py`):**
Quando `pronto=True`, novo hook extrai via IA habilidades e experiências declaradas pelo candidato durante a entrevista e insere nas tabelas `habilidades` e `experiencias` — sem deletar, sem sobrescrever. Checagem de duplicatas por `nome` (habilidades) e `cargo+empresa` (experiências).

**Prompt do Recrutador IA refatorado (`rotinas/importacao.py`):**
- Verificação de contexto do histórico como primeira instrução (não no meio das regras)
- PROIBIDO inventar referências a conversas anteriores não registradas no histórico
- Instrução explícita de encerramento cordial pós-75%: pergunta sutil se candidato deseja acrescentar algo; se acrescentar algo pertinente, incorpora ao score e encerra; se não, encerra sem novas perguntas
- Instrução de leitura de perfil estruturado + currículo premium antes do cálculo de score

**Restauração de histórico ao retornar à seção (`curriculos.js`):**
Corrigido double-wrap: `dados.dados.historico` em vez de `dados.historico`. Ao restaurar conversa com `status=pronto`, reativa automaticamente o botão "Gerar Currículo Final" e restaura o score correto.

**Foto do desenvolvedor na página Sobre (`aplicacao.py`, `SAR.html`):**
Endpoints `GET /dev/foto` e `POST /dev/foto` — públicos, sem autenticação. Foto salva em `apoio/imagens/dev_foto.{ext}`. Avatar na página Sobre clicável: exibe foto se existir, fallback para iniciais "RA". Upload via `input[type=file]`, substituição automática de foto anterior.

---

*Documento mantido pela equipe de desenvolvimento. Atualização obrigatória a cada turno de trabalho concluído.*
