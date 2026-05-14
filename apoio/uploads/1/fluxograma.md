# FLUXOGRAMA VISUAL — Valida Provas PRO (v1.0)

> Documento Normativo Oficial — gerado em 04/04/2026.
> Reflete a arquitetura implementada e homologada pelo Arquiteto do Sistema.
> Qualquer alteração deve ser registrada no `diario_de_bordo.md`.

## Status Atual (2026-04-19)

- Integração em migração aplicada para protocolo Ukiceker v1.0 com autenticação Modo C (API Key + Profile Name).
- Operação do Valida consolidada em runtime WebSocket-only, sem provisão HTTP automática no cliente.
- Validação técnica real concluída com Ukiceker ativo: health, api-key, profile, import e query.
- Contrato HTTP consolidado: `api-key` exige `backend_id`; `profile` exige objeto `conexao` completo.
- Discrepâncias de legado documental saneadas e marcadas com contexto histórico onde aplicável.
- Saneamento complementar concluído em instruções de fase, arquitetura atual e guia de consultas da integração.
- Próxima etapa obrigatória: validação funcional de negócio com transações DML em ambiente controlado.

---

## Definições Oficiais

| Conceito | Quem é | Quem dispara | Campos na troca | ACL |
|----------|--------|--------------|-----------------|-----|
| **ADMIN** | Primeiro usuário do sistema, criado automaticamente | Boot com tabela vazia | Nome + Nick + Senha | Privilégio FULL gerado automaticamente |
| **DEUS** | Super-usuário de contingência, criado silenciosamente | Auto-cura (sem FULL na base) | Nome + Nick + Senha | Privilégio FULL gerado automaticamente |
| **RESET** | Usuário existente que perdeu o acesso | Admin clica "Restaurar Acesso" (botão exclusivo para FULL) | **Só Senha + Confirmação** (Nome/Nick/ACL bloqueados) | Mantém ACL existente intocada |

> **Lógica de Senhas Universal:** O backend envia o **hash bcrypt** para o frontend injetar silenciosamente.
> O backend detecta se recebeu hash (comparação direta) ou texto plano (`bcrypt.checkpw`).
> Hash direto só é aceito se `requer_troca_senha='S'`.

> **Silêncio Absoluto:** A senha nunca é exibida ou enviada em mensagem ao usuário.
> O hash bcrypt é injetado pelo frontend de forma transparente.

---

## Fluxo Mestre

