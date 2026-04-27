# Contrato de Governança - Sistema de Automação de Recolocação (SAR)

Este documento é a única fonte de verdade para a estrutura, nomenclatura e evolução do projeto. Nenhuma linha de código deve ser escrita sem atender a estes critérios.

## 1. Nomenclatura de Arquivos
Os nomes de arquivos devem ser funcionais e utilizar prefixos para identificar sua natureza técnica:
- **Orquestrador/Servidor:** Prefixo `srv_` | Principal: `servidor.py`
- **Persistência de Dados:** Prefixo `db_` (Ex: `db_manipulacao_sqlite.py`)
- **Automação/Scraping:** Prefixo `bot_` (Ex: `bot_extracao_vagas.py`)
- **Configurações:** Prefixo `cfg_` (Ex: `cfg_dependencias_sistema.txt`)
- **Processamento de Dados:** Prefixo `prc_` (Ex: `prc_calculo_compatibilidade.py`)
- **Interface de Usuário:** Prefixo `gui_` | Principal: `SAR.html`

## 2. Hierarquia e Divisão de Competências (Ambiente Puro Python/Web)
- `/documentacao`: Contratos de governança, planos e documentação técnica.
- `/backend`: Orquestrador (`servidor.py`), processamento (`prc_`), banco de dados (`db_`) e subpasta `/rotinas`.
- `/frontend`: Interface de usuário (`SAR.html`) e recursos de apresentação.
- `/integracao`: Módulos de comunicação externa e subpasta `/rotas` para APIs de comunicação.
- `/apoio`: Arquivos de teste, logs, ferramentas de suporte e arquivos não vinculados à regra de negócio.

## 3. Regras de Implementação
- **Unicidade:** É proibida a criação de múltiplos arquivos em um único turno de trabalho.
- **Verdade Absoluta:** O banco de dados SQLite é a única fonte confiável de dados do sistema.
- **Dependências:** Gerenciadas exclusivamente no arquivo `cfg_dependencias_python.txt`.

## 4. Protocolo de Qualidade
1. Planejamento (Markdown)
2. Análise de Prioridade
3. Execução Técnica (Um arquivo por vez)
4. Teste de Laboratório (Logs de execução)
5. Teste de Usuário (Validação manual)