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
| 5 | Motor 4 — Importação + Perfil + Currículo Premium (IA) | ✅ Concluída |
| 6 | Distribuição — empacotamento e modo demo acadêmico | ✅ Concluída |
| 7 | UX/UI — refinamento da interface | ⏳ Pendente |
| 8 | Stress & QA — testes e simulação de falhas | ⏳ Pendente |
| 9 | Certificação — auditoria e congelamento de versão | ⏳ Pendente |

---

## 3. Status Atual — 2026-05-18

**Fase ativa:** Refinamentos pós-Motor 4 — sistema em uso, distribuição demo concluída

### Certificado
- [x] Estrutura de pastas do projeto e governança completa
- [x] Backend: FastAPI + SQLite em `%APPDATA%\SAR\sar_repositorio.db`
- [x] CRUD agnóstico em `rotinas/genericas.py` — ponto único de acesso ao banco
- [x] Frontend: `SAR.html`, `visual.css`, `vagas.js`, `perfil.js`, `curriculos.js`, `api.js`
- [x] Repositório GitHub sincronizado
- [x] SSL local configurado com mkcert (válido até 27/07/2028)
- [x] Motor 1 — Sync bidirecional Peixe 30, UPSERT por `id_externo`, DELETE protegido
- [x] Motor 2 — Auth bcrypt, token UUID4 em `sessionStorage`, middleware, telas login/cadastro
- [x] Motor 3 — Cadastro básico e acesso: 8 tabelas no banco, CRUD completo, upload de arquivo
- [x] Motor 4 — fluxo completo validado em produção
- [x] Distribuição demo acadêmica — `SAR.exe` autocontido com PyInstaller

### Motor 4 — Validado
- [x] Importação de currículo (PDF/DOCX) → IA extrai → merge incremental nas tabelas (sem sobrescrever)
- [x] Complementação manual: blocos de experiências, formações, habilidades, idiomas, certificações, contatos
- [x] Botão "Adicionar currículo" para importações adicionais (merge incremental)
- [x] Card de vagas: modal interno "Ver descrição" + botão "Preparar candidatura"
- [x] Camada IA abstrata — Gemini primário + Groq fallback automático
- [x] Prompts totalmente agnósticos — qualquer área profissional (não só jurídico)
- [x] `_obter_base_perfil` usa perfil estruturado do banco (fonte de verdade) — não currículos gerados
- [x] Recrutador IA orientado a lacunas de informação, não de capacidade
- [x] Entrevista guiada com Recrutador IA — pergunta a pergunta, histórico persistido
- [x] Score de aderência com barra visual e marco de 75%
- [x] Upload de documentos complementares durante entrevista (📎)
- [x] Geração de currículo premium ABNT — sem markdown, sem viés de área
- [x] Editor `contenteditable` — candidato edita o currículo antes de exportar
- [x] DA-02: cada geração salva como ativo independente com timestamp
- [x] Onboarding gate: menus bloqueados até importar currículo
- [x] Restauração de sessão: último currículo + histórico de chat ao retornar
- [x] PDF com formatação ABNT via `window.print()`
- [x] Aviso não-bloqueante de vaga indisponível
- [x] Cache-Control: no-store em arquivos estáticos
- [x] Tela Sobre: equipe completa, professora/coordenadora, links do desenvolvedor

### Distribuição demo acadêmica — Concluída
- [x] Trava de expiração: 30/06/2026
- [x] Leitura remota de `.env` e `sar.key` via URLs no `instalacao.dat`
- [x] Modo dev (sem `instalacao.dat`) usa arquivos locais
- [x] `SAR.exe` autocontido — Python, frontend, integracao e certificado embutidos
- [x] Abertura automática do browser em `/login`
- [x] `instalar.bat` e `modo_dev.bat`

### Pendências — próximas sessões
- [ ] Inno Setup — instalador profissional `SAR_Setup.exe`
- [ ] Múltiplos currículos base por candidato (arquitetura discutida)
- [ ] Tom adaptativo do Recrutador IA (sênior vs. jovem aprendiz)
- [ ] Carta de apresentação gerada pela IA
- [ ] Pacote ZIP no Desktop (PDF + carta + documentos)
- [ ] Link externo (DA-03) após ciclo completo
- [ ] Certificação end-to-end completa

---

## 4. Fluxo de Dados (Arquitetura Vigente)

```
[frontend/telas/SAR.html]
        |
        ↓
[frontend/scripts/*.js]      ← lógica de negócio por domínio
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
- **Agnóstico:** todos os prompts de IA avaliam qualquer área profissional — sem viés jurídico
- **Fonte de verdade para IA:** perfil estruturado do banco, nunca currículos gerados anteriormente

---

## 6. Próximos Passos (ordem de execução)

1. Inno Setup — instalador profissional `SAR_Setup.exe` para distribuição
2. Múltiplos currículos base — candidato importa bases por área, IA seleciona o mais aderente
3. Tom adaptativo — Recrutador IA ajusta linguagem ao perfil (sênior vs. jovem aprendiz)
4. Carta de apresentação gerada pela IA junto com o currículo premium
5. Pacote ZIP no Desktop (PDF + carta + documentos apensos)
6. Link externo (DA-03) liberado após pacote gerado
7. Certificação end-to-end do fluxo completo