```mermaid
flowchart TD
    subgraph INIT["INICIALIZAÇÃO"]
        FE["FRONTEND"] --> CHECK{"check_init\nVerifica estado da tabela"}
    end

    subgraph VAZIO["A — TABELA VAZIA"]
        CHECK -- "Banco vazio" --> CRIA_ADMIN["Auto-Cura: cria ADMIN\nvia .env + HMAC registrado"]
        CRIA_ADMIN --> BOOT_VAZIO["boot_vazio\nFrontend injeta hash ADMIN"]
        BOOT_VAZIO --> LOGIN_INIT["Usuário confirma com ENTER\n(hash injetado silenciosamente)"]
        LOGIN_INIT --> REDIR_GU_A["Redireciona para\nGestão de Usuários"]
        REDIR_GU_A --> TROCA_A["Troca obrigatória:\nNome + Nick + Senha\nHMAC recriado"]
        TROCA_A --> LOGOFF_A["Logoff obrigatório"]
        LOGOFF_A --> LOGIN_NOVO_A["Novo login com\nnovas credenciais"]
        LOGIN_NOVO_A -. "Falhou" .-> LOOP_A["Loop de Barreira\nFoco volta ao nick"]
        LOGIN_NOVO_A -- "Sucesso" --> DASHBOARD
    end

    subgraph POVOADO["B — TABELA POVOADA"]
        CHECK -- "Tabela povoada" --> TESTA_FULL{"Existe usuário\ncom privilégio FULL?"}
    end

    subgraph SEM_FULL["B1 — SEM FULL"]
        TESTA_FULL -- "Não" --> CRIA_DEUS["Auto-Cura: cria DEUS\nsilenciosamente\n+ HMAC registrado"]
        CRIA_DEUS --> RELOAD["Recarrega snapshot\nde boot"]
        RELOAD --> BOOT_ONLINE
    end

    subgraph COM_FULL["B2 — COM FULL"]
        TESTA_FULL -- "Sim" --> TESTA_ADMIN{"Existe nick ADMIN\nno banco?"}
        TESTA_ADMIN -- "Sim" --> BOOT_PEND["boot_pendencia\nFrontend injeta hash ADMIN"]
        BOOT_PEND --> LOGIN_PEND["Usuário confirma com ENTER"]
        LOGIN_PEND --> REDIR_GU_B["Redireciona para\nGestão de Usuários"]
        REDIR_GU_B --> TROCA_B["Troca obrigatória:\nNome + Nick + Senha\nHMAC recriado"]
        TROCA_B --> LOGOFF_B["Logoff obrigatório"]
        LOGOFF_B --> LOGIN_NOVO_B["Novo login com\nnovas credenciais"]
        LOGIN_NOVO_B -- "Sucesso" --> DASHBOARD
        TESTA_ADMIN -- "Não" --> BOOT_ONLINE["boot_online\nTela de login normal"]
        BOOT_ONLINE --> TELA_LOGIN
    end

    subgraph LOGIN["TELA DE LOGIN"]
        TELA_LOGIN["Campo nick\n(blur dispara check_status)"] --> CHECK_STATUS{"check_status\n(prioridade: reset=S primeiro)"}
        CHECK_STATUS -- "Nick = ADMIN" --> INJ_ADMIN["Injeta hash ADMIN\nMsg: CONFIGURAÇÃO PENDENTE"]
        CHECK_STATUS -- "Nick = DEUS" --> INJ_DEUS["Injeta hash DEUS\nMsg: ACESSO DE CONTINGÊNCIA"]
        CHECK_STATUS -- "reset = S" --> INJ_RESET["Injeta hash RESET_SENHA\nMsg: ACESSO REESTABELECIDO"]
        CHECK_STATUS -- "requer_troca = S" --> INJ_PRIM["Injeta hash\nMsg: PRIMEIRO ACESSO"]
        CHECK_STATUS -- "Normal" --> CAMPO_SENHA["Foco move para campo senha"]
        CHECK_STATUS -- "Inativo" --> BLOQ["Bloqueado\nContate o administrador"]
        INJ_ADMIN --> CONFIRMA["Usuário confirma\ncom ENTER"]
        INJ_DEUS --> CONFIRMA
        INJ_RESET --> CONFIRMA
        INJ_PRIM --> CONFIRMA
        CONFIRMA --> AUTENTICA
        CAMPO_SENHA --> AUTENTICA
    end

    subgraph AUTH["AUTENTICAÇÃO"]
        AUTENTICA["POST /api/seguranca/autenticacao\nacao=login"] --> HMAC{"Validação HMAC\n(camada extra)"}
        HMAC -- "Falhou" --> ERRO_AUTH["Erro: integridade\nde credencial"]
        HMAC -- "OK" --> ATIVO{"Usuário ativo?"}
        ATIVO -- "Não" --> ERRO_INATIVO["Erro: usuário inativo"]
        ATIVO -- "Sim" --> SENHA{"Senha válida?\n(hash direto ou bcrypt)"}
        SENHA -- "Não" --> LOOP_AUTH["Loop de Barreira\nFoco volta ao nick"]
        SENHA -- "Sim" --> REQUER_TROCA{"requer_troca_senha = S?"}
        REQUER_TROCA -- "Sim" --> SESSAO_REDIR["Salva sessão\nRedireciona para\nGestão de Usuários"]
        REQUER_TROCA -- "Não" --> LOGIN_OK["status: ok\nSalva sessão"]
        LOGIN_OK --> DASHBOARD
        SESSAO_REDIR --> GU
    end

    subgraph GU["GESTÃO DE USUÁRIOS (Ambiente Controlado)"]
        GU_TELA["Tela de Gestão\nde Usuários"] --> TROCA_CRED["Troca de credenciais\n(campos conforme perfil)"]
        TROCA_CRED --> SALVA_HMAC["Salva novas credenciais\nHMAC recriado\nrequer_troca_senha = N"]
        SALVA_HMAC --> LOGOFF_GU["Logoff obrigatório"]
        LOGOFF_GU --> TELA_LOGIN
    end

    subgraph DESTINO["DESTINO FINAL"]
        DASHBOARD["DASHBOARD\nPainel do Perito"]
    end

    style INIT fill:#1a1a2e,stroke:#16213e,color:#e6e6e6
    style VAZIO fill:#0d3b66,stroke:#1e5f8a,color:#e6e6e6
    style POVOADO fill:#1b2838,stroke:#2a4858,color:#e6e6e6
    style SEM_FULL fill:#4a1525,stroke:#6b2035,color:#e6e6e6
    style COM_FULL fill:#1a3a2a,stroke:#2a5a3a,color:#e6e6e6
    style LOGIN fill:#2a1a3a,stroke:#4a2a5a,color:#e6e6e6
    style AUTH fill:#1a2a3a,stroke:#2a3a5a,color:#e6e6e6
    style GU fill:#3a2a0a,stroke:#5a4a1a,color:#e6e6e6
    style DESTINO fill:#0a3a0a,stroke:#1a5a1a,color:#e6e6e6
    style DASHBOARD fill:#004d00,stroke:#008800,color:#fff
```

