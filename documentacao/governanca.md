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
| `api.js` | `/integracao/rotas` | comunicação com o backend |
| `vagas.js` | `/frontend/scripts` | lógica da tela de vagas |

## 2. Hierarquia e Divisão de Competências

Cada pasta tem responsabilidade única e exclusiva. Nenhum arquivo deve residir fora da pasta que representa sua natureza.

```
/
├── backend/
│   ├── servidor.py              → orquestrador central: carrega .env, SSL e sobe o servidor
│   ├── interface_backend.py     → definição das rotas FastAPI e inicialização do banco
│   └── rotinas/
│       └── genericas.py         → CRUD agnóstico SQLite (funções reutilizáveis)
│
├── frontend/
│   ├── telas/                   → arquivos HTML (uma tela por arquivo)
│   ├── estilos/
│   │   └── visual.css           → design system global — único CSS do sistema
│   └── scripts/                 → EXCLUSIVO para lógica de negócio (JS por tela/domínio)
│
├── integracao/
│   └── rotas/                   → camada de transporte e abstração de comunicação
│                                   (api.js e futuros conectores externos)
│
├── certificado/
│   ├── publico/                 → certificado SSL público (versionado no git)
│   └── privado/                 → chave privada (NUNCA no git)
│
├── documentacao/                → governança, plano, fluxograma, diário de bordo
├── apoio/                       → testes, logs, scripts de suporte, mocks
│
├── .env                         → variáveis de ambiente (NUNCA no git)
├── sar.pid                      → PID do processo ativo (NUNCA no git — gerado em runtime)
├── .gitignore
└── dependencias.txt             → dependências Python do projeto
```

### Regras de Divisão

- **`backend/`** — todo código Python que processa, persiste ou serve dados.
- **`frontend/scripts/`** — apenas lógica de negócio JavaScript. Nunca comunicação HTTP.
- **`integracao/rotas/`** — única camada que sabe como os dados trafegam. Frontend e backend nunca se comunicam diretamente — sempre passam por aqui.
- **`apoio/`** — nenhum arquivo de apoio entra em produção. É zona de laboratório.

## 3. Regras de Implementação

- **Unicidade:** É proibida a criação ou edição de múltiplos arquivos em um único turno de trabalho. Um arquivo por turno, sem exceção.
- **Autorização explícita:** Nenhuma linha de código é escrita sem estar prevista na governança, alinhada ao protocolo de qualidade e expressamente autorizada pelo usuário.
- **Verdade Absoluta:** O banco de dados SQLite é a única fonte confiável de dados do sistema. Nenhum dado é mantido em memória, cache ou variável de sessão.
- **Dependências:** Gerenciadas exclusivamente no arquivo `dependencias.txt` na raiz do projeto.
- **Documentação obrigatória:** Ao final de cada tarefa concluída, atualizar obrigatoriamente: `diario_de_bordo.md`, `fluxograma.md` e `plano_de_desenvolvimento.md`.

### 3.1 Banco de Dados — Regras Invioláveis

- **Localização obrigatória:** O banco reside exclusivamente em `%APPDATA%\SAR\sar_repositorio.db`. Portável, isolado por usuário Windows, sem dependência de estrutura de pastas do projeto.
- **Ponto único de acesso:** `_obter_conexao()` em `backend/rotinas/genericas.py` é o único local autorizado a chamar `sqlite3.connect()`. Nenhum outro arquivo do projeto pode chamar `sqlite3.connect()` diretamente.
- **Paths proibidos:** É terminantemente proibido usar paths relativos para dados críticos (banco, certificados, uploads). Todo path deve ser resolvido via variável de ambiente (`os.environ["APPDATA"]`) ou constante absoluta definida em `genericas.py`.
- **Sem duplicidade:** O sistema opera com um único arquivo de banco. A existência de múltiplos arquivos `.db` é falha arquitetural grave que compromete integridade dos dados.

## 4. Controle de Repositório — Regra Pétrea

**Somente arquivos estritamente necessários ao funcionamento do sistema são versionados no repositório git.**

### 4.1 O que PODE ir ao repositório
- Código-fonte do sistema (`backend/`, `frontend/`, `integracao/`)
- Documentação do projeto (`documentacao/`)
- Configurações de ambiente genéricas (`.gitignore`, `dependencias.txt`)
- Certificado SSL público (`certificado/publico/sar.crt`)
- Scripts de inicialização (`iniciar_servidor.bat`, `finalizar_servidor.bat`)

### 4.2 O que NUNCA vai ao repositório — proibição absoluta
- **Dados pessoais** de qualquer pessoa — currículos, documentos, certificados, fotografias
- **Arquivos gerados em runtime** — currículos premium gerados, uploads de candidatos (`apoio/uploads/`)
- **Credenciais e segredos** — `.env`, chave privada SSL (`sar.key`), tokens de API, senhas
- **Arquivos de processo** — `sar.pid`, `datetime` e similares gerados em execução
- **Banco de dados** — `*.db`, `*.sqlite` (a Verdade Absoluta nunca sai da máquina local)

