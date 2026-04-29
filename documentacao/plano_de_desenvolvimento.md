# Plano de Desenvolvimento — SAR (Sistema de Automação de Recolocação)

**Objetivo:** Plataforma inteligente para automação da jornada de recolocação profissional — captura de vagas, geração de currículo personalizado via IA e otimização para sistemas ATS de recrutamento.

**Última atualização:** 2026-04-28 (sessão de análise completa — 4 motores fechados)

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
│   ├── interface_backend.py     ← rotas FastAPI + inicialização do banco ✅
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
- Sessão por token UUID4 armazenado no `localStorage` — enviado no header `Authorization: Bearer`
- Tabela `sessoes` no banco — auditável, revogável, sem cookie
- Isolamento total: toda query filtrada por `id_candidato` extraído do token
- Modelo mestre-detalhe: `candidatos` (identidade) + `perfis` (dados profissionais)

### Motor 3 — Perfil do Candidato
**Responsabilidade:** construir e manter o perfil profissional completo do candidato.
- Duas entradas: importação de documento existente (IA extrai) OU formulário manual
- Salvamento parcial permitido — bloqueio só na validação para geração do currículo
- Mínimo para geração: nome + contato + 1 habilidade + (1 experiência OU 1 formação OU 1 certificação)
- Mínimo inclusivo — atende jovem aprendiz e primeiro emprego sem elevar o sarrafo
- Tabelas filhas com FK para `candidatos`: experiências, formações, habilidades, idiomas, certificações
- Proficiência de habilidades: Básico / Intermediário / Avançado / Especialista
- Proficiência de idiomas: Básico / Intermediário / Avançado / Fluente / Nativo
- Contêiner de documentos: arquivos apensos (certificados, diplomas, portfólio, carta de apresentação)
- Carta de apresentação: upload manual ou gerada pela IA sob demanda na hora do empacotamento

### Motor 4 — Geração de Currículo Premium
**Responsabilidade:** gerar currículo personalizado por vaga, empacotar e exportar.
- Geração em 3 etapas via Gemini:
  1. Extrai requisitos reais da vaga (palavras-chave, competências, soft skills)
  2. Compara com perfil do candidato → calcula score de aderência (0–100)
  3. Gera currículo enfatizando convergências, minimizando lacunas
- Score exibido antes da geração — candidato decide se avança
- Tom adaptativo: IA ajusta linguagem ao perfil (jovem aprendiz ≠ sênior)
- Edição em texto livre (`contenteditable`) — candidato tem autonomia total antes do PDF
- PDF gerado por `weasyprint` — WYSIWYG, o que o candidato vê é o que sai no arquivo
- Pacote ZIP salvo no Desktop do usuário (`~/Desktop`) — sem problemas de permissão ou BitLocker
- ZIP contém: currículo PDF + carta de apresentação + documentos apensos selecionados
- Envio ao recrutador: responsabilidade do candidato (cada vaga tem seu canal)
- Histórico de currículos gerados preservado no banco para consulta futura
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

## Esquema de Banco de Dados

### Tabelas existentes
| Tabela | Propósito |
|---|---|
| `vagas` | repositório de vagas do Peixe 30 (renomear para `vagas_peixe30` na expansão) |
| `configuracoes` | parâmetros agnósticos do sistema |
| `logs_sistema` | rastreabilidade total de ações |

### Tabelas previstas
| Tabela | Fase | Campos principais |
|---|---|---|
| `candidatos` | 3 | nome, email, telefone, formação, habilidades, experiências, arquivo_original |
| `curriculos_gerados` | 4 | id_candidato, id_vaga, arquivo_pdf, data_geracao, score_aderencia |

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
| `perfis` | id_candidato (FK 1:1), telefone, cidade, estado, linkedin, github, resumo_profissional |
| `candidato_experiencias` | id, id_candidato (FK), empresa, cargo, inicio, fim, descricao, atual |
| `candidato_formacoes` | id, id_candidato (FK), instituicao, curso, nivel, inicio, conclusao, em_andamento |
| `candidato_habilidades` | id, id_candidato (FK), habilidade, nivel (Básico/Intermediário/Avançado/Especialista) |
| `candidato_idiomas` | id, id_candidato (FK), idioma, proficiencia (Básico/Intermediário/Avançado/Fluente/Nativo) |
| `candidato_certificacoes` | id, id_candidato (FK), nome, instituicao, data_obtencao, validade |
| `documentos` | id, id_candidato (FK), tipo, nome_arquivo, caminho, descricao, data_upload |

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
| `interface_backend.py` — rotas FastAPI + StaticFiles | ✅ |
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

