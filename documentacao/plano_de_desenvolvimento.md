# Plano de Desenvolvimento — SAR (Sistema de Automação de Recolocação)

**Objetivo:** Plataforma inteligente para automação da jornada de recolocação profissional — captura de vagas, geração de currículo personalizado via IA e otimização para sistemas ATS de recrutamento.

**Última atualização:** 2026-05-04 (Motor 3 certificado com escopo correto — Motor 4 iniciando)

---

## Pilares Técnicos

1. **Simplicidade:** Código limpo, descritivo e de fácil manutenção.
2. **Segurança de Dados:** Persistência direta no SQLite (Verdade Absoluta), integridade via chaves estrangeiras.
3. **Rastreabilidade:** Diário de bordo atualizado a cada evolução.
4. **Segurança de Rede:** HTTPS obrigatório em todos os ambientes. Servidor bloqueado sem certificado SSL válido.

---

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.12+, FastAPI, Uvicorn |
| Frontend | HTML5, CSS3, JavaScript Vanilla |
| Banco de Dados | SQLite (chaves estrangeiras ativas) |
| SSL | mkcert — CA local, cert válido até 27/07/2028 |
| Fonte de vagas | Peixe 30 Jobs — API REST pública |
| IA — extração | Google Gemini 2.0 Flash (free tier) |
| IA — geração | Google Gemini 2.0 Flash (free tier) |
| Extração PDF | pdfplumber |
| Extração DOCX | python-docx |
| Extração ODT/RTF | textract |
| Detecção de formato | python-magic |
| Geração de PDF | a definir (Fase 4) |

---

## Hierarquia de Pastas

```
/
├── backend/
│   ├── servidor.py              ← orquestrador central + PID management ✅
│   ├── aplicacao.py             ← rotas FastAPI + inicialização do banco ✅
│   └── rotinas/
│       ├── genericas.py         ← CRUD agnóstico SQLite ✅
│       ├── sincronizacao.py     ← motor de sync com Peixe 30 (Fase 2)
│       └── ia.py                ← abstração de chamadas Gemini (Fase 3)
├── frontend/
│   ├── telas/
│   │   ├── SAR.html             ← tela principal ✅
│   │   ├── candidatos.html      ← cadastro e perfil do candidato (Fase 3)
│   │   └── curriculos.html      ← geração e histórico de currículos (Fase 4)
│   ├── estilos/
│   │   └── visual.css           ← design system global ✅
│   └── scripts/
│       ├── vagas.js             ← lógica da tela de vagas ✅
│       ├── candidatos.js        ← lógica da tela de candidatos (Fase 3)
│       └── curriculos.js        ← lógica da tela de geração (Fase 4)
├── integracao/
│   └── rotas/
│       └── api.js               ← transporte HTTP centralizado ✅
├── certificado/
│   ├── publico/sar.crt          ← certificado SSL ✅
│   └── privado/sar.key          ← chave privada (nunca no git) ✅
├── documentacao/                ← governança, plano, fluxograma, diário ✅
├── apoio/                       ← testes, logs, scripts de suporte
├── .env                         ← variáveis de ambiente (nunca no git) ✅
├── sar.pid                      ← PID do processo ativo (nunca no git) ✅
├── .gitignore                   ✅
├── dependencias.txt             ✅
└── .devcontainer/               ✅
```

---

## Arquitetura por Motores

O SAR é composto por quatro motores funcionais independentes e interdependentes. Cada motor tem responsabilidade única e alimenta o próximo. Nenhum motor é implementado sem análise e alinhamento completos.

### Motor 1 — Captura de Vagas
**Responsabilidade:** buscar vagas de plataformas externas e persistir no banco local.
- Fonte atual: Peixe 30 (API REST pública, sem autenticação)
- Sync manual — acionado pelo candidato via botão "Atualizar", nunca automático no startup
- UPSERT por `id_externo` — atualiza dados da fonte sem tocar dados do candidato
- DELETE protegido — remove apenas vagas com `status = PENDENTE` que sumiram da plataforma
- Expansão futura: tabelas distintas por plataforma + VIEW `vagas_todas` (ver DA-01)

