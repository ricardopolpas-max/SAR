# SAR — Sistema de Automação de Recolocação

Plataforma web com IA generativa integrada para automatizar a jornada de recolocação profissional no mercado jurídico. Desenvolvida como projeto acadêmico da disciplina de Desenvolvimento Pessoal e Trabalhabilidade (DPT) — Área: Direito — UNINASSAU Campina Grande.

**Ao vivo:** https://sar.ukiceker.com.br/login
**Infraestrutura:** EC2 Ubuntu (AWS) · HTTPS via Certbot/Let's Encrypt · Domínio próprio

---

## O que o sistema faz

O SAR automatiza o processo operacional de candidatura para que o profissional foque no que a IA não substitui: raciocínio jurídico, capacidade argumentativa e relações profissionais.

**Fluxo completo:**

1. **Cadastro e perfil** — o candidato registra resumo profissional, experiências, habilidades com nível de proficiência e links (GitHub, portfólio)
2. **Importação de vagas** — 850+ vagas da plataforma Peixe 30 com filtros por tipo de contrato (CLT, PJ, Estágio, Autônomo) e modalidade (Presencial, Remoto, Híbrido)
3. **Entrevista conduzida por agente LLM** — o Recrutador SAR lê o perfil do candidato, cruza com os requisitos da vaga e conduz entrevista personalizada em tempo real via WebSocket
4. **Dosimetria de aderência** — barra de progresso visual com meta em 75%; o currículo só é gerado ao atingir a meta
5. **Geração de currículo premium** — documento personalizado para cada vaga, produzido com base nos dados apurados pelo agente durante a entrevista

---

## Stack técnica

| Camada | Tecnologias |
|---|---|
| Backend | Python 3.12 · FastAPI · Uvicorn (assíncrono) |
| Frontend | Vue 3 · Vite · JavaScript Vanilla · HTML/CSS |
| Banco de dados | SQLite |
| IA / LLMs | Google Gemini 2.5 Flash · Groq API (fallback) |
| Comunicação | WebSocket (protocolo próprio — Ukiceker Conecta) |
| Segurança | JWT · bcrypt · SSL/HTTPS |
| Infraestrutura | AWS EC2 Ubuntu · Certbot/Let's Encrypt · Domínio próprio |

---

## Incidentes reais em produção

Três incidentes diagnosticados e corrigidos durante operação real com usuários:

- **Viés de modelo** — o agente favorecia perfis com determinado padrão de resposta; corrigido via ajuste de prompt e critérios de avaliação
- **Alucinação de contexto** — o LLM perdia referência ao perfil do candidato em sessões longas; corrigido com injeção de contexto controlada por turno
- **Fallback incompleto** — falha silenciosa na troca entre Gemini e Groq sem notificação ao usuário; corrigido com tratamento explícito de estado e log auditável

Diário de bordo completo disponível no repositório.

---

## Arquitetura

O sistema opera com quatro motores independentes:

- **Motor de vagas** — captura, normalização e filtragem de oportunidades do Peixe 30
- **Motor de identidade e acesso** — autenticação JWT, registro e gerenciamento de sessão
- **Motor de perfil** — cadastro estruturado do candidato com habilidades categorizadas e níveis de proficiência
- **Motor de geração** — agente LLM recrutador + dosimetria de aderência + produção do currículo premium

Comunicação entre frontend e backend via protocolo WebSocket desenvolvido internamente (Ukiceker Conecta), sem dependência de bibliotecas externas de integração.

---

## Contexto de desenvolvimento

Desenvolvido por um desenvolvedor autodidata com formação em Direito, usando IA como ferramenta de execução dentro de escopo fechado e documentado. Toda arquitetura, lógica e decisão técnica é do desenvolvedor — validada fisicamente contra resultado esperado antes de aceitar qualquer entrega como pronta.

**Autor:** Ricardo Alisson Dantas Macedo · [LinkedIn](https://linkedin.com/in/ricardo-alisson-macedo) · [GitHub](https://github.com/ricardopolpas-max)