---

## Detalhamento: check_status (Blur no Campo Nick)

> Executado automaticamente ao sair do campo nick (evento `blur`).
> Determina o tipo de credencial e injeta o hash no campo senha silenciosamente.

```mermaid
flowchart LR
    subgraph ENTRADA["Entrada"]
        N["Nick digitado\n(blur)"] --> CS["POST /api/seguranca/check_status"]
    end

    subgraph PRIORIDADES["Prioridades de Detecção (ordem)"]
        CS --> P1{"1. reset = S?"}
        P1 -- "Sim" --> R_RESET["status: reset\nHash de RESET_SENHA injetado\nMsg: ACESSO REESTABELECIDO"]
        P1 -- "Não" --> P2{"2. Nick = ADMIN?"}
        P2 -- "Sim" --> R_ADMIN["status: ADMIN\nHash de ADMIN_SENHA injetado\nMsg: CONFIGURAÇÃO PENDENTE"]
        P2 -- "Não" --> P3{"3. Nick = DEUS?"}
        P3 -- "Sim" --> R_DEUS["status: DEUS\nHash de DEUS_SENHA injetado\nMsg: ACESSO DE CONTINGÊNCIA"]
        P3 -- "Não" --> P4{"4. requer_troca = S?"}
        P4 -- "Sim" --> R_PRIM["status: primeiro_acesso_pendente\nHash injetado\nMsg: PRIMEIRO ACESSO"]
        P4 -- "Não" --> P5{"5. ativo = S?"}
        P5 -- "Sim" --> R_NORM["status: normal\nFoco move para campo senha"]
        P5 -- "Não" --> R_INAT["status: inativo\nFormulário bloqueado"]
    end

    subgraph RESERVADOS["Nicks Reservados Inexistentes"]
        CS --> RES{"Nick reservado\nsem registro no banco?"}
        RES -- "Sim" --> R_RES["status: reservado_indisponivel\nMsg: Contate o administrador"]
        RES -- "Não encontrado" --> R_DESC["status: desconhecido\nFoco move para campo senha"]
    end
```

---

## Detalhamento: Camada HMAC (Validação Extra)

> Camada de segurança adicional executada em **todo login**, antes de qualquer outra verificação de negócio.
> Garante integridade da credencial mesmo em caso de dump parcial do banco.