### 4.3 Verificação obrigatória antes de todo commit
Antes de qualquer `git add` ou `git commit`, verificar:
1. Nenhum arquivo de `apoio/uploads/` está staged
2. Nenhum `.env` ou chave privada está staged
3. Nenhum `.db` ou `.sqlite` está staged
4. Nenhum arquivo com dado pessoal identificável está staged

**Em caso de dúvida sobre se um arquivo deve ou não ir ao repositório — não commitar e consultar.**

---

## 5. Segurança e Certificação SSL

### 5.1 Proibições — Regras Invioláveis
- **É terminantemente proibido** iniciar o servidor sem certificado SSL ativo.
- **É terminantemente proibido** expor qualquer rota da API em protocolo `http://` em qualquer ambiente.
- **É terminantemente proibido** commitar a chave privada (`sar.key`), o arquivo `.env` ou o arquivo `sar.pid` no repositório.
- **É terminantemente proibido** compartilhar ou transmitir a chave privada por qualquer meio (e-mail, chat, repositório, nuvem).
- **É terminantemente proibido** iniciar o servidor diretamente pelo Uvicorn — o ponto de entrada obrigatório é sempre o `servidor.py`.

### 5.2 Localização dos Certificados
```
certificado/
  publico/
    sar.crt       → certificado público (versionado no git)
  privado/
    sar.key       → chave privada (NUNCA vai ao git — protegida no .gitignore)
```

### 5.3 Variáveis de Ambiente
Caminhos referenciados exclusivamente via `.env` na raiz do projeto:
```
SSL_CERTFILE=certificado/publico/sar.crt
SSL_KEYFILE=certificado/privado/sar.key
HOST=127.0.0.1
PORT=8000
```

### 5.4 Inicialização Obrigatória do Servidor
O servidor é sempre iniciado pelo orquestrador `servidor.py`, que lê o `.env` e configura SSL automaticamente:
```bash
cd backend
python servidor.py
```
Nunca iniciar com Uvicorn diretamente na linha de comando.

### 5.5 Renovação do Certificado
- Certificado atual expira em **27/07/2028**.
- Ao renovar: executar `mkcert` nas mesmas pastas e reiniciar o servidor.
- Em máquina nova: executar `mkcert -install` para registrar a CA local no sistema antes de gerar o certificado.

## 6. Protocolo de Qualidade

Fluxo obrigatório para toda e qualquer entrega. Nenhuma etapa pode ser pulada.

### Etapas

| # | Etapa | Descrição |
|---|---|---|
| 1 | **Planejamento** | Descrever o que será feito, qual arquivo será alterado e qual o impacto esperado. Apresentar ao usuário antes de qualquer execução. |
| 2 | **Análise de Prioridade** | Avaliar riscos, dependências e ordem de execução. Identificar o que pode quebrar. |
| 3 | **Autorização** | Aguardar confirmação explícita do usuário. Sem autorização, nenhuma linha é escrita. |
| 4 | **Execução** | Um único arquivo por turno. Sem criatividade fora do escopo autorizado. |
| 5 | **Teste de Laboratório** | Verificar execução, logs e ausência de erros técnicos. |
| 6 | **Validação do Usuário** | Solicitar teste real ao usuário. A conclusão só é declarada após validação manual — nunca por presunção. |
| 7 | **Documentação** | Atualizar obrigatoriamente ao final de cada tarefa: `diario_de_bordo.md`, `fluxograma.md` e `plano_de_desenvolvimento.md`. |

### Regras de Conduta do Assistente

- Analisar como desenvolvedor sênior, executar como júnior disciplinado.
- Nunca tomar decisões sozinho — questionar sempre que houver dúvida.
- Nunca presumir contexto — perguntar se necessário.
- Sugerir melhorias, mas só implementar com autorização.
- Nunca considerar uma tarefa concluída sem validação real do usuário.

---

## 7. Implantação em Nuvem e Migração de Infraestrutura

### 7.1 Modelo de implantação vigente

O SAR é desenvolvido localmente (Windows) e implantado numa **VM Linux única** como serviço. A nuvem fornece apenas a máquina — o sistema **não depende de nenhuma API do provedor** para operar. Trocar de provedor = recriar a VM, levar os dados e repontar o DNS.

**Componentes da VM (documentados em `instalacao/setup_vm.sh`):**

| Item | Localização na VM |
|---|---|
| Código | `/home/<usuario>/SAR` (clone do git) |
| Ambiente Python | `venv/` dentro do app dir |
| Serviço | `systemd` — unit `sar.service`, `Restart=always`, executa `venv/bin/python servidor.py` a partir de `backend/` |
| Banco SQLite | `~/.local/share/SAR/sar_repositorio.db` (equivalente Linux de `%APPDATA%\SAR`) |
| Segredos | `~/SAR/.env` e `~/SAR/certificado/privado/sar.key` — criados manualmente, nunca no git |
| Uploads | `~/SAR/apoio/uploads/` e `~/SAR/apoio/Imagens/` — nunca no git |
| Porta | redirecionamento `iptables` 443 → 1024 (processo não-root) |
| TLS | Let's Encrypt via `certbot certonly --standalone` |

