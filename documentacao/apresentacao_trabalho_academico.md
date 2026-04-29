# SAR — Sistema de Automação de Recolocação
### Documento de Apresentação — Trabalho Acadêmico
**Disciplina:** Desenvolvimento Pessoal e Trabalhabilidade
**Área de Atuação:** Direito

---

## 1. Contexto e Problema

O mercado jurídico brasileiro é altamente competitivo. Bacharéis e advogados em fase de colocação ou recolocação profissional enfrentam um conjunto de desafios que dificultam sua inserção no mercado:

- **Volume e dispersão de vagas:** oportunidades espalhadas em múltiplas plataformas, com atualização constante e difícil rastreamento manual.
- **Currículos genéricos:** a maioria dos profissionais utiliza um único currículo para todas as candidaturas, ignorando os requisitos específicos de cada vaga.
- **Sistemas ATS (Applicant Tracking System):** grandes escritórios e empresas utilizam filtros automáticos que eliminam currículos antes mesmo de chegarem ao recrutador humano, penalizando candidatos que não otimizam seus documentos para esses sistemas.
- **Tempo e esforço:** adaptar currículo, vasculhar vagas e candidatar-se a dezenas de posições de forma manual consome horas diárias que poderiam ser dedicadas ao desenvolvimento técnico-jurídico.

Esses fatores comprometem diretamente o **desenvolvimento pessoal e a trabalhabilidade** dos profissionais da área jurídica — o eixo central desta disciplina.

---

## 2. Proposta de Solução — O SAR

O **SAR (Sistema de Automação de Recolocação)** é uma plataforma web inteligente desenvolvida para automatizar a jornada de recolocação profissional de operadores do Direito.

### O que o SAR faz

O sistema atua em três frentes integradas:

| Frente | O que entrega |
|---|---|
| **Captura de Vagas** | Sincroniza automaticamente vagas jurídicas de fontes externas, eliminando a busca manual e mantendo um repositório atualizado |
| **Leitura de Perfil via IA** | O candidato importa seu currículo atual (qualquer formato); a inteligência artificial extrai e estrutura automaticamente suas competências, experiências e formação |
| **Currículo Personalizado** | Para cada vaga de interesse, a IA gera um currículo sob medida, otimizado com as palavras-chave e seções que os sistemas ATS esperam encontrar |

### Resultado prático para o profissional jurídico

- Menos tempo gasto em tarefas operacionais de candidatura.
- Maior taxa de aprovação nas triagens automáticas (ATS).
- Currículo alinhado ao vocabulário técnico-jurídico exigido por cada posição.
- Mais tempo disponível para preparação técnica, networking e desenvolvimento pessoal.

---

## 3. Conexão com a Disciplina

A disciplina **Desenvolvimento Pessoal e Trabalhabilidade** aborda competências essenciais para a inserção e progressão no mercado de trabalho. O SAR materializa esse conceito de forma prática:

| Pilar da Disciplina | Como o SAR contribui |
|---|---|
| **Autoconhecimento profissional** | A análise do currículo pela IA fornece ao candidato uma visão estruturada de seu próprio perfil, revelando lacunas e pontos fortes |
| **Trabalhabilidade** | Automatiza tarefas de baixo valor cognitivo, permitindo que o profissional concentre energia no que realmente diferencia: conhecimento jurídico e relacionamento |
| **Adaptabilidade** | O currículo gerado por vaga demonstra ao candidato como adaptar sua narrativa profissional a diferentes contextos e empregadores |
| **Tecnologia como aliada** | Introduz o profissional jurídico ao uso estratégico de ferramentas digitais e IA — competência cada vez mais valorizada no mercado |

---

## 4. Visão Geral da Arquitetura (sem tecnicismo)

O SAR funciona como uma aplicação web local, rodando no computador do usuário. A comunicação é segura (HTTPS), e todos os dados são armazenados localmente — sem envio de informações pessoais para servidores externos.

```
[Você, no navegador]
        ↓
[Interface SAR — tela de vagas, candidatos, currículos]
        ↓
[Servidor local seguro (HTTPS)]
        ↓
[Banco de dados local]     [Inteligência Artificial — Google Gemini]
```

**Privacidade:** o currículo e os dados do candidato ficam exclusivamente no dispositivo local. Apenas o texto do currículo é enviado à IA para análise, sem identificação pessoal que não seja necessária.

---

## 5. Tecnologias Utilizadas

As escolhas tecnológicas foram orientadas por dois critérios: **custo zero** (contexto acadêmico) e **robustez** (plataforma capaz de evoluir para uso real).

| Componente | Tecnologia | Justificativa |
|---|---|---|
| Servidor | Python + FastAPI | Moderno, rápido, amplamente utilizado em sistemas profissionais |
| Interface | HTML + CSS + JavaScript | Sem dependências externas; compatível com qualquer navegador |
| Banco de Dados | SQLite | Leve, local, sem necessidade de instalação de servidor |
| Segurança | SSL/HTTPS (mkcert) | Criptografia obrigatória em todas as comunicações |
| Inteligência Artificial | Google Gemini 2.0 Flash | Tier gratuito com 1.500 requisições/dia — suficiente para o contexto acadêmico |
| Leitura de currículos | Bibliotecas especializadas | Suporte a PDF, Word (DOCX), texto puro, ODT e RTF |

---

## 6. Estágio Atual de Desenvolvimento

O projeto está estruturado em fases progressivas:

| Fase | Descrição | Status |
|---|---|---|
| **Fase 1** | Infraestrutura: servidor, banco de dados, interface base, segurança SSL | **Concluída** |
| **Fase 2** | Captura automática de vagas com sincronização em tempo real | Em desenvolvimento |
| **Fase 3** | Upload de currículo e extração de perfil via IA | Planejada |
| **Fase 4** | Geração de currículo personalizado por vaga com otimização ATS | Planejada |
| **Fase 5** | Refinamento de usabilidade e experiência do usuário | Planejada |
| **Fase 6** | Testes de qualidade e robustez | Planejada |
| **Fase 7** | Auditoria final e versão estável | Planejada |

A Fase 1 encontra-se **operacional**: o sistema sobe, o banco de dados é inicializado, a interface é servida com segurança, e a estrutura de dados para vagas está definida.

---

## 7. Impacto Esperado

O SAR não é apenas um exercício técnico. Ele endereça um problema real e recorrente para estudantes e profissionais do Direito:

> *"Tenho o conhecimento jurídico, mas não sei por onde começar a me candidatar, nem como fazer meu currículo se destacar."*

Ao automatizar a etapa operacional da candidatura, o sistema libera o profissional para focar no que nenhuma inteligência artificial substitui: **o raciocínio jurídico, a capacidade argumentativa e o desenvolvimento das relações profissionais**.

Isso é trabalhabilidade aplicada.

---

## 8. Próximos Passos para a Apresentação

- Demonstração ao vivo da Fase 1: servidor rodando, interface carregada em HTTPS.
- Apresentação do roadmap completo e das funcionalidades previstas.
- Contextualização do problema de empregabilidade jurídica e como o SAR responde a ele.

---

*Documento elaborado para uso interno da equipe acadêmica.*
*Versão: 2026-04-28*