```mermaid
flowchart LR
    subgraph HMAC_FLOW["Validação HMAC"]
        L["Login recebido"] --> BU["Busca usuário por nick"]
        BU --> CV["Consulta credenciais_validacao\npor id do usuário"]
        CV --> EX{"Registro\nexiste?"}
        EX -- "Não" --> FAIL["Falha: integridade\nContate o administrador"]
        EX -- "Sim" --> AT{"Status = A\n(Ativo)?"}
        AT -- "Não" --> FAIL
        AT -- "Sim" --> CALC["Recalcula HMAC:\nid | login | hash_senha | chave_unica | versao"]
        CALC --> CMP{"compare_digest\nOK?"}
        CMP -- "Não" --> ADULTER["Falha: sinal de\nadulteração de banco"]
        CMP -- "Sim" --> PASS["HMAC OK\nSegue autenticação"]
    end

    subgraph REGISTRO["Quando o HMAC é Registrado/Atualizado"]
        R1["Boot: criar_usuario_padrao (ADMIN)"]
        R2["Boot: criar_usuario_deuses (DEUS)"]
        R3["Gestão de Usuários: salvar_usuario (novo)"]
        R4["Gestão de Usuários: salvar_usuario (update com nova senha)"]
        R5["Autenticação: trocar_senha_usuario (troca de credenciais)"]
    end
```

---

## Detalhamento: Gestão de Usuários (Ambiente Controlado)

> Acesso restrito a usuários autenticados.
> Toda operação de credencial é registrada na trilha de auditoria imutável.

```mermaid
flowchart TD
    subgraph ACESSO["Acesso ao Módulo"]
        SES["Sessão válida\n(sessionStorage + 8h)"] --> GU["Tela de Gestão\nde Usuários"]
    end

    subgraph OPERACOES["Operações Disponíveis"]
        GU --> OP1["Novo Usuário\nNome + Nick + Senha + ACL"]
        GU --> OP2["Editar Usuário\n(Nick/Senha → recria HMAC)"]
        GU --> OP3["Restaurar Acesso\n(apenas FULL)\nGrava reset=S + hash RESET_SENHA"]
        GU --> OP4["Definir ACL\nGranular por Módulo + Ação"]
        GU --> OP5["Excluir Usuário\n(CASCADE: credenciais + permissões)"]
        GU --> OP6["Troca de Credenciais\n(requer_troca_senha=S)\nredirecionado pelo login"]
    end

    subgraph TROCA["Fluxo Troca de Credenciais (requer_troca_senha=S)"]
        OP6 --> TC1{"Perfil?"}
        TC1 -- "ADMIN / DEUS / Novo" --> TC2["Campos: Nome + Nick + Senha\n+ Confirmação"]
        TC1 -- "RESET (reset=S)" --> TC3["Campos: Senha + Confirmação\n(Nome/Nick/ACL bloqueados)"]
        TC2 --> TC4["Valida:\n- Nick não pode ser reservado\n- Senha mín. 8 chars\n- Senha ≠ senhas padrão do sistema"]
        TC3 --> TC4
        TC4 --> TC5["Salva:\nNova senha (bcrypt)\nHMAC recriado\nrequer_troca_senha=N\nreset=N"]
        TC5 --> TC6["Logoff obrigatório\nNovo login com novas credenciais"]
    end

    subgraph ACL["ACL Granular"]
        OP4 --> ACL1["Matriz: Módulo × Ação"]
        ACL1 --> ACL2["Sem hierarquia de cargo\nPermissão direta por par"]
        ACL2 --> ACL3["Bypass: privilegio_total = S\n(ignora permissões, acesso irrestrito)"]
        ACL3 --> ACL4["Aba ACL visível apenas\npara usuários FULL"]
    end
```

---

## Arquitetura de Integração

> O sistema opera em arquitetura **agnóstica**: o backend nunca acessa o banco diretamente.
> Toda comunicação de dados passa pela camada WebSocket (Ukiceker Conecta).

```mermaid
flowchart LR
    subgraph FRONT["Frontend"]
        BR["Navegador\n(JS Vanilla)"]
    end

    subgraph BACK["Backend (FastAPI + Uvicorn)"]
        API["Endpoints REST\n/api/seguranca/*\n/api/evidencias/*\n/api/ferramentas/*"]
        MW["Middlewares:\n- CORS\n- No-Cache\n- Redirect localhost\n- Auditoria"]
        INT["integracao/conecta_banco.py\n(Camada Agnóstica)"]
    end

    subgraph BRIDGE["Ukiceker Conecta (Bridge)"]
        WS["WebSocket Server\nProtocolo v1.0 (Modo C)\nidentify -> import(api_key+profile_name) -> query/transaction"]
    end

    subgraph DB["Banco de Dados (MySQL)"]
        MYSQL["Banco: valida\nTabelas: usuarios\ncredenciais_validacao\npermissoes_usuario\nmodulos / acoes\ntrilha_auditoria\nevidencias\nsolicitacoes\n..."]
    end

    BR -- "HTTPS" --> API
    API --> MW
    MW --> INT
    INT -- "WSS (WebSocket Seguro)" --> WS
    WS -- "SQL" --> MYSQL
    MYSQL -- "Resultado" --> WS
    WS -- "JSON" --> INT
    INT -- "Dict Python" --> API
    API -- "JSON" --> BR
```

