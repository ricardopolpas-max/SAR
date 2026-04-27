# Fluxograma de Processos - SAR (Sistema de Automação de Recolocação)

## 1. Ciclo de Vida da Funcionalidade (Pilar de Qualidade)
[Planejamento no Plano] -> [Atualização da Governança] -> [Codificação de Arquivo Único] -> [Teste de Laboratório em /apoio] -> [Validação de Usuário] -> [Estabilização/Merge]

## 2. Roadmap de Evolução por Fases
1. **Fase 1: Fundação** (Ambiente limpo, Orquestrador `servidor.py` e Interface `SAR.html`).
2. **Fase 2: Persistência** (Modelagem SQLite e Rotinas de CRUD agnósticas em `/rotinas`).
3. **Fase 3: Inteligência** (Motores de Scoring `prc_` e processamento de dados).
4. **Fase 4: Conectividade** (Subpasta `/integracao/rotas` e Robôs `bot_` isolados).
5. **Fase 5: UX/UI** (Refinamento da Interface e integração total via Fetch API).
6. **Fase 6: Stress & QA** (Simulação de falhas, logs em `/apoio` e testes unitários).
7. **Fase 7: Certificação** (Auditoria de performance, limpeza de código e congelamento de versão).

---
## 3. Fluxo de Dados (Agnóstico)
[Interface GUI] <--> [Orquestrador servidor.py]
                        |
                        +--> [Processamento /prc_]
                        +--> [Persistência /db_]
                        +--> [Integração /rotas]

**Status Atual:** Fase 1 iniciada. Governança estabelecida.
**Próxima Meta:** Consolidar `servidor.py` e remover vestígios de arquivos `.js`.