### [Fase 3] Motor 2 — Identidade e Acesso — ⏳ Próxima implementação

**Objetivo:** Sistema com login obrigatório, isolamento de dados por candidato e sessão segura.

| Entrega | Status |
|---|---|
| Tela `login.html` — porta de entrada obrigatória | ❌ |
| Tela `cadastro.html` — primeiro acesso | ❌ |
| Tabelas `candidatos` e `sessoes` no banco | ❌ |
| Endpoint `POST /auth/cadastrar` | ❌ |
| Endpoint `POST /auth/login` — devolve token UUID4 | ❌ |
| Endpoint `POST /auth/logout` — revoga token | ❌ |
| Middleware de autenticação — intercepta toda rota protegida | ❌ |
| `api.js` — header `Authorization: Bearer` em toda requisição | ❌ |
| `iniciar_servidor.bat` abre `/login` (não `/sar`) | ❌ |
| `dependencias.txt` atualizado: `passlib[bcrypt]` | ❌ |
| **Certificação:** acesso bloqueado sem login, dados isolados por candidato | ❌ |

---

### [Fase 4] Motor 3 — Perfil do Candidato — ⏳ Pendente

**Objetivo:** Candidato constrói perfil completo via importação de documento ou formulário manual.

| Entrega | Status |
|---|---|
| Tabelas filhas: perfis, experiências, formações, habilidades, idiomas, certificações, documentos | ❌ |
| Endpoint `POST /candidatos/importar` — upload de arquivo | ❌ |
| `rotinas/ia.py` — abstração Gemini | ❌ |
| Extração de texto: PDF, DOCX, TXT | ❌ |
| Prompt Gemini etapa única: texto → perfil estruturado JSON | ❌ |
| Tela `candidatos.html` — formulário com salvamento parcial | ❌ |
| Validação mínima para geração: nome + contato + habilidade + experiência OU formação OU certificação | ❌ |
| Contêiner de documentos — upload, catalogação e listagem | ❌ |
| `.env` atualizado: `IA_PROVEDOR`, `IA_MODELO`, `IA_API_KEY` | ❌ |
| `dependencias.txt`: google-generativeai, pdfplumber, python-docx | ❌ |
| **Certificação:** perfil real importado e extraído corretamente pela IA | ❌ |

---

### [Fase 5] Motor 4 — Geração de Currículo Premium — ⏳ Pendente

**Objetivo:** IA gera currículo personalizado por vaga, candidato revisa e exporta pacote ZIP.

| Entrega | Status |
|---|---|
| Tabelas `candidaturas` e `curriculos_gerados` no banco | ❌ |
| Endpoint `POST /curriculos/analisar` — Gemini etapa 1+2 (requisitos + score) | ❌ |
| Endpoint `POST /curriculos/gerar` — Gemini etapa 3 (currículo HTML) | ❌ |
| Endpoint `POST /curriculos/exportar` — weasyprint → PDF | ❌ |
| Endpoint `POST /curriculos/empacotar` — ZIP no Desktop | ❌ |
| Editor `contenteditable` — edição livre antes do PDF | ❌ |
| Geração de carta de apresentação sob demanda (Gemini) | ❌ |
| Score de aderência exibido antes da geração | ❌ |
| Tom adaptativo por perfil (jovem aprendiz / sênior) | ❌ |
| Histórico de currículos gerados por candidato | ❌ |
| `dependencias.txt`: weasyprint | ❌ |
| **Certificação:** currículo premium gerado, editado, exportado em ZIP no Desktop | ❌ |

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
