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
| 4 | Motor 3 — Cadastro e Acesso (cadastro + login + sessão) | ✅ Certificado |
| 5 | Motor 4 — Importação + Perfil + Currículo Premium (IA) | ⏳ Pendente |
| 6 | UX/UI — refinamento da interface | ⏳ Pendente |
| 7 | Stress & QA — testes e simulação de falhas | ⏳ Pendente |
| 8 | Certificação — auditoria e congelamento de versão | ⏳ Pendente |

---

## 3. Status Atual — 2026-05-04

**Fase ativa:** Motor 4 — Importação, Perfil e Currículo Premium (pendente)

### Certificado
- [x] Estrutura de pastas do projeto e governança completa
- [x] Backend: FastAPI + SQLite em `%APPDATA%\SAR\sar_repositorio.db`
- [x] CRUD agnóstico em `rotinas/genericas.py` — ponto único de acesso ao banco
- [x] Frontend: `SAR.html`, `visual.css`, `vagas.js`, `api.js`
- [x] Repositório GitHub sincronizado
- [x] SSL local configurado com mkcert (válido até 27/07/2028)
- [x] Motor 1 — Sync bidirecional Peixe 30, UPSERT por `id_externo`, DELETE protegido
- [x] Motor 2 — Auth bcrypt, token UUID4 em `sessionStorage`, middleware, telas login/cadastro
- [x] Motor 3 — Cadastro básico e acesso: 8 tabelas no banco, CRUD completo, upload de arquivo (infraestrutura pronta para Motor 4)
- [x] Correção arquitetural: DB único em AppData, `_obter_conexao()` como ponto único
- [x] Cadastro: campo confirmação de senha + eye toggle
- [x] Vagas: select de localidade com filtro dinâmico
- [x] DA-02 registrada: currículo como ativo reutilizável do candidato
- [x] DA-03 registrada: contenção na plataforma — link externo só no Motor 4
- [x] Decisão de escopo: Motor 3 = cadastro básico + acesso. Perfil detalhado = Motor 4

### Pendente — Motor 4
- [ ] Importação de currículo (PDF/DOCX) como entrada primária do perfil
- [ ] Complementação manual dos dados extraídos pela IA
- [ ] Card de vagas: modal interno "Ver descrição" + botão "Preparar candidatura" (substituir "Ver ↗")
- [ ] Endpoint leve `GET /vagas/verificar-disponibilidade` — ciclo automático de 20 min
- [ ] Score de aderência candidato × vaga
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

## 6. Próximos Passos — Motor 4 (ordem de execução)

1. Importação de currículo existente (PDF/DOCX) → IA extrai → popula perfil automaticamente
2. Complementação manual dos dados extraídos (blocos: experiências, formações, habilidades, idiomas, certificações)
3. Modal interno "Ver descrição" + botão "Preparar candidatura" no card de vagas
4. Endpoint leve de verificação de disponibilidade de vagas (ciclo 20 min)
5. Score de aderência candidato × vaga via Gemini
6. Geração de currículo personalizado (DA-02 + DA-03 aplicadas)
7. Exportação PDF + pacote ZIP no Desktop
