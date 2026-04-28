# Fluxograma de Processos - SAR (Sistema de Automação de Recolocação)

## 1. Ciclo de Vida da Funcionalidade (Pilar de Qualidade)
[Planejamento] → [Análise de Prioridade] → [Execução — 1 arquivo por vez] → [Teste de Laboratório] → [Validação do Usuário] → [Documentação obrigatória: diário + fluxograma + plano]

---

## 2. Roadmap de Evolução por Fases

| Fase | Nome | Status |
|---|---|---|
| 1 | Fundação — ambiente, orquestrador e interface inicial | 🔄 Em andamento |
| 2 | Persistência — SQLite e CRUD agnóstico | 🔄 Em andamento |
| 3 | Inteligência — motores de scoring e processamento | ⏳ Pendente |
| 4 | Conectividade — rotas de integração e robôs | ⏳ Pendente |
| 5 | UX/UI — refinamento da interface | ⏳ Pendente |
| 6 | Stress & QA — testes e simulação de falhas | ⏳ Pendente |
| 7 | Certificação — auditoria e congelamento de versão | ⏳ Pendente |

---

## 3. Status Atual — 2026-04-27

**Fase ativa:** Fase 1 (Fundação) — em processo de regularização

### Concluído
- [x] Estrutura de pastas do projeto
- [x] Backend: rotas `/` e `/vagas`, banco SQLite inicializado
- [x] CRUD agnóstico em `rotinas/genericas.py`
- [x] Frontend: `SAR.html`, `visual.css`, `vagas.js`
- [x] Repositório GitHub sincronizado
- [x] Devcontainer configurado para Codespaces
- [x] SSL local configurado com mkcert (válido até 27/07/2028)
- [x] Governança Seção 1 corrigida (prefixos abolidos)
- [x] Diário de bordo criado

### Em andamento — correções de governança
- [ ] Governança Seções 2, 3, 4, 5
- [ ] Renomear `srv_interface_backend.py` → `interface_backend.py`
- [ ] Renomear `cfg_dependencias_python.txt` → `dependencias.txt`
- [ ] Mover `api.js` → `integracao/rotas/api.js`
- [ ] Criar `servidor.py` (orquestrador com SSL)
- [ ] Teste real do frontend pelo usuário

### Pendente (Fase 1 — certificação bloqueada até concluir acima)
- [ ] Handshake GUI ↔ Backend validado pelo usuário em HTTPS

---

## 4. Fluxo de Dados (Arquitetura Vigente)

```
[frontend/telas/SAR.html]
        |
        ↓
[frontend/scripts/vagas.js]  ← lógica de negócio
        |
        ↓
[integracao/rotas/api.js]    ← transporte (HTTP/REST)
        |
        ↓
[backend/interface_backend.py]  ← rotas FastAPI
        |
        ↓
[backend/rotinas/genericas.py]  ← CRUD SQLite
        |
        ↓
[armazenamento_dados/sar_repositorio.db]  ← Verdade Absoluta
```

---

## 5. Decisões Arquiteturais Vigentes

- Prefixos abolidos — nomenclatura descritiva por função
- `frontend/scripts/` → apenas lógica de negócio
- `integracao/rotas/` → camada de transporte e abstração
- CSS global em `visual.css` — local apenas quando necessário
- WebSocket não utilizado neste projeto (acadêmico)
- SSL obrigatório — servidor nunca sobe sem certificado

---

## 6. Próximos Passos (ordem de execução)

1. Corrigir Governança Seções 2 a 5
2. Renomear `srv_interface_backend.py`
3. Renomear `cfg_dependencias_python.txt`
4. Mover `api.js` para `integracao/rotas/`
5. Criar `servidor.py`
6. Solicitar teste real do usuário
7. Certificar Fase 1
8. Iniciar Fase 3 (Inteligência)
