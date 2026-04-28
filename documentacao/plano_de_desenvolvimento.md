# Plano de Desenvolvimento — SAR (Sistema de Automação de Recolocação)

**Objetivo:** Desenvolver uma plataforma inteligente para automação da jornada de recolocação profissional, focada em mineração de vagas, scoring de compatibilidade e geração de currículos inteligentes.

**Última atualização:** 2026-04-27

---

## Pilares Técnicos

1. **Simplicidade:** Código limpo, descritivo e de fácil manutenção.
2. **Segurança de Dados:** Persistência direta no SQLite (Verdade Absoluta), integridade via chaves estrangeiras.
3. **Rastreabilidade:** Diário de bordo atualizado a cada evolução.
4. **Automação Segura:** Robôs de extração (`bot_*`) via camada de integração dedicada.

---

## Tecnologias

- **Backend:** Python 3.12+, FastAPI, Uvicorn
- **Frontend:** HTML5, CSS3, JavaScript Vanilla
- **Banco de Dados:** SQLite (chaves estrangeiras ativas)
- **Integração:** Web Scraping e APIs Externas via `integracao/rotas/`
- **Segurança:** SSL via mkcert (dev) — certificado válido até 27/07/2028

---

## Hierarquia de Pastas

```
/
├── backend/
│   ├── servidor.py              ← orquestrador central (pendente)
│   ├── interface_backend.py     ← rotas FastAPI (pendente renomeação)
│   └── rotinas/
│       └── genericas.py         ← CRUD agnóstico SQLite ✅
├── frontend/
│   ├── telas/
│   │   └── SAR.html             ← tela principal ✅
│   ├── estilos/
│   │   └── visual.css           ← design system global ✅
│   └── scripts/
│       └── vagas.js             ← lógica de negócio ✅
├── integracao/
│   └── rotas/
│       └── api.js               ← transporte HTTP (pendente mover)
├── certificado/
│   ├── publico/sar.crt          ← certificado SSL ✅
│   └── privado/sar.key          ← chave privada (não vai ao git) ✅
├── documentacao/                ← governança, plano, fluxograma, diário ✅
├── apoio/                       ← testes, logs, scripts de suporte
├── .env                         ← variáveis de ambiente (não vai ao git) ✅
├── .gitignore                   ✅
├── dependencias.txt             ← pendente renomeação
└── .devcontainer/               ✅
```

---

## Roadmap por Fases

### [Fase 1] Fundação e Orquestração — 🔄 Em andamento

**Objetivo:** Ambiente funcional com handshake GUI ↔ Backend validado em HTTPS.

| Entrega | Status |
|---|---|
| Estrutura de pastas | ✅ |
| `rotinas/genericas.py` — CRUD SQLite | ✅ |
| `interface_backend.py` — rotas FastAPI | 🔄 (pendente renomeação) |
| `SAR.html` — tela principal | ✅ |
| `visual.css` — design system | ✅ |
| `vagas.js` — lógica de negócio | ✅ |
| `api.js` — transporte (mover para `integracao/rotas/`) | 🔄 |
| `servidor.py` — orquestrador com SSL | ❌ |
| Certificado SSL mkcert | ✅ |
| Correções de governança | 🔄 |
| **Certificação:** handshake HTTPS validado pelo usuário | ❌ |

### [Fase 2] Persistência e Verdade Absoluta — 🔄 Parcialmente iniciada

| Entrega | Status |
|---|---|
| Esquema SQLite (tabelas vagas, configuracoes, logs_sistema) | ✅ |
| CRUD agnóstico em `genericas.py` | ✅ |
| **Certificação:** teste de integridade e Foreign Keys | ❌ |

### [Fase 3] Processamento e Inteligência — ⏳ Pendente

- Motor de scoring (`calculo_compatibilidade.py`)
- Processamento de texto e automação de currículos
- **Certificação:** acurácia do score vs. critérios manuais

### [Fase 4] Integração e Conectividade — ⏳ Pendente

- Rotas de consumo de APIs externas em `integracao/rotas/`
- Robôs de extração com isolamento de falhas
- **Certificação:** logs de sucesso e tratamento de timeouts

### [Fase 5] Interface e UX — ⏳ Pendente

- Refinamento do `SAR.html` e novas telas
- Integração total Frontend ↔ Backend
- **Certificação:** validação de usabilidade pelo usuário

### [Fase 6] Qualidade e Stress — ⏳ Pendente

- Testes unitários e de integração em `/apoio`
- Simulação de falhas de rede e corrupção de banco

### [Fase 7] Certificação e Estabilização — ⏳ Pendente

- Auditoria de performance e limpeza de código
- Teste de Usuário Final (UAT) e congelamento de versão

---

## Protocolo de Qualidade (Obrigatório)

1. **Planejamento** — descrever antes de codificar
2. **Análise de Prioridade** — avaliar impactos e riscos
3. **Execução** — um arquivo por vez, autorização explícita do usuário
4. **Teste de Laboratório** — execução e logs
5. **Validação do Usuário** — teste real, não apenas execução de código
6. **Documentação** — atualizar diário de bordo, fluxograma e este plano

---

**Documentos relacionados:**
- `fluxograma.md` — status atual e próximos passos
- `governanca.md` — contrato de regras e nomenclatura
- `diario_de_bordo.md` — registro cronológico de decisões e eventos
