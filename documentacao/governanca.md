# Contrato de Governança - Sistema de Automação de Recolocação (SAR)

Este documento é a única fonte de verdade para a estrutura, nomenclatura e evolução do projeto. Nenhuma linha de código deve ser escrita sem atender a estes critérios.

## 1. Nomenclatura de Arquivos

**Decisão vigente:** prefixos abolidos. Nenhum arquivo do projeto usa prefixo técnico (`srv_`, `db_`, `bot_`, `cfg_`, `prc_`, `gui_` ou similares).

### Regra
- O **nome do arquivo** comunica sua função de forma descritiva e legível.
- A **localização na pasta** comunica sua natureza técnica.
- Nomes em português, sem abreviações obscuras, sem underscores de prefixo.

### Exemplos vigentes
| Arquivo | Pasta | O que comunica |
|---|---|---|
| `servidor.py` | `/backend` | ponto de entrada e orquestrador do sistema |
| `interface_backend.py` | `/backend` | definição das rotas e configuração da API |
| `genericas.py` | `/backend/rotinas` | rotinas genéricas de persistência |
| `dependencias.txt` | raiz | dependências Python do projeto |
| `SAR.html` | `/frontend/telas` | tela principal do sistema |
| `visual.css` | `/frontend/estilos` | identidade visual global |
| `api.js` | `/frontend/scripts` | comunicação com o backend |
| `vagas.js` | `/frontend/scripts` | lógica da tela de vagas |

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

## 4. Segurança e Certificação SSL

### 4.1 Proibições — Regras Invioláveis
- **É terminantemente proibido** iniciar o servidor (`srv_interface_backend.py`) sem certificado SSL ativo.
- **É terminantemente proibido** expor qualquer rota da API em protocolo `http://` em ambiente de desenvolvimento ou produção.
- **É terminantemente proibido** commitar a chave privada (`sar.key`) ou o arquivo `.env` no repositório. Esses arquivos estão protegidos no `.gitignore` e devem permanecer assim.
- **É terminantemente proibido** compartilhar, copiar ou transmitir a chave privada por qualquer meio (e-mail, chat, repositório, nuvem).

### 4.2 Localização dos Certificados
```
certificado/
  publico/
    sar.crt       → Certificado público (pode ser versionado no git)
  privado/
    sar.key       → Chave privada (NUNCA vai ao git — .gitignore ativo)
```

### 4.3 Variáveis de Ambiente
Os caminhos dos certificados são referenciados exclusivamente via `.env` na raiz do projeto:
```
SSL_CERTFILE=certificado/publico/sar.crt
SSL_KEYFILE=certificado/privado/sar.key
```

### 4.4 Comando Obrigatório de Inicialização do Servidor
```bash
uvicorn srv_interface_backend:app \
  --ssl-certfile=../certificado/publico/sar.crt \
  --ssl-keyfile=../certificado/privado/sar.key \
  --reload
```

### 4.5 Renovação
- O certificado local gerado via `mkcert` expira em **27/07/2028**.
- Ao renovar: gerar novos arquivos nas mesmas pastas e reiniciar o servidor.
- A CA local (`mkcert -install`) deve ser reinstalada em toda máquina nova de desenvolvimento.

## 5. Protocolo de Qualidade
1. Planejamento (Markdown)
2. Análise de Prioridade
3. Execução Técnica (Um arquivo por vez)
4. Teste de Laboratório (Logs de execução)
5. Teste de Usuário (Validação manual)