import io
import re
import json

from rotinas.ia import gerar_conteudo

_PROMPT = """Você é um assistente especializado em análise de currículos profissionais brasileiros de qualquer área.
Extraia as informações do currículo abaixo e retorne APENAS um JSON válido, sem markdown, sem explicações.

Estrutura esperada:
{
  "resumo_profissional": "string ou null",
  "localizacao": "Cidade, UF ou null",
  "pretensao_salarial": 0,
  "contatos": {
    "telefone": "string ou null",
    "linkedin": "URL ou null",
    "github": "URL ou null",
    "website": "URL ou null"
  },
  "experiencias": [
    {
      "cargo": "string",
      "empresa": "string",
      "data_inicio": "YYYY-MM-DD ou null",
      "data_fim": "YYYY-MM-DD ou null",
      "em_atual": 0,
      "descricao": "string ou null"
    }
  ],
  "formacoes": [
    {
      "instituicao": "string",
      "curso": "string",
      "nivel": "graduacao|pos_graduacao|mestrado|doutorado|tecnico|curso",
      "data_inicio": "YYYY-MM-DD ou null",
      "data_conclusao": "YYYY-MM-DD ou null",
      "em_progresso": 0
    }
  ],
  "habilidades": [
    {
      "nome": "string",
      "proficiencia": "basico|intermediario|avancado|especialista",
      "categoria": "juridica|tecnica|comportamental ou null"
    }
  ],
  "idiomas": [
    {
      "nome": "string",
      "proficiencia": "basico|intermediario|avancado|fluente|nativo"
    }
  ],
  "certificacoes": [
    {
      "nome": "string",
      "emissor": "string",
      "data_emissao": "YYYY-MM-DD ou null",
      "data_expiracao": "YYYY-MM-DD ou null",
      "url": "string ou null"
    }
  ]
}

Currículo:
"""


def extrair_texto_pdf(conteudo: bytes) -> str:
    import pdfplumber
    texto = []
    with pdfplumber.open(io.BytesIO(conteudo)) as pdf:
        for pagina in pdf.pages:
            t = pagina.extract_text()
            if t:
                texto.append(t)
    return "\n".join(texto)


def extrair_texto_docx(conteudo: bytes) -> str:
    import docx
    doc = docx.Document(io.BytesIO(conteudo))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


_PROMPT_CURRICULO = """Você é um especialista sênior em recrutamento brasileiro e redação estratégica de currículos.
Sua missão é produzir um currículo PREMIUM, altamente personalizado para a vaga abaixo,
seguindo rigorosamente o padrão ABNT NBR 9050 adaptado ao mercado de trabalho brasileiro.

DIRETRIZ PRINCIPAL: Este não é um exercício de transcrição. Você deve ANALISAR, SELECIONAR e TRANSFORMAR
estrategicamente as informações, apresentando o candidato da forma mais competitiva possível para ESTA vaga.

ESTRATÉGIAS OBRIGATÓRIAS:
- OBJETIVO PROFISSIONAL: 2-3 linhas que conectem diretamente a trajetória do candidato ao cargo pretendido,
  usando palavras-chave da descrição da vaga
- REFRAME DE EXPERIÊNCIAS: Traduza cargos anteriores em competências transferíveis para a vaga-alvo.
  Candidatos multidisciplinares têm trajetória rica — valorize cada área como diferencial complementar.
  Exemplos: gerência → liderança de equipes e gestão de processos; programação → análise de sistemas e
  automação; eletricidade → conformidade técnica e gestão de contratos de manutenção; condução de veículos
  pesados → logística, responsabilidade e cumprimento de normas regulatórias
- SELEÇÃO INTELIGENTE: Inclua apenas o que agrega valor para esta vaga — omita o que não contribui
- ENTREVISTA: Use as informações coletadas para enriquecer com detalhes específicos desta candidatura
- DOCUMENTOS: Se o candidato enviou arquivos complementares, use o conteúdo para fortalecer com evidências

FORMATAÇÃO ABNT OBRIGATÓRIA — siga EXATAMENTE este modelo:
- Cabeçalho: NOME COMPLETO EM MAIÚSCULO (sem cargo, sem data, sem foto)
- Linha de contato: telefone | e-mail | cidade, UF (apenas o que estiver disponível)
- Cada seção com título em MAIÚSCULAS e sublinhado com traços (ex: FORMAÇÃO ACADÊMICA)
- Experiências: cargo em negrito textual (sem asterisco), seguido de nome da empresa e período no formato Mês/AAAA – Mês/AAAA (ou "atual")
- Datas APENAS dentro de cada item de experiência/formação, NUNCA nos cabeçalhos de seção
- Bullet points com hífen (-) para responsabilidades e habilidades
- Uma linha em branco entre seções
- Linguagem objetiva, sem adjetivos vazios (não use "dinâmico", "proativo", "dedicado")
- NÃO inclua CPF, RG, endereço completo, foto, idade ou estado civil
- NÃO use markdown (sem **, sem ##, sem *)
- NÃO inclua data de geração, rodapé ou cabeçalho com data
- Retorne APENAS o texto puro do currículo, começando pelo nome do candidato

ESTRUTURA DAS SEÇÕES (nesta ordem, inclua apenas as que tiverem dados):
DADOS DE CONTATO → OBJETIVO PROFISSIONAL → FORMAÇÃO ACADÊMICA → EXPERIÊNCIA PROFISSIONAL → HABILIDADES → IDIOMAS → CERTIFICAÇÕES E CURSOS

VAGA:
Título: {titulo}
Descrição: {descricao}

PERFIL BASE DO CANDIDATO:
{perfil}

INFORMAÇÕES ADICIONAIS DA ENTREVISTA (use se disponíveis):
{historico}
"""

