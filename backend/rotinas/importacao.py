import io
import re
import json

from rotinas.ia import gerar_conteudo

_PROMPT = """Você é um assistente especializado em análise de currículos jurídicos brasileiros.
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


_PROMPT_CURRICULO = """Você é um especialista em recrutamento jurídico brasileiro e redação de currículos.
Com base no perfil do candidato e na descrição da vaga abaixo, redija um currículo profissional personalizado.

Diretrizes:
- Destaque as competências e experiências mais relevantes para essa vaga específica
- Use linguagem objetiva, profissional e adequada ao mercado jurídico brasileiro
- Estruture na ordem: DADOS PESSOAIS → OBJETIVO PROFISSIONAL → FORMAÇÃO → EXPERIÊNCIA → HABILIDADES → IDIOMAS → CERTIFICAÇÕES
- Objetivo profissional: 1 parágrafo direcionado especificamente para a vaga
- Experiências: do mais recente ao mais antigo
- NÃO invente informações — use apenas o que está no perfil
- NÃO inclua CPF, RG nem endereço completo
- Retorne APENAS o texto do currículo com seções em maiúsculo, SEM markdown, SEM JSON

VAGA:
Título: {titulo}
Descrição: {descricao}

PERFIL DO CANDIDATO:
{perfil}
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


def gerar_curriculo_com_ia(titulo: str, descricao: str, perfil: str) -> str:
    prompt = (
        _PROMPT_CURRICULO
        .replace("{titulo}", titulo)
        .replace("{descricao}", descricao or "Não informada")
        .replace("{perfil}", perfil)
    )
    return gerar_conteudo(prompt)
