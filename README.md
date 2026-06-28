# SAR — Sistema de Automação de Recolocação

Plataforma web local que integra IA generativa para automatizar a jornada de recolocação profissional. O candidato importa seu currículo existente, a IA extrai e estrutura o perfil automaticamente, conduz uma entrevista guiada e gera um currículo personalizado para cada vaga — com score de aderência calculado e exibido antes da geração.

Desenvolvido como projeto acadêmico por um desenvolvedor autodidata com formação em Direito, usando IA estritamente como ferramenta de produção de código. Toda lógica, arquitetura e decisões são do desenvolvedor, validadas por testes físicos ponta a ponta contra uma verdade absoluta definida.

**Stack:** Python 3.12 · FastAPI · SQLite · HTML/CSS/JS Vanilla · Google Gemini 2.5 Flash · Groq (fallback) · HTTPS obrigatório (mkcert)

---

## Arquitetura — Quatro Motores Funcionais

O sistema é estruturado em quatro motores independentes e interdependentes. Cada um tem responsabilidade única e alimenta o próximo.

**Motor 1 — Captura de Vagas**
Sincroniza vagas da API pública do Peixe 30 Jobs sob demanda. Usa o padrão UPDATE → INSERT (não UPSERT com índices parciais, que falhou silenciosamente no SQLite — ver comportamentos observados abaixo). Dados do candidato (status, score, notas) nunca são sobrescritos. Vagas removidas da plataforma são marcadas como indisponíveis, nunca deletadas — o candidato pode ter progresso vinculado a elas.

**Motor 2 — Identidade e Acesso**
Sistema com login obrigatório (modelo ERP). Autenticação via bcrypt + token UUID4 em sessionStorage, enviado como `Authorization: Bearer` em toda requisição. Tokens são auditáveis e revogáveis via tabela `sessoes`. Todas as queries são filtradas por `id_candidato` extraído do token validado — nenhum candidato acessa dados de outro.

**Motor 3 — Cadastro e Infraestrutura**
Gerencia o cadastro do candidato e cria a infraestrutura completa do banco (8 tabelas de perfil) prontas para o Motor 4: `perfil_candidato`, `experiencias`, `formacoes`, `habilidades`, `idiomas`, `certificacoes`, `documentos`, `contatos` — todas com `ON DELETE CASCADE`.

**Motor 4 — Importação, Perfil e Currículo Premium (núcleo de IA)**
A camada de inteligência do sistema:

1. Candidato faz upload do currículo existente (PDF ou DOCX)
2. IA extrai dados estruturados e popula as 8 tabelas de perfil (merge incremental, nunca sobrescreve)
3. Entrevista guiada com o Recrutador IA aprofunda o perfil — uma pergunta por vez, histórico persistido na tabela `conversas`
4. Após a entrevista, habilidades e experiências atestadas são inseridas incrementalmente nas tabelas de perfil (enriquecimento não-destrutivo)
5. Score de aderência (0–100) é calculado comparando o perfil completo do candidato com os requisitos reais da vaga
6. Ao atingir 75%, a geração do currículo é desbloqueada — o candidato decide se avança
7. Um currículo personalizado no formato ABNT é gerado para a vaga específica, com tom adaptativo (jovem aprendiz vs. sênior)
8. O candidato edita o resultado livremente (contenteditable) antes de exportar para PDF

O link externo da vaga só é liberado após o ciclo completo — o candidato nunca sai da plataforma despreparado.

---

## Comportamentos de Modelo Observados — Registro Empírico

Estes são incidentes reais documentados no diário de bordo (`documentacao/diario_de_bordo.md`), cada um identificado por teste físico ponta a ponta, diagnosticado até a causa raiz e corrigido por intervenção no prompt.

### Incidente 1 — Viés de Área no Score de Aderência (2026-05-18)

**Comportamento observado:** Candidatos com habilidades técnicas (HTML, CSS, JavaScript) recebiam score de aderência 0% para vagas de front-end.