### 7.2 Ativos insubstituíveis — únicos que migram entre provedores

Só estes três não são recriados pelo `setup_vm.sh` e precisam ser copiados da VM antiga:

1. `~/.local/share/SAR/sar_repositorio.db` — a Verdade Absoluta (candidatos reais).
2. `~/SAR/.env` — configuração de produção + chaves de IA.
3. `~/SAR/apoio/uploads/` e `~/SAR/apoio/Imagens/` — arquivos enviados por candidatos.

O certificado **não migra** — é reemitido no destino (IP novo).

### 7.3 Migração AWS → Oracle Cloud — CONCLUÍDA (10/09/2026)

**Motivo:** o período gratuito da conta AWS expirava em 19/09/2026. **Destino final:** Oracle Cloud Always Free, região Sudeste do Brasil (Vinhedo), instância `sar-prod`.

**Desvios do plano original**, registrados para histórico:
- Shape planejado era `VM.Standard.A1.Flex` (ARM) — **capacidade esgotada** em Vinhedo no momento da criação. Usado **`VM.Standard.E2.1.Micro`** (AMD, 1 OCPU / 1 GB, Always Free) + swapfile de 2 GB.
- O certificado **foi migrado** (copiado de `/etc/letsencrypt` da AWS), não reemitido do zero — evitou depender de propagação de DNS antes do cutover.
- Antes do cutover, foi preciso resolver uma **divergência de git** entre o `main` local e o `origin/main` (histórico havia se separado) e corrigir a **trava de expiração** do `servidor.py`, que estava vencida (30/06/2026 → 30/06/2027).

**Execução (todos os 9 passos do plano original concluídos).** Cutover: DNS `sar.ukiceker.com.br` A-record apontado para o IP reservado da Oracle via registro.br; propagação confirmada em <5 min nos principais resolvedores. Validado com login real, import de currículo e geração de currículo tailored. AWS mantida no ar como rollback por alguns dias após o cutover, depois desligada (ver §7.5 e histórico no `diario_de_bordo.md`).

**Alterações de código efetivamente feitas nesta migração:** `instalacao/setup_vm.sh` (adaptado para Oracle/Ubuntu — fora do git, `.gitignore`), `dependencias.txt` e `backend/servidor.py` e `backend/rotinas/ia.py` (ver §7.5 — correções descobertas durante o review pós-cutover, não previstas no plano original).

### 7.4 Certificação SSL — §5.5 corrigida

A §5.5 desta governança estava desatualizada, descrevendo renovação via `mkcert` (válido só para o ambiente de desenvolvimento local). **Em produção o certificado é Let's Encrypt/`certbot`**, com renovação automática via `certbot.timer` + `deploy-hook` em `/etc/letsencrypt/renewal-hooks/deploy/` que copia o certificado renovado para `certificado/` e reinicia o serviço (ver §7.5, item B1). Sem o deploy-hook, o serviço continuaria servindo o certificado antigo após a renovação — foi exatamente essa falha, herdada da configuração da AWS, que este ajuste corrige.

### 7.5 Correções pós-cutover (review de sistema, 10/09/2026)

Um review completo pós-migração encontrou e corrigiu riscos que não eram do escopo da migração em si, mas que a exposição à produção real revelou:

| # | Achado | Correção |
|---|---|---|
| A1 | `dependencias.txt` citava `sqlalchemy` (0 usos no código) e `google-generativeai` (pacote errado — o código usa `from google import genai`) | Removido `sqlalchemy`; trocado para `google-genai` |
| A2 | `servidor.py`: seleção de porta sem `SO_REUSEADDR` — após restart, TIME_WAIT fazia o processo subir na porta errada e o redirecionamento `iptables 443→1024` deixava de funcionar | Adicionado `SO_REUSEADDR` em `_porta_livre()` |
| A3 | Groq descontinuou os modelos Llama nas chaves em uso — IA falhando em produção | `backend/rotinas/ia.py`: nova `_resolver_modelo()` consulta os modelos disponíveis via API e escolhe automaticamente, com o `.env` como preferência (não obrigação) — ver `feedback_filosofia_autocura` na memória do projeto |
| B1 | certbot sem deploy-hook — cert renovaria mas o serviço continuaria servindo o antigo | Deploy-hook criado (ver §7.4) |
| B2 | Nenhum backup do banco SQLite | Cron diário de backup local (retenção de 5 dias) — fallback de falha operacional, não substitui a Verdade Absoluta nem é disaster recovery |
| B3 | `vm.swappiness` no padrão (60) num host de 1 GB de RAM | Ajustado para 10 |