### Motor 2 — Identidade e Acesso
**Responsabilidade:** autenticar candidatos e isolar dados por identidade.
- Tela de login como porta de entrada obrigatória (modelo ERP — nenhum dado exposto sem autenticação)
- Autenticação por email + senha (hash bcrypt)
- Sessão por token UUID4 armazenado no `sessionStorage` — enviado no header `Authorization: Bearer`
- Tabela `sessoes` no banco — auditável, revogável, sem cookie
- Isolamento total: toda query filtrada por `id_candidato` extraído do token
- Modelo mestre-detalhe: `candidatos` (identidade) + `perfil_candidato` (dados profissionais)

### Motor 3 — Cadastro e Acesso
**Responsabilidade:** registrar o candidato e garantir acesso autenticado à plataforma.
- Cadastro básico: nome, e-mail, senha (hash bcrypt), confirmação de senha com eye toggle
- Login: e-mail + senha → token UUID4 em `sessionStorage` → header `Authorization: Bearer`
- Sessão auditável: tabela `sessoes` — revogável, sem cookie
- Infraestrutura de dados profissionais: 8 tabelas criadas (`perfil_candidato`, `experiencias`, `formacoes`, `habilidades`, `idiomas`, `certificacoes`, `documentos`, `contatos`) — prontas para Motor 4
- Interface Motor 3: exibe apenas dados de acesso (nome, e-mail) — sem formulários de perfil detalhado

### Motor 4 — Importação, Perfil e Currículo Premium
**Responsabilidade:** importar currículo existente, construir perfil profissional completo e gerar currículo personalizado por vaga.
- **Entrada primária:** importação de currículo existente (PDF/DOCX) → IA extrai dados → popula perfil automaticamente
- **Entrada alternativa:** complementação ou preenchimento manual dos blocos de perfil (experiências, formações, habilidades, idiomas, certificações, contatos)
- Mínimo para geração: nome + contato + 1 habilidade + (1 experiência OU 1 formação OU 1 certificação) — inclusivo, atende jovem aprendiz e primeiro emprego
- Entrada no ciclo de candidatura via botão "Preparar candidatura" no card da vaga (ver DA-03)
- Verificação de disponibilidade da vaga ao entrar no Motor 4 — aviso não-bloqueante se indisponível
- Geração em 3 etapas via Gemini:
  1. Extrai requisitos reais da vaga (palavras-chave, competências, soft skills)
  2. Compara com perfil do candidato → calcula score de aderência (0–100)
  3. Gera currículo enfatizando convergências, minimizando lacunas
- Score exibido antes da geração — candidato decide se avança
- Tom adaptativo: IA ajusta linguagem ao perfil (jovem aprendiz ≠ sênior)
- Edição em texto livre (`contenteditable`) — candidato tem autonomia total antes do PDF
- **Salvar como base:** currículo em qualquer estágio pode ser salvo desvinculado da vaga para reaproveitamento futuro (ver DA-02)
- **Carregar base:** ao iniciar nova candidatura, sistema oferece bases salvas como ponto de partida
- PDF gerado por `weasyprint` — WYSIWYG, o que o candidato vê é o que sai no arquivo
- Pacote ZIP salvo no Desktop do usuário (`~/Desktop`) — sem problemas de permissão ou BitLocker
- ZIP contém: currículo PDF + carta de apresentação + documentos apensos selecionados
- **Link externo liberado somente aqui** — após ciclo completo, candidato acessa a vaga na plataforma para candidatura
- Histórico de currículos: `status` = `rascunho` | `base_salva` | `finalizado`
- Rastreamento externo: nenhum — o sistema é facilitador, não integrado aos portais

---

## Decisões Arquiteturais Registradas

### [DA-01] Integração Multi-Plataforma de Vagas

**Contexto:** O SAR integra atualmente apenas o Peixe 30. Há intenção documentada de expandir para outras plataformas (LinkedIn, Catho, InfoJobs, etc.) em versões futuras.

**Decisão:** Cada nova plataforma integrada deve ter sua própria tabela no banco de dados, nomeada `vagas_<plataforma>` (ex: `vagas_peixe30`, `vagas_linkedin`). A tabela de cada plataforma preserva os campos nativos daquela API, sem forçar normalização artificial.