**Diagnóstico:** O `_PROMPT_SCORE` original usava o currículo premium gerado anteriormente como base de análise. Currículos anteriores foram produzidos com enquadramento implícito da área jurídica, contexto original do projeto acadêmico. O modelo tratava currículos de domínio jurídico como referência e pontuava habilidades técnicas como irrelevantes.

**Causa raiz:** Dois problemas combinados — (1) o prompt alimentava currículos gerados como entrada, em vez do perfil estruturado do banco, e (2) o enquadramento residual de área no texto do prompt viesava os critérios de avaliação do modelo.

**Correção:** `_obter_base_perfil()` foi reescrita para sempre ler das tabelas estruturadas do banco como única fonte de verdade, nunca de currículos gerados. `_PROMPT_SCORE` foi reescrito com 6 instruções obrigatórias: percorrer o perfil estruturado completo antes de calcular; proibir score zero quando habilidades técnicas relevantes estão declaradas; reconhecer explicitamente habilidades transferíveis entre áreas.

---

### Incidente 2 — Alucinação de Contexto na Entrevista (2026-05-21)

**Comportamento observado:** O Recrutador IA referenciava conversas anteriores que não existiam no histórico persistido — fabricando continuidade entre sessões.

**Diagnóstico:** O prompt não instruía explicitamente o modelo sobre como tratar o parâmetro de histórico de conversa. O modelo preencheu a ausência de instrução explícita gerando referências plausíveis mas inventadas.

**Correção:** `_PROMPT_RECRUTADOR` foi reestruturado para que a verificação do histórico seja a primeira instrução, antes de todas as outras regras. Uma proibição explícita foi adicionada: o modelo nunca pode referenciar conversas não registradas no histórico fornecido. A correção precede todas as outras instruções para impedir que o modelo estabeleça um enquadramento alucinado antes de encontrar a restrição.

---

### Incidente 3 — Lógica de Fallback Incompleta (2026-05-21)

**Comportamento observado:** O sistema travava em erros de provedor como `503 UNAVAILABLE` e `ConnectError`, mesmo com um provedor alternativo (Groq) configurado.

**Diagnóstico:** A condição de fallback original em `ia.py` verificava apenas strings de erro de cota/rate-limit (`429`, `quota`, `rate`, `limit`). Erros de rede e indisponibilidade do servidor lançavam exceções que bypassavam completamente a condição de fallback e propagavam imediatamente.

**Correção:** A lógica de fallback foi reestruturada para capturar todas as exceções de qualquer provedor e sempre tentar o próximo, independente do tipo de erro. O try/except agora envolve a chamada completa ao provedor; qualquer falha aciona a continuação para o próximo. O sistema só lança exceção após todos os provedores configurados se esgotarem.

```python
# ia.py — lógica de fallback atual
def gerar_conteudo(prompt: str) -> str:
    provedores = _resolver_provedores()
    ultimo_erro = None
    for nome, tipo, api_key in provedores:
        fn = _TIPO_FN.get(tipo)
        if not fn:
            continue
        try:
            return fn(api_key, prompt)
        except Exception as e:
            ultimo_erro = e
            print(f"[IA] {nome} — falhou ({type(e).__name__}: {e}), tentando próximo...")
            continue
    raise RuntimeError(f"Todos os provedores esgotaram. Último erro: {ultimo_erro}")
```

---

## Decisões de Design

**Verdade Absoluta:** Banco SQLite em `%APPDATA%\SAR\sar_repositorio.db`. Sem cache, sem estado de sessão, sem dados em memória. `_obter_conexao()` em `genericas.py` é o único ponto autorizado de acesso ao banco — verificado por grep em todo o codebase.

**IA como ferramenta, não arquiteta:** Toda lógica, fluxo de dados e decisões arquiteturais foram projetados pelo desenvolvedor. A IA foi usada exclusivamente para produzir código a partir dessas especificações. A validação foi sempre física — executar o fluxo completo do usuário contra o resultado esperado, não apenas rodar scripts.

**Abstração de provedores:** `ia.py` resolve provedores a partir de `IA_PROVIDERS` no `.env` em runtime. Adicionar uma nova chave Groq requer apenas uma nova entrada no `.env` — sem alteração de código. A sequência de fallback é totalmente configurável sem tocar na camada de abstração.