---

## Tabela Comparativa de Perfis

| Aspecto | ADMIN | DEUS | RESET |
|---------|-------|------|-------|
| **Quem é** | 1º usuário do sistema | Contingência silenciosa | Existente, perdeu acesso |
| **Nick na tela** | ADMIN | DEUS | Nick real do usuário |
| **Detecção** | `check_status` (nick=ADMIN) | `check_status` (nick=DEUS) | `check_status` (reset=S) **PRIORIDADE** |
| **Hash injetado** | Hash bcrypt de ADMIN_SENHA (.env) | Hash bcrypt de ADMIN_SENHA (.env) | Hash bcrypt de RESET_SENHA (.env) |
| **Campos na troca** | Nome + Nick + Senha | Nome + Nick + Senha | **Só Senha + Confirmação** |
| **ACL** | FULL gerada automaticamente | FULL gerada automaticamente | Mantida intacta |
| **Após salvar** | Nick ADMIN desaparece do banco | Nick DEUS desaparece do banco | `reset=N` |

---

## Regras de Ouro

> **Silêncio Absoluto:** O hash bcrypt é injetado silenciosamente pelo frontend. A senha nunca aparece em mensagem, log visível ao usuário ou campo de texto legível.

> **Hash só com Pendência:** O backend aceita comparação direta de hash (`senha_input == hash_armazenado`) **somente** se `requer_troca_senha='S'`. Login normal usa sempre `bcrypt.checkpw`.

> **Prioridade do RESET:** No `check_status`, `reset=S` é verificado **antes** de qualquer outro perfil (ADMIN, DEUS, normal). Se `reset=N`, segue com as demais verificações.

> **Loop de Barreira:** Credencial inválida → campo nick limpo → foco retorna ao nick → sem limite de tentativas programático → acesso barrado até acertar.

> **Auto-Cura Soberana:** No boot, o sistema verifica e corrige seu próprio estado: banco vazio → cria ADMIN. Sem super usuário → cria DEUS silenciosamente. Ambos incluem registro HMAC obrigatório.

> **ACL Intocável:** A troca de credenciais **nunca** altera permissões. ACL é gerenciada exclusivamente pelo módulo de gestão de usuários, por usuário FULL.

> **HMAC Obrigatório:** Todo login passa pela validação HMAC antes de qualquer verificação de negócio. Registro ausente ou divergente = falha de integridade = acesso negado.

> **Ambiente Controlado:** Troca de credenciais ocorre exclusivamente na tela de Gestão de Usuários, com sessão autenticada ativa. Logoff e novo login são obrigatórios após a troca, para registro em auditoria.

---

## Mapa de Endpoints de Autenticação

| Endpoint | Método | Ação | Descrição |
|----------|--------|------|-----------|
| `/api/seguranca/autenticacao` | POST | `check_init` | Diagnóstico de boot |
| `/api/seguranca/autenticacao` | POST | `login` | Autenticação completa |
| `/api/seguranca/check_status` | POST | — | Estado do nick (blur) |
| `/api/seguranca/trocar_senha` | POST | — | Troca de credenciais (gestão de usuários) |
| `/api/seguranca/usuarios` | GET | — | Listar usuários |
| `/api/seguranca/usuarios/salvar` | POST | — | Criar/editar usuário |
| `/api/seguranca/usuarios/excluir/{id}` | DELETE | — | Remover usuário |
| `/api/seguranca/acl/modulos_acoes` | GET | — | Estrutura de ACL |
| `/api/seguranca/acl/usuario/{id}/salvar` | POST | — | Salvar permissões |