_PROMPT_SCORE = """Você é um especialista em recrutamento jurídico brasileiro.
Analise a compatibilidade entre o candidato e a vaga abaixo.
Retorne APENAS um JSON válido, sem markdown, sem explicações.

Estrutura esperada:
{
  "score": <inteiro 0 a 100>,
  "resumo": "<1 frase explicando o nível de compatibilidade>",
  "pontos_fortes": ["<item>", "<item>"],
  "lacunas": ["<item>", "<item>"]
}

VAGA:
Título: {titulo}
Descrição: {descricao}

CANDIDATO:
{perfil}
"""


def _extrair_json(texto: str) -> dict:
    if texto.startswith("```"):
        linhas = texto.split("\n")
        texto = "\n".join(linhas[1:-1])
    match = re.search(r'\{[\s\S]*\}', texto)
    if match:
        return json.loads(match.group())
    return json.loads(texto)


def processar_score_com_ia(titulo: str, descricao: str, perfil: str) -> dict:
    prompt = (
        _PROMPT_SCORE
        .replace("{titulo}", titulo)
        .replace("{descricao}", descricao or "Não informada")
        .replace("{perfil}", perfil)
    )
    return _extrair_json(gerar_conteudo(prompt))


def processar_curriculo_com_ia(texto: str) -> dict:
    return _extrair_json(gerar_conteudo(_PROMPT + texto))


def gerar_curriculo_com_ia(titulo: str, descricao: str, perfil: str, historico: str = "") -> str:
    prompt = (
        _PROMPT_CURRICULO
        .replace("{titulo}", titulo)
        .replace("{descricao}", descricao or "Não informada")
        .replace("{perfil}", perfil)
        .replace("{historico}", historico or "(sem informações adicionais da entrevista)")
    )
    return gerar_conteudo(prompt)


_PROMPT_RECRUTADOR = """Você é um recrutador especializado em Direito brasileiro, conduzindo uma entrevista estruturada.
Seu objetivo é conhecer o candidato profundamente para a vaga abaixo, identificando e preenchendo lacunas do currículo.

INSTRUÇÕES:
- Faça APENAS UMA pergunta por vez — seja objetivo, profissional e cordial
- Foque nas lacunas entre o perfil do candidato e os requisitos da vaga
- Leve em conta tudo que o candidato já respondeu no histórico da conversa
- Estime internamente o score de aderência do candidato à vaga (0 a 100)
- Quando o score estimado atingir 75 ou mais, defina "pronto": true e informe ao candidato
- Se o histórico estiver vazio, apresente-se brevemente e faça a primeira pergunta relevante
- Em momento oportuno da entrevista (após cobrir experiência e formação, antes de encerrar),
  pergunte ao candidato se ele possui documentos complementares que gostaria de compartilhar —
  como certificados, declarações, portfólio ou comprovantes de cursos. Deixe claro que é opcional
  e que ele pode enviá-los pelo botão de anexo (📎) disponível na tela

VAGA:
Título: {titulo}
Descrição: {descricao}

PERFIL ATUAL DO CANDIDATO:
{perfil}

HISTÓRICO DA CONVERSA:
{historico}

Retorne APENAS um JSON válido, sem markdown, sem explicações:
{
  "mensagem": "sua mensagem para o candidato",
  "pronto": false,
  "score_estimado": 0
}
"""


def conduzir_entrevista(titulo: str, descricao: str, perfil: str, historico: list) -> dict:
    hist_texto = "\n".join(
        f"{h['role'].upper()}: {h['conteudo']}" for h in historico
    ) if historico else "(nenhuma troca anterior — inicie a entrevista apresentando-se)"

    prompt = (
        _PROMPT_RECRUTADOR
        .replace("{titulo}",   titulo)
        .replace("{descricao}", descricao or "Não informada")
        .replace("{perfil}",   perfil)
        .replace("{historico}", hist_texto)
    )

    try:
        return _extrair_json(gerar_conteudo(prompt))
    except Exception:
        return {
            "mensagem": "Desculpe, tive um problema ao processar. Pode repetir sua resposta?",
            "pronto": False,
            "score_estimado": 0,
        }
