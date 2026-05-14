# Plano de Desenvolvimento - Valida Provas (Planta Baixa)

O objetivo é construir o MVP (Produto Mínimo Viável) do sistema de validação de provas.

## Fase 1: Fundação (Marco Zero)
- [x] Estrutura de pastas e documentação base (Arquitetura por Competências).
- [x] Configuração do Servidor (FastAPI/Uvicorn).
- [x] Modelagem do Banco de Dados (PostgreSQL/MySQL).
- [x] Ponte de Integração (WebSocket/Ukiceker Conecta).


## Fase 2: Captura e Assinatura

- [x] Endpoint de envio de arquivos.
- [x] Lógica de geração de Hash SHA-256.
- [x] Registro de metadados (IP, Carimbo de Tempo).


## Fase 3: Cadeia de Custódia

- [x] Implementação de logs encadeados (auditoria).
- [x] Geração de relatório básico em PDF (Motor Unificado).


## Fase 4: Interface e Orquestração

- [x] Redesign do Dashboard Profissional.
- [ ] Gestão de Solicitações Nominais em Banco.
- [ ] Integração de Auditoria em Tempo Real.
- [ ] Ciclo completo de testes físicos e de laboratório.

## Fase 5: Utilitários e Orquestração (Frontend/Backend)
- [ ] Tela de Navegação e Exploração de Pastas (Repositório).
- [ ] Gestão Dinâmica de Links do Google Drive.
- [ ] Salvatagem e Vínculo de Links no Banco de Dados.

## Atualização de Bloco - 2026-04-19
- [x] Migração da integração para protocolo Ukiceker v1.0 (Modo C only) no backend.
- [x] Runtime do Valida consolidado em WebSocket-only (identify -> import_request -> query/transaction).
- [x] Startup consolidado para validação de ambiente, sem provisão HTTP automática.
- [x] Validação técnica real com Ukiceker ativo (health, api-key, profile, import, query).
- [x] Saneamento de documentação legada para aderência à fase atual do projeto.
- [x] Saneamento complementar de discrepâncias legadas em documentos auxiliares (instruções, arquitetura e guia de consultas).
- [ ] Validação funcional de negócio (fluxos completos de evidências/solicitações com transações DML em ambiente controlado).

## Atualização de Bloco - 2026-05-10 (Auditoria de Governança)
- [x] Varredura integral e correção de 100% das violações de nomenclatura (Seções 2 e 3 da Governança v2.0).
- [x] Código Python: 5 correções (acento em variável, argumento de função errado, variáveis locais em UPPERCASE, caminhos hardcoded com maiúsculas).
- [x] Diretórios: 5 renomeações (Imagens, Modulo_captura, Pacotes, Provas, doc_integração → todos lowercase/sem acento).
- [x] Arquivos: 9 renomeações (espaços, traços, maiúsculas removidos de .png, .txt, .bat, .hta, .md).
- [x] Removido backend/modelos/tabelas.py (DDL via Python — violação da Seção 4; conflito de nome de tabela).
- [ ] Próximo: Validação funcional de negócio com transações DML reais (INSERT/UPDATE/DELETE) em ambiente controlado.
