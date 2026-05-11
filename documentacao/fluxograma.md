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

## 3. Status Atual — 2026-05-11

**Fase ativa:** Motor 4 — implementado, pendente refinamentos e certificação end-to-end

### Certificado
- [x] Estrutura de pastas do projeto e governança completa
- [x] Backend: FastAPI + SQLite em `%APPDATA%\SAR\sar_repositorio.db`
- [x] CRUD agnóstico em `rotinas/genericas.py` — ponto único de acesso ao banco
- [x] Frontend: `SAR.html`, `visual.css`, `vagas.js`, `api.js`
- [x] Repositório GitHub sincronizado
- [x] SSL local configurado com mkcert (válido até 27/07/2028)
- [x] Motor 1 — Sync bidirecional Peixe 30, UPSERT por `id_externo`, DELETE protegido
- [x] Motor 2 — Auth bcrypt, token UUID4 em `sessionStorage`, middleware, telas login/cadastro
- [x] Motor 3 — Cadastro básico e acesso: 8 tabelas no banco, CRUD completo, upload de arquivo
- [x] DA-02 e DA-03 registradas e implementadas
- [x] Motor 4 — fluxo completo implementado (ver detalhes abaixo)

### Motor 4 — Implementado (pendente certificação física)
- [x] Importação de currículo (PDF/DOCX) → IA extrai → 8 tabelas populadas
- [x] Complementação manual: blocos de experiências, formações, habilidades, idiomas, certificações, contatos
- [x] Card de vagas: modal interno "Ver descrição" + botão "Preparar candidatura"
- [x] Camada IA abstrata — Gemini primário + Groq fallback automático
- [x] Entrevista guiada com Recrutador IA — pergunta a pergunta, histórico persistido
- [x] Score de aderência com barra visual e marco de 75%
- [x] Upload de documentos complementares durante entrevista (📎)
- [x] Geração de currículo personalizado — prompt ABNT, perfil multidisciplinar
- [x] DA-02: cada geração salva como ativo independente com timestamp
- [x] `_obter_base_perfil`: combina todos os currículos gerados como contexto multidisciplinar
- [x] Onboarding gate: menus bloqueados até importar currículo
- [x] Restauração de sessão: último currículo exibido ao retornar
- [x] PDF com formatação ABNT via `window.print()` — sem data/hora do browser
- [x] Texto do currículo justificado com `div.curriculo-display`
- [x] Prompt de importação genérico — contempla candidato multidisciplinar

### Pendências — próxima sessão
- [ ] Editor `contenteditable` — candidato edita o currículo antes de exportar
- [ ] Link externo liberado após gerar currículo (DA-03 completo)
- [ ] Restauração do histórico de chat ao retornar à seção
- [ ] Aviso não-bloqueante de vaga indisponível ao entrar no ciclo
- [ ] Tom adaptativo no prompt do Recrutador IA (jovem aprendiz ≠ sênior)
- [ ] Pacote ZIP no Desktop (PDF + carta + documentos)
- [ ] Carta de apresentação gerada junto com o currículo
- [ ] **Certificação end-to-end:** importação → entrevista → score 75% → geração → edição → PDF → candidatura

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

## 6. Próximos Passos — Refinamento Motor 4 (ordem de execução)

1. Editor `contenteditable` no currículo gerado — candidato ajusta antes de exportar
2. Link externo da vaga liberado após geração do currículo (DA-03 completa)
3. Restauração do histórico de chat ao retornar à seção Currículo Premium
4. Aviso não-bloqueante de vaga indisponível ao entrar no ciclo de candidatura
5. Tom adaptativo no prompt do Recrutador IA
6. Carta de apresentação gerada junto com o currículo
7. Pacote ZIP no Desktop (PDF + carta + documentos apensos)
8. Certificação end-to-end do fluxo completo