**Enriquecimento incremental:** Dados de importação e entrevista são mesclados nos registros existentes do perfil, nunca substituindo. Preserva dados inseridos pelo candidato entre múltiplas sessões de importação.

**Proteção do trabalho do candidato:** Currículos gerados são ativos, não documentos descartáveis. Cada geração é salva independentemente com timestamp. Se uma vaga desaparece durante a produção, o candidato recebe um aviso não-bloqueante e pode salvar o trabalho como base reutilizável para candidaturas futuras.

---

## Estrutura do Projeto

```
/
├── backend/
│   ├── servidor.py              ← orquestrador: lê .env, gerencia SSL e PID
│   ├── aplicacao.py             ← rotas FastAPI e inicialização do banco
│   └── rotinas/
│       ├── genericas.py         ← CRUD SQLite agnóstico (ponto único de acesso ao banco)
│       ├── ia.py                ← abstração Gemini + Groq com fallback completo
│       ├── importacao.py        ← prompts de IA: extração, score, entrevista, currículo
│       ├── sincronizacao.py     ← motor de sync Peixe 30 (padrão UPDATE→INSERT)
│       └── autenticacao.py      ← hash bcrypt, token UUID4, gestão de sessão
│
├── frontend/
│   ├── telas/                   ← telas HTML (SAR.html, login.html, cadastro.html)
│   ├── estilos/visual.css       ← design system global
│   └── scripts/                 ← lógica de negócio JS (vagas.js, perfil.js, curriculos.js)
│
├── integracao/rotas/api.js      ← camada de transporte HTTP (todas as chamadas fetch centralizadas)
├── certificado/publico/sar.crt  ← certificado SSL (mkcert, válido até 27/07/2028)
├── documentacao/                ← governança, plano de desenvolvimento, fluxograma, diário
├── apoio/                       ← testes, logs, uploads temporários (nunca commitados)
└── dependencias.txt             ← dependências Python
```

---

## Como Executar Localmente

