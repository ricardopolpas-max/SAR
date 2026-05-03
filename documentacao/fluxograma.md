# Fluxograma de Processos - SAR (Sistema de Automação de Recolocação)

## 1. Ciclo de Vida da Funcionalidade (Pilar de Qualidade)
[Planejamento] → [Análise de Prioridade] → [Execução — 1 arquivo por vez] → [Teste de Laboratório] → [Validação do Usuário] → [Documentação obrigatória: diário + fluxograma + plano]

---

## 2. Roadmap de Evolução por Fases

| Fase | Nome | Status |
|---|---|---|
| 1 | Fundação — ambiente, orquestrador e interface inicial | ✅ Concluída |
| 2 | Motor 1 — Captura de vagas (Peixe 30) | ✅ Concluída |
| 3 | Motor 2 — Identidade e Acesso (auth + sessão) | ✅ Concluída |
| 4 | Motor 3 — Perfil do Candidato | ✅ Implementado / ⏳ Certificação pendente |
| 5 | Motor 4 — Geração de Currículo Premium (IA) | ⏳ Pendente |
| 6 | UX/UI — refinamento da interface | ⏳ Pendente |
| 7 | Stress & QA — testes e simulação de falhas | ⏳ Pendente |
| 8 | Certificação — auditoria e congelamento de versão | ⏳ Pendente |

---

## 3. Status Atual — 2026-05-03

**Fase ativa:** Motor 3 — Perfil do Candidato (implementado, aguardando certificação)

### Concluído
- [x] Estrutura de pastas do projeto e governança completa
- [x] Backend: FastAPI + SQLite em `%APPDATA%\SAR\sar_repositorio.db`
- [x] CRUD agnóstico em `rotinas/genericas.py` — ponto único de acesso ao banco
- [x] Frontend: `SAR.html`, `visual.css`, `vagas.js`, `api.js`
- [x] Repositório GitHub sincronizado
- [x] SSL local configurado com mkcert (válido até 27/07/2028)
- [x] Motor 1 — Sync bidirecional Peixe 30, UPSERT por `id_externo`, DELETE protegido
- [x] Motor 2 — Auth bcrypt, token UUID4 em `sessionStorage`, middleware, telas login/cadastro
- [x] Motor 3 — Perfil do candidato: 8 tabelas, CRUD completo, upload de arquivo
- [x] Correção arquitetural: DB único em AppData, `_obter_conexao()` como ponto único

### Pendente — certificação Motor 3 (teste físico não concluído — 2026-05-02)
- [ ] **Bug crítico:** formulários das abas do perfil não abrem (binding `data-aba` desconectado)
- [ ] Cadastro: falta confirmação de senha + eye toggle
- [ ] Vagas: falta filtro de localidade (combobox `SELECT DISTINCT localizacao`)
- [ ] UX perfil: avaliar página única vs abas (preferência do usuário: sem trocas de página)

### Próximo — Motor 4 (bloqueado até certificação do Motor 3)
- [ ] Geração de currículo personalizado por vaga via Gemini
- [ ] Score de aderência candidato × vaga
- [ ] Exportação PDF + pacote ZIP no Desktop

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
[backend/aplicacao.py]          ← rotas FastAPI
        |
        ↓
[backend/rotinas/genericas.py]  ← CRUD SQLite (_obter_conexao — ponto único)
        |
        ↓
[%APPDATA%\SAR\sar_repositorio.db]  ← Verdade Absoluta
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

1. Corrigir bug crítico: formulários das abas do perfil não abrem
2. Corrigir cadastro: adicionar confirmação de senha + eye toggle
3. Corrigir vagas: adicionar filtro de localidade
4. Decidir UX perfil: página única vs abas
5. Validação real do Motor 3 pelo usuário (certificação)
6. Iniciar Motor 4 — Geração de Currículo Premium
