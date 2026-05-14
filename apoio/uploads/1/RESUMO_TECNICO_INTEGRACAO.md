# Resumo tecnico de integracao - Ukiceker Conecta

Aviso de conformidade: documento subordinado a documentacao/governanca.md.
Em caso de conflito de diretriz, prevalece a governanca tecnica.

Data: 2026-04-19
Versao de protocolo: 1.0

## 1. Objetivo

Fornecer um guia rapido para integrar backend cliente ao servidor Ukiceker Conecta,
utilizando validacao obrigatoria por API Key e Profile Name (Modo C).

## 2. Canais e endpoints

- WebSocket: sessao de operacao (importacao, consulta, transacao).
- HTTP local:
  - GET /health
  - POST /api/v1/integration/api-key
  - POST /api/v1/integration/profile
  - POST /api/v1/integration/resolve
  - POST /api/v1/integration/registry-sync

## 3. Fluxo de sessao WebSocket

1. handshake
2. identify
3. import_request
4. query_request / transaction_request / data_chunk

## 4. Formato correto de identify

```json
{
  "version": "1.0",
  "type": "identify",
  "payload": {
    "client_id": "meu-backend",
    "origin": "api",
    "app_version": "1.0.0"
  }
}
```

## 5. Formato correto de import_request (Modo C)

**ÚNICO MODO SUPORTADO: Validação por API Key + Profile Name**

### Modo C - api_key + profile_name

```json
{
  "version": "1.0",
  "type": "import_request",
  "payload": {
    "api_key": "<chave>",
    "profile_name": "db_producao"
  }
}
```

## 6. Hidratação de .env no primeiro contato

No primeiro import_request valido com API Key + Profile Name:

- servidor valida a api_key e profile_name recebidos;
- preenche RUNTIME_DB_* no .env conforme profile configurado;
- marca RUNTIME_DB_HYDRATED=1;
- se .env nao for gravavel, grava fallback em %TEMP% (.env.runtime);
- continua operacao sem derrubar o processo.

## 6.1 Sincronizacao do API Registry

Quando o cliente envia payload para POST /api/v1/integration/registry-sync:

- o servidor valida o objeto api_registry_data;
- persiste em memoria e tenta sincronizar no .env;
- em falha de escrita local, grava no fallback em %TEMP%;
- mantém continuidade operacional sem interromper a API.

## 7. Campos runtime gerados

- RUNTIME_DB_TYPE
- RUNTIME_DB_HOST
- RUNTIME_DB_PORT
- RUNTIME_DB_USER
- RUNTIME_DB_PASSWORD
- RUNTIME_DB_NAME
- RUNTIME_DB_HYDRATED
- RUNTIME_DB_HYDRATED_AT

## 8. Erros comuns

- identify sem origin/app_version: rejeitado pelo protocolo.
- import_request sem api_key ou profile_name: rejeitado pelo protocolo.
- api_key invalida ou expirada: import_request retorna erro de autenticacao.
- profile_name nao encontrado: import_request retorna erro de profile invalido.

## 8.1 Contrato de erro HTTP para integrador

Para erros da API HTTP, o contrato padrao inclui:

- code
- message
- details
- correlation_id
- header X-Correlation-ID

Cenario conhecido por engine:

- profile com driver ausente pode retornar 422 CONFIGURATION_ERROR (sem derrubar servidor).

## 9. Referencia operacional

- documento unico de execucao: documentacao/ROADMAP_TECNICO_EXECUCAO.md
- variaveis e guia de payload: .env.exemplo
- endpoint de geracao de api_key: POST /api/v1/integration/api-key
- endpoint de sincronizacao de registry: POST /api/v1/integration/registry-sync
- formato unico de payload: esta secao 5 (Modo C)

## 9.1 Diretriz de alinhamento para conectores

- O servidor nao deve ficar engessado em uma engine unica.
- A validacao de driver deve ocorrer por requisicao e por tipo de banco solicitado.
- Falha em driver de uma engine deve ser isolada, com erro claro para o integrador.
- Demais engines devem continuar operando normalmente no mesmo runtime.

## 10. Prompt tecnico de integracao (reutilizavel)

Use o texto abaixo para orientar integracao em outro projeto, mantendo contrato de payload e validacao de API:

Objetivo:

Integrar este projeto ao servico Ukiceker Conecta, implementando:

1. montagem dos payloads corretos
2. validacao de API HTTP
3. fluxo de sessao WebSocket completo
4. testes de ponta a ponta com evidencias

Contexto tecnico da integracao:

- Servico HTTP local padrao: http://127.0.0.1:8080
- Servico WebSocket: host e porta ativos do ambiente
- Fluxo obrigatorio de sessao:
  1. handshake
  2. identify
  3. import_request
  4. operacoes de dados

Endpoints HTTP a implementar e validar:

1. GET /health
2. POST /api/v1/integration/api-key
3. POST /api/v1/integration/profile
4. POST /api/v1/integration/resolve
5. POST /api/v1/integration/registry-sync
6. OPTIONS para preflight CORS dos endpoints de integracao

Requisitos obrigatorios de implementacao:

1. Criar cliente HTTP para os endpoints acima com timeout, retry e tratamento de erro.
2. Criar cliente WebSocket com reconexao controlada.
3. Nunca logar senha, api_key completa ou dados sensiveis.
4. Validar contrato JSON antes do envio.
5. Implementar fallback de erro com mensagens claras para integrador.
6. Permitir configuracao por ambiente (host, portas, credenciais, modo).

Validacao obrigatoria:

1. Health check retorna sucesso.
2. Geracao de api_key retorna chave valida.
3. Resolve por api_key + profile_name funciona.
4. Preflight CORS responde corretamente.
5. Fluxo WebSocket handshake -> identify -> import_request (Modo C) responde sem erro.
6. Cenarios de erro validados:
  - payload invalido (faltam api_key ou profile_name)
  - endpoint inexistente
  - api_key invalida ou expirada
  - profile_name nao encontrado
  - indisponibilidade temporaria de servico

Entregaveis esperados:

1. Codigo de integracao com clientes HTTP e WebSocket.
2. Modulo de montagem e validacao de payloads.
3. Suite de testes de integracao real ponta a ponta.
4. Relatorio final contendo:
  - testes executados
  - resultado de cada teste
  - evidencias de sucesso/falha
  - pendencias e riscos

Criterio de aceite:

A integracao so e considerada pronta se todos os testes criticos acima passarem em ambiente real.
