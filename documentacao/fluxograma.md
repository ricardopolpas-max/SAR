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

### Implementado — aguardando teste físico (2026-05-03)
- [~] Correção duplo aninhamento `/perfil-candidato/completo` — implementado, não testado
- [~] Remoção de tags orphans em `SAR.html` — implementado, não testado
- [~] Cadastro: campo confirmação de senha + eye toggle — implementado, não testado
- [~] Vagas: select de localidade com filtro dinâmico — implementado, não testado
- [x] DA-02 registrada: currículo como ativo reutilizável do candidato
- [x] DA-03 registrada: contenção na plataforma — link externo só no Motor 4

### Pendente — certificação Motor 3 (teste físico necessário)
- [ ] Teste físico de todas as correções acima pelo usuário
- [ ] UX perfil: avaliar página única vs abas (preferência do usuário: sem trocas de página)
- [ ] Card de vagas: modal interno "Ver descrição" + botão "Preparar candidatura" (substituir "Ver ↗")
- [ ] Endpoint leve `GET /vagas/verificar-disponibilidade` — ciclo automático de 20 min
- [ ] Validação real pelo usuário (certificação completa do Motor 3)

### Próximo — Motor 4 (bloqueado até certificação do Motor 3)
- [ ] Modal "Ver descrição" como pré-visualização da vaga antes de entrar no Motor 4
- [ ] Entrada via "Preparar candidatura" — score de aderência candidato × vaga
- [ ] Geração de currículo personalizado por vaga via Gemini
- [ ] Salvar como base / carregar base salva (DA-02)
- [ ] Exportação PDF + pacote ZIP no Desktop
- [ ] Link externo liberado somente após ciclo completo (DA-03)

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
- **DA-02:** Currículo é ativo reutilizável — nunca descartado, salvo como base para reaproveitamento
- **DA-03:** Candidato nunca sai da plataforma antes do ciclo completo — link externo só no Motor 4

---

## 6. Próximos Passos (ordem de execução)

1. Implementar modal interno "Ver descrição" + botão "Preparar candidatura" no card de vagas
2. Decidir e implementar UX perfil: página única vs abas
3. Implementar endpoint leve de verificação de disponibilidade de vagas (ciclo 20 min)
4. Validação real pelo usuário — certificação Motor 3
5. Iniciar Motor 4 — Geração de Currículo Premium (DA-02 + DA-03 aplicadas)
