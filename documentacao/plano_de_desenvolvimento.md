# Plano de Desenvolvimento — SAR (Sistema de Automação de Recolocação)

**Objetivo:** Plataforma inteligente para automação da jornada de recolocação profissional — captura de vagas, geração de currículo personalizado via IA e otimização para sistemas ATS de recrutamento.

**Última atualização:** 2026-04-28

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

## Esquema de Banco de Dados

### Tabelas existentes
| Tabela | Propósito |
|---|---|
| `vagas` | repositório central de oportunidades (expandir na Fase 2) |
| `configuracoes` | parâmetros agnósticos do sistema |
| `logs_sistema` | rastreabilidade total de ações |

### Tabelas previstas
| Tabela | Fase | Campos principais |
|---|---|---|
| `candidatos` | 3 | nome, email, telefone, formação, habilidades, experiências, arquivo_original |
| `curriculos_gerados` | 4 | id_candidato, id_vaga, arquivo_pdf, data_geracao, score_aderencia |

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

### [Fase 2] Captura de Vagas — ⏳ Próxima

**Objetivo:** Sistema sincroniza automaticamente com Peixe 30 e exibe vagas atualizadas.

**Fonte:** `GET https://api.jobs.peixe30.com/v1/jobs/search/eligible-to-apply-for?page=N&perPage=50`

| Entrega | Status |
|---|---|
| Migração DB: novos campos na tabela `vagas` | ❌ |
| `rotinas/sincronizacao.py` — motor de sync bidirecional | ❌ |
| Endpoint `POST /vagas/sincronizar` | ❌ |
| Sync automático no startup do servidor | ❌ |
| Botão "Atualizar Vagas" na tela principal | ❌ |
| Cards de vagas com campos completos (empresa, local, salário, regime) | ❌ |
| Filtros na tela: área, localização, regime, salário | ❌ |
| `dependencias.txt` atualizado com httpx ou requests | ❌ |
| **Certificação:** vagas do Peixe 30 aparecem na tela, sync funciona | ❌ |

**Algoritmo de sync:**
```
1. Registra timestamp de início
2. Busca todas as páginas (perPage=50, ~17 chamadas)
3. Para cada vaga: INSERT se nova, UPDATE se existente (chave: publicUrl)
4. DELETE vagas onde ultima_sincronizacao < timestamp (removidas do Peixe 30)
```

---

### [Fase 3] Candidatos e Extração de Perfil — ⏳ Pendente

**Objetivo:** Candidato importa currículo existente; IA extrai e estrutura o perfil automaticamente.

| Entrega | Status |
|---|---|
| Tabela `candidatos` no banco | ❌ |
| Endpoint `POST /candidatos/upload` (recebe arquivo) | ❌ |
| `rotinas/ia.py` — abstração Gemini (agnóstica ao provedor) | ❌ |
| Extração de texto: PDF, DOCX, TXT, ODT, RTF | ❌ |
| Prompt Gemini: texto bruto → perfil estruturado JSON | ❌ |
| Tela `candidatos.html` — upload + formulário de revisão pré-preenchido | ❌ |
| `candidatos.js` — lógica da tela | ❌ |
| `.env` atualizado: IA_PROVEDOR, IA_MODELO, IA_API_KEY | ❌ |
| `dependencias.txt` atualizado: google-generativeai, pdfplumber, python-docx, textract, python-magic | ❌ |
| **Certificação:** currículo real importado, perfil extraído corretamente pela IA | ❌ |

---

### [Fase 4] Geração de Currículo Personalizado — ⏳ Pendente

**Objetivo:** IA gera currículo personalizado por vaga com metadados ATS para maximizar aderência.

| Entrega | Status |
|---|---|
| Tabela `curriculos_gerados` no banco | ❌ |
| Endpoint `POST /curriculos/gerar` (candidato + vaga) | ❌ |
| Prompt Gemini: perfil + requisitos da vaga → currículo otimizado | ❌ |
| Injeção de metadados ATS (keywords, seções padronizadas, datas ISO) | ❌ |
| Geração de PDF com formatação profissional | ❌ |
| Tela `curriculos.html` — seleção candidato/vaga + download PDF | ❌ |
| Score de aderência candidato ↔ vaga | ❌ |
| **Certificação:** currículo gerado revisado e aprovado pelo usuário | ❌ |

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