**Relacionamento entre plataformas:** Uma SQL VIEW chamada `vagas_todas` deve ser criada agregando todas as tabelas de plataformas com os campos comuns normalizados. Essa view é o ponto de entrada para:
- Exibir ao usuário todas as vagas disponíveis independente da origem
- Filtrar por área de interesse em todas as plataformas simultaneamente
- Apresentar dados tratados e de fácil comparação entre plataformas

```sql
-- Exemplo da VIEW unificada (a criar quando houver segunda plataforma)
CREATE VIEW vagas_todas AS
  SELECT 'peixe30'  AS plataforma, id_externo, titulo, empresa,
         localizacao, modalidade, tipo_contrato, salario_inicial, link, data_extracao
  FROM vagas_peixe30
  UNION ALL
  SELECT 'linkedin' AS plataforma, id_externo, titulo, empresa,
         localizacao, modalidade, tipo_contrato, salario_inicial, link, data_extracao
  FROM vagas_linkedin;
```

**Referência nas candidaturas:** A tabela de candidaturas referencia a vaga pelo par `plataforma + id_externo`, não por chave numérica, garantindo rastreabilidade independente da origem.

**Responsabilidade de expansão:** A integração com cada nova plataforma é de responsabilidade do desenvolvedor, que deve conduzir análise de API, testes de integração e mapeamento de campos antes de qualquer implementação. Não há código especulativo para plataformas não integradas.

**Estado atual:** Apenas Peixe 30 integrado. Tabela `vagas` em uso (a ser renomeada para `vagas_peixe30` quando da primeira expansão de plataforma).

---

### [DA-02] Currículo como Ativo Reutilizável do Candidato

**Contexto:** Durante o Motor 4, o candidato pode estar produzindo um currículo quando a vaga alvo desaparece da plataforma externa. Descartar o trabalho produzido seria uma perda irreparável para o candidato.

**Decisão:** O currículo produzido é um **ativo permanente do candidato**, não um documento descartável vinculado a uma única vaga. Quando uma vaga fica indisponível durante a produção:
- O sistema emite um **aviso não-bloqueante** — o candidato é informado mas não é impedido de continuar
- O candidato decide livremente se continua ou interrompe a produção
- O candidato pode **salvar o trabalho como base** — o currículo é desvinculado da vaga e fica disponível para reaproveitamento
- Ao iniciar uma nova candidatura, o sistema **oferece carregar a base salva** como ponto de partida, eliminando a necessidade de produção do zero

**Impacto no esquema — tabela `curriculos_gerados`:**

| Campo | Tipo | Descrição |
|---|---|---|
| `status` | TEXT | `rascunho` → em produção vinculado à vaga |
| | | `base_salva` → desvinculado, disponível para reaproveitamento |
| | | `finalizado` → ciclo completo, candidatura pronta |
| `id_vaga` | INT nullable | NULL quando `status = base_salva` |

**Princípio:** cada currículo produzido agrega ao patrimônio profissional do candidato. O esforço nunca é perdido.

---

### [DA-03] Fluxo de Candidatura — Contenção na Plataforma

**Contexto:** O botão "Ver ↗" no card de vagas direcionava o candidato diretamente para a plataforma externa antes de estar preparado para a candidatura real, quebrando o fluxo de valor do SAR.

**Decisão:** O candidato **nunca sai da plataforma SAR** antes de concluir o ciclo completo de produção. O link externo da vaga (`vagas.link`) é um dado interno — não é exposto ao candidato até o Motor 4 estar concluído.

**Fluxo definido:**
```
Card de vaga
├── "Ver descrição"      → Modal interno com dados da vaga carregados do JSON local
│                           (sem nenhuma chamada externa, sem sair da plataforma)
└── "Preparar candidatura" → Entrada no Motor 4
                              ↓ (após ciclo completo)
                           Link externo liberado para candidatura na plataforma
```

**Impacto no card de vagas:**
- Botão "Ver ↗" removido
- "Ver descrição" abre modal interno com: título, empresa, localização, modalidade, contrato, salário e descrição completa
- "Preparar candidatura" é o único caminho para o link externo — via Motor 4