**Requisitos:** Python 3.12+, [mkcert](https://github.com/FiloSottile/mkcert), chave de API Google Gemini (free tier), chave Groq opcional.

```bash
# 1. Instalar CA do mkcert e gerar certificado
mkcert -install
mkcert -cert-file certificado/publico/sar.crt -key-file certificado/privado/sar.key 127.0.0.1

# 2. Criar .env na raiz do projeto com as seguintes variáveis:
# SSL_CERTFILE=certificado/publico/sar.crt
# SSL_KEYFILE=certificado/privado/sar.key
# HOST=127.0.0.1
# PORTA_DEFAULT=8000
# IA_PROVIDERS=gemini,groq_1          # separados por vírgula, tentados em ordem
# GEMINI_API_KEY=sua_chave_aqui       # aistudio.google.com → Get API key
# GEMINI_MODEL=gemini-2.5-flash
# GROQ_API_KEY_1=sua_chave_aqui       # console.groq.com → API Keys (opcional)
# GROQ_MODEL=llama-3.3-70b-versatile

# 3. Instalar dependências
pip install -r dependencias.txt

# 4. Iniciar (sempre pelo orquestrador — nunca pelo uvicorn diretamente)
cd backend
python servidor.py
```

O servidor abre `https://127.0.0.1:8000/login` automaticamente.

> **Atenção:** HTTPS é obrigatório. O servidor bloqueia a inicialização sem certificado SSL válido.

---

## Documentação

O projeto mantém quatro documentos de governança atualizados após cada tarefa concluída:

- [`documentacao/governanca.md`](documentacao/governanca.md) — contrato de governança técnica: regras de nomenclatura, hierarquia de pastas, regras de implementação, política SSL, protocolo de qualidade
- [`documentacao/plano_de_desenvolvimento.md`](documentacao/plano_de_desenvolvimento.md) — plano de desenvolvimento: motores, esquema do banco, decisões arquiteturais (DA-01, DA-02, DA-03), roadmap por fases
- [`documentacao/fluxograma.md`](documentacao/fluxograma.md) — fluxograma de processos: status atual, fases concluídas, pendências, diagrama de fluxo de dados
- [`documentacao/diario_de_bordo.md`](documentacao/diario_de_bordo.md) — diário de bordo cronológico: cada decisão, bug, correção e pivô arquitetural registrado com data e causa raiz

---

## Nota sobre Metodologia

Este projeto foi desenvolvido sem formação formal em ciência da computação. Todas as decisões arquiteturais foram tomadas antes da codificação, documentadas na governança e validadas por testes físicos ponta a ponta. O desenvolvedor atuou como usuário final em cada etapa — nenhuma funcionalidade foi considerada concluída sem validação manual contra o resultado esperado.

Ferramentas de IA foram usadas exclusivamente para produzir código a partir de especificações pré-definidas. Quando o resultado divergia do comportamento esperado, o processo de debug sempre começava pelos logs e pelos documentos de governança — rastreando a falha até a causa raiz antes de qualquer correção.

Essa abordagem produziu três casos documentados de observação de comportamento de LLM (acima) que emergiram naturalmente da metodologia de validação: a saída do modelo foi comparada contra uma verdade absoluta definida, a divergência foi diagnosticada e o prompt foi corrigido com base no modo de falha observado.

---

---

# SAR — Professional Replacement Automation System

A local web platform that integrates generative AI to automate professional job placement. The candidate imports an existing resume, the AI extracts and structures the profile automatically, conducts a guided interview, and generates a personalized resume for each job opening — with an adherence score calculated and displayed before generation.

Built as an academic project by a self-taught developer with a background in Law, using AI strictly as a code production tool. All logic, architecture, and decisions are the developer's own, validated through physical end-to-end testing against a defined ground truth.

**Stack:** Python 3.12 · FastAPI · SQLite · HTML/CSS/JS Vanilla · Google Gemini 2.5 Flash · Groq (fallback) · HTTPS mandatory (mkcert)

---

## Architecture — Four Functional Engines

The system is structured around four independent but interdependent engines. Each has a single responsibility and feeds the next.

**Engine 1 — Job Capture**
Syncs job listings from the Peixe 30 Jobs public API on demand. Uses an UPDATE → INSERT pattern (not UPSERT with partial indexes, which silently failed on SQLite — see observed behaviors below). Candidate-owned data (status, score, notes) is never overwritten. Jobs removed from the platform are soft-marked as unavailable, never deleted — the candidate may have active progress linked to them.

**Engine 2 — Identity and Access**
Login-gated system (ERP-style). Authentication via bcrypt + UUID4 session token stored in sessionStorage, sent as `Authorization: Bearer` on every request. Tokens are auditable and revocable via the `sessoes` table. All queries are filtered by `id_candidato` extracted from the validated token — no candidate can access another's data.

**Engine 3 — Registration and Infrastructure**
Handles candidate registration and creates the full database infrastructure (8 profile tables) ready for Engine 4: `perfil_candidato`, `experiencias`, `formacoes`, `habilidades`, `idiomas`, `certificacoes`, `documentos`, `contatos` — all with `ON DELETE CASCADE`.

**Engine 4 — Import, Profile, and Premium Resume (AI core)**
The system's intelligence layer:

1. Candidate uploads an existing resume (PDF or DOCX)
2. AI extracts structured data and populates the 8 profile tables (merge, never overwrite)
3. A guided interview with the Recruiter AI deepens the profile — one question at a time, history persisted in the `conversas` table
4. After the interview, skills and experiences attested during the conversation are incrementally inserted into the profile tables (non-destructive enrichment)
5. An adherence score (0–100) is calculated by comparing the candidate's full profile against the job's real requirements
6. At 75% score, resume generation is unlocked — the candidate decides whether to proceed
7. A personalized ABNT-formatted resume is generated for the specific job, with an adaptive tone (junior vs. senior)
8. The candidate edits the result freely (contenteditable) before exporting to PDF

The external job link is only released after the full cycle is complete — the candidate never leaves the platform unprepared.

---

## Observed Model Behaviors — Empirical Record

These are real incidents documented in the development diary (`documentacao/diario_de_bordo.md`), each identified through physical end-to-end testing, diagnosed to root cause, and corrected through prompt intervention.

### Incident 1 — Domain Bias in Adherence Score (2026-05-18)

**Observed behavior:** Candidates with technical skills (HTML, CSS, JavaScript) received a 0% adherence score for front-end job listings.

**Diagnosis:** The original `_PROMPT_SCORE` used the candidate's previously generated resume as its analysis base. Earlier resumes were produced with implicit legal domain framing from the project's original academic context. The model treated legal-domain resumes as the reference point and scored technical skills as irrelevant.

**Root cause:** Two compounding issues — (1) the prompt was feeding generated resumes as input instead of the structured profile from the database, and (2) residual domain framing in the prompt text biased the model's evaluation criteria.

**Correction:** `_obter_base_perfil()` was rewritten to always read from the structured database tables as the single source of truth, never from generated resumes. `_PROMPT_SCORE` was rewritten with 6 mandatory instructions: traverse the full structured profile before calculating; prohibit zero score when relevant technical skills are declared; explicitly recognize transferable skills across domains.

---

### Incident 2 — Context Hallucination in Interview (2026-05-21)

**Observed behavior:** The Recruiter AI referenced prior conversations that did not exist in the persisted history — fabricating continuity between sessions.

**Diagnosis:** The prompt did not explicitly instruct the model on how to handle the conversation history parameter. The model filled the absence of explicit guidance by generating plausible-sounding but invented references.

**Correction:** `_PROMPT_RECRUTADOR` was restructured so that history verification is the first instruction, before all other rules. An explicit prohibition was added: the model must never reference conversations not recorded in the provided history. The correction preceded all other instructions to prevent the model from establishing a hallucinated frame before encountering the constraint.

---

### Incident 3 — Incomplete Fallback Logic (2026-05-21)

**Observed behavior:** The system crashed on provider errors like `503 UNAVAILABLE` and `ConnectError`, even though a fallback provider (Groq) was configured.

**Diagnosis:** The original fallback condition in `ia.py` checked only for quota/rate-limit error strings (`429`, `quota`, `rate`, `limit`). Network errors and server-side unavailability raised exceptions that bypassed the fallback condition entirely and propagated immediately.

**Correction:** The fallback logic was restructured to catch all exceptions from any provider and always attempt the next one, regardless of error type. The try/except now wraps the full provider call; any failure triggers continuation to the next provider. The system only raises after all configured providers are exhausted.

```python
# ia.py — current fallback logic
def gerar_conteudo(prompt: str) -> str:
    provedores = _resolver_provedores()
    ultimo_erro = None
    for nome, tipo, api_key in provedores:
        fn = _TIPO_FN.get(tipo)
        if not fn:
            continue
        try:
            return fn(api_key, prompt)
        except Exception as e:
            ultimo_erro = e
            print(f"[IA] {nome} — falhou ({type(e).__name__}: {e}), tentando próximo...")
            continue
    raise RuntimeError(f"Todos os provedores esgotaram. Último erro: {ultimo_erro}")
```

---

## Key Design Decisions

**Single source of truth:** SQLite database at `%APPDATA%\SAR\sar_repositorio.db`. No caching, no session state, no in-memory data. `_obter_conexao()` in `genericas.py` is the only authorized point of database access — verified by grep across the codebase.

**AI as production tool, not architect:** All logic, data flow, and architectural decisions were designed by the developer. AI was used exclusively to produce code from those designs. Validation was always physical — running the full user flow against expected output, not just executing scripts.

**Provider abstraction:** `ia.py` resolves providers from `IA_PROVIDERS` in `.env` at runtime. Adding a new Groq key requires only a new `.env` entry — no code changes. The fallback sequence is fully configurable without touching the abstraction layer.

**Incremental enrichment:** Resume import and interview data are merged into existing profile records, never replacing them. This preserves candidate-entered data across multiple import sessions.

**Candidate data protection:** Generated resumes are assets, not disposable documents. Each generation is saved independently with a timestamp. If a job listing disappears during production, the candidate receives a non-blocking warning and can save the work as a reusable base for future applications.

---

## Project Structure

```
/
├── backend/
│   ├── servidor.py              ← orchestrator: reads .env, manages SSL and PID
│   ├── aplicacao.py             ← FastAPI routes and database initialization
│   └── rotinas/
│       ├── genericas.py         ← agnostic SQLite CRUD (single DB access point)
│       ├── ia.py                ← Gemini + Groq abstraction with full fallback
│       ├── importacao.py        ← AI prompts: extraction, scoring, interview, resume
│       ├── sincronizacao.py     ← Peixe 30 sync engine (UPDATE→INSERT pattern)
│       └── autenticacao.py      ← bcrypt hash, UUID4 token, session management
│
├── frontend/
│   ├── telas/                   ← HTML screens (SAR.html, login.html, cadastro.html)
│   ├── estilos/visual.css       ← global design system
│   └── scripts/                 ← business logic JS (vagas.js, perfil.js, curriculos.js)
│
├── integracao/rotas/api.js      ← HTTP transport layer (all fetch calls centralized here)
├── certificado/publico/sar.crt  ← SSL certificate (mkcert, valid until 2028-07-27)
├── documentacao/                ← governance contract, development plan, flowchart, diary
├── apoio/                       ← tests, logs, upload staging (never committed)
└── dependencias.txt             ← Python dependencies
```

---

## Running Locally

**Requirements:** Python 3.12+, [mkcert](https://github.com/FiloSottile/mkcert), Google Gemini API key (free tier), optional Groq API key.

```bash
# 1. Install mkcert CA and generate certificate
mkcert -install
mkcert -cert-file certificado/publico/sar.crt -key-file certificado/privado/sar.key 127.0.0.1

# 2. Create .env in the project root with the following variables:
# SSL_CERTFILE=certificado/publico/sar.crt
# SSL_KEYFILE=certificado/privado/sar.key
# HOST=127.0.0.1
# PORTA_DEFAULT=8000
# IA_PROVIDERS=gemini,groq_1          # comma-separated, tried in order
# GEMINI_API_KEY=your_key_here        # aistudio.google.com → Get API key
# GEMINI_MODEL=gemini-2.5-flash
# GROQ_API_KEY_1=your_key_here        # console.groq.com → API Keys (optional)
# GROQ_MODEL=llama-3.3-70b-versatile

# 3. Install dependencies
pip install -r dependencias.txt

# 4. Start (always via orchestrator — never uvicorn directly)
cd backend
python servidor.py
```

The server opens `https://127.0.0.1:8000/login` automatically.

> **Note:** HTTPS is mandatory. The server blocks startup if no valid SSL certificate is found.

---

## Documentation

The project maintains four governance documents updated after every completed task:

- [`documentacao/governanca.md`](documentacao/governanca.md) — technical governance contract: naming rules, folder hierarchy, implementation rules, SSL policy, quality protocol
- [`documentacao/plano_de_desenvolvimento.md`](documentacao/plano_de_desenvolvimento.md) — development plan: engines, database schema, architectural decisions (DA-01, DA-02, DA-03), phase roadmap
- [`documentacao/fluxograma.md`](documentacao/fluxograma.md) — process flowchart: current status, completed phases, pending items, data flow diagram
- [`documentacao/diario_de_bordo.md`](documentacao/diario_de_bordo.md) — chronological development diary: every decision, bug, correction, and architectural pivot recorded with date and root cause

---

## Methodology Note

This project was developed without formal computer science training. All architectural decisions were made before coding, documented in governance, and validated through physical end-to-end testing. The developer acted as the final user at every step — no feature was considered complete without manual validation against expected output.

AI tools were used exclusively to produce code from pre-designed specifications. When the output diverged from the expected behavior, the debugging process always began with the logs and the governance documents — tracing the failure back to root cause before any correction.

This approach produced three documented cases of LLM behavior observation (above) that emerged naturally from the validation methodology: the model's output was compared against a defined ground truth, the divergence was diagnosed, and the prompt was corrected based on the observed failure mode.