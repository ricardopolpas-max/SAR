# Plano de Desenvolvimento: SAR - Sistema de Automação de Recolocação

**Objetivo:** Desenvolver uma plataforma inteligente para automação da jornada de recolocação profissional, focada em mineração de vagas, scoring de compatibilidade e geração de currículos inteligentes.

## Pilares Técnicos
1. **Simplicidade:** Código limpo e de fácil manutenção.
2. **Segurança de Dados:** Persistência direta no SQLite (Garantia de Verdade Absoluta), com integridade via DELETE CASCADE.
3. **Rastreabilidade:** Diario de bordo atualizado a cada evolução.
4. **Automação Segura:** Implementação de robôs de extração (bot_) via camada de integração dedicada.

## Hierarquia de Pastas (Divisão de Competências)
- `/documentacao`: Contratos de governança, planos e documentação técnica.
- `/backend`: Orquestrador (`servidor.py`), processamento (`prc_`), persistência (`db_`) e `/rotinas`.
- `/frontend`: Interface de usuário (`SAR.html`) e recursos de apresentação.
- `/integracao`: Módulos de comunicação externa e subpasta `/rotas` (APIs de comunicação).
- `/apoio`: Arquivos de teste, logs, mocks e recursos de suporte técnico.

## Tecnologias Identificadas
- Backend: Python 3.12+ (FastAPI / Uvicorn)
- Frontend: HTML5, CSS3, JavaScript Vanilla
- Banco de Dados: SQLite (com chaves estrangeiras ativas)
- Integrações: Web Scraping e APIs Externas

## Roadmap de Evolução (Ciclo de Vida Certificado)

### [Fase 1] Fundação e Orquestração (Módulo 0)
- Configuração do ambiente virtual (VENV) e `cfg_dependencias_python.txt`.
- Implementação do `servidor.py` (Orquestrador Central).
- Criação da interface inicial `SAR.html` no `/frontend`.
*Certificação:* Validação de conectividade Handshake (GUI <-> Servidor).

### [Fase 2] Persistência e Verdade Absoluta (Módulo 1)
- Modelagem do esquema SQLite em `db_manipulacao_sqlite.py`.
- Implementação de rotinas de CRUD agnósticas em `backend/rotinas/genericas.py`.
*Certificação:* Teste de integridade de dados e conformidade de Foreign Keys.

### [Fase 3] Processamento e Inteligência (Módulo 2)
- Desenvolvimento do motor de scoring (`prc_calculo_compatibilidade.py`).
- Implementação de processamento de texto e automação de currículos.
*Certificação:* Validação de acurácia do score comparado a critérios manuais.

### [Fase 4] Integração e Conectividade (Módulo 3)
- Criação da subpasta `/integracao/rotas` para consumo de APIs externas.
- Desenvolvimento de robôs de extração (`bot_`) com isolamento de falhas.
*Certificação:* Logs de sucesso em chamadas externas e tratamento de timeouts.

### [Fase 5] Interface e UX (Módulo 4)
- Refinamento do `SAR.html` e componentes `gui_`.
- Integração total Frontend <-> Backend via Fetch API agnóstica.

### [Fase 6] Qualidade e Stress (Módulo 5)
- Implementação de testes unitários e de integração na pasta `/apoio`.
- Simulação de falhas de rede e corrupção de banco de dados.

### [Fase 7] Certificação e Estabilização (Módulo 6)
- Auditoria de performance e limpeza de código (Debloating).
- Teste de Usuário Final (UAT) e congelamento de versão (Baseline).

## Protocolo de Qualidade (Checklist Mandatório)
1. **Planejamento:** Toda nova funcionalidade deve ser descrita antes de codada.
2. **Análise de Prioridade:** Focar no que traz segurança e resultado imediato.
3. **Execução:** Um arquivo por vez para evitar conflitos.
4. **Teste de Laboratório:** Execução de scripts e logs.
5. **Teste Físico:** Solicitação de validação manual.

---
**Documentos Relacionados:**
- `fluxograma.md` (Controle de tarefas)
- `governanca.md` (Contrato de Governança)

**Última atualização: Fase 1 (Fundação) - Ambiente em conformidade.**