**Estado atual:** Modal e botão implementados no card. Link externo preservado no banco para uso exclusivo do Motor 4.

---

## Esquema de Banco de Dados

### Tabelas existentes
| Tabela | Propósito |
|---|---|
| `vagas` | repositório de vagas do Peixe 30 (renomear para `vagas_peixe30` na expansão) |
| `configuracoes` | parâmetros agnósticos do sistema |
| `logs_sistema` | rastreabilidade total de ações |
| `candidatos` | identidade e acesso — autenticação bcrypt, token UUID4 |
| `sessoes` | tokens de sessão auditáveis e revogáveis |
| `perfil_candidato` | dados profissionais do candidato (1:1 com candidatos) |
| `experiencias` | histórico de empregos do candidato |
| `formacoes` | histórico de formação acadêmica |
| `habilidades` | habilidades técnicas com nível de proficiência |
| `idiomas` | idiomas com nível de proficiência |
| `certificacoes` | certificações e cursos concluídos |
| `documentos` | arquivos apensos (diplomas, portfólio, carta de apresentação) |
| `contatos` | dados de contato e redes profissionais (1:1 com candidatos) |

### Tabelas previstas
| Tabela | Fase | Campos principais |
|---|---|---|
| `curriculos_gerados` | 5 | id_candidato, id_vaga, arquivo_pdf, data_geracao, score_aderencia |

### Arquitetura futura — Multi-Plataforma (ver DA-01)
| Elemento | Tipo | Descrição |
|---|---|---|
| `vagas_peixe30` | Tabela | Vagas nativas do Peixe 30 |
| `vagas_linkedin` | Tabela (futuro) | Vagas nativas do LinkedIn |
| `vagas_<plataforma>` | Tabela (futuro) | Padrão para cada nova plataforma |
| `vagas_todas` | VIEW (futuro) | Agregação normalizada de todas as plataformas |

### Tabelas — Motor 2 (Identidade e Acesso)
| Tabela | Campos principais |
|---|---|
| `candidatos` | id, nome, email (UNIQUE), senha_hash, status, criado_em, ultimo_acesso |
| `sessoes` | token (PK UUID4), id_candidato (FK), criado_em, expira_em |

### Tabelas — Motor 3 (Perfil do Candidato)
| Tabela | Campos principais |
|---|---|
| `perfil_candidato` | id_candidato (FK 1:1), cidade, estado, resumo_profissional |
| `experiencias` | id, id_candidato (FK), empresa, cargo, inicio, fim, descricao, atual |
| `formacoes` | id, id_candidato (FK), instituicao, curso, nivel, inicio, conclusao, em_andamento |
| `habilidades` | id, id_candidato (FK), habilidade, nivel (Básico/Intermediário/Avançado/Especialista) |
| `idiomas` | id, id_candidato (FK), idioma, proficiencia (Básico/Intermediário/Avançado/Fluente/Nativo) |
| `certificacoes` | id, id_candidato (FK), nome, instituicao, data_obtencao, validade |
| `documentos` | id, id_candidato (FK), tipo, nome_arquivo, caminho, descricao, data_upload |
| `contatos` | id_candidato (FK 1:1), telefone, linkedin, github, portfolio, outras_redes |

### Tabelas — Motor 4 (Geração)
| Tabela | Campos principais |
|---|---|
| `candidaturas` | id, id_candidato (FK), id_vaga (FK), score_aderencia, data_criacao — UNIQUE(id_candidato, id_vaga) |
| `curriculos_gerados` | id, id_candidato (FK), id_vaga (FK), conteudo_html, caminho_pdf, score_aderencia, data_geracao, versao |

---

## Roadmap por Fases

### [Fase 1] Fundação e Orquestração — ✅ Concluída

**Objetivo:** Ambiente funcional com handshake GUI ↔ Backend validado em HTTPS.

| Entrega | Status |
|---|---|
| Estrutura de pastas | ✅ |
| `rotinas/genericas.py` — CRUD SQLite | ✅ |
| `aplicacao.py` — rotas FastAPI + StaticFiles | ✅ |
| `SAR.html` — tela principal com design system | ✅ |
| `visual.css` — design system global | ✅ |
| `vagas.js` — lógica de negócio | ✅ |
| `api.js` — transporte em `integracao/rotas/` | ✅ |
| `servidor.py` — orquestrador com SSL e PID management | ✅ |
| Certificado SSL mkcert instalado | ✅ |
| Correções de governança (prefixos, hierarquia, SSL) | ✅ |
| **Certificação:** frontend carregado em HTTPS, backend online | ✅ |

---

### [Fase 2] Motor 1 — Captura de Vagas — ✅ Implementado / Pendente certificação

**Objetivo:** Sistema sincroniza com Peixe 30 sob demanda e exibe vagas na tela.

| Entrega | Status |
|---|---|
| Migração DB: campos completos na tabela `vagas` | ✅ |
| `rotinas/sincronizacao.py` — motor de sync bidirecional | ✅ |
| Endpoint `POST /vagas/sincronizar` | ✅ |
| Sync manual apenas (startup sem sync automático) | ✅ |
| DELETE protegido — só remove vagas com status PENDENTE | ✅ |
| Botão "Atualizar Vagas" na tela principal | ✅ |
| Cards de vagas com campos completos | ✅ |
| Filtros na tela: regime, modalidade | ✅ |
| Endpoints CRUD completos: GET/POST/PUT/DELETE `/vagas` | ✅ |
| Endpoints `/configuracoes` e `/logs` | ✅ |
| `iniciar_servidor.bat` abre browser automaticamente | ✅ |
| Índice UNIQUE em `id_externo` (migration segura) | ✅ |
| `rotinas/__init__.py` declarado | ✅ |
| **Certificação:** vagas do Peixe 30 aparecem na tela, sync funciona | ⏳ Pendente teste real |

**Decisões de sync:**
- `perPage=50` → ~17 chamadas para 841 vagas atuais
- UPSERT por `id_externo` — campos do candidato (status, score) nunca sobrescritos
- DELETE só vagas PENDENTE órfãs — vagas em andamento preservadas mesmo removidas da plataforma
- API pública confirmada — sem autenticação necessária

---

### [Fase 3] Motor 2 — Identidade e Acesso — ✅ Implementado / Pendente certificação

**Objetivo:** Sistema com login obrigatório, isolamento de dados por candidato e sessão segura.

| Entrega | Status |
|---|---|
| Tela `login.html` — porta de entrada obrigatória | ✅ |
| Tela `cadastro.html` — primeiro acesso | ✅ |
| Tabelas `candidatos` e `sessoes` no banco | ✅ |
| Endpoint `POST /auth/cadastrar` | ✅ |
| Endpoint `POST /auth/login` — devolve token UUID4 | ✅ |
| Endpoint `POST /auth/logout` — revoga token | ✅ |
| Middleware de autenticação — intercepta toda rota protegida | ✅ |
| `api.js` — header `Authorization: Bearer` em toda requisição | ✅ |
| `iniciar_servidor.bat` abre `/login` (não `/sar`) | ✅ |
| `dependencias.txt` atualizado: `passlib[bcrypt]` | ✅ |
| **Certificação:** acesso bloqueado sem login, dados isolados por candidato | ⏳ Pendente teste real |

---

### [Fase 4] Motor 3 — Cadastro e Acesso — ✅ Certificado (2026-05-04)

**Objetivo:** Candidato cadastra-se e acessa a plataforma com segurança. Infraestrutura de dados profissionais criada para Motor 4.

| Entrega | Status |
|---|---|
| Tela `login.html` — porta de entrada obrigatória | ✅ |
| Tela `cadastro.html` — campo confirmação de senha + eye toggle | ✅ |
| Tabelas `candidatos` e `sessoes` no banco | ✅ |
| Endpoints `POST /auth/cadastrar`, `/auth/login`, `/auth/logout` | ✅ |
| Middleware de autenticação — intercepta toda rota protegida | ✅ |
| Token UUID4 em `sessionStorage` — header `Authorization: Bearer` | ✅ |
| Tabelas de perfil criadas (infraestrutura para Motor 4): perfil_candidato, experiencias, formacoes, habilidades, idiomas, certificacoes, documentos, contatos | ✅ |
| Endpoint `POST /perfil-candidato/upload-arquivo` — upload de arquivo | ✅ |
| Endpoints CRUD completos para cada seção do perfil (backend pronto) | ✅ |
| Vagas: select de localidade com filtro dinâmico | ✅ |
| `Meu Perfil` na interface: exibe apenas dados de acesso (nome, e-mail) | ✅ |
| **Decisão de escopo (2026-05-04):** perfil detalhado é Motor 4, não Motor 3 | ✅ |
| **Certificação:** cadastro, login e acesso funcionando; infraestrutura de perfil pronta | ✅ |

---

### [Fase 5] Motor 4 — Importação, Perfil e Currículo Premium — ⏳ Pendente

**Objetivo:** Candidato importa currículo existente → IA popula perfil → candidato complementa → geração de currículo personalizado por vaga → exportação.

| Entrega | Status |
|---|---|
| Upload de currículo (PDF/DOCX/ODT) — tela de importação | ❌ |
| Endpoint `POST /perfil-candidato/importar` — Gemini extrai dados do arquivo e popula as tabelas de perfil | ❌ |
| Interface de complementação: blocos editáveis (experiências, formações, habilidades, idiomas, certificações, contatos) | ❌ |
| Modal interno "Ver descrição" no card de vagas — dados do JSON local, sem saída da plataforma (DA-03) | ❌ |
| Botão "Preparar candidatura" no card de vagas — entrada exclusiva no ciclo Motor 4 | ❌ |
| Endpoint leve `GET /vagas/verificar-disponibilidade` — aviso não-bloqueante ao candidato | ❌ |
| Tabelas `candidaturas` e `curriculos_gerados` no banco | ❌ |
| Endpoint `POST /curriculos/analisar` — Gemini etapa 1+2 (requisitos + score de aderência) | ❌ |
| Endpoint `POST /curriculos/gerar` — Gemini etapa 3 (currículo HTML personalizado) | ❌ |
| Endpoint `POST /curriculos/exportar` — weasyprint → PDF | ❌ |
| Endpoint `POST /curriculos/empacotar` — ZIP no Desktop | ❌ |
| Editor `contenteditable` — edição livre antes do PDF | ❌ |
| Score de aderência exibido antes da geração | ❌ |
| Tom adaptativo por perfil (jovem aprendiz / sênior) | ❌ |
| Salvar como base / carregar base salva (DA-02) | ❌ |
| Histórico de currículos gerados por candidato | ❌ |
| Link externo liberado após ciclo completo (DA-03) | ❌ |
| `dependencias.txt`: weasyprint, pdfplumber, python-docx, python-magic | ❌ |
| **Certificação:** importação → complementação → geração → edição → exportação ZIP validados | ❌ |

---

### [Fase 5] Refinamento de UX — ⏳ Pendente

- Revisão geral do design system (visual.css)
- Navegação entre telas
- Estados de loading, erro e sucesso em todas as operações
- **Certificação:** validação de usabilidade pelo usuário

### [Fase 6] Qualidade e Stress — ⏳ Pendente

- Testes unitários e de integração em `/apoio`
- Simulação de falhas de rede e indisponibilidade da API do Peixe 30
- Limites de rate da API Gemini (1.500 req/dia)

### [Fase 7] Certificação e Estabilização — ⏳ Pendente

- Auditoria de performance e limpeza de código
- Teste de Usuário Final (UAT) e congelamento de versão

---

## Protocolo de Qualidade (Obrigatório)

1. **Planejamento** — descrever antes de codificar
2. **Análise de Prioridade** — avaliar impactos e riscos
3. **Autorização** — aguardar confirmação explícita do usuário
4. **Execução** — um arquivo por vez, sem criatividade fora do escopo
5. **Teste de Laboratório** — execução e logs
6. **Validação do Usuário** — teste real, nunca por presunção
7. **Documentação** — atualizar diário de bordo, fluxograma e este plano

---

**Documentos relacionados:**
- `fluxograma.md` — status atual e próximos passos visuais
- `governanca.md` — contrato de regras e nomenclatura
- `diario_de_bordo.md` — registro cronológico de decisões e eventos
